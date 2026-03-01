---
name: vibe-rag-task-workflow
description: Complete workflow for task execution from start to finish - ensures brainstorming, TDD, proper commits, and verification before completion
---

**Note:** This skill is loaded via file read (`.claude/skills/vibe-rag-task-workflow.md`) because Claude Code does not support project-local skill registration.

# vibe-rag Task Workflow

Use this skill when starting ANY task or before marking a task complete.

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

## During Implementation

1. **Follow TDD religiously** - Read `.claude/skills/vibe-rag-tdd.md`
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
6. **Use parallel agents when beneficial** - Read `.claude/skills/vibe-rag-agent-teams.md` for guidance

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
6. **Update documentation** - Read `.claude/skills/vibe-rag-documentation.md` if needed
7. **Commit all changes** - Read `.claude/skills/vibe-rag-commit-guidelines.md`
8. **Use `/superpowers:verification-before-completion`** - Final check

## Common Pitfalls to Avoid

❌ **Skip brainstorming** → Leads to wrong implementations
❌ **Skip tests** → Introduces bugs
❌ **Over-engineer** → YAGNI violation
❌ **Copy-paste code** → DRY violation
❌ **Ignore dependencies** → Build in wrong order
❌ **Skip documentation** → No one knows how to use it
❌ **Commit broken code** → Breaks main branch

✅ **DO: Brainstorm → TDD → Small commits → Verify → Complete**

## Questions? Ask!

- Unclear requirements? **Ask before coding**
- Multiple approaches? **Present options with tradeoffs**
- Uncertain about design? **Use `/superpowers:brainstorming` skill**
- Blocked by dependencies? **Clarify and document**

**Remember:** Senior engineers think deeply, ask questions, and deliver quality over speed.
