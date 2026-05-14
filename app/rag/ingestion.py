# app/rag/ingestion.py

"""
RAG Ingestion Pipeline:
1. Reads all markdown chunks from app/rag/chunks/
2. Parses metadata (frontmatter)
3. Generates embeddings via sentence-transformers
4. Stores in FAISS index
"""

import os
import pickle
import logging
from pathlib import Path
from typing import List, Dict
import re

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ─────────────────────────
# 📁 PATHS
# ─────────────────────────
RAG_DIR = Path(__file__).parent
CHUNKS_DIR = RAG_DIR / "chunks"
INDEX_DIR = RAG_DIR / "faiss_index"
INDEX_FILE = INDEX_DIR / "california_index.bin"
METADATA_FILE = INDEX_DIR / "chunks_metadata.pkl"

# ─────────────────────────
# 🤖 EMBEDDING MODEL
# ─────────────────────────
# all-MiniLM-L6-v2: 384 dim, fast, good for short texts
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parses YAML-like frontmatter from markdown.

    Example:
    ---
    chunk_id: tax_prop_13
    category: tax
    sources: [IRS Pub 17]
    ---

    # Content here...

    Returns: (metadata_dict, content_without_frontmatter)
    """
    pattern = r"^---\n(.*?)\n---\n(.*)"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return {}, content

    fm_text = match.group(1)
    body = match.group(2)

    metadata = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

    return metadata, body.strip()


def load_chunks() -> List[Dict]:
    """
    Loads all markdown chunks from chunks/ directory.
    Returns list of dicts with: id, category, sources, content, full_text
    """
    chunks = []

    if not CHUNKS_DIR.exists():
        logger.warning(f"Chunks directory not found: {CHUNKS_DIR}")
        return chunks

    for category_dir in CHUNKS_DIR.iterdir():
        if not category_dir.is_dir():
            continue

        category = category_dir.name

        for md_file in category_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                metadata, body = parse_frontmatter(content)

                chunk = {
                    "id": metadata.get("chunk_id", md_file.stem),
                    "category": metadata.get("category", category),
                    "sources": metadata.get("sources", "General knowledge"),
                    "filename": md_file.name,
                    "content": body,
                    # For embedding — combine category + content
                    "full_text": f"[{category}] {body}",
                }
                chunks.append(chunk)
            except Exception as e:
                logger.error(f"Error loading {md_file}: {e}")

    logger.info(f"Loaded {len(chunks)} chunks from {CHUNKS_DIR}")
    return chunks


def build_faiss_index(chunks: List[Dict]) -> tuple[faiss.IndexFlatL2, List[Dict]]:
    """
    Generates embeddings and builds FAISS index.
    Returns (index, chunks_in_order).
    """
    if not chunks:
        raise ValueError("No chunks to index")

    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [c["full_text"] for c in chunks]

    logger.info(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype("float32")

    # Build FAISS L2 index
    index = faiss.IndexFlatL2(EMBEDDING_DIM)
    index.add(embeddings)

    logger.info(f"✅ FAISS index built with {index.ntotal} vectors")
    return index, chunks


def save_index(index: faiss.IndexFlatL2, chunks: List[Dict]) -> None:
    """Saves FAISS index + chunks metadata to disk."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(INDEX_FILE))

    with open(METADATA_FILE, "wb") as f:
        pickle.dump(chunks, f)

    logger.info(f"✅ Saved index to {INDEX_FILE}")
    logger.info(f"✅ Saved metadata to {METADATA_FILE}")


def ingest_all() -> int:
    """
    Main entry point: loads chunks, builds index, saves to disk.
    Returns number of chunks indexed.
    """
    chunks = load_chunks()
    if not chunks:
        logger.warning("No chunks found — nothing to index")
        return 0

    index, chunks = build_faiss_index(chunks)
    save_index(index, chunks)

    return len(chunks)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    count = ingest_all()
    print(f"\n✅ Ingested {count} chunks into FAISS index")