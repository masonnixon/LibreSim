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
| **Tests Passing** | 1904 |
| **Overall Coverage** | 84% |
| **Test Framework** | pytest |

**High-coverage modules (>90%):**
- `src/codegen/languages/*/blocks/` - Code generation templates
- `src/osk/blocks/` - LibreSim simulation blocks
- `src/models/` - Pydantic data models
- `src/simulation/compiler.py` - Model compilation

**Lower-coverage modules (needs improvement):**
- `src/api/` - API routes (0% - need integration tests)
- `src/main.py` - Application entry point (0%)
- `src/simulation/runner.py` - Simulation runner (83%)
- `src/simulation/osk_adapter.py` - OSK adapter (76%)

### Frontend (TypeScript/React)

| Metric | Value |
|--------|-------|
| **Tests Passing** | 659 |
| **Overall Coverage** | 40% |
| **Test Framework** | Vitest |
| **Test Files** | 14 |

**High-coverage modules (90%+):**
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

**Moderate-coverage modules (50-85%):**
- `src/components/Editor/BlockNode.tsx` - Block node component (82%)
- `src/utils/mdlImporter.ts` - MDL import (74%)
- `src/components/Sidebar/Sidebar.tsx` - Block library sidebar (63%)

**Lower-coverage modules (needs improvement):**
- `src/components/Toolbar/Toolbar.tsx` - Toolbar (16% - complex component)
- `src/components/Editor/Editor.tsx` - Main editor (0% - requires ReactFlow mocking)
- `src/components/Editor/CustomEdge.tsx` - Edge routing (0% - requires ReactFlow mocking)
- `src/components/*/` - Modal components (0% - need component tests)

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

**Prerequisites:**
- Python 3.11+ with conda environment `libresim`
- Dependencies installed: `pip install -e ".[dev]"`

```bash
# Navigate to backend directory
cd backend

# Run all tests with coverage
/c/Users/Mason/anaconda3/envs/libresim/python.exe -m pytest tests/ -v

# Run with coverage report
/c/Users/Mason/anaconda3/envs/libresim/python.exe -m pytest tests/ --cov=src --cov-report=term-missing

# Run specific test file
/c/Users/Mason/anaconda3/envs/libresim/python.exe -m pytest tests/test_blocks.py -v

# Run specific test class
/c/Users/Mason/anaconda3/envs/libresim/python.exe -m pytest tests/test_blocks.py::TestGainBlock -v

# Run tests in parallel (faster)
/c/Users/Mason/anaconda3/envs/libresim/python.exe -m pytest tests/ -n auto
```

**Coverage Reports:**
- Terminal: Shows missing lines inline
- HTML: `backend/htmlcov/index.html`
- XML: `backend/coverage.xml` (for CI integration)

### Frontend Tests

**Prerequisites:**
- Docker Compose running (`docker compose up`)
- Frontend container must be active

```bash
# Run all tests
docker exec libresimgit-frontend-1 npm run test

# Run tests once (no watch mode)
docker exec libresimgit-frontend-1 npm run test:run

# Run with coverage
docker exec libresimgit-frontend-1 npm run test:coverage

# Run specific test file
docker exec libresimgit-frontend-1 npx vitest run src/store/modelStore.test.ts
```

**Note:** The host machine does not have Node.js installed. All frontend commands must run inside the Docker container.

### SQA Checks

**Backend:**
```bash
cd backend

# Linting
/c/Users/Mason/anaconda3/envs/libresim/python.exe -m ruff check src/ tests/

# Auto-fix lint issues
/c/Users/Mason/anaconda3/envs/libresim/python.exe -m ruff check src/ tests/ --fix

# Type checking
/c/Users/Mason/anaconda3/envs/libresim/python.exe -m mypy src/ --config-file=pyproject.toml

# Security scanning
/c/Users/Mason/anaconda3/envs/libresim/python.exe -m bandit -r src/ -c pyproject.toml
```

**Frontend:**
```bash
# ESLint
docker exec libresimgit-frontend-1 npm run lint

# TypeScript type checking
docker exec libresimgit-frontend-1 npx tsc --noEmit
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

Validation tests verify simulation accuracy against reference implementations (MATLAB/Simulink).

### Location
- `codegen_verification/` - Generated code validation
- `examples/` - Reference models with known outputs

### Running Validation
```bash
# Run codegen validation script
python scripts/validate_codegen.py

# Compare with reference outputs
python scripts/compare_gui_models.py
```

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
# Ensure package is installed in dev mode
cd backend
pip install -e ".[dev]"
```

### Frontend tests failing with "Cannot find module"
```bash
# Rebuild the container
docker compose down
docker compose up --build
```

### Coverage not updating
```bash
# Clear pytest cache
cd backend
rm -rf .pytest_cache htmlcov .coverage
```

### Pre-commit hooks failing
```bash
# Update hooks
pre-commit autoupdate

# Clear and reinstall
pre-commit clean
pre-commit install
```
