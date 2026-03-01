"""Document processing and chunking."""

from typing import Optional
from uuid import uuid4

from langchain_text_splitters import (
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

    def process(self, content: str, metadata: Optional[dict] = None) -> list[Document]:
        """Process text into chunks with enriched metadata.

        Args:
            content: Text content to chunk
            metadata: Source metadata to copy to chunks

        Returns:
            List of Document objects with enriched metadata.
            Each chunk's metadata includes:
            - chunk_index: Position in chunk sequence (0-indexed)
            - chunk_total: Total number of chunks created
            - chunk_size: Actual character count of this chunk
            - chunking_strategy: Strategy used ("fixed", "recursive", "custom")
            - parent_doc_id: UUID linking chunks from same source document
            - chunk_overlap: Configured overlap size in characters
            - Plus any metadata from the original source document

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

    @classmethod
    def register_strategy(cls, name: str, splitter_class: type) -> None:
        """Register custom chunking strategy.

        Args:
            name: Strategy identifier
            splitter_class: TextSplitter class (or compatible)
        """
        cls._strategies[name] = splitter_class
