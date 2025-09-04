# resume_rag.py
# Lightweight, precise RAG over a JSON resume (no LLM required).
# - Field-aware retrieval with boosts
# - Query rewrite + synonym expansion
# - Hybrid scoring (BM25 + token overlap)
# - Intent routing for FAQs (email/phone/skills/education/etc.)
# - Extractive answer synthesis + confidence gating

import json, re, math
from typing import List, Tuple, Dict, Any
from collections import Counter, defaultdict
from rank_bm25 import BM25Okapi

TOKEN_RE = re.compile(r"\b[\w@.\-+]+\b", re.UNICODE)
SPLIT_SENT_RE = re.compile(r"(?<=[.!?])\s+")
WHITESPACE_RE = re.compile(r"\s+")

def _tok(x: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(x or "")]

def _dedupe(seq):
    seen = set(); out = []
    for x in seq:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

# ---- Query rewrite: synonyms & normalization ----
SYNONYMS = {
    "llm": ["large language model", "language model", "gpt", "gemini"],
    "rag": ["retrieval augmented generation", "retrieval-augmented generation"],
    "cv": ["resume"],
    "job": ["role", "position"],
    "tech": ["technology", "stack"],
    "stt": ["speech to text", "speech-to-text", "asr"],
    "tts": ["text to speech", "text-to-speech"],
    "deploy": ["deployment"],
    "school": ["university", "college"],
    "masters": ["ms", "master"],
    "bachelors": ["bs", "bachelor"],
}

def expand_query(q: str) -> str:
    toks = _tok(q)
    extra = []
    for t in toks:
        for k, syns in SYNONYMS.items():
            if t == k or t in syns:
                extra.extend([k] + syns)
    # Keep it short but richer
    expanded = _dedupe(toks + extra)[:40]
    return " ".join(expanded)

# ---- Flatten resume into fielded docs with boosts ----
FIELD_BOOSTS = {
    "Summary": 1.2,
    "Skill": 1.5,
    "Project": 1.6,
    "Experience": 1.7,
    "Education": 1.1,
    "Award": 1.0,
}

def _sentences(text: str) -> List[str]:
    return [s.strip() for s in SPLIT_SENT_RE.split(text or "") if s.strip()]

def _flatten_resume(resume: dict) -> List[Tuple[str, str, str]]:
    """
    Returns list of (field_tag, title, content) where field_tag in FIELD_BOOSTS keys.
    """
    docs: List[Tuple[str, str, str]] = []
    b = resume.get("basics", {})
    if b.get("summary"):
        docs.append(("Summary", "Summary", b["summary"]))

    for s in resume.get("skills", []):
        name = s.get("name", "Skill")
        kws = ", ".join(s.get("keywords", []))
        docs.append(("Skill", f"Skill: {name}", kws))

    for p in resume.get("projects", []):
        title = p.get("name", "Project")
        desc = p.get("description", "")
        hi = " ".join(p.get("highlights", []))
        tech = " ".join(p.get("tech", []))
        body = " ".join(x for x in [desc, hi, tech] if x)
        docs.append(("Project", f"Project: {title}", body))

    for w in resume.get("work", []):
        company = w.get("name", "Company")
        role = w.get("position", "Role")
        dates = " ".join([w.get("startDate", ""), "-", w.get("endDate", "")]).strip(" -")
        body = " ".join(filter(None, [w.get("summary", ""), " ".join(w.get("highlights", []))]))
        title = f"Experience: {company} – {role}" + (f" ({dates})" if dates else "")
        docs.append(("Experience", title, body))

    for e in resume.get("education", []):
        inst = e.get("institution", "Institution")
        detail = " ".join(filter(None, [e.get("studyType", ""), e.get("area", "")]))
        docs.append(("Education", f"Education: {inst}", detail))

    for a in resume.get("awards", []):
        title = a.get("title", "Award")
        body = " ".join(filter(None, [a.get("date", ""), a.get("summary", "")]))
        docs.append(("Award", f"Award: {title}", body))

    return [(tag, t, c) for (tag, t, c) in docs if (t.strip() or c.strip())]

