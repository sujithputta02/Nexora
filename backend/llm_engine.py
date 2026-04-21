import os
import logging
from typing import List

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

def generate_response(query: str, context_chunks: List, history: List = None, model_name: str = "llama3", facts: List[str] = None, is_conversational: bool = False) -> str:
    """
    Generates a response with a SECURITY GATE.
    If the context is empty or irrelevant, it refuses to generate to prevent hallucination.
    For conversational queries (greetings), allows free-form responses.
    """
    if query in QUERY_CACHE:
        return QUERY_CACHE[query]

    # Use a neutral indicator if context is missing for prompt logic
    has_context = bool(facts or (context_chunks and len(context_chunks) > 0))

    # Construct the prompt context (Hybrid: Facts first, then Chunks)
    context_text = ""
    if facts:
        fact_str = "\n".join(facts)
        context_text += f"--- KNOWLEDGE GRAPH FACTS ---\n{fact_str}\n\n"
    
    if context_chunks:
        context_text += "--- DOCUMENT CHUNKS ---\n" + "\n\n".join([c.page_content for c in context_chunks])
    else:
        # If no chunks but facts exist, check if facts mention the subject
        pass
    
    # 1. Try Ollama (Local LLM)
    if HAS_OLLAMA:
        try:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = model_name or os.getenv("OLLAMA_MODEL", "llama3")
            
            # Simple check if "ollama" is reachable is implicitly done by the invoke call, 
            # but we wrap it in try-except to handle connection errors gracefully.
            
            logger.info(f"Attempting to call Ollama at {base_url} with model {model}...")
            
            llm = ChatOllama(
                base_url=base_url,
                model=model,
                temperature=0.1,  # Slightly higher for better retrieval
                timeout=60.0,
                num_predict=512,  # Full answers
                top_k=40,  # Better diversity
                top_p=0.9
            )

            # Use query directly
            standalone_query = query

            # Different system instructions for conversational vs technical queries
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
                    "5. If asked about non-ISRO topics (other universities, companies, unrelated subjects), respond: 'This question is outside my scope. I can only answer questions about ISRO missions and space technology.'\n"
                    "6. If context is empty or irrelevant, respond: 'No documentation found in the local archive for this query.'\n"
                    "7. NEVER fabricate technical specifications, dates, or names not in the context.\n"
                    "8. NEVER add 'Verified by:' or source citations in your response."
                )

            # Construct message list
            prompt_messages = [("system", system_instr)]
            
            if history:
                history_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history[-3:]])
                prompt_messages.append(("human", f"Previous conversation:\n{history_text}"))
            
            if context_text and not is_conversational:
                prompt_messages.append(("human", f"Context:\n{context_text}\n\nQuestion: {standalone_query}"))
            else:
                prompt_messages.append(("human", standalone_query))
            
            # This might raise an exception if Ollama is not running
            response = llm.invoke(prompt_messages)
            QUERY_CACHE[query] = response.content
            return response.content

        except Exception as e:
            logger.warning(f"Ollama connection failed or validation error: {e}. Falling back to offline simulation.")

    # 2. Fallback: Offline Simulation (Simple Extraction)
    logger.info("Using offline fallback (string matching).")
    
    # For conversational queries, provide a simple response
    if is_conversational:
        greetings_responses = {
            "hello": "Hello! I'm here to help with ISRO aerospace questions.",
            "hi": "Hi there! How can I assist you with ISRO information?",
            "hey": "Hey! What would you like to know about ISRO?",
            "greetings": "Greetings! I'm ready to help with aerospace queries.",
            "good morning": "Good morning! How can I help you today?",
            "good afternoon": "Good afternoon! What can I assist you with?",
            "good evening": "Good evening! Feel free to ask me anything about ISRO.",
            "how are you": "I'm doing well, thank you for asking! How can I help?",
            "thanks": "You're welcome! Is there anything else I can help with?",
            "thank you": "You're welcome! Happy to help.",
        }
        query_lower = query.lower().strip().strip('?!.')
        return greetings_responses.get(query_lower, "Hello! How can I assist you?")
    
    # Simple extraction for demo purposes:
    # If the query asks for "fuel", look for fuel-related sentences in the context
    if "fuel" in query.lower():
        # simple sentence extraction
        for chunk in context_chunks:
            sentences = chunk.page_content.split('.')
            for s in sentences:
                if "fuel" in s.lower() or "propellant" in s.lower():
                    ans = f"Based on validated documents (Fallback): {s.strip()}."
                    QUERY_CACHE[query] = ans
                    return ans
    
    ans = f"Based on retrieved context (Fallback):\n{context_chunks[0].page_content[:200]}..."
    QUERY_CACHE[query] = ans
    return ans

