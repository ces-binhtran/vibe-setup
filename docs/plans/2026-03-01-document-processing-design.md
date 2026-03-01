# Document Processing Design

**Date:** 2026-03-01
**Project:** vibe-rag
**Version:** 1.0
**Status:** Approved
**Phase:** 1.5 - Document Processing

## Executive Summary

This document outlines the design for document loading and chunking capabilities in vibe-rag. The implementation enables RAG workflows to break documents into semantically meaningful chunks that fit in context windows while maintaining rich metadata for traceability and future visualization/debugging systems.

**Key Design Principles:**
- **Leverage LangChain**: Thin wrappers around battle-tested components
- **Extensibility First**: Support custom chunking strategies via direct injection or registry
- **Rich Metadata**: Comprehensive traceability for debugging and visualization
- **Error Context**: Detailed exceptions with partial results when possible
- **Production-Ready**: Async-friendly, well-tested, follows vibe-rag patterns

---

## 1. Architecture Overview

### 1.1 Component Structure

Three main components implement document processing:

1. **DocumentProcessor** (`vibe_rag/transformers/document.py`)
   - Orchestrates document chunking with flexible strategy system
   - Primary interface: Accept any LangChain text splitter instance
   - Convenience layer: Built-in strategies ("fixed", "recursive") via registry
   - Enriches chunks with metadata for traceability
   - Configurable chunk size, overlap, and strategy

2. **Document Loaders** (`vibe_rag/loaders/`)
   - `TextLoader` - Plain text files with encoding detection
   - `PDFLoader` - PDF extraction using LangChain's PyPDFLoader
   - `MarkdownLoader` - Markdown files preserving structure
   - Each returns list of `Document` objects with metadata

3. **Error Handling**
   - New exception: `DocumentProcessingError` in `vibe_rag/utils/errors.py`
   - Rich context: file path, error type, original exception, partial results
   - Supports debugging and visualization systems

### 1.2 Data Flow

```
File Path → Loader → Raw Document(s) → DocumentProcessor → Chunked Documents
                     (with metadata)                         (with enriched metadata)
```

### 1.3 Extensibility Design

The system supports three levels of customization:

**Maximum Flexibility** - Users provide their own splitters:
```python
from langchain.text_splitter import CustomSplitter
processor = DocumentProcessor(text_splitter=CustomSplitter(...))
```

**Convenience** - Built-in strategies for common cases:
```python
processor = DocumentProcessor(strategy="recursive", chunk_size=512)
```

**Advanced** - Custom strategies can be registered:
```python
DocumentProcessor.register_strategy("semantic", SemanticSplitter)
processor = DocumentProcessor(strategy="semantic")
```

---

## 2. DocumentProcessor Design

### 2.1 Core API

```python
class DocumentProcessor:
    """Handles document chunking with flexible strategy system.

    Supports three usage modes:
    1. Direct injection: Pass any LangChain text splitter
    2. Built-in strategies: Use "fixed" or "recursive"
    3. Custom registry: Register and use custom strategies
    """

    def __init__(
        self,
        text_splitter: Optional[TextSplitter] = None,  # Custom splitter (primary)
        strategy: str = "recursive",                    # Built-in strategy (convenience)
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        """Initialize DocumentProcessor.

        Args:
            text_splitter: Custom LangChain text splitter (overrides strategy)
            strategy: Built-in strategy name ("fixed", "recursive")
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks for context preservation
        """

    async def process(
        self,
        content: str,
        metadata: Optional[dict] = None
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

    @classmethod
    def register_strategy(cls, name: str, splitter_class: type) -> None:
        """Register custom chunking strategy.

        Args:
            name: Strategy identifier
            splitter_class: LangChain TextSplitter class
        """
```

### 2.2 Metadata Enrichment

Each chunk receives two types of metadata:

**Source Metadata** (copied from original document):
- `source_file`: Original file path
- `file_type`: Document type (text, pdf, markdown)
- `page_number`: Page number (for PDFs)
- `total_pages`: Total pages (for PDFs)
- `encoding`: File encoding (for text files)
- Any custom metadata passed to `process()`

**Chunk Metadata** (added by DocumentProcessor):
- `chunk_index`: Position in sequence (0-based)
- `chunk_total`: Total number of chunks from this document
- `chunk_size`: Actual size of this chunk in characters
- `chunking_strategy`: Strategy used ("fixed", "recursive", or custom class name)
- `parent_doc_id`: Original document ID for traceability
- `chunk_overlap`: Configured overlap size

