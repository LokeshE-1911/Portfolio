from fastapi import APIRouter, HTTPException
from .config import OPENAI_API_KEY, OPENAI_CHAT_MODEL
from .rag import RAGIndex
import httpx, os
from threading import Lock

router = APIRouter()

_RAG = None
_LOCK = Lock()

def get_rag():
    global _RAG
    if _RAG is None:
        with _LOCK:
            if _RAG is None:
                here = os.path.dirname(__file__)
                resume = os.path.join(here, "..", "resume", "resume.json")
                cache  = os.path.join(here, "..", "resume", "resume_index.npz")
                _RAG = RAGIndex(resume, cache)
    return _RAG

HEADERS = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
STYLE = ("You are a warm, concise portfolio assistant. "
         "Use provided resume snippets. If unsure, ask a short follow-up. "
         "Avoid buzzwords; be clear and human.")

def _chat(messages):
    url = "https://api.openai.com/v1/chat/completions"
    payload = {"model": OPENAI_CHAT_MODEL, "messages": messages, "temperature": 0.7}
    with httpx.Client(timeout=60) as c:
        r = c.post(url, headers=HEADERS, json=payload)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

@router.post("/chat")
def chat(body: dict):
    try:
        msg = (body.get("message") or "").strip()
        if not msg:
            raise HTTPException(400, "message is required")
        rag = get_rag()
        ctx = rag.search(msg, k=5)
        ctx_block = "\n\n".join(f"- {c}" for c in ctx)
        messages = [
            {"role":"system","content":STYLE},
            {"role":"system","content":f"Resume/context:\n{ctx_block}"},
            {"role":"user","content":msg}
        ]
        reply = _chat(messages)
        return {"reply": reply}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
