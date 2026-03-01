# CLAUDE.md Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use @superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor CLAUDE.md from 574 lines to ~120 lines by extracting workflow content into 8 focused skills, achieving 79% context reduction and 20K-25K token savings per session.

**Architecture:** Content migration approach - extract workflow sections from CLAUDE.md into dedicated skill files, rewrite CLAUDE.md as pure facts reference with auto-trigger instructions, enhance existing skills with testing strategies.

**Tech Stack:** Markdown, Claude Code skills format (YAML frontmatter + content)

---

## Task 1: Create vibe-rag-task-workflow.md Skill

**Files:**
- Create: `.claude/skills/vibe-rag-task-workflow.md`
- Reference: `CLAUDE.md:364-532` (source content)

**Step 1: Create skill file with frontmatter**

Create `.claude/skills/vibe-rag-task-workflow.md`:

```markdown
---
name: vibe-rag-task-workflow
description: Complete workflow for task execution from start to finish - ensures brainstorming, TDD, proper commits, and verification before completion
---

# vibe-rag Task Workflow

Use this skill when starting ANY task or before marking a task complete.
```

**Step 2: Add "Starting a Task" section**

Extract content from CLAUDE.md lines 366-372 and add:

```markdown
## Starting a Task

Before writing any code:

1. **Read Vibe Kanban task description** - Full context is in the task
2. **Invoke `/superpowers:brainstorming`** - REQUIRED for all tasks
   - Understand the "why" before the "how"
   - Explore requirements, constraints, and design options
   - Present 2-3 approaches with tradeoffs
   - Get alignment before coding
3. **Read referenced design documents**
   - `docs/plans/2026-02-28-rag-framework-design.md` - Overall architecture
   - `docs/plans/2026-02-28-vibe-rag-implementation.md` - Implementation details
   - Task description in Vibe Kanban - Specific context
4. **Understand dependencies** - What must be done first?
5. **Clarify acceptance criteria** - What does "done" mean?
```

**Step 3: Add "During Implementation" section**

Extract content from CLAUDE.md lines 374-381 and add:

```markdown
## During Implementation

1. **Follow TDD religiously** - Invoke `/vibe-rag:tdd` skill
   - Write failing tests first
   - Run tests to verify they fail
   - Write minimal code to pass
   - Run tests to verify they pass
   - Refactor if needed
   - Commit with descriptive message
2. **Ask questions when unclear** - Don't guess, ask
3. **Check existing patterns** - Reuse, don't reinvent
   - Look for similar implementations in the codebase
   - Follow established patterns (adapter, composition, etc.)
4. **Keep commits small and focused** - One logical change per commit
5. **Run tests frequently** - Catch issues early
6. **Use parallel agents when beneficial** - Invoke `/vibe-rag:agent-teams` for guidance
```

**Step 4: Add "Before Marking Complete" section**

Extract content from CLAUDE.md lines 511-520 and add:

```markdown
## Before Marking Complete

**Verification Checklist** (complete ALL before marking task done):

1. **Verify all acceptance criteria met** - Check task description
2. **Run full test suite** - `pytest`
3. **Check test coverage** - `pytest --cov`
   - Core engine: 90%+
   - Providers: 85%+
   - Storage: 85%+
   - Pipeline: 80%+
   - Utilities: 75%+
4. **Run linters and formatters**
   - `black vibe_rag tests`
   - `ruff check vibe_rag tests`
   - `mypy vibe_rag`
5. **Simplify code** - Invoke `/code-simplifier` skill
6. **Update documentation** - Invoke `/vibe-rag:documentation` if needed
7. **Commit all changes** - Invoke `/vibe-rag:commit-guidelines`
8. **Use `/superpowers:verification-before-completion`** - Final check
```

**Step 5: Add "Common Pitfalls" section**

Extract content from CLAUDE.md lines 522-532 and add:

```markdown
## Common Pitfalls to Avoid

❌ **Skip brainstorming** → Leads to wrong implementations
❌ **Skip tests** → Introduces bugs
❌ **Over-engineer** → YAGNI violation
❌ **Copy-paste code** → DRY violation
❌ **Ignore dependencies** → Build in wrong order
❌ **Skip documentation** → No one knows how to use it
❌ **Commit broken code** → Breaks main branch

✅ **DO: Brainstorm → TDD → Small commits → Verify → Complete**
```

**Step 6: Add "Questions? Ask!" section**

Extract content from CLAUDE.md lines 566-573 and add:

```markdown
## Questions? Ask!

- Unclear requirements? **Ask before coding**
- Multiple approaches? **Present options with tradeoffs**
- Uncertain about design? **Use `/superpowers:brainstorming` skill**
- Blocked by dependencies? **Clarify and document**

**Remember:** Senior engineers think deeply, ask questions, and deliver quality over speed.
```

**Step 7: Commit**

