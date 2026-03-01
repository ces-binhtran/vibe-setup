---
name: vibe-rag-code-quality
description: Enforce DRY, YAGNI, SOLID principles and production-ready code standards - ensures maintainable, performant, and correct implementations
---

# vibe-rag Code Quality Standards

Use this skill during code implementation to ensure quality.

## Core Principles

### DRY (Don't Repeat Yourself)

- **Extract common patterns** into functions or classes
- **Reuse existing components** - check for similar implementations first
- **Avoid copy-paste code** - if you copy, you should abstract instead

### YAGNI (You Aren't Gonna Need It)

- **Build only what's needed NOW** - not what might be needed later
- **No speculative features** - don't add functionality "just in case"
- **No premature optimization** - make it work, make it clear, then optimize if needed

## SOLID Principles

- **Single Responsibility:** Each class does ONE thing well
- **Open/Closed:** Extend via inheritance, not modification of existing code
- **Liskov Substitution:** Subclasses must work like base classes (adapter pattern)
- **Interface Segregation:** Small, focused interfaces (not monolithic)
- **Dependency Inversion:** Depend on abstractions (interfaces), not concretions

## Production-Ready Code

All vibe-rag code must meet these standards:

- **Type hints everywhere** (Python 3.10+ syntax)
- **Comprehensive docstrings** (Google style - see `/vibe-rag:documentation`)
- **Error handling with custom exceptions** (see `/vibe-rag:error-handling`)
- **Async/await for I/O operations** (database calls, API requests)
- **Proper resource cleanup** (async context managers for connections)

## Architecture Patterns

### Adapter Pattern (CRITICAL for vibe-rag)

**Every pluggable component uses adapter pattern:**

- All LLM providers implement `BaseLLMProvider`
- All storage backends implement `BaseVectorStore`
- All pipeline components implement `BasePipelineComponent`

**Why?** Enables swapping implementations without changing core code.

**Example:**

```python
# ✅ GOOD: Code uses the interface
def use_provider(provider: BaseLLMProvider):
    result = await provider.generate(prompt)

# ❌ BAD: Code depends on concrete implementation
def use_provider(provider: GeminiProvider):
    result = await provider.generate(prompt)
```

### Composition over Inheritance

- Use `PipelineBuilder` to compose components
- Inject dependencies (provider, storage) into `RAGEngine`
- Favor small, composable pieces over large inheritance hierarchies

### Configuration over Code

- Use Pydantic models for all configuration
- Support both programmatic and YAML config
- Validate early (at config load time, not runtime)

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
