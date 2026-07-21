# LibreSim Testing Guide

This document provides a comprehensive overview of testing in LibreSim, including how to run tests, current coverage status, and testing strategies.

## Test Categories

LibreSim employs three types of tests:

| Type | Purpose | Location |
|------|---------|----------|
| **Unit Tests** | Test individual functions, classes, and components in isolation | `backend/tests/`, `frontend/src/**/*.test.ts` |
| **SQA Tests** | Static analysis, linting, type checking, security scanning | Pre-commit hooks, CI pipeline |
| **Validation Tests** | End-to-end simulation accuracy against reference implementations | `codegen_verification/`, manual validation |

## Current Test Coverage Status

### Backend (Python)

| Metric | Value |
|--------|-------|
| **Tests Passing** | 3,769 |
| **Skipped** | 1 (documented external MDL fixture) |
| **Overall Coverage** | 100% statements / 100% branches |
| **Test Framework** | pytest |

All backend modules, including API routes, application entry points, codegen,
OSK blocks, and simulation services, are fully covered.

### Frontend (TypeScript/React)

| Metric | Value |
|--------|-------|
| **Tests Passing** | 962 |
| **Overall Coverage** | 100% statements / branches / functions / lines |
| **Test Framework** | Vitest |
| **Test Files** | 42 |
| **Measured Source Files** | 62 |

**Representative fully covered modules:**
- `src/blocks/` - Block definitions and registry (100%)
- `src/store/simulationStore.ts` - Simulation state management (100%)
- `src/store/uiStore.ts` - UI state management (100%)
- `src/types/` - TypeScript type definitions (100%)
- `src/utils/nanoid.ts` - ID generation (100%)
- `src/utils/mdlExporter.ts` - MDL export (100%)
- `src/components/Toast/Toast.tsx` - Toast notifications (100%)
- `src/api/client.ts` - API client (98%)
- `src/store/libraryStore.ts` - Library state management (92%)
- `src/store/modelStore.ts` - Model state management (88%)

**Additional fully covered modules:**
- `src/components/Editor/BlockNode.tsx` - Block node component (100%)
- `src/utils/mdlImporter.ts` - MDL import (100%)
- `src/components/Sidebar/Sidebar.tsx` - Block library sidebar (100%)

**No lower-coverage modules remain:**
- `src/components/Toolbar/Toolbar.tsx` - Toolbar (100%)
- `src/components/Editor/Editor.tsx` - Main editor (100%)
- `src/components/Editor/CustomEdge.tsx` - Edge routing (100%)
- `src/components/*/` - Modal components (100%)

**Test files:**
- `src/api/client.test.ts` - API client tests (36 tests)
- `src/blocks/index.test.ts` - Block registry tests
- `src/store/libraryStore.test.ts` - Library store tests
- `src/store/modelStore.test.ts` - Model store tests (156 tests)
- `src/store/simulationStore.test.ts` - Simulation store tests
- `src/store/uiStore.test.ts` - UI store tests
- `src/types/library.test.ts` - Type tests
- `src/utils/mdlExporter.test.ts` - MDL export tests
- `src/utils/mdlImporter.test.ts` - MDL import tests
- `src/utils/nanoid.test.ts` - ID generation tests
- `src/components/Editor/BlockNode.test.tsx` - Block node component tests (45 tests)
- `src/components/Toast/Toast.test.tsx` - Toast notification tests (14 tests)
- `src/components/Sidebar/Sidebar.test.tsx` - Sidebar component tests (16 tests)
- `src/components/Toolbar/Toolbar.test.tsx` - Toolbar component tests (27 tests)

## Running Tests

### Backend Tests

All project commands run in Docker. From the repository root:

```bash
# Complete backend suite with the permanent 100% gate
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps \
  -v "$PWD/examples:/examples:ro" backend sh -c \
  "pip install -q -e '.[dev]' && pytest tests/ -q"

# Focused backend test file
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps backend sh -c \
  "pip install -q -e '.[dev]' && pytest tests/test_blocks.py -q"
```

