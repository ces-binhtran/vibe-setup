"""Base interface for vector storage backends."""

from abc import ABC, abstractmethod
from typing import Any

from vibe_rag.models import Document


class BaseVectorStore(ABC):
    """Abstract base class for vector storage implementations.

    All vector storage backends must implement this interface to ensure
    consistent behavior across different storage systems (PostgreSQL + pgvector,
    Pinecone, Weaviate, etc.).

    Supports async context manager protocol for automatic resource cleanup.

    Args:
        collection_name: Name of the collection/table to store vectors

    Example:
        >>> async with PostgresVectorStore(...) as store:
        ...     await store.add_documents(docs, embeddings)
        ...     results = await store.similarity_search(query)
        # Automatic cleanup via close()
    """

    def __init__(self, collection_name: str):
        """Initialize the vector store.

        Args:
            collection_name: Name of the collection/table to store vectors
        """
        self.collection_name = collection_name

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize storage backend (create connections, tables, etc.).

        This method must be called before using the vector store.
        For implementations that don't need initialization, this can be a no-op.

        Raises:
            StorageError: If initialization fails
        """
        pass

    @abstractmethod
    async def add_documents(
        self, documents: list[Document], embeddings: list[list[float]]
    ) -> list[str]:
        """Add documents with their embeddings to the vector store.

        Args:
            documents: List of documents to add
            embeddings: List of embedding vectors (same length as documents)

        Returns:
            List of document IDs that were added

        Raises:
            StorageError: If adding documents fails
        """
        pass

    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[Document]:
        """Search for documents similar to the query embedding.

        Args:
            query_embedding: Vector representation of the query
            k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"source": "docs"})

        Returns:
            List of documents ordered by similarity (most similar first)

        Raises:
            RetrievalError: If search fails
        """
        pass

    @abstractmethod
    async def delete_collection(self) -> None:
        """Delete the entire collection/table.

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connections and cleanup resources.

        This method should be called when the vector store is no longer needed.
        For implementations that don't need cleanup, this can be a no-op.
        """
        pass

    async def __aenter__(self) -> "BaseVectorStore":
        """Enter async context manager - initializes the store.

        Returns:
            Self for use in 'async with' statements
        """
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None:
        """Exit async context manager - closes the store.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)

        Returns:
            None (don't suppress exceptions)
        """
        await self.close()
        return None