### 2.3 Built-in Strategies

**"fixed"**: Character-based splitting
- Uses LangChain's `CharacterTextSplitter`
- Splits on fixed character count
- Simple but may split mid-sentence

**"recursive"**: Intelligent splitting (default)
- Uses LangChain's `RecursiveCharacterTextSplitter`
- Tries to split on: paragraphs → sentences → words → characters
- Preserves semantic meaning
- Recommended for production use

### 2.4 Strategy Registry

The registry pattern enables custom strategies without modifying vibe-rag code:

```python
# Internal registry (class variable)
_strategies: dict[str, type] = {
    "fixed": CharacterTextSplitter,
    "recursive": RecursiveCharacterTextSplitter,
}

# Users can extend
from my_module import SemanticChunkingSplitter
DocumentProcessor.register_strategy("semantic", SemanticChunkingSplitter)

# Then use it
processor = DocumentProcessor(strategy="semantic")
```

---

## 3. Document Loaders Design

### 3.1 Base Interface

All loaders implement a common interface for consistency:

```python
from abc import ABC, abstractmethod

class BaseLoader(ABC):
    """Base interface for document loaders."""

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

### 3.2 TextLoader

**Purpose**: Load plain text files with encoding detection

**Implementation**: Wraps LangChain's `TextLoader`

**Features**:
- Automatic encoding detection (utf-8, latin-1, cp1252)
- Fallback to binary read if all encodings fail
- Single document output

**Metadata**:
- `source_file`: File path
- `file_type`: "text"
- `encoding`: Detected encoding (e.g., "utf-8")

### 3.3 PDFLoader

**Purpose**: Extract text from PDF files page-by-page

**Implementation**: Wraps LangChain's `PyPDFLoader`

**Features**:
- Page-by-page extraction
- Multiple documents output (one per page)
- Handles multi-page PDFs gracefully

**Metadata**:
- `source_file`: File path
- `file_type`: "pdf"
- `page_number`: Current page (1-based)
- `total_pages`: Total pages in PDF

**Partial Results**: If pages 1-5 succeed but page 6 fails, returns 5 documents + raises error with partial results

### 3.4 MarkdownLoader

**Purpose**: Load Markdown files preserving structure

**Implementation**: Wraps LangChain's `UnstructuredMarkdownLoader`

**Features**:
- Preserves headers, lists, code blocks
- Structure-aware parsing
- Single document output with structure metadata

**Metadata**:
- `source_file`: File path
- `file_type`: "markdown"
- `headers`: Section hierarchy (e.g., ["# Title", "## Section"])

---

## 4. Error Handling Design

### 4.1 DocumentProcessingError

New exception type added to `vibe_rag/utils/errors.py`:

```python
class DocumentProcessingError(RAGException):
    """Document processing failed (loading or chunking).

    Provides rich context for debugging and visualization systems.
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        error_type: Optional[str] = None,
        original_error: Optional[Exception] = None,
        partial_results: Optional[list[Document]] = None,
    ):
        """Initialize error with context.

        Args:
            message: Human-readable error description
            file_path: Path to file that failed
            error_type: Error category (FileNotFoundError, CorruptPDFError, etc.)
            original_error: Underlying exception
            partial_results: Any successfully processed chunks/pages
        """
        super().__init__(message)
        self.file_path = file_path
        self.error_type = error_type
        self.original_error = original_error
        self.partial_results = partial_results
```

### 4.2 Error Categories

**File Access Errors**:
- `FileNotFoundError`: File doesn't exist
- `PermissionError`: No read permission
- `IsADirectoryError`: Path is directory, not file

**Processing Errors**:
- `EncodingError`: Text file encoding issues
- `CorruptPDFError`: PDF file is corrupt or unreadable
- `ParseError`: Markdown/structure parsing failed

**Chunking Errors**:
- `ChunkingError`: Text splitting failed
- `ConfigurationError`: Invalid chunk size/overlap

### 4.3 Error Context for Visualization

The rich exception attributes support future debugging/visualization:

```python
try:
    documents = await loader.load("large_document.pdf")
except DocumentProcessingError as e:
    # Visualization system can display:
    print(f"File: {e.file_path}")              # Which file failed
    print(f"Error: {e.error_type}")            # Category for filtering
    print(f"Details: {e.original_error}")      # Full stack trace

    if e.partial_results:
        # Show partial progress: "Processed 45/50 pages"
        print(f"Partial: {len(e.partial_results)} documents succeeded")
        # User can choose to continue with partial results
```

---

## 5. Testing Strategy

### 5.1 Test Coverage Targets

Following vibe-rag standards:
- **DocumentProcessor**: 80%+ (pipeline component)
- **Loaders**: 80%+ (transformers)
- **Error handling**: 85%+ (utilities)

### 5.2 Unit Tests

**DocumentProcessor** (`tests/unit/transformers/test_document_processor.py`):

Test cases:
- Initialization with built-in strategies ("fixed", "recursive")
- Initialization with custom text splitter
- Metadata enrichment (all chunk metadata fields)
- Strategy registry (register and use custom strategies)
- Error handling (invalid strategy, chunking failures)

Mocking:
- Mock LangChain text splitters (no actual text splitting)
- Mock splitter returns predictable chunks for validation

**TextLoader** (`tests/unit/loaders/test_text_loader.py`):

Test cases:
- Successful loading with valid text file
- Encoding detection (utf-8, latin-1)
- File not found error
- Permission error
- Empty file handling

Mocking:
- Mock file system (no actual file I/O)
- Mock LangChain TextLoader

**PDFLoader** (`tests/unit/loaders/test_pdf_loader.py`):

Test cases:
- Successful loading with valid PDF
- Multi-page PDFs (verify page metadata)
- Corrupt PDF error
- Partial results on page failure
- Empty PDF handling

Mocking:
- Mock LangChain PyPDFLoader
- Mock page extraction

**MarkdownLoader** (`tests/unit/loaders/test_markdown_loader.py`):

Test cases:
- Successful loading with valid markdown
- Header hierarchy extraction
- Code block preservation
- Malformed markdown handling

Mocking:
- Mock LangChain UnstructuredMarkdownLoader
- Mock structure parsing

### 5.3 Integration Tests (Optional for Phase 1.5)

Can be deferred to later phases:
- Test with real files (sample PDFs, markdown, text)
- Test end-to-end: load → chunk → verify output
- Located in `tests/integration/`

### 5.4 Test Fixtures

Create in `tests/fixtures/`:
- `sample.txt`: Simple text file (UTF-8)
- `sample_latin1.txt`: Latin-1 encoded file
- `sample.pdf`: Small 3-page PDF
- `sample.md`: Markdown with headers and code blocks
- `corrupt.pdf`: Intentionally corrupted PDF for error testing

---

## 6. Dependencies

### 6.1 New Dependencies

None required - all dependencies already in `pyproject.toml`:
- `langchain>=1.0.0` (provides text splitters and loaders)
- `langchain-core>=0.3.0` (base classes)

Optional for PDF support:
- `pypdf` (LangChain's PyPDFLoader dependency)

Optional for Markdown support:
- `unstructured` (LangChain's MarkdownLoader dependency)

### 6.2 Dependency Notes

**LangChain Text Splitters**:
- `CharacterTextSplitter`: Simple character-based splitting
- `RecursiveCharacterTextSplitter`: Intelligent recursive splitting

**LangChain Loaders**:
- `TextLoader`: Text file loading with encoding detection
- `PyPDFLoader`: PDF extraction (requires pypdf)
- `UnstructuredMarkdownLoader`: Markdown parsing (requires unstructured)

---

## 7. Usage Examples

### 7.1 Basic Usage

```python
from vibe_rag.loaders import TextLoader, PDFLoader
from vibe_rag.transformers import DocumentProcessor

# Load document
loader = TextLoader()
documents = await loader.load("knowledge_base/policy.txt")

# Chunk with default recursive strategy
processor = DocumentProcessor(chunk_size=512, chunk_overlap=50)
chunks = await processor.process(
    content=documents[0].content,
    metadata=documents[0].metadata
)

# Each chunk has rich metadata
for chunk in chunks:
    print(f"Chunk {chunk.metadata['chunk_index']}/{chunk.metadata['chunk_total']}")
    print(f"Strategy: {chunk.metadata['chunking_strategy']}")
    print(f"Source: {chunk.metadata['source_file']}")
```

### 7.2 Custom Strategy via Injection

```python
from langchain.text_splitter import TokenTextSplitter

# Bring your own splitter
custom_splitter = TokenTextSplitter(
    chunk_size=100,
    chunk_overlap=10
)

processor = DocumentProcessor(text_splitter=custom_splitter)
chunks = await processor.process(content, metadata)
```

### 7.3 Custom Strategy via Registry

```python
from my_rag_extensions import SemanticChunkingSplitter

# Register once
DocumentProcessor.register_strategy("semantic", SemanticChunkingSplitter)

# Use everywhere
processor = DocumentProcessor(strategy="semantic")
chunks = await processor.process(content, metadata)
```

### 7.4 Error Handling with Partial Results

```python
from vibe_rag.loaders import PDFLoader
from vibe_rag.utils.errors import DocumentProcessingError

loader = PDFLoader()

try:
    documents = await loader.load("large_report.pdf")
except DocumentProcessingError as e:
    logger.error(f"Failed to load {e.file_path}: {e.error_type}")

    # Use partial results if available
    if e.partial_results:
        logger.info(f"Using {len(e.partial_results)} successfully loaded pages")
        documents = e.partial_results
    else:
        raise  # No partial results, re-raise
```

---

## 8. Implementation Phases

### Phase 1: Core Infrastructure
1. Add `DocumentProcessingError` to `vibe_rag/utils/errors.py`
2. Implement `DocumentProcessor` with strategy registry
3. Write tests for `DocumentProcessor`

### Phase 2: Loaders
1. Implement `BaseLoader` interface
2. Implement `TextLoader` with encoding detection
3. Implement `PDFLoader` with partial results
4. Implement `MarkdownLoader` with structure preservation
5. Write tests for each loader

### Phase 3: Integration
1. Export classes in package `__init__.py` files
2. Add usage examples to documentation
3. Integration tests (optional)

---

## 9. Future Enhancements

### Semantic Chunking (Phase 2+)
- Embedding-based chunking
- Split at semantic boundaries
- Requires LLM provider integration

### Additional Loaders (Phase 2+)
- `DocxLoader` - Microsoft Word documents
- `HTMLLoader` - Web pages
- `CSVLoader` - Tabular data
- `JSONLoader` - Structured data

### Advanced Features (Phase 3+)
- Async batch processing
- Streaming for large documents
- Chunking strategy auto-selection based on content
- Chunk quality metrics (semantic coherence score)

---

## 10. Design Decisions

### Why Thin Wrappers Around LangChain?

**Decision**: Use LangChain components rather than custom implementations

**Rationale**:
- Battle-tested in production
- Active maintenance and bug fixes
- Comprehensive test coverage
- We already depend on LangChain
- Focus on value-add: metadata enrichment, error handling, integration

**Trade-offs**:
- Coupled to LangChain (acceptable - it's a core dependency)
- Less control over algorithm details (acceptable - can extend via registry)

### Why Strategy Registry Pattern?

**Decision**: Support both direct injection and named strategies

**Rationale**:
- Maximum flexibility (bring your own splitter)
- Convenience for common cases (built-in strategies)
- Extensible without modifying vibe-rag
- Follows "batteries included but removable" philosophy

**Trade-offs**:
- Slightly more complex API (two ways to configure)
- Need to maintain registry (small overhead)

### Why Rich Error Context?

**Decision**: Capture file path, error type, original exception, and partial results

**Rationale**:
- Supports future visualization/debugging systems
- Enables informed error recovery decisions
- Provides traceability for production debugging
- Aligns with vibe-rag quality standards

**Trade-offs**:
- More verbose exception handling code
- Need to carefully preserve partial results (complexity)

---

## 11. Success Criteria

Phase 1.5 is complete when:

- ✅ `DocumentProcessor` chunks text correctly with fixed and recursive strategies
- ✅ Chunk size and overlap are configurable
- ✅ Custom text splitters can be injected
- ✅ Strategy registry allows custom strategies
- ✅ `TextLoader` loads plain text files with encoding detection
- ✅ `PDFLoader` extracts text from PDFs with page metadata
- ✅ `MarkdownLoader` preserves structure
- ✅ Rich metadata is added to every chunk (chunk_index, chunk_total, strategy, etc.)
- ✅ `DocumentProcessingError` provides file path, error type, partial results
- ✅ Tests verify chunking strategies with 80%+ coverage
- ✅ Tests verify loaders with 80%+ coverage
- ✅ Tests verify error handling with 85%+ coverage

---

## 12. References

- **Main Design Doc**: `docs/plans/2026-02-28-rag-framework-design.md` (Section 8: Document Processing)
- **Implementation Plan**: `docs/plans/2026-02-28-vibe-rag-implementation.md` (Task 9)
- **LangChain Text Splitters**: https://python.langchain.com/docs/modules/data_connection/document_transformers/
- **LangChain Document Loaders**: https://python.langchain.com/docs/modules/data_connection/document_loaders/

---

**Document Status**: Approved for implementation
**Next Step**: Create implementation plan with vibe-rag TDD workflow
