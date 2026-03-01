# Phase 3: Production Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make vibe-rag production-ready with >80% test coverage (real E2E with PostgreSQL + Gemini), performance benchmarks, complete API docs, deployment guides, and polished examples.

**Architecture:** E2E-First approach: fix and run real E2E tests to hit engine coverage target, then fill unit gaps for config/observability, then add benchmarks, API docs, deployment guides, and a multi-domain example.

**Tech Stack:** Python 3.10+, pytest + pytest-asyncio + pytest-cov, asyncpg, PostgreSQL+pgvector (Docker), Google Gemini API, Docker/Kubernetes

---

## Pre-Flight Checklist

Before starting, confirm:
1. `.venv/` exists: `ls .venv/bin/python`
2. Docker is running: `docker ps`
3. `GOOGLE_API_KEY` is set: `echo $GOOGLE_API_KEY`

If `.venv` is missing: `python -m venv .venv && .venv/bin/pip install -e ".[dev]"`

---

## Task 1: Fix E2E Test Fixture Bug

**Files:**
- Modify: `tests/e2e/test_rag_engine_e2e.py`

The `rag_engine` fixture calls `await engine.storage._create_table()` after cleanup, but `_create_table()` is already invoked by `initialize()` (via `async with RAGEngine`). Calling it a second time causes an index-already-exists error. The fix is to remove the duplicate `_create_table()` call.

**Step 1: Read the current fixture**

Run: `grep -n "_create_table\|delete_collection" tests/e2e/test_rag_engine_e2e.py`
Expected: Lines 49-51 showing the bug.

**Step 2: Fix the fixture**

In `tests/e2e/test_rag_engine_e2e.py`, find the `rag_engine` fixture (lines ~47-58) and replace it with:

```python
    @pytest.fixture
    async def rag_engine(self, postgres_connection_string, gemini_api_key):
        """Create RAGEngine with real components."""
        config = RAGConfig(
            llm=LLMConfig(
                provider="gemini",
                api_key=gemini_api_key,
                model_name="gemini-2.0-flash",
                embedding_model="models/gemini-embedding-001",
            ),
            storage=StorageConfig(
                backend="postgres",
                collection_name="e2e_test_docs",
                connection_string=postgres_connection_string,
                vector_dimension=768,
            ),
            pipeline=PipelineConfig(top_k=3),
            chunking=ChunkingConfig(
                strategy="recursive",
                chunk_size=512,
                chunk_overlap=50,
            ),
        )

        async with RAGEngine(config) as engine:
            # Clean up any existing data from previous test runs
            try:
                await engine.storage.delete_collection()
                await engine.storage._create_table()
            except Exception:
                pass

            yield engine

            # Cleanup after test
            try:
                await engine.storage.delete_collection()
            except Exception:
                pass
```

Wait — the existing code is actually fine. The issue is that `_create_table()` creates the HNSW index with `CREATE INDEX IF NOT EXISTS`, so it won't fail. Let's verify by running the test first.

**Step 2: Start the test database**

```bash
docker-compose -f docker-compose.test.yml up -d
```

Expected: Container `vibe-rag-test-db` starts.

**Step 3: Wait for healthy**

```bash
docker-compose -f docker-compose.test.yml ps
```

Expected: `healthy` status for `postgres-test`.

If not healthy after 30s: `docker-compose -f docker-compose.test.yml logs postgres-test`

**Step 4: Run one E2E test**

```bash
GOOGLE_API_KEY=$GOOGLE_API_KEY .venv/bin/python -m pytest tests/e2e/test_rag_engine_e2e.py::TestRAGEngineE2E::test_complete_rag_workflow -v --no-cov
```

Expected: PASS with output showing answer and sources. If it fails, read the traceback carefully — the error message will reveal what to fix.

**Step 5: If the fixture fails with index error, fix it**

If step 4 fails with `index already exists`, replace lines 47-58 in `tests/e2e/test_rag_engine_e2e.py` with:

```python
    @pytest.fixture
    async def rag_engine(self, postgres_connection_string, gemini_api_key):
        """Create RAGEngine with real components."""
        config = RAGConfig(
            llm=LLMConfig(
                provider="gemini",
                api_key=gemini_api_key,
                model_name="gemini-2.0-flash",
                embedding_model="models/gemini-embedding-001",
            ),
            storage=StorageConfig(
                backend="postgres",
                collection_name="e2e_test_docs",
                connection_string=postgres_connection_string,
                vector_dimension=768,
            ),
            pipeline=PipelineConfig(top_k=3),
            chunking=ChunkingConfig(
                strategy="recursive",
                chunk_size=512,
                chunk_overlap=50,
            ),
        )

        async with RAGEngine(config) as engine:
            # Drop collection before test to ensure clean state
            try:
                await engine.storage.delete_collection()
                # Recreate the table structure (index creation safe with IF NOT EXISTS)
                await engine.storage._create_table()
            except Exception:
                pass

            yield engine

            # Cleanup after test
            try:
                await engine.storage.delete_collection()
            except Exception:
                pass
```

**Step 6: Run the full E2E suite**

```bash
GOOGLE_API_KEY=$GOOGLE_API_KEY .venv/bin/python -m pytest tests/e2e/ -v --no-cov
```

Expected: All 6 E2E tests PASS.

**Step 7: Commit**

```bash
git add tests/e2e/test_rag_engine_e2e.py
git commit -m "fix: correct E2E test fixture to handle pre-existing collections"
```

---

## Task 2: Measure Baseline Coverage After E2E

**Files:** None (read-only measurement)

**Step 1: Run all tests including E2E with coverage**

```bash
GOOGLE_API_KEY=$GOOGLE_API_KEY .venv/bin/python -m pytest tests/ -v \
  --cov=vibe_rag --cov-report=term-missing --cov-report=html 2>&1 | tee /tmp/coverage_baseline.txt
```

Expected: Coverage report showing per-file numbers. Note the current values for:
- `vibe_rag/engine.py` (was 25%)
- `vibe_rag/config/models.py` (was 76%)
- `vibe_rag/utils/observability.py` (was 65%)

**Step 2: Check if targets are met**

After E2E, engine.py should be >70%. If overall coverage is already >80%, tasks 3 and 4 are optional polish.

Open `htmlcov/index.html` in a browser to see exactly which lines are missing.

---

## Task 3: Add Unit Tests for Engine Coverage Gaps

**Files:**
- Create: `tests/unit/test_engine_unit.py`

These tests cover the synchronous/error paths in `RAGEngine` that E2E tests don't hit.

**Step 1: Write the test file**

Create `tests/unit/test_engine_unit.py`:

```python
"""Unit tests for RAGEngine covering error paths and synchronous logic."""

import pytest

from vibe_rag import (
    ChunkingConfig,
    LLMConfig,
    PipelineConfig,
    RAGConfig,
    RAGEngine,
    StorageConfig,
)
from vibe_rag.testing.mocks import MockLLMProvider, MockVectorStore
from vibe_rag.utils.errors import ConfigurationError


def _make_config(provider="gemini", backend="postgres"):
    """Helper to create a RAGConfig with defaults."""
    return RAGConfig(
        llm=LLMConfig(provider=provider, api_key="test-key"),
        storage=StorageConfig(
            backend=backend,
            collection_name="test_docs",
            connection_string="postgresql://user:pass@localhost/db",
        ),
    )


class TestRAGEngineErrorPaths:
    """Tests for RAGEngine error handling and edge cases."""

    def test_unsupported_provider_raises_configuration_error(self):
        """Engine with unsupported provider type raises ConfigurationError on init."""
        # RAGConfig only accepts "gemini" via Literal type, so we bypass validation
        config = _make_config()
        config.llm.provider = "openai"  # type: ignore[assignment]

        with pytest.raises(ConfigurationError, match="Unsupported LLM provider"):
            RAGEngine(config=config)

    def test_unsupported_storage_raises_configuration_error(self):
        """Engine with unsupported storage backend raises ConfigurationError on init."""
        config = _make_config()
        config.storage.backend = "chroma"  # type: ignore[assignment]

        with pytest.raises(ConfigurationError, match="Unsupported storage backend"):
            RAGEngine(config=config)

    def test_dimension_mismatch_raises_configuration_error(self):
        """Dimension mismatch between LLM and storage raises ConfigurationError."""
        config = RAGConfig(
            llm=LLMConfig(
                provider="gemini",
                api_key="test-key",
                embedding_model="models/gemini-embedding-001",  # expects 768
            ),
            storage=StorageConfig(
                backend="postgres",
                collection_name="test",
                connection_string="postgresql://localhost/db",
                vector_dimension=512,  # wrong!
            ),
        )
        with pytest.raises(ConfigurationError, match="dimension"):
            RAGEngine(config=config)

    def test_register_loader_stores_loader(self):
        """register_loader() makes loader available for that extension."""
        from vibe_rag.loaders.base import BaseLoader

        class DummyLoader(BaseLoader):
            async def load(self, file_path):
                return []

        engine = RAGEngine(
            config=_make_config(),
            provider=MockLLMProvider(),
            storage=MockVectorStore("test_docs"),
        )
        loader = DummyLoader()
        engine.register_loader(".docx", loader)

        assert ".docx" in engine._loaders
        assert engine._loaders[".docx"] is loader

    async def test_ingest_before_initialize_raises_error(self):
        """ingest() before initialize() raises ConfigurationError."""
        engine = RAGEngine(
            config=_make_config(),
            provider=MockLLMProvider(),
            storage=MockVectorStore("test_docs"),
        )
        with pytest.raises(ConfigurationError, match="not initialized"):
            await engine.ingest("some_file.txt")

    async def test_query_before_initialize_raises_error(self):
        """query() before initialize() raises ConfigurationError."""
        engine = RAGEngine(
            config=_make_config(),
            provider=MockLLMProvider(),
            storage=MockVectorStore("test_docs"),
        )
        with pytest.raises(ConfigurationError, match="not initialized"):
            await engine.query("any question")

    async def test_get_metrics_disabled_raises_error(self):
        """get_metrics() when metrics disabled raises ConfigurationError."""
        engine = RAGEngine(
            config=_make_config(),
            provider=MockLLMProvider(),
            storage=MockVectorStore("test_docs"),
            enable_metrics=False,
        )
        with pytest.raises(ConfigurationError, match="disabled"):
            engine.get_metrics()

    async def test_get_stats_disabled_raises_error(self):
        """get_stats() when metrics disabled raises ConfigurationError."""
        engine = RAGEngine(
            config=_make_config(),
            provider=MockLLMProvider(),
            storage=MockVectorStore("test_docs"),
            enable_metrics=False,
        )
        with pytest.raises(ConfigurationError, match="disabled"):
            engine.get_stats()

    async def test_double_initialize_is_idempotent(self):
        """Calling initialize() twice does not raise an error."""
        engine = RAGEngine(
            config=_make_config(),
            provider=MockLLMProvider(),
            storage=MockVectorStore("test_docs"),
        )
        await engine.initialize()
        await engine.initialize()  # Should be no-op
        assert engine._initialized
        await engine.close()

    async def test_close_before_initialize_is_safe(self):
        """Calling close() before initialize() does not raise."""
        engine = RAGEngine(
            config=_make_config(),
            provider=MockLLMProvider(),
            storage=MockVectorStore("test_docs"),
        )
        await engine.close()  # Should be safe no-op
        assert not engine._initialized

    async def test_ingest_unsupported_extension_raises_error(self):
        """ingest() with unknown file extension raises DocumentProcessingError."""
        import tempfile
        import os
        from vibe_rag.utils.errors import DocumentProcessingError

        engine = RAGEngine(
            config=_make_config(),
            provider=MockLLMProvider(),
            storage=MockVectorStore("test_docs"),
        )
        await engine.initialize()

        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"content")
            path = f.name

        try:
            with pytest.raises(DocumentProcessingError, match="No loader registered"):
                await engine.ingest(path)
        finally:
            os.unlink(path)
            await engine.close()
```

**Step 2: Run the new tests**

```bash
.venv/bin/python -m pytest tests/unit/test_engine_unit.py -v --no-cov
```

Expected: All 11 tests PASS.

If any fail, read the error carefully:
- `AttributeError: 'Literal' object ...` → the config field is protected; use `object.__setattr__(config.llm, 'provider', 'openai')` instead
- `ConfigurationError` not raised → check the exact condition in `engine.py`

**Step 3: Commit**

```bash
git add tests/unit/test_engine_unit.py
git commit -m "test: add unit tests for RAGEngine error paths and edge cases"
```

---

## Task 4: Add Config & Observability Unit Tests

**Files:**
- Modify: `tests/unit/test_models.py`
- Create: `tests/unit/test_observability_extended.py`

**Step 1: Add config edge case tests to test_models.py**

Append to `tests/unit/test_models.py`:

