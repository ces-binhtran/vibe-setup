"""Pytest fixtures for vibe-rag testing."""

import pytest

from vibe_rag.models import Document
from vibe_rag.testing.mocks import MockLLMProvider, MockVectorStore


@pytest.fixture
def sample_documents() -> list[Document]:
    """Sample documents for testing.

    Returns:
        List of 3 documents with varied content and metadata

    Design notes:
        - Covers different document types (guide, tutorial, handbook)
        - Includes metadata for testing filtering
        - Content varies for similarity testing
    """
    return [
        Document(
            content="Python programming guide for beginners",
            metadata={"type": "guide", "topic": "python", "level": "beginner"},
        ),
        Document(
            content="Machine learning tutorial with practical examples",
            metadata={"type": "tutorial", "topic": "ml", "level": "intermediate"},
        ),
        Document(
            content="Data science handbook covering statistics and visualization",
            metadata={"type": "handbook", "topic": "data-science", "level": "advanced"},
        ),
    ]


@pytest.fixture
def sample_embeddings() -> list[list[float]]:
    """Sample embedding vectors for testing.

    Returns:
        List of 3 embedding vectors (768-dimensional)

    Design notes:
        - 768 dimensions match common embedding models
        - Different patterns for similarity testing
        - Deterministic values for reproducible tests
    """
    return [
        [0.1 + i * 0.001 for i in range(768)],  # Pattern 1
        [0.5 + i * 0.001 for i in range(768)],  # Pattern 2
        [0.9 + i * 0.001 for i in range(768)],  # Pattern 3
    ]


@pytest.fixture
def mock_llm_provider() -> MockLLMProvider:
    """Pre-configured mock LLM provider.

    Returns:
        MockLLMProvider instance ready for testing

    Design notes:
        - Instantiated and ready to use
        - No configuration needed
        - Provides deterministic responses
    """
    return MockLLMProvider()


@pytest.fixture
def mock_vector_store() -> MockVectorStore:
    """Pre-configured mock vector store.

    Returns:
        MockVectorStore instance ready for testing

    Design notes:
        - Empty in-memory storage
        - Fresh instance per test (isolation)
        - No cleanup needed (garbage collected)
    """
    return MockVectorStore()


@pytest.fixture
async def populated_mock_store(
    sample_documents: list[Document], sample_embeddings: list[list[float]]
) -> MockVectorStore:
    """Mock vector store pre-populated with sample documents.

    Args:
        sample_documents: Fixture providing sample documents
        sample_embeddings: Fixture providing sample embeddings

    Returns:
        MockVectorStore with documents already added

    Design notes:
        - Ready for immediate search testing
        - Uses 'test_collection' as collection name
        - Combines sample_documents and sample_embeddings fixtures
    """
    store = MockVectorStore("test_collection")
    await store.add_documents(sample_documents, sample_embeddings)
    return store
