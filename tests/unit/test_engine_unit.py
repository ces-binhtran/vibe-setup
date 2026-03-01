"""Unit tests for RAGEngine with mocked dependencies.

Tests the engine's unit-testable code paths using mocks to avoid
any external I/O (database, API calls, file system where avoidable).
"""

import pytest

from vibe_rag.config.models import (
    ChunkingConfig,
    LLMConfig,
    PipelineConfig,
    RAGConfig,
    StorageConfig,
)
from vibe_rag.engine import RAGEngine
from vibe_rag.testing.mocks import MockLLMProvider, MockVectorStore
from vibe_rag.utils.errors import ConfigurationError, DocumentProcessingError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def base_config():
    """Minimal valid RAGConfig using mock-compatible settings."""
    return RAGConfig(
        llm=LLMConfig(
            provider="gemini",
            api_key="test-key",
        ),
        storage=StorageConfig(
            backend="postgres",
            collection_name="test_docs",
            connection_string="postgresql://user:pass@localhost/db",
        ),
        pipeline=PipelineConfig(top_k=3),
        chunking=ChunkingConfig(chunk_size=256, chunk_overlap=20),
    )


@pytest.fixture
def engine(base_config):
    """RAGEngine with mock provider and storage injected (not initialized)."""
    return RAGEngine(
        config=base_config,
        provider=MockLLMProvider(),
        storage=MockVectorStore("test_docs"),
    )


# ---------------------------------------------------------------------------
# Tests: _create_provider() – unsupported provider raises ConfigurationError
# ---------------------------------------------------------------------------


class TestCreateProvider:
    """Tests for the _create_provider() factory method."""

    def test_unsupported_provider_raises_configuration_error(self, base_config):
        """_create_provider() raises ConfigurationError for unknown providers.

        Because LLMConfig.provider is Literal["gemini"], we must bypass
        Pydantic validation with model_construct() to inject an unsupported
        provider value and exercise the else-branch in _create_provider().
        """
        # Bypass Pydantic's Literal validation to inject unsupported provider
        bad_llm = LLMConfig.model_construct(
            provider="openai",
            api_key="key",
            model_name="gpt-4",
            embedding_model="text-embedding-ada-002",
            generation_kwargs={},
        )
        bad_config = RAGConfig.model_construct(
            llm=bad_llm,
            storage=base_config.storage,
            pipeline=base_config.pipeline,
            chunking=base_config.chunking,
        )

        # Create engine with mock storage to isolate provider creation
        engine = RAGEngine(
            config=base_config,
            provider=MockLLMProvider(),
            storage=MockVectorStore(),
        )
        # Monkey-patch config to simulate unsupported provider
        engine.config = bad_config

        with pytest.raises(ConfigurationError) as exc_info:
            engine._create_provider()

        assert "Unsupported LLM provider: openai" in str(exc_info.value)

    def test_supported_gemini_provider_does_not_raise(self, base_config):
        """_create_provider() with 'gemini' provider creates a GeminiProvider."""
        from vibe_rag.providers.gemini import GeminiProvider

        engine = RAGEngine(
            config=base_config,
            provider=MockLLMProvider(),
            storage=MockVectorStore(),
        )
        # Reset config to valid gemini to test the if-branch explicitly
        provider = engine._create_provider()
        assert isinstance(provider, GeminiProvider)


# ---------------------------------------------------------------------------
# Tests: _create_storage() – unsupported backend raises ConfigurationError
# ---------------------------------------------------------------------------


class TestCreateStorage:
    """Tests for the _create_storage() factory method."""

    def test_unsupported_backend_raises_configuration_error(self, base_config):
        """_create_storage() raises ConfigurationError for unknown backends.

        Like _create_provider(), we bypass Pydantic Literal validation via
        model_construct() to inject an unsupported backend value.
        """
        bad_storage = StorageConfig.model_construct(
            backend="weaviate",
            collection_name="docs",
            connection_string="http://localhost:8080",
            vector_dimension=768,
        )
        bad_config = RAGConfig.model_construct(
            llm=base_config.llm,
            storage=bad_storage,
            pipeline=base_config.pipeline,
            chunking=base_config.chunking,
        )

        engine = RAGEngine(
            config=base_config,
            provider=MockLLMProvider(),
            storage=MockVectorStore(),
        )
        engine.config = bad_config

        with pytest.raises(ConfigurationError) as exc_info:
            engine._create_storage()

        assert "Unsupported storage backend: weaviate" in str(exc_info.value)

    def test_supported_postgres_backend_does_not_raise(self, base_config):
        """_create_storage() with 'postgres' backend creates a PostgresVectorStore."""
        from vibe_rag.storage.postgres_vector import PostgresVectorStore

        engine = RAGEngine(
            config=base_config,
            provider=MockLLMProvider(),
            storage=MockVectorStore(),
        )
        storage = engine._create_storage()
        assert isinstance(storage, PostgresVectorStore)


