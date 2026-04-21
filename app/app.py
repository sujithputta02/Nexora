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

from backend.main_engine import rag_system
from backend.session_store import session_store
from backend.vector_store import load_vector_store
from backend.query_cache import query_cache
from backend.analytics import analytics_engine
from backend.exporter import exporter
from fastapi.responses import Response, FileResponse

app = FastAPI(title="Secure ISRO RAG")

@app.on_event("startup")
async def startup_event():
    print("Application starting up... Eagerly loading models.")
    # This ensures the model and vector store are loaded in the main thread
    load_vector_store()

templates = Jinja2Templates(directory="app/templates")

class QueryRequest(BaseModel):
    query: str
    role: str
    session_id: str = None
    model_name: str = "llama3"

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

@app.post("/login")
async def login_user(req: LoginRequest):
    if req.username == "scientist" and req.password == "isro123":
        return {"success": True, "message": "Authenticated"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

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
                clean_response = "\n".join([l for l in full_response.split("\n") if not l.startswith("__METADATA__:")])
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