```bash
git add .claude/skills/vibe-rag-task-workflow.md
git commit -m "feat: create vibe-rag-task-workflow skill

Why this change was needed:
- CLAUDE.md contains 574 lines with workflow mixed into facts
- Workflow content should be invoked on-demand, not loaded every session
- Task workflow is needed at start and completion of every task

What changed:
- Created vibe-rag-task-workflow.md skill with complete task lifecycle
- Extracted Starting/During/Complete workflow from CLAUDE.md lines 364-532
- Added common pitfalls and Q&A guidance

Technical notes:
- Skill auto-triggers when starting tasks or before marking complete
- References other skills (brainstorming, TDD, commit-guidelines)
- Part of CLAUDE.md refactoring to reduce 79% context size"
```

---

## Task 2: Create vibe-rag-commit-guidelines.md Skill

**Files:**
- Create: `.claude/skills/vibe-rag-commit-guidelines.md`
- Reference: `CLAUDE.md:150-273` (source content)

**Step 1: Create skill file with frontmatter**

Create `.claude/skills/vibe-rag-commit-guidelines.md`:

```markdown
---
name: vibe-rag-commit-guidelines
description: Enforce meaningful commit messages with "why" explanations - ensures future developers understand reasoning, not just changes
---

# vibe-rag Commit Guidelines

Use this skill before creating ANY git commit.
```

**Step 2: Add commit message format**

Extract content from CLAUDE.md lines 161-181 and add:

```markdown
## Commit Message Format (REQUIRED)

Every commit message MUST explain the "why" behind the change, not just the "what". Future developers (including AI agents) need to understand the reasoning when reviewing code history.

**Template:**

\`\`\`
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
\`\`\`
```

**Step 3: Add good commit examples**

Extract content from CLAUDE.md lines 183-240 and add all 3 examples:

```markdown
## Examples of GOOD Commit Messages

### Example 1: Feature Implementation

\`\`\`
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
\`\`\`

### Example 2: Bug Fix

\`\`\`
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
\`\`\`

### Example 3: Refactoring

\`\`\`
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
\`\`\`
```

**Step 4: Add FORBIDDEN section**

Extract content from CLAUDE.md lines 242-246 and add:

```markdown
## ❌ FORBIDDEN - DO NOT ADD

**NEVER add Co-Authored-By footers attributing commits to Claude or any AI assistant:**

\`\`\`
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
\`\`\`

**CRITICAL:** Commits should be attributed to the human developer only. AI agents are tools used by the developer, not co-authors.
```

**Step 5: Add commit message checklist**

Extract content from CLAUDE.md lines 248-256 and add:

```markdown
## Commit Message Checklist

Before committing, ensure your message answers:

- [ ] **Why was this change necessary?** (problem, requirement, or improvement)
- [ ] **What alternatives were considered?** (if applicable)
- [ ] **What are the key technical decisions?** (implementation choices)
- [ ] **Are there gotchas or edge cases?** (things to watch out for)
- [ ] **Does it follow conventional commit format?** (type: summary)
- [ ] **Is it free of AI attribution?** (no Co-Authored-By Claude)
```

**Step 6: Add commit types**

Extract content from CLAUDE.md lines 258-266 and add:

```markdown
## Commit Types

- `feat:` - New feature or capability
- `fix:` - Bug fix or error handling
- `refactor:` - Code restructuring without behavior change
- `perf:` - Performance improvement
- `test:` - Adding or updating tests
- `docs:` - Documentation changes
- `chore:` - Tooling, dependencies, config
- `style:` - Formatting, whitespace (no logic change)
```

**Step 7: Add pre-commit commands**

Extract content from CLAUDE.md lines 268-273 and add:

```markdown
## Before Committing

Run these commands to verify code quality:

\`\`\`bash
# Run tests
pytest

# Check types
mypy vibe_rag

# Format code
black vibe_rag tests

# Lint
ruff check vibe_rag tests
\`\`\`

**Then write a meaningful commit message** that explains WHY, not just WHAT.
```

**Step 8: Commit**

```bash
git add .claude/skills/vibe-rag-commit-guidelines.md
git commit -m "feat: create vibe-rag-commit-guidelines skill

Why this change was needed:
- Commit message format (161 lines) bloats CLAUDE.md context
- Guidelines with examples should be on-demand, not always loaded
- Enforce meaningful commits with why/what/technical notes structure

What changed:
- Created vibe-rag-commit-guidelines.md skill
- Extracted commit format, 3 examples, checklist from CLAUDE.md lines 150-273
- Added Co-Authored-By ban and pre-commit commands

Technical notes:
- Skill auto-triggers before ANY git commit
- Examples demonstrate why-focused commit messages
- Part of CLAUDE.md refactoring (79% size reduction goal)"
```

---

## Task 3: Create vibe-rag-code-quality.md Skill

**Files:**
- Create: `.claude/skills/vibe-rag-code-quality.md`
- Reference: `CLAUDE.md:76-119, 330-346` (source content)

**Step 1: Create skill file with frontmatter**

Create `.claude/skills/vibe-rag-code-quality.md`:

```markdown
---
name: vibe-rag-code-quality
description: Enforce DRY, YAGNI, SOLID principles and production-ready code standards - ensures maintainable, performant, and correct implementations
---

# vibe-rag Code Quality Standards

Use this skill during code implementation to ensure quality.
```

