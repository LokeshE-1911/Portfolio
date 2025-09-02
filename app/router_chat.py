
from fastapi import APIRouter, HTTPException
from .models import ChatRequest, ChatResponse
from .config import GROQ_API_KEY, GROQ_CHAT_MODEL
from .rag import RAGIndex
import httpx, os
from threading import Lock

router = APIRouter()
_RAG = None
_LOCK = Lock()

def get_rag() -> RAGIndex:
    global _RAG
    if _RAG is None:
        with _LOCK:
            if _RAG is None:
                here = os.path.dirname(__file__)
                resume_path = os.path.join(here, "..", "resume", "resume.json")
                _RAG = RAGIndex(resume_path)
    return _RAG

SYSTEM_STYLE = """You are Lokesh's portfolio assistant.
Speak warmly and naturally. Use the resume context to answer.
If something isn't in the context, say you're not sure and ask a short follow-up.
Keep answers concise unless the user asks for detail."""

def _groq_chat(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {"model": GROQ_CHAT_MODEL, "messages": messages, "temperature": 0.6}
    with httpx.Client(timeout=60) as c:
        r = c.post(url, headers=headers, json=payload)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()["choices"][0]["message"]["content"]

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        rag = get_rag()
        ctx = rag.search(req.message, top_k=req.top_k)
        ctx_block = "\n\n".join(f"- {c}" for c in ctx)
        msgs = [
            {"role":"system","content":SYSTEM_STYLE},
            {"role":"system","content":f"Resume/context snippets:\n{ctx_block}"},
        ]
        for m in (req.history or [])[-6:]:
            msgs.append({"role": m.role, "content": m.content})
        msgs.append({"role":"user","content":req.message})
        reply = _groq_chat(msgs)
        return ChatResponse(reply=reply)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
