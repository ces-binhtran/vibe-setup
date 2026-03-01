"""Tests for core data models and configuration models."""

import pytest
from vibe_rag.models import Document


def test_document_creation():
    """Test creating a Document with required fields."""
    doc = Document(
        content="Sample content",
        metadata={"source": "test.pdf"}
    )

    assert doc.content == "Sample content"
    assert doc.metadata == {"source": "test.pdf"}
    assert doc.id is not None  # Should auto-generate ID


def test_document_with_id():
    """Test creating a Document with explicit ID."""
    doc_id = "test-id-123"
    doc = Document(
        id=doc_id,
        content="Sample content"
    )

    assert doc.id == doc_id


def test_document_metadata_optional():
    """Test that metadata is optional."""
    doc = Document(content="Sample content")

    assert doc.metadata == {}  # Default to empty dict


def test_document_score_optional():
    """Test that score is optional and defaults to None."""
    doc = Document(content="Sample content")

    assert doc.score is None


def test_document_with_score():
    """Test creating a Document with similarity score."""
    doc = Document(
        content="Sample content",
        score=0.95
    )

    assert doc.score == 0.95


def test_document_id_auto_generation():
    """Test that IDs are auto-generated and unique."""
    doc1 = Document(content="Content 1")
    doc2 = Document(content="Content 2")

    assert doc1.id != doc2.id
    assert len(doc1.id) > 0
    assert len(doc2.id) > 0


# ---------------------------------------------------------------------------
# Configuration model tests
# ---------------------------------------------------------------------------


class TestChunkingConfig:
    """Tests for ChunkingConfig validation and defaults."""

    def test_default_values(self):
        """ChunkingConfig provides sensible defaults."""
        from vibe_rag.config.models import ChunkingConfig

        config = ChunkingConfig()
        assert config.strategy == "recursive"
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50

    def test_fixed_strategy_accepted(self):
        """ChunkingConfig accepts 'fixed' strategy."""
        from vibe_rag.config.models import ChunkingConfig

        config = ChunkingConfig(strategy="fixed", chunk_size=256, chunk_overlap=20)
        assert config.strategy == "fixed"

    def test_recursive_strategy_accepted(self):
        """ChunkingConfig accepts 'recursive' strategy."""
        from vibe_rag.config.models import ChunkingConfig

        config = ChunkingConfig(strategy="recursive", chunk_size=256, chunk_overlap=20)
        assert config.strategy == "recursive"

    def test_chunk_overlap_less_than_chunk_size_is_valid(self):
        """chunk_overlap < chunk_size is accepted."""
        from vibe_rag.config.models import ChunkingConfig

        config = ChunkingConfig(chunk_size=500, chunk_overlap=100)
        assert config.chunk_overlap == 100

    def test_chunk_overlap_equal_to_chunk_size_raises(self):
        """chunk_overlap == chunk_size raises ValueError."""
        from pydantic import ValidationError

        from vibe_rag.config.models import ChunkingConfig

        with pytest.raises(ValidationError) as exc_info:
            ChunkingConfig(chunk_size=256, chunk_overlap=256)

        assert "chunk_overlap" in str(exc_info.value)

    def test_chunk_overlap_greater_than_chunk_size_raises(self):
        """chunk_overlap > chunk_size raises ValueError."""
        from pydantic import ValidationError

        from vibe_rag.config.models import ChunkingConfig

        with pytest.raises(ValidationError) as exc_info:
            ChunkingConfig(chunk_size=100, chunk_overlap=200)

        assert "chunk_overlap" in str(exc_info.value)

    def test_chunk_overlap_zero_is_valid(self):
        """chunk_overlap == 0 is accepted (no overlap)."""
        from vibe_rag.config.models import ChunkingConfig

        config = ChunkingConfig(chunk_size=512, chunk_overlap=0)
        assert config.chunk_overlap == 0

    def test_chunk_size_below_minimum_raises(self):
        """chunk_size < 100 raises ValidationError."""
        from pydantic import ValidationError

        from vibe_rag.config.models import ChunkingConfig

        with pytest.raises(ValidationError):
            ChunkingConfig(chunk_size=50, chunk_overlap=0)

    def test_chunk_size_above_maximum_raises(self):
        """chunk_size > 4096 raises ValidationError."""
        from pydantic import ValidationError

        from vibe_rag.config.models import ChunkingConfig

        with pytest.raises(ValidationError):
            ChunkingConfig(chunk_size=5000, chunk_overlap=0)


