"""Custom exceptions for vibe-rag."""


class RAGException(Exception):
    """Base exception for all RAG errors."""
    pass


class EmbeddingError(RAGException):
    """Embedding generation failed."""
    pass


class RetrievalError(RAGException):
    """Document retrieval failed."""
    pass


class LLMProviderError(RAGException):
    """LLM provider error (API error, timeout, etc.)."""
    pass


class StorageError(RAGException):
    """Storage backend error."""
    pass


class ConfigurationError(RAGException):
    """Configuration validation error."""
    pass


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