def _build_field_weighted_text(tag: str, title: str, content: str) -> str:
    boost = FIELD_BOOSTS.get(tag, 1.0)
    # Soft-boost by replicating tokens (simple & fast)
    tokens = _tok(f"{title}\n{content}")
    weighted = tokens * max(1, int(math.floor((boost - 1.0) * 3)))
    return " ".join(tokens + weighted)

# ---- Heuristic overlap scoring (for hybrid) ----
def jaccard(a: List[str], b: List[str]) -> float:
    A, B = set(a), set(b)
    if not A or not B: return 0.0
    return len(A & B) / len(A | B)

def precision_at_k(a: List[str], b: List[str], k: int = 8) -> float:
    if not a or not b: return 0.0
    A = a[:k]; B = set(b)
    hit = sum(1 for t in A if t in B)
    return hit / max(1, len(A))

# ---- Answer synthesis (extract + compress) ----
def extractive_answer(query: str, texts: List[str], max_sentences: int = 3) -> str:
    q_toks = _tok(query)
    scored_sents = []
    for txt in texts:
        for s in _sentences(txt):
            st = _tok(s)
            # Simple score: weighted overlap
            score = 0.6 * jaccard(q_toks, st) + 0.4 * precision_at_k(q_toks, st, 8)
            if score > 0:
                scored_sents.append((score, s))
    scored_sents.sort(key=lambda x: -x[0])
    picked = _dedupe([s for _, s in scored_sents])[:max_sentences]
    # Minimal compression: strip redundant whitespace
    ans = " ".join(picked)
    return WHITESPACE_RE.sub(" ", ans).strip()

# ---- Intent routing for frequent “unexpected” asks ----
INTENT_PATTERNS = {
    "email": re.compile(r"\b(email|mail)\b", re.I),
    "phone": re.compile(r"\b(phone|mobile|contact number)\b", re.I),
    "skills": re.compile(r"\b(skills?|tech|stack|technologies)\b", re.I),
    "education": re.compile(r"\b(education|degree|gpa|university|school|masters|bachelors)\b", re.I),
    "experience": re.compile(r"\b(experience|work history|employment)\b", re.I),
    "projects": re.compile(r"\b(projects?)\b", re.I),
    "awards": re.compile(r"\b(awards?|achievements?)\b", re.I),
    "summary": re.compile(r"\b(summary|overview|profile)\b", re.I),
}

def route_intent(q: str) -> str:
    for name, pat in INTENT_PATTERNS.items():
        if pat.search(q):
            return name
    return "generic"

def format_intent_answer(intent: str, resume: Dict[str, Any]) -> str:
    b = resume.get("basics", {})
    if intent == "email":
        return b.get("email") or "No email listed."
    if intent == "phone":
        return b.get("phone") or "No phone listed."
    if intent == "skills":
        skills = resume.get("skills", [])
        out = []
        for s in skills:
            name = s.get("name", "Skill")
            kws = ", ".join(s.get("keywords", []))
            out.append(f"{name}: {kws}" if kws else name)
        return "; ".join(out) or "No skills listed."
    if intent == "education":
        edu = []
        for e in resume.get("education", []):
            inst = e.get("institution", "")
            area = e.get("area", "")
            degree = e.get("studyType", "")
            gpa = e.get("gpa", "")
            line = " | ".join(x for x in [degree, area, inst, (f"GPA {gpa}" if gpa else "")] if x)
            if line: edu.append(line)
        return "; ".join(edu) or "No education listed."
    if intent == "experience":
        ex = []
        for w in resume.get("work", []):
            company = w.get("name", "")
            role = w.get("position", "")
            dates = f"{w.get('startDate','')}–{w.get('endDate','')}".strip("–")
            ex.append(" | ".join(x for x in [role, company, dates] if x))
        return "; ".join(ex) or "No experience listed."
    if intent == "projects":
        pr = []
        for p in resume.get("projects", []):
            pr.append(p.get("name", "Project"))
        return "; ".join(pr) or "No projects listed."
    if intent == "awards":
        aw = []
        for a in resume.get("awards", []):
            title = a.get("title", "Award")
            date = a.get("date", "")
            aw.append(" | ".join(x for x in [title, date] if x))
        return "; ".join(aw) or "No awards listed."
    if intent == "summary":
        return (resume.get("basics", {}) or {}).get("summary", "No summary listed.")
    return ""  # generic

