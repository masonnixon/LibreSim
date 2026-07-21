# Documentation Consolidation and Purge Plan

## Goal

Make `docs/` the single home for durable LibreSim documentation, with a clear
index and lifecycle for active guidance, plans, completed work, audits, reports,
and historical material. Remove redundant or generated files only after their
unique information and consumers have been identified.

This plan does not move or delete files by itself. Every purge is gated by a
content comparison, reference scan, and maintainer decision.

## Special-location exceptions

These files should remain outside `docs/` because repository conventions or
runtime behavior depend on their locations:

- `README.md`: repository landing page.
- `LICENSE`: standard repository-root license location.
- `AGENTS.md`: agent instructions discovered from the repository root.
- `examples/README.md`: served by `backend/src/main.py` and asserted by API
  tests.
- Dependency manifests such as `backend/requirements.txt`: not documentation.

## Proposed structure

```text
docs/
├── README.md
├── refs/
│   ├── adding-new-plot-types.md
│   ├── blockset-development-guide.md
│   ├── libresim-coder.md
│   ├── mdl-format-reference.md
│   ├── running-headless.md
│   ├── software-quality.md          # decision: merge into testing instead
│   └── testing.md
├── plans/
│   ├── documentation-consolidation-and-purge.md
│   ├── refactoring-recommendations.md
│   ├── sim-state-compatibility-facade-deprecation.md
│   └── completed/
│       ├── coverage-100.md
│       ├── control-analysis-visualization-design.md
│       ├── fable-audit-completion.md
│       ├── fac-9-sim-context-concurrency.md
│       └── simulation-correctness-remediation.md
├── audits/
│   ├── fable-2026-07-07.md
│   ├── fable-remediation-checkpoint-2026-07-10.md
│   └── fable-remediation-final-2026-07-16.md
├── reports/
│   ├── codegen-validation-report.md # generated canonical report, if tracked
│   └── archive/
│       ├── codegen-validation-2026-01-21.md
│       └── codegen-cross-language-consistency-2026-01-21.md
├── assets/
└── archive/
    └── legacy-project-context-2026-01.md  # only if retained
```

## Disposition inventory

| Current path | Proposed disposition | Target or prerequisite |
|---|---|---|
| `.claude/docs/coverage-100-plan.md` | Move and rename | `docs/plans/completed/coverage-100.md` |
| `.claude/docs/coverage-100-remaining-checklist.md` | Merge, then purge | Append unique closeout evidence to `coverage-100.md` first |
| `.claude/docs/fable-audit-2026-07-07.md` | Move and begin tracking | `docs/audits/fable-2026-07-07.md` |
| `.claude/docs/fable-audit-remediation-status-2026-07-10.md` | Move and begin tracking | `docs/audits/fable-remediation-checkpoint-2026-07-10.md` |
| `.claude/docs/fable-audit-remediation-status-2026-07-16.md` | Move and begin tracking | `docs/audits/fable-remediation-final-2026-07-16.md` |
| `.claude/docs/hermes-codex-config-with-docker.toml` | Purge from repository workspace | Machine-specific Codex/Hermes configuration; retain privately if needed |
| `.claude/context.md` | Decision: archive or purge | Audit unique durable decisions before acting |
| `codegen_verification/VERIFICATION_REPORT.md` | Move/archive | `docs/reports/archive/codegen-cross-language-consistency-2026-01-21.md` |
| `codegen_verification/IMPROVEMENT_PLAN.md` | Merge, then purge | Preserve unique outcomes in the archived consistency report |
| `docs/plans/completed/codegen-validation-report.md` | Move/archive | It is a historical report, not a completed plan |
| `docs/codegen-validation-report.md` | Decision: keep tracked or make CI artifact | Producer and all references must change atomically if moved/untracked |
| `docs/plans/completed/SQA.md` | Merge or rename | Merge nonduplicated material into `testing.md`, or create `software-quality.md` |
| `docs/kf_eg_screenshot.PNG` | Decision: retain under assets or purge | It currently appears unreferenced; visually inspect before deciding |
| `docs/refs/*.md` | Keep, then freshness-audit | Durable user/developer guidance |
| `docs/plans/refactoring-recommendations.md` | Keep active | Repair stale `docs/SQA.md` and `docs/testing.md` links |
| `docs/plans/sim-state-compatibility-facade-deprecation.md` | Keep active | Reassess completion separately from this reorganization |
| `docs/plans/completed/*.md` remediation/design files | Keep | Historical implementation and acceptance evidence |
| Backend `coverage*.json`, frontend coverage directories | Purge generated workspace artifacts | Add appropriately scoped ignore patterns after confirming no consumer |
| Cache/build documentation inside ignored output directories | Purge with generated output | Never treat generated README files as project docs |

