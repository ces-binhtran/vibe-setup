# Document Processing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement document loading and chunking capabilities for vibe-rag with flexible strategy system and rich metadata traceability.

**Architecture:** Three components - DocumentProcessor (orchestrates chunking with strategy registry), Document Loaders (TextLoader, PDFLoader, MarkdownLoader wrapping LangChain), and DocumentProcessingError (rich error context). Follows TDD with mocked LangChain dependencies.

**Tech Stack:** Python 3.10+, LangChain text splitters and loaders, Pydantic, pytest with AsyncMock

---

## Task 1: Add DocumentProcessingError Exception

**Files:**
- Modify: `vibe_rag/utils/errors.py`
- Test: `tests/unit/test_errors.py`

**Step 1: Write failing tests for DocumentProcessingError**

Create or append to `tests/unit/test_errors.py`:

```python
import pytest
from vibe_rag.utils.errors import DocumentProcessingError
from vibe_rag.models import Document


def test_document_processing_error_basic():
    """Test basic DocumentProcessingError initialization."""
    error = DocumentProcessingError("Test error")
    assert str(error) == "Test error"
    assert error.file_path is None
    assert error.error_type is None
    assert error.original_error is None
    assert error.partial_results is None


def test_document_processing_error_with_context():
    """Test DocumentProcessingError with full context."""
    original = ValueError("Original error")
    partial_docs = [Document(content="test", metadata={"page": 1})]

    error = DocumentProcessingError(
        message="Failed to process document",
        file_path="/path/to/doc.pdf",
        error_type="CorruptPDFError",
        original_error=original,
        partial_results=partial_docs,
    )

    assert str(error) == "Failed to process document"
    assert error.file_path == "/path/to/doc.pdf"
    assert error.error_type == "CorruptPDFError"
    assert error.original_error is original
    assert error.partial_results == partial_docs
    assert len(error.partial_results) == 1


def test_document_processing_error_inheritance():
    """Test that DocumentProcessingError inherits from RAGException."""
    from vibe_rag.utils.errors import RAGException

    error = DocumentProcessingError("test")
    assert isinstance(error, RAGException)
    assert isinstance(error, Exception)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_errors.py::test_document_processing_error_basic -v`
Expected: FAIL with "ImportError: cannot import name 'DocumentProcessingError'"

**Step 3: Implement DocumentProcessingError**

Add to `vibe_rag/utils/errors.py`:

```python
class DocumentProcessingError(RAGException):
    """Document processing failed (loading or chunking).

    Provides rich context for debugging and visualization systems.

    Attributes:
        file_path: Path to file that failed
        error_type: Error category (FileNotFoundError, CorruptPDFError, etc.)
        original_error: Underlying exception
        partial_results: Any successfully processed chunks/pages
    """

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        error_type: str | None = None,
        original_error: Exception | None = None,
        partial_results: list | None = None,
    ):
        """Initialize error with context.

        Args:
            message: Human-readable error description
            file_path: Path to file that failed
            error_type: Error category
            original_error: Underlying exception
            partial_results: Any successfully processed chunks/pages
        """
        super().__init__(message)
        self.file_path = file_path
        self.error_type = error_type
        self.original_error = original_error
        self.partial_results = partial_results
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_errors.py::test_document_processing_error -v`
Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add vibe_rag/utils/errors.py tests/unit/test_errors.py
git commit -m "feat: add DocumentProcessingError with rich context

- Add DocumentProcessingError exception class
- Support file_path, error_type, original_error, partial_results
- Enable detailed error tracking for visualization
- Add comprehensive tests with context validation"
```

---

## Task 2: Implement DocumentProcessor Core

**Files:**
- Create: `vibe_rag/transformers/document.py`
- Create: `tests/unit/transformers/__init__.py`
- Create: `tests/unit/transformers/test_document_processor.py`

**Step 1: Write failing tests for DocumentProcessor initialization**

Create `tests/unit/transformers/__init__.py` (empty file).

Create `tests/unit/transformers/test_document_processor.py`:

```python
"""Tests for DocumentProcessor."""

import pytest
from unittest.mock import Mock, patch
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter

from vibe_rag.transformers.document import DocumentProcessor
from vibe_rag.models import Document
from vibe_rag.utils.errors import DocumentProcessingError, ConfigurationError


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
    custom_splitter = CharacterTextSplitter(chunk_size=100)
    processor = DocumentProcessor(text_splitter=custom_splitter)

    assert processor.text_splitter is custom_splitter
    assert processor.strategy == "custom"


