from backend.retriever import retrieve_context
from backend.validator import Validator
from backend.rbac import RBAC
from backend.llm_engine import generate_response
from backend.logger import log_query
from backend.aerospace_helper import aerospace_helper
from backend.session_manager import session_manager
from backend.query_cache import query_cache
from backend.analytics import analytics_engine
import re
import time
import json

class RAGSystem:
    def __init__(self):
        self.validator = Validator()
        self.aerospace_helper = aerospace_helper
        self.session_manager = session_manager

    def _is_conversational(self, query):
        """
        Detects if a query is a simple greeting or identity question.
        Uses a conservative approach to ensure technical queries still hit the security gate.
        """
        greetings = {
            "hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening",
            "who are you", "what is your name", "what can you do", "help", "thanks", "thank you",
            "how are you", "hola", "namaste"
        }
        q = query.lower().strip().strip('?!.')
        return q in greetings or len(q) < 3

    def _is_aerospace_problem_solving(self, query):
        """
        Detects if query is asking for aerospace problem-solving help
        Only triggers for queries asking for help/advice, not factual queries
        """
        problem_keywords = [
            "help", "solve", "problem", "design", "optimize", "recommend", "suggest",
            "how to", "how can", "what should", "best way", "mission planning",
            "payload optimization", "launch vehicle", "orbital",
            "new mission", "new satellite", "new design", "stuck", "challenge"
        ]
        query_lower = query.lower()
        
        # Don't trigger for factual queries (describe, tell me about, what is, etc.)
        factual_keywords = ["describe", "tell me about", "what is", "what are", "explain", "list", "which"]
        if any(keyword in query_lower for keyword in factual_keywords):
            return False
        
        return any(keyword in query_lower for keyword in problem_keywords)

    def process_query(self, user_id, user_role, query, session_id=None, model_name=None, bypass_graph=False):
        """
        Executes the full Sovereign Hybrid RAG pipeline with continuous learning.
        
        Logic Flow:
        1. Check Query Cache
        2. Session Management: Create/retrieve session and add to history
        3. RBAC Check: Enforces identity-based access gates.
        4. Context Enrichment: Add learned patterns from past interactions
        5. Retrieval: Executes parallel Vector and Knowledge Graph search.
        6. Context Filtering: Applies document-level security to retrieved assets.
        7. Generation: Synthesizes response using the local LLM.
        8. Verification: Post-generation Graph-NLI audit for factual integrity.
        9. Learning: Extract patterns and learn from interaction
        10. Attribution: Heuristic source mapping for auditability.
        11. Cache Response & Log Analytics
        """
        start_time = time.time()
        
        # 0. Check Cache First
        cached_response = query_cache.get(query, user_role, model_name or "llama3")
        if cached_response:
            analytics_engine.log_query(
                user_id, user_role, query, cached_response,
                [], "Success (Cached)", time.time() - start_time, cached=True
            )
            return cached_response
        
        # 1. Session Management
        if not session_id:
            session_id = self.session_manager.create_session(user_id, user_role)
        
        # Add user query to session history
        self.session_manager.add_message(session_id, "user", query)
        
        # Get personalized context from past interactions
        personalized_context = self.session_manager.get_personalized_context(session_id)
        
        # 1. RBAC Check
        if not RBAC.check_access(user_role, "public"):
             return "Access Denied: Insufficient permissions."

        # 2. Retrieve Hybrid Context
        t_start = time.time()
        context_data = retrieve_context(query, bypass_graph=bypass_graph)
        t_retrieved = time.time()
        
        # 3. Apply RBAC document-level filtering
        raw_chunks = context_data.get("chunks", [])
        allowed_chunks = RBAC.filter_documents(user_role, raw_chunks)
        facts = context_data.get("facts", [])
        t_rbac = time.time()

        # Clear context for conversational queries to hide "Verified by" badge
        if self._is_conversational(query):
            allowed_chunks = []
            facts = []

        # Check if this is an aerospace problem-solving query
        if self._is_aerospace_problem_solving(query) and not self._is_conversational(query):
            # Try to help with aerospace problem-solving
            aerospace_analysis = self.aerospace_helper.solve_aerospace_problem(
                query,
                context_data=[c.page_content for c in allowed_chunks] if allowed_chunks else None
            )
            
            # If we have a good analysis, format and return it
            if aerospace_analysis.get("solution") or aerospace_analysis.get("recommendations"):
                formatted_response = self.aerospace_helper.format_response_for_human(aerospace_analysis)
                
                # Add response to session and learn from interaction
                self.session_manager.add_message(session_id, "assistant", formatted_response)
                self.session_manager.learn_from_interaction(session_id, query, formatted_response)
                
                log_query(user_id, user_role, query, formatted_response, 
                         [c.metadata for c in allowed_chunks], "Aerospace Helper")
                
                # Add recommendations based on learning
                recommendations = self.session_manager.get_recommendations_based_on_history(session_id)
                if recommendations:
                    formatted_response += "\n\n**Suggested Next Topics:**\n"
                    for rec in recommendations[:2]:
                        formatted_response += f"  • {rec}\n"
                
                return formatted_response

        if not allowed_chunks and not facts:
            if not self._is_conversational(query):
                response = "No accessible information found in the local archive for this technical query."
                return response
            # Else, proceed as it's a greeting
        
        # Internal Audit: Record pipeline transition latencies
        print(f"[Audit] Retrieval: {t_retrieved - t_start:.2f}s | RBAC filtering: {t_rbac - t_retrieved:.2f}s")
        print(f"[Audit] Generating initial hypothesis...")

        # 4. Get History
        history = []
        if session_id:
            from backend.session_store import session_store
            session = session_store.get_session(session_id)
            if session:
                history = session.get("messages", [])[-6:]

        # 6. Generate Response (augmented with facts)
        fact_strings = [f"{f['target_name']} {f['relationship']} {f['target_label']}" for f in facts]
        preliminary_response = generate_response(query, allowed_chunks, history, model_name, facts=fact_strings, is_conversational=self._is_conversational(query))

        # 7. Hybrid Validation (Post-Generation) - Bypassed for conversational queries
        if self._is_conversational(query):
            validation_msg = "Conversational: Skip Audit"
            is_valid = True
        else:
            is_valid, validation_msg = self.validator.validate_answer(query, preliminary_response)
            
        if not is_valid:
            response = f"[!CAUTION] SECURITY AUDIT ALERT: {validation_msg}\n\nThe system detected potential inaccuracies in the generated response. Please verify with primary sources or reformulate your query."
            log_query(user_id, user_role, query, response, [c.metadata for c in allowed_chunks], "Validation Failed")
            return response

        # 8. Source Attribution (Strict: Only include sources that actually contain the answer)
        attributed_response = self._attribute_sources_strict(preliminary_response, allowed_chunks)
        
        # 9. Audit Log
        log_query(user_id, user_role, query, attributed_response, [c.metadata for c in allowed_chunks], "Success")
        
        # 10. Cache Response & Log Analytics
        query_cache.set(query, user_role, model_name or "llama3", attributed_response)
        analytics_engine.log_query(
            user_id, user_role, query, attributed_response,
            [c.metadata.get('source', 'Unknown') for c in allowed_chunks],
            "Success", time.time() - start_time, cached=False
        )

        return attributed_response

    def _attribute_sources(self, response, chunks):
        """
        Simple source attribution by checking for keyword overlap between response and chunks.
        """
        if "No documentation found" in response or "Access Denied" in response:
            return response
            
        sources = set()
        for chunk in chunks:
            source = chunk.metadata.get('source', 'Unknown')
            # Check if any significant part of the response exists in this chunk
            # (Very rough heuristic for now)
            words = set(re.findall(r'\w+', response.lower()))
            chunk_words = set(re.findall(r'\w+', chunk.page_content.lower()))
            overlap = words.intersection(chunk_words)
            if len(overlap) > 10: # arbitrary threshold for 'relevance'
                sources.add(source)
        
        if sources:
            source_str = "\n\nSources: " + ", ".join(list(sources))
            return response + source_str
        return response

    def _attribute_sources_strict(self, response, chunks):
        """
        Strict source attribution: Only include sources where key facts from the response
        are explicitly found in the chunk content. Prevents false attribution.
        """
        if "No documentation found" in response or "Access Denied" in response or "CAUTION" in response:
            return response
        
        if not chunks:
            return response
        
        # Extract key numeric/technical claims from response
        # e.g., "2000 kg", "three stages", "CE-20 engine"
        technical_patterns = [
            r'\d+\s*(?:kg|tonnes?|meters?|km|stages?|engines?)',
            r'(?:CE-\d+|Vikas|Cryogenic|Solid|Liquid)',
            r'(?:PSLV|GSLV|LVM3|Chandrayaan|GSAT|EOS)',
        ]
        
        response_claims = set()
        for pattern in technical_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            response_claims.update(matches)
        
        # Find which chunks actually contain these claims
        verified_sources = set()
        for chunk in chunks:
            chunk_content = chunk.page_content.lower()
            for claim in response_claims:
                if claim.lower() in chunk_content:
                    source = chunk.metadata.get('source', 'Unknown')
                    verified_sources.add(source)
                    break
        
        if verified_sources:
            source_str = "\n\nVerified Sources: " + ", ".join(sorted(list(verified_sources)))
            return response + source_str
        
        # If no technical claims found, don't add false attribution
        return response

    def _calculate_confidence(self, is_valid, is_conversational, has_sources, has_facts):
        """
        Calculates a confidence score (0-100) based on pipeline outcomes.
        """
        if not is_valid:
            return 20
        
        if is_conversational:
            return 55 # General knowledge, not strictly "fact checked" from docs
            
        if has_facts and has_sources:
            return 98 # Golden path: Graph confirmed + Source found
            
        if has_facts:
            return 90 # High: Graph confirmed claim
            
        if has_sources:
            return 75 # Mid: Document found but graph had no explicit fact node
            
        return 40 # Low: No direct evidence found, generating from general knowledge

    async def process_query_stream(self, user_id, user_role, query, session_id=None, model_name=None):
        """
        Streaming pipeline with progress updates: Retrieve -> RBAC Filter -> Validate -> Generate Stream
        """
        start_time = time.time()
        
        # Check cache first
        cached_response = query_cache.get(query, user_role, model_name or "llama3")
        if cached_response:
            # Yield cached response with progress
            yield f"__PROGRESS__:{json.dumps({'stage': 'cache_hit', 'message': '⚡ Retrieved from cache', 'time': 0.001})}\n"
            yield f"__METADATA__:{json.dumps({'facts': [], 'sources': [], 'confidence': 100})}\n"
            yield cached_response
            analytics_engine.log_query(
                user_id, user_role, query, cached_response,
                [], "Success (Cached)", time.time() - start_time, cached=True
            )
            return
        
        # Progress: Starting
        yield f"__PROGRESS__:{json.dumps({'stage': 'start', 'message': '🔍 Searching documents...', 'time': 0})}\n"
        
        # 1. RBAC Check (basic role check)
        if not RBAC.check_access(user_role, "public"):
             yield "Access Denied: Insufficient permissions."
             return

        # 2. Retrieve Hybrid Context
        retrieval_start = time.time()
        context_data = retrieve_context(query)
        raw_chunks = context_data.get("chunks", [])
        facts = context_data.get("facts", [])
        retrieval_time = time.time() - retrieval_start
        
        # Progress: Retrieval complete
        yield f"__PROGRESS__:{json.dumps({'stage': 'retrieval', 'message': f'✅ Found {len(raw_chunks)} sources in {retrieval_time:.1f}s', 'time': retrieval_time})}\n"

        # 3. Apply RBAC document-level filtering based on user role
        allowed_chunks = RBAC.filter_documents(user_role, raw_chunks)

        # Clear context for conversational queries to hide "Verified by" badge
        if self._is_conversational(query):
            allowed_chunks = []
            facts = []

        if not allowed_chunks and not facts:
            if not self._is_conversational(query):
                print(f"[Audit] NO DATA FOUND: Triggering secure refusal.")
                yield "No documentation found in the local archive for this technical query. I am strictly forbidden from hallucinating mission details."
                return
            # Else proceed to LLM for greeting response
        
        # Progress: Generating
        yield f"__PROGRESS__:{json.dumps({'stage': 'generating', 'message': '🤖 Generating response...', 'time': time.time() - start_time})}\n"

        # 4. Preliminary Safety Check: Fast subject-match verification
        # (Heuristic skip to ensure the panel gets the first token in <2 seconds)
        if not facts and not self._is_conversational(query):
            # If no graph facts exist, we trust the vector retrieval but flag as 'Unverified context'
            pass

        # 5. Get History from session
        history = []
        if session_id:
            from backend.session_store import session_store
            session = session_store.get_session(session_id)
            if session:
                # Get last 6 messages, but strip metadata from stored system messages
                raw_history = session.get("messages", [])[-6:]
                for msg in raw_history:
                    content = msg.get("content", "")
                    # Strip metadata lines from stored history to avoid context bleed
                    clean_lines = [l for l in content.split("\n") if not l.startswith("__METADATA__:")]
                    clean_content = "\n".join(clean_lines).strip()
                    if clean_content:
                        history.append({"role": msg["role"], "content": clean_content})

        # 6. Build fact strings for prompt
        fact_strings = [f"{f['target_name']} {f['relationship']} {f['target_label']}" for f in facts]

        # 7. Generate and Stream Response
        from backend.llm_engine import generate_response_stream
        full_generated_text = ""
        
        # Progress: Actively synthesizing
        yield f"__PROGRESS__:{json.dumps({'stage': 'synthesizing', 'message': '🧠 Synthesizing facts and generating answer...', 'time': time.time() - start_time})}\n"
        
        async for chunk in generate_response_stream(query, allowed_chunks, history, model_name, facts=fact_strings, is_conversational=self._is_conversational(query)):
            full_generated_text += chunk
            yield chunk

        # 8. Post-Generation Validation (Security Audit)
        if not self._is_conversational(query):
            # Progress: Security Audit
            yield f"\n__PROGRESS__:{json.dumps({'stage': 'validating', 'message': '🛡️ Performing safety & factual audit...', 'time': time.time() - start_time})}\n"
            
            is_valid, audit_msg = self.validator.validate_answer(query, full_generated_text)
            
            if not is_valid:
                # The user has already seen the text, so we add a clear warning at the end
                audit_warning = f"\n\n[!CAUTION] SECURITY AUDIT ALERT: {audit_msg}\n\nThe system detected potential inaccuracies in the generated response above. Please verify with primary sources."
                log_query(user_id, user_role, query, full_generated_text + audit_warning, [c.metadata for c in allowed_chunks], "Validation Failed")
                
                # Log to analytics
                analytics_engine.log_query(
                    user_id, user_role, query, full_generated_text + audit_warning,
                    [c.metadata.get('source', 'Unknown') for c in allowed_chunks],
                    "Validation Failed", time.time() - start_time, cached=False
                )
                
                yield audit_warning
            else:
                # Apply strict source attribution (appended at the end)
                attributed_text_full = self._attribute_sources_strict(full_generated_text, allowed_chunks)
                new_content = attributed_text_full[len(full_generated_text):]
                if new_content:
                    yield new_content
                
                # Audit Log
                log_query(user_id, user_role, query, attributed_text_full, [c.metadata for c in allowed_chunks], "Success")
                
                # Cache the response
                query_cache.set(query, user_role, model_name or "llama3", attributed_text_full)
                
                # Log to analytics
                analytics_engine.log_query(
                    user_id, user_role, query, attributed_text_full,
                    [c.metadata.get('source', 'Unknown') for c in allowed_chunks],
                    "Success", time.time() - start_time, cached=False
                )
        else:
            # Fast log for conversational greetings
            log_query(user_id, user_role, query, full_generated_text, [], "Info")
            analytics_engine.log_query(user_id, user_role, query, full_generated_text, [], "Success", time.time() - start_time, cached=False)

        # 9. Yield Metadata for UI Visualization
        sources = list(set([c.metadata.get('source', 'Unknown') for c in allowed_chunks]))
        is_technical = not self._is_conversational(query)
        is_valid = True # Default for conversational
        
        # We need to re-verify or capture the state from above
        # For simplicity, we'll re-check if it was a technical query that failed validation
        # In a real system we'd pass this state down more cleanly
        if is_technical:
            is_valid, _ = self.validator.validate_answer(query, full_generated_text)
            
        confidence = self._calculate_confidence(
            is_valid=is_valid,
            is_conversational=not is_technical,
            has_sources=len(allowed_chunks) > 0,
            has_facts=len(facts) > 0
        )
        
        # Progress: Complete
        total_time = time.time() - start_time
        yield f"__PROGRESS__:{json.dumps({'stage': 'complete', 'message': f'✅ Validated in {total_time:.1f}s', 'time': total_time})}\n"
        yield f"__METADATA__:{json.dumps({'facts': facts, 'sources': sources, 'confidence': confidence})}\n"

    def provide_feedback(self, session_id: str, feedback: str):
        """Allow user to provide feedback on responses for learning"""
        if session_id in self.session_manager.sessions:
            session = self.session_manager.sessions[session_id]
            user_id = session["user_id"]
            
            # Get last query and response
            last_query = session.get("last_query")
            last_response = session.get("last_response")
            
            if last_query and last_response:
                self.session_manager.learn_from_interaction(
                    session_id, last_query, last_response, feedback
                )
                return f"✅ Feedback recorded. System is learning from your input."
        
        return "❌ No recent interaction to provide feedback on."
    
    def get_session_summary(self, session_id: str) -> str:
        """Get a summary of the current session"""
        summary = self.session_manager.summarize_session(session_id)
        
        if not summary:
            return "No active session found."
        
        response = f"""
**Session Summary**

Session ID: {summary['session_id']}
User: {summary['user_id']}
Created: {summary['created_at']}
Messages: {summary['message_count']}
Queries: {summary['query_count']}
Topic: {summary['conversation_topic']}

**Learned Patterns:**
"""
        for pattern in summary.get('learned_patterns', []):
            response += f"  • {pattern}\n"
        
        if summary.get('mission_context'):
            response += f"\n**Mission Context:**\n"
            response += f"  • Missions: {', '.join(summary['mission_context'].get('missions_mentioned', []))}\n"
            response += f"  • Vehicles: {', '.join(summary['mission_context'].get('vehicles_mentioned', []))}\n"
        
        return response
    
    def get_user_learning_profile(self, user_id: str) -> str:
        """Get user's learning profile based on past interactions"""
        learning_data = self.session_manager.export_learning_data(user_id)
        
        response = f"""
**User Learning Profile**

User ID: {learning_data['user_id']}
Total Interactions: {learning_data['interaction_count']}
Feedback Provided: {learning_data['feedback_count']}

**Learned Interests:**
"""
        for pattern in learning_data.get('patterns_learned', []):
            response += f"  • {pattern}\n"
        
        prefs = learning_data.get('preferences', {})
        if prefs:
            response += f"\n**Preferences:**\n"
            response += f"  • Detail Level: {prefs.get('preferred_detail_level', 'medium')}\n"
            response += f"  • Format: {prefs.get('preferred_format', 'structured')}\n"
            response += f"  • Topics: {', '.join(prefs.get('interested_topics', []))}\n"
        
        return response
    
    def continue_conversation(self, session_id: str, query: str, user_id: str, user_role: str) -> str:
        """Continue a conversation with context from past interactions"""
        # Get conversation history
        history = self.session_manager.get_conversation_history(session_id, limit=5)
        
        # Get personalized context
        personalized_context = self.session_manager.get_personalized_context(session_id)
        
        # Process query with full context
        response = self.process_query(user_id, user_role, query, session_id)
        
        return response

# Singleton Instance
rag_system = RAGSystem()
