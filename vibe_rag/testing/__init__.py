"""Testing utilities for vibe-rag.

Provides mock implementations and pytest fixtures for testing vibe-rag components.

Mock Implementations:
    - MockLLMProvider: Fast, deterministic LLM provider for unit tests
    - MockVectorStore: In-memory vector store for isolated testing

Pytest Fixtures:
    - sample_documents: List of varied test documents
    - sample_embeddings: 768-dimensional embedding vectors
    - mock_llm_provider: Pre-configured MockLLMProvider
    - mock_vector_store: Empty MockVectorStore
    - populated_mock_store: MockVectorStore with sample data

Example:
    ```python
    from vibe_rag.testing import MockLLMProvider, sample_documents

    def test_my_feature(sample_documents, mock_llm_provider):
        # Use fixtures in your tests
        result = await mock_llm_provider.generate("test prompt")
        assert "Mock response" in result
    ```
"""

from vibe_rag.testing.fixtures import (
    mock_llm_provider,
    mock_vector_store,
    populated_mock_store,
    sample_documents,
    sample_embeddings,
)
from vibe_rag.testing.mocks import MockLLMProvider, MockVectorStore

__all__ = [
    # Mock implementations
    "MockLLMProvider",
    "MockVectorStore",
    # Fixtures
    "sample_documents",
    "sample_embeddings",
    "mock_llm_provider",
    "mock_vector_store",
    "populated_mock_store",
]
