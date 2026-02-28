# vibe-rag Development Guidelines

## Project Context

Building **vibe-rag**: A production-grade, modular RAG (Retrieval-Augmented Generation) framework with "batteries included but removable" philosophy.

**Architecture:** Three-layer design (Core library → Service layer → Client layer) with pluggable components for LLM providers, storage backends, and pipeline strategies.

**Tech Stack:** Python 3.10+, LangChain, Google Gemini, PostgreSQL + pgvector, Pydantic, pytest

## Engineering Standards

### 1. Senior Engineer Mindset

When starting any task:

1. **ALWAYS use `/superpowers:brainstorming` skill FIRST**
   - Understand the "why" before the "how"
   - Explore requirements, constraints, and design options
   - Present 2-3 approaches with tradeoffs
   - Get alignment before coding

2. **Read the design documents**
   - `docs/plans/2026-02-28-rag-framework-design.md` - Overall architecture
   - `docs/plans/2026-02-28-vibe-rag-implementation.md` - Implementation details
   - Task description in Vibe Kanban - Specific context

3. **Think before coding**
   - Question assumptions
   - Consider edge cases
   - Think about testability
   - Plan for extensibility

### 2. Test-Driven Development (TDD)

**REQUIRED:** Follow TDD for all implementation work.

1. **Write failing tests first** (`/superpowers:test-driven-development`)
2. **Run tests to verify they fail**
3. **Write minimal code to pass**
4. **Run tests to verify they pass**
5. **Refactor if needed**
6. **Commit with descriptive message**

**Example workflow:**
```bash
# 1. Write test
pytest tests/unit/test_providers.py::test_gemini_generate -v

# 2. Implement
# ... write code ...

# 3. Verify
pytest tests/unit/test_providers.py::test_gemini_generate -v

# 4. Commit
git add tests/ vibe_rag/
git commit -m "feat: implement GeminiProvider.generate() method"
```

### 3. Code Quality Standards

