"""Unit tests for BasicRAGModule convenience class."""

import pytest

from vibe_rag.engine import RAGEngine


class TestBasicRAGModule:
    """Tests for BasicRAGModule pre-configured wrapper."""

    def test_init_creates_engine(self):
        """BasicRAGModule.__init__ should create an underlying RAGEngine."""
        from vibe_rag.modules.basic import BasicRAGModule

        module = BasicRAGModule(
            api_key="test-key",
            db_url="postgresql://user:pass@localhost/db",
        )
        assert hasattr(module, "_engine")
        assert isinstance(module._engine, RAGEngine)

    def test_default_collection_name(self):
        """Default collection_name should be 'documents'."""
        from vibe_rag.modules.basic import BasicRAGModule

        module = BasicRAGModule(
            api_key="key",
            db_url="postgresql://localhost/db",
        )
        assert module._engine.config.storage.collection_name == "documents"

    def test_custom_collection_name(self):
        """Custom collection_name should be passed through."""
        from vibe_rag.modules.basic import BasicRAGModule

        module = BasicRAGModule(
            api_key="key",
            db_url="postgresql://localhost/db",
            collection_name="my_collection",
        )
        assert module._engine.config.storage.collection_name == "my_collection"

    def test_api_key_passed_through(self):
        """api_key should map to engine LLM config."""
        from vibe_rag.modules.basic import BasicRAGModule

        module = BasicRAGModule(
            api_key="my-secret-key",
            db_url="postgresql://localhost/db",
        )
        assert module._engine.config.llm.api_key == "my-secret-key"

    def test_db_url_passed_through(self):
        """db_url should map to storage connection_string."""
        from vibe_rag.modules.basic import BasicRAGModule

        db_url = "postgresql://user:pass@host:5432/mydb"
        module = BasicRAGModule(api_key="key", db_url=db_url)
        assert module._engine.config.storage.connection_string == db_url

    def test_engine_not_initialized_on_init(self):
        """Engine should not be initialized until context manager is entered."""
        from vibe_rag.modules.basic import BasicRAGModule

        module = BasicRAGModule(api_key="key", db_url="postgresql://localhost/db")
        assert not module._engine._initialized

    async def test_context_manager_initializes_engine(self, mock_llm_provider, mock_vector_store):
        """async with BasicRAGModule should initialize and clean up the engine."""
        from vibe_rag.modules.basic import BasicRAGModule

        module = BasicRAGModule(api_key="key", db_url="postgresql://localhost/db")
        module._engine.provider = mock_llm_provider
        module._engine.storage = mock_vector_store
        module._engine.pipeline = module._engine._build_pipeline()

        async with module as m:
            assert m._engine._initialized

        assert not module._engine._initialized

    async def test_context_manager_returns_self(self, mock_llm_provider, mock_vector_store):
        """async with should yield the BasicRAGModule itself."""
        from vibe_rag.modules.basic import BasicRAGModule

        module = BasicRAGModule(api_key="key", db_url="postgresql://localhost/db")
        module._engine.provider = mock_llm_provider
        module._engine.storage = mock_vector_store
        module._engine.pipeline = module._engine._build_pipeline()

        async with module as m:
            assert m is module

    async def test_ingest_delegates_to_engine(self, mock_llm_provider, mock_vector_store):
        """BasicRAGModule.ingest() should delegate to the underlying engine."""
        import tempfile
        import os
        from vibe_rag.modules.basic import BasicRAGModule

        module = BasicRAGModule(api_key="key", db_url="postgresql://localhost/db")
        module._engine.provider = mock_llm_provider
        module._engine.storage = mock_vector_store
        module._engine.pipeline = module._engine._build_pipeline()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content for BasicRAGModule ingestion.")
            temp_path = f.name

        try:
            async with module:
                doc_ids = await module.ingest(temp_path)
            assert len(doc_ids) > 0
        finally:
            os.unlink(temp_path)

    async def test_query_delegates_to_engine(self, mock_llm_provider, mock_vector_store, populated_mock_store):
        """BasicRAGModule.query() should delegate to the underlying engine."""
        from vibe_rag.modules.basic import BasicRAGModule

        module = BasicRAGModule(api_key="key", db_url="postgresql://localhost/db")
        module._engine.provider = mock_llm_provider
        module._engine.storage = populated_mock_store
        module._engine.pipeline = module._engine._build_pipeline()

        async with module:
            result = await module.query("What is Python?")

        assert "answer" in result
        assert "sources" in result
        assert "metadata" in result
