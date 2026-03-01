"""
vibe-rag: Production-grade modular RAG framework.

A batteries-included but removable RAG framework with pluggable components.
"""

from vibe_rag.models import Document
from vibe_rag.utils.errors import (
    ConfigurationError,
    EmbeddingError,
    LLMProviderError,
    RAGException,
    RetrievalError,
    StorageError,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Document",
    "RAGException",
    "EmbeddingError",
    "RetrievalError",
    "LLMProviderError",
    "StorageError",
    "ConfigurationError",
]
