"""BasicRAGModule - pre-configured RAG module with sensible defaults."""

from typing import Any, Optional

from vibe_rag.engine import RAGEngine
from vibe_rag.loaders.base import BaseLoader
from vibe_rag.quick import QuickSetup


class BasicRAGModule:
    """Pre-configured RAG module for immediate use with minimal setup.

    A thin wrapper around QuickSetup.create() providing a named, importable
    entry point with explicitly named parameters.

    Example:
        >>> async with BasicRAGModule(
        ...     api_key="your-api-key",
        ...     db_url="postgresql://user:pass@localhost/db"
        ... ) as rag:
        ...     await rag.ingest("knowledge_base.pdf")
        ...     result = await rag.query("What is the main topic?")
        ...     print(result["answer"])
    """

    def __init__(
        self,
        api_key: str,
        db_url: str,
        collection_name: str = "documents",
        top_k: int = 5,
    ) -> None:
        """Initialize BasicRAGModule.

        Args:
            api_key: Gemini API key
            db_url: PostgreSQL connection string
            collection_name: Vector store collection name (default: "documents")
            top_k: Documents to retrieve per query (default: 5)
        """
        self._engine: RAGEngine = QuickSetup.create(
            provider_api_key=api_key,
            database_url=db_url,
            collection_name=collection_name,
            top_k=top_k,
        )

    async def __aenter__(self) -> "BasicRAGModule":
        """Enter async context manager, initializing the underlying engine."""
        await self._engine.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager, closing the underlying engine."""
        await self._engine.close()

    async def ingest(
        self,
        source: str,
        metadata: Optional[dict[str, Any]] = None,
        loader: Optional[BaseLoader] = None,
    ) -> list[str]:
        """Ingest a document into the RAG system.

        Args:
            source: File path to document
            metadata: Optional metadata to attach to all chunks
            loader: Optional custom loader (overrides auto-detection)

        Returns:
            List of document IDs added
        """
        return await self._engine.ingest(source, metadata=metadata, loader=loader)

    async def query(
        self,
        query: str,
        generation_kwargs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Execute a RAG query.

        Args:
            query: User question
            generation_kwargs: Optional parameters for LLM generation

        Returns:
            Dictionary with 'answer', 'sources', and 'metadata'
        """
        return await self._engine.query(query, generation_kwargs=generation_kwargs)
