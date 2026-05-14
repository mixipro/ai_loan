# app/rag/retriever.py

"""
RAG Retriever — semantic search over California knowledge base.

Usage:
    from app.rag.retriever import retrieve
    chunks = retrieve("Bay Area tech worker startup equity", top_k=3)
"""

import pickle
import logging
from pathlib import Path
from typing import List, Dict, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ─────────────────────────
# 📁 PATHS
# ─────────────────────────
RAG_DIR = Path(__file__).parent
INDEX_DIR = RAG_DIR / "faiss_index"
INDEX_FILE = INDEX_DIR / "california_index.bin"
METADATA_FILE = INDEX_DIR / "chunks_metadata.pkl"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ─────────────────────────
# 🌐 GLOBAL STATE (singleton pattern)
# ─────────────────────────
_index: Optional[faiss.IndexFlatL2] = None
_chunks: Optional[List[Dict]] = None
_model: Optional[SentenceTransformer] = None


def _load_index_and_model():
    """Lazy loads FAISS index + embedding model on first query."""
    global _index, _chunks, _model

    if _index is None or _chunks is None or _model is None:
        if not INDEX_FILE.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {INDEX_FILE}. "
                f"Run 'python -m app.rag.ingestion' first to build index."
            )

        logger.info("Loading FAISS index and embedding model...")
        _index = faiss.read_index(str(INDEX_FILE))

        with open(METADATA_FILE, "rb") as f:
            _chunks = pickle.load(f)

        _model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"✅ Loaded {len(_chunks)} chunks into memory")


def retrieve(
        query: str,
        top_k: int = 3,
        category_filter: Optional[str] = None
) -> List[Dict]:
    """
    Semantic search over California knowledge base.

    Args:
        query: Natural language query (e.g., "Bay Area tech equity tax")
        top_k: Number of top chunks to return
        category_filter: Optional filter by category ("tax", "real_estate", etc.)

    Returns:
        List of relevant chunks with similarity scores.
    """
    _load_index_and_model()

    # Embed query
    query_embedding = _model.encode([query], convert_to_numpy=True).astype("float32")

    # Retrieve more than top_k if filtering (to leave room for category filter)
    search_k = top_k * 3 if category_filter else top_k

    distances, indices = _index.search(query_embedding, search_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue

        chunk = _chunks[idx].copy()
        chunk["similarity_score"] = float(1 / (1 + dist))  # convert distance to similarity
        chunk["distance"] = float(dist)

        if category_filter and chunk["category"] != category_filter:
            continue

        results.append(chunk)

        if len(results) >= top_k:
            break

    return results


def build_context_for_llm(query: str, top_k: int = 3, category_filter: Optional[str] = None) -> str:
    """
    Retrieves chunks and formats them as LLM-ready context string.

    Returns formatted text block to inject into prompt.
    """
    chunks = retrieve(query, top_k=top_k, category_filter=category_filter)

    if not chunks:
        return "[No relevant knowledge found]"

    context_parts = ["📚 RELEVANT CALIFORNIA KNOWLEDGE:\n"]

    for i, chunk in enumerate(chunks, 1):
        context_parts.append(f"""
═══ Source {i}: {chunk['id']} (relevance: {chunk['similarity_score'] * 100:.0f}%) ═══
Sources: {chunk.get('sources', 'N/A')}

{chunk['content']}
""")

    return "\n".join(context_parts)


def get_stats() -> dict:
    """Returns stats about the loaded index."""
    _load_index_and_model()

    categories = {}
    for c in _chunks:
        categories[c["category"]] = categories.get(c["category"], 0) + 1

    return {
        "total_chunks": len(_chunks),
        "categories": categories,
        "embedding_model": EMBEDDING_MODEL,
        "index_file": str(INDEX_FILE),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    # Demo query
    print("\n" + "=" * 60)
    print("DEMO QUERY: 'Bay Area tech worker with startup equity'")
    print("=" * 60)

    results = retrieve("Bay Area tech worker with startup equity", top_k=3)

    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['id']} (score: {r['similarity_score'] * 100:.0f}%)")
        print(f"    Category: {r['category']}")
        print(f"    Sources: {r.get('sources', 'N/A')}")
        print(f"    Preview: {r['content'][:150]}...")

    print("\n" + "=" * 60)
    print("STATS:")
    print("=" * 60)
    stats = get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")