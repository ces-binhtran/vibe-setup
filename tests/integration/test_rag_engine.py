"""Integration tests for RAG engine."""

import os
import tempfile

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


@pytest.mark.integration
class TestRAGEngineIntegration:
    """Integration tests for RAGEngine with mock components."""

    @pytest.fixture
    def mock_config(self):
        """Create config with mock components."""
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
    async def mock_engine(self, mock_config, mock_llm_provider, mock_vector_store):
        """Create RAGEngine with mock components."""
        engine = RAGEngine(
            config=mock_config,
            provider=mock_llm_provider,
            storage=mock_vector_store,
        )
        async with engine:
            yield engine

    async def test_engine_initialization(self, mock_config, mock_llm_provider, mock_vector_store):
        """Test engine initialization and cleanup."""
        engine = RAGEngine(
            config=mock_config,
            provider=mock_llm_provider,
            storage=mock_vector_store,
        )

        assert not engine._initialized

        await engine.initialize()
        assert engine._initialized

        await engine.close()
        assert not engine._initialized

    async def test_engine_context_manager(self, mock_config, mock_llm_provider, mock_vector_store):
        """Test engine as async context manager."""
        async with RAGEngine(
            config=mock_config,
            provider=mock_llm_provider,
            storage=mock_vector_store,
        ) as engine:
            assert engine._initialized

    async def test_ingest_text_file(self, mock_engine):
        """Test ingesting a text file."""
        # Create temporary text file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a test document.\nIt has multiple lines.\n")
            temp_path = f.name

        try:
            # Ingest document
            doc_ids = await mock_engine.ingest(
                source=temp_path,
                metadata={"source": "test", "type": "text"},
            )

            # Verify documents were added
            assert len(doc_ids) > 0
            assert isinstance(doc_ids[0], str)

        finally:
            # Cleanup
            os.unlink(temp_path)

    async def test_ingest_with_chunking(self, mock_engine):
        """Test document chunking during ingestion."""
        # Create document larger than chunk size
        content = "This is a sentence. " * 100  # ~2000 chars

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            doc_ids = await mock_engine.ingest(source=temp_path)

            # Should create multiple chunks (chunk_size=256)
            # ~2000 chars should create ~8-10 chunks
            assert len(doc_ids) >= 5

        finally:
            os.unlink(temp_path)

    async def test_query_with_context(self, mock_engine, populated_mock_store):
        """Test RAG query with retrieved context."""
        # Replace storage with populated store
        mock_engine.storage = populated_mock_store

        # Rebuild pipeline with new storage
        mock_engine.pipeline = mock_engine._build_pipeline()

        # Execute query
        result = await mock_engine.query("What is Python?")

        # Verify response structure
        assert "answer" in result
        assert "sources" in result
        assert "metadata" in result

        # Verify answer was generated
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0

        # Verify sources were retrieved
        assert len(result["sources"]) > 0
        assert all("content" in src for src in result["sources"])
        assert all("score" in src for src in result["sources"])

        # Verify metadata
        metadata = result["metadata"]
        assert "query_id" in metadata
        assert "retrieval_time_ms" in metadata
        assert "generation_time_ms" in metadata
        assert "total_time_ms" in metadata
        assert metadata["documents_retrieved"] > 0

    async def test_query_with_generation_kwargs(self, mock_engine, populated_mock_store):
        """Test query with custom generation parameters."""
        mock_engine.storage = populated_mock_store
        mock_engine.pipeline = mock_engine._build_pipeline()

        result = await mock_engine.query(
            "What is Python?",
            generation_kwargs={"temperature": 0.5, "max_tokens": 100},
        )

        assert "answer" in result
        # MockLLMProvider should have received the kwargs
        # (In real tests, we'd verify this with a spy/mock)

    async def test_metrics_tracking(self, mock_engine, populated_mock_store):
        """Test metrics tracking across multiple queries."""
        mock_engine.storage = populated_mock_store
        mock_engine.pipeline = mock_engine._build_pipeline()

        # Execute multiple queries
        await mock_engine.query("Question 1")
        await mock_engine.query("Question 2")
        await mock_engine.query("Question 3")

        # Get metrics
        metrics = mock_engine.get_metrics()
        assert len(metrics) == 3

        # Verify each metric
        for metric in metrics:
            assert metric.query_id is not None
            assert metric.total_time_ms > 0
            assert metric.retrieval_time_ms > 0
            assert metric.generation_time_ms > 0
            assert metric.documents_retrieved > 0

        # Get aggregate stats
        stats = mock_engine.get_stats()
        assert stats["total_queries"] == 3
        assert stats["avg_total_time_ms"] > 0
        assert stats["avg_retrieval_time_ms"] > 0
        assert stats["avg_generation_time_ms"] > 0
        assert stats["avg_documents_retrieved"] > 0

    async def test_metrics_disabled(self, mock_config, mock_llm_provider, mock_vector_store):
        """Test engine with metrics disabled."""
        async with RAGEngine(
            config=mock_config,
            provider=mock_llm_provider,
            storage=mock_vector_store,
            enable_metrics=False,
        ) as engine:
            assert not engine.enable_metrics
            assert engine.metrics_tracker is None

            # Should raise error when trying to get metrics
            with pytest.raises(Exception):
                engine.get_metrics()

    async def test_custom_loader_registration(self, mock_engine):
        """Test registering custom document loader."""
        from vibe_rag.loaders.base import BaseLoader

        class CustomLoader(BaseLoader):
            async def load(self, file_path):
                from vibe_rag import Document

                return [Document(content="Custom loaded content")]

        # Register custom loader
        mock_engine.register_loader(".custom", CustomLoader())

        # Create file with custom extension
        with tempfile.NamedTemporaryFile(mode="w", suffix=".custom", delete=False) as f:
            f.write("This will be ignored by custom loader")
            temp_path = f.name

        try:
            doc_ids = await mock_engine.ingest(source=temp_path)
            assert len(doc_ids) > 0

        finally:
            os.unlink(temp_path)

    async def test_ingest_unsupported_file_type(self, mock_engine):
        """Test ingesting unsupported file type raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False) as f:
            f.write("content")
            temp_path = f.name

        try:
            with pytest.raises(Exception) as exc_info:
                await mock_engine.ingest(source=temp_path)

            assert "No loader registered" in str(exc_info.value)

        finally:
            os.unlink(temp_path)

    async def test_query_before_initialize_raises_error(self, mock_config):
        """Test querying before initialization raises error."""
        engine = RAGEngine(
            config=mock_config,
            provider=MockLLMProvider(),
            storage=MockVectorStore("test"),
        )

        with pytest.raises(Exception) as exc_info:
            await engine.query("test")

        assert "not initialized" in str(exc_info.value).lower()

    async def test_config_validation(self):
        """Test configuration validation."""
        # Test dimension mismatch
        config = RAGConfig(
            llm=LLMConfig(
                provider="gemini",
                api_key="test-key",
                embedding_model="models/text-embedding-004",  # 768 dims
            ),
            storage=StorageConfig(
                backend="postgres",
                collection_name="test",
                connection_string="postgresql://localhost/db",
                vector_dimension=512,  # Wrong dimension!
            ),
        )

        # Should raise error during engine initialization
        with pytest.raises(Exception) as exc_info:
            RAGEngine(config=config)

        assert "dimension" in str(exc_info.value).lower()