class TestStorageConfig:
    """Tests for StorageConfig validation and defaults."""

    def test_valid_collection_name_lowercase(self):
        """Lowercase letters and underscores are valid collection names."""
        from vibe_rag.config.models import StorageConfig

        config = StorageConfig(
            collection_name="my_documents",
            connection_string="postgresql://localhost/db",
        )
        assert config.collection_name == "my_documents"

    def test_valid_collection_name_mixed_case(self):
        """Mixed-case names with underscores and digits are valid."""
        from vibe_rag.config.models import StorageConfig

        config = StorageConfig(
            collection_name="MyDocs_v2",
            connection_string="postgresql://localhost/db",
        )
        assert config.collection_name == "MyDocs_v2"

    def test_valid_collection_name_starts_with_underscore(self):
        """Names starting with underscore are valid PostgreSQL identifiers."""
        from vibe_rag.config.models import StorageConfig

        config = StorageConfig(
            collection_name="_private_table",
            connection_string="postgresql://localhost/db",
        )
        assert config.collection_name == "_private_table"

    def test_invalid_collection_name_starts_with_digit_raises(self):
        """Collection names starting with a digit are invalid."""
        from pydantic import ValidationError

        from vibe_rag.config.models import StorageConfig

        with pytest.raises(ValidationError) as exc_info:
            StorageConfig(
                collection_name="1_bad_name",
                connection_string="postgresql://localhost/db",
            )

        assert "Invalid collection name" in str(exc_info.value)

    def test_invalid_collection_name_with_hyphen_raises(self):
        """Collection names with hyphens are not valid PostgreSQL identifiers."""
        from pydantic import ValidationError

        from vibe_rag.config.models import StorageConfig

        with pytest.raises(ValidationError) as exc_info:
            StorageConfig(
                collection_name="my-collection",
                connection_string="postgresql://localhost/db",
            )

        assert "Invalid collection name" in str(exc_info.value)

    def test_default_backend_is_postgres(self):
        """Default backend is 'postgres'."""
        from vibe_rag.config.models import StorageConfig

        config = StorageConfig(connection_string="postgresql://localhost/db")
        assert config.backend == "postgres"

    def test_default_collection_name_is_documents(self):
        """Default collection name is 'documents'."""
        from vibe_rag.config.models import StorageConfig

        config = StorageConfig(connection_string="postgresql://localhost/db")
        assert config.collection_name == "documents"

    def test_default_vector_dimension_is_768(self):
        """Default vector dimension is 768."""
        from vibe_rag.config.models import StorageConfig

        config = StorageConfig(connection_string="postgresql://localhost/db")
        assert config.vector_dimension == 768


class TestRAGConfigValidation:
    """Tests for RAGConfig.validate_dimensions()."""

    def test_matching_dimensions_passes(self):
        """validate_dimensions() does not raise when dimensions match."""
        from vibe_rag.config.models import LLMConfig, RAGConfig, StorageConfig

        config = RAGConfig(
            llm=LLMConfig(
                embedding_model="models/gemini-embedding-001",
                api_key="key",
            ),
            storage=StorageConfig(
                connection_string="postgresql://localhost/db",
                vector_dimension=768,
            ),
        )
        # Should not raise
        config.validate_dimensions()

    def test_dimension_mismatch_raises_value_error(self):
        """validate_dimensions() raises ValueError when storage dimension mismatches."""
        from vibe_rag.config.models import LLMConfig, RAGConfig, StorageConfig

        config = RAGConfig(
            llm=LLMConfig(
                embedding_model="models/gemini-embedding-001",
                api_key="key",
            ),
            storage=StorageConfig(
                connection_string="postgresql://localhost/db",
                vector_dimension=512,
            ),
        )

        with pytest.raises(ValueError) as exc_info:
            config.validate_dimensions()

        assert "512" in str(exc_info.value)
        assert "768" in str(exc_info.value)

    def test_non_gemini_embedding_model_skips_validation(self):
        """validate_dimensions() is a no-op for non-gemini-embedding-001 models."""
        from vibe_rag.config.models import LLMConfig, RAGConfig, StorageConfig

        # Using a different embedding model - no dimension check performed
        config = RAGConfig(
            llm=LLMConfig(
                embedding_model="models/some-other-model",
                api_key="key",
            ),
            storage=StorageConfig(
                connection_string="postgresql://localhost/db",
                vector_dimension=1536,
            ),
        )
        # Should not raise (no validation for unknown models)
        config.validate_dimensions()

    def test_pipeline_and_chunking_default_factories(self):
        """RAGConfig creates default PipelineConfig and ChunkingConfig when not provided."""
        from vibe_rag.config.models import LLMConfig, RAGConfig, StorageConfig

        config = RAGConfig(
            llm=LLMConfig(api_key="key"),
            storage=StorageConfig(connection_string="postgresql://localhost/db"),
        )
        assert config.pipeline is not None
        assert config.chunking is not None
        assert config.pipeline.top_k == 5
        assert config.chunking.chunk_size == 512


