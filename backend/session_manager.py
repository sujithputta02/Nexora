"""
NEXORA Session Manager
Manages continuous conversations and self-learning from past prompts
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Tuple
from collections import defaultdict

class SessionManager:
    """
    Manages user sessions with:
    - Continuous conversation history
    - Context preservation across queries
    - Self-learning from past interactions
    - Pattern recognition
    - Personalized recommendations
    """
    
    def __init__(self):
        self.sessions = {}  # user_id -> session data
        self.learning_patterns = defaultdict(list)  # user_id -> patterns learned
        self.query_history = defaultdict(list)  # user_id -> all queries
        self.response_feedback = defaultdict(list)  # user_id -> feedback on responses
        self.user_preferences = defaultdict(dict)  # user_id -> preferences
        
    def create_session(self, user_id: str, user_role: str) -> str:
        """Create a new session for a user"""
        session_id = f"{user_id}_{int(time.time())}"
        
        self.sessions[session_id] = {
            "user_id": user_id,
            "user_role": user_role,
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "context": {},
            "mission_context": None,
            "last_query": None,
            "last_response": None,
            "query_count": 0,
            "learning_enabled": True,
        }
        
        print(f"[SessionManager] Created session {session_id} for user {user_id}")
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None):
        """Add a message to session history"""
        if session_id not in self.sessions:
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.sessions[session_id]["messages"].append(message)
        
        # Track in query history
        user_id = self.sessions[session_id]["user_id"]
        self.query_history[user_id].append({
            "query": content if role == "user" else None,
            "response": content if role == "assistant" else None,
            "timestamp": message["timestamp"]
        })
        
        return True
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        if session_id not in self.sessions:
            return []
        
        messages = self.sessions[session_id]["messages"]
        return messages[-limit:] if len(messages) > limit else messages
    
    def get_context_from_history(self, session_id: str) -> Dict:
        """Extract context from conversation history for next query"""
        if session_id not in self.sessions:
            return {}
        
        session = self.sessions[session_id]
        messages = session["messages"]
        
        context = {
            "previous_queries": [],
            "mission_context": session.get("mission_context"),
            "user_preferences": self._get_user_preferences(session["user_id"]),
            "learned_patterns": self._get_learned_patterns(session["user_id"]),
            "conversation_topic": self._identify_topic(messages),
        }
        
        # Extract previous queries for context
        for msg in messages[-5:]:
            if msg["role"] == "user":
                context["previous_queries"].append(msg["content"])
        
        return context
    
    def learn_from_interaction(self, session_id: str, query: str, response: str, feedback: str = None):
        """Learn from user interactions"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        user_id = session["user_id"]
        
        # Extract patterns from query
        patterns = self._extract_patterns(query)
        self.learning_patterns[user_id].extend(patterns)
        
        # Store feedback if provided
        if feedback:
            self.response_feedback[user_id].append({
                "query": query,
                "response": response,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat()
            })
        
        # Update user preferences based on query
        self._update_preferences(user_id, query, response)
        
        # Update mission context if relevant
        if self._is_mission_query(query):
            session["mission_context"] = self._extract_mission_context(query)
        
        session["last_query"] = query
        session["last_response"] = response
        session["query_count"] += 1
    
    def _extract_patterns(self, query: str) -> List[str]:
        """Extract learning patterns from query"""
        patterns = []
        
        # Mission-related patterns
        if "mission" in query.lower():
            patterns.append("interested_in_missions")
        
        if "payload" in query.lower() or "mass" in query.lower():
            patterns.append("interested_in_payload_optimization")
        
        if "orbit" in query.lower() or "orbital" in query.lower():
            patterns.append("interested_in_orbital_mechanics")
        
        if "design" in query.lower() or "satellite" in query.lower():
            patterns.append("interested_in_satellite_design")
        
        if "propulsion" in query.lower() or "engine" in query.lower():
            patterns.append("interested_in_propulsion")
        
        if "help" in query.lower() or "solve" in query.lower():
            patterns.append("seeking_problem_solving_help")
        
        if "compare" in query.lower() or "difference" in query.lower():
            patterns.append("interested_in_comparisons")
        
        if "how" in query.lower() or "what" in query.lower():
            patterns.append("seeking_technical_knowledge")
        
        return patterns
    
    def _is_mission_query(self, query: str) -> bool:
        """Check if query is about a specific mission"""
        mission_keywords = [
            "mission", "chandrayaan", "mangalyaan", "gaganyaan", "aditya",
            "gsat", "pslv", "gslv", "launch", "satellite"
        ]
        return any(keyword in query.lower() for keyword in mission_keywords)
    
    def _extract_mission_context(self, query: str) -> Dict:
        """Extract mission context from query"""
        context = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "missions_mentioned": [],
            "vehicles_mentioned": [],
            "orbits_mentioned": [],
        }
        
        # Extract missions
        missions = ["chandrayaan", "mangalyaan", "gaganyaan", "aditya", "risat", "cartosat"]
        for mission in missions:
            if mission in query.lower():
                context["missions_mentioned"].append(mission)
        
        # Extract vehicles
        vehicles = ["pslv", "gslv", "lvm3"]
        for vehicle in vehicles:
            if vehicle in query.lower():
                context["vehicles_mentioned"].append(vehicle)
        
        # Extract orbits
        orbits = ["leo", "gto", "sso", "geo", "heo"]
        for orbit in orbits:
            if orbit in query.lower():
                context["orbits_mentioned"].append(orbit)
        
        return context
    
    def _identify_topic(self, messages: List[Dict]) -> str:
        """Identify the main topic of conversation"""
        if not messages:
            return "general"
        
        # Analyze recent messages
        recent_content = " ".join([msg["content"].lower() for msg in messages[-5:]])
        
        if "mission" in recent_content:
            return "mission_planning"
        elif "payload" in recent_content or "mass" in recent_content:
            return "payload_optimization"
        elif "orbit" in recent_content:
            return "orbital_mechanics"
        elif "design" in recent_content:
            return "satellite_design"
        elif "propulsion" in recent_content:
            return "propulsion_systems"
        else:
            return "general"
    
    def _update_preferences(self, user_id: str, query: str, response: str):
        """Update user preferences based on interaction"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                "preferred_detail_level": "medium",
                "preferred_format": "structured",
                "interested_topics": [],
                "interaction_count": 0,
            }
        
        prefs = self.user_preferences[user_id]
        
        # Increase interaction count
        prefs["interaction_count"] += 1
        
        # Detect detail level preference
        if len(response) > 1000:
            prefs["preferred_detail_level"] = "detailed"
        elif len(response) < 200:
            prefs["preferred_detail_level"] = "brief"
        
        # Track interested topics
        topics = self._extract_patterns(query)
        for topic in topics:
            if topic not in prefs["interested_topics"]:
                prefs["interested_topics"].append(topic)
    
    def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences"""
        return self.user_preferences.get(user_id, {})
    
    def _get_learned_patterns(self, user_id: str) -> List[str]:
        """Get learned patterns for user"""
        patterns = self.learning_patterns.get(user_id, [])
        # Return unique patterns
        return list(set(patterns))
    
    def get_personalized_context(self, session_id: str) -> Dict:
        """Get personalized context for next response"""
        if session_id not in self.sessions:
            return {}
        
        session = self.sessions[session_id]
        user_id = session["user_id"]
        
        return {
            "user_preferences": self._get_user_preferences(user_id),
            "learned_patterns": self._get_learned_patterns(user_id),
            "interaction_history": self.query_history[user_id][-10:],
            "mission_context": session.get("mission_context"),
            "conversation_topic": self._identify_topic(session["messages"]),
            "interaction_count": session["query_count"],
        }
    
    def get_recommendations_based_on_history(self, session_id: str) -> List[str]:
        """Get recommendations based on conversation history"""
        if session_id not in self.sessions:
            return []
        
        session = self.sessions[session_id]
        user_id = session["user_id"]
        patterns = self._get_learned_patterns(user_id)
        
        recommendations = []
        
        # Based on learned patterns, suggest next topics
        if "interested_in_missions" in patterns:
            recommendations.append("Would you like to explore other ISRO missions?")
        
        if "interested_in_payload_optimization" in patterns:
            recommendations.append("I can help optimize payload for different orbits")
        
        if "interested_in_orbital_mechanics" in patterns:
            recommendations.append("Would you like to learn about different orbit types?")
        
        if "interested_in_satellite_design" in patterns:
            recommendations.append("I can help with satellite design considerations")
        
        if "seeking_problem_solving_help" in patterns:
            recommendations.append("What aerospace challenge can I help you solve?")
        
        if "interested_in_comparisons" in patterns:
            recommendations.append("Would you like to compare different launch vehicles?")
        
        return recommendations
    
    def summarize_session(self, session_id: str) -> Dict:
        """Summarize a session"""
        if session_id not in self.sessions:
            return {}
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "user_id": session["user_id"],
            "created_at": session["created_at"],
            "message_count": len(session["messages"]),
            "query_count": session["query_count"],
            "conversation_topic": self._identify_topic(session["messages"]),
            "mission_context": session.get("mission_context"),
            "learned_patterns": self._get_learned_patterns(session["user_id"]),
            "user_preferences": self._get_user_preferences(session["user_id"]),
        }
    
    def export_learning_data(self, user_id: str) -> Dict:
        """Export learning data for a user"""
        return {
            "user_id": user_id,
            "patterns_learned": self._get_learned_patterns(user_id),
            "preferences": self._get_user_preferences(user_id),
            "interaction_count": len(self.query_history.get(user_id, [])),
            "feedback_count": len(self.response_feedback.get(user_id, [])),
            "query_history": self.query_history.get(user_id, [])[-20:],
        }

# Singleton instance
session_manager = SessionManager()