# ---------------------------------------------------------------------------
# Tests: ConfigurationError from validate_dimensions()
# ---------------------------------------------------------------------------


class TestConfigValidation:
    """Tests for RAGConfig.validate_dimensions() integration in __init__."""

    def test_dimension_mismatch_raises_configuration_error(self):
        """RAGEngine.__init__ raises ConfigurationError for dimension mismatch.

        validate_dimensions() raises ValueError which the engine wraps as
        ConfigurationError.
        """
        config = RAGConfig(
            llm=LLMConfig(
                provider="gemini",
                api_key="key",
                embedding_model="models/gemini-embedding-001",
            ),
            storage=StorageConfig(
                backend="postgres",
                collection_name="docs",
                connection_string="postgresql://localhost/db",
                vector_dimension=512,  # Should be 768 for gemini-embedding-001
            ),
        )
        with pytest.raises(ConfigurationError) as exc_info:
            RAGEngine(
                config=config,
                provider=MockLLMProvider(),
                storage=MockVectorStore(),
            )

        assert "dimension" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Tests: get_metrics() and get_stats() when metrics disabled
# ---------------------------------------------------------------------------


class TestMetricsDisabled:
    """Tests for metric methods when enable_metrics=False."""

    def test_get_metrics_raises_when_disabled(self, base_config):
        """get_metrics() raises ConfigurationError when metrics tracking is off."""
        engine = RAGEngine(
            config=base_config,
            provider=MockLLMProvider(),
            storage=MockVectorStore(),
            enable_metrics=False,
        )

        with pytest.raises(ConfigurationError) as exc_info:
            engine.get_metrics()

        assert "Metrics tracking is disabled" in str(exc_info.value)

    def test_get_stats_raises_when_disabled(self, base_config):
        """get_stats() raises ConfigurationError when metrics tracking is off."""
        engine = RAGEngine(
            config=base_config,
            provider=MockLLMProvider(),
            storage=MockVectorStore(),
            enable_metrics=False,
        )

        with pytest.raises(ConfigurationError) as exc_info:
            engine.get_stats()

        assert "Metrics tracking is disabled" in str(exc_info.value)

    def test_metrics_tracker_is_none_when_disabled(self, base_config):
        """metrics_tracker attribute is None when metrics are disabled."""
        engine = RAGEngine(
            config=base_config,
            provider=MockLLMProvider(),
            storage=MockVectorStore(),
            enable_metrics=False,
        )
        assert engine.metrics_tracker is None
        assert not engine.enable_metrics


# ---------------------------------------------------------------------------
# Tests: register_loader()
# ---------------------------------------------------------------------------


class TestRegisterLoader:
    """Tests for the register_loader() method."""

    def test_register_loader_stores_loader(self, engine):
        """register_loader() stores the loader under the given extension."""
        from vibe_rag.loaders.base import BaseLoader
        from vibe_rag.models import Document

        class StubLoader(BaseLoader):
            async def load(self, file_path: str) -> list[Document]:
                return [Document(content="stub content")]

        stub = StubLoader()
        engine.register_loader(".docx", stub)

        assert ".docx" in engine._loaders
        assert engine._loaders[".docx"] is stub

    def test_register_loader_overwrites_existing(self, engine):
        """register_loader() can overwrite an existing loader for an extension."""
        from vibe_rag.loaders.base import BaseLoader
        from vibe_rag.models import Document

        class NewTextLoader(BaseLoader):
            async def load(self, file_path: str) -> list[Document]:
                return [Document(content="new loader")]

        new_loader = NewTextLoader()
        engine.register_loader(".txt", new_loader)

        assert engine._loaders[".txt"] is new_loader

    def test_default_loaders_registered_on_init(self, engine):
        """Engine initializes with .txt, .md, and .pdf loaders by default."""
        assert ".txt" in engine._loaders
        assert ".md" in engine._loaders
        assert ".pdf" in engine._loaders


