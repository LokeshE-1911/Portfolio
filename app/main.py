from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .router_chat import router as chat_router

app = FastAPI(title="Portfolio + Chat")

# Same-origin site + API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # same host; acceptable here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/", StaticFiles(directory="static", html=True), name="static")
app.include_router(chat_router, prefix="/api")

@app.get("/healthz")
def health():
    return {"ok": True}
