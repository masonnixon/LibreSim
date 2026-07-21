# Fable Audit Remediation Status

**Date:** 2026-07-10  
**Branch:** `fable-audit-plan`  
**HEAD:** `d0d3382989332d371d560d39a155f4023cd47a8f`  
**Plan:** `docs/plans/simulation-correctness-remediation.md`

> **Historical checkpoint — not current project status.** This document intentionally
> preserves the branch state observed on 2026-07-10 at `d0d3382`. Active execution and
> current results are tracked in `docs/plans/fable-audit-completion.md`.
>
> Since this checkpoint, the missing LS-3, LS-5, LS-6, LS-7, and LS-9 acceptance
> coverage was completed; frontend and backend quality gates were restored; and FAC-8
> reached 156/156 generated-code validation in `6a60e13`. The maintainer selected FAC-9
> implementation in `e536fb4` and approved its dedicated design after `16c97ab`.
> FAC-10 has not been completed.

## Executive summary

The core implementation for LS-1 through LS-9 is committed on
`fable-audit-plan`. LS-10 remains intentionally blocked because the plan requires
maintainer sign-off before starting the instance-scoped simulation-context
refactor.

The remediation is not yet complete against every acceptance criterion in the
plan. Backend behavior and tests are healthy, but several specifically requested
regression tests were implemented more narrowly than prescribed. Frontend lint
and type-check gates also expose pre-existing failures, and strict generated-code
comparison identifies substantial model/codegen mismatches.

The status ledger in the plan currently marks LS-1 through LS-9 complete. Treat
those entries as "implementation committed" rather than confirmation that every
acceptance check is satisfied.

## Committed work

| Task | Implementation status | Commit(s) | Summary |
|---|---|---|---|
| LS-1 | Implemented | `09552bd` | Removed the RK4 double-halving in the kernel clock and added autonomous convergence tests. |
| LS-2 | Implemented | `88fcf73` | Added stage-local time to kernel, adapter, and generated loops; regenerated 156 fixtures; guarded stateful major-step updates. |
| LS-3 | Implemented | `9efe204` | Serialized runner replacement and added scheduled/paused run shutdown tracking. |
| LS-4 | Implemented | `15fa0bd`, `d0d3382` | Removed CI soft-fails, changed accuracy ground truth to the adapter loop, and hardened codegen output comparison. |
| LS-5 | Implemented | `896f0ff` | Bounded result histories, added decimation statistics, and replaced runner/scope snapshot copies with lengths. |
| LS-6 | Implemented | `2b79fcb` | Made nested subsystem flattening recursive. |
| LS-7 | Implemented | `230086b` | Removed unity-gain fallbacks for unknown block types and constructor failures. |
| LS-8 | Implemented | `e75e26c`, `570d036`, `cd0f509` | Simplified kernel sampling, added stable block identifiers, and removed mutable/dead class defaults. |
| LS-9 | Implemented | `c28fee1`, `2172fa0`, `043a29a` | Sanitized codegen names, restricted examples to the manifest, and enforced WebSocket origins. |
| LS-10 | Not started | - | Blocked pending maintainer sign-off, as required by the plan. |

## Verification completed

- Backend Docker test suite: **1,915 passed, 1 skipped**.
- Numerical/kernel/codegen-accuracy suite from the canonical repository: **33 passed**.
- Frontend Vitest suite: **659 passed**.
- All 156 generated projects were regenerated, built, and executed.
- Strict codegen comparison: **53/156 passed (34.0%)**.
- Previous checked-in codegen report baseline: **36/156 (23.1%)**.
- The branch exceeds its configured 23.1% non-regression threshold, but this
  threshold does not mean generated output is broadly correct.
- The only intentional uncommitted worktree changes are the maintainer's local
  Tailscale settings in `docker-compose.yml` and `frontend/vite.config.ts`.

## Remaining acceptance work

### LS-3: overlapping simulation requests

- Add the prescribed API-level regression that starts two long-running
  simulations concurrently with different solvers.
- Confirm the first background coroutine exits and only the second runner remains
  active.
