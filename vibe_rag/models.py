"""Core data models for vibe-rag."""

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    """Document model representing a piece of text with metadata.

    Used throughout the RAG pipeline to represent documents during
    ingestion, retrieval, and generation.

    Attributes:
        id: Unique identifier (auto-generated UUID if not provided)
        content: The text content of the document
        metadata: Optional metadata (source, page number, etc.)
        score: Optional similarity score (set during retrieval)
    """

    model_config = ConfigDict(frozen=False)

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float | None = None