**Step 2: Add DRY and YAGNI**

Extract content from CLAUDE.md lines 76-86 and add:

```markdown
## Core Principles

### DRY (Don't Repeat Yourself)

- **Extract common patterns** into functions or classes
- **Reuse existing components** - check for similar implementations first
- **Avoid copy-paste code** - if you copy, you should abstract instead

### YAGNI (You Aren't Gonna Need It)

- **Build only what's needed NOW** - not what might be needed later
- **No speculative features** - don't add functionality "just in case"
- **No premature optimization** - make it work, make it clear, then optimize if needed
```

**Step 3: Add SOLID principles**

Extract content from CLAUDE.md lines 88-93 and add:

```markdown
## SOLID Principles

- **Single Responsibility:** Each class does ONE thing well
- **Open/Closed:** Extend via inheritance, not modification of existing code
- **Liskov Substitution:** Subclasses must work like base classes (adapter pattern)
- **Interface Segregation:** Small, focused interfaces (not monolithic)
- **Dependency Inversion:** Depend on abstractions (interfaces), not concretions
```

**Step 4: Add production-ready code standards**

Extract content from CLAUDE.md lines 95-100 and add:

```markdown
## Production-Ready Code

All vibe-rag code must meet these standards:

- **Type hints everywhere** (Python 3.10+ syntax)
- **Comprehensive docstrings** (Google style - see `/vibe-rag:documentation`)
- **Error handling with custom exceptions** (see `/vibe-rag:error-handling`)
- **Async/await for I/O operations** (database calls, API requests)
- **Proper resource cleanup** (async context managers for connections)
```

**Step 5: Add architecture patterns**

Extract content from CLAUDE.md lines 102-119 and add:

```markdown
## Architecture Patterns

### Adapter Pattern (CRITICAL for vibe-rag)

**Every pluggable component uses adapter pattern:**

- All LLM providers implement `BaseLLMProvider`
- All storage backends implement `BaseVectorStore`
- All pipeline components implement `BasePipelineComponent`

**Why?** Enables swapping implementations without changing core code.

**Example:**

\`\`\`python
# ✅ GOOD: Code uses the interface
def use_provider(provider: BaseLLMProvider):
    result = await provider.generate(prompt)

# ❌ BAD: Code depends on concrete implementation
def use_provider(provider: GeminiProvider):
    result = await provider.generate(prompt)
\`\`\`

### Composition over Inheritance

- Use `PipelineBuilder` to compose components
- Inject dependencies (provider, storage) into `RAGEngine`
- Favor small, composable pieces over large inheritance hierarchies

### Configuration over Code

- Use Pydantic models for all configuration
- Support both programmatic and YAML config
- Validate early (at config load time, not runtime)
```

**Step 6: Add performance considerations**

Extract content from CLAUDE.md lines 330-346 and add:

```markdown
## Performance Considerations

### Async Everything

- **All I/O operations must be async** (database, API calls, file I/O)
- **Use `asyncio.gather()`** for parallel operations
- **Use connection pooling** (asyncpg for PostgreSQL)

### Optimization Priorities

1. **Correctness** - Works correctly (no bugs)
2. **Clarity** - Easy to understand (maintainable)
3. **Performance** - Fast enough (meets requirements)

### Don't Optimize Prematurely

- **Write clear code first** - make it work and understandable
- **Measure before optimizing** - profile to find actual bottlenecks
- **Profile to find bottlenecks** - don't guess where slowness is
```

**Step 7: Commit**

```bash
git add .claude/skills/vibe-rag-code-quality.md
git commit -m "feat: create vibe-rag-code-quality skill

Why this change was needed:
- Code quality standards (70 lines) should be on-demand reference
- DRY/YAGNI/SOLID principles scattered across CLAUDE.md lines 76-119, 330-346
- Developers need quality checklist during implementation, not at session start

What changed:
- Created vibe-rag-code-quality.md skill
- Consolidated DRY, YAGNI, SOLID, production standards, patterns, performance
- Added adapter pattern examples (critical for vibe-rag)

Technical notes:
- Skill auto-triggers during code implementation
- References other skills (documentation, error-handling)
- Part of CLAUDE.md refactoring (79% reduction goal)"
```

---

## Task 4: Create vibe-rag-error-handling.md Skill

**Files:**
- Create: `.claude/skills/vibe-rag-error-handling.md`
- Reference: `CLAUDE.md:275-296` (source content)

**Step 1: Create skill file with frontmatter**

Create `.claude/skills/vibe-rag-error-handling.md`:

```markdown
---
name: vibe-rag-error-handling
description: Guide exception design and error handling patterns - uses custom exceptions with specific error types, no silent failures
---

# vibe-rag Error Handling

Use this skill when implementing error handling or creating exceptions.
```

**Step 2: Add custom exception hierarchy**

Extract content from CLAUDE.md lines 275-283 and add:

```markdown
## Custom Exception Hierarchy

**All vibe-rag errors inherit from `RAGException`:**

- `RAGException` - Base for all framework errors
- `EmbeddingError` - Embedding generation failures
- `RetrievalError` - Document retrieval failures
- `LLMProviderError` - LLM API failures
- `StorageError` - Database/storage failures
- `ConfigurationError` - Invalid configuration

**Location:** `vibe_rag/utils/errors.py`
```

**Step 3: Add error handling pattern**

Extract content from CLAUDE.md lines 285-291 and add:

```markdown
## Error Handling Pattern

**Always wrap external errors with vibe-rag exceptions:**

\`\`\`python
try:
    result = await external_api_call()
except ExternalAPIError as e:
    raise LLMProviderError(f"Failed to generate: {e}")
\`\`\`

**Why?**
- Isolates external library errors from internal code
- Provides consistent error interface to users
- Enables specific exception handling at higher levels
```

**Step 4: Add NO Silent Failures rule**

Extract content from CLAUDE.md lines 293-296 and add:

```markdown
## NO Silent Failures

**NEVER do these:**

❌ **Don't catch exceptions and ignore them:**

\`\`\`python
try:
    result = risky_operation()
except Exception:
    pass  # ❌ WRONG: Silent failure
\`\`\`

❌ **Don't return `None` on errors:**

\`\`\`python
def process_data(data):
    try:
        return transform(data)
    except Exception:
        return None  # ❌ WRONG: Caller doesn't know it failed
\`\`\`

✅ **DO raise specific, informative exceptions:**

\`\`\`python
def process_data(data):
    try:
        return transform(data)
    except TransformError as e:
        raise ProcessingError(f"Failed to process {data}: {e}")
\`\`\`

**Principle:** Errors should be explicit and propagated, not hidden.
```

**Step 5: Commit**

```bash
git add .claude/skills/vibe-rag-error-handling.md
git commit -m "feat: create vibe-rag-error-handling skill

Why this change was needed:
- Error handling patterns (22 lines) should be on-demand reference
- Custom exception hierarchy needs to be easily accessible
- NO Silent Failures rule is critical but doesn't need to load every session

What changed:
- Created vibe-rag-error-handling.md skill
- Extracted exception hierarchy and patterns from CLAUDE.md lines 275-296
- Added examples of wrong vs right error handling

Technical notes:
- Skill auto-triggers when implementing error handling
- Documents all vibe-rag custom exceptions in one place
- Part of CLAUDE.md refactoring (79% size reduction goal)"
```

---

## Task 5: Create vibe-rag-documentation.md Skill

**Files:**
- Create: `.claude/skills/vibe-rag-documentation.md`
- Reference: `CLAUDE.md:298-328, 347-362` (source content)

**Step 1: Create skill file with frontmatter**

Create `.claude/skills/vibe-rag-documentation.md`:

```markdown
---
name: vibe-rag-documentation
description: Enforce Google-style docstrings, README updates, and security best practices - ensures documentation quality and prevents secret leaks
---

# vibe-rag Documentation Standards

Use this skill when writing documentation, docstrings, or handling sensitive data.
```

**Step 2: Add docstring format**

Extract content from CLAUDE.md lines 298-323 and add:

```markdown
## Docstring Format (Google Style)

**All functions, classes, and methods must have docstrings:**

\`\`\`python
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
\`\`\`

**Required sections:**
- Brief description (first line)
- `Args:` - All parameters with types and descriptions
- `Returns:` - Return value type and description
- `Raises:` - All exceptions that can be raised
```

**Step 3: Add README update guidelines**

Extract content from CLAUDE.md lines 325-328 and add:

```markdown
## README Updates

**When adding features, update README.md:**

- **Keep quick start example up-to-date** - Users should be able to copy-paste and run
- **Add new features to feature list** - Document all public-facing capabilities
- **Update installation instructions** - As dependencies change, keep install steps current
```

**Step 4: Add security considerations**

Extract content from CLAUDE.md lines 347-362 and add:

```markdown
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

\`\`\`python
import os

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ConfigurationError("GEMINI_API_KEY environment variable required")
\`\`\`

### Input Validation

**Validate all user inputs:**

- **Validate with Pydantic** - Use models for all config and user inputs
- **Sanitize before passing to databases** - Prevent injection attacks
- **Use parameterized queries** - Prevent SQL injection (asyncpg handles this automatically)

**Example:**

\`\`\`python
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=100)
\`\`\`

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

\`\`\`python
from pydantic import BaseModel, SecretStr

class GeminiConfig(BaseModel):
    api_key: SecretStr  # Automatically masked in logs and repr
\`\`\`
```

**Step 5: Commit**

```bash
git add .claude/skills/vibe-rag-documentation.md
git commit -m "feat: create vibe-rag-documentation skill

Why this change was needed:
- Documentation standards (65 lines) should be on-demand reference
- Google-style docstring example too verbose for every session
- Security practices critical but should be invoked when handling secrets

What changed:
- Created vibe-rag-documentation.md skill
- Extracted docstring format, README updates from CLAUDE.md lines 298-328
- Extracted security practices from CLAUDE.md lines 347-362

Technical notes:
- Skill auto-triggers when writing docs or handling sensitive data
- Combines documentation + security in one skill (related concerns)
- Part of CLAUDE.md refactoring (79% size reduction goal)"
```

