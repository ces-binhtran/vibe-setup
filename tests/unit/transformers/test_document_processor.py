"""Tests for DocumentProcessor."""


import pytest
from langchain_text_splitters import CharacterTextSplitter

from vibe_rag.models import Document
from vibe_rag.transformers.document import DocumentProcessor
from vibe_rag.utils.errors import ConfigurationError


def test_document_processor_init_default():
    """Test DocumentProcessor with default settings."""
    processor = DocumentProcessor()

    assert processor.chunk_size == 512
    assert processor.chunk_overlap == 50
    assert processor.strategy == "recursive"
    assert processor.text_splitter is not None


def test_document_processor_init_with_strategy():
    """Test DocumentProcessor with built-in strategy."""
    processor = DocumentProcessor(strategy="fixed", chunk_size=256, chunk_overlap=25)

    assert processor.chunk_size == 256
    assert processor.chunk_overlap == 25
    assert processor.strategy == "fixed"


def test_document_processor_init_with_custom_splitter():
    """Test DocumentProcessor with custom splitter."""
    custom_splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=10)
    processor = DocumentProcessor(text_splitter=custom_splitter)

    assert processor.text_splitter is custom_splitter
    assert processor.strategy == "custom"


def test_document_processor_init_invalid_strategy():
    """Test DocumentProcessor with invalid strategy."""
    with pytest.raises(ConfigurationError, match="Unknown chunking strategy"):
        DocumentProcessor(strategy="invalid_strategy")


@pytest.mark.asyncio
async def test_document_processor_process_basic():
    """Test basic document processing."""
    processor = DocumentProcessor(strategy="fixed", chunk_size=20, chunk_overlap=5)

    content = "This is a test document with some content to chunk."
    metadata = {"source_file": "test.txt", "file_type": "text"}

    chunks = await processor.process(content, metadata)

    assert len(chunks) > 0
    assert all(isinstance(chunk, Document) for chunk in chunks)
    # Verify source metadata is copied
    assert all(chunk.metadata.get("source_file") == "test.txt" for chunk in chunks)


@pytest.mark.asyncio
async def test_document_processor_process_metadata_enrichment():
    """Test that chunks are enriched with chunk-specific metadata."""
    processor = DocumentProcessor(strategy="fixed", chunk_size=30, chunk_overlap=10)

    content = "A" * 100  # Simple repeating content
    metadata = {"source": "original"}

    chunks = await processor.process(content, metadata)

    # Verify chunk metadata
    for i, chunk in enumerate(chunks):
        assert chunk.metadata["chunk_index"] == i
        assert chunk.metadata["chunk_total"] == len(chunks)
        assert chunk.metadata["chunking_strategy"] == "fixed"
        assert "parent_doc_id" in chunk.metadata
        assert chunk.metadata["chunk_size"] == len(chunk.content)
        assert chunk.metadata["chunk_overlap"] == 10
        # Verify source metadata copied
        assert chunk.metadata["source"] == "original"


@pytest.mark.asyncio
async def test_document_processor_process_empty_content():
    """Test processing empty content."""
    processor = DocumentProcessor()

    chunks = await processor.process("", {})

    # Empty content should return empty list or single empty chunk
    # LangChain behavior may vary, just ensure it doesn't crash
    assert isinstance(chunks, list)


@pytest.mark.asyncio
async def test_document_processor_process_no_metadata():
    """Test processing without metadata."""
    processor = DocumentProcessor(strategy="recursive", chunk_size=50)

    content = "Some content without metadata."

    chunks = await processor.process(content)

    assert len(chunks) > 0
    # Should still have chunk metadata even without source metadata
    assert all("chunk_index" in chunk.metadata for chunk in chunks)


def test_document_processor_register_strategy():
    """Test registering custom strategy."""

    # Create a mock splitter class
    class CustomSplitter:
        def __init__(self, chunk_size, chunk_overlap):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap

        def split_text(self, text):
            return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

    # Register custom strategy
    DocumentProcessor.register_strategy("custom_test", CustomSplitter)

    # Verify it's registered
    assert "custom_test" in DocumentProcessor._strategies

    # Use the custom strategy
    processor = DocumentProcessor(strategy="custom_test", chunk_size=10)
    assert processor.strategy == "custom_test"
    assert isinstance(processor.text_splitter, CustomSplitter)


def test_document_processor_register_strategy_duplicate():
    """Test registering strategy with existing name."""

    class AnotherSplitter:
        pass

    # Should allow overwriting existing strategies
    DocumentProcessor.register_strategy("fixed", AnotherSplitter)
    assert DocumentProcessor._strategies["fixed"] == AnotherSplitter

    # Restore original for other tests
    DocumentProcessor.register_strategy("fixed", CharacterTextSplitter)
