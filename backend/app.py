import json
import os
import queue
import threading
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .agent import Agent
from .config import LLM_BASE_URL, LLM_MODEL
from .exchange import get_egp_rate
from .tools import load_knowledge_base

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = FastAPI(title="Veeza AI - European visa assistant for Egyptians")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: dict[str, Agent] = {}


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    kind: str  # "message" | "question" | "plan"
    plan: dict | None = None


@app.get("/api/health")
def health():
    return {"status": "ok", "model": LLM_MODEL, "base_url": LLM_BASE_URL}


@app.get("/api/rate")
def rate():
    return {"eur_to_egp": get_egp_rate()}


@app.get("/api/knowledge")
def knowledge():
    return load_knowledge_base()


def _get_or_create_agent(session_id: str | None) -> tuple[str, Agent]:
    if not session_id or session_id not in SESSIONS:
        sid = session_id or uuid.uuid4().hex
        SESSIONS[sid] = Agent(sid)
    else:
        sid = session_id
    if len(SESSIONS) > 200:
        del SESSIONS[next(iter(SESSIONS))]
    return sid, SESSIONS[sid]


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    session_id, agent = _get_or_create_agent(req.session_id)
    events = queue.Queue()

    def worker():
        try:
            for event in agent.run_stream(message):
                events.put(event)
        except Exception as e:  # surface server-side bugs to the client instead of dying silently
            import traceback

            traceback.print_exc()
            events.put({"type": "message", "reply": f"Sorry, an internal error occurred: {e}"})
        finally:
            events.put(None)

    threading.Thread(target=worker, daemon=True).start()

    def sse():
        while True:
            event = events.get()
            if event is None:
                yield "data: [DONE]\n\n"
                break
            event["session_id"] = session_id
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        sse(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    session_id, agent = _get_or_create_agent(req.session_id)
    result = agent.run(message)
    return ChatResponse(
        session_id=session_id,
        reply=result["reply"],
        kind=result.get("kind", "message"),
        plan=result.get("plan"),
    )


@app.post("/api/reset")
def reset(req: dict):
    sid = req.get("session_id")
    if sid:
        SESSIONS.pop(sid, None)
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
