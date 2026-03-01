"""Tests for PDFLoader."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from vibe_rag.loaders.pdf import PDFLoader
from vibe_rag.loaders.base import BaseLoader
from vibe_rag.models import Document
from vibe_rag.utils.errors import DocumentProcessingError


def test_pdf_loader_inheritance():
    """Test that PDFLoader inherits from BaseLoader."""
    loader = PDFLoader()
    assert isinstance(loader, BaseLoader)


@pytest.mark.asyncio
@patch("builtins.open", create=True)
@patch("vibe_rag.loaders.pdf.PyPDF2.PdfReader")
@patch("vibe_rag.loaders.pdf.Path")
async def test_pdf_loader_load_success(mock_path_class, mock_pdf_reader, mock_open):
    """Test successful PDF loading."""
    # Mock file path
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path_class.return_value = mock_path

    # Mock file opening
    mock_file = Mock()
    mock_open.return_value.__enter__.return_value = mock_file

    # Mock PDF pages
    mock_page1 = Mock()
    mock_page1.extract_text.return_value = "Page 1 content"
    mock_page2 = Mock()
    mock_page2.extract_text.return_value = "Page 2 content"

    mock_reader = Mock()
    mock_reader.pages = [mock_page1, mock_page2]
    mock_pdf_reader.return_value = mock_reader

    loader = PDFLoader()
    documents = await loader.load("test.pdf")

    assert len(documents) == 2
    assert documents[0].content == "Page 1 content"
    assert documents[0].metadata["source_file"] == "test.pdf"
    assert documents[0].metadata["file_type"] == "pdf"
    assert documents[0].metadata["page_number"] == 1
    assert documents[0].metadata["total_pages"] == 2

    assert documents[1].content == "Page 2 content"
    assert documents[1].metadata["page_number"] == 2


@pytest.mark.asyncio
@patch("vibe_rag.loaders.pdf.Path")
async def test_pdf_loader_file_not_found(mock_path_class):
    """Test error handling for missing PDF."""
    mock_path = Mock()
    mock_path.exists.return_value = False
    mock_path_class.return_value = mock_path

    loader = PDFLoader()

    with pytest.raises(DocumentProcessingError) as exc_info:
        await loader.load("missing.pdf")

    assert "File not found" in str(exc_info.value)
    assert exc_info.value.file_path == "missing.pdf"


@pytest.mark.asyncio
@patch("builtins.open", create=True)
@patch("vibe_rag.loaders.pdf.PyPDF2.PdfReader")
@patch("vibe_rag.loaders.pdf.Path")
async def test_pdf_loader_corrupt_pdf(mock_path_class, mock_pdf_reader, mock_open):
    """Test error handling for corrupt PDF."""
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path_class.return_value = mock_path

    # Mock file opening
    mock_file = Mock()
    mock_open.return_value.__enter__.return_value = mock_file

    # Simulate corrupt PDF
    mock_pdf_reader.side_effect = Exception("PDF parsing error")

    loader = PDFLoader()

    with pytest.raises(DocumentProcessingError) as exc_info:
        await loader.load("corrupt.pdf")

    assert "Failed to load PDF" in str(exc_info.value)
    assert exc_info.value.file_path == "corrupt.pdf"
    assert exc_info.value.error_type == "Exception"


@pytest.mark.asyncio
@patch("builtins.open", create=True)
@patch("vibe_rag.loaders.pdf.PyPDF2.PdfReader")
@patch("vibe_rag.loaders.pdf.Path")
async def test_pdf_loader_partial_failure(mock_path_class, mock_pdf_reader, mock_open):
    """Test partial results when some pages fail."""
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path_class.return_value = mock_path

    # Mock file opening
    mock_file = Mock()
    mock_open.return_value.__enter__.return_value = mock_file

    # Page 1 succeeds, page 2 fails
    mock_page1 = Mock()
    mock_page1.extract_text.return_value = "Page 1 content"
    mock_page2 = Mock()
    mock_page2.extract_text.side_effect = Exception("Page extraction error")

    mock_reader = Mock()
    mock_reader.pages = [mock_page1, mock_page2]
    mock_pdf_reader.return_value = mock_reader

    loader = PDFLoader()

    with pytest.raises(DocumentProcessingError) as exc_info:
        await loader.load("partial.pdf")

    # Should have partial results
    assert exc_info.value.partial_results is not None
    assert len(exc_info.value.partial_results) == 1
    assert exc_info.value.partial_results[0].content == "Page 1 content"
