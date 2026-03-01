# pyproject.toml Setup Design

**Date:** 2026-03-01
**Project:** vibe-rag
**Task:** Create pyproject.toml with dependencies
**Status:** Approved

## Overview

This document outlines the design for creating the initial `pyproject.toml` file for the vibe-rag project. This file establishes Python packaging configuration, dependency management, and development tool settings.

## Design Decision

**Approach:** Use the implementation plan template directly (Option 1)

**Rationale:**
- The implementation plan already contains a carefully designed pyproject.toml template
- All dependencies have been vetted against the architecture requirements
- Follows modern Python packaging best practices (PEP 517/518)
- Provides one-time setup vs. incremental updates
- Aligns with existing design documents

## Package Metadata & Build System

### Build System
- **Backend:** `setuptools.build_meta`
- **Requirements:** `setuptools>=68.0`, `wheel`
- **Standard:** PEP 517/518 compliant

### Package Information
- **Name:** vibe-rag
- **Version:** 0.1.0 (initial development)
- **Author:** Binh Tran (congbinh24k@gmail.com)
- **License:** MIT
- **Python Requirement:** >=3.10 (required for modern type hints like `list[str]`)
- **Description:** Production-grade modular RAG framework

## Dependencies

### Core Runtime Dependencies

The following dependencies are required for the framework to function:

1. **LangChain Ecosystem:**
   - `langchain>=0.1.0` - Core RAG framework foundation
   - `langchain-google-genai>=1.0.0` - Gemini LLM provider integration
   - `langchain-core>=0.1.0` - Core abstractions and interfaces

2. **Database & Vector Storage:**
   - `psycopg[binary]>=3.1.0` - Modern async PostgreSQL driver
   - `pgvector>=0.2.0` - PostgreSQL vector similarity extension

3. **Data Validation & Settings:**
   - `pydantic>=2.0.0` - Data validation and modeling
   - `pydantic-settings>=2.0.0` - Environment-based settings management

4. **Utilities:**
   - `numpy>=1.24.0` - Array operations for embedding vectors
   - `python-dotenv>=1.0.0` - Environment variable loading from .env files

### Development Dependencies (Optional)

Development tools are optional dependencies to keep production installs lean:

1. **Testing:**
   - `pytest>=7.0.0` - Testing framework
   - `pytest-asyncio>=0.21.0` - Async test support (critical for async RAG operations)
   - `pytest-cov>=4.0.0` - Test coverage reporting

2. **Code Quality:**
   - `black>=23.0.0` - Code formatting
   - `ruff>=0.1.0` - Fast Python linting
   - `mypy>=1.0.0` - Static type checking

### Optional Feature Dependencies

1. **LangGraph Integration:**
   - `langgraph>=0.1.0` - For agentic RAG module (future Phase 3)

2. **All Dependencies:**
   - `all` - Meta-package to install everything (dev + langgraph)

## Tool Configurations

### pytest Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
asyncio_mode = "auto"
```

**Key Settings:**
- **testpaths:** Look for tests in `tests/` directory
- **File/Function patterns:** Standard pytest naming conventions
- **asyncio_mode = "auto":** Automatically handle async tests (critical for async RAG engine)

### black Configuration

```toml
[tool.black]
line-length = 100
target-version = ['py310']
```

**Key Settings:**
- **100 character line length:** Modern standard, balances readability and screen width
- **Target Python 3.10+:** Ensures compatibility with project requirements

### ruff Configuration

```toml
[tool.ruff]
line-length = 100
target-version = "py310"
```

**Key Settings:**
- **Line length matches black:** Ensures consistency between formatter and linter
- **Python 3.10 target:** Aligns with project requirements

## Installation Modes

The pyproject.toml supports multiple installation modes:

```bash
# Basic installation (runtime dependencies only)
pip install vibe-rag

# Development installation (includes testing and code quality tools)
pip install vibe-rag[dev]

# LangGraph support (includes langgraph integration)
pip install vibe-rag[langgraph]

# Everything (all optional dependencies)
pip install vibe-rag[all]

# Editable development installation
pip install -e ".[dev]"
```

## Acceptance Criteria

1. ✅ pyproject.toml exists in project root
2. ✅ All dependencies specified match architecture design
3. ✅ `pip install -e .` works without errors
4. ✅ Tool configurations (pytest, black, ruff) are properly defined
5. ✅ Author information correctly set to Binh Tran

## Implementation Notes

- The pyproject.toml will be created based on the template in the implementation plan (lines 40-94)
- Only modifications: Update author information
- After creation, verify with: `pip install -e .`
- This establishes the foundation for all subsequent development tasks

## References

- Implementation Plan: `docs/plans/2026-02-28-vibe-rag-implementation.md` (Task 1, Step 1)
- Architecture Design: `docs/plans/2026-02-28-rag-framework-design.md` (Section 11)
