# app/main.py
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

# IMPORTANT: keep heavy things OUT of top-level imports (e.g., langchain, hf, etc.)
# We'll lazy-load in getters inside request handlers.

# --- Lifespan: keep startup light, avoid heavy model loads here ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # placeholders; will be created on first use
    app.state.llm = None
    app.state.rag = None
    yield
    # optional: nothing to teardown

app = FastAPI(title="Lokesh Portfolio API", docs_url="/docs", openapi_url="/openapi.json", lifespan=lifespan)

# CORS: allow your static site origins (add Firebase/Vercel if needed)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health & Prewarm ---
@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.get("/prewarm")
async def prewarm(req: Request):
    """
    Triggers lazy initialization of LLM/RAG once after cold start.
    Used by GitHub Actions/UptimeRobot to keep things warm.
    """
    # do NOT import heavy libs at top; import inline
    _ = get_llm(req)
    _ = get_rag(req)
    return {"warmed": True}

# --- Lazy getters ---
def get_llm(req: Request):
    if req.app.state.llm is None:
        # Put any heavy imports HERE so they run only once on first request
        # from groq import Groq         # example
        # api_key = os.getenv("GROQ_API_KEY")
        # req.app.state.llm = Groq(api_key=api_key)
        req.app.state.llm = object()  # placeholder client; replace with real client
    return req.app.state.llm

def get_rag(req: Request):
    if req.app.state.rag is None:
        # Example: init vector store / embeddings lazily
        # from my_rag_lib import VectorStore
        # req.app.state.rag = VectorStore.connect(os.getenv("RAG_URL"))
        req.app.state.rag = object()  # placeholder
    return req.app.state.rag

# --- Mount routers (they will call the getters above) ---
from .router_chat import router as chat_router
app.include_router(chat_router, prefix="", tags=["chat"])
