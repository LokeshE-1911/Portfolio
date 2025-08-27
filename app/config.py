import os

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")  # serving same origin

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")