**Coverage Reports:**
- Terminal: Shows missing lines inline
- HTML: `backend/htmlcov/index.html`
- XML: `backend/coverage.xml` (for CI integration)

### Frontend Tests

```bash
# Run coverage (the 100% gate)
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend \
  npm run test:coverage

# Run a specific test file
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend \
  npx vitest run src/store/modelStore.test.ts
```

All frontend commands run inside the Docker container.

### SQA Checks

**Backend:**
```bash
# Linting
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps backend \
  ruff check src/ tests/

# Type checking
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps backend \
  mypy src/ --config-file=pyproject.toml

# Security scanning
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps backend \
  bandit -r src/ -c pyproject.toml
```

**Frontend:**
```bash
# ESLint
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend npm run lint

# TypeScript type checking
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend npm run typecheck
```

### Pre-commit Hooks

All SQA checks run automatically before each commit via pre-commit hooks:

```bash
# Install hooks (one-time setup)
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
```

## Test Configuration

### Backend (pytest)

Configuration in `backend/pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "-v --strict-markers --strict-config --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/__pycache__/*"]
```

### Frontend (Vitest)

Configuration in `frontend/vite.config.ts`:

```typescript
test: {
  globals: true,
  environment: 'jsdom',
  setupFiles: ['./src/test/setup.ts'],
  include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
  coverage: {
    provider: 'istanbul',
    reporter: ['text', 'json', 'html'],
    exclude: [
      'node_modules/',
      'src/test/',
      '**/*.d.ts',
      'src/main.tsx',
      'src/vite-env.d.ts',
    ],
    thresholds: { statements: 100, branches: 100, functions: 100, lines: 100 },
  },
}
```

## Writing Tests

### Backend Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py          # Shared pytest fixtures
├── test_blocks.py       # LibreSim block unit tests
├── test_codegen.py      # Code generation tests
└── test_simulation.py   # Simulation engine tests
```

**Example test:**
```python
import pytest
from src.osk.blocks.math_ops import Gain

class TestGainBlock:
    """Tests for the Gain block."""

    def test_gain_default_value(self):
        """Test Gain block with default value."""
        gain = Gain(value=2.0)
        gain.setInput(0, 5.0)
        gain.update(0.0)
        assert gain.getOutput(0) == 10.0

    def test_gain_negative(self):
        """Test Gain block with negative gain."""
        gain = Gain(value=-1.0)
        gain.setInput(0, 3.0)
        gain.update(0.0)
        assert gain.getOutput(0) == -3.0
```

### Frontend Test Structure

```
frontend/src/
├── test/
│   └── setup.ts              # Test setup (mocks)
├── api/
│   └── client.test.ts        # API client tests
├── store/
│   ├── modelStore.test.ts    # Store tests (156 tests)
│   ├── libraryStore.test.ts  # Library store tests
│   ├── simulationStore.test.ts
│   └── uiStore.test.ts
├── utils/
│   ├── mdlImporter.test.ts   # Utility tests
│   ├── mdlExporter.test.ts
│   └── nanoid.test.ts
└── components/
    ├── Editor/
    │   └── BlockNode.test.tsx    # Block node tests (45 tests)
    ├── Toast/
    │   └── Toast.test.tsx        # Toast tests (14 tests)
    ├── Sidebar/
    │   └── Sidebar.test.tsx      # Sidebar tests (16 tests)
    └── Toolbar/
        └── Toolbar.test.tsx      # Toolbar tests (27 tests)
```

**Example store test:**
```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { useModelStore } from './modelStore'

describe('modelStore', () => {
  beforeEach(() => {
    useModelStore.setState({ blocks: [], connections: [] })
  })

  it('should add a block', () => {
    const { addBlock } = useModelStore.getState()
    addBlock({ type: 'constant', position: { x: 0, y: 0 } })

    const { blocks } = useModelStore.getState()
    expect(blocks).toHaveLength(1)
    expect(blocks[0].type).toBe('constant')
  })
})
```

### React Component Testing Patterns

**Mocking Zustand stores:**
```typescript
import { vi } from 'vitest'

