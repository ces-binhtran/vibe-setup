"""Mock implementations for testing vibe-rag components."""

import hashlib
from typing import Any, Optional

from vibe_rag.models import Document


class MockLLMProvider:
    """Mock LLM provider for testing.

    Provides deterministic responses for unit testing without external API calls.
    Implements the expected BaseLLMProvider interface.

    Design decisions:
    - Returns predictable responses based on prompt content
    - No network calls or API dependencies
    - Async methods for compatibility with real providers
    - Deterministic embeddings for reproducible tests
    """

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "mock"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> str:
        """Generate predictable mock response.

        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Sampling temperature (ignored in mock)
            max_tokens: Maximum tokens (ignored in mock)
            **kwargs: Additional parameters (ignored in mock)

        Returns:
            Deterministic response based on prompt
        """
        if system_prompt:
            return f"Mock response to system '{system_prompt}' and prompt '{prompt}'"
        return f"Mock response to: {prompt}"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate deterministic mock embeddings.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (768-dimensional)

        Note:
            Returns same embedding for same text (deterministic)
            Embedding dimension matches common models (768)
        """
        # Return deterministic embeddings based on MD5 hash
        embeddings = []
        for text in texts:
            # Use MD5 for deterministic hashing across processes
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16) % 1000 / 1000.0
            embedding = [hash_val + i * 0.01 for i in range(768)]
            embeddings.append(embedding)
        return embeddings


class MockVectorStore:
    """Mock vector store for testing.

    In-memory storage for fast, isolated unit testing without database dependencies.
    Implements the expected BaseVectorStore interface.

    Design decisions:
    - Uses dict for in-memory storage (fast, isolated)
    - Simple cosine similarity for search (deterministic)
    - Supports all base operations (add, search, delete)
    - No external dependencies or setup required
    """

    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self.documents: dict[str, list[tuple[Document, list[float]]]] = {}

    @property
    def store_name(self) -> str:
        """Return storage backend identifier."""
        return "mock"

    async def add_documents(
        self, documents: list[Document], collection_name: str, embeddings: list[list[float]]
    ) -> list[str]:
        """Add documents with embeddings to collection.

        Args:
            documents: List of documents to add
            collection_name: Name of the collection
            embeddings: List of embedding vectors (one per document)

        Returns:
            List of document IDs

        Raises:
            ValueError: If documents and embeddings counts don't match
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Document count ({len(documents)}) must match "
                f"embedding count ({len(embeddings)})"
            )

        # Initialize collection if needed
        if collection_name not in self.documents:
            self.documents[collection_name] = []

        # Store documents with their embeddings
        doc_ids = []
        for doc, embedding in zip(documents, embeddings):
            self.documents[collection_name].append((doc, embedding))
            doc_ids.append(doc.id)

        return doc_ids

    async def similarity_search(
        self,
        query_embedding: list[float],
        collection_name: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> list[Document]:
        """Search for similar documents using cosine similarity.

        Args:
            query_embedding: Query embedding vector
            collection_name: Name of the collection to search
            top_k: Number of top results to return
            filters: Optional metadata filters

        Returns:
            List of similar documents with scores

        Note:
            Simple cosine similarity implementation for testing
            Filters match exact metadata key-value pairs
        """
        if collection_name not in self.documents:
            return []

        # Calculate similarities
        results = []
        for doc, embedding in self.documents[collection_name]:
            # Apply metadata filters if provided
            if filters:
                if not all(doc.metadata.get(key) == value for key, value in filters.items()):
                    continue

            # Simple cosine similarity
            similarity = self._cosine_similarity(query_embedding, embedding)
            # Copy document and update score for result
            doc_with_score = doc.model_copy(update={"score": similarity})
            results.append(doc_with_score)

        # Sort by similarity score (descending) and return top_k
        results.sort(key=lambda d: d.score or 0.0, reverse=True)
        return results[:top_k]

    async def delete_collection(self, collection_name: str) -> None:
        """Delete an entire collection.

        Args:
            collection_name: Name of the collection to delete
        """
        if collection_name in self.documents:
            del self.documents[collection_name]

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (-1.0 to 1.0)

        Note:
            Returns 0.0 if vectors have different dimensions or zero magnitude
        """
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return float(dot_product / (magnitude1 * magnitude2))
