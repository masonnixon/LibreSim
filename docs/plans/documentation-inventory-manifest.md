# Documentation Inventory Manifest

- **Recorded:** 2026-07-21
- **Repository:** `/home/mason/repos/LibreSim.git`
- **Plan:** `docs/plans/documentation-consolidation-and-purge.md`, checklist 1.1

## Scope

This manifest records project-authored documentation and documentation-like
assets by Git state before the consolidation begins. Third-party dependency
documentation and generated cache/build documentation are not listed file by
file; those complete generated families are counted separately below.

The path inventory was recorded first. The reference map added during
checklist item 1.3 appears below the hash register.

Documentation ownership is shared by the LibreSim maintainers. Generated
codegen-report ownership additionally belongs to `scripts/validate_codegen.py`
and the two CI pipelines that publish its output.

## SHA-256 hash register — checklist item 1.2

These hashes identify the documents selected for merge, comparison, or
historical retention. They are a pre-migration baseline; any content merge or
rewrite must produce a new hash and an explicit diff review.

| SHA-256 | Path |
|---|---|
| `960968dde673e0d4e2018ed531279960b4afb7f269fb22d4aec726bdabae3829` | `.claude/docs/coverage-100-plan.md` |
| `51ea78e45238dd24eb1c02461a43eeec99dbc230b4724ee2384a6f72b7a62895` | `.claude/docs/coverage-100-remaining-checklist.md` |
| `89215f92a66dacebb610657efa1fcd9a2e58b101dd813ed3af28dc97e6f602d4` | `.claude/docs/fable-audit-2026-07-07.md` |
| `dfff4177e2259b060f93a9b3d39d8a84de120426f74e7172285aeb38b3a9a436` | `.claude/docs/fable-audit-remediation-status-2026-07-10.md` |
| `05daa3b6e3cdc8efb3929445fd11474616d33210ff52c7dde1863453891c376f` | `.claude/docs/fable-audit-remediation-status-2026-07-16.md` |
| `37d5e709f38338e9584f215d7d01f8d815ea654d822437ee27a7f7dbbebf312c` | `codegen_verification/IMPROVEMENT_PLAN.md` |
| `76debbf791f14ff828fd06463c9d22882ab99786d747d982a0f4892cb6f22bf8` | `codegen_verification/VERIFICATION_REPORT.md` |
| `a94835a7ed048a4fc8177613b355ef07c314fc8a13cc5382eaef07ecd022a28c` | `docs/codegen-validation-report.md` |
| `7b845ded88d7f5e1ab79c1d91b1027aebf8eb266376a40d3935df98a8ccc4e72` | `docs/plans/completed/codegen-validation-report.md` |
| `264421c7f963222b465bce77bf5fe3a111c562447cb2f71ee7fd7b8f11e71b5a` | `docs/plans/completed/SQA.md` |
| `7870a2f35fe3a8f79d2d9d5b76f71b0b0e64ca290cde5524db0037dc4f3d00c8` | `docs/refs/testing.md` |
| `d19fddc94926e1462374d9c502f09ea5943d197e2d700b347af134be874d7186` | `.claude/context.md` |

## Reference map — checklist item 1.3

The pre-migration `rg` scan covered tracked and ignored workspace files while
excluding Git internals, dependency trees, and generated build output. It
found 67 matches. References in the consolidation plan and this inventory are
intentional disposition records; all other consumers are listed here.

| Source family | Consumers identified |
|---|---|
| `docs/codegen-validation-report.md` | `scripts/validate_codegen.py`, `.github/workflows/ci.yml`, `.gitlab-ci.yml`, `docs/refs/testing.md`, `docs/plans/refactoring-recommendations.md`, `docs/plans/completed/codegen-validation-report.md`, `docs/plans/completed/fable-audit-completion.md`, `docs/plans/completed/simulation-correctness-remediation.md` |
| `codegen_verification/VERIFICATION_REPORT.md`, `IMPROVEMENT_PLAN.md` | `docs/refs/testing.md`, `docs/plans/refactoring-recommendations.md` |
| `docs/refs/` | the six guides in that directory plus inventory/plan path records; links move with the directory |
| `.claude/docs/fable-audit*.md` | `docs/plans/completed/fable-audit-completion.md`, `docs/plans/completed/simulation-correctness-remediation.md` |
| `.claude/docs/coverage-100*.md` | inventory/plan records only; checklist facts will be merged into the completed coverage plan |
| `docs/plans/completed/SQA.md` | no external consumer beyond inventory/plan records; content overlaps `docs/refs/testing.md` |
| `docs/kf_eg_screenshot.PNG`, `.claude/docs/hermes-codex-config-with-docker.toml` | no code, CI, or Markdown consumers |

The transient scan output is intentionally not a project artifact.

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