def test_document_processor_init_invalid_strategy():
    """Test DocumentProcessor with invalid strategy."""
    with pytest.raises(ConfigurationError, match="Unknown chunking strategy"):
        DocumentProcessor(strategy="invalid_strategy")
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/transformers/test_document_processor.py::test_document_processor_init_default -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.transformers.document'"

**Step 3: Implement DocumentProcessor initialization**

Create `vibe_rag/transformers/document.py`:

```python
"""Document processing and chunking."""

from typing import Optional
from langchain.text_splitter import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    TextSplitter,
)

from vibe_rag.models import Document
from vibe_rag.utils.errors import ConfigurationError, DocumentProcessingError


class DocumentProcessor:
    """Handles document chunking with flexible strategy system.

    Supports three usage modes:
    1. Direct injection: Pass any LangChain text splitter
    2. Built-in strategies: Use "fixed" or "recursive"
    3. Custom registry: Register and use custom strategies
    """

    # Strategy registry (class variable)
    _strategies: dict[str, type[TextSplitter]] = {
        "fixed": CharacterTextSplitter,
        "recursive": RecursiveCharacterTextSplitter,
    }

    def __init__(
        self,
        text_splitter: Optional[TextSplitter] = None,
        strategy: str = "recursive",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        """Initialize DocumentProcessor.

        Args:
            text_splitter: Custom LangChain text splitter (overrides strategy)
            strategy: Built-in strategy name ("fixed", "recursive")
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks for context preservation

        Raises:
            ConfigurationError: If strategy is unknown and no text_splitter provided
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        if text_splitter is not None:
            # Custom splitter provided - use it directly
            self.text_splitter = text_splitter
            self.strategy = "custom"
        else:
            # Use built-in strategy
            if strategy not in self._strategies:
                raise ConfigurationError(
                    f"Unknown chunking strategy: {strategy}. "
                    f"Available: {list(self._strategies.keys())}"
                )

            self.strategy = strategy
            splitter_class = self._strategies[strategy]

            # Instantiate the splitter with chunk size and overlap
            self.text_splitter = splitter_class(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/transformers/test_document_processor.py::test_document_processor_init -v`
Expected: PASS (all 4 init tests)

**Step 5: Commit**

```bash
git add vibe_rag/transformers/document.py tests/unit/transformers/
git commit -m "feat: add DocumentProcessor initialization

- Implement DocumentProcessor with strategy system
- Support built-in strategies (fixed, recursive)
- Support custom text splitter injection
- Add strategy registry pattern
- Validate strategy names with ConfigurationError"
```

---

## Task 3: Implement DocumentProcessor.process() Method

**Files:**
- Modify: `vibe_rag/transformers/document.py`
- Modify: `tests/unit/transformers/test_document_processor.py`

**Step 1: Write failing tests for process() method**

Add to `tests/unit/transformers/test_document_processor.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/transformers/test_document_processor.py::test_document_processor_process_basic -v`
Expected: FAIL with "AttributeError: 'DocumentProcessor' object has no attribute 'process'"

**Step 3: Implement process() method**

Add to `vibe_rag/transformers/document.py`:

```python
from uuid import uuid4


class DocumentProcessor:
    # ... (existing code)

    async def process(
        self, content: str, metadata: Optional[dict] = None
    ) -> list[Document]:
        """Process text into chunks with enriched metadata.

        Args:
            content: Text content to chunk
            metadata: Source metadata to copy to chunks

        Returns:
            List of Document objects with enriched metadata

        Raises:
            DocumentProcessingError: If chunking fails
        """
        try:
            # Split text using configured splitter
            chunks_text = self.text_splitter.split_text(content)

            # Generate parent document ID for traceability
            parent_doc_id = str(uuid4())

            # Create Document objects with enriched metadata
            documents = []
            chunk_total = len(chunks_text)

            for i, chunk_text in enumerate(chunks_text):
                # Start with source metadata (if provided)
                chunk_metadata = metadata.copy() if metadata else {}

                # Add chunk-specific metadata
                chunk_metadata.update(
                    {
                        "chunk_index": i,
                        "chunk_total": chunk_total,
                        "chunk_size": len(chunk_text),
                        "chunking_strategy": self.strategy,
                        "parent_doc_id": parent_doc_id,
                        "chunk_overlap": self.chunk_overlap,
                    }
                )

                # Create Document
                doc = Document(content=chunk_text, metadata=chunk_metadata)
                documents.append(doc)

            return documents

        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to process document: {e}",
                error_type=type(e).__name__,
                original_error=e,
            )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/transformers/test_document_processor.py::test_document_processor_process -v`