**DRY (Don't Repeat Yourself):**
- Extract common patterns into functions/classes
- Reuse existing components
- Avoid copy-paste code

**YAGNI (You Aren't Gonna Need It):**
- Build only what's needed NOW
- No speculative features
- No premature optimization

**SOLID Principles:**
- Single Responsibility: Each class does ONE thing
- Open/Closed: Extend via inheritance, not modification
- Liskov Substitution: Subclasses must work like base classes
- Interface Segregation: Small, focused interfaces
- Dependency Inversion: Depend on abstractions, not concretions

**Production-Ready Code:**
- Type hints everywhere (Python 3.10+)
- Comprehensive docstrings (Google style)
- Error handling with custom exceptions
- Async/await for I/O operations
- Proper resource cleanup (async context managers)

### 4. Architecture Patterns

**Adapter Pattern (CRITICAL):**
- All providers implement `BaseLLMProvider`
- All storage backends implement `BaseVectorStore`
- All pipeline components implement `BasePipelineComponent`
- This enables swapping implementations without changing core code

**Composition over Inheritance:**
- Use PipelineBuilder to compose components
- Inject dependencies (provider, storage) into RAGEngine
- Favor small, composable pieces

**Configuration over Code:**
- Use Pydantic models for all config
- Support both programmatic and YAML config
- Validate early (at config load time)

### 5. Testing Strategy

**Test Coverage Targets:**
- Core engine: 90%+
- Providers: 85%+
- Storage: 85%+
- Pipeline: 80%+
- Utilities: 75%+

**Testing Levels:**

1. **Unit Tests** (fast, isolated):
   - Mock external dependencies (APIs, databases)
   - Test one component at a time
   - Located in `tests/unit/`

2. **Integration Tests** (slower, real dependencies):
   - Test component interactions
   - Use testcontainers for databases
   - Located in `tests/integration/`

3. **E2E Tests** (slowest, full workflow):
   - Test complete user workflows
   - Located in `tests/e2e/`

**Mocking Guidelines:**
- NEVER call real APIs in unit tests (Gemini, OpenAI, etc.)
- Use `unittest.mock.AsyncMock` for async functions
- Use `unittest.mock.patch` for external dependencies

### 6. Git Workflow

**Branching:**
- Work in dedicated worktrees (managed by Vibe Kanban)
- Branch naming: `vk/<issue-id>-<description>`
- Target branch: `origin/main`

**Commits:**
- Commit frequently (after each passing test)
- Use conventional commits format:
  ```
  feat: add GeminiProvider with text generation
  fix: handle empty query in similarity search
  test: add unit tests for Document model
  docs: update README with quick start guide
  ```
- Include `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>`

**Before Committing:**
- Run tests: `pytest`
- Check types: `mypy vibe_rag`
- Format code: `black vibe_rag tests`
- Lint: `ruff check vibe_rag tests`

### 7. Error Handling

**Use Custom Exceptions:**
- `RAGException` - Base for all framework errors
- `EmbeddingError` - Embedding generation failures
- `RetrievalError` - Document retrieval failures
- `LLMProviderError` - LLM API failures
- `StorageError` - Database/storage failures
- `ConfigurationError` - Invalid configuration

**Error Handling Pattern:**
```python
try:
    result = await external_api_call()
except ExternalAPIError as e:
    raise LLMProviderError(f"Failed to generate: {e}")
```

**NO Silent Failures:**
- Don't catch exceptions and ignore them
- Don't return `None` on errors
- Raise specific, informative exceptions

### 8. Documentation

**Docstring Format (Google Style):**
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

**README Updates:**
- Keep quick start example up-to-date
- Add new features to feature list
- Update installation instructions as dependencies change

### 9. Performance Considerations

**Async Everything:**
- All I/O operations must be async (database, API calls)
- Use `asyncio.gather()` for parallel operations
- Use connection pooling (asyncpg for PostgreSQL)

**Optimization Priorities:**
1. Correctness (works correctly)
2. Clarity (easy to understand)
3. Performance (fast enough)

**Don't Optimize Prematurely:**
- Write clear code first
- Measure before optimizing
- Profile to find bottlenecks

### 10. Security

**Never Commit Secrets:**
- Use environment variables for API keys
- Use `.env` files (gitignored)
- Document required env vars in README

**Input Validation:**
- Validate all user inputs with Pydantic
- Sanitize before passing to databases
- Use parameterized queries (prevent SQL injection)

**API Key Safety:**
- Never log API keys
- Never include in error messages
- Use `SecretStr` in Pydantic models

## Task Execution Workflow

### Starting a Task

1. **Read Vibe Kanban task description** (has full context)
2. **Invoke `/superpowers:brainstorming`** (REQUIRED)
3. **Read referenced design documents**
4. **Understand dependencies** (what must be done first)
5. **Clarify acceptance criteria** (what does "done" mean)

### During Implementation

1. **Follow TDD religiously** (test → code → test → commit)
2. **Ask questions when unclear** (don't guess)
3. **Check existing patterns** (reuse, don't reinvent)
4. **Keep commits small and focused** (one logical change)
5. **Run tests frequently** (catch issues early)

### Before Marking Complete

1. **Verify all acceptance criteria met**
2. **Run full test suite** (`pytest`)
3. **Check test coverage** (`pytest --cov`)
4. **Run linters** (`black`, `ruff`, `mypy`)
5. **Update documentation** (docstrings, README)
6. **Commit all changes**
7. **Use `/superpowers:verification-before-completion`**

### Common Pitfalls to Avoid

❌ **Skip brainstorming** → Leads to wrong implementations
❌ **Skip tests** → Introduces bugs
❌ **Over-engineer** → YAGNI violation
❌ **Copy-paste code** → DRY violation
❌ **Ignore dependencies** → Build in wrong order
❌ **Skip documentation** → No one knows how to use it
❌ **Commit broken code** → Breaks main branch

✅ **DO: Brainstorm → TDD → Small commits → Verify → Complete**

## Key Architecture Decisions

### Why PostgreSQL + pgvector?
- Production-ready, battle-tested
- Leverage existing PostgreSQL infrastructure
- No vendor lock-in from managed vector DBs
- JSONB for flexible metadata
- Lower operational cost

### Why Gemini First?
- Modern, clean API
- Cost-effective
- Good performance
- Easy to add other providers later via adapter pattern

### Why Adapter Pattern Everywhere?
- Swappable components without code changes
- Testable (mock implementations)
- Extensible (users can add custom implementations)
- Production-ready from day one

### Why "Batteries Included, But Removable"?
- Quick start (5 minutes with QuickSetup)
- Full customization (compose your own pipeline)
- Appeals to both beginners and experts

## Reference Documents

- **Design Doc:** `docs/plans/2026-02-28-rag-framework-design.md`
- **Implementation Plan:** `docs/plans/2026-02-28-vibe-rag-implementation.md`
- **Vibe Kanban Tasks:** Check task description for specific context

## Questions? Ask!

- Unclear requirements? **Ask before coding**
- Multiple approaches? **Present options with tradeoffs**
- Uncertain about design? **Use brainstorming skill**
- Blocked by dependencies? **Clarify and document**

**Remember:** Senior engineers think deeply, ask questions, and deliver quality over speed.
