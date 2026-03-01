---
name: vibe-rag-commit-guidelines
description: Guides agent through vibe-rag commit message standards and Git workflow
---

**Note:** This skill is loaded via file read (`.claude/skills/vibe-rag-commit-guidelines.md`) because Claude Code does not support project-local skill registration.

# vibe-rag Commit Guidelines

## Git Workflow

**Branching:**
- Work in dedicated worktrees (managed by Vibe Kanban)
- Branch naming: `vk/<issue-id>-<description>`
- Target branch: `origin/main`

**Commits:**
- Commit frequently (after each passing test)
- Use conventional commits format with meaningful explanations

## Commit Message Format (REQUIRED)

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

## Examples of GOOD Commit Messages

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

## ❌ FORBIDDEN - DO NOT ADD

```
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**CRITICAL:** Never add Co-Authored-By footers attributing commits to Claude or any AI assistant. Commits should be attributed to the human developer only.

## Commit Message Checklist

Before committing, ensure your message answers:
- [ ] **Why was this change necessary?** (problem, requirement, or improvement)
- [ ] **What alternatives were considered?** (if applicable)
- [ ] **What are the key technical decisions?** (implementation choices)
- [ ] **Are there gotchas or edge cases?** (things to watch out for)
- [ ] **Does it follow conventional commit format?** (type: summary)
- [ ] **Is it free of AI attribution?** (no Co-Authored-By Claude)

## Commit Types

- `feat:` - New feature or capability
- `fix:` - Bug fix or error handling
- `refactor:` - Code restructuring without behavior change
- `perf:` - Performance improvement
- `test:` - Adding or updating tests
- `docs:` - Documentation changes
- `chore:` - Tooling, dependencies, config
- `style:` - Formatting, whitespace (no logic change)

## Before Committing

- Run tests: `pytest`
- Check types: `mypy vibe_rag`
- Format code: `black vibe_rag tests`
- Lint: `ruff check vibe_rag tests`
- **Write meaningful commit message** (explains WHY, not just WHAT)