# ---------------------------------------------------------------------------
# Tests: ingest() / query() before initialize()
# ---------------------------------------------------------------------------


class TestNotInitialized:
    """Tests for engine method guards before calling initialize()."""

    async def test_ingest_before_initialize_raises_configuration_error(self, engine):
        """ingest() raises ConfigurationError when called before initialize()."""
        with pytest.raises(ConfigurationError) as exc_info:
            await engine.ingest("some_file.txt")

        assert "Engine not initialized" in str(exc_info.value)
        assert "initialize()" in str(exc_info.value)

    async def test_query_before_initialize_raises_configuration_error(self, engine):
        """query() raises ConfigurationError when called before initialize()."""
        with pytest.raises(ConfigurationError) as exc_info:
            await engine.query("What is RAG?")

        assert "Engine not initialized" in str(exc_info.value)
        assert "initialize()" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Tests: double initialize() is idempotent
# ---------------------------------------------------------------------------


class TestDoubleInitialize:
    """Tests for idempotent initialize() behavior."""

    async def test_double_initialize_is_safe(self, engine):
        """Calling initialize() twice does not raise and leaves engine initialized."""
        await engine.initialize()
        assert engine._initialized

        # Second call must not raise and must keep engine initialized
        await engine.initialize()
        assert engine._initialized

        # Cleanup
        await engine.close()

    async def test_initialize_sets_initialized_flag(self, engine):
        """initialize() sets _initialized to True."""
        assert not engine._initialized
        await engine.initialize()
        assert engine._initialized
        await engine.close()


# ---------------------------------------------------------------------------
# Tests: close() before initialize() is safe
# ---------------------------------------------------------------------------


class TestCloseSafety:
    """Tests for safe close() behavior."""

    async def test_close_before_initialize_does_not_raise(self, engine):
        """close() called on an uninitialized engine must not raise."""
        assert not engine._initialized
        # Should complete without error
        await engine.close()
        assert not engine._initialized


# ---------------------------------------------------------------------------
# Tests: ingest() with unsupported file extension
# ---------------------------------------------------------------------------


class TestIngestUnsupportedExtension:
    """Tests for ingest() with file types that have no registered loader."""

    async def test_ingest_unknown_extension_raises_document_processing_error(
        self, engine
    ):
        """ingest() raises DocumentProcessingError for unregistered file extensions."""
        await engine.initialize()

        try:
            with pytest.raises(DocumentProcessingError) as exc_info:
                await engine.ingest("document.xyz")

            error_msg = str(exc_info.value)
            assert "No loader registered for file type: .xyz" in error_msg
        finally:
            await engine.close()

    async def test_ingest_no_extension_raises_document_processing_error(self, engine):
        """ingest() raises DocumentProcessingError for files with no extension."""
        await engine.initialize()

        try:
            with pytest.raises(DocumentProcessingError) as exc_info:
                await engine.ingest("no_extension_file")

            error_msg = str(exc_info.value)
            # Empty extension '' is not in _loaders
            assert "No loader registered for file type:" in error_msg
        finally:
            await engine.close()


# ---------------------------------------------------------------------------
# Tests: ingest() exception wrapping paths
# ---------------------------------------------------------------------------


