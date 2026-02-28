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

# 4. Commit with meaningful message
git add tests/ vibe_rag/
git commit -m "feat: implement GeminiProvider.generate() method

Why this change was needed:
- GeminiProvider needs text generation to fulfill BaseLLMProvider contract
- Users expect streaming and non-streaming generation modes
- Production apps need configurable temperature and token limits

What changed:
- Implemented generate() and generate_stream() methods
- Added parameter validation using Pydantic
- Integrated with Gemini's generateContent API

Technical notes:
- Default temperature 0.7 balances creativity and consistency
- Max tokens default 2048 matches typical RAG response length
- Streaming uses server-sent events, requires async iteration"
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
- Use conventional commits format with meaningful explanations

**Commit Message Format (REQUIRED):**

Every commit message MUST explain the "why" behind the change, not just the "what". Future developers (including the AI agent itself) need to understand the reasoning when reviewing code history.

```
<type>: <short summary (50 chars max)>

Why this change was needed:
- <Reason 1: problem being solved or requirement being met>
- <Reason 2: constraint or edge case being handled>
- <Reason 3: architectural decision or pattern being followed>

What changed:
- <Key change 1>
- <Key change 2>

Technical notes:
- <Implementation detail worth remembering>
- <Alternative considered and why rejected>
- <Gotcha or edge case to watch for>
```

**Examples of GOOD commit messages:**

```
feat: implement async context manager for PostgresVectorStore

Why this change was needed:
- PostgreSQL connections must be properly closed to avoid connection pool exhaustion
- asyncpg requires explicit connection lifecycle management
- Production deployments need graceful shutdown handling

What changed:
- Added __aenter__ and __aexit__ methods to PostgresVectorStore
- Wrapped connection acquisition in async context manager
- Added connection pool cleanup in __aexit__

Technical notes:
- Considered using atexit handler but async cleanup requires event loop
- Connection timeout set to 30s based on typical query duration profiling
- Pool size defaults to 10 based on expected concurrent request volume
```

```
fix: handle None embeddings in similarity_search

Why this change was needed:
- Gemini API returns None for empty strings instead of raising error
- This caused crashes in retrieval pipeline when processing empty documents
- Users expect graceful degradation, not crashes

What changed:
- Added None check before vector similarity computation
- Return empty list when query embedding is None
- Added logging to track when this happens

Technical notes:
- Alternative was to fail fast, but that breaks batch processing
- Considered returning error object but empty list matches pgvector behavior
- This matches the Liskov Substitution Principle for BaseVectorStore
```

```
refactor: extract embedding batching logic into EmbeddingBatcher

Why this change was needed:
- Gemini API has 100-item batch limit, exceeding it causes 400 errors
- Same batching logic was duplicated in 3 different provider classes (DRY violation)
- Adding new providers required re-implementing complex batching logic

What changed:
- Created EmbeddingBatcher utility class
- Moved batch splitting and rate limiting to shared component
- Updated all providers to use EmbeddingBatcher

Technical notes:
- Batch size configurable per provider (Gemini=100, OpenAI=2048)
- Preserves order of results to match input documents
- Async batching with asyncio.gather for parallel requests
```

**❌ FORBIDDEN - DO NOT ADD:**
```
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```
**CRITICAL:** Never add Co-Authored-By footers attributing commits to Claude or any AI assistant. Commits should be attributed to the human developer only.

**Commit Message Checklist:**

Before committing, ensure your message answers:
- [ ] **Why was this change necessary?** (problem, requirement, or improvement)
- [ ] **What alternatives were considered?** (if applicable)
- [ ] **What are the key technical decisions?** (implementation choices)
- [ ] **Are there gotchas or edge cases?** (things to watch out for)
- [ ] **Does it follow conventional commit format?** (type: summary)
- [ ] **Is it free of AI attribution?** (no Co-Authored-By Claude)

**Commit Types:**
- `feat:` - New feature or capability
- `fix:` - Bug fix or error handling
- `refactor:` - Code restructuring without behavior change
- `perf:` - Performance improvement
- `test:` - Adding or updating tests
- `docs:` - Documentation changes
- `chore:` - Tooling, dependencies, config
- `style:` - Formatting, whitespace (no logic change)

**Before Committing:**
- Run tests: `pytest`
- Check types: `mypy vibe_rag`
- Format code: `black vibe_rag tests`
- Lint: `ruff check vibe_rag tests`
- **Write meaningful commit message** (explains WHY, not just WHAT)

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
6. **Use parallel agents when beneficial** (see below)

### Agent Teams & Parallel Work

**vibe-rag uses agent teams for parallel development.** Choose the right approach based on your task.

#### Three Approaches to Parallel Work