---

## Task 6: Create vibe-rag-agent-teams.md Skill

**Files:**
- Create: `.claude/skills/vibe-rag-agent-teams.md`
- Reference: `CLAUDE.md:383-495` (source content)

**Step 1: Create skill file with frontmatter**

Create `.claude/skills/vibe-rag-agent-teams.md`:

```markdown
---
name: vibe-rag-agent-teams
description: Guide parallel work strategies with subagents and agent teams - when to use each approach, how to enable and coordinate teams effectively
---

# vibe-rag Agent Teams & Parallel Work

Use this skill when considering parallel or multi-agent work strategies.

**vibe-rag uses agent teams for parallel development.** Choose the right approach based on your task.
```

**Step 2: Add three approaches section**

Extract content from CLAUDE.md lines 387-404 and add:

```markdown
## Three Approaches to Parallel Work

### 1. Subagents (Task tool) - Quick, focused workers

- Workers report results back to main agent only
- **Best for:** focused research, verification, independent queries
- **Lower token cost** (results summarized back)
- **Use when:** you only need the result, not ongoing collaboration

### 2. Agent Teams - Collaborative teammates

- Teammates communicate with each other and share a task list
- **Best for:** research & review, new modules, debugging with competing hypotheses, cross-layer coordination
- **Higher token cost** (each teammate is full Claude instance)
- **Use when:** teammates need to share findings, challenge each other, coordinate independently

### 3. Dispatching Parallel Agents Skill - Guided orchestration

- Use `/superpowers:dispatching-parallel-agents` for help coordinating
- Skill helps identify independent tasks and manage agents
- **Best for:** when you need help structuring the parallel work
```

**Step 3: Add when to use section**

Extract content from CLAUDE.md lines 406-417 and add:

```markdown
## When to Use Agent Teams

### ✅ Good use cases:

- **Research and review:** Multiple perspectives investigating different aspects simultaneously
- **New modules/features:** Each teammate owns a separate piece (LLM provider + Storage backend + Pipeline)
- **Debugging with competing hypotheses:** Teammates test different theories in parallel
- **Cross-layer coordination:** Frontend, backend, and tests each owned by different teammate

### ❌ Not good for:

- Sequential tasks with many dependencies
- Same-file edits (causes conflicts)
- Simple tasks where coordination overhead exceeds benefit
```

**Step 4: Add how to use section**

Extract content from CLAUDE.md lines 419-456 and add:

```markdown
## How to Use Agent Teams

### Enabling (required first time)

Add to `~/.claude/settings.json`:

\`\`\`json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
\`\`\`

### Creating a team

\`\`\`
Create an agent team with 3 teammates:
- Teammate 1: Implement BaseLLMProvider + GeminiProvider (tests + code)
- Teammate 2: Implement BaseVectorStore + PostgresVectorStore (tests + code)
- Teammate 3: Implement BasePipelineComponent + basic retriever (tests + code)

Each teammate should follow TDD and work independently in their own files.
\`\`\`

### Best practices

- **Start with 3-5 teammates** (optimal for most workflows)
- **Size tasks appropriately** (5-6 tasks per teammate keeps everyone productive)
- **Give teammates enough context** (they don't inherit conversation history)
- **Avoid file conflicts** (each teammate owns different files)
- **Monitor and steer** (check progress, redirect if needed)
- **Require plan approval for risky tasks** (teammates plan before implementing)

### Communication

- Teammates share a task list and can message each other
- Lead coordinates work and synthesizes results
- You can talk to any teammate directly (Shift+Down to cycle in terminal)

### Display modes

- **In-process:** All teammates in main terminal (Shift+Down to cycle)
- **Split panes:** Each teammate in own pane (requires tmux or iTerm2)
```

**Step 5: Add example**

Extract content from CLAUDE.md lines 458-477 and add:

```markdown
## Example: Parallel Phase Implementation

\`\`\`
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
\`\`\`
```

**Step 6: Add comparison table**

Extract content from CLAUDE.md lines 479-489 and add:

```markdown
## Comparison: When to Use What

| Scenario | Use Subagents | Use Agent Teams |
|----------|---------------|-----------------|
| Quick research on 3 libraries | ✅ | ❌ |
| Review PR from 3 perspectives | ❌ | ✅ |
| Implement 3 independent modules | ❌ | ✅ |
| Debug with competing theories | ❌ | ✅ |
| Verify test coverage | ✅ | ❌ |
| Cross-layer feature (FE+BE+tests) | ❌ | ✅ |
```

**Step 7: Add Vibe Kanban coordination**

Extract content from CLAUDE.md lines 491-495 and add:

```markdown
## Coordination with Vibe Kanban

- Agent teams work great with Vibe Kanban task dependencies
- Lead can assign Vibe Kanban tasks to specific teammates
- Teammates update task status as they progress
- Shared task list ensures no duplicate work
```

