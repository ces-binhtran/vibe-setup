"""Tests for TextLoader."""

import pytest
from unittest.mock import AsyncMock, Mock, patch, mock_open
from pathlib import Path

from vibe_rag.loaders.text import TextLoader
from vibe_rag.loaders.base import BaseLoader
from vibe_rag.models import Document
from vibe_rag.utils.errors import DocumentProcessingError


def test_text_loader_inheritance():
    """Test that TextLoader inherits from BaseLoader."""
    loader = TextLoader()
    assert isinstance(loader, BaseLoader)


@pytest.mark.asyncio
@patch("vibe_rag.loaders.text.Path")
async def test_text_loader_load_success(mock_path_class):
    """Test successful text file loading."""
    # Mock file reading
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path.read_text.return_value = "Test file content"
    mock_path_class.return_value = mock_path

    loader = TextLoader()
    documents = await loader.load("test.txt")

    assert len(documents) == 1
    assert documents[0].content == "Test file content"
    assert documents[0].metadata["source_file"] == "test.txt"
    assert documents[0].metadata["file_type"] == "text"
    assert documents[0].metadata["encoding"] == "utf-8"


@pytest.mark.asyncio
@patch("vibe_rag.loaders.text.Path")
async def test_text_loader_file_not_found(mock_path_class):
    """Test error handling for missing file."""
    mock_path = Mock()
    mock_path.exists.return_value = False
    mock_path_class.return_value = mock_path

    loader = TextLoader()

    with pytest.raises(DocumentProcessingError) as exc_info:
        await loader.load("missing.txt")

    assert "File not found" in str(exc_info.value)
    assert exc_info.value.file_path == "missing.txt"
    assert exc_info.value.error_type == "FileNotFoundError"


@pytest.mark.asyncio
@patch("vibe_rag.loaders.text.Path")
async def test_text_loader_not_a_file(mock_path_class):
    """Test error handling for directory path."""
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = False
    mock_path_class.return_value = mock_path

    loader = TextLoader()

    with pytest.raises(DocumentProcessingError) as exc_info:
        await loader.load("directory/")

    assert "Not a file" in str(exc_info.value)
    assert exc_info.value.error_type == "IsADirectoryError"


@pytest.mark.asyncio
@patch("vibe_rag.loaders.text.Path")
async def test_text_loader_encoding_fallback(mock_path_class):
    """Test encoding detection with fallback."""
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True

    # First call (utf-8) fails, second (latin-1) succeeds
    mock_path.read_text.side_effect = [
        UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"),
        "Content with latin-1 encoding",
    ]

    mock_path_class.return_value = mock_path

    loader = TextLoader()
    documents = await loader.load("test.txt")

    assert len(documents) == 1
    assert documents[0].content == "Content with latin-1 encoding"
    assert documents[0].metadata["encoding"] == "latin-1"
