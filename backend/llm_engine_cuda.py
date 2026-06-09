"""
CUDA-Optimized LLM Engine for Nexora RAG System
Provides faster inference using GPU acceleration with multiple backend options:
1. Ollama with CUDA support
2. Direct Hugging Face Transformers with GPU
3. vLLM for ultra-fast inference
"""

import os
import logging
import torch
from typing import List, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Global Cache for frequent queries
QUERY_CACHE = {}

# Check CUDA availability
USE_CUDA = torch.cuda.is_available()
if USE_CUDA:
    logger.info(f"🚀 CUDA Available: {torch.cuda.get_device_name(0)}")
    logger.info(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
else:
    logger.warning("⚠️  CUDA not available, falling back to CPU")

# Try to import backends
try:
    from langchain_ollama import ChatOllama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False
    logger.warning("langchain_ollama not found.")

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("transformers not found.")

try:
    from vllm import LLM, SamplingParams
    HAS_VLLM = True
except ImportError:
    HAS_VLLM = False
    logger.warning("vLLM not found. Install with: pip install vllm")

# Backend selection priority: vLLM > Transformers > Ollama > Fallback
BACKEND = None
_LLM_MODEL = None
_TOKENIZER = None

def initialize_backend(backend_type: str = "auto", model_name: str = None):
    """
    Initialize the LLM backend with CUDA acceleration.
    
    Args:
        backend_type: "auto", "vllm", "transformers", "ollama", or "fallback"
        model_name: Model name/path (e.g., "meta-llama/Llama-2-7b-chat-hf")
    """
    global BACKEND, _LLM_MODEL, _TOKENIZER
    
    if BACKEND is not None:
        return BACKEND
    
    # Auto-detect best backend
    if backend_type == "auto":
        if HAS_VLLM and USE_CUDA:
            backend_type = "vllm"
        elif HAS_TRANSFORMERS and USE_CUDA:
            backend_type = "transformers"
        elif HAS_OLLAMA:
            backend_type = "ollama"
        else:
            backend_type = "fallback"
    
    logger.info(f"🔧 Initializing backend: {backend_type}")
    
    # vLLM Backend (Fastest for batch inference)
    if backend_type == "vllm" and HAS_VLLM and USE_CUDA:
        try:
            model_name = model_name or os.getenv("VLLM_MODEL", "meta-llama/Llama-2-7b-chat-hf")
            logger.info(f"Loading vLLM model: {model_name}")
            _LLM_MODEL = LLM(
                model=model_name,
                tensor_parallel_size=1,  # Use 1 GPU
                gpu_memory_utilization=0.8,
                max_model_len=2048,
                dtype="half"  # FP16 for speed
            )
            BACKEND = "vllm"
            logger.info("✅ vLLM backend initialized")
            return BACKEND
        except Exception as e:
            logger.error(f"vLLM initialization failed: {e}")
    
    # Transformers Backend (Good balance of speed and compatibility)
    if backend_type == "transformers" and HAS_TRANSFORMERS:
        try:
            model_name = model_name or os.getenv("HF_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
            logger.info(f"Loading Transformers model: {model_name}")
            
            device = "cuda" if USE_CUDA else "cpu"
            _TOKENIZER = AutoTokenizer.from_pretrained(model_name)
            _LLM_MODEL = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if USE_CUDA else torch.float32,
                device_map="auto" if USE_CUDA else None,
                low_cpu_mem_usage=True
            )
            
            if not USE_CUDA:
                _LLM_MODEL = _LLM_MODEL.to(device)
            
            BACKEND = "transformers"
            logger.info(f"✅ Transformers backend initialized on {device.upper()}")
            return BACKEND
        except Exception as e:
            logger.error(f"Transformers initialization failed: {e}")
    
    # Ollama Backend (with CUDA if configured)
    if backend_type == "ollama" and HAS_OLLAMA:
        BACKEND = "ollama"
        logger.info("✅ Ollama backend selected")
        return BACKEND
    
    # Fallback
    BACKEND = "fallback"
    logger.info("⚠️  Using fallback mode (no LLM)")
    return BACKEND


def generate_response_cuda(
    query: str, 
    context_chunks: List, 
    history: List = None, 
    model_name: str = None,
    facts: List[str] = None, 
    is_conversational: bool = False,
    backend: str = "auto"
) -> str:
    """
    Generates a response using CUDA-accelerated inference.
    Falls back gracefully to CPU or other backends if GPU is unavailable.
    """
    if query in QUERY_CACHE:
        return QUERY_CACHE[query]
    
    # Initialize backend if needed
    initialize_backend(backend, model_name)
    
    # Construct context
    context_text = ""
    if facts:
        fact_str = "\n".join(facts)
        context_text += f"--- KNOWLEDGE GRAPH FACTS ---\n{fact_str}\n\n"
    
    if context_chunks:
        context_text += "--- DOCUMENT CHUNKS ---\n" + "\n\n".join([c.page_content for c in context_chunks])
    
    # Build system instruction
    if is_conversational:
        system_instr = (
            "You are a helpful and friendly assistant for ISRO aerospace queries.\n"
            "Respond naturally and helpfully to greetings and general questions.\n"
            "Be warm and professional."
        )
    else:
        system_instr = (
            "You are an ISRO aerospace documentation assistant.\n"
            "CRITICAL RULES:\n"
            "1. ONLY answer questions about ISRO, Indian space missions, satellites, launch vehicles, and space technology.\n"
            "2. Use information from the provided context to answer questions.\n"
            "3. For general questions about ISRO (achievements, missions, capabilities), synthesize information from the context.\n"
            "4. For specific technical questions (specifications, dates, names), ONLY use exact information from context.\n"
            "5. If asked about non-ISRO topics, respond: 'This question is outside my scope. I can only answer questions about ISRO missions and space technology.'\n"
            "6. If context is empty or irrelevant, respond: 'No documentation found in the local archive for this query.'\n"
            "7. NEVER fabricate technical specifications, dates, or names not in the context.\n"
            "8. NEVER add 'Verified by:' or source citations in your response."
        )
    
    # Route to appropriate backend
    try:
        if BACKEND == "vllm":
            response = _generate_vllm(query, context_text, system_instr, history)
        elif BACKEND == "transformers":
            response = _generate_transformers(query, context_text, system_instr, history)
        elif BACKEND == "ollama":
            response = _generate_ollama(query, context_text, system_instr, history, model_name)
        else:
            response = _generate_fallback(query, context_chunks, is_conversational)
        
        QUERY_CACHE[query] = response
        return response
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return _generate_fallback(query, context_chunks, is_conversational)


def _generate_vllm(query: str, context: str, system_instr: str, history: List) -> str:
    """Generate response using vLLM backend."""
    global _LLM_MODEL
    
    # Build prompt
    prompt = f"{system_instr}\n\n"
    if history:
        for msg in history[-3:]:
            prompt += f"{msg['role'].upper()}: {msg['content']}\n"
    if context:
        prompt += f"Context:\n{context}\n\n"
    prompt += f"Question: {query}\nAnswer:"
    
    # Generate
    sampling_params = SamplingParams(
        temperature=0.1,
        top_p=0.9,
        max_tokens=512
    )
    
    outputs = _LLM_MODEL.generate([prompt], sampling_params)
    return outputs[0].outputs[0].text.strip()


def _generate_transformers(query: str, context: str, system_instr: str, history: List) -> str:
    """Generate response using Transformers backend with GPU acceleration."""
    global _LLM_MODEL, _TOKENIZER
    
    # Build prompt
    messages = [{"role": "system", "content": system_instr}]
    if history:
        messages.extend(history[-3:])
    
    user_msg = query
    if context:
        user_msg = f"Context:\n{context}\n\nQuestion: {query}"
    messages.append({"role": "user", "content": user_msg})
    
    # Tokenize
    prompt = _TOKENIZER.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = _TOKENIZER(prompt, return_tensors="pt", truncation=True, max_length=1536)
    
    # Move to GPU if available
    if USE_CUDA:
        inputs = {k: v.cuda() for k, v in inputs.items()}
    
    # Generate
    with torch.no_grad():
        outputs = _LLM_MODEL.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.1,
            top_p=0.9,
            do_sample=True,
            pad_token_id=_TOKENIZER.eos_token_id
        )
    
    # Decode
    response = _TOKENIZER.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return response.strip()