- Verify the second result matches an isolated run of the same model.
- Exercise the `IDLE`-but-scheduled race through the API, not only the runner-level
  paused shutdown behavior.

### LS-5: rollback equivalence and decimation

- Add the exact five-steps-forward, three-steps-backward result-equivalence test.
- Add a step-mode test that crosses a deliberately small decimation limit.
- Define and verify rollback behavior when decimation rewrites an earlier result
  prefix referenced by retained history entries.
- Confirm Scope and Scope3D length-based restoration through public stepping
  behavior, not only existing general step tests.

### LS-6: nested subsystem boundary wiring

- Expand the regression model to contain nested
  `inport -> gain -> outport` wiring at both subsystem boundaries.
- Assert the doubly prefixed gain is in the execution order.
- Assert external connections are rewired to the correct nested inport/outport
  blocks and the compiled model produces the expected numerical output.
- Add a depth limit or explicit malformed-recursion protection if recursive model
  construction can be introduced outside Pydantic validation.

### LS-7: error propagation through the API

- Add a model containing `type: does_not_exist` to an API simulation request.
- Poll `/api/simulate/status` and assert `status == error`.
- Assert the reported error includes both the block ID and unknown type.
- Add equivalent API coverage for constructor failure if that path remains
  externally reachable.

### LS-9: endpoint-level hardening coverage

- Add a `/api/codegen/generate` request with a hostile `project_name` and assert a
  sanitized `Content-Disposition` filename.
- Cover the compile/download response filename where practical.
- Add an existing JSON file that is absent from `EXAMPLE_MANIFEST` via a temporary
  directory/monkeypatch and assert the endpoint returns 404.
- Retain traversal smoke tests even though router normalization and single-segment
  matching already reject common traversal URLs.
- Add a rejected WebSocket-origin test that asserts close code 1008.

## Quality gates still failing

### Frontend

- ESLint reports **7 errors** in existing test files, including explicit `any`
  usage and unused variables.
- `tsc --noEmit` reports **10 errors** in existing tests, including mock type
  incompatibilities, widened solver strings, and unused variables.
- Vitest itself is green, but the newly hardened CI job will fail until lint and
  type-check findings are fixed.

### Backend static analysis

- Full Ruff is not green because of existing `UP042` findings for enums inheriting
  from both `str` and `Enum`.
- Full mypy is not green because of existing typing errors in codegen generators,
  adapter scope-state handling, and runner compiled-model state.
- Re-run both tools after fixing these findings using the Docker commands in the
  remediation plan.

### Generated-code correctness

- Strict validation currently reports **103 mismatches out of 156 targets**.
- The report is stored in `docs/reports/codegen-validation-report.md`.
- Several failures are shared across all four generated languages, indicating
  model/template semantic mismatches rather than compiler-specific issues.
- Discrete blocks and stateful generated blocks need particular review after the
  stage-local time change; generated APIs do not yet expose the backend's
  `State.ready` major-step boundary semantics.
- Do not raise tolerances or weaken output matching to make this gate green.

## Recommended execution order

1. Add the missing LS-3, LS-5, LS-6, LS-7, and LS-9 regression tests and address
   any behavior they expose.
2. Fix frontend ESLint and TypeScript test errors so the hardened CI gate can pass.
3. Fix backend Ruff and mypy findings or document and configure narrowly justified
   exclusions.
4. Triage codegen mismatches by common failure family, starting with discrete and
   stateful blocks affected by stage-local time.
5. Re-run the full Docker backend/frontend/static-analysis/codegen matrix.
6. Update the plan ledger with concrete commit hashes rather than `this commit`.
7. Obtain maintainer sign-off and write a dedicated design plan before LS-10.

## Definition of fully complete

The audit remediation should be considered complete only when:

- Every prescribed regression scenario has coverage at the specified layer.
- Backend tests, Ruff, and mypy pass in Docker.
- Frontend tests, ESLint, and TypeScript checks pass in Docker.
- Codegen validation meets the maintainer-approved correctness target without
  missing-output or tolerance loopholes.
- The status ledger contains actual commit hashes and accurately describes any
  accepted residual risk.
- LS-10 is either completed under a separately approved plan or explicitly
  deferred by the maintainer.
