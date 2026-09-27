"""Document Indexer for chunking and storing knowledge base files."""

import os
from pathlib import Path
from typing import List, Dict, Any
from rag.store import doc_store

def chunk_text(text: str, source_name: str, chunk_size: int = 600, overlap: int = 100) -> List[Dict[str, Any]]:
    """Splits raw text into sliding window chunks with overlap."""
    chunks = []
    text = text.strip()
    if not text:
        return []

    start = 0
    chunk_idx = 0
    while start < len(text):
        end = start + chunk_size
        chunk_content = text[start:end].strip()
        if chunk_content:
            chunks.append({
                "id": f"{source_name}_chunk_{chunk_idx}",
                "source": source_name,
                "text": chunk_content,
                "start_char": start,
                "end_char": end
            })
            chunk_idx += 1
        start += chunk_size - overlap

    return chunks

def index_file(file_path: str) -> str:
    """Reads a text, markdown, code, or documentation file and indexes it for RAG.
    
    Args:
        file_path: Relative or absolute path to the document file.
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / file_path

    if not path.exists():
        return f"File not found: {file_path}"

    filename = path.name

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        chunks = chunk_text(content, source_name=filename)
        if not chunks:
            return f"File '{filename}' is empty."

        doc_store.add_document(filename, chunks)
        return f"Successfully indexed '{filename}' ({len(chunks)} chunks stored in knowledge base)."
    except Exception as e:
        return f"Error indexing '{filename}': {str(e)}"
