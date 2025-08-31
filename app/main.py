from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from .router_chat import router as chat_router

app = FastAPI(title="Lokesh Portfolio (Groq + RAG)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes at /chat and /api/chat
app.include_router(chat_router, prefix="/api")
app.include_router(chat_router)

# Serve static
app.mount("/static", StaticFiles(directory="static"), name="static")

LANDING_HTML = """<!doctype html><meta charset="utf-8">
<title>Lokesh — Portfolio</title>
<meta http-equiv="refresh" content="0; url=/static/index.html">
<p>Redirecting to the portfolio... <a href="/static/index.html">Open</a></p>"""

@app.get("/", include_in_schema=False)
def root():
    return HTMLResponse(LANDING_HTML)

@app.get("/healthz")
def health():
    return {"ok": True}

# Helpful info for browser GET /chat
@app.get("/chat", include_in_schema=False)
def chat_get_info():
    return JSONResponse({"use":"POST /chat (or /api/chat)", "body":{"message":"Summarize your backend skills"}})
