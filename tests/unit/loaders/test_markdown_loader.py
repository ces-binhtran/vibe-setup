"""Tests for MarkdownLoader."""

import pytest
from unittest.mock import Mock, patch

from vibe_rag.loaders.markdown import MarkdownLoader
from vibe_rag.loaders.base import BaseLoader
from vibe_rag.models import Document
from vibe_rag.utils.errors import DocumentProcessingError


def test_markdown_loader_inheritance():
    """Test that MarkdownLoader inherits from BaseLoader."""
    loader = MarkdownLoader()
    assert isinstance(loader, BaseLoader)


@pytest.mark.asyncio
@patch("vibe_rag.loaders.markdown.Path")
async def test_markdown_loader_load_success(mock_path_class):
    """Test successful markdown loading."""
    markdown_content = """# Title

## Section 1

Some content here.

## Section 2

More content.
"""
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path.read_text.return_value = markdown_content
    mock_path_class.return_value = mock_path

    loader = MarkdownLoader()
    documents = await loader.load("test.md")

    assert len(documents) == 1
    assert documents[0].content == markdown_content
    assert documents[0].metadata["source_file"] == "test.md"
    assert documents[0].metadata["file_type"] == "markdown"
    assert "headers" in documents[0].metadata


@pytest.mark.asyncio
@patch("vibe_rag.loaders.markdown.Path")
async def test_markdown_loader_extract_headers(mock_path_class):
    """Test header extraction from markdown."""
    markdown_content = """# Main Title
## Subtitle
### Subsection
Content here
"""
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path.read_text.return_value = markdown_content
    mock_path_class.return_value = mock_path

    loader = MarkdownLoader()
    documents = await loader.load("test.md")

    headers = documents[0].metadata["headers"]
    assert "# Main Title" in headers
    assert "## Subtitle" in headers
    assert "### Subsection" in headers


@pytest.mark.asyncio
@patch("vibe_rag.loaders.markdown.Path")
async def test_markdown_loader_file_not_found(mock_path_class):
    """Test error handling for missing markdown file."""
    mock_path = Mock()
    mock_path.exists.return_value = False
    mock_path_class.return_value = mock_path

    loader = MarkdownLoader()

    with pytest.raises(DocumentProcessingError) as exc_info:
        await loader.load("missing.md")

    assert "File not found" in str(exc_info.value)
    assert exc_info.value.file_path == "missing.md"


@pytest.mark.asyncio
@patch("vibe_rag.loaders.markdown.Path")
async def test_markdown_loader_encoding_error(mock_path_class):
    """Test error handling for encoding issues."""
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path.read_text.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
    mock_path_class.return_value = mock_path

    loader = MarkdownLoader()

    with pytest.raises(DocumentProcessingError) as exc_info:
        await loader.load("bad_encoding.md")

    assert "Failed to load markdown" in str(exc_info.value)
    assert exc_info.value.error_type == "UnicodeDecodeError"
