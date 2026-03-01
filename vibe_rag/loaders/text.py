"""Text file loader."""

from pathlib import Path

from vibe_rag.loaders.base import BaseLoader
from vibe_rag.models import Document
from vibe_rag.utils.errors import DocumentProcessingError


class TextLoader(BaseLoader):
    """Load plain text files with encoding detection.

    Attempts to detect file encoding using common encodings:
    utf-8, latin-1, cp1252
    """

    ENCODINGS = ["utf-8", "latin-1", "cp1252"]

    async def load(self, file_path: str) -> list[Document]:
        """Load text file with encoding detection.

        Args:
            file_path: Path to text file

        Returns:
            List containing single Document with file content

        Raises:
            DocumentProcessingError: If file not found, not a file, or encoding fails
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

        # Try to read with different encodings
        content = None
        encoding_used = None

        for encoding in self.ENCODINGS:
            try:
                content = path.read_text(encoding=encoding)
                encoding_used = encoding
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise DocumentProcessingError(
                f"Failed to decode file with any encoding: {self.ENCODINGS}",
                file_path=file_path,
                error_type="EncodingError",
            )

        # Create document with metadata
        metadata = {
            "source_file": file_path,
            "file_type": "text",
            "encoding": encoding_used,
        }

        return [Document(content=content, metadata=metadata)]