Expected: PASS (all 4 process tests)

**Step 5: Commit**

```bash
git add vibe_rag/transformers/document.py tests/unit/transformers/test_document_processor.py
git commit -m "feat: implement DocumentProcessor.process() method

- Add async process() method for text chunking
- Enrich chunks with metadata (index, total, size, strategy, parent_id)
- Copy source metadata to all chunks
- Handle errors with DocumentProcessingError
- Add comprehensive tests for metadata enrichment"
```

---

## Task 4: Implement DocumentProcessor Strategy Registry

**Files:**
- Modify: `vibe_rag/transformers/document.py`
- Modify: `tests/unit/transformers/test_document_processor.py`

**Step 1: Write failing tests for register_strategy()**

Add to `tests/unit/transformers/test_document_processor.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/transformers/test_document_processor.py::test_document_processor_register_strategy -v`
Expected: FAIL with "AttributeError: type object 'DocumentProcessor' has no attribute 'register_strategy'"

**Step 3: Implement register_strategy() class method**

Add to `vibe_rag/transformers/document.py` in the `DocumentProcessor` class:

```python
    @classmethod
    def register_strategy(cls, name: str, splitter_class: type) -> None:
        """Register custom chunking strategy.

        Args:
            name: Strategy identifier
            splitter_class: TextSplitter class (or compatible)
        """
        cls._strategies[name] = splitter_class
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/transformers/test_document_processor.py::test_document_processor_register_strategy -v`
Expected: PASS (both registry tests)

**Step 5: Commit**

```bash
git add vibe_rag/transformers/document.py tests/unit/transformers/test_document_processor.py
git commit -m "feat: add strategy registry to DocumentProcessor

- Implement register_strategy() class method
- Allow custom strategies to be registered dynamically
- Support strategy name overwriting
- Add tests for registry functionality"
```

---

## Task 5: Export DocumentProcessor in Package

**Files:**
- Modify: `vibe_rag/transformers/__init__.py`
- Modify: `vibe_rag/__init__.py`

**Step 1: Update transformers package exports**

Edit `vibe_rag/transformers/__init__.py`:

```python
"""Document transformers and processors."""

from vibe_rag.transformers.document import DocumentProcessor

__all__ = ["DocumentProcessor"]
```

**Step 2: Update main package exports**

Edit `vibe_rag/__init__.py` to add:

```python
from vibe_rag.transformers import DocumentProcessor
```

And add to `__all__`:

```python
"DocumentProcessor",
```

**Step 3: Verify imports work**

Run: `python -c "from vibe_rag import DocumentProcessor; print('Import success')"`
Expected: "Import success"

**Step 4: Commit**

```bash
git add vibe_rag/transformers/__init__.py vibe_rag/__init__.py
git commit -m "feat: export DocumentProcessor in package

- Add DocumentProcessor to transformers package exports
- Export DocumentProcessor from main vibe_rag package
- Enable direct import: from vibe_rag import DocumentProcessor"
```

---

## Task 6: Implement BaseLoader Interface

**Files:**
- Create: `vibe_rag/loaders/base.py`
- Create: `tests/unit/loaders/__init__.py`
- Create: `tests/unit/loaders/test_base_loader.py`

**Step 1: Write failing tests for BaseLoader**

Create `tests/unit/loaders/__init__.py` (empty file).

Create `tests/unit/loaders/test_base_loader.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/loaders/test_base_loader.py::test_base_loader_is_abstract -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.loaders.base'"

**Step 3: Implement BaseLoader**

Create `vibe_rag/loaders/base.py`:

```python
"""Base loader interface."""

from abc import ABC, abstractmethod

from vibe_rag.models import Document


class BaseLoader(ABC):
    """Base interface for document loaders.

    All loaders must implement the load() method to load documents
    from file paths and return Document objects with metadata.
    """

    @abstractmethod
    async def load(self, file_path: str) -> list[Document]:
        """Load document(s) from file path.

        Args:
            file_path: Path to file

        Returns:
            List of Document objects with metadata

        Raises:
            DocumentProcessingError: If loading fails
        """
        pass
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/loaders/test_base_loader.py -v`
Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add vibe_rag/loaders/base.py tests/unit/loaders/
git commit -m "feat: add BaseLoader interface

- Create abstract BaseLoader class
- Define load() method interface
- Add tests for abstract interface
- Verify mock implementation works"
```

