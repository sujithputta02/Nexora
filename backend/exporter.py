import json
import os
from datetime import datetime

class Exporter:
    def __init__(self, session_store):
        self.session_store = session_store

    def export_to_markdown(self, session_id):
        session = self.session_store.get_session(session_id)
        if not session:
            return None
        
        md = f"# Research Report: {session.get('title', 'New Chat')}\n"
        md += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        md += f"*Role: {session.get('role', 'Public')}*\n\n"
        md += "---\n\n"
        
        for msg in session.get("messages", []):
            role_name = "Researcher" if msg["role"] == "user" else "Nexora AI"
            content = msg["content"]
            
            # Clean up content (remove metadata prefixes if any remain)
            clean_content = "\n".join([l for l in content.split("\n") if not l.startswith("__METADATA__:")])
            
            md += f"### {role_name}\n"
            md += f"{clean_content.strip()}\n\n"
            md += "---\n\n"
            
        md += "\n*Confidential - ISRO Internal Use Only*"
        return md

    def export_to_json(self, session_id):
        session = self.session_store.get_session(session_id)
        if not session:
            return None
        return json.dumps(session, indent=4)

    def export_to_text(self, session_id):
        session = self.session_store.get_session(session_id)
        if not session:
            return None
        
        text = f"NEXORA RESEARCH REPORT\n"
        text += f"======================\n\n"
        text += f"Title: {session.get('title', 'New Chat')}\n"
        text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += f"Role: {session.get('role', 'Public')}\n\n"
        text += "----------------------\n\n"
        
        for msg in session.get("messages", []):
            role_name = "USER" if msg["role"] == "user" else "SYSTEM"
            content = msg["content"]
            clean_content = "\n".join([l for l in content.split("\n") if not l.startswith("__METADATA__:")])
            
            text += f"[{role_name}]:\n{clean_content.strip()}\n\n"
            
        return text

# Singleton instance
from backend.session_store import session_store
exporter = Exporter(session_store)
