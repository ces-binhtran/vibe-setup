"""Pytest configuration and fixtures for vibe-rag tests.

This conftest.py makes all fixtures from vibe_rag.testing.fixtures available
to all test modules without requiring explicit imports.
"""

# Import fixtures to make them available to all tests
# pylint: disable=unused-import
from vibe_rag.testing.fixtures import (
    mock_llm_provider,
    mock_vector_store,
    populated_mock_store,
    sample_documents,
    sample_embeddings,
)
