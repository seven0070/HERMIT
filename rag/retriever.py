"""Retriever for querying relevant knowledge base chunks."""

import re
import math
from typing import List, Dict, Any, Tuple
from rag.store import doc_store
from rag.embeddings import embed_texts, cosine

def tokenize(text: str) -> List[str]:
    """Simple lowercase alphanumeric tokenizer."""
    return re.findall(r'\b[a-zA-Z0-9_-]+\b', text.lower())

def score_chunk(query_tokens: List[str], chunk_text: str) -> float:
    """Calculates relevance score using term frequency and exact phrase matching."""
    chunk_lower = chunk_text.lower()
    chunk_tokens = tokenize(chunk_text)
    
    if not chunk_tokens:
        return 0.0

    score = 0.0
    token_set = set(chunk_tokens)
    
    # 1. Individual token overlap with frequency damping
    for token in query_tokens:
        if token in token_set:
            count = chunk_tokens.count(token)
            score += 1.0 + math.log(1.0 + count)

    # 2. Exact phrase bonus
    query_phrase = " ".join(query_tokens)
    if query_phrase and query_phrase in chunk_lower:
        score += 3.0

    return score

def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """Searches the knowledge base for chunks relevant to the query.
    
    Args:
        query: The search query or question to look up.
        top_k: Number of most relevant passages to return. Defaults to 3.
    """
    chunks = doc_store.get_all_chunks()
    if not chunks:
        return "Knowledge base is currently empty. Use index_document(file_path) to add documents."

    query_tokens = tokenize(query)
    if not query_tokens:
        return "Please provide a valid query."

    # Keyword scores, normalized to 0..1
    kw_scored: List[Tuple[float, Dict[str, Any]]] = []
    for c in chunks:
        s = score_chunk(query_tokens, c.get("text", ""))
        if s > 0.0:
            kw_scored.append((s, c))
    max_kw = max((s for s, _ in kw_scored), default=0.0)

    # Semantic scores when both sides have embeddings (otherwise keyword-only)
    query_vec_list = embed_texts([query])
    query_vec = query_vec_list[0] if query_vec_list else None
    have_vectors = query_vec is not None and any(c.get("embedding") for c in chunks)

    scored: List[Tuple[float, Dict[str, Any]]] = []
    if have_vectors:
        mode = "semantic + keyword (hybrid)"
        seen = set()
        for c in chunks:
            kw = 0.0
            for s, kc in kw_scored:
                if kc is c:
                    kw = s / max_kw if max_kw else 0.0
                    break
            sem = cosine(query_vec, c["embedding"]) if c.get("embedding") else 0.0
            sem = max(0.0, sem)
            final = 0.45 * kw + 0.55 * sem
            if final > 0.0 and id(c) not in seen:
                seen.add(id(c))
                scored.append((final, c))
    else:
        mode = "keyword"
        scored = [(s / max_kw if max_kw else 0.0, c) for s, c in kw_scored]

    # Sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)
    top_results = scored[:top_k]

    if not top_results:
        return f"No relevant passages found in the knowledge base for '{query}'."

    output = [f"Found {len(top_results)} relevant passage(s) for query: '{query}' [mode: {mode}]\n"]
    for i, (score, chunk) in enumerate(top_results, 1):
        clean_text = chunk.get("text", "").encode("ascii", "ignore").decode("ascii").strip()
        output.append(f"--- [Passage {i}] Source: {chunk.get('source')} (Score: {round(score, 2)}) ---")
        output.append(clean_text)
        output.append("")

    return "\n".join(output).strip()
