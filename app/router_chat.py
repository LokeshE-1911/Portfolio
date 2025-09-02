# app/router_chat.py
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class ChatIn(BaseModel):
    message: str

def get_llm(req: Request):
    # import from main to reuse the same lazy getter / shared state
    from .main import get_llm as _get_llm
    return _get_llm(req)

@router.post("/chat")
async def chat(req: Request, body: ChatIn):
    llm = get_llm(req)  # this initializes on first call, then reuses
    user_msg = body.message.strip()

    # TODO: replace with your real LLM call
    # reply = llm.generate(user_msg)
    reply = f"You said: {user_msg}. (LLM stub reply)"

    return {"reply": reply}