class ResumeRAG:
    def __init__(self, resume_path: str):
        with open(resume_path, "r", encoding="utf-8") as f:
            self.resume = json.load(f)

        raw_docs = _flatten_resume(self.resume)
        self.rows: List[Dict[str, Any]] = []
        for tag, title, content in raw_docs:
            weighted_text = _build_field_weighted_text(tag, title, content)
            self.rows.append({
                "tag": tag,
                "title": title,
                "content": content,
                "weighted": weighted_text,
            })

        self.texts: List[str] = [r["weighted"] for r in self.rows]
        self.tokens: List[List[str]] = [_tok(txt) for txt in self.texts]
        self.bm25 = BM25Okapi(self.tokens)

        # Precompute raw (unweighted) for answer synthesis
        self.raw_joined: List[str] = [f"{r['title']}. {r['content']}".strip() for r in self.rows]

    def _hybrid_scores(self, query: str) -> List[float]:
        q_tokens = _tok(query)
        bm25_scores = self.bm25.get_scores(q_tokens)

        # Heuristic overlap with raw_joined to stabilize on OOD queries
        overlap_scores = []
        for txt in self.raw_joined:
            t = _tok(txt)
            sc = 0.6 * jaccard(q_tokens, t) + 0.4 * precision_at_k(q_tokens, t, 8)
            overlap_scores.append(sc)

        # Normalize overlap to BM25 scale
        if overlap_scores:
            m = max(overlap_scores) or 1e-9
            overlap_scaled = [s / m for s in overlap_scores]
        else:
            overlap_scaled = [0.0] * len(bm25_scores)

        # Blend (BM25 dominates; overlap refines)
        scores = [0.85 * bm + 0.15 * ov for bm, ov in zip(bm25_scores, overlap_scaled)]
        return scores

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[float, str]]:
        qx = expand_query(query)
        scores = self._hybrid_scores(qx)
        idxs = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
        return [(scores[i], self.raw_joined[i]) for i in idxs]

    def answer(self, query: str, top_k: int = 5, min_conf: float = 0.35) -> Dict[str, Any]:
        # Intent short-circuit (precise answers for common asks)
        intent = route_intent(query)
        if intent != "generic":
            routed = format_intent_answer(intent, self.resume)
            if routed:
                return {
                    "answer": routed,
                    "intent": intent,
                    "confidence": 0.95,
                    "sources": []
                }

        hits = self.retrieve(query, top_k=top_k)
        best_score = hits[0][0] if hits else 0.0
        contexts = [txt for _, txt in hits]

        if best_score < min_conf:
            # Low confidence: still try to be helpful + transparent
            sketch = extractive_answer(query, contexts, max_sentences=2)
            return {
                "answer": sketch or "I couldn’t find that in the resume. Closest matches are shown.",
                "intent": "generic",
                "confidence": round(float(best_score), 3),
                "sources": contexts
            }

        final = extractive_answer(query, contexts, max_sentences=3)
        # Tighten answer length a bit
        if len(final) > 450:
            final = final[:447].rsplit(" ", 1)[0] + "..."
        return {
            "answer": final or contexts[0],
            "intent": "generic",
            "confidence": round(float(best_score), 3),
            "sources": contexts
        }

# ------------- Example -------------
# idx = ResumeRAG("resume.json")
# print(idx.answer("What are your top skills?"))
# print(idx.answer("What's your email?"))
# print(idx.answer("Tell me about LLM + RAG projects."))
# print(idx.answer("Do you have FPGA experience?"))