class TestIngestExceptionHandling:
    """Tests for ingest() exception handling and wrapping logic."""

    async def test_ingest_re_raises_document_processing_error_from_loader(self, engine):
        """ingest() re-raises DocumentProcessingError raised by the loader.

        This exercises the 'except (DocumentProcessingError, StorageError)' branch
        (lines 265-267 in engine.py) where known errors pass through unchanged.
        """
        from unittest.mock import AsyncMock

        from vibe_rag.loaders.base import BaseLoader
        from vibe_rag.models import Document

        class FailingLoader(BaseLoader):
            async def load(self, file_path: str) -> list[Document]:
                raise DocumentProcessingError("Loader encountered corrupt file")

        engine.register_loader(".corrupt", FailingLoader())
        await engine.initialize()

        try:
            with pytest.raises(DocumentProcessingError) as exc_info:
                await engine.ingest("test.corrupt")

            assert "Loader encountered corrupt file" in str(exc_info.value)
        finally:
            await engine.close()

    async def test_ingest_wraps_unexpected_exception_as_document_processing_error(
        self, engine
    ):
        """ingest() wraps unexpected exceptions as DocumentProcessingError.

        This exercises the 'except Exception' fallback branch (lines 268-274)
        where unknown errors get wrapped with context about the failed source.
        """
        from vibe_rag.loaders.base import BaseLoader
        from vibe_rag.models import Document

        class BrokenLoader(BaseLoader):
            async def load(self, file_path: str) -> list[Document]:
                raise RuntimeError("unexpected internal error")

        engine.register_loader(".broken", BrokenLoader())
        await engine.initialize()

        try:
            with pytest.raises(DocumentProcessingError) as exc_info:
                await engine.ingest("test.broken")

            error_msg = str(exc_info.value)
            assert "Failed to ingest document from test.broken" in error_msg
            assert exc_info.value.error_type == "RuntimeError"
        finally:
            await engine.close()

    async def test_ingest_re_raises_storage_error_from_storage(self, engine):
        """ingest() re-raises StorageError from the storage backend.

        This exercises the known-error re-raise branch via StorageError.
        """
        import tempfile
        import os

        from vibe_rag.utils.errors import StorageError

        # Make storage.add_documents raise StorageError
        original_add = engine.storage.add_documents

        async def failing_add(docs, embeddings):
            raise StorageError("Storage backend unavailable")

        engine.storage.add_documents = failing_add
        await engine.initialize()

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write("test content for ingestion")
                temp_path = f.name

            try:
                with pytest.raises(StorageError) as exc_info:
                    await engine.ingest(temp_path)

                assert "Storage backend unavailable" in str(exc_info.value)
            finally:
                os.unlink(temp_path)
        finally:
            engine.storage.add_documents = original_add
            await engine.close()


# ---------------------------------------------------------------------------
# Tests: query() exception re-raise paths
# ---------------------------------------------------------------------------


class TestQueryExceptionHandling:
    """Tests for query() exception handling and wrapping logic."""

    async def test_query_wraps_unexpected_exception_as_rag_exception(self, engine):
        """query() wraps unexpected exceptions as RAGException.

        This exercises the 'except Exception' fallback (lines 397-399) in query().
        We make the pipeline component raise an unexpected error to trigger wrapping.
        """
        from vibe_rag.utils.errors import RAGException

        # Replace the pipeline with one that raises an unexpected error
        original_pipeline = engine.pipeline

        class FailingComponent:
            async def process(self, context):
                raise RuntimeError("unexpected pipeline error")

        engine.pipeline = [FailingComponent()]
        await engine.initialize()

        try:
            with pytest.raises(RAGException) as exc_info:
                await engine.query("What is RAG?")

            assert "Query execution failed" in str(exc_info.value)
        finally:
            engine.pipeline = original_pipeline
            await engine.close()

    async def test_query_re_raises_retrieval_error_unchanged(self, engine):
        """query() re-raises RetrievalError without wrapping.

        This exercises the 'except (RetrievalError, LLMProviderError)' branch
        (lines 394-396) where known retrieval errors pass through unchanged.
        """
        from vibe_rag.utils.errors import RetrievalError

        class FailingRetriever:
            async def process(self, context):
                raise RetrievalError("Vector index unavailable")

        original_pipeline = engine.pipeline
        engine.pipeline = [FailingRetriever()]
        await engine.initialize()

        try:
            with pytest.raises(RetrievalError) as exc_info:
                await engine.query("What is RAG?")

            assert "Vector index unavailable" in str(exc_info.value)
        finally:
            engine.pipeline = original_pipeline
            await engine.close()

    async def test_query_re_raises_llm_provider_error_unchanged(self, engine, populated_mock_store):
        """query() re-raises LLMProviderError without wrapping.

        This exercises the 'except (RetrievalError, LLMProviderError)' branch
        via an LLM provider failure during generation.
        """
        from vibe_rag.utils.errors import LLMProviderError

        # Make provider.generate raise LLMProviderError
        original_generate = engine.provider.generate

        async def failing_generate(prompt, **kwargs):
            raise LLMProviderError("API quota exceeded")

        engine.provider.generate = failing_generate

        # Use the populated store so retrieval succeeds but generation fails
        engine.storage = populated_mock_store
        engine.pipeline = engine._build_pipeline()
        await engine.initialize()

        try:
            with pytest.raises(LLMProviderError) as exc_info:
                await engine.query("What is Python?")

            assert "API quota exceeded" in str(exc_info.value)
        finally:
            engine.provider.generate = original_generate
            await engine.close()
