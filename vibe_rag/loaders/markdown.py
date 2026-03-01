"""Markdown file loader."""

import re
from pathlib import Path

from vibe_rag.loaders.base import BaseLoader
from vibe_rag.models import Document
from vibe_rag.utils.errors import DocumentProcessingError


class MarkdownLoader(BaseLoader):
    """Load Markdown files with structure preservation.

    Extracts headers and preserves markdown structure in metadata.
    """

    async def load(self, file_path: str) -> list[Document]:
        """Load markdown file with header extraction.

        Args:
            file_path: Path to markdown file

        Returns:
            List containing single Document with markdown content and headers

        Raises:
            DocumentProcessingError: If file not found or reading fails
        """
        path = Path(file_path)

        # Validate file exists and is a file
        if not path.exists():
            raise DocumentProcessingError(
                f"File not found: {file_path}",
                file_path=file_path,
                error_type="FileNotFoundError",
            )

        if not path.is_file():
            raise DocumentProcessingError(
                f"Not a file: {file_path}",
                file_path=file_path,
                error_type="IsADirectoryError",
            )

        try:
            # Read markdown content
            content = path.read_text(encoding="utf-8")

            # Extract headers (lines starting with #)
            headers = self._extract_headers(content)

            # Create document with metadata
            metadata = {
                "source_file": file_path,
                "file_type": "markdown",
                "headers": headers,
            }

            return [Document(content=content, metadata=metadata)]

        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to load markdown {file_path}: {e}",
                file_path=file_path,
                error_type=type(e).__name__,
                original_error=e,
            )

    def _extract_headers(self, content: str) -> list[str]:
        """Extract markdown headers from content.

        Args:
            content: Markdown text

        Returns:
            List of header lines (e.g., ["# Title", "## Section"])
        """
        # Match lines starting with one or more # followed by space
        header_pattern = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)
        headers = header_pattern.findall(content)
        return headers
