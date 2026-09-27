"""Retriever for querying relevant knowledge base chunks."""

import re
import math
from typing import List, Dict, Any, Tuple
from rag.store import doc_store

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

    scored: List[Tuple[float, Dict[str, Any]]] = []
    for c in chunks:
        s = score_chunk(query_tokens, c.get("text", ""))
        if s > 0.0:
            scored.append((s, c))

    # Sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)
    top_results = scored[:top_k]

    if not top_results:
        return f"No relevant passages found in the knowledge base for '{query}'."

    output = [f"Found {len(top_results)} relevant passage(s) for query: '{query}'\n"]
    for i, (score, chunk) in enumerate(top_results, 1):
        clean_text = chunk.get("text", "").encode("ascii", "ignore").decode("ascii").strip()
        output.append(f"--- [Passage {i}] Source: {chunk.get('source')} (Score: {round(score, 2)}) ---")
        output.append(clean_text)
        output.append("")

    return "\n".join(output).strip()
