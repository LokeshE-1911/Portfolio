import json, re
from typing import List, Tuple
from rank_bm25 import BM25Okapi

TOKEN_RE = re.compile(r"\b\w+\b", re.UNICODE)
def _tok(x: str) -> List[str]: return TOKEN_RE.findall(x.lower())

def _flatten_resume(resume: dict) -> List[Tuple[str,str]]:
    docs: List[Tuple[str,str]] = []
    b = resume.get("basics", {})
    if b.get("summary"): docs.append(("Summary", b["summary"]))

    for s in resume.get("skills", []):
        name = s.get("name","Skill")
        kws = ", ".join(s.get("keywords", []))
        docs.append((f"Skill: {name}", kws))

    for p in resume.get("projects", []):
        title = p.get("name","Project")
        desc  = p.get("description","")
        hi    = " ".join(p.get("highlights", []))
        docs.append((f"Project: {title}", f"{desc} {hi}".strip()))

    for w in resume.get("work", []):
        company = w.get("name","Company")
        role    = w.get("position","Role")
        body    = " ".join(filter(None, [w.get("summary",""), " ".join(w.get("highlights", []))]))
        docs.append((f"Experience: {company} – {role}", body))

    for e in resume.get("education", []):
        inst = e.get("institution","Institution")
        detail = " ".join(filter(None,[e.get("studyType",""), e.get("area","")]))
        docs.append((f"Education: {inst}", detail))

    for a in resume.get("awards", []):
        title = a.get("title","Award")
        docs.append((f"Award: {title}", a.get("summary","")))

    return [(t,c) for t,c in docs if (t.strip() or c.strip())]

class RAGIndex:
    """Lightweight BM25 retriever over flattened resume sections."""
    def __init__(self, resume_path: str):
        with open(resume_path, "r", encoding="utf-8") as f:
            resume = json.load(f)
        self.texts: List[str] = [f"{t}\n{c}".strip() for (t,c) in _flatten_resume(resume)]
        self.tokens: List[List[str]] = [_tok(txt) for txt in self.texts]
        self.bm25 = BM25Okapi(self.tokens)

    def search(self, query: str, top_k: int = 5) -> List[str]:
        if not query.strip():
            return self.texts[:top_k]
        scores = self.bm25.get_scores(_tok(query))
        idxs = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
        return [self.texts[i] for i in idxs]
