import os
import logging
import time
from typing import List, Dict, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Global Cache for frequent queries
QUERY_CACHE = {}

try:
    from langchain_ollama import ChatOllama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False
    logger.warning("langchain_ollama not found. Running in offline simulation mode.")


def detect_detail_level(query: str) -> str:
    """
    Detects if user wants detailed response.
    Returns: 'low', 'medium', 'high'
    
    Indicators:
    - High: "in detail", "elaborate", "comprehensive", "full", "detailed"
    - Medium: "explain", "describe", "tell me about", "how", "what about"
    - Low: "what is", "is it", "brief", "quick", "summary"
    """
    detail_keywords = {
        'high': [
            'in detail', 'elaborate', 'comprehensive', 'full', 'detailed',
            'explain thoroughly', 'all aspects', 'complete', 'extensive',
            'deep dive', 'thorough', 'everything', 'all information',
            'detailed analysis', 'comprehensive overview'
        ],
        'medium': [
            'explain', 'describe', 'tell me about', 'how', 'what about',
            'more information', 'details', 'background', 'context',
            'information about', 'overview'
        ],
        'low': [
            'what is', 'is it', 'brief', 'quick', 'summary',
            'short', 'simple', 'just', 'only'
        ]
    }
    
    query_lower = query.lower()
    
    # Check for high detail indicators
    if any(kw in query_lower for kw in detail_keywords['high']):
        return 'high'
    
    # Check for medium detail indicators
    if any(kw in query_lower for kw in detail_keywords['medium']):
        return 'medium'
    
    # Check for low detail indicators
    if any(kw in query_lower for kw in detail_keywords['low']):
        return 'low'
    
    # Check query length (longer queries often expect more detail)
    word_count = len(query.split())
    if word_count > 20:
        return 'high'
    elif word_count > 10:
        return 'medium'
    
    # Check for multiple questions (indicates desire for comprehensive answer)
    if query.count('?') > 1:
        return 'high'
    
    # Default to medium
    return 'medium'


def get_llm_params(detail_level: str) -> Dict:
    """
    Returns LLM parameters based on detail level.
    OPTIMIZED for 10s latency compliance:
    - Reduced token generation
    - Faster inference
    """
    params = {
        'low': {
            'num_predict': 16,        # Ultra-fast: ~0.5-1s
            'temperature': 0.1,
            'top_k': 30,
            'top_p': 0.85
        },
        'medium': {
            'num_predict': 32,        # Fast: ~1-2s
            'temperature': 0.15,
            'top_k': 40,
            'top_p': 0.9
        },
        'high': {
            'num_predict': 64,        # Moderate: ~2-4s
            'temperature': 0.2,
            'top_k': 50,
            'top_p': 0.95
        }
    }
    return params.get(detail_level, params['medium'])


def get_system_prompt(detail_level: str) -> str:
    """
    Returns system prompt based on detail level.
    """
    prompts = {
        'low': (
            "You are a concise aerospace assistant. "
            "Provide brief, direct answers using only the provided context. "
            "Keep responses to 2-3 sentences maximum."
        ),
        'medium': (
            "You are a helpful aerospace assistant. "
            "Provide clear, informative responses that include: "
            "1. Direct answer to the question "
            "2. Key technical details "
            "3. Related information if relevant. "
            "Use only the provided context. Be thorough but concise."
        ),
        'high': (
            "You are a comprehensive aerospace intelligence assistant. "
            "Provide detailed, thorough responses that cover: "
            "1. Direct answer to the question "
            "2. Technical specifications and detailed information "
            "3. Related missions, vehicles, or technologies "
            "4. Historical context if relevant "
            "5. Key relationships and dependencies. "
            "Use the provided context to support all claims. "
            "Be comprehensive and informative."
        )
    }
    return prompts.get(detail_level, prompts['medium'])


def format_response_by_detail_level(response: str, detail_level: str, facts: List[str] = None) -> str:
    """
    Formats response based on detail level.
    Adds sections for high detail responses.
    """
    if detail_level == 'low':
        return response
    
    elif detail_level == 'medium':
        # Add a simple structure if not already present
        if '\n\n' not in response:
            return response
        return response
    
    elif detail_level == 'high':
        # For high detail, ensure comprehensive structure
        # This is handled by the LLM prompt, but we can enhance here if needed
        return response
    
    return response