---

## Task 7: Implement TextLoader

**Files:**
- Create: `vibe_rag/loaders/text.py`
- Create: `tests/unit/loaders/test_text_loader.py`

**Step 1: Write failing tests for TextLoader**

Create `tests/unit/loaders/test_text_loader.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/loaders/test_text_loader.py::test_text_loader_inheritance -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.loaders.text'"

**Step 3: Implement TextLoader**

Create `vibe_rag/loaders/text.py`:

```python
"""Text file loader."""

from pathlib import Path

from vibe_rag.loaders.base import BaseLoader
from vibe_rag.models import Document
from vibe_rag.utils.errors import DocumentProcessingError


class TextLoader(BaseLoader):
    """Load plain text files with encoding detection.

    Attempts to detect file encoding using common encodings:
    utf-8, latin-1, cp1252
    """

    ENCODINGS = ["utf-8", "latin-1", "cp1252"]

    async def load(self, file_path: str) -> list[Document]:
        """Load text file with encoding detection.

        Args:
            file_path: Path to text file

        Returns:
            List containing single Document with file content

        Raises:
            DocumentProcessingError: If file not found, not a file, or encoding fails
        """
        path = Path(file_path)

        # Validate file exists and is a file
        if not path.exists():
            raise DocumentProcessingError(
                f"File not found: {file_path}",
                file_path=file_path,
                error_type="FileNotFoundError",
            )

        if not path.is_file():
            raise DocumentProcessingError(
                f"Not a file: {file_path}",
                file_path=file_path,
                error_type="IsADirectoryError",
            )

        # Try to read with different encodings
        content = None
        encoding_used = None

        for encoding in self.ENCODINGS:
            try:
                content = path.read_text(encoding=encoding)
                encoding_used = encoding
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise DocumentProcessingError(
                f"Failed to decode file with any encoding: {self.ENCODINGS}",
                file_path=file_path,
                error_type="EncodingError",
            )

        # Create document with metadata
        metadata = {
            "source_file": file_path,
            "file_type": "text",
            "encoding": encoding_used,
        }

        return [Document(content=content, metadata=metadata)]
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/loaders/test_text_loader.py -v`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add vibe_rag/loaders/text.py tests/unit/loaders/test_text_loader.py
git commit -m "feat: implement TextLoader with encoding detection

- Add TextLoader for plain text files
- Support multiple encodings (utf-8, latin-1, cp1252)
- Validate file exists and is a file
- Raise DocumentProcessingError with context
- Add comprehensive tests with mocking"
```

---

## Task 8: Implement PDFLoader

**Files:**
- Create: `vibe_rag/loaders/pdf.py`
- Create: `tests/unit/loaders/test_pdf_loader.py`

**Step 1: Write failing tests for PDFLoader**

Create `tests/unit/loaders/test_pdf_loader.py`:

```python
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
@patch("vibe_rag.loaders.pdf.PyPDF2.PdfReader")
@patch("vibe_rag.loaders.pdf.Path")
async def test_pdf_loader_load_success(mock_path_class, mock_pdf_reader):
    """Test successful PDF loading."""
    # Mock file path
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path_class.return_value = mock_path

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
@patch("vibe_rag.loaders.pdf.PyPDF2.PdfReader")
@patch("vibe_rag.loaders.pdf.Path")
async def test_pdf_loader_corrupt_pdf(mock_path_class, mock_pdf_reader):
    """Test error handling for corrupt PDF."""
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path_class.return_value = mock_path

    # Simulate corrupt PDF
    mock_pdf_reader.side_effect = Exception("PDF parsing error")

    loader = PDFLoader()

    with pytest.raises(DocumentProcessingError) as exc_info:
        await loader.load("corrupt.pdf")

    assert "Failed to load PDF" in str(exc_info.value)
    assert exc_info.value.file_path == "corrupt.pdf"
    assert exc_info.value.error_type == "Exception"


@pytest.mark.asyncio
@patch("vibe_rag.loaders.pdf.PyPDF2.PdfReader")
@patch("vibe_rag.loaders.pdf.Path")
async def test_pdf_loader_partial_failure(mock_path_class, mock_pdf_reader):
    """Test partial results when some pages fail."""
    mock_path = Mock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path_class.return_value = mock_path

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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/loaders/test_pdf_loader.py::test_pdf_loader_inheritance -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.loaders.pdf'"

**Step 3: Implement PDFLoader**

Create `vibe_rag/loaders/pdf.py`:

```python
"""PDF file loader."""

