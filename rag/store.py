"""Persistent storage for RAG document chunks and metadata."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"
INDEX_FILE = DEFAULT_KNOWLEDGE_DIR / "index.json"

class DocumentStore:
    """Manages indexed documents, chunks, and metadata."""

    def __init__(self, index_path: Path = INDEX_FILE):
        self.index_path = index_path
        self._ensure_storage()

    def _ensure_storage(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            initial_data = {
                "total_documents": 0,
                "total_chunks": 0,
                "documents": [],
                "chunks": []
            }
            self.save(initial_data)

    def load(self) -> Dict[str, Any]:
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"total_documents": 0, "total_chunks": 0, "documents": [], "chunks": []}

    def save(self, data: Dict[str, Any]):
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_document(self, filename: str, chunks: List[Dict[str, Any]]):
        data = self.load()
        # Remove existing document entries if re-indexing
        data["documents"] = [d for d in data.get("documents", []) if d.get("filename") != filename]
        data["chunks"] = [c for c in data.get("chunks", []) if c.get("source") != filename]

        data["documents"].append({
            "filename": filename,
            "chunk_count": len(chunks)
        })
        data["chunks"].extend(chunks)
        data["total_documents"] = len(data["documents"])
        data["total_chunks"] = len(data["chunks"])
        self.save(data)

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        data = self.load()
        return data.get("chunks", [])

    def get_documents(self) -> List[Dict[str, Any]]:
        return self.load().get("documents", [])

    def get_document_summary(self) -> str:
        data = self.load()
        docs = data.get("documents", [])
        if not docs:
            return "Knowledge Base is empty. No documents indexed yet."
        summary = f"Indexed Documents ({len(docs)} files, {data.get('total_chunks', 0)} chunks):\n"
        for d in docs:
            summary += f"- {d['filename']} ({d['chunk_count']} chunks)\n"
        return summary.strip()

doc_store = DocumentStore()