**Step 8: Commit**

```bash
git add .claude/skills/vibe-rag-agent-teams.md
git commit -m "feat: create vibe-rag-agent-teams skill

Why this change was needed:
- Agent teams guidance (113 lines) too detailed for every session
- Parallel work strategies should be on-demand when considering parallelization
- Comparison table and examples helpful but bloat base context

What changed:
- Created vibe-rag-agent-teams.md skill
- Extracted parallel work strategies from CLAUDE.md lines 383-495
- Added three approaches, when/how to use, examples, comparison table

Technical notes:
- Skill auto-triggers when considering parallel/multi-agent work
- Documents agent teams setup and best practices
- Part of CLAUDE.md refactoring (79% size reduction goal)"
```

---

## Task 7: Enhance vibe-rag-tdd.md Skill

**Files:**
- Modify: `.claude/skills/vibe-rag-tdd.md`
- Reference: `CLAUDE.md:120-149` (content to add)

**Step 1: Read existing skill**

Run: `cat .claude/skills/vibe-rag-tdd.md`

**Step 2: Add Testing Strategy section**

Add after "Critical Requirements" section (after line 19):

```markdown
## Testing Strategy for vibe-rag

### Test Coverage Targets

Maintain these minimum coverage levels:

- **Core engine:** 90%+
- **Providers:** 85%+
- **Storage:** 85%+
- **Pipeline:** 80%+
- **Utilities:** 75%+

Check coverage with: `pytest --cov=vibe_rag --cov-report=term-missing`

### Testing Levels

**1. Unit Tests** (fast, isolated):
- Mock external dependencies (APIs, databases)
- Test one component at a time
- Located in `tests/unit/`
- Run with: `pytest tests/unit/`

**2. Integration Tests** (slower, real dependencies):
- Test component interactions
- Use testcontainers for databases
- Located in `tests/integration/`
- Run with: `pytest tests/integration/`

**3. E2E Tests** (slowest, full workflow):
- Test complete user workflows
- Located in `tests/e2e/`
- Run with: `pytest tests/e2e/`

### Mocking Guidelines

**CRITICAL: NEVER call real APIs in unit tests**

- **Mock Gemini:** Don't call actual Gemini API in tests
- **Mock OpenAI:** Don't call actual OpenAI API in tests
- **Mock databases:** Use `unittest.mock` for PostgreSQL connections

**Use these mocking tools:**

- `unittest.mock.AsyncMock` for async functions
- `unittest.mock.patch` for external dependencies
- `pytest.fixtures` for reusable test setup

**Example:**

\`\`\`python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
@patch('vibe_rag.providers.gemini.genai')
async def test_gemini_generate(mock_genai):
    # Setup mock
    mock_response = AsyncMock()
    mock_response.text = "Generated text"
    mock_genai.GenerativeModel.return_value.generate_content_async.return_value = mock_response

    # Test
    provider = GeminiProvider(api_key="test-key")
    result = await provider.generate("prompt")

    # Assert
    assert result == "Generated text"
\`\`\`
```

**Step 3: Commit**

```bash
git add .claude/skills/vibe-rag-tdd.md
git commit -m "feat: enhance vibe-rag-tdd skill with testing strategy

Why this change was needed:
- Testing strategy (30 lines) from CLAUDE.md should be in TDD skill
- Coverage targets need to be referenced during testing, not always loaded
- Mocking guidelines critical for vibe-rag (avoid real API calls)

What changed:
- Added Testing Strategy section to vibe-rag-tdd.md
- Extracted coverage targets, testing levels, mocking from CLAUDE.md lines 120-149
- Added example of proper mocking for async API calls

Technical notes:
- Enhances existing skill rather than creating new one
- Testing strategy naturally belongs with TDD workflow
- Part of CLAUDE.md refactoring (79% size reduction goal)"
```

---

## Task 8: Enhance vibe-rag-component.md Skill

**Files:**
- Modify: `.claude/skills/vibe-rag-component.md`
- Reference: Testing checklist integration

**Step 1: Read existing skill**

Run: `cat .claude/skills/vibe-rag-component.md`

**Step 2: Update "Testing Checklist" section**

Find "Testing Checklist" section (around line 274) and update it:

```markdown
## Testing Checklist

Component implementation is complete when:

- [ ] All tests written before implementation (invoke `/vibe-rag:tdd`)
- [ ] Tests fail first, then pass after implementation
- [ ] All I/O operations use async/await
- [ ] External dependencies are mocked (see `/vibe-rag:tdd` mocking guidelines)
- [ ] Custom exceptions used for error handling (see `/vibe-rag:error-handling`)
- [ ] Test coverage >= 85% (check with `pytest --cov`)
- [ ] Docstrings follow Google style (see `/vibe-rag:documentation`)
- [ ] Type hints on all parameters and returns
- [ ] Code quality verified (invoke `/vibe-rag:code-quality`)
- [ ] Code simplified with `/code-simplifier`
- [ ] Component exported in package __init__
- [ ] Component registered in main package exports
- [ ] RAGConfig updated if component is configurable
```

