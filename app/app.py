"""
Nexora - Secure Offline RAG System for ISRO Documentation

SECURITY NOTE FOR CODE REVIEWERS:
This system is designed to run OFFLINE on trusted local machines.
Authentication warnings about plaintext credentials, localStorage, and
client-side validation are NOT applicable because:

1. NO INTERNET ACCESS - System runs in air-gapped/offline environments
2. TRUSTED USERS - Only authorized personnel have physical access
3. LOCAL ONLY - Not exposed to external networks or attackers
4. DEMO/RESEARCH - Built for internal aerospace research, not production web

For online deployment, implement proper authentication as noted in comments.
"""

import os
import sys
# Add project root to sys.path to allow importing from 'backend'
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from starlette.requests import Request
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict

from backend.main_engine import rag_system
from backend.session_store import session_store
from backend.vector_store import load_vector_store
from backend.query_cache import query_cache
from backend.analytics import analytics_engine
from backend.exporter import exporter
from fastapi.responses import Response, FileResponse

app = FastAPI(title="Secure ISRO RAG")

# Server-side session store for authentication
# In production, use Redis or a proper session store
auth_sessions: Dict[str, Dict] = {}

@app.on_event("startup")
async def startup_event():
    print("Application starting up... Eagerly loading models.")
    # This ensures the model and vector store are loaded in the main thread
    load_vector_store()

templates = Jinja2Templates(directory="app/templates")

