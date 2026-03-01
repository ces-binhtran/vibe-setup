"""Base interface for vector storage backends."""

from abc import ABC, abstractmethod

from vibe_rag.models import Document


class BaseVectorStore(ABC):
    """Abstract base class for vector storage implementations.

    All vector storage backends must implement this interface to ensure
    consistent behavior across different storage systems (PostgreSQL + pgvector,
    Pinecone, Weaviate, etc.).

    Args:
        collection_name: Name of the collection/table to store vectors
    """

    def __init__(self, collection_name: str):
        """Initialize the vector store.

        Args:
            collection_name: Name of the collection/table to store vectors
        """
        self.collection_name = collection_name

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
