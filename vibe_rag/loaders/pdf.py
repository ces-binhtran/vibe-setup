"""PDF file loader."""

from pathlib import Path
import PyPDF2

from vibe_rag.loaders.base import BaseLoader
from vibe_rag.models import Document
from vibe_rag.utils.errors import DocumentProcessingError


class PDFLoader(BaseLoader):
    """Load PDF files page-by-page.

    Extracts text from each page and returns a Document per page
    with page metadata.
    """

    async def load(self, file_path: str) -> list[Document]:
        """Load PDF file and extract text from all pages.

        Args:
            file_path: Path to PDF file

        Returns:
            List of Documents (one per page) with page metadata

        Raises:
            DocumentProcessingError: If file not found or PDF parsing fails
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
            # Open PDF
            with open(path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                total_pages = len(reader.pages)

                documents = []
                partial_results = []

                # Extract text from each page
                for page_num, page in enumerate(reader.pages, start=1):
                    try:
                        text = page.extract_text()

                        # Create document with page metadata
                        metadata = {
                            "source_file": file_path,
                            "file_type": "pdf",
                            "page_number": page_num,
                            "total_pages": total_pages,
                        }

                        doc = Document(content=text, metadata=metadata)
                        documents.append(doc)
                        partial_results.append(doc)

                    except Exception as page_error:
                        # Page extraction failed - raise with partial results
                        raise DocumentProcessingError(
                            f"Failed to extract page {page_num} from {file_path}: {page_error}",
                            file_path=file_path,
                            error_type=type(page_error).__name__,
                            original_error=page_error,
                            partial_results=partial_results,
                        )

                return documents

        except DocumentProcessingError:
            # Re-raise our own exceptions
            raise
        except Exception as e:
            # Catch PDF parsing errors
            raise DocumentProcessingError(
                f"Failed to load PDF {file_path}: {e}",
                file_path=file_path,
                error_type=type(e).__name__,
                original_error=e,
            )