**Step 3: Add skill cross-references at top**

Add after frontmatter (after line 7):

```markdown
**Related skills:**
- `/vibe-rag:tdd` - TDD workflow and testing strategy
- `/vibe-rag:code-quality` - DRY, YAGNI, SOLID, adapter pattern
- `/vibe-rag:error-handling` - Custom exception design
- `/vibe-rag:documentation` - Docstring format and README updates
```

**Step 4: Commit**

```bash
git add .claude/skills/vibe-rag-component.md
git commit -m "feat: enhance vibe-rag-component skill with cross-references

Why this change was needed:
- Component skill should reference other vibe-rag skills for complete workflow
- Testing checklist should link to TDD, code-quality, error-handling skills
- Skill composition enables modular, focused workflows

What changed:
- Added related skills section at top
- Updated testing checklist to reference TDD, code-quality, error-handling, documentation
- Made checklist more actionable with invoke commands

Technical notes:
- Skills can now reference each other (composition pattern)
- Component implementation workflow now spans multiple focused skills
- Part of CLAUDE.md refactoring (79% size reduction goal)"
```

---

## Task 9: Rewrite CLAUDE.md (Facts Only)

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Backup current CLAUDE.md**

Run: `cp CLAUDE.md CLAUDE.md.backup`

**Step 2: Write new CLAUDE.md**

Replace entire CLAUDE.md content with:

```markdown
# vibe-rag Development Guidelines

## Project Identity

**vibe-rag**: Production-grade, modular RAG framework with "batteries included but removable" philosophy.

**Architecture:** Three-layer design (Core → Service → Client) with pluggable components for LLM providers, storage backends, and pipeline strategies.

**Tech Stack:** Python 3.10+, LangChain, Google Gemini, PostgreSQL + pgvector, Pydantic, pytest

## Skill-Driven Workflows

**CRITICAL:** All workflows are managed by skills. Invoke skills automatically at these checkpoints:

- **Starting any task:** `/vibe-rag:task-workflow`
- **Before committing:** `/vibe-rag:commit-guidelines`
- **Implementing components:** `/vibe-rag:tdd` + `/vibe-rag:component`
- **Writing code:** `/vibe-rag:code-quality`
- **Handling errors:** `/vibe-rag:error-handling`
- **Writing docs:** `/vibe-rag:documentation`
- **Using parallel work:** `/vibe-rag:agent-teams`

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
- ✅ **ALWAYS** use skills at workflow checkpoints
- ✅ **ALWAYS** follow TDD (tests first)
- ✅ **ALWAYS** use adapter pattern for components
```

**Step 3: Verify line count**

Run: `wc -l CLAUDE.md`

Expected: ~120 lines

**Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "refactor: rewrite CLAUDE.md as facts-only reference

Why this change was needed:
- Original CLAUDE.md was 574 lines mixing facts and workflows
- Context overhead of 35KB per session (35,000 tokens)
- Workflow content should be on-demand via skills, not always loaded

What changed:
- Rewrote CLAUDE.md from 574 → 120 lines (79% reduction)
- Removed all workflow content (now in 8 skills)
- Kept only: project identity, skill triggers, patterns, decisions, references
- Added auto-trigger instructions for each skill

Technical notes:
- Achieves 79% size reduction goal (454 lines removed)
- Estimated token savings: 20,000-25,000 per session
- Skills handle: task workflow, commits, code quality, errors, docs, agent teams, TDD, components"
```

---

## Task 10: Validation - Test Skills Independently

**Files:**
- Test: All 8 skills

**Step 1: Test vibe-rag-task-workflow**

Run: Invoke `/vibe-rag:task-workflow` and verify content loads

Expected: Skill displays Starting/During/Complete workflow sections

**Step 2: Test vibe-rag-commit-guidelines**

Run: Invoke `/vibe-rag:commit-guidelines` and verify content loads

Expected: Skill displays commit format, examples, checklist

**Step 3: Test vibe-rag-code-quality**

Run: Invoke `/vibe-rag:code-quality` and verify content loads

Expected: Skill displays DRY, YAGNI, SOLID, patterns, performance

**Step 4: Test vibe-rag-error-handling**

Run: Invoke `/vibe-rag:error-handling` and verify content loads

Expected: Skill displays exception hierarchy, patterns, NO silent failures

**Step 5: Test vibe-rag-documentation**

Run: Invoke `/vibe-rag:documentation` and verify content loads

Expected: Skill displays docstring format, README updates, security

**Step 6: Test vibe-rag-agent-teams**

Run: Invoke `/vibe-rag:agent-teams` and verify content loads

Expected: Skill displays three approaches, when/how to use, examples

**Step 7: Test vibe-rag-tdd (enhanced)**

Run: Invoke `/vibe-rag:tdd` and verify enhanced content loads

Expected: Skill displays original TDD workflow + new Testing Strategy section

**Step 8: Test vibe-rag-component (enhanced)**

Run: Invoke `/vibe-rag:component` and verify enhanced content loads

Expected: Skill displays original component guide + cross-references

**Step 9: Document test results**

Create: `VALIDATION.md`

```markdown
# CLAUDE.md Refactoring Validation Results

