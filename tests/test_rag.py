"""RAG: keyword fallback works fully offline."""
import os
os.environ["RAG_EMBED_PROVIDER"] = "none"  # force offline keyword mode
from pathlib import Path
from rag import index_file, search_knowledge_base

def test_keyword_index_and_search(tmp_path):
    doc = tmp_path / "dogs.md"
    doc.write_text("Dogs need daily walks. Puppies require gentle training routines.")
    res = index_file(str(doc))
    assert "Error" not in res
    out = search_knowledge_base("daily walks")
    assert "dogs.md" in out

def test_search_labels_mode(tmp_path):
    doc = tmp_path / "modes.md"
    doc.write_text("Retrieval modes must be labeled honestly in results.")
    index_file(str(doc))
    out = search_knowledge_base("labeled honestly")
    assert "modes.md" in out
    assert "keyword" in out.lower()