from pathlib import Path
import PyPDF2

from vibe_rag.loaders.base import BaseLoader
from vibe_rag.models import Document
from vibe_rag.utils.errors import DocumentProcessingError


class PDFLoader(BaseLoader):
    """Load PDF files page-by-page.

    Extracts text from each page and returns a Document per page
    with page metadata.
    """

    async def load(self, file_path: str) -> list[Document]:
        """Load PDF file and extract text from all pages.

        Args:
            file_path: Path to PDF file

        Returns:
            List of Documents (one per page) with page metadata

        Raises:
            DocumentProcessingError: If file not found or PDF parsing fails
        """
        path = Path(file_path)

        # Validate file exists and is a file
        if not path.exists():
            raise DocumentProcessingError(
                f"File not found: {file_path}",
                file_path=file_path,
                error_type="FileNotFoundError",
            )

        if not path.is_file():
            raise DocumentProcessingError(
                f"Not a file: {file_path}",
                file_path=file_path,
                error_type="IsADirectoryError",
            )

        try:
            # Open PDF
            with open(path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                total_pages = len(reader.pages)

                documents = []
                partial_results = []

                # Extract text from each page
                for page_num, page in enumerate(reader.pages, start=1):
                    try:
                        text = page.extract_text()

                        # Create document with page metadata
                        metadata = {
                            "source_file": file_path,
                            "file_type": "pdf",
                            "page_number": page_num,
                            "total_pages": total_pages,
                        }

                        doc = Document(content=text, metadata=metadata)
                        documents.append(doc)
                        partial_results.append(doc)

                    except Exception as page_error:
                        # Page extraction failed - raise with partial results
                        raise DocumentProcessingError(
                            f"Failed to extract page {page_num} from {file_path}: {page_error}",
                            file_path=file_path,
                            error_type=type(page_error).__name__,
                            original_error=page_error,
                            partial_results=partial_results,
                        )

                return documents

        except DocumentProcessingError:
            # Re-raise our own exceptions
            raise
        except Exception as e:
            # Catch PDF parsing errors
            raise DocumentProcessingError(
                f"Failed to load PDF {file_path}: {e}",
                file_path=file_path,
                error_type=type(e).__name__,
                original_error=e,
            )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/loaders/test_pdf_loader.py -v`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add vibe_rag/loaders/pdf.py tests/unit/loaders/test_pdf_loader.py
git commit -m "feat: implement PDFLoader with page-by-page extraction

- Add PDFLoader using PyPDF2
- Extract text from each page separately
- Include page metadata (page_number, total_pages)
- Support partial results when page extraction fails
- Raise DocumentProcessingError with context
- Add comprehensive tests with mocking"
```

---

## Task 9: Implement MarkdownLoader

**Files:**
- Create: `vibe_rag/loaders/markdown.py`
- Create: `tests/unit/loaders/test_markdown_loader.py`

**Step 1: Write failing tests for MarkdownLoader**

Create `tests/unit/loaders/test_markdown_loader.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/loaders/test_markdown_loader.py::test_markdown_loader_inheritance -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.loaders.markdown'"

**Step 3: Implement MarkdownLoader**

Create `vibe_rag/loaders/markdown.py`:

```python
"""Markdown file loader."""

import re
from pathlib import Path

from vibe_rag.loaders.base import BaseLoader
from vibe_rag.models import Document
from vibe_rag.utils.errors import DocumentProcessingError


class MarkdownLoader(BaseLoader):
    """Load Markdown files with structure preservation.

    Extracts headers and preserves markdown structure in metadata.
    """

    async def load(self, file_path: str) -> list[Document]:
        """Load markdown file with header extraction.

        Args:
            file_path: Path to markdown file

        Returns:
            List containing single Document with markdown content and headers

        Raises:
            DocumentProcessingError: If file not found or reading fails
        """
        path = Path(file_path)

        # Validate file exists and is a file
        if not path.exists():
            raise DocumentProcessingError(
                f"File not found: {file_path}",
                file_path=file_path,
                error_type="FileNotFoundError",
            )

        if not path.is_file():
            raise DocumentProcessingError(
                f"Not a file: {file_path}",
                file_path=file_path,
                error_type="IsADirectoryError",
            )

        try:
            # Read markdown content
            content = path.read_text(encoding="utf-8")

            # Extract headers (lines starting with #)
            headers = self._extract_headers(content)

            # Create document with metadata
            metadata = {
                "source_file": file_path,
                "file_type": "markdown",
                "headers": headers,
            }

            return [Document(content=content, metadata=metadata)]

        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to load markdown {file_path}: {e}",
                file_path=file_path,
                error_type=type(e).__name__,
                original_error=e,
            )

    def _extract_headers(self, content: str) -> list[str]:
        """Extract markdown headers from content.

        Args:
            content: Markdown text

        Returns:
            List of header lines (e.g., ["# Title", "## Section"])
        """
        # Match lines starting with one or more # followed by space
        header_pattern = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)
        headers = header_pattern.findall(content)
        return headers
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/loaders/test_markdown_loader.py -v`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add vibe_rag/loaders/markdown.py tests/unit/loaders/test_markdown_loader.py
git commit -m "feat: implement MarkdownLoader with header extraction

- Add MarkdownLoader for markdown files
- Extract headers using regex pattern
- Preserve structure metadata
- Raise DocumentProcessingError with context
- Add comprehensive tests with mocking"
```

