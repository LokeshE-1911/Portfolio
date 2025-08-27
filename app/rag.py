import os, json, time
from typing import List, Tuple, Optional
import numpy as np, httpx
from .config import OPENAI_API_KEY, OPENAI_EMBED_MODEL

HEADERS = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
BATCH = 64

def _post(url, payload, max_retries=6):
    backoff = 1.0
    for _ in range(max_retries):
        try:
            with httpx.Client(timeout=60) as c:
                r = c.post(url, headers=HEADERS, json=payload)
                if r.status_code == 429:
                    time.sleep(float(r.headers.get("retry-after", backoff)))
                    backoff = min(backoff * 2, 16)
                    continue
                r.raise_for_status()
                return r
        except httpx.RequestError:
            time.sleep(backoff); backoff = min(backoff * 2, 16)
    raise RuntimeError("OpenAI request failed after retries")

def _embed(texts: List[str]) -> np.ndarray:
    url = "https://api.openai.com/v1/embeddings"
    vecs = []
    for i in range(0, len(texts), BATCH):
        payload = {"model": OPENAI_EMBED_MODEL, "input": texts[i:i+BATCH]}
        data = _post(url, payload).json()["data"]
        vecs.extend([d["embedding"] for d in data])
    return np.array(vecs, dtype=np.float32)

def _cos(a, b):
    a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-10)
    b = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return a @ b.T

def _flatten(resume: dict) -> List[Tuple[str, str]]:
    docs = []
    b = resume.get("basics", {})
    if b: docs.append(("Summary", b.get("summary","")))
    for s in resume.get("skills", []):
        docs.append((f"Skill: {s.get('name','')}", ", ".join(s.get("keywords",[]))))
    for p in resume.get("projects", []):
        docs.append((f"Project: {p.get('name','')}", f"{p.get('description','')} {' '.join(p.get('highlights',[]))}"))
    for w in resume.get("work", []):
        docs.append((f"Experience: {w.get('name','')} – {w.get('position','')}",
                     f"{w.get('summary','')} {' '.join(w.get('highlights',[]))}"))
    for e in resume.get("education", []):
        docs.append((f"Education: {e.get('institution','')}", f"{e.get('studyType','')} in {e.get('area','')}"))
    return docs

class RAGIndex:
    def __init__(self, resume_path: str, cache_path: str):
        self.resume_path = resume_path
        self.cache_path = cache_path
        self.texts: Optional[List[str]] = None
        self.embeddings: Optional[np.ndarray] = None

    def load_or_build(self):
        if os.path.exists(self.cache_path):
            data = np.load(self.cache_path, allow_pickle=True)
            self.texts = list(data["texts"])
            self.embeddings = data["embeddings"].astype(np.float32)
            return
        with open(self.resume_path, "r", encoding="utf-8") as f:
            docs = _flatten(json.load(f))
        self.texts = [f"{t}\n{c}".strip() for t,c in docs]
        self.embeddings = _embed(self.texts)
        tmp = self.cache_path + ".tmp"
        np.savez_compressed(tmp, texts=np.array(self.texts, dtype=object), embeddings=self.embeddings)
        os.replace(tmp, self.cache_path)

    def search(self, q: str, k: int = 5) -> List[str]:
        if self.texts is None: self.load_or_build()
        qv = _embed([q])
        sims = _cos(qv, self.embeddings)[0]
        idx = np.argsort(-sims)[:k]
        return [self.texts[i] for i in idx]
