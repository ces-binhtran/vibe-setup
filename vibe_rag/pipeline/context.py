"""Pipeline context for tracking execution state."""

import time
from typing import Any

from vibe_rag.models import Document


class PipelineContext:
    """Rich context for pipeline execution with built-in observability.

    Tracks query, documents, answer, and metadata throughout pipeline execution.
    Provides audit trail for debugging and visualization.

    Attributes:
        query: The user's question or search query
        documents: Retrieved documents (populated by retriever components)
        answer: Generated answer (populated by generator components)
        metadata: Component execution metadata
        _trace: Execution trace with timestamps

    Example:
        >>> context = PipelineContext(query="What is RAG?")
        >>> context.add_component_metadata("VectorRetriever", {"top_k": 5})
        >>> print(context.to_dict())
    """

    def __init__(self, query: str):
        """Initialize context with user query.

        Args:
            query: The user's question or search query
        """
        self.query = query
        self.documents: list[Document] = []
        self.answer: str | None = None
        self.metadata: dict[str, Any] = {}
        self._trace: list[dict] = []

    def add_component_metadata(
        self,
        component_name: str,
        metadata: dict
    ) -> None:
        """Add metadata for a component execution.

        Automatically tracks component name, timestamp, and custom metadata.

        Args:
            component_name: Name of the component
            metadata: Component-specific metadata (timing, scores, etc.)
        """
        self.metadata[component_name] = metadata
        self._trace.append({
            "component": component_name,
            "timestamp": time.time(),
            **metadata
        })

    def to_dict(self) -> dict:
        """Export as dictionary for serialization.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "query": self.query,
            "documents": [d.model_dump() for d in self.documents],
            "answer": self.answer,
            "metadata": self.metadata,
            "trace": self._trace
        }
