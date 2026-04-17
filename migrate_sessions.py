#!/usr/bin/env python3
"""
Migrate existing sessions to include role field
All existing sessions are marked as 'Public' since they were created before role separation
"""

import json
import os

SESSIONS_FILE = "logs/sessions.json"

def migrate_sessions():
    if not os.path.exists(SESSIONS_FILE):
        print("No sessions file found")
        return
    
    with open(SESSIONS_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Invalid JSON in sessions file")
            return
    
    # Add role field to all sessions that don't have it
    migrated = 0
    for session_id, session in data.items():
        if "role" not in session:
            session["role"] = "Public"  # Default to Public for existing sessions
            migrated += 1
    
    # Save back
    with open(SESSIONS_FILE, "w") as f:
        json.dump(data, f, indent=4)
    
    print(f"✅ Migrated {migrated} sessions")
    print(f"Total sessions: {len(data)}")

if __name__ == "__main__":
    migrate_sessions()
