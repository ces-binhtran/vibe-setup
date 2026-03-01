---
name: vibe-rag-agent-teams
description: Guide parallel work strategies with subagents and agent teams - when to use each approach, how to enable and coordinate teams effectively
---

# vibe-rag Agent Teams & Parallel Work

Use this skill when considering parallel or multi-agent work strategies.

**vibe-rag uses agent teams for parallel development.** Choose the right approach based on your task.

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

## How to Use Agent Teams

### Enabling (required first time)

Add to `~/.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### Creating a team

```
Create an agent team with 3 teammates:
- Teammate 1: Implement BaseLLMProvider + GeminiProvider (tests + code)
- Teammate 2: Implement BaseVectorStore + PostgresVectorStore (tests + code)
- Teammate 3: Implement BasePipelineComponent + basic retriever (tests + code)

Each teammate should follow TDD and work independently in their own files.
```

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

## Example: Parallel Phase Implementation

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

## Comparison: When to Use What

| Scenario | Use Subagents | Use Agent Teams |
|----------|---------------|-----------------|
| Quick research on 3 libraries | ✅ | ❌ |
| Review PR from 3 perspectives | ❌ | ✅ |
| Implement 3 independent modules | ❌ | ✅ |
| Debug with competing theories | ❌ | ✅ |
| Verify test coverage | ✅ | ❌ |
| Cross-layer feature (FE+BE+tests) | ❌ | ✅ |

## Coordination with Vibe Kanban

- Agent teams work great with Vibe Kanban task dependencies
- Lead can assign Vibe Kanban tasks to specific teammates
- Teammates update task status as they progress
- Shared task list ensures no duplicate work
