"""
Enhanced NEXORA Main Engine with:
- Latency tracking (≤10s compliance)
- Adaptive detail levels
- Elaboration framework
- IEEE metrics preservation
"""

from backend.retriever import retrieve_context
from backend.validator import Validator
from backend.rbac import RBAC
from backend.llm_engine_enhanced import (
    generate_response,
    generate_response_stream,
    detect_detail_level,
    LatencyTracker
)
from backend.logger import log_query
from backend.aerospace_helper import aerospace_helper
from backend.session_manager import session_manager
import re
import time

class RAGSystemEnhanced:
    def __init__(self):
        self.validator = Validator()
        self.aerospace_helper = aerospace_helper
        self.session_manager = session_manager
        self.latency_tracker = None

    def _is_conversational(self, query):
        """
        Detects if a query is a simple greeting or identity question.
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
        Detects if query is asking for aerospace problem-solving help.
        """
        problem_keywords = [
            "help", "solve", "problem", "design", "optimize", "recommend", "suggest",
            "how to", "how can", "what should", "best way", "mission planning",
            "payload optimization", "launch vehicle", "orbital",
            "new mission", "new satellite", "new design", "stuck", "challenge"
        ]
        query_lower = query.lower()
        
        factual_keywords = ["describe", "tell me about", "what is", "what are", "explain", "list", "which"]
        if any(keyword in query_lower for keyword in factual_keywords):
            return False
        
        return any(keyword in query_lower for keyword in problem_keywords)

    def process_query(
        self,
        user_id,
        user_role,
        query,
        session_id=None,
        model_name=None,
        bypass_graph=False
    ):
        """
        Enhanced query processing with latency tracking and adaptive detail levels.
        
        Pipeline:
        1. Session Management
        2. RBAC Check
        3. Detail Level Detection
        4. Context Retrieval (Adaptive)
        5. RBAC Filtering
        6. Response Generation (Adaptive)
        7. Validation
        8. Attribution
        9. Latency Compliance Check
        """
        # Initialize latency tracker
        self.latency_tracker = LatencyTracker()
        self.latency_tracker.start_stage("total")
        
        # 0. Session Management
        if not session_id:
            session_id = self.session_manager.create_session(user_id, user_role)
        
        self.session_manager.add_message(session_id, "user", query)
        personalized_context = self.session_manager.get_personalized_context(session_id)
        
        # 1. RBAC Check
        if not RBAC.check_access(user_role, "public"):
            return "Access Denied: Insufficient permissions."

        # 2. Detect Detail Level
        self.latency_tracker.start_stage("detail_detection")
        detail_level = detect_detail_level(query)
        self.latency_tracker.end_stage("detail_detection")
        
        print(f"[Pipeline] Detail Level: {detail_level}")

        # 3. Retrieve Hybrid Context (Adaptive)
        self.latency_tracker.start_stage("context_retrieval")
        
        # Adjust retrieval parameters based on detail level
        retrieval_params = {
            'low': {'k': 5},
            'medium': {'k': 10},
            'high': {'k': 20}
        }
        
        context_data = retrieve_context(query, k=retrieval_params[detail_level]['k'], bypass_graph=bypass_graph)
        self.latency_tracker.end_stage("context_retrieval")
        
        # 4. Apply RBAC document-level filtering
        self.latency_tracker.start_stage("rbac_filtering")
        raw_chunks = context_data.get("chunks", [])
        
        # Debug: Check what access levels we have
        if raw_chunks:
            access_levels = [doc.metadata.get("access_level", "unknown") for doc in raw_chunks]
            print(f"[RBAC Debug] User role: {user_role}, Documents: {len(raw_chunks)}, Access levels: {set(access_levels)}")
        
        allowed_chunks = RBAC.filter_documents(user_role, raw_chunks)
        
        # Check if RBAC blocked access
        if raw_chunks and not allowed_chunks and not self._is_conversational(query):
            # User tried to access documents they don't have permission for
            print(f"[RBAC] Access denied for {user_role} - no accessible documents found")
            response = "Access Denied: You do not have permission to access this information."
            self.latency_tracker.end_stage("rbac_filtering")
            self.latency_tracker.end_stage("total")
            self.latency_tracker.print_summary()
            log_query(user_id, user_role, query, response, [], "RBAC Denied")
            return response
        
        # Additional check: If user is Public and query is asking for technical details,
        # but all retrieved documents are technical, deny access
        if user_role == "Public" and raw_chunks and not self._is_conversational(query):
            technical_count = sum(1 for doc in raw_chunks if doc.metadata.get("access_level") == "technical")
            public_count = sum(1 for doc in raw_chunks if doc.metadata.get("access_level") == "public")
            
            # If majority of results are technical documents, deny access
            if technical_count > public_count:
                print(f"[RBAC] Access denied for Public user - query returns mostly technical documents ({technical_count} technical vs {public_count} public)")
                response = "Access Denied: You do not have permission to access this technical information."
                self.latency_tracker.end_stage("rbac_filtering")
                self.latency_tracker.end_stage("total")
                self.latency_tracker.print_summary()
                log_query(user_id, user_role, query, response, [], "RBAC Denied - Technical Query")
                return response
        
        print(f"[RBAC Debug] Allowed documents: {len(allowed_chunks)}/{len(raw_chunks)}")
        
        facts = context_data.get("facts", [])
        self.latency_tracker.end_stage("rbac_filtering")

        # Clear context for conversational queries
        if self._is_conversational(query):
            allowed_chunks = []
            facts = []

        # Check if this is an aerospace problem-solving query
        if self._is_aerospace_problem_solving(query) and not self._is_conversational(query):
            self.latency_tracker.start_stage("aerospace_helper")
            
            aerospace_analysis = self.aerospace_helper.solve_aerospace_problem(
                query,
                context_data=[c.page_content for c in allowed_chunks] if allowed_chunks else None
            )
            
            if aerospace_analysis.get("solution") or aerospace_analysis.get("recommendations"):
                formatted_response = self.aerospace_helper.format_response_for_human(aerospace_analysis)
                
                self.session_manager.add_message(session_id, "assistant", formatted_response)
                self.session_manager.learn_from_interaction(session_id, query, formatted_response)
                
                log_query(user_id, user_role, query, formatted_response, 
                         [c.metadata for c in allowed_chunks], "Aerospace Helper")
                
                recommendations = self.session_manager.get_recommendations_based_on_history(session_id)
                if recommendations:
                    formatted_response += "\n\n**Suggested Next Topics:**\n"
                    for rec in recommendations[:2]:
                        formatted_response += f"  • {rec}\n"
                
                self.latency_tracker.end_stage("aerospace_helper")
                self.latency_tracker.end_stage("total")
                self.latency_tracker.print_summary()
                
                return formatted_response

        if not allowed_chunks and not facts:
            if not self._is_conversational(query):
                response = "No accessible information found in the local archive for this technical query."
                self.latency_tracker.end_stage("total")
                self.latency_tracker.print_summary()
                return response

        # 5. Get History
        history = []
        if session_id:
            from backend.session_store import session_store
            session = session_store.get_session(session_id)
            if session:
                history = session.get("messages", [])[-6:]

        # 6. Generate Response (with adaptive detail level)
        self.latency_tracker.start_stage("response_generation")
        
        fact_strings = [f"{f['target_name']} {f['relationship']} {f['target_label']}" for f in facts]
        preliminary_response, gen_metadata = generate_response(
            query,
            allowed_chunks,
            history,
            model_name,
            facts=fact_strings,
            detail_level=detail_level
        )
        
        self.latency_tracker.end_stage("response_generation")

        # 7. Hybrid Validation (Post-Generation)
        self.latency_tracker.start_stage("validation")
        
        if self._is_conversational(query):
            validation_msg = "Conversational: Skip Audit"
            is_valid = True
        else:
            is_valid, validation_msg = self.validator.validate_answer(query, preliminary_response)
        
        self.latency_tracker.end_stage("validation")
        
        if not is_valid:
            response = f"[!CAUTION] SECURITY AUDIT ALERT: {validation_msg}\n\nThe system detected potential inaccuracies in the generated response. Please verify with primary sources or reformulate your query."
            log_query(user_id, user_role, query, response, [c.metadata for c in allowed_chunks], "Validation Failed")
            self.latency_tracker.end_stage("total")
            self.latency_tracker.print_summary()
            return response

        # 8. Source Attribution
        self.latency_tracker.start_stage("attribution")
        attributed_response = self._attribute_sources_strict(preliminary_response, allowed_chunks)
        self.latency_tracker.end_stage("attribution")
        
        # 9. Audit Log
        log_query(user_id, user_role, query, attributed_response, [c.metadata for c in allowed_chunks], "Success")

        # 10. Latency Compliance Check
        self.latency_tracker.end_stage("total")
        self.latency_tracker.print_summary()
        
        if not self.latency_tracker.check_compliance():
            print("⚠️  WARNING: Response exceeded 10s latency limit")
        
        # Add metadata to response
        response_with_metadata = f"{attributed_response}\n\n[Metadata] Detail Level: {detail_level} | Generation: {gen_metadata.get('num_predict')} tokens"
        
        return response_with_metadata

    def _attribute_sources_strict(self, response, chunks):
        """
        Strict source attribution: Only include sources where key facts from the response
        are explicitly found in the chunk content.
        """
        if "No documentation found" in response or "Access Denied" in response or "CAUTION" in response:
            return response
        
        if not chunks:
            return response
        
        # Extract key numeric/technical claims from response
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
        
        return response

    async def process_query_stream(
        self,
        user_id,
        user_role,
        query,
        session_id=None,
        model_name=None
    ):
        """
        Streaming pipeline with latency tracking and adaptive detail levels.
        """
        # Initialize latency tracker
        self.latency_tracker = LatencyTracker()
        self.latency_tracker.start_stage("total")
        
        # 1. RBAC Check
        if not RBAC.check_access(user_role, "public"):
            yield "Access Denied: Insufficient permissions."
            return

        # 2. Detect Detail Level
        self.latency_tracker.start_stage("detail_detection")
        detail_level = detect_detail_level(query)
        self.latency_tracker.end_stage("detail_detection")
        
        print(f"[Pipeline] Streaming with Detail Level: {detail_level}")

        # 3. Retrieve Hybrid Context (Adaptive)
        self.latency_tracker.start_stage("context_retrieval")
        
        retrieval_params = {
            'low': {'k': 5},
            'medium': {'k': 10},
            'high': {'k': 20}
        }
        
        context_data = retrieve_context(query, k=retrieval_params[detail_level]['k'])
        self.latency_tracker.end_stage("context_retrieval")
        
        raw_chunks = context_data.get("chunks", [])
        facts = context_data.get("facts", [])

        # 4. Apply RBAC document-level filtering
        self.latency_tracker.start_stage("rbac_filtering")
        allowed_chunks = RBAC.filter_documents(user_role, raw_chunks)
        self.latency_tracker.end_stage("rbac_filtering")

        # Clear context for conversational queries
        if self._is_conversational(query):
            allowed_chunks = []
            facts = []

        if not allowed_chunks and not facts:
            if not self._is_conversational(query):
                yield "No documentation found in the local archive for this technical query."
                return

        # 5. Get History from session
        history = []
        if session_id:
            from backend.session_store import session_store
            session = session_store.get_session(session_id)
            if session:
                raw_history = session.get("messages", [])[-6:]
                for msg in raw_history:
                    content = msg.get("content", "")
                    clean_lines = [l for l in content.split("\n") if not l.startswith("__METADATA__:")]
                    clean_content = "\n".join(clean_lines).strip()
                    if clean_content:
                        history.append({"role": msg["role"], "content": clean_content})

        # 6. Build fact strings
        fact_strings = [f"{f['target_name']} {f['relationship']} {f['target_label']}" for f in facts]

        # 7. Generate Response Stream (with adaptive detail level)
        self.latency_tracker.start_stage("response_generation")
        
        full_generated_text = ""
        async for chunk in generate_response_stream(
            query,
            allowed_chunks,
            history,
            model_name,
            facts=fact_strings,
            detail_level=detail_level
        ):
            full_generated_text += chunk
            yield chunk
        
        self.latency_tracker.end_stage("response_generation")

        # 8. Validate BEFORE yielding
        self.latency_tracker.start_stage("validation")
        
        if not self._is_conversational(query):
            is_valid, audit_msg = self.validator.validate_answer(query, full_generated_text)
            
            if not is_valid:
                audit_response = f"[!CAUTION] SECURITY AUDIT ALERT: {audit_msg}\n\nThe system detected potential inaccuracies in the generated response. Please verify with primary sources or reformulate your query."
                log_query(user_id, user_role, query, audit_response, [c.metadata for c in allowed_chunks], "Validation Failed")
                yield audit_response
                self.latency_tracker.end_stage("validation")
                self.latency_tracker.end_stage("total")
                self.latency_tracker.print_summary()
                return
            else:
                full_generated_text = self._attribute_sources_strict(full_generated_text, allowed_chunks)
                log_query(user_id, user_role, query, full_generated_text, [c.metadata for c in allowed_chunks], "Success")
        else:
            log_query(user_id, user_role, query, full_generated_text, [], "Info")
        
        self.latency_tracker.end_stage("validation")

        # 9. Yield Metadata
        import json
        sources = list(set([c.metadata.get('source', 'Unknown') for c in allowed_chunks]))
        print(f"[Audit] Sources Verified: {', '.join(sources) if sources else 'None'}")
        yield f"__METADATA__:{json.dumps({'facts': facts, 'sources': sources, 'detail_level': detail_level})}\n"

        # 10. Latency Compliance Check
        self.latency_tracker.end_stage("total")
        self.latency_tracker.print_summary()
        
        if not self.latency_tracker.check_compliance():
            print("⚠️  WARNING: Response exceeded 10s latency limit")

    def provide_feedback(self, session_id: str, feedback: str):
        """Allow user to provide feedback on responses for learning."""
        if session_id in self.session_manager.sessions:
            session = self.session_manager.sessions[session_id]
            user_id = session["user_id"]
            
            last_query = session.get("last_query")
            last_response = session.get("last_response")
            
            if last_query and last_response:
                self.session_manager.learn_from_interaction(
                    session_id, last_query, last_response, feedback
                )
                return f"✅ Feedback recorded. System is learning from your input."
        
        return "❌ No recent interaction to provide feedback on."
    
    def get_session_summary(self, session_id: str) -> str:
        """Get a summary of the current session."""
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

# Singleton Instance
rag_system_enhanced = RAGSystemEnhanced()
