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
