# Vibe-RAG Examples

This directory contains example scripts demonstrating vibe-rag functionality.

## Prerequisites

Before running examples:

1. **Python 3.10+** installed
2. **PostgreSQL with pgvector** running:
   ```bash
   docker-compose -f ../docker-compose.test.yml up -d
   ```
3. **Google Gemini API key** set:
   ```bash
   export GOOGLE_API_KEY="your-api-key"
   ```
4. **Install vibe-rag**:
   ```bash
   pip install -e ..
   ```

## Examples

### simple_rag.py

A complete RAG workflow demonstrating:
- Configuration setup
- Document ingestion (multiple files)
- Querying with natural language
- Metrics and observability
- Result analysis

**Run:**
```bash
python simple_rag.py
```

**What it does:**
1. Creates sample documents about Python
2. Ingests them into the vector database
3. Runs several test queries
4. Shows answers, sources, and metrics

**Expected output:**
```
╔═══════════════════════════════════════════════════════════════╗
║              Vibe-RAG Simple Example                          ║
║  Production-grade RAG framework with batteries included       ║
╚═══════════════════════════════════════════════════════════════╝

🔧 Configuring RAG engine...
🚀 Initializing RAG engine...
✅ Collection cleaned

📝 Creating sample documents...
  📄 Ingesting python_intro.txt...
  📄 Ingesting python_history.txt...
  📄 Ingesting python_ecosystem.txt...
✅ Ingested 3 documents

🔍 Running test queries...

======================================================================
Query 1: Who created Python and when?
======================================================================

💡 Answer:
Python was created by Guido van Rossum in 1991. The first official release
was Python 0.9.0 in February 1991.

📊 Metadata:
  - Documents retrieved: 3
  - Retrieval time: 145.23ms
  - Generation time: 892.45ms
  - Total time: 1037.68ms

📚 Top sources:
  1. Score: 0.1234
     From: python_history.txt
     Preview: Python was conceived in the late 1980s by Guido van Rossum...

...

✅ Example completed successfully!
```

## Customization

### Change Chunking Strategy

```python
chunking=ChunkingConfig(
    strategy="fixed",      # or "recursive"
    chunk_size=1024,      # larger chunks
    chunk_overlap=100,    # more overlap
)
```

### Adjust Retrieval

```python
pipeline=PipelineConfig(
    top_k=10,                          # retrieve more documents
    filter_metadata={"category": "tech"},  # filter by metadata
)
```

### Custom Generation

```python
result = await engine.query(
    "Your question?",
    generation_kwargs={
        "temperature": 0.7,  # more creative
        "max_tokens": 500,   # longer answers
    }
)
```

## Troubleshooting

### Database Connection Error

```bash
# Check if PostgreSQL is running
docker ps | grep vibe-rag-test-db

# Start it if not running
docker-compose -f ../docker-compose.test.yml up -d

# Check connection
docker exec -it vibe-rag-test-db psql -U vibetest -d vibe_rag_test -c "SELECT version();"
```

### API Key Error

```bash
# Verify API key is set
echo $GOOGLE_API_KEY

# Set it if not
export GOOGLE_API_KEY="your-actual-key"

# Or hardcode in script (not recommended for production)
api_key="your-key-here"
```

### Import Errors

```bash
# Ensure vibe-rag is installed
pip install -e ..

# Verify installation
python -c "import vibe_rag; print(vibe_rag.__version__)"
```

## Next Steps

- 📖 Read [Quickstart Guide](../docs/quickstart.md)
- 🧪 See [Testing Guide](../docs/testing-guide.md)
- 🏗️ Check [Architecture Documentation](../docs/plans/)
- 🚀 Build your own RAG application!

## Additional Examples (Coming Soon)

- `custom_loader.py` - Custom document loaders
- `metadata_filtering.py` - Advanced metadata filtering
- `streaming_responses.py` - Streaming LLM responses
- `multi_collection.py` - Multiple knowledge bases
- `production_config.py` - Production-ready configuration