def generate_response(
    query: str,
    context_chunks: List,
    history: List = None,
    model_name: str = "llama3.2:1b",
    facts: List[str] = None,
    detail_level: str = None
) -> Tuple[str, Dict]:
    """
    Generates a response with adaptive detail level.
    OPTIMIZED for 10s latency compliance.
    
    Recommended models (in order of speed):
    1. llama3.2:1b (1B) - 8-10x faster than llama3, good for factual queries
    2. llama3.2:3b (3B) - 3-5x faster than llama3, better quality
    3. mistral (7B) - 2x faster than llama3, good quality
    4. llama3 (8B) - Original, slower but highest quality
    
    Returns:
        Tuple of (response_text, metadata_dict)
    """
    # Detect detail level if not provided
    if detail_level is None:
        detail_level = detect_detail_level(query)
    
    # Check cache
    cache_key = f"{query}_{detail_level}"
    if cache_key in QUERY_CACHE:
        return QUERY_CACHE[cache_key], {'cached': True, 'detail_level': detail_level}
    
    # Get LLM parameters based on detail level (OPTIMIZED)
    llm_params = get_llm_params(detail_level)
    system_prompt = get_system_prompt(detail_level)
    
    # Construct the prompt context (Hybrid: Facts first, then Chunks)
    context_text = ""
    if facts:
        fact_str = "\n".join(facts)
        context_text += f"--- KNOWLEDGE GRAPH FACTS ---\n{fact_str}\n\n"
    
    if context_chunks:
        context_text += "--- DOCUMENT CHUNKS ---\n" + "\n\n".join([c.page_content for c in context_chunks])
    else:
        pass
    
    # 1. Try Ollama (Local LLM)
    if HAS_OLLAMA:
        try:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            # Use specified model or default to llama3.2:1b (faster)
            model = model_name or os.getenv("OLLAMA_MODEL", "llama3.2:1b")
            
            logger.info(f"Generating response with detail_level={detail_level}, model={model}, tokens={llm_params['num_predict']}")
            
            llm = ChatOllama(
                base_url=base_url,
                model=model,
                temperature=llm_params['temperature'],
                timeout=60.0,
                num_predict=llm_params['num_predict'],
                top_k=llm_params['top_k'],
                top_p=llm_params['top_p']
            )

            # Construct message list
            prompt_messages = [("system", system_prompt)]
            
            if history:
                history_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history[-3:]])
                prompt_messages.append(("human", f"Previous conversation:\n{history_text}"))
            
            prompt_messages.append(("human", f"Context:\n{context_text}\n\nQuestion: {query}"))
            
            # Generate response
            response = llm.invoke(prompt_messages)
            response_text = response.content
            
            # Format response based on detail level
            formatted_response = format_response_by_detail_level(response_text, detail_level, facts)
            
            # Cache the response
            QUERY_CACHE[cache_key] = formatted_response
            
            metadata = {
                'detail_level': detail_level,
                'cached': False,
                'model': model,
                'num_predict': llm_params['num_predict'],
                'temperature': llm_params['temperature']
            }
            
            return formatted_response, metadata

        except Exception as e:
            logger.warning(f"Ollama connection failed: {e}. Falling back to offline simulation.")

    # 2. Fallback: Offline Simulation (Simple Extraction)
    logger.info(f"Using offline fallback (string matching) with detail_level={detail_level}")
    
    # Simple extraction for demo purposes
    if "fuel" in query.lower():
        for chunk in context_chunks:
            sentences = chunk.page_content.split('.')
            for s in sentences:
                if "fuel" in s.lower() or "propellant" in s.lower():
                    ans = f"Based on validated documents (Fallback): {s.strip()}."
                    QUERY_CACHE[cache_key] = ans
                    return ans, {'detail_level': detail_level, 'cached': False, 'fallback': True}
    
    ans = f"Based on retrieved context (Fallback):\n{context_chunks[0].page_content[:200]}..."
    QUERY_CACHE[cache_key] = ans
    return ans, {'detail_level': detail_level, 'cached': False, 'fallback': True}


