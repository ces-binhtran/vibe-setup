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

---

## Examples

### simple_rag.py

A complete RAG workflow demonstrating the full pipeline from configuration to answers.

**What it shows:**
- Manual `RAGConfig` setup with explicit `LLMConfig`, `StorageConfig`, `PipelineConfig`, `ChunkingConfig`
- Ingesting multiple `.txt` files into a shared collection
- Querying with natural language and printing answers
- Accessing per-query metrics and aggregate statistics

**Run:**
```bash
python simple_rag.py
```

**Expected output:**
```
Configuring RAG engine...
Initializing RAG engine...

Creating sample documents...
  Ingesting python_intro.txt...
  Ingesting python_history.txt...
  Ingesting python_ecosystem.txt...
Ingested 3 documents

Running test queries...

Query 1: Who created Python and when?
Answer:
Python was created by Guido van Rossum. The first release was Python 0.9.0 in
February 1991...

...

Example completed successfully!
```

---

### advanced_rag.py

Demonstrates extensibility patterns: metadata filtering, chunking strategy comparison,
and multi-collection querying.

**What it shows:**
- Metadata filtering — restrict retrieval to a specific domain without separate collections
- Chunking strategy comparison — `recursive` vs `fixed` at different chunk sizes
- Multi-collection querying — separate knowledge bases per domain

**Run:**
```bash
python advanced_rag.py
```

**Expected output:**
```
=== Advanced RAG Techniques Demo ===

--- Technique 1: Metadata Filtering ---
  Ingested: legal
  Ingested: engineering
  Query (no filter): 5 sources
  Query (legal filter): 2 sources
  Domains returned: {'legal'}

--- Technique 2: Chunking Strategies ---
  strategy='recursive', chunk_size=256: 8 chunks
  strategy='fixed', chunk_size=512: 4 chunks

--- Technique 3: Multi-Collection ---
  [legal] 'What are the key requirements?' -> 1 docs
  [engineering] 'What are the key requirements?' -> 1 docs

=== Done ===
```

---

### multi_domain_rag.py

Shows how to maintain isolated knowledge bases for distinct business domains and
compare the same query across all of them.

**Domains covered:**
- HR Policy — vacation, leave, expense reimbursement, remote work rules
- Engineering Guide — language standards, architecture patterns, testing requirements
- Legal Compliance — data retention, GDPR, contract review, incident response

**What it shows:**
- Using `BasicRAGModule` for concise, named per-domain setup
- Ingesting inline content (no external files beyond temp files)
- Cross-domain comparison: the same question answered by each domain's knowledge base
- Domain isolation verification: confirming that HR queries only return HR documents
- Domain-specific targeted queries for each area

**Run:**
```bash
python multi_domain_rag.py
```

**Expected output:**
```
Multi-Domain RAG Example
Demonstrates domain isolation using separate collections

--- Ingesting domain knowledge bases ---

  Ingesting HR Policy -> collection 'multi_domain_hr'...
    -> 5 chunks stored
  Ingesting Engineering Guide -> collection 'multi_domain_eng'...
    -> 6 chunks stored
  Ingesting Legal Compliance -> collection 'multi_domain_legal'...
    -> 7 chunks stored

--- Cross-Domain Comparison ---

  Question: "What are the key requirements and time limits I need to know?"

  [HR Policy]
    Docs retrieved: 3
    Time: 1245ms
    Answer preview: Key time limits in HR policy include: 30-day expense submission
    window, 10-day sick leave entitlement, and leave accrual...

  [Engineering Guide]
    Docs retrieved: 3
    Time: 1180ms
    Answer preview: Key engineering requirements include Python 3.10+, TDD with
    90% coverage target, and async I/O for all database calls...

  [Legal Compliance]
    Docs retrieved: 3
    Time: 1310ms
    Answer preview: Key legal time limits: 90-day data retention after account
    closure, 72-hour data breach reporting window...

--- Domain Isolation Verification ---

  Query sent to HR domain only: "How many days of vacation leave do employees get?"
  Sources retrieved: 3
  Domains present in sources: {'hr_policy'}
  PASS: Sources are isolated to the HR domain.

--- Domain-Specific Queries ---

  [HR Policy] What is the expense reimbursement policy?
    Answer: All business expenses must be submitted within 30 days...

  [Engineering Guide] What architecture pattern should I use for pluggable components?
    Answer: Use the adapter pattern for all pluggable components...

  [Legal Compliance] How quickly must data breaches be reported?
    Answer: Data breaches involving personal data must be reported within 72 hours...

======================================================================
Done. Each domain's knowledge base is fully isolated.
======================================================================
```

---

## Customization

### Change Chunking Strategy

```python
chunking=ChunkingConfig(
    strategy="fixed",      # or "recursive"
    chunk_size=1024,       # larger chunks
    chunk_overlap=100,     # more overlap
)
```

### Adjust Retrieval

```python
pipeline=PipelineConfig(
    top_k=10,                              # retrieve more documents
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

### Use a Specific Domain Collection

```python
async with BasicRAGModule(
    api_key=os.environ["GOOGLE_API_KEY"],
    db_url=os.environ["DATABASE_URL"],
    collection_name="engineering",   # targets only engineering docs
) as rag:
    result = await rag.query("What testing framework should I use?")
```

---

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
```

### Import Errors

```bash
# Ensure vibe-rag is installed
pip install -e ..

# Verify installation
python -c "import vibe_rag; print(vibe_rag.__version__)"
```

---

## Further Reading

- [API Reference](../docs/api-reference.md)
- [Quickstart Guide](../docs/quickstart.md)
- [Testing Guide](../docs/testing-guide.md)
- [Docker Deployment](../docs/deployment/docker.md)
- [Kubernetes Deployment](../docs/deployment/kubernetes.md)
- [Architecture Plans](../docs/plans/)
