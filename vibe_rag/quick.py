"""QuickSetup convenience class for one-liner RAG initialization."""

from vibe_rag.config.models import ChunkingConfig, LLMConfig, PipelineConfig, RAGConfig, StorageConfig
from vibe_rag.engine import RAGEngine


class QuickSetup:
    """One-liner setup for the RAG engine with sensible defaults.

    Provides a fast path for getting started without verbose configuration.
    Uses Gemini as the LLM provider and PostgreSQL+pgvector for storage.

    Example:
        >>> async with QuickSetup.create(
        ...     provider_api_key="your-api-key",
        ...     database_url="postgresql://user:pass@localhost/db"
        ... ) as rag:
        ...     await rag.ingest("docs.txt")
        ...     result = await rag.query("What is this about?")
        ...     print(result["answer"])
    """

    @staticmethod
    def create(
        provider_api_key: str,
        database_url: str,
        collection_name: str = "documents",
        top_k: int = 5,
    ) -> RAGEngine:
        """Create a pre-configured RAGEngine with sensible defaults.

        Args:
            provider_api_key: Gemini API key
            database_url: PostgreSQL connection string (e.g. "postgresql://...")
            collection_name: Name of the vector store collection (default: "documents")
            top_k: Number of documents to retrieve per query (default: 5)

        Returns:
            Configured RAGEngine (not yet initialized — use as async context manager)
        """
        config = RAGConfig(
            llm=LLMConfig(
                provider="gemini",
                api_key=provider_api_key,
                model_name="gemini-2.0-flash",
                embedding_model="models/gemini-embedding-001",
            ),
            storage=StorageConfig(
                backend="postgres",
                collection_name=collection_name,
                connection_string=database_url,
                vector_dimension=768,
            ),
            pipeline=PipelineConfig(top_k=top_k),
            chunking=ChunkingConfig(
                strategy="recursive",
                chunk_size=512,
                chunk_overlap=50,
            ),
        )
        return RAGEngine(config)
