# pyproject.toml Setup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create pyproject.toml with all required dependencies and tool configurations, verify installation works.

**Architecture:** Modern Python packaging using PEP 517/518 with setuptools backend. Dependencies organized into core runtime, development tools, and optional features.

**Tech Stack:** Python 3.10+, setuptools, pytest, black, ruff, mypy

---

## Task 1: Create pyproject.toml

**Files:**
- Create: `pyproject.toml`

**Step 1: Create pyproject.toml with complete configuration**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "vibe-rag"
version = "0.1.0"
description = "Production-grade modular RAG framework"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Binh Tran", email = "congbinh24k@gmail.com"}
]

dependencies = [
    "langchain>=0.1.0",
    "langchain-google-genai>=1.0.0",
    "langchain-core>=0.1.0",
    "psycopg[binary]>=3.1.0",
    "pgvector>=0.2.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "numpy>=1.24.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
langgraph = [
    "langgraph>=0.1.0",
]
all = ["vibe-rag[dev,langgraph]"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
asyncio_mode = "auto"

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
target-version = "py310"
```

**Step 2: Verify file was created correctly**

Run: `cat pyproject.toml | head -20`
Expected: Should see `[build-system]` and `[project]` sections with correct author info

**Step 3: Commit pyproject.toml**

```bash
git add pyproject.toml
git commit -m "feat: create pyproject.toml with dependencies and tool configs

Why this change was needed:
- Establish Python package structure for vibe-rag framework
- Define all runtime and development dependencies
- Configure development tools (pytest, black, ruff) with consistent settings
- Enable editable installation for development workflow

What changed:
- Created pyproject.toml using modern PEP 517/518 format
- Added core dependencies: langchain, gemini, psycopg, pgvector, pydantic
- Added dev dependencies: pytest, black, ruff, mypy
- Configured pytest for async test support
- Set 100-char line length for black and ruff

Technical notes:
- Python 3.10+ required for modern type hints (list[str], dict[str, Any])
- asyncio_mode=auto handles async tests without decorators
- Optional dependencies keep production installs lean
- psycopg[binary] includes compiled C extensions for performance"
```

---

## Task 2: Verify Installation Works

**Files:**
- Test: `pyproject.toml`

**Step 1: Create virtual environment (if needed)**

Run: `python3 --version`
Expected: Python 3.10 or higher

Note: If no venv exists, create one:
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

**Step 2: Install package in editable mode**

Run: `pip install -e .`
Expected: Should install all core dependencies without errors. Look for:
- "Successfully installed langchain..."
- "Successfully installed pydantic..."
- "Successfully installed psycopg..."
- No error messages

**Step 3: Verify core dependencies are installed**

Run: `pip list | grep -E "(langchain|pydantic|psycopg|pgvector)"`
Expected: Should see all core packages listed with versions

**Step 4: Install dev dependencies**

Run: `pip install -e ".[dev]"`
Expected: Should install pytest, black, ruff, mypy without errors

**Step 5: Verify dev tools work**

Run: `pytest --version && black --version && ruff --version && mypy --version`
Expected: All tools should report their versions without errors

**Step 6: Document successful installation**

No commit needed - verification complete.

---

## Summary

After completing these tasks:

1. ✅ `pyproject.toml` exists with all dependencies
2. ✅ File is committed to git
3. ✅ `pip install -e .` works without errors
4. ✅ Core dependencies are installed
5. ✅ Dev dependencies are installed
6. ✅ All dev tools are functional

**Acceptance criteria met:** pyproject.toml exists and `pip install -e .` works.

---

## Notes

- This establishes the foundation for all subsequent development
- No Python code is written yet - this is pure packaging setup
- Next tasks will create the actual package structure (vibe_rag/__init__.py, etc.)
- The implementation plan (docs/plans/2026-02-28-vibe-rag-implementation.md) has full project setup in Task 1
