# tests/test_phase3_setup.py

"""
Phase 3 — Validate FAISS RAG setup with first 10 chunks.
"""

import sys

sys.path.insert(0, ".")

from app.rag.ingestion import ingest_all, load_chunks
from app.rag.retriever import retrieve, build_context_for_llm, get_stats


def test_load_chunks():
    print("=" * 70)
    print("TEST 1: Load chunks from disk")
    print("=" * 70)

    chunks = load_chunks()
    print(f"✅ Loaded {len(chunks)} chunks")

    for c in chunks[:3]:
        print(f"   • {c['id']} ({c['category']})")
        print(f"     Sources: {c.get('sources', 'N/A')}")
    print()


def test_build_index():
    print("=" * 70)
    print("TEST 2: Build FAISS index")
    print("=" * 70)

    count = ingest_all()
    print(f"✅ Ingested {count} chunks into FAISS")
    print()


def test_retrieve_prop13():
    print("=" * 70)
    print("TEST 3: Retrieve 'property tax in California'")
    print("=" * 70)

    results = retrieve("property tax in California Prop 13", top_k=3)

    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['id']} ({r['similarity_score'] * 100:.0f}% relevance)")
        print(f"    Category: {r['category']}")
        print(f"    Preview: {r['content'][:100]}...")
    print()


def test_retrieve_qsbs():
    print("=" * 70)
    print("TEST 4: Retrieve 'startup equity tax exclusion'")
    print("=" * 70)

    results = retrieve("startup equity tax exclusion millionaire", top_k=3)

    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['id']} ({r['similarity_score'] * 100:.0f}% relevance)")
        print(f"    Category: {r['category']}")
        print(f"    Preview: {r['content'][:100]}...")
    print()


def test_llm_context():
    print("=" * 70)
    print("TEST 5: Build LLM-ready context")
    print("=" * 70)

    context = build_context_for_llm(
        "Bay Area software engineer with RSU stock options",
        top_k=2
    )
    print(context[:800] + "...")
    print()


def test_stats():
    print("=" * 70)
    print("TEST 6: Index statistics")
    print("=" * 70)

    stats = get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print()


if __name__ == "__main__":
    print("\n🌴 PHASE 3 RAG VALIDATION\n")

    try:
        test_load_chunks()
        test_build_index()
        test_retrieve_prop13()
        test_retrieve_qsbs()
        test_llm_context()
        test_stats()

        print("=" * 70)
        print("✅ ALL PHASE 3 TESTS PASSED")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)