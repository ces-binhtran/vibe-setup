"""
Advanced RAG techniques example for vibe-rag.

Demonstrates extensibility patterns that prepare you for advanced retrieval
accuracy improvements inspired by https://github.com/NirDiamant/RAG_Techniques

Techniques shown:
    1. Metadata filtering — restrict retrieval to a domain/category
    2. Custom chunking strategies — tune chunk size and overlap
    3. Multi-collection querying — separate knowledge bases per domain

Future techniques (hooks shown as TODO comments):
    - HyDE (Hypothetical Document Embeddings)
    - Multi-query retrieval
    - Reranking (cross-encoder, LLM-based)
    - Contextual compression

Prerequisites:
    - PostgreSQL with pgvector: docker-compose -f docker-compose.test.yml up -d
    - Gemini API key: export GEMINI_API_KEY="your-key"

Run:
    python examples/advanced_rag.py
"""

import asyncio
import os
import tempfile
from pathlib import Path

from vibe_rag import (
    ChunkingConfig,
    LLMConfig,
    PipelineConfig,
    RAGConfig,
    RAGEngine,
    StorageConfig,
)

API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://vibetest:vibetest123@localhost:5434/vibe_rag_test",
)


def make_config(
    collection: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    top_k: int = 5,
    filter_metadata: dict | None = None,
) -> RAGConfig:
    """Build a RAGConfig with configurable chunking and retrieval options."""
    return RAGConfig(
        llm=LLMConfig(
            provider="gemini",
            api_key=API_KEY,
            model_name="gemini-2.0-flash",
        ),
        storage=StorageConfig(
            backend="postgres",
            collection_name=collection,
            connection_string=DATABASE_URL,
            vector_dimension=768,
        ),
        # Tune retrieval: how many docs come back
        pipeline=PipelineConfig(
            top_k=top_k,
            filter_metadata=filter_metadata,  # <-- Metadata filtering hook
        ),
        # Tune chunking: affects retrieval granularity and accuracy
        chunking=ChunkingConfig(
            strategy="recursive",   # "recursive" respects sentence boundaries
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        ),
    )


DOCUMENTS = {
    "legal": {
        "content": (
            "Legal Policy: All employees must submit expense reports within 30 days "
            "of incurring costs. Receipts are required for amounts over $25. "
            "International travel requires manager approval 2 weeks in advance."
        ),
        "metadata": {"domain": "legal", "type": "policy"},
    },
    "engineering": {
        "content": (
            "Engineering Guide: Use Python 3.10+ for all new services. "
            "Follow the adapter pattern for pluggable components. "
            "All async I/O must use connection pooling. "
            "Write tests before implementation (TDD)."
        ),
        "metadata": {"domain": "engineering", "type": "guide"},
    },
}


async def demo_metadata_filtering() -> None:
    """Technique 1: Metadata filtering — query only within a domain."""
    print("\n--- Technique 1: Metadata Filtering ---")

    # Ingest both domains into the same collection
    config = make_config("advanced_demo")
    async with RAGEngine(config) as rag:
        for name, doc in DOCUMENTS.items():
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(doc["content"])
                path = f.name
            try:
                await rag.ingest(path, metadata=doc["metadata"])
                print(f"  Ingested: {name}")
            finally:
                Path(path).unlink()

        # Query without filter (returns from all domains)
        result = await rag.query("What are the requirements?")
        print(f"\n  Query (no filter): {result['metadata']['documents_retrieved']} sources")

    # Query with metadata filter — only legal domain
    # TODO: Future technique: add HyDE here to hypothetically expand the query
    #       before embedding (improves retrieval for vague queries)
    filtered_config = make_config(
        "advanced_demo",
        filter_metadata={"domain": "legal"},  # Restrict to legal docs
    )
    async with RAGEngine(filtered_config) as rag:
        result = await rag.query("What are the requirements?")
        print(f"  Query (legal filter): {result['metadata']['documents_retrieved']} sources")
        domains_in_sources = {s["metadata"].get("domain") for s in result["sources"]}
        print(f"  Domains returned: {domains_in_sources}")


async def demo_chunking_strategies() -> None:
    """Technique 2: Chunking strategy comparison."""
    print("\n--- Technique 2: Chunking Strategies ---")

    long_text = " ".join([
        "Retrieval-Augmented Generation (RAG) improves LLM accuracy by grounding responses "
        "in retrieved documents from a knowledge base.",
        "The retrieval step uses dense vector embeddings to find semantically similar chunks.",
        "Chunk size affects the trade-off between context density and retrieval precision.",
        "Smaller chunks improve precision; larger chunks preserve more surrounding context.",
        "Chunk overlap ensures that information spanning chunk boundaries is not lost.",
        "Recursive chunking respects sentence and paragraph boundaries for better coherence.",
        "Fixed-size chunking is faster but may split sentences at arbitrary points.",
    ] * 3)  # Make it long enough to produce multiple chunks

    for strategy, chunk_size, overlap in [
        ("recursive", 256, 30),   # Fine-grained, boundary-aware
        ("fixed", 512, 50),       # Coarser, faster
    ]:
        config = make_config(
            f"chunking_{strategy}",
            chunk_size=chunk_size,
            chunk_overlap=overlap,
        )
        async with RAGEngine(config) as rag:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(long_text)
                path = f.name
            try:
                doc_ids = await rag.ingest(path)
                print(f"  strategy={strategy!r}, chunk_size={chunk_size}: {len(doc_ids)} chunks")
                # TODO: Future technique: add reranker after retrieval to improve
                #       ordering of retrieved chunks (cross-encoder or LLM-based)
            finally:
                Path(path).unlink()


async def demo_multi_collection() -> None:
    """Technique 3: Multi-collection — separate knowledge bases per domain."""
    print("\n--- Technique 3: Multi-Collection ---")

    for domain, doc in DOCUMENTS.items():
        config = make_config(f"domain_{domain}", top_k=3)
        async with RAGEngine(config) as rag:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(doc["content"])
                path = f.name
            try:
                await rag.ingest(path, metadata=doc["metadata"])
            finally:
                Path(path).unlink()

            # Query domain-specific knowledge base
            question = "What are the key requirements?"
            result = await rag.query(question)
            # TODO: Future technique: multi-query retrieval — generate multiple
            #       phrasings of the question, retrieve for each, then merge and dedupe
            print(f"  [{domain}] '{question}' -> {result['metadata']['documents_retrieved']} docs")


async def main() -> None:
    print("=== Advanced RAG Techniques Demo ===")
    print("Demonstrates extensibility points for accuracy improvements.\n")

    await demo_metadata_filtering()
    await demo_chunking_strategies()
    await demo_multi_collection()

    print("\n=== Done ===")
    print("Next steps: add reranking, HyDE, multi-query, or contextual compression")
    print("See: https://github.com/NirDiamant/RAG_Techniques")


if __name__ == "__main__":
    asyncio.run(main())
