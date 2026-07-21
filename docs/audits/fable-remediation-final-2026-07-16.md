# LibreSim Fable Audit — Final Remediation Status

**Date:** 2026-07-16
**Branch:** `fable-audit-plan`
**Clean validation commit:** `6e7f690e60acea827398887c73197219690082cc`
**FAC-9 closeout commit:** `15b54a9`
**FAC-10 archive commit:** `1b97a8b`

## Outcome

The Fable audit is complete. FAC-0 through FAC-10 and LS-1 through LS-10 satisfy their
recorded acceptance criteria. The original remediation plan, FAC-9 design, and audit
completion plan are archived under `docs/plans/completed/`.

The 2026-07-10 status remains unchanged as a historical checkpoint; it must not be read
as the final branch state.

## Clean-checkout verification

A detached worktree at `6e7f690e60acea827398887c73197219690082cc` was clean before
the matrix. The validator rewrote `docs/reports/codegen-validation-report.md` byte-identically,
and `git status --short` remained empty after all gates.

| Gate | Final result |
|---|---|
| Backend pytest | 2,185 passed, 1 skipped, 2 warnings |
| Backend Ruff | All checks passed |
| Backend mypy | No issues in 138 source files |
| Frontend Vitest | 664 passed in 14 files |
| Frontend ESLint | Passed with zero warnings allowed |
| Frontend TypeScript | `tsc --noEmit` passed |
| Canonical numerical subset | 33 passed, 1 warning |
| Generated-code validator | 156/156 passed; 0 simulation, build, run, or output-validation failures |

The single skip is the optional external Windows-path MDL fixture in
`test_crosstalk_bug.py`; the file is not part of this checkout. The backend warnings are
the existing Starlette `TestClient` deprecation and a pytest return-value warning in
`test_create_model`; neither gate failed.

Commands were the FAC-0 matrix from the completed audit plan. Every Docker invocation
used `DOCKER_HOST=unix:///run/docker.sock`; backend test commands mounted the repository
examples at `/examples`, and the validator used the CI-equivalent nested Docker setup
with identical host/container repository paths.

## Toolchain

- Docker 29.5.2, build 79eb04c
- Docker Compose 5.1.4
- Python 3.11.15
- pytest 9.1.1
- Ruff 0.15.22
- mypy 2.3.0
- Node 18.20.8
- npm 10.8.2
- Vitest 1.6.1
- ESLint 8.57.1
- TypeScript 5.9.3

## Remediation ledger

- LS-1: `09552bd`
- LS-2: `88fcf73`
- LS-3: `9efe204`, `a2cfd1c`
- LS-4: `15fa0bd`, `d0d3382`
- LS-5: `896f0ff`, `b5e4bfa`
- LS-6: `2b79fcb`, `5ed9bdf`
- LS-7: `230086b`, `3f07404`
- LS-8: `e75e26c`, `570d036`, `cd0f509`
- LS-9: `c28fee1`, `2172fa0`, `043a29a`, `24741bf`
- LS-10/FAC-9: `e536fb4`, `16c97ab`, `f3051b9`, `41d257e`, `9d4531a`,
  `68eee69`, `a450f20`, `ec15bb1`, `70dbd33`, `e33a9fd`, `66cadc0`,
  `3898ed5`, `959e8aa`, `5cde103`, `cc0fc70`, `4df7b63`, `e00ba89`,
  `6e7f690`, `15b54a9`

The complete FAC-1 through FAC-8 commit ledger remains in
`docs/plans/completed/fable-audit-completion.md`.

## Approved residual boundaries

- `State.*` and `Sim.*` remain temporary compatibility facades for external/custom
  callers. Built-in correctness uses explicit `SimContext` ownership. Removal requires
  separate maintainer approval under
  `docs/plans/sim-state-compatibility-facade-deprecation.md`.
- The concurrent-session registry is intentionally process-local and bounded. A
  multi-worker deployment requires sticky routing; a distributed registry was an
  explicit FAC-9 non-goal.
- `docs/plans/refactoring-recommendations.md` remains active and was not conflated with
  correctness remediation.

These boundaries were part of the maintainer-approved FAC-9 design and do not leave an
unmet Fable audit acceptance criterion.
