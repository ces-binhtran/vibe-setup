"""Configuration models for RAG engine."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LLMConfig(BaseModel):
    """Configuration for LLM provider.

    Attributes:
        provider: Provider type (currently only "gemini" supported)
        api_key: API key for the provider
        model_name: Model name for text generation
        embedding_model: Model name for embeddings
        generation_kwargs: Additional parameters for text generation
    """

    model_config = ConfigDict(frozen=False)

    provider: Literal["gemini"] = "gemini"
    api_key: Optional[str] = None
    model_name: str = "gemini-2.0-flash-exp"
    embedding_model: str = "models/text-embedding-004"
    generation_kwargs: dict[str, Any] = Field(default_factory=dict)


class StorageConfig(BaseModel):
    """Configuration for vector storage.

    Attributes:
        backend: Storage backend type (currently only "postgres" supported)
        collection_name: Name of the collection/table
        connection_string: Database connection string
        vector_dimension: Dimension of embedding vectors (must match LLM embeddings)
    """

    model_config = ConfigDict(frozen=False)

    backend: Literal["postgres"] = "postgres"
    collection_name: str = "documents"
    connection_string: str
    vector_dimension: int = 768

    @field_validator("collection_name")
    @classmethod
    def validate_collection_name(cls, v: str) -> str:
        """Validate collection name is a valid PostgreSQL identifier.

        Args:
            v: Collection name to validate

        Returns:
            Validated collection name

        Raises:
            ValueError: If collection name is invalid
        """
        import re

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(
                f"Invalid collection name: {v}. "
                "Must start with a letter or underscore and contain only "
                "letters, numbers, and underscores."
            )
        return v


class PipelineConfig(BaseModel):
    """Configuration for retrieval pipeline.

    Attributes:
        top_k: Number of documents to retrieve
        filter_metadata: Optional metadata filters for retrieval
        reranking_enabled: Whether to enable reranking (future feature)
    """

    model_config = ConfigDict(frozen=False)

    top_k: int = Field(default=5, ge=1, le=100)
    filter_metadata: Optional[dict[str, Any]] = None
    reranking_enabled: bool = False


class ChunkingConfig(BaseModel):
    """Configuration for document chunking.

    Attributes:
        strategy: Chunking strategy ("fixed" or "recursive")
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between chunks for context preservation
    """

    model_config = ConfigDict(frozen=False)

    strategy: Literal["fixed", "recursive"] = "recursive"
    chunk_size: int = Field(default=512, ge=100, le=4096)
    chunk_overlap: int = Field(default=50, ge=0)

    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """Validate chunk_overlap is less than chunk_size.

        Args:
            v: Chunk overlap value
            info: Validation info containing other field values

        Returns:
            Validated overlap value

        Raises:
            ValueError: If overlap >= chunk_size
        """
        # During model creation, info.data contains the field values
        chunk_size = info.data.get("chunk_size", 512)
        if v >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({v}) must be less than chunk_size ({chunk_size})"
            )
        return v


class RAGConfig(BaseModel):
    """Complete RAG engine configuration.

    This is the main configuration object that orchestrates all components.

    Example:
        >>> config = RAGConfig(
        ...     llm=LLMConfig(api_key="your-key"),
        ...     storage=StorageConfig(connection_string="postgresql://..."),
        ...     pipeline=PipelineConfig(top_k=10),
        ...     chunking=ChunkingConfig(chunk_size=1024)
        ... )
        >>> engine = RAGEngine(config)
    """

    model_config = ConfigDict(frozen=False)

    llm: LLMConfig
    storage: StorageConfig
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)

    def validate_dimensions(self) -> None:
        """Validate embedding dimensions match between LLM and storage.

        Raises:
            ValueError: If dimensions don't match
        """
        # Gemini text-embedding-004 produces 768 dimensions
        if self.llm.embedding_model == "models/text-embedding-004":
            expected_dim = 768
            if self.storage.vector_dimension != expected_dim:
                raise ValueError(
                    f"Storage vector_dimension ({self.storage.vector_dimension}) "
                    f"must match embedding model dimension ({expected_dim})"
                )