class TestLLMConfig:
    """Tests for LLMConfig defaults and structure."""

    def test_default_provider_is_gemini(self):
        """Default provider is 'gemini'."""
        from vibe_rag.config.models import LLMConfig

        config = LLMConfig()
        assert config.provider == "gemini"

    def test_default_model_name(self):
        """Default model_name is 'gemini-2.0-flash'."""
        from vibe_rag.config.models import LLMConfig

        config = LLMConfig()
        assert config.model_name == "gemini-2.0-flash"

    def test_default_embedding_model(self):
        """Default embedding_model is 'models/gemini-embedding-001'."""
        from vibe_rag.config.models import LLMConfig

        config = LLMConfig()
        assert config.embedding_model == "models/gemini-embedding-001"

    def test_api_key_optional_defaults_to_none(self):
        """api_key is optional and defaults to None."""
        from vibe_rag.config.models import LLMConfig

        config = LLMConfig()
        assert config.api_key is None

    def test_generation_kwargs_defaults_to_empty_dict(self):
        """generation_kwargs defaults to an empty dict."""
        from vibe_rag.config.models import LLMConfig

        config = LLMConfig()
        assert config.generation_kwargs == {}

    def test_generation_kwargs_can_be_set(self):
        """generation_kwargs can be populated with arbitrary key-value pairs."""
        from vibe_rag.config.models import LLMConfig

        config = LLMConfig(generation_kwargs={"temperature": 0.5, "max_tokens": 200})
        assert config.generation_kwargs["temperature"] == 0.5
        assert config.generation_kwargs["max_tokens"] == 200


class TestPipelineConfig:
    """Tests for PipelineConfig defaults and validation."""

    def test_default_top_k_is_5(self):
        """Default top_k is 5."""
        from vibe_rag.config.models import PipelineConfig

        config = PipelineConfig()
        assert config.top_k == 5

    def test_top_k_minimum_is_1(self):
        """top_k must be >= 1."""
        from pydantic import ValidationError

        from vibe_rag.config.models import PipelineConfig

        with pytest.raises(ValidationError):
            PipelineConfig(top_k=0)

    def test_top_k_maximum_is_100(self):
        """top_k must be <= 100."""
        from pydantic import ValidationError

        from vibe_rag.config.models import PipelineConfig

        with pytest.raises(ValidationError):
            PipelineConfig(top_k=101)

    def test_top_k_at_boundaries(self):
        """top_k accepts values at its boundaries (1 and 100)."""
        from vibe_rag.config.models import PipelineConfig

        assert PipelineConfig(top_k=1).top_k == 1
        assert PipelineConfig(top_k=100).top_k == 100

    def test_filter_metadata_defaults_to_none(self):
        """filter_metadata is None by default."""
        from vibe_rag.config.models import PipelineConfig

        config = PipelineConfig()
        assert config.filter_metadata is None

    def test_reranking_enabled_defaults_to_false(self):
        """reranking_enabled defaults to False."""
        from vibe_rag.config.models import PipelineConfig

        config = PipelineConfig()
        assert config.reranking_enabled is False

    def test_filter_metadata_can_be_set(self):
        """filter_metadata accepts a dict of key-value filters."""
        from vibe_rag.config.models import PipelineConfig

        config = PipelineConfig(filter_metadata={"source": "wiki", "lang": "en"})
        assert config.filter_metadata == {"source": "wiki", "lang": "en"}