vi.mock('../../store/uiStore', () => ({
  useUIStore: vi.fn(),
}))

const mockedUseUIStore = vi.mocked(useUIStore)
mockedUseUIStore.mockReturnValue({
  sidebarCollapsed: false,
  toggleSidebar: vi.fn(),
})
```

**Mocking useSyncExternalStore (stable references required):**
```typescript
// IMPORTANT: Return stable reference to avoid infinite re-render loop
const emptyArray: never[] = []
vi.mock('../../blocks', () => ({
  blockRegistry: {
    getLibraryBlocks: () => emptyArray,  // Same reference each call
    subscribe: vi.fn(() => () => {}),
  },
}))
```

**Mocking drag events with dataTransfer:**
```typescript
const dataTransfer = { effectAllowed: '', setData: vi.fn() }
fireEvent.dragStart(element, { dataTransfer })
expect(dataTransfer.effectAllowed).toBe('move')
```

**Module state isolation with vi.resetModules():**
```typescript
beforeEach(async () => {
  vi.resetModules()
  const module = await import('./Toast')
  toast = module.toast
})
```

## Validation Tests

Validation tests verify that generated code produces correct simulation results.

### Location
- `scripts/validate_codegen.py` - Official validation against headless simulation
- `codegen_verification/compare_languages.py` - Cross-language consistency check
- `codegen_verification/builds/` - Built examples with results
- `examples/` - Reference models

### Two Validation Approaches

| Approach | Script | Purpose | Tolerance | Status |
|----------|--------|---------|-----------|--------|
| **Official Validation** | `scripts/validate_codegen.py` | Compare generated code vs LibreSim headless simulation | 3% (final values) | 100% PASS |
| **Cross-Language Check** | `codegen_verification/compare_languages.py` | Compare C vs C++ vs Python vs Rust | 0.01% (full series) | 46% PASS |

**Official Validation** is the ground truth test. It verifies that generated code produces the same
results as running the model in the LibreSim GUI/headless simulation.

**Cross-Language Check** is a stricter consistency test. Some numerical drift between languages
is expected due to floating-point precision differences, but significant structural differences
(like missing outputs) indicate bugs.

### Running Validation

```bash
# Official validation (must pass 100%)
python scripts/validate_codegen.py

# Cross-language consistency (informational)
cd codegen_verification
python compare_languages.py --tolerance 1e-4

# With looser tolerance matching official validation
python compare_languages.py --tolerance 0.03
```

### Validation Reports
- `docs/codegen-validation-report.md` - Official validation results
- `codegen_verification/VERIFICATION_REPORT.md` - Cross-language comparison
- `codegen_verification/IMPROVEMENT_PLAN.md` - Plan to address discrepancies

## Continuous Integration

Tests run automatically in CI on:
- Pull requests
- Pushes to main branch

### CI Stages
1. **Lint** - Ruff, ESLint, TypeScript
2. **Test** - pytest (backend), Vitest (frontend)
3. **Security** - Bandit, dependency audits
4. **Build** - Production builds

## Troubleshooting

### Backend tests not finding modules
```bash
# Reinstall the backend package and run a focused import-bearing test
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps backend sh -c \
  "pip install -q -e '.[dev]' && pytest tests/test_blocks.py -q"
```

### Frontend tests failing with "Cannot find module"
```bash
# Rebuild the container
DOCKER_HOST=unix:///run/docker.sock docker compose down
DOCKER_HOST=unix:///run/docker.sock docker compose up --build
```

### Coverage not updating
```bash
# Reset coverage data and pytest's cache inside the project container
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps backend sh -c \
  "coverage erase && pytest --cache-clear --collect-only -q"
```

### Pre-commit hooks failing
```bash
# Update hooks
pre-commit autoupdate

# Clear and reinstall
pre-commit clean
pre-commit install
```