## Known reference and tooling dependencies

- Completed Fable/remediation plans currently reference ignored
  `.claude/docs` audit files. Moving those audits into tracked `docs/audits/`
  fixes a portability defect, but all references must be updated together.
- `docs/plans/refactoring-recommendations.md` names nonexistent
  `docs/SQA.md` and `docs/testing.md`; the actual files are currently under
  `docs/plans/completed/` and `docs/refs/`.
- `scripts/validate_codegen.py` writes
  `docs/codegen-validation-report.md`. Moving that generated report requires
  coordinated changes to the script, both CI pipelines, testing guidance, and
  completed plans that cite it.
- `docs/refs/testing.md` references both files under
  `codegen_verification/`; those links must follow any archive move.
- `examples/README.md` cannot move without changing the API implementation and
  its tests.
- The three ignored Fable audit/status files are absent from normal clones;
  moving them under `docs/` should use explicit adds so they become tracked.

## Decisions to settle before execution

- [ ] **D1 — Legacy context:** archive `.claude/context.md` under
  `docs/archive/`, or purge it after extracting any unique decisions?
- [ ] **D2 — SQA material:** merge `SQA.md` into `docs/refs/testing.md`, or
  retain a separate `docs/refs/software-quality.md`?
- [ ] **D3 — Generated validation report:** keep
  `docs/codegen-validation-report.md` tracked at its current stable path, move
  it to `docs/reports/`, or stop tracking it and publish it only as a CI
  artifact?
- [ ] **D4 — Historical checkpoint depth:** retain both the 2026-07-10
  checkpoint and 2026-07-16 final Fable status, or merge the checkpoint's
  unique evidence into the final status and purge it?
- [ ] **D5 — Screenshot:** retain `docs/kf_eg_screenshot.PNG` under
  `docs/assets/` with a documented consumer, or purge it as orphaned?
- [ ] **D6 — Directory naming:** keep the established `docs/refs/` name, or
  rename it to `docs/guides/` and accept the larger link migration?

## Execution checklist

### 1. Freeze the inventory and establish safety

- [ ] Record a complete tracked, ignored, and untracked documentation manifest.
- [ ] Record SHA-256 hashes for files being merged or considered duplicates.
- [ ] Identify every code, CI, and Markdown reference to each source path.
- [ ] Confirm the worktree contains no unrelated staged changes.
- [ ] Create one migration branch/commit series; do not mix product behavior
  changes into documentation commits.

Acceptance: every candidate has an owner, disposition, target, and reference
list before any move or purge.

### 2. Create the documentation spine

- [ ] Add `docs/README.md` as the documentation index.
- [ ] Explain the roles of `refs/`, active `plans/`, `plans/completed/`,
  `audits/`, `reports/`, `assets/`, and `archive/`.
- [ ] Link the root `README.md` to `docs/README.md` without duplicating its
  quick-start content.
- [ ] Add lifecycle rules: active plan, completed plan, generated report,
  historical report, audit record, and purge eligibility.

Acceptance: a reader can discover every durable document from one index and
knows where new documentation belongs.

### 3. Consolidate the completed coverage work

- [ ] Move `.claude/docs/coverage-100-plan.md` to
  `docs/plans/completed/coverage-100.md` with Git history preserved.
- [ ] Add a closeout appendix containing the checklist's unique final counts,
  gates, verification commands, and commit IDs.
- [ ] Verify every checklist fact against current configs and coverage
  artifacts.
- [ ] Remove the standalone completed checklist only after the appendix is
  reviewed.
- [ ] Update all references to both old `.claude/docs` paths.

Acceptance: no coverage history or verification evidence is lost, and no
tracked coverage documentation remains under `.claude/docs/`.

### 4. Consolidate the Fable audit trail

- [ ] Move the original audit and both remediation status files into
  `docs/audits/` using the agreed names.
- [ ] Ensure the previously ignored files become tracked.
- [ ] Add clear `original`, `historical checkpoint`, and `final` labels.
- [ ] Apply decision D4 without discarding unique acceptance evidence.
- [ ] Update links in `simulation-correctness-remediation.md`,
  `fable-audit-completion.md`, and any other referring documents.

Acceptance: a clean clone contains the complete audit trail and all links
resolve within `docs/`.

### 5. Consolidate software-quality guidance

- [ ] Compare `docs/plans/completed/SQA.md` section-by-section with
  `docs/refs/testing.md`.
