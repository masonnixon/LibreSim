# Test Coverage Report

**Date:** July 21, 2026  
**Branch:** `fable-audit-plan`  
**Commit:** `647baac`

Fresh full-suite coverage runs report 100% coverage for the configured backend and frontend production source sets.

## Results

| Area | Test files | Tests | Result | Coverage |
|---|---:|---:|---|---|
| Backend | 61 | 3,770 | 3,769 passed, 1 skipped | 100% statements and branches |
| Frontend | 42 | 962 | 962 passed | 100% statements, branches, functions, and lines |
| GUI stack regression | 1 | 2 | 2 passed | End-to-end; not separately instrumented |
| **Total** | **104** | **4,734** | **4,733 passed, 1 skipped, 0 failed** | **100% of configured production code** |

## Coverage Counters

- Backend: 15,901 of 15,901 statements and 4,542 of 4,542 branches covered.
- Frontend: 4,892 of 4,892 statements, 3,378 of 3,378 branches, 1,011 of 1,011 functions, and 4,355 of 4,355 lines covered.
- Combined: 20,793 covered statements and 7,920 covered branches.

Coverage excludes test code, generated reports, TypeScript declaration files, test infrastructure, and other files excluded by the project coverage configurations. The GUI stack tests exercise example loading and a sine-wave-to-scope simulation through the deployed frontend proxy. The run emitted one Starlette/httpx deprecation warning and had no test failures.
