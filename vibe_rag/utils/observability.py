"""Observability and metrics tracking for RAG operations."""

import time
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4


@dataclass
class RAGMetrics:
    """Metrics for a single RAG query operation.

    Tracks performance, costs, and metadata for observability.

    Attributes:
        query_id: Unique identifier for this query
        query: Original user query
        answer: Generated answer
        retrieval_time_ms: Time spent retrieving documents
        generation_time_ms: Time spent generating answer
        total_time_ms: Total end-to-end time
        documents_retrieved: Number of documents retrieved
        documents_used: Number of documents actually used in generation
        input_tokens: Estimated input tokens (query + context)
        output_tokens: Estimated output tokens (answer)
        metadata: Additional metadata (timestamps, component info, etc.)
    """

    query_id: str = field(default_factory=lambda: str(uuid4()))
    query: str = ""
    answer: str = ""
    retrieval_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    total_time_ms: float = 0.0
    documents_retrieved: int = 0
    documents_used: int = 0
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary.

        Returns:
            Dictionary representation of metrics
        """
        return {
            "query_id": self.query_id,
            "query": self.query,
            "answer": self.answer,
            "retrieval_time_ms": self.retrieval_time_ms,
            "generation_time_ms": self.generation_time_ms,
            "total_time_ms": self.total_time_ms,
            "documents_retrieved": self.documents_retrieved,
            "documents_used": self.documents_used,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "metadata": self.metadata,
        }

    def summarize(self) -> str:
        """Generate human-readable summary.

        Returns:
            Formatted summary string
        """
        return (
            f"Query {self.query_id}:\n"
            f"  Total time: {self.total_time_ms:.2f}ms\n"
            f"  Retrieval: {self.retrieval_time_ms:.2f}ms ({self.documents_retrieved} docs)\n"
            f"  Generation: {self.generation_time_ms:.2f}ms\n"
            f"  Tokens: {self.input_tokens or 'N/A'} in, {self.output_tokens or 'N/A'} out"
        )


class MetricsTracker:
    """Tracks and aggregates metrics across multiple queries.

    Provides statistics and insights for monitoring RAG performance.

    Example:
        tracker = MetricsTracker()
        metrics = tracker.create_metrics(query="What is RAG?")
        # ... perform query ...
        tracker.record(metrics)
        print(tracker.get_stats())
    """

    def __init__(self):
        """Initialize metrics tracker."""
        self._metrics: list[RAGMetrics] = []

    def create_metrics(self, query: str) -> RAGMetrics:
        """Create new metrics object for a query.

        Args:
            query: User query

        Returns:
            New RAGMetrics instance
        """
        metrics = RAGMetrics(query=query)
        metrics.metadata["created_at"] = time.time()
        return metrics

    def record(self, metrics: RAGMetrics) -> None:
        """Record completed metrics.

        Args:
            metrics: Completed metrics object
        """
        metrics.metadata["recorded_at"] = time.time()
        self._metrics.append(metrics)

    def get_all(self) -> list[RAGMetrics]:
        """Get all recorded metrics.

        Returns:
            List of all metrics
        """
        return self._metrics.copy()

    def get_stats(self) -> dict[str, Any]:
        """Calculate aggregate statistics.

        Returns:
            Dictionary with aggregate stats:
            - total_queries: Total number of queries
            - avg_total_time_ms: Average total time
            - avg_retrieval_time_ms: Average retrieval time
            - avg_generation_time_ms: Average generation time
            - avg_documents_retrieved: Average documents retrieved
            - total_input_tokens: Total input tokens (if tracked)
            - total_output_tokens: Total output tokens (if tracked)
        """
        if not self._metrics:
            return {
                "total_queries": 0,
                "avg_total_time_ms": 0.0,
                "avg_retrieval_time_ms": 0.0,
                "avg_generation_time_ms": 0.0,
                "avg_documents_retrieved": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
            }

        n = len(self._metrics)
        return {
            "total_queries": n,
            "avg_total_time_ms": sum(m.total_time_ms for m in self._metrics) / n,
            "avg_retrieval_time_ms": sum(m.retrieval_time_ms for m in self._metrics) / n,
            "avg_generation_time_ms": sum(m.generation_time_ms for m in self._metrics) / n,
            "avg_documents_retrieved": sum(m.documents_retrieved for m in self._metrics) / n,
            "total_input_tokens": sum(
                m.input_tokens for m in self._metrics if m.input_tokens is not None
            ),
            "total_output_tokens": sum(
                m.output_tokens for m in self._metrics if m.output_tokens is not None
            ),
        }

    def clear(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()