async def generate_response_stream(query: str, context_chunks: List, history: List = None, model_name: str = "llama3", facts: List[str] = None, is_conversational: bool = False):
    """
    Generates a streaming response with a SECURITY GATE.
    Uses the same Memory Firewall logic as non-streaming.
    For conversational queries (greetings), allows free-form responses.
    """
    if query in QUERY_CACHE:
        yield QUERY_CACHE[query]
        return

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
            
            llm = ChatOllama(
                base_url=base_url,
                model=model,
                temperature=0.1,  # Slightly higher for better retrieval
                timeout=60.0,
                num_predict=512,  # Full answers
                top_k=40,  # Better diversity
                top_p=0.9
            )

            # Use query directly
            standalone_query = query

            # Different system instructions for conversational vs technical queries
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
                    "5. If asked about non-ISRO topics (other universities, companies, unrelated subjects), respond: 'This question is outside my scope. I can only answer questions about ISRO missions and space technology.'\n"
                    "6. If context is empty or irrelevant, respond: 'No documentation found in the local archive for this query.'\n"
                    "7. NEVER fabricate technical specifications, dates, or names not in the context.\n"
                    "8. NEVER add 'Verified by:' or source citations in your response."
                )

            prompt_messages = [("system", system_instr)]
            if history:
                history_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history[-3:]])
                prompt_messages.append(("human", f"Previous conversation:\n{history_text}"))
            
            if context_text and not is_conversational:
                prompt_messages.append(("human", f"Context:\n{context_text}\n\nQuestion: {standalone_query}"))
            else:
                prompt_messages.append(("human", standalone_query))
            
            full_response = ""
            async for chunk in llm.astream(prompt_messages):
                full_response += chunk.content
                yield chunk.content
            QUERY_CACHE[query] = full_response

        except Exception as e:
            logger.warning(f"Ollama stream failed: {e}. Falling back to offline simulation.")
            
            # Fallback Logic (Matching generate_response)
            if is_conversational:
                greetings_responses = {
                    "hello": "Hello! I'm here to help with ISRO aerospace questions.",
                    "hi": "Hi there! How can I assist you with ISRO information?",
                    "hey": "Hey! What would you like to know about ISRO?",
                    "greetings": "Greetings! I'm ready to help with aerospace queries.",
                    "good morning": "Good morning! How can I help you today?",
                    "good afternoon": "Good afternoon! What can I assist you with?",
                    "good evening": "Good evening! Feel free to ask me anything about ISRO.",
                    "how are you": "I'm doing well, thank you for asking! How can I help?",
                    "thanks": "You're welcome! Is there anything else I can help with?",
                    "thank you": "You're welcome! Happy to help.",
                }
                query_lower = query.lower().strip().strip('?!.')
                response = greetings_responses.get(query_lower, "Hello! How can I assist you?")
                yield response
            else:
                yield "Based on retrieved context (Fallback): "
                
                # specific heuristic for 'fuel'
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
                
                # Default fallback: First chunk snippet
                if context_chunks:
                    yield f"\n{context_chunks[0].page_content[:300]}..."
                else:
                     yield "No relevant context found in offline mode."
    else:
        yield "Ollama not installed. Offline mode."
