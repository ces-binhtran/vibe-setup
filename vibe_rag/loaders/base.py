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