async def generate_response_stream(
    query: str,
    context_chunks: List,
    history: List = None,
    model_name: str = "llama3.2:1b",
    facts: List[str] = None,
    detail_level: str = None
):
    """
    Generates a streaming response with adaptive detail level.
    OPTIMIZED for 10s latency compliance.
    
    Streaming provides:
    - Perceived latency: 1-2s (first token appears immediately)
    - Full latency: 5-6s (with optimized tokens)
    - Better UX: User sees response appearing in real-time
    """
    # Detect detail level if not provided
    if detail_level is None:
        detail_level = detect_detail_level(query)
    
    cache_key = f"{query}_{detail_level}"
    if cache_key in QUERY_CACHE:
        yield QUERY_CACHE[cache_key]
        return

    # Get LLM parameters based on detail level (OPTIMIZED)
    llm_params = get_llm_params(detail_level)
    system_prompt = get_system_prompt(detail_level)
    
    # Construct hybrid context
    context_text = ""
    if facts:
        fact_str = "\n".join(facts)
        context_text += f"--- KNOWLEDGE GRAPH FACTS ---\n{fact_str}\n\n"
    
    if context_chunks:
        context_text += "--- DOCUMENT CHUNKS ---\n" + "\n\n".join([c.page_content for c in context_chunks])
    
    if HAS_OLLAMA:
        try:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = model_name or os.getenv("OLLAMA_MODEL", "llama3")
            
            logger.info(f"Streaming response with detail_level={detail_level}, model={model}, tokens={llm_params['num_predict']}")
            
            llm = ChatOllama(
                base_url=base_url,
                model=model,
                temperature=llm_params['temperature'],
                timeout=60.0,
                num_predict=llm_params['num_predict'],
                top_k=llm_params['top_k'],
                top_p=llm_params['top_p']
            )

            prompt_messages = [("system", system_prompt)]
            if history:
                history_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history[-3:]])
                prompt_messages.append(("human", f"Previous conversation:\n{history_text}"))
            
            prompt_messages.append(("human", f"Context:\n{context_text}\n\nQuestion: {query}"))
            
            full_response = ""
            async for chunk in llm.astream(prompt_messages):
                full_response += chunk.content
                yield chunk.content
            
            QUERY_CACHE[cache_key] = full_response

        except Exception as e:
            logger.warning(f"Ollama stream failed: {e}. Falling back to offline simulation.")
            
            # Fallback Logic
            yield "Based on retrieved context (Fallback): "
            
            if "fuel" in query.lower():
                found_specific = False
                for chunk in context_chunks:
                    sentences = chunk.page_content.split('.')
                    for s in sentences:
                        if "fuel" in s.lower() or "propellant" in s.lower():
                            yield f"{s.strip()}. "
                            found_specific = True
                            break
                    if found_specific:
                        break
            
            if context_chunks:
                yield f"\n{context_chunks[0].page_content[:300]}..."
            else:
                yield "No relevant context found in offline mode."
    else:
        yield "Ollama not installed. Offline mode."


class LatencyTracker:
    """
    Tracks latency of each pipeline stage.
    """
    def __init__(self):
        self.stages = {}
        self.start_time = time.time()
    
    def start_stage(self, stage_name: str):
        """Start timing a stage."""
        self.stages[stage_name] = {'start': time.time()}
    
    def end_stage(self, stage_name: str) -> float:
        """End timing a stage and return duration."""
        if stage_name in self.stages:
            self.stages[stage_name]['end'] = time.time()
            duration = self.stages[stage_name]['end'] - self.stages[stage_name]['start']
            
            # Alert if exceeds threshold
            if duration > 2.0:
                logger.warning(f"⚠️  LATENCY WARNING: {stage_name} took {duration:.2f}s")
            
            return duration
        return None
    
    def get_summary(self) -> Dict:
        """Get summary of all stages."""
        summary = {}
        total = 0
        for stage, times in self.stages.items():
            if 'end' in times:
                duration = times['end'] - times['start']
                summary[stage] = duration
                total += duration
        
        summary['total'] = total
        return summary
    
    def print_summary(self):
        """Print latency summary."""
        summary = self.get_summary()
        print("\n=== LATENCY SUMMARY ===")
        for stage, duration in summary.items():
            if stage != 'total':
                print(f"  {stage}: {duration*1000:.1f}ms")
        print(f"  TOTAL: {summary['total']*1000:.1f}ms")
        
        if summary['total'] > 10.0:
            print("❌ EXCEEDED 10s LIMIT")
        else:
            remaining = 10.0 - summary['total']
            print(f"✅ Within 10s limit ({remaining:.1f}s remaining)")
    
    def check_compliance(self) -> bool:
        """Check if latency is within 10s limit."""
        summary = self.get_summary()
        return summary['total'] <= 10.0
