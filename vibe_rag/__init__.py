"""
vibe-rag: Production-grade modular RAG framework.

A batteries-included but removable RAG framework with pluggable components.
"""

from vibe_rag.config.models import (
    ChunkingConfig,
    LLMConfig,
    PipelineConfig,
    RAGConfig,
    StorageConfig,
)
from vibe_rag.engine import RAGEngine
from vibe_rag.loaders import MarkdownLoader, PDFLoader, TextLoader
from vibe_rag.models import Document
from vibe_rag.modules.basic import BasicRAGModule
from vibe_rag.quick import QuickSetup
from vibe_rag.retrievers import VectorRetriever
from vibe_rag.transformers import DocumentProcessor
from vibe_rag.utils.errors import (
    ConfigurationError,
    DocumentProcessingError,
    EmbeddingError,
    LLMProviderError,
    RAGException,
    RetrievalError,
    StorageError,
)
from vibe_rag.utils.observability import MetricsTracker, RAGMetrics

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Document",
    "RAGEngine",
    "QuickSetup",
    "BasicRAGModule",
    "RAGConfig",
    "LLMConfig",
    "StorageConfig",
    "PipelineConfig",
    "ChunkingConfig",
    "RAGMetrics",
    "MetricsTracker",
    "VectorRetriever",
    "DocumentProcessor",
    "TextLoader",
    "PDFLoader",
    "MarkdownLoader",
    "RAGException",
    "EmbeddingError",
    "RetrievalError",
    "LLMProviderError",
    "StorageError",
    "ConfigurationError",
    "DocumentProcessingError",
]