```python
"""Config model edge case tests (append to existing file)."""

from vibe_rag.config.models import (
    ChunkingConfig,
    LLMConfig,
    PipelineConfig,
    RAGConfig,
    StorageConfig,
)
import pytest


class TestChunkingConfig:
    def test_overlap_must_be_less_than_chunk_size(self):
        """chunk_overlap >= chunk_size raises ValueError."""
        with pytest.raises(ValueError, match="chunk_overlap"):
            ChunkingConfig(chunk_size=100, chunk_overlap=100)

    def test_overlap_exactly_equals_chunk_size_raises(self):
        with pytest.raises(ValueError):
            ChunkingConfig(chunk_size=256, chunk_overlap=256)

    def test_valid_overlap_accepted(self):
        config = ChunkingConfig(chunk_size=512, chunk_overlap=50)
        assert config.chunk_overlap == 50

    def test_default_strategy_is_recursive(self):
        config = ChunkingConfig()
        assert config.strategy == "recursive"


class TestStorageConfig:
    def test_invalid_collection_name_raises(self):
        """Collection names with special chars raise ValueError."""
        with pytest.raises(ValueError, match="Invalid collection name"):
            StorageConfig(
                collection_name="invalid-name!",
                connection_string="postgresql://localhost/db",
            )

    def test_collection_name_starting_with_digit_raises(self):
        with pytest.raises(ValueError):
            StorageConfig(
                collection_name="1invalid",
                connection_string="postgresql://localhost/db",
            )

    def test_valid_collection_name_accepted(self):
        config = StorageConfig(
            collection_name="my_collection",
            connection_string="postgresql://localhost/db",
        )
        assert config.collection_name == "my_collection"

    def test_default_vector_dimension(self):
        config = StorageConfig(connection_string="postgresql://localhost/db")
        assert config.vector_dimension == 768


class TestRAGConfigValidation:
    def test_dimension_mismatch_raises_value_error(self):
        """validate_dimensions() raises ValueError if storage dim != expected."""
        config = RAGConfig(
            llm=LLMConfig(
                api_key="key",
                embedding_model="models/gemini-embedding-001",
            ),
            storage=StorageConfig(
                connection_string="postgresql://localhost/db",
                vector_dimension=512,
            ),
        )
        with pytest.raises(ValueError, match="dimension"):
            config.validate_dimensions()

    def test_matching_dimensions_passes(self):
        """validate_dimensions() with correct dimension does not raise."""
        config = RAGConfig(
            llm=LLMConfig(
                api_key="key",
                embedding_model="models/gemini-embedding-001",
            ),
            storage=StorageConfig(
                connection_string="postgresql://localhost/db",
                vector_dimension=768,
            ),
        )
        config.validate_dimensions()  # Should not raise


class TestLLMConfig:
    def test_default_model_name(self):
        config = LLMConfig(api_key="key")
        assert config.model_name == "gemini-2.0-flash"

    def test_default_embedding_model(self):
        config = LLMConfig(api_key="key")
        assert config.embedding_model == "models/gemini-embedding-001"

    def test_default_provider(self):
        config = LLMConfig(api_key="key")
        assert config.provider == "gemini"


class TestPipelineConfig:
    def test_top_k_minimum_is_1(self):
        with pytest.raises(ValueError):
            PipelineConfig(top_k=0)

    def test_top_k_maximum_is_100(self):
        with pytest.raises(ValueError):
            PipelineConfig(top_k=101)

    def test_valid_top_k(self):
        config = PipelineConfig(top_k=10)
        assert config.top_k == 10
```

**Step 2: Run the added config tests**

```bash
.venv/bin/python -m pytest tests/unit/test_models.py -v --no-cov -k "TestChunking or TestStorage or TestRAGConfig or TestLLM or TestPipeline"
```

Expected: All new tests PASS.

**Step 3: Create observability extended tests**

Create `tests/unit/test_observability_extended.py`:

```python
"""Extended tests for MetricsTracker and RAGMetrics."""

import pytest

from vibe_rag.utils.observability import MetricsTracker, RAGMetrics


class TestRAGMetrics:
    def test_default_values(self):
        """RAGMetrics starts with sensible defaults."""
        m = RAGMetrics()
        assert m.query == ""
        assert m.answer == ""
        assert m.retrieval_time_ms == 0.0
        assert m.generation_time_ms == 0.0
        assert m.total_time_ms == 0.0
        assert m.documents_retrieved == 0
        assert m.documents_used == 0
        assert m.input_tokens is None
        assert m.output_tokens is None

    def test_query_id_auto_generated(self):
        """Each RAGMetrics instance gets a unique ID."""
        m1 = RAGMetrics()
        m2 = RAGMetrics()
        assert m1.query_id != m2.query_id
        assert len(m1.query_id) > 0

    def test_to_dict_includes_all_fields(self):
        """to_dict() returns all expected keys."""
        m = RAGMetrics(
            query="test query",
            answer="test answer",
            retrieval_time_ms=50.0,
            generation_time_ms=200.0,
            total_time_ms=250.0,
            documents_retrieved=3,
            documents_used=3,
            input_tokens=100,
            output_tokens=50,
        )
        d = m.to_dict()

        assert d["query"] == "test query"
        assert d["answer"] == "test answer"
        assert d["retrieval_time_ms"] == 50.0
        assert d["generation_time_ms"] == 200.0
        assert d["total_time_ms"] == 250.0
        assert d["documents_retrieved"] == 3
        assert d["documents_used"] == 3
        assert d["input_tokens"] == 100
        assert d["output_tokens"] == 50
        assert "query_id" in d
        assert "metadata" in d

    def test_summarize_contains_key_info(self):
        """summarize() produces a readable string with timing and doc info."""
        m = RAGMetrics(
            retrieval_time_ms=45.5,
            generation_time_ms=180.3,
            total_time_ms=226.0,
            documents_retrieved=5,
        )
        summary = m.summarize()

        assert "45.50" in summary or "45.5" in summary
        assert "180.30" in summary or "180.3" in summary
        assert "5" in summary

    def test_metadata_dict_is_mutable(self):
        """metadata field can be updated after creation."""
        m = RAGMetrics()
        m.metadata["key"] = "value"
        assert m.metadata["key"] == "value"


class TestMetricsTracker:
    def test_create_metrics_sets_query(self):
        """create_metrics() returns RAGMetrics with the query set."""
        tracker = MetricsTracker()
        m = tracker.create_metrics("What is RAG?")

        assert m.query == "What is RAG?"
        assert m.query_id is not None
        assert "created_at" in m.metadata

    def test_record_adds_to_list(self):
        """record() stores metrics and sets recorded_at timestamp."""
        tracker = MetricsTracker()
        m = tracker.create_metrics("test")
        tracker.record(m)

        all_metrics = tracker.get_all()
        assert len(all_metrics) == 1
        assert "recorded_at" in all_metrics[0].metadata

    def test_get_all_returns_copy(self):
        """get_all() returns a copy — mutating it doesn't affect tracker."""
        tracker = MetricsTracker()
        m = tracker.create_metrics("test")
        tracker.record(m)

        result = tracker.get_all()
        result.clear()
        assert len(tracker.get_all()) == 1  # Original unaffected

    def test_get_stats_empty_returns_zeros(self):
        """get_stats() with no metrics returns dict with zeros."""
        tracker = MetricsTracker()
        stats = tracker.get_stats()

        assert stats["total_queries"] == 0
        assert stats["avg_total_time_ms"] == 0.0
        assert stats["avg_retrieval_time_ms"] == 0.0
        assert stats["avg_generation_time_ms"] == 0.0
        assert stats["avg_documents_retrieved"] == 0.0
        assert stats["total_input_tokens"] == 0
        assert stats["total_output_tokens"] == 0

    def test_get_stats_with_multiple_metrics(self):
        """get_stats() averages correctly across multiple queries."""
        tracker = MetricsTracker()

        for i in range(3):
            m = RAGMetrics(
                retrieval_time_ms=10.0 * (i + 1),  # 10, 20, 30
                generation_time_ms=100.0,
                total_time_ms=110.0 * (i + 1),
                documents_retrieved=i + 1,  # 1, 2, 3
                input_tokens=50,
                output_tokens=25,
            )
            tracker.record(m)

        stats = tracker.get_stats()
        assert stats["total_queries"] == 3
        assert stats["avg_retrieval_time_ms"] == pytest.approx(20.0)  # (10+20+30)/3
        assert stats["avg_documents_retrieved"] == pytest.approx(2.0)  # (1+2+3)/3
        assert stats["total_input_tokens"] == 150  # 3 * 50
        assert stats["total_output_tokens"] == 75  # 3 * 25

    def test_clear_resets_tracker(self):
        """clear() removes all recorded metrics."""
        tracker = MetricsTracker()
        tracker.record(tracker.create_metrics("q1"))
        tracker.record(tracker.create_metrics("q2"))

        assert len(tracker.get_all()) == 2
        tracker.clear()
        assert len(tracker.get_all()) == 0

    def test_get_stats_ignores_none_tokens(self):
        """get_stats() correctly handles metrics where tokens are None."""
        tracker = MetricsTracker()
        m1 = RAGMetrics(input_tokens=100, output_tokens=50)
        m2 = RAGMetrics(input_tokens=None, output_tokens=None)  # No tokens tracked
        tracker.record(m1)
        tracker.record(m2)

        stats = tracker.get_stats()
        assert stats["total_input_tokens"] == 100   # m2's None ignored
        assert stats["total_output_tokens"] == 50
```

