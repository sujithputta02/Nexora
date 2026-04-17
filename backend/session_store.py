import json
import os
import uuid
from datetime import datetime

# Resolve storage path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSIONS_FILE = os.path.join(_PROJECT_ROOT, "logs", "sessions.json")

class SessionStore:
    def __init__(self):
        os.makedirs(os.path.dirname(SESSIONS_FILE), exist_ok=True)
        if not os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, "w") as f:
                json.dump({}, f)
        
    def _load(self):
        with open(SESSIONS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def _save(self, data):
        with open(SESSIONS_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def create_session(self, title="New Chat", role="Public"):
        session_id = str(uuid.uuid4())
        data = self._load()
        data[session_id] = {
            "id": session_id,
            "title": title,
            "role": role,  # Track which role this session belongs to
            "updated_at": datetime.now().isoformat(),
            "messages": []
        }
        self._save(data)
        return session_id

    def get_sessions_list(self, role="Public"):
        """Get sessions filtered by role"""
        data = self._load()
        # Filter by role and sort by updated_at descending
        sessions = [s for s in data.values() if s.get("role") == role]
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return [{"id": s["id"], "title": s["title"]} for s in sessions]

    def get_session(self, session_id):
        data = self._load()
        return data.get(session_id)

    def add_message(self, session_id, role, content):
        data = self._load()
        if session_id not in data:
            return False
        
        data[session_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # update title if this is the first user query
        if role == "user" and len(data[session_id]["messages"]) <= 2:
            data[session_id]["title"] = content[:30] + ("..." if len(content) > 30 else "")
            
        data[session_id]["updated_at"] = datetime.now().isoformat()
        self._save(data)
        return True

    def delete_session(self, session_id):
        data = self._load()
        if session_id in data:
            del data[session_id]
            self._save(data)
            return True
        return False

session_store = SessionStore()
