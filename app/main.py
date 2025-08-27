from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .router_chat import router as chat_router
import os

app = FastAPI(title="Portfolio + Chat")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1) Register API routes FIRST so StaticFiles won't shadow them
app.include_router(chat_router, prefix="/api")

# 2) Serve static at /static (not "/")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 3) Serve index.html at root
INDEX_PATH = os.path.join(STATIC_DIR, "index.html")

@app.get("/")
def home():
    return FileResponse(INDEX_PATH)

@app.get("/healthz")
def health():
    return {"ok": True}