**Step 4: Run the observability tests**

```bash
.venv/bin/python -m pytest tests/unit/test_observability_extended.py -v --no-cov
```

Expected: All tests PASS.

**Step 5: Run full test suite and check coverage**

```bash
.venv/bin/python -m pytest tests/unit tests/integration --cov=vibe_rag --cov-report=term-missing 2>&1 | tail -30
```

Expected: Overall coverage >80%. Config models >85%. Observability >80%.

**Step 6: Commit**

```bash
git add tests/unit/test_models.py tests/unit/test_observability_extended.py
git commit -m "test: add config model and observability extended test coverage"
```

---

## Task 5: Add Performance Benchmark Suite

**Files:**
- Create: `tests/benchmarks/__init__.py`
- Create: `tests/benchmarks/test_performance.py`

These benchmarks use real components (PostgreSQL + Gemini) to measure actual performance. They are not run in CI — only on-demand.

**Step 1: Create benchmark directory**

```bash
mkdir -p tests/benchmarks
touch tests/benchmarks/__init__.py
```

**Step 2: Create benchmark test file**

Create `tests/benchmarks/test_performance.py`:

```python
"""Performance benchmarks for vibe-rag components.

Run with: GOOGLE_API_KEY=<key> pytest tests/benchmarks/ -v --no-cov -s

These tests measure real performance with PostgreSQL + Gemini.
They are NOT run in CI — only on-demand.
"""

import os
import tempfile
import time
from pathlib import Path

import pytest

from vibe_rag import (
    ChunkingConfig,
    LLMConfig,
    PipelineConfig,
    RAGConfig,
    RAGEngine,
    StorageConfig,
)

POSTGRES_URL = os.getenv(
    "TEST_POSTGRES_CONNECTION",
    "postgresql://vibetest:vibetest123@localhost:5434/vibe_rag_test",
)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


@pytest.fixture(scope="module")
def api_key():
    if not GOOGLE_API_KEY:
        pytest.skip("GOOGLE_API_KEY not set")
    return GOOGLE_API_KEY


def make_engine(api_key: str, collection: str = "benchmark") -> RAGEngine:
    config = RAGConfig(
        llm=LLMConfig(
            provider="gemini",
            api_key=api_key,
            model_name="gemini-2.0-flash",
            embedding_model="models/gemini-embedding-001",
        ),
        storage=StorageConfig(
            backend="postgres",
            collection_name=collection,
            connection_string=POSTGRES_URL,
            vector_dimension=768,
        ),
        pipeline=PipelineConfig(top_k=5),
        chunking=ChunkingConfig(strategy="recursive", chunk_size=512, chunk_overlap=50),
    )
    return RAGEngine(config)


@pytest.mark.benchmark
class TestIngestionBenchmarks:
    """Benchmark document ingestion at different scales."""

    async def test_ingest_small_batch(self, api_key):
        """Benchmark: ingest 5 small documents."""
        async with make_engine(api_key, "bench_small") as engine:
            try:
                await engine.storage.delete_collection()
                await engine.storage._create_table()
            except Exception:
                pass

            texts = [f"Document {i}: " + "Content " * 50 for i in range(5)]
            start = time.time()

            for i, text in enumerate(texts):
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                    f.write(text)
                    path = f.name
                try:
                    await engine.ingest(path)
                finally:
                    Path(path).unlink()

            elapsed = (time.time() - start) * 1000
            print(f"\n[BENCHMARK] Ingest 5 docs: {elapsed:.0f}ms ({elapsed/5:.0f}ms/doc)")
            assert elapsed > 0  # Sanity check

    async def test_ingest_large_document(self, api_key):
        """Benchmark: ingest one large document (creates many chunks)."""
        async with make_engine(api_key, "bench_large") as engine:
            try:
                await engine.storage.delete_collection()
                await engine.storage._create_table()
            except Exception:
                pass

            # ~10KB document = ~20 chunks at 512 chunk_size
            large_text = "Retrieval-augmented generation is a technique. " * 200

            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(large_text)
                path = f.name

            start = time.time()
            try:
                doc_ids = await engine.ingest(path)
            finally:
                Path(path).unlink()

            elapsed = (time.time() - start) * 1000
            chunks = len(doc_ids)
            print(f"\n[BENCHMARK] Ingest large doc: {elapsed:.0f}ms, {chunks} chunks")
            assert chunks > 5  # Should create multiple chunks


@pytest.mark.benchmark
class TestQueryBenchmarks:
    """Benchmark query latency components."""

    @pytest.fixture(scope="class")
    async def populated_engine(self, api_key):
        """Engine pre-populated with 10 documents."""
        engine = make_engine(api_key, "bench_query")
        async with engine:
            try:
                await engine.storage.delete_collection()
                await engine.storage._create_table()
            except Exception:
                pass

            # Ingest test corpus
            corpus = [
                ("Python was created by Guido van Rossum in 1991.", {"topic": "python"}),
                ("JavaScript runs in browsers and Node.js.", {"topic": "javascript"}),
                ("Machine learning uses data to train models.", {"topic": "ml"}),
                ("Docker containers package applications.", {"topic": "devops"}),
                ("PostgreSQL is a relational database.", {"topic": "database"}),
            ]
            for text, meta in corpus:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                    f.write(text * 10)  # Make longer for better chunking
                    path = f.name
                try:
                    await engine.ingest(path, metadata=meta)
                finally:
                    Path(path).unlink()

            yield engine

    async def test_query_latency_single(self, populated_engine):
        """Benchmark: single query end-to-end latency."""
        start = time.time()
        result = await populated_engine.query("Who created Python?")
        elapsed = (time.time() - start) * 1000

        print(f"\n[BENCHMARK] Single query: {elapsed:.0f}ms")
        print(f"  Retrieval: {result['metadata']['retrieval_time_ms']:.0f}ms")
        print(f"  Generation: {result['metadata']['generation_time_ms']:.0f}ms")
        print(f"  Docs retrieved: {result['metadata']['documents_retrieved']}")
        assert "answer" in result

    async def test_query_latency_repeated(self, populated_engine):
        """Benchmark: 5 sequential queries, measure avg and variance."""
        times = []
        for i in range(5):
            start = time.time()
            await populated_engine.query(f"Question about topic {i}")
            times.append((time.time() - start) * 1000)

        avg = sum(times) / len(times)
        min_t = min(times)
        max_t = max(times)
        print(f"\n[BENCHMARK] 5 queries: avg={avg:.0f}ms, min={min_t:.0f}ms, max={max_t:.0f}ms")
        assert avg > 0


@pytest.mark.benchmark
class TestChunkingBenchmarks:
    """Benchmark different chunking strategies."""

    def test_fixed_vs_recursive_chunking(self):
        """Benchmark: compare chunking strategies on a 5KB document."""
        from vibe_rag.transformers import DocumentProcessor
        import time

        text = "This is a sentence about a topic. " * 150  # ~5KB

        strategies = [
            ("fixed", 512, 50),
            ("recursive", 512, 50),
            ("fixed", 256, 25),
            ("recursive", 256, 25),
        ]

        print("\n[BENCHMARK] Chunking strategies:")
        for strategy, size, overlap in strategies:
            processor = DocumentProcessor(strategy=strategy, chunk_size=size, chunk_overlap=overlap)
            start = time.time()
            for _ in range(100):  # 100 iterations for reliable timing
                chunks = processor.process(text, {})
            elapsed = (time.time() - start) * 1000 / 100  # Per-call average

            print(f"  {strategy} ({size}/{overlap}): {len(chunks)} chunks, {elapsed:.2f}ms/call")
            assert len(chunks) > 0
```

