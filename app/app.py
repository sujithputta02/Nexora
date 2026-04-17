import os
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

@app.post("/login")
async def login_user(req: LoginRequest):
    if req.username == "scientist" and req.password == "isro123":
        return {"success": True, "message": "Authenticated"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/sessions")
async def list_sessions(role: str = "Public"):
    """Get sessions filtered by role"""
    return session_store.get_sessions_list(role=role)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
