---
name: vibe-rag-documentation
description: Enforce Google-style docstrings, README updates, and security best practices - ensures documentation quality and prevents secret leaks
---

# vibe-rag Documentation Standards

Use this skill when writing documentation, docstrings, or handling sensitive data.

## Docstring Format (Google Style)

**All functions, classes, and methods must have docstrings:**

```python
async def similarity_search(
    self,
    query_embedding: list[float],
    collection_name: str,
    top_k: int = 5,
    filters: dict | None = None
) -> list[Document]:
    """Search for similar documents using vector similarity.

    Args:
        query_embedding: Query embedding vector
        collection_name: Name of the collection to search
        top_k: Number of top results to return
        filters: Optional metadata filters

    Returns:
        List of similar documents with scores

    Raises:
        RetrievalError: If search fails
    """
```

**Required sections:**
- Brief description (first line)
- `Args:` - All parameters with types and descriptions
- `Returns:` - Return value type and description
- `Raises:` - All exceptions that can be raised

## README Updates

**When adding features, update README.md:**

- **Keep quick start example up-to-date** - Users should be able to copy-paste and run
- **Add new features to feature list** - Document all public-facing capabilities
- **Update installation instructions** - As dependencies change, keep install steps current

## Security Best Practices

### Never Commit Secrets

❌ **DON'T commit:**
- API keys
- Passwords
- Database credentials
- Private keys

✅ **DO instead:**
- Use environment variables for API keys
- Use `.env` files (add to `.gitignore`)
- Document required env vars in README

**Example:**

```python
import os

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ConfigurationError("GEMINI_API_KEY environment variable required")
```

### Input Validation

**Validate all user inputs:**

- **Validate with Pydantic** - Use models for all config and user inputs
- **Sanitize before passing to databases** - Prevent injection attacks
- **Use parameterized queries** - Prevent SQL injection (asyncpg handles this automatically)

**Example:**

```python
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=100)
```

### API Key Safety

**Protect API keys in code:**

❌ **NEVER do:**
- Log API keys: `logger.info(f"Using key: {api_key}")`
- Include in error messages: `raise Error(f"API key {api_key} is invalid")`

✅ **DO instead:**
- Use `SecretStr` in Pydantic models
- Mask in logs: `logger.info("Using configured API key")`
- Generic errors: `raise Error("API key is invalid")`

**Example:**

```python
from pydantic import BaseModel, SecretStr

class GeminiConfig(BaseModel):
    api_key: SecretStr  # Automatically masked in logs and repr
```
