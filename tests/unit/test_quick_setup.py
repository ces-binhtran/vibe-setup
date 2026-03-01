"""Unit tests for QuickSetup convenience class."""

import pytest

from vibe_rag.engine import RAGEngine


class TestQuickSetup:
    """Tests for QuickSetup.create() factory method."""

    def test_create_returns_rag_engine(self):
        """QuickSetup.create() should return a RAGEngine instance."""
        from vibe_rag.quick import QuickSetup

        engine = QuickSetup.create(
            provider_api_key="test-key",
            database_url="postgresql://user:pass@localhost/db",
        )
        assert isinstance(engine, RAGEngine)

    def test_create_with_gemini_defaults(self):
        """Created engine should use Gemini defaults."""
        from vibe_rag.quick import QuickSetup

        engine = QuickSetup.create(
            provider_api_key="my-api-key",
            database_url="postgresql://localhost/testdb",
        )
        assert engine.config.llm.provider == "gemini"
        assert engine.config.llm.api_key == "my-api-key"
        assert engine.config.llm.model_name == "gemini-2.0-flash"
        assert engine.config.llm.embedding_model == "models/gemini-embedding-001"
        assert engine.config.storage.vector_dimension == 768

    def test_create_default_collection_name(self):
        """Default collection name should be 'documents'."""
        from vibe_rag.quick import QuickSetup

        engine = QuickSetup.create(
            provider_api_key="key",
            database_url="postgresql://localhost/db",
        )
        assert engine.config.storage.collection_name == "documents"

    def test_create_custom_collection_name(self):
        """Custom collection_name should be passed through to storage config."""
        from vibe_rag.quick import QuickSetup

        engine = QuickSetup.create(
            provider_api_key="key",
            database_url="postgresql://localhost/db",
            collection_name="my_kb",
        )
        assert engine.config.storage.collection_name == "my_kb"

    def test_create_default_top_k(self):
        """Default top_k should be 5."""
        from vibe_rag.quick import QuickSetup

        engine = QuickSetup.create(
            provider_api_key="key",
            database_url="postgresql://localhost/db",
        )
        assert engine.config.pipeline.top_k == 5

    def test_create_custom_top_k(self):
        """Custom top_k should be passed through to pipeline config."""
        from vibe_rag.quick import QuickSetup

        engine = QuickSetup.create(
            provider_api_key="key",
            database_url="postgresql://localhost/db",
            top_k=10,
        )
        assert engine.config.pipeline.top_k == 10

    def test_create_database_url_passed_through(self):
        """database_url should map to storage connection_string."""
        from vibe_rag.quick import QuickSetup

        db_url = "postgresql://myuser:mypass@myhost:5432/mydb"
        engine = QuickSetup.create(
            provider_api_key="key",
            database_url=db_url,
        )
        assert engine.config.storage.connection_string == db_url

    def test_engine_not_initialized_on_create(self):
        """Engine returned by create() should not be initialized yet."""
        from vibe_rag.quick import QuickSetup

        engine = QuickSetup.create(
            provider_api_key="key",
            database_url="postgresql://localhost/db",
        )
        assert not engine._initialized

    async def test_engine_works_as_async_context_manager(self, mock_llm_provider, mock_vector_store):
        """Engine returned by QuickSetup.create() should support async with."""
        from vibe_rag.quick import QuickSetup

        engine = QuickSetup.create(
            provider_api_key="key",
            database_url="postgresql://localhost/db",
        )
        # Override with mocks so we don't need a real DB
        engine.provider = mock_llm_provider
        engine.storage = mock_vector_store
        engine.pipeline = engine._build_pipeline()

        async with engine as initialized_engine:
            assert initialized_engine._initialized

        assert not engine._initialized