---

## Task 10: Export Loaders in Package

**Files:**
- Modify: `vibe_rag/loaders/__init__.py`
- Modify: `vibe_rag/__init__.py`

**Step 1: Update loaders package exports**

Edit `vibe_rag/loaders/__init__.py`:

```python
"""Document loaders for various file formats."""

from vibe_rag.loaders.base import BaseLoader
from vibe_rag.loaders.text import TextLoader
from vibe_rag.loaders.pdf import PDFLoader
from vibe_rag.loaders.markdown import MarkdownLoader

__all__ = ["BaseLoader", "TextLoader", "PDFLoader", "MarkdownLoader"]
```

**Step 2: Update main package exports**

Edit `vibe_rag/__init__.py` to add:

```python
from vibe_rag.loaders import TextLoader, PDFLoader, MarkdownLoader
```

And add to `__all__`:

```python
"TextLoader",
"PDFLoader",
"MarkdownLoader",
```

**Step 3: Verify imports work**

Run: `python -c "from vibe_rag import TextLoader, PDFLoader, MarkdownLoader; print('Import success')"`
Expected: "Import success"

**Step 4: Commit**

```bash
git add vibe_rag/loaders/__init__.py vibe_rag/__init__.py
git commit -m "feat: export loaders in package

- Add loaders to package exports
- Export TextLoader, PDFLoader, MarkdownLoader from main package
- Enable direct imports from vibe_rag"
```

---

## Task 11: Add PyPDF2 Dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add PyPDF2 to dependencies**

Edit `pyproject.toml` dependencies section to add:

```toml
dependencies = [
    # ... existing dependencies
    "PyPDF2>=3.0.0",
]
```

**Step 2: Install dependencies**

Run: `pip install -e .`
Expected: PyPDF2 installed successfully

**Step 3: Verify import**

Run: `python -c "import PyPDF2; print('PyPDF2 version:', PyPDF2.__version__)"`
Expected: Version printed (e.g., "PyPDF2 version: 3.0.1")

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add PyPDF2 for PDF loading

- Add PyPDF2>=3.0.0 to dependencies
- Required for PDFLoader functionality"
```

---

## Task 12: Run Full Test Suite and Check Coverage

**Files:**
- No files modified (verification step)

**Step 1: Run all document processing tests**

Run: `pytest tests/unit/transformers/ tests/unit/loaders/ -v`
Expected: All tests PASS

**Step 2: Check test coverage**

Run: `pytest tests/unit/transformers/ tests/unit/loaders/ --cov=vibe_rag.transformers --cov=vibe_rag.loaders --cov-report=term-missing`
Expected: Coverage >= 80% for both modules

**Step 3: Run full test suite**

Run: `pytest`
Expected: All tests PASS (including existing tests)

**Step 4: Check linting**

Run: `ruff check vibe_rag/transformers vibe_rag/loaders`
Expected: No errors

Run: `black --check vibe_rag/transformers vibe_rag/loaders`
Expected: No changes needed

**Step 5: If linting fails, fix issues**

Run: `black vibe_rag/transformers vibe_rag/loaders`
Run: `ruff check --fix vibe_rag/transformers vibe_rag/loaders`

If changes made, commit:

```bash
git add vibe_rag/transformers vibe_rag/loaders
git commit -m "style: format code with black and ruff

