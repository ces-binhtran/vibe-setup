"""Performance benchmark suite for vibe-rag.

Benchmarks are divided into three categories:

1. Chunking benchmarks (no external deps, always runs):
   - Compare recursive vs fixed strategy
   - Vary chunk sizes: 256, 512, 1024
   - Run 100 iterations each, report avg ms/call and chunk count

2. Embedding batch timing (mock, no external deps):
   - Time MockLLMProvider.embed() on batches of 10, 50, 100 texts
   - Measures mock overhead / Python async call cost

3. MockVectorStore search scaling (no external deps):
   - Populate with 100, 500, 1000 documents
   - Time similarity_search() for each size

Benchmarks requiring real components (API + DB) are marked @pytest.mark.benchmark
and skipped when GOOGLE_API_KEY is not set.
"""

import asyncio
import os
import time
from typing import Any

import pytest

from vibe_rag.testing.mocks import MockLLMProvider, MockVectorStore
from vibe_rag.transformers.document import DocumentProcessor
from vibe_rag.models import Document

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_DOCUMENT_5KB = (
    "Retrieval-Augmented Generation (RAG) is a technique that enhances large language "
    "models by grounding their responses in retrieved knowledge from an external corpus. "
    "Rather than relying solely on parameters learned during pre-training, a RAG system "
    "retrieves relevant documents at inference time and conditions the generation on them. "
    "This approach reduces hallucination, keeps knowledge up-to-date without retraining, "
    "and allows transparent attribution to source documents.\n\n"
    "The retrieval component typically uses dense vector embeddings produced by a "
    "bi-encoder model. The query and each candidate document are independently encoded "
    "into a shared embedding space. Approximate nearest-neighbour search (e.g. HNSW or "
    "IVFFlat indices in pgvector) identifies the top-k most similar document chunks. "
    "The retrieved chunks are then concatenated with the original query to form an "
    "augmented prompt that is passed to the generative model.\n\n"
    "Chunking strategy significantly influences retrieval quality. Fixed-size chunking "
    "splits text at character boundaries, which is fast but may split sentences mid-way. "
    "Recursive character splitting respects paragraph and sentence delimiters, producing "
    "semantically coherent chunks. Chunk size governs the granularity vs. context "
    "trade-off: smaller chunks improve retrieval precision at the cost of less "
    "surrounding context; larger chunks preserve context but may reduce relevance "
    "scoring accuracy.\n\n"
    "Chunk overlap ensures that content near chunk boundaries is not lost. A 10–20% "
    "overlap is a common heuristic. The optimal overlap depends on the downstream task "
    "and the verbosity of source documents. Academic papers with dense notation benefit "
    "from larger overlaps than chat transcripts or structured FAQs.\n\n"
    "Production RAG deployments must handle scale, latency, and cost constraints. "
    "Connection pooling (e.g. asyncpg with a pool of 10–50 connections) prevents "
    "database bottlenecks under concurrent load. Embedding API rate limits require "
    "batching: the Gemini embedding API accepts up to 100 texts per request. Caching "
    "frequently-asked query embeddings eliminates redundant API calls for hot queries.\n\n"
    "Evaluation of RAG systems is multi-dimensional: retrieval recall (are the right "
    "documents retrieved?), answer faithfulness (is the answer grounded in the context?), "
    "and answer relevance (does the answer address the question?). Frameworks such as "
    "RAGAS and TruLens provide automated evaluation pipelines.\n\n"
) * 2  # ~5 KB


