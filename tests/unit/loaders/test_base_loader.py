"""Tests for BaseLoader interface."""

import pytest
from abc import ABC

from vibe_rag.loaders.base import BaseLoader
from vibe_rag.models import Document


def test_base_loader_is_abstract():
    """Test that BaseLoader cannot be instantiated directly."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        BaseLoader()


def test_base_loader_interface():
    """Test that BaseLoader defines required interface."""
    assert hasattr(BaseLoader, "load")


class MockLoader(BaseLoader):
    """Mock loader for testing."""

    async def load(self, file_path: str) -> list[Document]:
        return [Document(content="test", metadata={"source": file_path})]


@pytest.mark.asyncio
async def test_mock_loader_implementation():
    """Test that BaseLoader can be implemented."""
    loader = MockLoader()
    documents = await loader.load("test.txt")

    assert len(documents) == 1
    assert documents[0].content == "test"
    assert documents[0].metadata["source"] == "test.txt"