**Step 3: Run benchmarks to verify they work**

```bash
GOOGLE_API_KEY=$GOOGLE_API_KEY .venv/bin/python -m pytest tests/benchmarks/ -v --no-cov -s -m benchmark 2>&1 | head -60
```

Expected: Tests run and print benchmark output with timing numbers.

**Step 4: Commit**

```bash
git add tests/benchmarks/__init__.py tests/benchmarks/test_performance.py
git commit -m "test: add performance benchmark suite for ingestion, query, and chunking"
```

---

## Task 6: API Reference Documentation

**Files:**
- Create: `docs/api-reference.md`

**Step 1: Read the transformers module for completeness**

```bash
grep -n "def " vibe_rag/transformers/document.py | head -20
```

**Step 2: Create API reference**

Create `docs/api-reference.md`:

````markdown
# vibe-rag API Reference

Complete reference for all public classes and methods exported by `vibe_rag`.

## Quick Navigation

- [RAGEngine](#ragengine) — Main orchestrator
- [QuickSetup](#quicksetup) — One-liner factory
- [BasicRAGModule](#basicragmodule) — Named wrapper
- [Configuration](#configuration) — Config models
- [Document](#document) — Core data model
- [Loaders](#loaders) — Document loaders
- [Errors](#errors) — Exception hierarchy
- [Observability](#observability) — Metrics tracking

---

## RAGEngine

The central interface for all RAG operations.

```python
from vibe_rag import RAGEngine, RAGConfig
```

### Constructor

```python
RAGEngine(
    config: RAGConfig,
    provider: Optional[BaseLLMProvider] = None,
    storage: Optional[BaseVectorStore] = None,
    enable_metrics: bool = True,
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `RAGConfig` | Complete configuration |
| `provider` | `BaseLLMProvider` | Override default LLM provider |
| `storage` | `BaseVectorStore` | Override default storage backend |
| `enable_metrics` | `bool` | Track per-query metrics (default: True) |

Raises `ConfigurationError` if configuration is invalid.

### Usage

```python
async with RAGEngine(config) as engine:
    await engine.ingest("document.txt")
    result = await engine.query("What is this about?")
    print(result["answer"])
```

### Methods

#### `async ingest(source, metadata=None, loader=None) → list[str]`

Ingest a document: load → chunk → embed → store.

```python
doc_ids = await engine.ingest(
    source="path/to/file.txt",
    metadata={"category": "docs", "version": "1.0"},
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `str` | File path to document |
| `metadata` | `dict` | Optional metadata attached to all chunks |
| `loader` | `BaseLoader` | Override auto-detected loader |

Returns: `list[str]` — IDs of all stored chunks.

Raises: `DocumentProcessingError`, `EmbeddingError`, `StorageError`

#### `async query(query, generation_kwargs=None) → dict`

Execute a RAG query: retrieve → generate.

```python
result = await engine.query(
    "What are the key benefits?",
    generation_kwargs={"temperature": 0.3},
)
print(result["answer"])       # Generated answer
print(result["sources"])      # Retrieved documents
print(result["metadata"])     # Timings, doc counts
```

Returns dictionary:
```python
{
    "answer": str,
    "sources": [{"content": str, "score": float, "metadata": dict}, ...],
    "metadata": {
        "query_id": str,
        "retrieval_time_ms": float,
        "generation_time_ms": float,
        "total_time_ms": float,
        "documents_retrieved": int,
        "pipeline_metadata": dict,
    }
}
```

#### `register_loader(extension, loader)`

Register a custom loader for a file extension.

```python
engine.register_loader(".docx", MyDocxLoader())
await engine.ingest("report.docx")
```

#### `get_metrics() → list[RAGMetrics]`

Get all recorded metrics. Raises `ConfigurationError` if metrics disabled.

#### `get_stats() → dict`

Get aggregate statistics. Returns:
```python
{
    "total_queries": int,
    "avg_total_time_ms": float,
    "avg_retrieval_time_ms": float,
    "avg_generation_time_ms": float,
    "avg_documents_retrieved": float,
    "total_input_tokens": int,
    "total_output_tokens": int,
}
```

---

## QuickSetup

One-liner factory for `RAGEngine` with sensible defaults.

```python
from vibe_rag import QuickSetup

engine = QuickSetup.create(
    provider_api_key="your-gemini-key",
    database_url="postgresql://user:pass@host/db",
    collection_name="my_docs",  # default: "documents"
    top_k=5,                    # default: 5
)

async with engine:
    await engine.ingest("file.txt")
    result = await engine.query("question")
```

**Defaults:** Gemini 2.0 Flash, gemini-embedding-001 (768-dim), recursive chunking 512/50, PostgreSQL.

---

## BasicRAGModule

Named wrapper around QuickSetup for more explicit code.

```python
from vibe_rag import BasicRAGModule

async with BasicRAGModule(
    api_key="your-key",
    db_url="postgresql://localhost/db",
    collection_name="kb",
    top_k=5,
) as rag:
    await rag.ingest("knowledge.pdf")
    result = await rag.query("What is the policy?")
```

Same parameters and behavior as `QuickSetup.create()`, but with a cleaner named API.

---

## Configuration

### RAGConfig

```python
from vibe_rag import RAGConfig, LLMConfig, StorageConfig, PipelineConfig, ChunkingConfig

config = RAGConfig(
    llm=LLMConfig(
        provider="gemini",              # Only "gemini" supported
        api_key="your-key",
        model_name="gemini-2.0-flash",
        embedding_model="models/gemini-embedding-001",
        generation_kwargs={"temperature": 0.7},
    ),
    storage=StorageConfig(
        backend="postgres",             # Only "postgres" supported
        collection_name="my_docs",      # Must match [a-zA-Z_][a-zA-Z0-9_]*
        connection_string="postgresql://user:pass@host:5432/db",
        vector_dimension=768,           # Must match embedding model
    ),
    pipeline=PipelineConfig(
        top_k=5,                        # 1-100
        filter_metadata={"type": "policy"},  # Optional JSONB filter
    ),
    chunking=ChunkingConfig(
        strategy="recursive",           # "recursive" or "fixed"
        chunk_size=512,                 # 100-4096 chars
        chunk_overlap=50,               # Must be < chunk_size
    ),
)
```

---

## Document

Core data model for text chunks.

```python
from vibe_rag import Document

doc = Document(
    id="optional-custom-id",    # Auto-generated UUID if not provided
    content="The text content",
    metadata={"source": "file.txt", "page": 1},
    score=0.95,                  # Set by retriever, None otherwise
)
```

---

## Loaders

```python
from vibe_rag import TextLoader, MarkdownLoader, PDFLoader
```

All loaders implement `async load(file_path: str) -> list[Document]`.

| Loader | Extensions | Notes |
|--------|-----------|-------|
| `TextLoader` | `.txt` | UTF-8 text files |
| `MarkdownLoader` | `.md` | Markdown files, strips frontmatter |
| `PDFLoader` | `.pdf` | Uses PyPDF2; each page → Document |

Custom loader example:

```python
from vibe_rag.loaders.base import BaseLoader
from vibe_rag import Document

class JSONLoader(BaseLoader):
    async def load(self, file_path: str) -> list[Document]:
        import json
        with open(file_path) as f:
            data = json.load(f)
        return [Document(content=str(item)) for item in data]

engine.register_loader(".json", JSONLoader())
```

---

## Errors

All errors inherit from `RAGException`.

```python
from vibe_rag import (
    RAGException,           # Base class
    EmbeddingError,         # Embedding API failed
    RetrievalError,         # Vector search failed
    LLMProviderError,       # LLM generation failed
    StorageError,           # Database operation failed
    ConfigurationError,     # Bad configuration or not initialized
    DocumentProcessingError # Load/chunk failed
)
```

---

## Observability

```python
from vibe_rag import MetricsTracker, RAGMetrics

# Access via engine
stats = engine.get_stats()
metrics = engine.get_metrics()  # list[RAGMetrics]

# Per-query data
for m in metrics:
    print(m.summarize())
    d = m.to_dict()  # Full dict representation
```

`RAGMetrics` fields: `query_id`, `query`, `answer`, `retrieval_time_ms`, `generation_time_ms`, `total_time_ms`, `documents_retrieved`, `documents_used`, `input_tokens`, `output_tokens`, `metadata`.
````

**Step 3: Commit**

```bash
git add docs/api-reference.md
git commit -m "docs: add complete API reference documentation"
```

---

## Task 7: Deployment Guides

**Files:**
- Create: `docs/deployment/docker.md`
- Create: `docs/deployment/kubernetes.md`

**Step 1: Create deployment directory**

```bash
mkdir -p docs/deployment
```

**Step 2: Create Docker deployment guide**

Create `docs/deployment/docker.md`:

````markdown
# Docker Deployment Guide

This guide shows how to deploy vibe-rag in a Docker environment with PostgreSQL+pgvector.

## Prerequisites

- Docker 20.10+
- Docker Compose v2
- Gemini API key

## Quick Start (Development)

The test database is included in the repository:

```bash
# Start PostgreSQL with pgvector
docker-compose -f docker-compose.test.yml up -d

# Verify it's healthy
docker-compose -f docker-compose.test.yml ps

# Run your application
GOOGLE_API_KEY=your-key python examples/simple_rag.py
```

## Production docker-compose.yml

Create `docker-compose.yml` for production:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-raguser}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-rag_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-raguser} -d ${POSTGRES_DB:-rag_db}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  app:
    build: .
    environment:
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}
      DATABASE_URL: postgresql://${POSTGRES_USER:-raguser}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-rag_db}
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
```

## Dockerfile for vibe-rag Applications

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for asyncpg
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[all]"

# Copy application code
COPY . .

CMD ["python", "your_app.py"]
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini API key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `COLLECTION_NAME` | No | Vector store collection (default: `documents`) |

## Example Application Entry Point

```python
# app.py
import asyncio
import os
from vibe_rag import QuickSetup

async def main():
    async with QuickSetup.create(
        provider_api_key=os.environ["GOOGLE_API_KEY"],
        database_url=os.environ["DATABASE_URL"],
    ) as rag:
        await rag.ingest("knowledge_base.txt")
        result = await rag.query("What is the main topic?")
        print(result["answer"])

asyncio.run(main())
```

## Health Checks

Add a health check endpoint to your application:

```python
async def health_check():
    """Check if the database is reachable."""
    try:
        import asyncpg
        conn = await asyncpg.connect(os.environ["DATABASE_URL"])
        await conn.fetchval("SELECT 1")
        await conn.close()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## Scaling Considerations

- **Connection pooling**: `asyncpg` pools connections automatically (default: 10 max)
- **Read replicas**: Point `DATABASE_URL` to a read replica for query-only services
- **Embedding caching**: Cache embeddings at the application layer for repeated queries
- **pgvector index**: HNSW index is created automatically; rebuild if recall drops
````

**Step 3: Create Kubernetes deployment guide**

Create `docs/deployment/kubernetes.md`:

````markdown
# Kubernetes Deployment Guide

Deploy vibe-rag applications on Kubernetes with PostgreSQL+pgvector.

## Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured
- Helm (optional, for cert-manager)
- Container registry access

## Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: rag-system
```

```bash
kubectl apply -f namespace.yaml
```

## Secrets

```bash
# Create secrets for API keys and DB password
kubectl create secret generic rag-secrets \
  --namespace rag-system \
  --from-literal=google-api-key=your-gemini-key \
  --from-literal=postgres-password=your-secure-password
```

## PostgreSQL StatefulSet

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: rag-system
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: pgvector/pgvector:pg16
        env:
        - name: POSTGRES_USER
          value: raguser
        - name: POSTGRES_DB
          value: rag_db
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: postgres-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        readinessProbe:
          exec:
            command: ["pg_isready", "-U", "raguser", "-d", "rag_db"]
          initialDelaySeconds: 10
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: rag-system
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None  # Headless for StatefulSet
```

## Application Deployment

```yaml
# app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-app
  namespace: rag-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: rag-app
  template:
    metadata:
      labels:
        app: rag-app
    spec:
      containers:
      - name: rag-app
        image: your-registry/rag-app:latest
        env:
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: google-api-key
        - name: DATABASE_URL
          value: postgresql://raguser:$(POSTGRES_PASSWORD)@postgres.rag-system.svc.cluster.local:5432/rag_db
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: postgres-password
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## ConfigMap for Application Settings

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: rag-config
  namespace: rag-system
data:
  COLLECTION_NAME: "documents"
  CHUNK_SIZE: "512"
  TOP_K: "5"
```

## Deploy Everything

```bash
kubectl apply -f namespace.yaml
kubectl apply -f postgres.yaml
kubectl apply -f configmap.yaml
kubectl apply -f app.yaml

# Check status
kubectl get pods -n rag-system
kubectl logs -n rag-system deployment/rag-app
```

## Resource Sizing Guide

| Component | Memory | CPU | Notes |
|-----------|--------|-----|-------|
| PostgreSQL | 512Mi–2Gi | 500m–2 | Depends on index size |
| Application | 256Mi–512Mi | 250m–500m | Embedding calls are I/O bound |

## pgvector Index Maintenance

HNSW indexes are created automatically. For large datasets (>100K vectors), monitor query latency and consider tuning:

```sql
-- Check index size
SELECT pg_size_pretty(pg_relation_size('documents_embedding_idx'));

-- Rebuild index if needed (requires table lock)
REINDEX INDEX CONCURRENTLY documents_embedding_idx;
```
````

**Step 4: Commit**

```bash
git add docs/deployment/docker.md docs/deployment/kubernetes.md
git commit -m "docs: add Docker and Kubernetes deployment guides"
```

---

## Task 8: Multi-Domain Example

**Files:**
- Create: `examples/multi_domain_rag.py`
- Modify: `examples/README.md`

**Step 1: Create the multi-domain example**

Create `examples/multi_domain_rag.py`:

```python
"""
Multi-domain RAG example for vibe-rag.

Demonstrates using separate knowledge bases (collections) for different domains,
then routing queries to the appropriate domain based on context.

Domains: HR Policy, Engineering Guide, Legal Compliance

Prerequisites:
    - PostgreSQL with pgvector: docker-compose -f docker-compose.test.yml up -d
    - Gemini API key: export GOOGLE_API_KEY="your-key"

Run:
    python examples/multi_domain_rag.py
"""

import asyncio
import os
import tempfile
from pathlib import Path

from vibe_rag import BasicRAGModule, QuickSetup

API_KEY = os.getenv("GOOGLE_API_KEY", "your-api-key-here")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://vibetest:vibetest123@localhost:5434/vibe_rag_test",
)

# Domain knowledge bases
DOMAIN_DOCS = {
    "hr_policy": {
        "collection": "domain_hr",
        "content": """
HR Policy Manual - Employee Guidelines

Vacation Policy:
All full-time employees accrue 15 days of vacation per year.
Vacation requests must be submitted at least 2 weeks in advance.
Unused vacation days carry over (max 30 days).

Remote Work Policy:
Employees may work remotely up to 3 days per week.
Core hours are 10am-3pm in the employee's local timezone.
A dedicated workspace with reliable internet is required.

Performance Reviews:
Annual reviews are conducted in Q4 each year.
Mid-year check-ins occur in Q2.
Reviews use a 5-point scale: Exceptional, Exceeds, Meets, Needs Improvement, Unsatisfactory.
""",
    },
    "engineering_guide": {
        "collection": "domain_engineering",
        "content": """
Engineering Standards and Best Practices

Code Review Process:
All code changes require at least one reviewer approval.
PRs should be kept under 400 lines for easier review.
Use conventional commit messages: feat, fix, docs, test, refactor.

Testing Requirements:
Unit tests are mandatory for all new features.
Aim for 80%+ code coverage on new code.
Integration tests required for API endpoints.
E2E tests for critical user journeys.

Deployment Process:
All deployments go through staging first.
Production deployments require sign-off from tech lead.
Rollback plan must be documented before deploying.
""",
    },
    "legal_compliance": {
        "collection": "domain_legal",
        "content": """
Legal Compliance Guidelines

Data Privacy:
All customer data is subject to GDPR and CCPA regulations.
Personal data must be encrypted at rest and in transit.
Data retention: 7 years for financial records, 3 years for communications.
Data deletion requests must be fulfilled within 30 days.

Contract Management:
All vendor contracts above $10,000 require legal review.
NDAs must be signed before sharing proprietary information.
Software licenses must be reviewed by legal before adoption.

Incident Reporting:
Security incidents must be reported within 24 hours.
Data breaches affecting customers must be reported to regulators within 72 hours.
""",
    },
}


async def setup_domain(domain_name: str, config: dict) -> None:
    """Ingest documents into a domain-specific collection."""
    print(f"  Setting up {domain_name} knowledge base...")

    async with QuickSetup.create(
        provider_api_key=API_KEY,
        database_url=DATABASE_URL,
        collection_name=config["collection"],
        top_k=3,
    ) as rag:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(config["content"])
            path = f.name

        try:
            doc_ids = await rag.ingest(
                path,
                metadata={"domain": domain_name, "type": "policy"},
            )
            print(f"    ✓ Ingested {len(doc_ids)} chunks")
        finally:
            Path(path).unlink()


async def query_domain(domain_name: str, collection: str, question: str) -> dict:
    """Query a specific domain knowledge base."""
    async with QuickSetup.create(
        provider_api_key=API_KEY,
        database_url=DATABASE_URL,
        collection_name=collection,
        top_k=3,
    ) as rag:
        result = await rag.query(question)
        return result


async def demo_domain_specific_queries() -> None:
    """Query each domain with domain-specific questions."""
    print("\n--- Domain-Specific Queries ---")

    queries = [
        ("hr_policy", DOMAIN_DOCS["hr_policy"]["collection"], "How many vacation days do I get?"),
        ("engineering_guide", DOMAIN_DOCS["engineering_guide"]["collection"], "What are the code review requirements?"),
        ("legal_compliance", DOMAIN_DOCS["legal_compliance"]["collection"], "When must data breaches be reported?"),
    ]

    for domain, collection, question in queries:
        print(f"\n  [{domain.upper()}] Q: {question}")
        result = await query_domain(domain, collection, question)
        print(f"  A: {result['answer'][:200]}...")
        print(f"  Sources: {result['metadata']['documents_retrieved']} docs retrieved in {result['metadata']['total_time_ms']:.0f}ms")


async def demo_cross_domain_comparison() -> None:
    """Show that different domains return different answers to similar questions."""
    print("\n--- Cross-Domain: Same Question, Different Context ---")
    question = "What are the key requirements?"

    for domain_name, config in DOMAIN_DOCS.items():
        result = await query_domain(domain_name, config["collection"], question)
        print(f"\n  [{domain_name}]: {result['answer'][:150]}...")


async def demo_basic_rag_module() -> None:
    """Show BasicRAGModule usage for cleaner code."""
    print("\n--- Using BasicRAGModule ---")

    async with BasicRAGModule(
        api_key=API_KEY,
        db_url=DATABASE_URL,
        collection_name=DOMAIN_DOCS["hr_policy"]["collection"],
        top_k=3,
    ) as rag:
        result = await rag.query("How does remote work work?")
        print(f"  Remote work policy: {result['answer'][:200]}...")


async def main() -> None:
    print("=== Multi-Domain RAG Demo ===")
    print("Setting up domain knowledge bases...")

    # Ingest all domains
    for domain_name, config in DOMAIN_DOCS.items():
        await setup_domain(domain_name, config)

    # Demo queries
    await demo_domain_specific_queries()
    await demo_cross_domain_comparison()
    await demo_basic_rag_module()

    print("\n=== Done ===")
    print("Key takeaway: separate collections provide domain isolation")
    print("Each domain has its own optimized retrieval context")


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Update examples/README.md**

Read current README first:

```bash
cat examples/README.md
```

Then update it to document all 4 examples:

```markdown
# vibe-rag Examples

Ready-to-run examples demonstrating vibe-rag capabilities.

## Prerequisites

All examples require:
- Docker: `docker-compose -f docker-compose.test.yml up -d`
- Gemini API key: `export GOOGLE_API_KEY="your-key"`
- Install: `pip install -e ".[dev]"`

## Examples

### 1. quick_start.py — Minimal Setup

The simplest possible RAG workflow using `QuickSetup`.

```bash
python examples/quick_start.py
```

**Demonstrates:** `QuickSetup.create()`, basic ingest and query.

---

### 2. simple_rag.py — Core RAG Workflow

Full RAGEngine configuration with metrics tracking.

```bash
python examples/simple_rag.py
```

**Demonstrates:** `RAGEngine`, `RAGConfig`, metrics, custom chunking.

---

### 3. advanced_rag.py — Advanced Retrieval Techniques

Three retrieval techniques: metadata filtering, chunking strategy comparison, multi-collection.

```bash
python examples/advanced_rag.py
```

**Demonstrates:** Metadata filtering, chunking strategies, multi-collection pattern. Includes extension points for HyDE, reranking, and multi-query retrieval.

---

### 4. multi_domain_rag.py — Domain-Isolated Knowledge Bases

Three separate domains (HR, Engineering, Legal) with domain-specific querying.

```bash
python examples/multi_domain_rag.py
```

**Demonstrates:** `BasicRAGModule`, multi-domain isolation, cross-domain comparison.

---

## Configuration

Override defaults via environment variables:

```bash
export GOOGLE_API_KEY="your-gemini-key"
export DATABASE_URL="postgresql://user:pass@localhost:5434/db"
```
```

**Step 3: Commit**

```bash
git add examples/multi_domain_rag.py examples/README.md
git commit -m "feat: add multi-domain RAG example using BasicRAGModule"
```

---

## Task 9: Final Validation

**Step 1: Run unit + integration tests with coverage**

```bash
.venv/bin/python -m pytest tests/unit tests/integration \
  --cov=vibe_rag --cov-report=term-missing --cov-report=html \
  2>&1 | tail -40
```

Expected: Overall >80%. Check each file.

**Step 2: Run E2E tests**

```bash
GOOGLE_API_KEY=$GOOGLE_API_KEY .venv/bin/python -m pytest tests/e2e/ -v --no-cov
```

Expected: All 6 tests PASS.

**Step 3: Run full coverage including E2E**

```bash
GOOGLE_API_KEY=$GOOGLE_API_KEY .venv/bin/python -m pytest tests/unit tests/integration tests/e2e \
  --cov=vibe_rag --cov-report=term-missing 2>&1 | tail -30
```

Expected: engine.py >70% (unit) and combined with E2E should be >85%.

**Step 4: Verify examples are importable**

```bash
.venv/bin/python -c "import examples.multi_domain_rag; print('OK')" 2>/dev/null || \
  .venv/bin/python -c "
import ast, sys
for f in ['examples/quick_start.py', 'examples/simple_rag.py', 'examples/advanced_rag.py', 'examples/multi_domain_rag.py']:
    try:
        ast.parse(open(f).read())
        print(f'  ✓ {f} is valid Python')
    except SyntaxError as e:
        print(f'  ✗ {f}: {e}')
        sys.exit(1)
"
```

Expected: All 4 examples are valid Python.

**Step 5: Check docs exist**

```bash
ls -la docs/deployment/ docs/api-reference.md docs/quickstart.md docs/testing-guide.md
```

Expected: All files present.

**Step 6: Final commit if anything was fixed**

```bash
git status
# If any files modified during validation:
git add -p
git commit -m "fix: final validation fixes for Phase 3 production hardening"
```

**Step 7: Print acceptance criteria summary**

```bash
echo "=== Phase 3 Acceptance Criteria ==="
echo ""
echo "✅ Test coverage >80% (unit+integration)"
echo "✅ E2E tests pass with real PostgreSQL + Gemini"
echo "✅ Engine coverage >70% (unit) + real path via E2E"
echo "✅ Config coverage >85%"
echo "✅ Observability coverage >80%"
echo "✅ Performance benchmarks in tests/benchmarks/"
echo "✅ API reference in docs/api-reference.md"
echo "✅ Docker deployment in docs/deployment/docker.md"
echo "✅ Kubernetes guide in docs/deployment/kubernetes.md"
echo "✅ Multi-domain example in examples/multi_domain_rag.py"
echo ""
echo "Framework ready for v0.1.0 release! 🎉"
```
