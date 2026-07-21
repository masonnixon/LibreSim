# Documentation Inventory Manifest

- **Recorded:** 2026-07-21
- **Repository:** `/home/mason/repos/LibreSim.git`
- **Plan:** `docs/plans/documentation-consolidation-and-purge.md`, checklist 1.1

## Scope

This manifest records project-authored documentation and documentation-like
assets by Git state before the consolidation begins. Third-party dependency
documentation and generated cache/build documentation are not listed file by
file; those complete generated families are counted separately below.

This step records paths only. Duplicate hashes and path references belong to
checklist items 1.2 and 1.3 and have intentionally not been collected here.

## Pre-manifest tracked durable documentation — 26 files

### Repository and special-location documents — 4

- `AGENTS.md`
- `LICENSE`
- `README.md`
- `examples/README.md`

### Tracked Claude-era documents — 3

- `.claude/context.md`
- `.claude/docs/coverage-100-plan.md`
- `.claude/docs/coverage-100-remaining-checklist.md`

### Codegen-verification documents outside docs — 2

- `codegen_verification/IMPROVEMENT_PLAN.md`
- `codegen_verification/VERIFICATION_REPORT.md`

### Current reports and assets — 2

- `docs/codegen-validation-report.md`
- `docs/kf_eg_screenshot.PNG`

### Active plans — 3

- `docs/plans/documentation-consolidation-and-purge.md`
- `docs/plans/refactoring-recommendations.md`
- `docs/plans/sim-state-compatibility-facade-deprecation.md`

### Completed plans and historical reports — 6

- `docs/plans/completed/SQA.md`
- `docs/plans/completed/codegen-validation-report.md`
- `docs/plans/completed/control-analysis-visualization-design.md`
- `docs/plans/completed/fable-audit-completion.md`
- `docs/plans/completed/fac-9-sim-context-concurrency.md`
- `docs/plans/completed/simulation-correctness-remediation.md`

### Reference guides — 6

- `docs/refs/adding-new-plot-types.md`
- `docs/refs/blockset-development-guide.md`
- `docs/refs/libresim-coder.md`
- `docs/refs/mdl-format-reference.md`
- `docs/refs/running-headless.md`
- `docs/refs/testing.md`

## Ignored project-authored documentation/configuration — 4 files

- `.claude/docs/fable-audit-2026-07-07.md`
- `.claude/docs/fable-audit-remediation-status-2026-07-10.md`
- `.claude/docs/fable-audit-remediation-status-2026-07-16.md`
- `.claude/docs/hermes-codex-config-with-docker.toml`

The three Markdown files are durable audit records currently missing from
normal clones. The TOML file is machine-specific configuration included in the
manifest because it lives in the documentation staging directory; it is not a
candidate for durable project documentation.

## Untracked, nonignored durable documentation — 0 files

No durable documentation was untracked and nonignored when this manifest was
recorded. This manifest itself is added as the output of checklist item 1.1.

## Ignored generated documentation families

These are reproducible output, not durable project documentation:

- `codegen_verification/builds/`: 156 generated `README.md` files, 78 generated
  `CMakeLists.txt` files, and 39 generated `requirements.txt` files.
- Pytest caches: 2 generated `.pytest_cache/README.md` files.
- Coverage HTML, dependency documentation under `frontend/node_modules/`, and
  cache metadata are ignored generated or third-party trees and remain outside
  the consolidation inventory.

## Explicit non-documentation exclusions

- `backend/requirements.txt`: tracked dependency manifest.
- `.claude/settings.local.json`: ignored local agent configuration.
- Coverage JSON/XML, compiled output, databases, caches, and Python bytecode:
  generated artifacts rather than documentation.

## Reconciliation

- Preexisting tracked durable documentation: 26 files; this manifest becomes
  the 27th when committed.
- Ignored project-authored documentation/configuration: 4 files.
- Untracked nonignored durable documentation: 0 files before this manifest.
- Every durable candidate in the consolidation plan is represented above.
