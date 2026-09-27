"""Optional local-first / free-first embeddings for semantic RAG.

Fully optional: when no embedding backend is reachable, every function returns
None and the retriever silently falls back to keyword-only scoring. No new
dependencies - plain httpx against OpenAI/Ollama/Gemini-compatible endpoints.

Provider order (RAG_EMBED_PROVIDER=auto):
  1. vLLM   - LOCAL_VLLM_URL/embeddings (his Hermit base server, if it embeds)
  2. Ollama - OLLAMA_URL/api/embed (default http://localhost:11434, model
              OLLAMA_EMBED_MODEL, default nomic-embed-text)
  3. Gemini - free API tier when GEMINI_API_KEY is set (GEMINI_EMBED_MODEL,
              default gemini-embedding-001)
Set RAG_EMBED_PROVIDER=none to force keyword-only.
"""

import os
from typing import List, Optional

import httpx

_PROVIDER_CACHE: Optional[str] = None  # resolved provider name or "none"

def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)

def resolve_provider() -> str:
    """Returns 'vllm' | 'ollama' | 'gemini' | 'none' (cached per process)."""
    global _PROVIDER_CACHE
    if _PROVIDER_CACHE is not None:
        return _PROVIDER_CACHE

    pref = _env("RAG_EMBED_PROVIDER", "auto").lower()
    if pref == "none":
        _PROVIDER_CACHE = "none"
        return _PROVIDER_CACHE

    def vllm_ok() -> bool:
        base = _env("LOCAL_VLLM_URL", "http://localhost:8000/v1").rstrip("/")
        try:
            with httpx.Client(timeout=1.0) as c:
                return c.get(f"{base}/models").status_code == 200
        except Exception:
            return False

    def ollama_ok() -> bool:
        base = _env("OLLAMA_URL", "http://localhost:11434").rstrip("/")
        try:
            with httpx.Client(timeout=1.0) as c:
                return c.get(f"{base}/api/tags").status_code == 200
        except Exception:
            return False

    def gemini_ok() -> bool:
        return bool(_env("GEMINI_API_KEY"))

    candidates = {
        "vllm": vllm_ok,
        "ollama": ollama_ok,
        "gemini": gemini_ok,
    }
    order = ["vllm", "ollama", "gemini"] if pref == "auto" else [pref]
    for name in order:
        check = candidates.get(name)
        if check and check():
            _PROVIDER_CACHE = name
            return name
    _PROVIDER_CACHE = "none"
    return "none"

def embed_texts(texts: List[str]) -> Optional[List[List[float]]]:
    """Embeds a batch of texts, or returns None if no backend is available."""
    if not texts:
        return None
    provider = resolve_provider()
    try:
        if provider == "vllm":
            base = _env("LOCAL_VLLM_URL", "http://localhost:8000/v1").rstrip("/")
            model = _env("VLLM_EMBED_MODEL") or _env("LOCAL_MODEL", "default")
            with httpx.Client(timeout=30.0) as c:
                r = c.post(f"{base}/embeddings", json={"model": model, "input": texts})
                r.raise_for_status()
                data = r.json()
            return [row["embedding"] for row in sorted(data["data"], key=lambda d: d["index"])]

        if provider == "ollama":
            base = _env("OLLAMA_URL", "http://localhost:11434").rstrip("/")
            model = _env("OLLAMA_EMBED_MODEL", "nomic-embed-text")
            with httpx.Client(timeout=30.0) as c:
                r = c.post(f"{base}/api/embed", json={"model": model, "input": texts})
                r.raise_for_status()
                return r.json()["embeddings"]

        if provider == "gemini":
            key = _env("GEMINI_API_KEY")
            model = _env("GEMINI_EMBED_MODEL", "gemini-embedding-001")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents?key={key}"
            requests = [
                {"model": f"models/{model}", "content": {"parts": [{"text": t}]}}
                for t in texts
            ]
            with httpx.Client(timeout=30.0) as c:
                r = c.post(url, json={"requests": requests})
                r.raise_for_status()
                return [e["values"] for e in r.json()["embeddings"]]
    except Exception:
        return None  # any embedding failure -> keyword-only fallback
    return None

def cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity in stdlib (no numpy dependency)."""
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / ((na ** 0.5) * (nb ** 0.5))