def _build_processor(strategy: str, chunk_size: int) -> DocumentProcessor:
    return DocumentProcessor(
        strategy=strategy,
        chunk_size=chunk_size,
        chunk_overlap=max(20, chunk_size // 10),
    )


def _time_call(fn, *args, **kwargs) -> float:
    """Return wall-clock time in milliseconds for a synchronous call."""
    start = time.perf_counter()
    fn(*args, **kwargs)
    return (time.perf_counter() - start) * 1000.0


async def _async_time_call(fn, *args, **kwargs) -> float:
    """Return wall-clock time in milliseconds for an async call."""
    start = time.perf_counter()
    await fn(*args, **kwargs)
    return (time.perf_counter() - start) * 1000.0


# ---------------------------------------------------------------------------
# Benchmark 1: Chunking strategy comparison (pure Python, no external deps)
# ---------------------------------------------------------------------------


class TestChunkingBenchmarks:
    """Benchmark chunking strategies at different chunk sizes.

    These tests always run — no external API or database required.
    They validate that DocumentProcessor is performant and produce
    meaningful chunk counts for real-world document sizes.
    """

    ITERATIONS = 100
    STRATEGIES = ["recursive", "fixed"]
    CHUNK_SIZES = [256, 512, 1024]

    @pytest.mark.parametrize("strategy", STRATEGIES)
    @pytest.mark.parametrize("chunk_size", CHUNK_SIZES)
    def test_chunking_timing(self, strategy: str, chunk_size: int) -> None:
        """Measure chunking throughput for a given strategy and chunk size.

        Runs ITERATIONS calls and reports avg ms/call, total time,
        and the number of chunks produced.
        """
        processor = _build_processor(strategy, chunk_size)

        # Warm-up (not counted)
        processor.process(SAMPLE_DOCUMENT_5KB)

        # Timed iterations
        times: list[float] = []
        chunk_count: int = 0
        for _ in range(self.ITERATIONS):
            t = _time_call(processor.process, SAMPLE_DOCUMENT_5KB)
            times.append(t)

        # Use the last run for chunk count (all runs produce the same output)
        chunks = processor.process(SAMPLE_DOCUMENT_5KB)
        chunk_count = len(chunks)

        avg_ms = sum(times) / len(times)
        total_ms = sum(times)
        min_ms = min(times)
        max_ms = max(times)

        print(
            f"\n  [{strategy:10s} | chunk_size={chunk_size:4d}] "
            f"avg={avg_ms:.3f}ms  min={min_ms:.3f}ms  max={max_ms:.3f}ms  "
            f"total={total_ms:.1f}ms ({self.ITERATIONS} iters)  "
            f"chunks={chunk_count}"
        )

        # Correctness assertions
        assert chunk_count > 0, "Chunking must produce at least one chunk"
        assert all(len(c.content) > 0 for c in chunks), "All chunks must have content"

        # Performance assertion: avg must be under 50ms on any reasonable machine
        assert avg_ms < 50.0, (
            f"Chunking is too slow: avg {avg_ms:.2f}ms > 50ms "
            f"(strategy={strategy}, chunk_size={chunk_size})"
        )

    def test_chunking_strategy_comparison_summary(self) -> None:
        """Compare recursive vs fixed strategy head-to-head at 512-char chunks.

        Prints a summary comparing both strategies on the same document.
        """
        results: dict[str, dict[str, Any]] = {}

        for strategy in self.STRATEGIES:
            processor = _build_processor(strategy, 512)
            processor.process(SAMPLE_DOCUMENT_5KB)  # warm-up

            times: list[float] = []
            for _ in range(self.ITERATIONS):
                times.append(_time_call(processor.process, SAMPLE_DOCUMENT_5KB))

            chunks = processor.process(SAMPLE_DOCUMENT_5KB)
            results[strategy] = {
                "avg_ms": sum(times) / len(times),
                "chunk_count": len(chunks),
                "avg_chunk_len": sum(len(c.content) for c in chunks) / len(chunks),
            }

        print("\n  === Chunking Strategy Comparison (chunk_size=512, 100 iters) ===")
        for strategy, r in results.items():
            print(
                f"  {strategy:10s}: avg={r['avg_ms']:.3f}ms  "
                f"chunks={r['chunk_count']}  "
                f"avg_chunk_len={r['avg_chunk_len']:.0f} chars"
            )

        # Both strategies must be functionally correct
        for strategy, r in results.items():
            assert r["chunk_count"] > 0, f"{strategy} must produce chunks"
            assert r["avg_ms"] < 50.0, f"{strategy} must complete under 50ms avg"


# ---------------------------------------------------------------------------
# Benchmark 2: Embedding batch timing (mock, no external deps)
# ---------------------------------------------------------------------------


class TestEmbeddingBatchBenchmarks:
    """Benchmark MockLLMProvider.embed() at different batch sizes.

    Tests the async call overhead and Python-level throughput of mock embedding.
    No external API calls are made.
    """

    BATCH_SIZES = [10, 50, 100]
    ITERATIONS = 20

    @pytest.mark.parametrize("batch_size", BATCH_SIZES)
    def test_mock_embedding_batch_timing(self, batch_size: int) -> None:
        """Measure mock embedding throughput for different batch sizes."""
        provider = MockLLMProvider()
        texts = [f"Sample document number {i} for embedding benchmark." for i in range(batch_size)]

        async def run() -> float:
            # Warm-up
            await provider.embed(texts)
            times: list[float] = []
            for _ in range(self.ITERATIONS):
                t = await _async_time_call(provider.embed, texts)
                times.append(t)
            return sum(times) / len(times)

        avg_ms = asyncio.get_event_loop().run_until_complete(run())
        throughput = (batch_size * self.ITERATIONS) / (avg_ms * self.ITERATIONS / 1000.0)

        print(
            f"\n  [embed batch_size={batch_size:3d}] "
            f"avg={avg_ms:.3f}ms  "
            f"throughput={throughput:.0f} texts/sec"
        )

        # The mock should be fast — well under 500ms even for 100 texts
        assert avg_ms < 500.0, (
            f"Mock embedding unexpectedly slow: {avg_ms:.2f}ms for batch {batch_size}"
        )

    def test_embedding_batch_scaling_summary(self) -> None:
        """Print scaling summary across all batch sizes."""

        provider = MockLLMProvider()

        async def run() -> dict[int, float]:
            results: dict[int, float] = {}
            for batch_size in self.BATCH_SIZES:
                texts = [f"Text {i}" for i in range(batch_size)]
                await provider.embed(texts)  # warm-up
                times: list[float] = []
                for _ in range(self.ITERATIONS):
                    times.append(await _async_time_call(provider.embed, texts))
                results[batch_size] = sum(times) / len(times)
            return results

        results = asyncio.get_event_loop().run_until_complete(run())

        print("\n  === Mock Embedding Batch Scaling ===")
        for batch_size, avg_ms in results.items():
            print(f"  batch={batch_size:3d}: avg={avg_ms:.3f}ms")

        # All results must be under 500ms
        for batch_size, avg_ms in results.items():
            assert avg_ms < 500.0, f"batch {batch_size} took {avg_ms:.2f}ms"


# ---------------------------------------------------------------------------
# Benchmark 3: MockVectorStore search scaling (no external deps)
# ---------------------------------------------------------------------------


class TestVectorSearchBenchmarks:
    """Benchmark MockVectorStore.similarity_search() at different collection sizes.

    Shows how in-memory cosine similarity scales with the number of stored documents.
    No external database required.
    """

    COLLECTION_SIZES = [100, 500, 1000]
    SEARCH_ITERATIONS = 50

    def _make_documents(self, count: int) -> tuple[list[Document], list[list[float]]]:
        """Create count synthetic documents with 768-dim embeddings."""
        import hashlib

        docs: list[Document] = []
        embeddings: list[list[float]] = []
        for i in range(count):
            doc = Document(content=f"Document {i}: synthetic content for benchmark.", metadata={"index": i})
            docs.append(doc)
            # Deterministic 768-dim embedding
            hash_val = int(hashlib.md5(f"doc-{i}".encode()).hexdigest(), 16) % 1000 / 1000.0
            emb = [hash_val + j * 0.001 for j in range(768)]
            embeddings.append(emb)
        return docs, embeddings

    def _make_query_embedding(self) -> list[float]:
        return [0.5 + i * 0.001 for i in range(768)]

    @pytest.mark.parametrize("collection_size", COLLECTION_SIZES)
    def test_similarity_search_timing(self, collection_size: int) -> None:
        """Measure similarity_search latency for a given collection size."""

        async def run() -> float:
            store = MockVectorStore(collection_name=f"bench_{collection_size}")
            docs, embeddings = self._make_documents(collection_size)
            await store.add_documents(docs, embeddings)

            query_emb = self._make_query_embedding()

            # Warm-up
            await store.similarity_search(query_emb, k=5)

            times: list[float] = []
            for _ in range(self.SEARCH_ITERATIONS):
                t = await _async_time_call(store.similarity_search, query_emb, k=5)
                times.append(t)
            return sum(times) / len(times)

        avg_ms = asyncio.get_event_loop().run_until_complete(run())

        print(
            f"\n  [search collection_size={collection_size:5d}] "
            f"avg={avg_ms:.3f}ms  ({self.SEARCH_ITERATIONS} iters, k=5)"
        )

        # The mock linear scan should still complete within 2 seconds for 1000 docs
        assert avg_ms < 2000.0, (
            f"Search too slow: {avg_ms:.2f}ms for {collection_size} docs"
        )

    def test_search_scaling_summary(self) -> None:
        """Print scaling summary showing how latency grows with collection size."""

        async def run() -> dict[int, float]:
            query_emb = self._make_query_embedding()
            results: dict[int, float] = {}
            for size in self.COLLECTION_SIZES:
                store = MockVectorStore(collection_name=f"summary_{size}")
                docs, embeddings = self._make_documents(size)
                await store.add_documents(docs, embeddings)
                await store.similarity_search(query_emb, k=5)  # warm-up

                times: list[float] = []
                for _ in range(self.SEARCH_ITERATIONS):
                    times.append(await _async_time_call(store.similarity_search, query_emb, k=5))
                results[size] = sum(times) / len(times)
            return results

        results = asyncio.get_event_loop().run_until_complete(run())

        print("\n  === MockVectorStore Search Scaling ===")
        for size, avg_ms in results.items():
            print(f"  docs={size:5d}: avg={avg_ms:.3f}ms")

        # Verify results are present for all sizes
        for size in self.COLLECTION_SIZES:
            assert size in results
            assert results[size] < 2000.0