- Apply black formatting
- Fix ruff linting issues"
```

---

## Task 13: Create Usage Examples in Documentation

**Files:**
- Create: `docs/examples/document_processing.md`

**Step 1: Create examples documentation**

Create `docs/examples/document_processing.md`:

```markdown
# Document Processing Examples

This guide shows how to use vibe-rag's document processing capabilities.

## Basic Text Loading and Chunking

```python
from vibe_rag import TextLoader, DocumentProcessor

# Load a text file
loader = TextLoader()
documents = await loader.load("knowledge_base/policy.txt")

# Chunk the document
processor = DocumentProcessor(
    strategy="recursive",  # Smart splitting
    chunk_size=512,
    chunk_overlap=50
)

chunks = await processor.process(
    content=documents[0].content,
    metadata=documents[0].metadata
)

# Inspect chunks
for chunk in chunks:
    print(f"Chunk {chunk.metadata['chunk_index']}/{chunk.metadata['chunk_total']}")
    print(f"Size: {chunk.metadata['chunk_size']} characters")
    print(f"Content: {chunk.content[:100]}...")
```

## PDF Loading with Page Metadata

```python
from vibe_rag import PDFLoader, DocumentProcessor

# Load PDF (one document per page)
loader = PDFLoader()
pages = await loader.load("reports/annual_report.pdf")

# Process each page
processor = DocumentProcessor(strategy="recursive", chunk_size=256)

all_chunks = []
for page in pages:
    chunks = await processor.process(page.content, page.metadata)
    all_chunks.extend(chunks)

# Each chunk knows which page it came from
for chunk in all_chunks:
    print(f"Page {chunk.metadata['page_number']}, Chunk {chunk.metadata['chunk_index']}")
```

## Markdown with Header Preservation

```python
from vibe_rag import MarkdownLoader, DocumentProcessor

# Load markdown
loader = MarkdownLoader()
documents = await loader.load("docs/README.md")

# Inspect headers
print("Document structure:")
for header in documents[0].metadata["headers"]:
    print(f"  {header}")

# Chunk with small size for granular sections
processor = DocumentProcessor(strategy="recursive", chunk_size=200)
chunks = await processor.process(
    content=documents[0].content,
    metadata=documents[0].metadata
)
```

## Custom Chunking Strategy

```python
from langchain.text_splitter import TokenTextSplitter
from vibe_rag import DocumentProcessor, TextLoader

# Use token-based splitting instead of character-based
token_splitter = TokenTextSplitter(
    chunk_size=100,  # tokens, not characters
    chunk_overlap=10
)

processor = DocumentProcessor(text_splitter=token_splitter)

loader = TextLoader()
documents = await loader.load("data.txt")
chunks = await processor.process(documents[0].content, documents[0].metadata)
```

## Registering Custom Strategy

```python
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from vibe_rag import DocumentProcessor

# Register once
DocumentProcessor.register_strategy(
    "sentence_transformer",
    SentenceTransformersTokenTextSplitter
)

# Use everywhere
processor = DocumentProcessor(
    strategy="sentence_transformer",
    chunk_size=256
)
```

## Error Handling with Partial Results

```python
from vibe_rag import PDFLoader
from vibe_rag.utils.errors import DocumentProcessingError

loader = PDFLoader()

try:
    documents = await loader.load("large_scan.pdf")
except DocumentProcessingError as e:
    print(f"Error: {e}")
    print(f"File: {e.file_path}")
    print(f"Error type: {e.error_type}")

    # Use partial results if available
    if e.partial_results:
        print(f"Successfully loaded {len(e.partial_results)} pages")
        documents = e.partial_results
    else:
        raise  # No partial results, re-raise
```

## Batch Processing Multiple Files

```python
import asyncio
from pathlib import Path
from vibe_rag import TextLoader, DocumentProcessor

async def process_directory(directory: str):
    loader = TextLoader()
    processor = DocumentProcessor(strategy="recursive", chunk_size=512)

    all_chunks = []

    for file_path in Path(directory).glob("*.txt"):
        try:
            # Load file
            documents = await loader.load(str(file_path))

            # Chunk
            for doc in documents:
                chunks = await processor.process(doc.content, doc.metadata)
                all_chunks.extend(chunks)

        except DocumentProcessingError as e:
            print(f"Failed to process {file_path}: {e}")
            continue

    return all_chunks

# Usage
chunks = await process_directory("knowledge_base/")
print(f"Processed {len(chunks)} chunks from directory")
```

## Integration with RAG Pipeline