- [ ] Extract unique lint, type-check, security, pre-commit, and CI guidance.
- [ ] Apply decision D2: merge into `testing.md` or create
  `software-quality.md`.
- [ ] Remove duplicated setup and stale host-specific commands.
- [ ] Remove `SQA.md` from completed plans only after all unique material is
  retained.
- [ ] Repair the stale references in `refactoring-recommendations.md`.

Acceptance: one authoritative location documents each quality command and the
obsolete SQA file is gone.

### 6. Consolidate code-generation reports

- [ ] Compare the canonical generated validation report, historical completed
  report, cross-language report, and improvement plan.
- [ ] Date historical reports from their own metadata or Git history.
- [ ] Merge unique completion notes from `IMPROVEMENT_PLAN.md` into the archived
  cross-language report, then remove the redundant plan.
- [ ] Move the historical completed-plan report into `docs/reports/archive/`.
- [ ] Apply decision D3 atomically across `scripts/validate_codegen.py`, GitHub
  Actions, GitLab CI, testing guidance, and completed-plan links.
- [ ] Preserve the generated report's reproducibility and CI visibility.

Acceptance: reports are classified as current/generated or historical, no
planning document remains in a data-output directory, and validation tooling
still writes and publishes the expected report.

### 7. Resolve legacy context, assets, and machine-specific files

- [ ] Audit `.claude/context.md` for decisions not present in current docs.
- [ ] Apply decision D1: extract and archive, or extract and purge.
- [ ] Visually inspect `docs/kf_eg_screenshot.PNG`, find its origin, and apply
  decision D5.
- [ ] Remove `.claude/docs/hermes-codex-config-with-docker.toml` from the
  repository workspace after confirming a private copy exists if needed.
- [ ] Ensure no secrets, personal paths, or machine-specific settings are moved
  into durable project documentation.

Acceptance: `.claude/` contains only active agent configuration/context that
must live there; historical documentation is in `docs/` or deliberately
purged.

### 8. Purge generated workspace artifacts and prevent recurrence

- [ ] Confirm no scripts or tests consume the ad hoc backend coverage JSON
  variants or `frontend/coverage-editor/`.
- [ ] Remove generated coverage reports and ignored cache/build documentation
  from the workspace using recoverable deletion where practical.
- [ ] Add narrowly scoped ignore rules for ad hoc backend coverage JSON and
  frontend coverage directories without hiding source fixtures.
- [ ] Confirm canonical CI artifacts remain generated on demand.

Acceptance: `git status --short --ignored` is free of obsolete documentation
and coverage clutter, while reproducible outputs remain excluded from commits.

### 9. Rewrite and validate references

- [ ] Update Markdown links, inline paths, script constants, and CI paths in one
  coordinated pass.
- [ ] Search for every old path and require zero unintended matches.
- [ ] Run a Markdown link checker against tracked documentation.
- [ ] Verify headings/anchors used by cross-document links.
- [ ] Confirm root and examples README behavior remains unchanged.

Acceptance: there are no broken local links, stale `.claude/docs` references,
or references to purged files.

### 10. Verify behavior and documentation quality

- [ ] Run focused API tests covering the root/examples README endpoints.
- [ ] If the generated report path changes, run the codegen validator and
  confirm its report output and CI configuration.
- [ ] Run documentation formatting/link checks.
- [ ] Run `git diff --check` and inspect all renames/deletions explicitly.
- [ ] Confirm no product source changed except consumers whose documentation
  paths intentionally moved.

Acceptance: all affected tests and tooling pass, and the diff is predominantly
renames, link updates, merges, and reviewed removals.

### 11. Commit in reviewable units

- [ ] Commit the documentation index and directory skeleton.
- [ ] Commit coverage/Fable audit migrations and link updates.
- [ ] Commit SQA consolidation.
- [ ] Commit codegen report consolidation and any atomic tooling changes.
- [ ] Commit approved legacy/generated-file purges and ignore rules.
- [ ] Review final status and the complete commit series before pushing.

Acceptance: each commit is independently understandable, no unrelated file is
included, and purges are isolated for easy review or reversal.

## Definition of done

- All durable project documentation is discoverable from `docs/README.md`.
- No durable documentation remains under `.claude/docs/` or
  `codegen_verification/`.
- Special-location exceptions are documented and intentional.
- No unique information is lost during merges or purges.
- All local documentation links and documentation-producing tooling resolve to
  the final paths.
- Generated/cache artifacts are reproducible, ignored, and absent from commits.
- The approved purge list is committed separately from content moves and merges.
