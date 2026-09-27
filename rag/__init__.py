from rag.store import doc_store
from rag.indexer import index_file
from rag.retriever import search_knowledge_base

def list_indexed_documents() -> str:
    """Lists all indexed files and total chunks in the RAG knowledge base."""
    return doc_store.get_document_summary()

__all__ = [
    "index_file",
    "search_knowledge_base",
    "list_indexed_documents",
    "doc_store",
]