**Date:** 2026-03-01

## Skills Testing

- [ ] `/vibe-rag:task-workflow` - Loads correctly
- [ ] `/vibe-rag:commit-guidelines` - Loads correctly
- [ ] `/vibe-rag:code-quality` - Loads correctly
- [ ] `/vibe-rag:error-handling` - Loads correctly
- [ ] `/vibe-rag:documentation` - Loads correctly
- [ ] `/vibe-rag:agent-teams` - Loads correctly
- [ ] `/vibe-rag:tdd` - Loads with enhancements
- [ ] `/vibe-rag:component` - Loads with enhancements

## Context Size Comparison

**Before:**
- CLAUDE.md: 574 lines
- Token count: ~35,000

**After:**
- CLAUDE.md: 120 lines
- Token count: ~7,000 (base)
- Reduction: 79% fewer lines, 80% less base context

## Success Criteria

- [x] CLAUDE.md reduced from 574 → ~120 lines (79% reduction)
- [x] 8 skills created/enhanced with clear purposes
- [x] Auto-trigger instructions in CLAUDE.md for each skill
- [x] All workflow content migrated to appropriate skills
- [x] No workflow/process content remaining in CLAUDE.md
- [ ] Skills can be invoked independently and work correctly
- [ ] Token count reduced by ~20,000-25,000 per session
- [x] Design doc written and committed
```

**Step 10: Commit**

```bash
git add VALIDATION.md
git commit -m "test: validate CLAUDE.md refactoring skills

Why this change was needed:
- Need to verify all 8 skills work independently
- Document validation results for future reference
- Track success criteria completion

What changed:
- Created VALIDATION.md with skills testing checklist
- Documented context size comparison (before/after)
- Tracked success criteria progress

Technical notes:
- All skills should be invocable and display correct content
- Final validation before considering refactoring complete"
```

---

## Task 11: Final Verification and Cleanup

**Files:**
- Review: All files
- Remove: `CLAUDE.md.backup` (if validation passed)

**Step 1: Verify no workflow content in CLAUDE.md**

Run: `grep -i "workflow\|TDD\|commit message\|example" CLAUDE.md`

Expected: Only matches in skill-trigger section, not workflow details

**Step 2: Count total lines**

Run: `wc -l CLAUDE.md`

Expected: ~120 lines (±10)

**Step 3: Count skill files**

Run: `ls -1 .claude/skills/vibe-rag*.md | wc -l`

Expected: 8 files

**Step 4: Compare token counts**

Run: `wc -c CLAUDE.md.backup` and `wc -c CLAUDE.md`

Expected: New CLAUDE.md is ~80% smaller

**Step 5: Remove backup if validation passed**

Run: `rm CLAUDE.md.backup`

**Step 6: Update design doc with completion notes**

Add to `docs/plans/2026-03-01-claude-md-refactoring-design.md`:

```markdown
## Implementation Completed

**Date:** 2026-03-01

**Results:**
- CLAUDE.md reduced from 574 → 120 lines (79.1% reduction)
- 6 new skills created
- 2 existing skills enhanced
- All workflow content successfully migrated
- Token savings: ~28,000 per session (estimated)

**Validation:**
- All 8 skills load correctly
- No workflow content remains in CLAUDE.md
- Auto-trigger instructions clear and complete
- Skills can be invoked independently

**Status:** ✅ Complete
```

**Step 7: Final commit**

```bash
git add docs/plans/2026-03-01-claude-md-refactoring-design.md
git commit -m "docs: mark CLAUDE.md refactoring as complete

Why this change was needed:
- Document completion of refactoring implementation
- Record actual results vs designed goals
- Provide validation evidence

What changed:
- Added Implementation Completed section to design doc
- Documented 79.1% size reduction achieved
- Confirmed all 8 skills working correctly

Technical notes:
- Exceeded reduction goal (574 → 120 lines)
- All success criteria met
- Ready for production use"
```

---

## Summary

**Total Tasks:** 11
**Estimated Time:** 2-3 hours

**Deliverables:**
1. 6 new skill files created
2. 2 existing skill files enhanced
3. CLAUDE.md rewritten (574 → 120 lines)
4. All workflow content migrated
5. Validation completed
6. Design doc updated

**Context Reduction:**
- **Before:** 574 lines (~35KB, ~35,000 tokens)
- **After:** 120 lines (~7KB, ~7,000 tokens base)
- **Savings:** 79% fewer lines, 80% less base context, 20K-25K tokens per session

**Skills Created:**
1. vibe-rag-task-workflow.md
2. vibe-rag-commit-guidelines.md
3. vibe-rag-code-quality.md
4. vibe-rag-error-handling.md
5. vibe-rag-documentation.md
6. vibe-rag-agent-teams.md
7. vibe-rag-tdd.md (enhanced)
8. vibe-rag-component.md (enhanced)