```python
from vibe_rag import (
    TextLoader,
    DocumentProcessor,
    GeminiProvider,
    PostgresVectorStore
)

# Load and chunk documents
loader = TextLoader()
processor = DocumentProcessor(strategy="recursive", chunk_size=512)

documents = await loader.load("knowledge.txt")
chunks = await processor.process(documents[0].content, documents[0].metadata)

# Generate embeddings and store
provider = GeminiProvider(api_key="...")
embeddings = await provider.embed([chunk.content for chunk in chunks])

store = PostgresVectorStore(connection_string="...")
await store.add_documents(
    documents=chunks,
    collection_name="knowledge_base",
    embeddings=embeddings
)
```
```

**Step 2: Commit documentation**

```bash
git add docs/examples/document_processing.md
git commit -m "docs: add document processing usage examples

- Add comprehensive usage examples
- Cover all loaders (text, PDF, markdown)
- Show custom strategies and error handling
- Include batch processing and RAG integration"
```

---

## Task 14: Final Verification

**Files:**
- No files modified (final verification)

**Step 1: Run complete test suite**

Run: `pytest -v`
Expected: All tests PASS

**Step 2: Verify coverage targets**

Run: `pytest --cov=vibe_rag --cov-report=term-missing`
Expected:
- `vibe_rag/transformers/`: >= 80%
- `vibe_rag/loaders/`: >= 80%
- `vibe_rag/utils/errors.py`: >= 85% (overall utilities)

**Step 3: Verify all acceptance criteria**

Check against Phase 1.5 requirements:
- ✅ DocumentProcessor chunks text correctly with fixed and recursive strategies
- ✅ Chunk size and overlap are configurable
- ✅ Custom text splitters can be injected
- ✅ Strategy registry allows custom strategies
- ✅ TextLoader loads plain text files with encoding detection
- ✅ PDFLoader extracts text from PDFs with page metadata
- ✅ MarkdownLoader preserves structure
- ✅ Rich metadata is added to every chunk
- ✅ DocumentProcessingError provides context and partial results
- ✅ Tests verify all functionality with >= 80% coverage

**Step 4: Run type checking**

Run: `mypy vibe_rag/transformers vibe_rag/loaders`
Expected: No type errors (or only acceptable warnings)

**Step 5: Verify imports from main package**

Run:
```python
python -c "
from vibe_rag import (
    DocumentProcessor,
    TextLoader,
    PDFLoader,
    MarkdownLoader,
    DocumentProcessingError
)
print('All imports successful')
"
```
Expected: "All imports successful"

---

## Summary

**Completed Tasks:**
1. ✅ Add DocumentProcessingError exception
2. ✅ Implement DocumentProcessor core (init + process)
3. ✅ Add strategy registry to DocumentProcessor
4. ✅ Export DocumentProcessor in package
5. ✅ Implement BaseLoader interface
6. ✅ Implement TextLoader with encoding detection
7. ✅ Implement PDFLoader with page extraction
8. ✅ Implement MarkdownLoader with header extraction
9. ✅ Export loaders in package
10. ✅ Add PyPDF2 dependency
11. ✅ Run full test suite and check coverage
12. ✅ Create usage documentation
13. ✅ Final verification

**Files Created:**
- `vibe_rag/transformers/document.py`
- `vibe_rag/loaders/base.py`
- `vibe_rag/loaders/text.py`
- `vibe_rag/loaders/pdf.py`
- `vibe_rag/loaders/markdown.py`
- `tests/unit/transformers/test_document_processor.py`
- `tests/unit/loaders/test_base_loader.py`
- `tests/unit/loaders/test_text_loader.py`
- `tests/unit/loaders/test_pdf_loader.py`
- `tests/unit/loaders/test_markdown_loader.py`
- `docs/examples/document_processing.md`

**Files Modified:**
- `vibe_rag/utils/errors.py` (added DocumentProcessingError)
- `vibe_rag/transformers/__init__.py`
- `vibe_rag/loaders/__init__.py`
- `vibe_rag/__init__.py`
- `pyproject.toml` (added PyPDF2)
- `tests/unit/test_errors.py`

**Key Features:**
- Flexible chunking with strategy registry
- Rich metadata for traceability
- Error handling with partial results
- Three file format loaders
- Comprehensive test coverage (>80%)
- Production-ready with async support

**Next Steps:**
- Phase 1.6: RAG Engine integration
- Integration tests with real files (optional)
- Additional loaders (DOCX, HTML, CSV) in Phase 2+
