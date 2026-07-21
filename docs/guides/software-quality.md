# Software Quality Assurance (SQA) Guide

This document describes the SQA tools and practices used in the LibreSim project.

## Overview

LibreSim uses a comprehensive suite of SQA tools to maintain code quality:

| Tool | Purpose | Stage |
|------|---------|-------|
| **Ruff** | Python linting & formatting | Pre-commit, CI |
| **MyPy** | Python type checking | Pre-commit, CI |
| **Bandit** | Python security scanning | Pre-commit, CI |
| **ESLint** | TypeScript/JavaScript linting | Pre-commit, CI |
| **TypeScript** | Type checking | Pre-commit, CI |
| **Pytest** | Python testing with coverage | CI |
| **detect-secrets** | Secret detection | Pre-commit |

## Quick Start

### 1. Install Development Dependencies

```bash
# Backend (Python)
cd backend
pip install -e ".[dev]"

# Frontend (Node.js)
cd frontend
npm install
```

### 2. Install Pre-commit Hooks

```bash
# From project root
pip install pre-commit
pre-commit install
```

This installs git hooks that automatically run checks before each commit.

### 3. Run Checks Manually

```bash
# Run all pre-commit hooks on all files
pre-commit run --all-files

# Run specific hooks
pre-commit run ruff --all-files
pre-commit run mypy --all-files
pre-commit run bandit --all-files
```

## Tool Details

### Ruff (Python Linting & Formatting)

Ruff is an extremely fast Python linter and formatter that replaces multiple tools (flake8, isort, black).

**Configuration:** `backend/pyproject.toml`

```bash
# Check for issues
cd backend
ruff check src/

# Auto-fix issues
ruff check src/ --fix

# Format code
ruff format src/
```

**Rule sets enabled:**
- `E`, `F`: PyFlakes and pycodestyle errors
- `I`: isort (import sorting)
- `B`: flake8-bugbear (common bugs)
- `UP`: pyupgrade (Python upgrade suggestions)
- `SIM`: flake8-simplify (code simplification)
- `N`, `W`: Naming and warnings

### MyPy (Type Checking)

MyPy performs static type analysis to catch type-related bugs.

**Configuration:** `backend/pyproject.toml`

```bash
cd backend
mypy src/
```

**Key settings:**
- `ignore_missing_imports = true`: Allows untyped third-party libraries
- `check_untyped_defs = true`: Checks inside untyped functions
- `strict_optional = true`: Enforces Optional type annotations

### Bandit (Security Scanning)

Bandit finds common security issues in Python code.

**Configuration:** `backend/pyproject.toml`

```bash
cd backend
bandit -r src/ -c pyproject.toml
```

**Excluded checks:**
- `B101`: assert_used (commonly used in tests)

### Pytest (Testing)

Pytest runs the test suite with coverage reporting.

**Configuration:** `backend/pyproject.toml`

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_blocks.py

# Run tests in parallel
pytest -n auto
```

**Coverage reports:**
- Terminal: Shows missing lines
- HTML: `backend/htmlcov/index.html`
- XML: `backend/coverage.xml` (for CI)

### ESLint (Frontend)

ESLint checks TypeScript/JavaScript code quality.

```bash
cd frontend
npm run lint
```

### TypeScript Compiler

TypeScript checks type correctness without emitting files.

```bash
cd frontend
npx tsc --noEmit
```

## GitLab CI Pipeline

The `.gitlab-ci.yml` file defines the CI/CD pipeline with these stages:

### Lint Stage
- `ruff-lint`: Python linting
- `ruff-format`: Python formatting check
- `eslint`: Frontend linting
- `typescript-check`: TypeScript type checking

### Test Stage
- `mypy`: Python type checking
- `pytest`: Python tests with coverage
- `frontend-test`: Frontend tests (when configured)

### Security Stage
- `bandit`: Security vulnerability scanning
- `dependency-check`: Python dependency audit
- `npm-audit`: Node.js dependency audit

### Build Stage
- `build-frontend`: Production frontend build
- `build-docker`: Docker image build (manual)

## Pre-commit Hooks

The `.pre-commit-config.yaml` configures hooks that run before each commit:

1. **Ruff lint & format** - Python code quality
2. **MyPy** - Python type checking
3. **Bandit** - Security scanning
4. **ESLint** - Frontend linting
5. **TSC** - TypeScript checking
6. **General checks**:
   - Large file detection
   - Merge conflict markers
   - YAML/JSON syntax
   - Trailing whitespace
   - End-of-file newlines
   - Debug statements
7. **detect-secrets** - Secret detection

### Bypassing Hooks (Use Sparingly)

```bash
# Skip all hooks for a single commit
git commit --no-verify -m "emergency fix"

# Skip specific hooks
SKIP=mypy git commit -m "message"
```

## Writing Tests

### Test File Structure

```
backend/tests/
├── __init__.py
├── conftest.py      # Shared fixtures
├── test_blocks.py   # Block tests
├── test_compiler.py # Compiler tests
└── test_api.py      # API endpoint tests
```

### Test Conventions

```python
# Use classes to group related tests
class TestConstantBlock:
    """Tests for the Constant block."""

    def test_constant_output(self):
        """Test that Constant block outputs the configured value."""
        const = Constant(value=5.0)
        assert const.getOutput() == 5.0

    def test_constant_string_value(self):
        """Test that Constant block parses string values."""
        const = Constant(value="3.14")
        assert const.getOutput() == pytest.approx(3.14)
```

### Using Fixtures

```python
# In conftest.py
@pytest.fixture
def sample_model():
    return {"id": "test", "blocks": [...]}

# In test file
def test_compile_model(sample_model):
    result = compiler.compile(sample_model)
    assert result.success
```

## Continuous Improvement

### Adding New Rules

To enable additional Ruff rules, edit `backend/pyproject.toml`:

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "N", "W", "NEW_RULE"]
```

### Increasing Coverage Threshold

Once test coverage improves, update the threshold:

```toml
[tool.coverage.report]
fail_under = 80  # Fail if coverage drops below 80%
```

### Adding Type Hints

Gradually add type hints to improve MyPy effectiveness:

```python
# Before
def process_block(block, config):
    ...

# After
def process_block(block: Block, config: SimulationConfig) -> ProcessResult:
    ...
```

## Troubleshooting

### Pre-commit hooks failing

```bash
# Update hooks to latest versions
pre-commit autoupdate

# Clear cache and reinstall
pre-commit clean
pre-commit install
```

### MyPy errors with third-party libraries

Add to `pyproject.toml`:
```toml
[[tool.mypy.overrides]]
module = "problematic_library.*"
ignore_missing_imports = true
```

### Tests not finding modules

Ensure the package is installed in development mode:
```bash
cd backend
pip install -e ".[dev]"
```
