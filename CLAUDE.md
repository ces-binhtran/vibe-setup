# vibe-rag Development Guidelines

## Project Identity

**vibe-rag**: Production-grade, modular RAG framework with "batteries included but removable" philosophy.

**Architecture:** Three-layer design (Core → Service → Client) with pluggable components for LLM providers, storage backends, and pipeline strategies.

**Tech Stack:** Python 3.10+, LangChain, Google Gemini, PostgreSQL + pgvector, Pydantic, pytest

## Workflow Checkpoints

**CRITICAL:** At each checkpoint, read the corresponding skill file and follow it exactly.

### File-Based Skill Loading

Claude Code cannot load project-local skills via the Skill tool. Instead, **read skill files directly** using the Read tool:

- **Starting any task:** Read `.claude/skills/vibe-rag-task-workflow.md`
- **Before committing:** Read `.claude/skills/vibe-rag-commit-guidelines.md`
- **Implementing components:** Read `.claude/skills/vibe-rag-tdd.md` + `.claude/skills/vibe-rag-component.md`
- **Writing code:** Read `.claude/skills/vibe-rag-code-quality.md`
- **Handling errors:** Read `.claude/skills/vibe-rag-error-handling.md`
- **Writing docs:** Read `.claude/skills/vibe-rag-documentation.md`
- **Using parallel work:** Read `.claude/skills/vibe-rag-agent-teams.md`

**Important:** These are instructions to Claude Code agents. Read the file, then follow it exactly.

## Project-Specific Patterns

### Adapter Pattern (CRITICAL)

All pluggable components use adapter pattern:

- All LLM providers implement `BaseLLMProvider`
- All storage backends implement `BaseVectorStore`
- All pipeline components implement `BasePipelineComponent`

**Why?** Enables swapping implementations without changing core code.

### Custom Exceptions

Located in `vibe_rag/utils/errors.py`:

- `RAGException` - Base for all framework errors
- `EmbeddingError` - Embedding generation failures
- `RetrievalError` - Document retrieval failures
- `LLMProviderError` - LLM API failures
- `StorageError` - Database/storage failures
- `ConfigurationError` - Invalid configuration

### Async Requirements

- All I/O operations must be async (database, API calls)
- Use connection pooling (asyncpg for PostgreSQL)
- Use async context managers for resource cleanup

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
- Easy to add other providers via adapter pattern

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

- **Design:** `docs/plans/2026-02-28-rag-framework-design.md`
- **Implementation:** `docs/plans/2026-02-28-vibe-rag-implementation.md`
- **Vibe Kanban:** Check task description for specific context

## Critical Reminders

- ❌ **NEVER** add `Co-Authored-By: Claude` footers to commits
- ✅ **ALWAYS** read and follow skills at workflow checkpoints
- ✅ **ALWAYS** follow TDD (tests first)
- ✅ **ALWAYS** use adapter pattern for components
