# app/models.py  (optional helper)
from starlette.requests import Request

def get_llm(req: Request):
    from .main import get_llm as _get_llm
    return _get_llm(req)

def get_rag(req: Request):
    from .main import get_rag as _get_rag
    return _get_rag(req)