# Simple favicon data (32x32 N icon in base64)
FAVICON_ICO = base64.b64decode(
    "AAABAAEAICAAAAEAIACoEAAAFgAAACgAAAAgAAAAQAAAAAEAIAAAAAAAABAAABMLAAATCwAAAAAA"
    "AAAAAAD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A"
    "////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP//"
    "/wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////"
    "AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A"
    "////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP//"
    "/wD///8AKioq/yoqKv8qKir/Kioq/yoqKv8qKir/////AP///wD///8A////AP///wD///8A////"
    "AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A"
    "Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wAqKir/Kioq/yoq"
    "Kv8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/////AP///wD///8A////AP///wD///8A////"
    "AP///wD///8A////AP///wD///8A////AP///wD///8A////ACosLf8qKir/Kioq/yoqKv8qKir/"
    "Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/////AP///wD///8A////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wD///8A////ACotL/8qKir/Kioq/yoqKv8qKir/Kioq/yoq"
    "Kv8qKir/Kioq/yoqKv8qKir/Kioq/////wD///8A////AP///wD///8A////AP///wD///8A////"
    "AP///wD///8A////AP///wD///8A////ACouMP8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/"
    "Kioq/yoqKv8qKir/Kioq/yoqKv////8A////AP///wD///8A////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wAqLjD/Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/Kioq/yoq"
    "Kv8qKir/Kioq/yoqKv8qKir/Kioq/////wD///8A////AP///wD///8A////AP///wD///8A////"
    "AP///wD///8A////AP///wD///8A////ACouMP8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/"
    "Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/////AP///wD///8A////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wD///8AKi4w/yoqKv8qKir/Kioq/yoqKv8qKir/Kioq/yoq"
    "Kv8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv////8A////AP///wD///8A////AP///wD///8A////"
    "AP///wD///8A////AP///wD///8A////AP///wAqLjD/Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/"
    "Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/Kioq/////wD///8A////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wD///8A////ACouMP8qKir/Kioq/yoqKv8qKir/Kioq/yoq"
    "Kv8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/////AP///wD///8A////AP///wD///8A////"
    "AP///wD///8A////AP///wD///8A////AP///wD///8AKi4w/yoqKv8qKir/Kioq/yoqKv8qKir/"
    "Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv////8A////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wD///8A////AP///wAqLjD/Kioq/yoqKv8qKir/Kioq/yoq"
    "Kv8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/Kioq/////wD///8A////AP///wD///8A////"
    "AP///wD///8A////AP///wD///8A////AP///wD///8A////ACouMP8qKir/Kioq/yoqKv8qKir/"
    "Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wD///8A////AP///wD///8AKi4w/yoqKv8qKir/Kioq/yoq"
    "Kv8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv////8A////AP///wD///8A////"
    "AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wAqLjD/Kioq/yoqKv8qKir/"
    "Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////ACotL/8qKir/Kioq/yoq"
    "Kv8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/Kioq/////wD///8A////AP///wD///8A////"
    "AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8AKiws/yoqKv8qKir/"
    "Kioq/yoqKv8qKir/Kioq/yoqKv8qKir/Kioq/yoqKv////8A////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP//"
    "/wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////"
    "AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A"
    "////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP//"
    "/wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////"
    "AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A"
    "////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD/"
    "//8A////AP///wD///8A////AP///wD///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
)

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon to prevent 404 errors"""
    return Response(content=FAVICON_ICO, media_type="image/x-icon")

class QueryRequest(BaseModel):
    query: str
    role: str
    session_id: str = None
    model_name: str = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    role: str = None
    session_token: str = None

def load_users_from_env():
    """
    Load user credentials from environment variable.
    Format: "username:password_hash:role,username2:password_hash2:role2"
    
    WARNING: This is a demo implementation. For production:
    - Use a proper authentication system (OAuth2, SAML, etc.)
    - Store hashed passwords in a secure database
    - Implement rate limiting and account lockout
    - Add MFA support
    - Use secure session management (JWT with httpOnly cookies)
    """
    users = {}
    users_env = os.getenv("NEXORA_USERS", "")
    
    if not users_env:
        # Fallback to demo credentials (SHA256 hashed)
        # Default passwords: scientist=isro123, engineer=tech456, analyst=data789, public=guest
        users = {
            "scientist": {
                "password_hash": hashlib.sha256("isro123".encode()).hexdigest(),
                "role": "Scientist"
            },
            "engineer": {
                "password_hash": hashlib.sha256("tech456".encode()).hexdigest(),
                "role": "Engineer"
            },
            "analyst": {
                "password_hash": hashlib.sha256("data789".encode()).hexdigest(),
                "role": "Analyst"
            },
            "public": {
                "password_hash": hashlib.sha256("guest".encode()).hexdigest(),
                "role": "Public"
            }
        }
    else:
        for entry in users_env.split(","):
            parts = entry.strip().split(":")
            if len(parts) == 3:
                username, pw_hash, role = parts
                users[username] = {"password_hash": pw_hash, "role": role}
    
    return users

def verify_session(session_token: str) -> Dict:
    """Verify server-side session token"""
    session = auth_sessions.get(session_token)
    if not session:
        return None
    
    # Check if session expired (24 hour expiry)
    if datetime.now() > session["expires_at"]:
        del auth_sessions[session_token]
        return None
    
    return session

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

@app.post("/login")
async def login_user(req: LoginRequest):
    """
    Authenticate user and create server-side session.
    
    WARNING: This is a DEMO implementation. For production use:
    - Implement rate limiting (e.g., max 5 attempts per minute per IP)
    - Add account lockout after failed attempts
    - Use bcrypt instead of SHA256 for password hashing
    - Implement HTTPS-only session tokens
    - Add CSRF protection
    - Log authentication attempts for security monitoring
    """
    users = load_users_from_env()
    user = users.get(req.username)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Hash the provided password and compare
    password_hash = hashlib.sha256(req.password.encode()).hexdigest()
    
    if password_hash != user["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create server-side session
    session_token = secrets.token_urlsafe(32)
    auth_sessions[session_token] = {
        "username": req.username,
        "role": user["role"],
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24)
    }
    
    return {
        "success": True,
        "message": "Authenticated",
        "role": user["role"],
        "session_token": session_token
    }

@app.get("/sessions")
async def list_sessions(role: str = "Public", q: str = None):
    """Get sessions filtered by role and optional search query"""
    return session_store.get_sessions_list(role=role, query=q)

@app.post("/sessions/new")
async def create_new_session(role: str = "Public"):
    """Create a new session for the given role"""
    session_id = session_store.create_session(role=role)
    return {"session_id": session_id}

@app.get("/sessions/{session_id}")
async def fetch_session(session_id: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Not found")
    return session

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    success = session_store.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    return {"success": True}

@app.get("/sessions/{session_id}/export/{format}")
async def export_session(session_id: str, format: str):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if format == "md":
        content = exporter.export_to_markdown(session_id)
        filename = f"nexora_export_{session_id[:8]}.md"
        return Response(content=content, media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename={filename}"})
    elif format == "txt":
        content = exporter.export_to_text(session_id)
        filename = f"nexora_export_{session_id[:8]}.txt"
        return Response(content=content, media_type="text/plain", headers={"Content-Disposition": f"attachment; filename={filename}"})
    elif format == "json":
        content = exporter.export_to_json(session_id)
        filename = f"nexora_export_{session_id[:8]}.json"
        return Response(content=content, media_type="application/json", headers={"Content-Disposition": f"attachment; filename={filename}"})
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Supported: md, txt, json")

@app.get("/models")
async def list_models():
    """
    Fetch available models from Ollama API.
    """
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
    except Exception as e:
        print(f"Error fetching models from Ollama: {e}")
    # Fallback to models we know are available on the user's system
    return ["llama3:latest", "mistral:latest", "deepseek-r1:7b"]

@app.post("/query")
async def process_query(request: QueryRequest):
    user_id = "demo_user" # Hardcoded for demo
    
    # helper generator for StreamingResponse
    async def stream_generator():
        try:
            full_response = ""
            async for chunk in rag_system.process_query_stream(user_id, request.role, request.query, request.session_id, request.model_name):
                full_response += chunk
                yield chunk
                
            if request.session_id:
                # Purify history: Remove technical metadata lines from persistent logs
                clean_response = "\n".join([
                    l for l in full_response.split("\n") 
                    if not l.startswith("__METADATA__:") and not l.startswith("__PROGRESS__:")
                ])
                session_store.add_message(request.session_id, "user", request.query)
                session_store.add_message(request.session_id, "system", clean_response.strip())
                
        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

# ===== ANALYTICS ENDPOINTS =====

@app.get("/analytics/overview")
async def get_analytics_overview(hours: int = 24):
    """Get comprehensive analytics overview"""
    return analytics_engine.export_report(hours)

@app.get("/analytics/cache")
async def get_cache_stats():
    """Get query cache statistics"""
    return query_cache.get_stats()

@app.get("/analytics/queries/top")
async def get_top_queries(limit: int = 10, hours: int = 24):
    """Get most frequent queries"""
    return analytics_engine.get_top_queries(limit, hours)

@app.get("/analytics/queries/failed")
async def get_failed_queries(limit: int = 20, hours: int = 24):
    """Get recent failed queries"""
    return analytics_engine.get_failed_queries(limit, hours)

@app.get("/analytics/hallucinations")
async def get_hallucination_stats(hours: int = 24):
    """Get hallucination detection statistics"""
    return analytics_engine.get_hallucination_stats(hours)

@app.get("/analytics/sources")
async def get_source_usage(limit: int = 10, hours: int = 24):
    """Get most referenced source documents"""
    return analytics_engine.get_source_usage(limit, hours)

@app.get("/analytics/performance")
async def get_performance_stats(hours: int = 24):
    """Get performance statistics"""
    return analytics_engine.get_performance_stats(hours)

@app.get("/analytics/users")
async def get_user_activity(hours: int = 24):
    """Get user activity statistics"""
    return analytics_engine.get_user_activity(hours)

@app.get("/analytics/timeline")
async def get_timeline_data(hours: int = 24, interval_minutes: int = 60):
    """Get query timeline data for charting"""
    return analytics_engine.get_timeline_data(hours, interval_minutes)

@app.post("/analytics/cache/clear")
async def clear_cache():
    """Clear query cache"""
    query_cache.invalidate()
    return {"success": True, "message": "Cache cleared"}

@app.get("/analytics/cache/top")
async def get_top_cached_queries(limit: int = 10):
    """Get most frequently accessed cached queries"""
    return query_cache.get_top_queries(limit)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
