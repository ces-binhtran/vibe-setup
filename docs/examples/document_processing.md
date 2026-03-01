# Document Processing Examples

This guide shows how to use vibe-rag's document processing capabilities.

## Basic Text Loading and Chunking

```python
from vibe_rag import TextLoader, DocumentProcessor

# Load a text file
loader = TextLoader()
documents = await loader.load("knowledge_base/policy.txt")

# Chunk the document
processor = DocumentProcessor(
    strategy="recursive",  # Smart splitting
    chunk_size=512,
    chunk_overlap=50
)

chunks = await processor.process(
    content=documents[0].content,
    metadata=documents[0].metadata
)

# Inspect chunks
for chunk in chunks:
    print(f"Chunk {chunk.metadata['chunk_index']}/{chunk.metadata['chunk_total']}")
    print(f"Size: {chunk.metadata['chunk_size']} characters")
    print(f"Content: {chunk.content[:100]}...")
```

## PDF Loading with Page Metadata

```python
from vibe_rag import PDFLoader, DocumentProcessor

# Load PDF (one document per page)
loader = PDFLoader()
pages = await loader.load("reports/annual_report.pdf")

# Process each page
processor = DocumentProcessor(strategy="recursive", chunk_size=256)

all_chunks = []
for page in pages:
    chunks = await processor.process(page.content, page.metadata)
    all_chunks.extend(chunks)

# Each chunk knows which page it came from
for chunk in all_chunks:
    print(f"Page {chunk.metadata['page_number']}, Chunk {chunk.metadata['chunk_index']}")
```

## Markdown with Header Preservation

```python
from vibe_rag import MarkdownLoader, DocumentProcessor

# Load markdown
loader = MarkdownLoader()
documents = await loader.load("docs/README.md")

# Inspect headers
print("Document structure:")
for header in documents[0].metadata["headers"]:
    print(f"  {header}")

# Chunk with small size for granular sections
processor = DocumentProcessor(strategy="recursive", chunk_size=200)
chunks = await processor.process(
    content=documents[0].content,
    metadata=documents[0].metadata
)
```

## Custom Chunking Strategy

```python
from langchain.text_splitter import TokenTextSplitter
from vibe_rag import DocumentProcessor, TextLoader

# Use token-based splitting instead of character-based
token_splitter = TokenTextSplitter(
    chunk_size=100,  # tokens, not characters
    chunk_overlap=10
)

processor = DocumentProcessor(text_splitter=token_splitter)

loader = TextLoader()
documents = await loader.load("data.txt")
chunks = await processor.process(documents[0].content, documents[0].metadata)
```

## Registering Custom Strategy

```python
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from vibe_rag import DocumentProcessor

# Register once
DocumentProcessor.register_strategy(
    "sentence_transformer",
    SentenceTransformersTokenTextSplitter
)

# Use everywhere
processor = DocumentProcessor(
    strategy="sentence_transformer",
    chunk_size=256
)
```

## Error Handling with Partial Results

```python
from vibe_rag import PDFLoader
from vibe_rag.utils.errors import DocumentProcessingError

loader = PDFLoader()

try:
    documents = await loader.load("large_scan.pdf")
except DocumentProcessingError as e:
    print(f"Error: {e}")
    print(f"File: {e.file_path}")
    print(f"Error type: {e.error_type}")

    # Use partial results if available
    if e.partial_results:
        print(f"Successfully loaded {len(e.partial_results)} pages")
        documents = e.partial_results
    else:
        raise  # No partial results, re-raise
```

## Batch Processing Multiple Files

```python
import asyncio
from pathlib import Path
from vibe_rag import TextLoader, DocumentProcessor

async def process_directory(directory: str):
    loader = TextLoader()
    processor = DocumentProcessor(strategy="recursive", chunk_size=512)

    all_chunks = []

    for file_path in Path(directory).glob("*.txt"):
        try:
            # Load file
            documents = await loader.load(str(file_path))

            # Chunk
            for doc in documents:
                chunks = await processor.process(doc.content, doc.metadata)
                all_chunks.extend(chunks)

        except DocumentProcessingError as e:
            print(f"Failed to process {file_path}: {e}")
            continue

    return all_chunks

# Usage
chunks = await process_directory("knowledge_base/")
print(f"Processed {len(chunks)} chunks from directory")
```

## Integration with RAG Pipeline

```python
from vibe_rag import (
    TextLoader,
    DocumentProcessor,
    GeminiProvider,
    PostgresVectorStore
)

# Load and chunk documents
loader = TextLoader()
processor = DocumentProcessor(strategy="recursive", chunk_size=512)

documents = await loader.load("knowledge.txt")
chunks = await processor.process(documents[0].content, documents[0].metadata)

# Generate embeddings and store
provider = GeminiProvider(api_key="...")
embeddings = await provider.embed([chunk.content for chunk in chunks])

store = PostgresVectorStore(connection_string="...")
await store.add_documents(
    documents=chunks,
    collection_name="knowledge_base",
    embeddings=embeddings
)
```