**1. Subagents (Task tool)** - Quick, focused workers
- Workers report results back to main agent only
- Best for: focused research, verification, independent queries
- Lower token cost (results summarized back)
- Use when: you only need the result, not ongoing collaboration

**2. Agent Teams** - Collaborative teammates
- Teammates communicate with each other and share a task list
- Best for: research & review, new modules, debugging with competing hypotheses, cross-layer coordination
- Higher token cost (each teammate is full Claude instance)
- Use when: teammates need to share findings, challenge each other, coordinate independently

**3. Dispatching Parallel Agents Skill** - Guided orchestration
- Use `/superpowers:dispatching-parallel-agents` for help coordinating
- Skill helps identify independent tasks and manage agents
- Best for: when you need help structuring the parallel work

#### When to Use Agent Teams

✅ **Good use cases:**
- **Research and review**: Multiple perspectives investigating different aspects simultaneously
- **New modules/features**: Each teammate owns a separate piece (LLM provider + Storage backend + Pipeline)
- **Debugging with competing hypotheses**: Teammates test different theories in parallel
- **Cross-layer coordination**: Frontend, backend, and tests each owned by different teammate

❌ **Not good for:**
- Sequential tasks with many dependencies
- Same-file edits (causes conflicts)
- Simple tasks where coordination overhead exceeds benefit

#### How to Use Agent Teams

**Enabling (required first time):**
```bash
# Add to ~/.claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

**Creating a team:**
```
Create an agent team with 3 teammates:
- Teammate 1: Implement BaseLLMProvider + GeminiProvider (tests + code)
- Teammate 2: Implement BaseVectorStore + PostgresVectorStore (tests + code)
- Teammate 3: Implement BasePipelineComponent + basic retriever (tests + code)

Each teammate should follow TDD and work independently in their own files.
```

**Best practices:**
- **Start with 3-5 teammates** (optimal for most workflows)
- **Size tasks appropriately** (5-6 tasks per teammate keeps everyone productive)
- **Give teammates enough context** (they don't inherit conversation history)
- **Avoid file conflicts** (each teammate owns different files)
- **Monitor and steer** (check progress, redirect if needed)
- **Require plan approval for risky tasks** (teammates plan before implementing)

**Communication:**
- Teammates share a task list and can message each other
- Lead coordinates work and synthesizes results
- You can talk to any teammate directly (Shift+Down to cycle in terminal)

**Display modes:**
- **In-process**: All teammates in main terminal (Shift+Down to cycle)
- **Split panes**: Each teammate in own pane (requires tmux or iTerm2)

#### Example: Parallel Phase Implementation

```
Task: Implement Phase 1 core components

Create agent team with 3 teammates:
1. "LLM Provider" teammate - Implements BaseLLMProvider + GeminiProvider with full test coverage
2. "Storage" teammate - Implements BaseVectorStore + PostgresVectorStore with full test coverage
3. "Pipeline" teammate - Implements BasePipelineComponent + SimpleRetriever with full test coverage

Requirements for all teammates:
- Follow TDD workflow (write tests first)
- Follow CLAUDE.md guidelines
- Use custom vibe-rag-tdd skill
- Achieve 85%+ test coverage
- Use async/await for all I/O
- Create separate files (no conflicts)

Each teammate should coordinate on shared dependencies via task list.
```

#### Comparison: When to Use What

| Scenario | Use Subagents | Use Agent Teams |
|----------|---------------|-----------------|
| Quick research on 3 libraries | ✅ | ❌ |
| Review PR from 3 perspectives | ❌ | ✅ |
| Implement 3 independent modules | ❌ | ✅ |
| Debug with competing theories | ❌ | ✅ |
| Verify test coverage | ✅ | ❌ |
| Cross-layer feature (FE+BE+tests) | ❌ | ✅ |

#### Coordination with Vibe Kanban

- Agent teams work great with Vibe Kanban task dependencies
- Lead can assign Vibe Kanban tasks to specific teammates
- Teammates update task status as they progress
- Shared task list ensures no duplicate work

### Code Simplification & Quality

**After Writing Code:**
1. **Use `/code-simplifier` skill** to refine and simplify code
   - Improves clarity and maintainability
   - Removes unnecessary complexity
   - Preserves all functionality
   - Applies after implementation, before final commit

**Example workflow:**
```
Write code → Tests pass → /code-simplifier → Review → Commit
```

### Before Marking Complete

1. **Verify all acceptance criteria met**
2. **Run full test suite** (`pytest`)
3. **Check test coverage** (`pytest --cov`)
4. **Run linters** (`black`, `ruff`, `mypy`)
5. **Simplify code** (`/code-simplifier`)
6. **Update documentation** (docstrings, README)
7. **Commit all changes**
8. **Use `/superpowers:verification-before-completion`**

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