def _generate_ollama(query: str, context: str, system_instr: str, history: List, model_name: str) -> str:
    """Generate response using Ollama backend (may use GPU if configured)."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = model_name or os.getenv("OLLAMA_MODEL", "llama3")
    
    llm = ChatOllama(
        base_url=base_url,
        model=model,
        temperature=0.1,
        timeout=60.0,
        num_predict=512,
        top_k=40,
        top_p=0.9,
        # Enable GPU in Ollama by setting OLLAMA_NUM_GPU in environment
        num_gpu=int(os.getenv("OLLAMA_NUM_GPU", "1")) if USE_CUDA else 0
    )
    
    prompt_messages = [("system", system_instr)]
    if history:
        history_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history[-3:]])
        prompt_messages.append(("human", f"Previous conversation:\n{history_text}"))
    
    if context:
        prompt_messages.append(("human", f"Context:\n{context}\n\nQuestion: {query}"))
    else:
        prompt_messages.append(("human", query))
    
    response = llm.invoke(prompt_messages)
    return response.content


def _generate_fallback(query: str, context_chunks: List, is_conversational: bool) -> str:
    """Fallback generation for offline/no-GPU mode."""
    if is_conversational:
        greetings_responses = {
            "hello": "Hello! I'm here to help with ISRO aerospace questions.",
            "hi": "Hi there! How can I assist you with ISRO information?",
            "hey": "Hey! What would you like to know about ISRO?",
        }
        return greetings_responses.get(query.lower().strip(), "Hello! How can I assist you?")
    
    if context_chunks:
        return f"Based on retrieved context:\n{context_chunks[0].page_content[:300]}..."
    return "No context available."


async def generate_response_stream_cuda(
    query: str,
    context_chunks: List,
    history: List = None,
    model_name: str = None,
    facts: List[str] = None,
    is_conversational: bool = False,
    backend: str = "auto"
):
    """
    Streaming version of CUDA-accelerated generation.
    """
    # For now, yield the full response (streaming implementation depends on backend)
    response = generate_response_cuda(
        query, context_chunks, history, model_name, facts, is_conversational, backend
    )
    
    # Simulate streaming by yielding chunks
    chunk_size = 20
    for i in range(0, len(response), chunk_size):
        yield response[i:i+chunk_size]


# Utility function to check GPU status
def get_gpu_status():
    """Returns GPU status and memory information."""
    if not USE_CUDA:
        return {
            "available": False,
            "message": "CUDA not available"
        }
    
    return {
        "available": True,
        "device": torch.cuda.get_device_name(0),
        "memory_total_gb": torch.cuda.get_device_properties(0).total_memory / 1e9,
        "memory_allocated_gb": torch.cuda.memory_allocated(0) / 1e9,
        "memory_reserved_gb": torch.cuda.memory_reserved(0) / 1e9,
        "backend": BACKEND
    }
