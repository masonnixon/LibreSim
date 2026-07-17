# LibreSim — Fable Audit Completion Plan

> Created 2026-07-10 on branch `fable-audit-plan` at
> `d0d3382989332d371d560d39a155f4023cd47a8f`.
>
> This is the execution plan for the work left after LS-1 through LS-9 were
> implemented. It supplements, rather than replaces,
> `simulation-correctness-remediation.md`. That original plan remains active until
> this plan's closeout task is complete.

## 1. Objective

Finish the unresolved acceptance work from the Fable audit and leave the branch in
a state where:

- the prescribed regressions exist at the API and public-behavior layers;
- backend tests, Ruff, and mypy pass in Docker;
- frontend tests, ESLint, and TypeScript checks pass in Docker;
- generated projects either match the simulator or are explicitly classified as
  unsupported by an enforced, maintainer-approved contract;
- the plan ledgers describe actual state using concrete commit hashes; and
- the process-global simulation context is either replaced under an approved design
  or explicitly deferred with its residual risk recorded.

This plan does not authorize unrelated items from `refactoring-recommendations.md`.
Refactoring is in scope only when it is necessary to satisfy an acceptance criterion
below.

## 2. Verified starting point

### Implemented

| Original task | Commit(s) | Current state |
|---|---|---|
| LS-1 | `09552bd` | Kernel RK4 coefficient correction and autonomous convergence coverage committed. |
| LS-2 | `88fcf73` | Stage-local time implemented in kernel, adapter, and four generated languages. |
| LS-3 | `9efe204` | Runner replacement is serialized; only runner-level shutdown coverage exists. |
| LS-4 | `15fa0bd`, `d0d3382` | CI soft-fails removed and strict output-set comparison added. |
| LS-5 | `896f0ff` | Result decimation and length-based rollback snapshots implemented. |
| LS-6 | `2b79fcb` | Nested flattening is recursive; boundary wiring is not adequately tested. |
| LS-7 | `230086b` | Unknown and invalid blocks no longer fall back to unity gain. |
| LS-8 | `e75e26c`, `570d036`, `cd0f509` | Sampling simplified, result IDs stabilized, mutable defaults removed. |
| LS-9 | `c28fee1`, `2172fa0`, `043a29a` | Project names sanitized, example manifest enforced, WebSocket origins checked. |

### Recorded verification baseline

- Backend: 1,915 passed, 1 skipped.
- Numerical/kernel/codegen-accuracy subset: 33 passed.
- Frontend Vitest: 659 passed.
- Generated projects: all 156 build and execute.
- Strict generated-output comparison: 53/156 pass (34.0%); 103 mismatch.
- Frontend ESLint: 7 errors.
- Frontend TypeScript: 10 errors.
- Full Ruff and mypy: failing.

These are recorded results, not a substitute for the fresh baseline in FAC-0.

### Worktree constraint

`docker-compose.yml` and `frontend/vite.config.ts` contain maintainer-owned local
Tailscale settings. Preserve them. Do not commit, revert, or use them to explain away
test failures.

## 3. Execution rules

1. Run project tests and quality tools in Docker, following the original plan.
2. Add a regression test before or with every behavioral correction.
3. Keep one task per commit or small, clearly related commit series. Do not push.
4. Do not weaken numerical comparisons, omit missing outputs, raise tolerances, or
   lower the 34.0% validator floor to produce a green result.
5. Do not count an output-less comparison as a pass. Unsupported analyses must be
   represented explicitly in the validation contract.
6. Update this plan's ledger after each task with concrete commit hashes and fresh
   command results.
7. If implementation contradicts this plan, stop and update the plan before changing
   behavior.

## 4. Task sequence

### FAC-0 — Capture a reproducible baseline

**Priority:** P0  
**Depends on:** nothing

Run the complete existing matrix before further changes and save the exact commands,
versions, counts, and failures in the task ledger.

Commands:

```bash
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm -v "$PWD/examples:/examples:ro" backend sh -c "pip install -q -e '.[dev]' && pytest tests/ -q"
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm backend sh -c "pip install -q -e '.[dev]' && ruff check src/ tests/"
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm backend sh -c "pip install -q -e '.[dev]' && mypy src/ --config-file=pyproject.toml"
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend npm test -- --run
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend npm run lint
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend npx tsc --noEmit
```

Also run the canonical numerical subset and `scripts/validate_codegen.py` using the
same compiler environment as CI. Confirm that the report is written to
`docs/codegen-validation-report.md` and that its summary agrees with the process exit
status.

```bash
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm -v "$PWD/examples:/examples:ro" backend sh -c "pip install -q -e '.[dev]' && pytest tests/test_osk.py tests/test_integration_accuracy.py tests/test_codegen_accuracy.py -q"

repo_path="$PWD"
backend_image="$(DOCKER_HOST=unix:///run/docker.sock docker compose images -q backend)"
DOCKER_HOST=unix:///run/docker.sock docker run --rm \
  -v "$repo_path:$repo_path" \
  -v /run/docker.sock:/var/run/docker.sock \
  -v /usr/bin/docker:/usr/bin/docker \
  -w "$repo_path" \
  -e "PYTHONPATH=$repo_path/backend" \
  "$backend_image" \
  sh -c "pip install -q -e '$repo_path/backend' && python scripts/validate_codegen.py"
```

The identical host/container repository path is required because the validator starts
nested compiler containers through the mounted Docker socket.

**Acceptance:** a dated baseline is recorded without modifying source or generated
fixtures.

### FAC-1 — Prove simulation replacement through the API

**Priority:** P0  
**Closes:** remaining LS-3 acceptance work  
**Depends on:** FAC-0

Add API-level tests in `backend/tests/test_api.py` or a focused
`backend/tests/test_concurrent_runs.py`:

1. Start a long-running simulation with one solver.
2. Immediately start a second simulation with a different solver.
3. Retain a handle or observable completion signal for the first background run and
   prove it exits.
4. Prove only the replacement runner remains live.
5. Compare the replacement run's result with an isolated execution of the same model.
6. Reproduce the `IDLE`-but-scheduled window and verify replacement still waits for the
   scheduled coroutine to exit.
7. Add a concurrent `/start` versus `/step/init` test to exercise the installation lock.

Avoid timing-only assertions where an event, task handle, runner identity, or result
comparison can provide deterministic evidence.

**Acceptance:** the new tests fail if `_install_runner()` does not serialize the old
run, and pass repeatedly in Docker without sleeps tuned to one machine.

### FAC-2 — Make rollback correct across decimation

**Priority:** P0  
**Closes:** remaining LS-5 acceptance work  
**Depends on:** FAC-0

The current snapshot stores only result lengths. Decimation rewrites the retained
prefix, so an old length alone cannot restore the exact earlier result set.

First add public step-mode tests that:

1. step forward five times and backward three times, then compare results and adapter
   state with a run stopped at the same logical step;
2. use a deliberately small `maxResultPoints` so step mode crosses the decimation
   threshold before rolling back;
3. exercise Scope and Scope3D restoration through `step_forward()` and
   `step_backward()`, not private helpers; and
4. step forward again after rollback and prove the result is deterministic.

Then define one coherent rollback model. Preferred implementation: store a compact,
immutable result checkpoint for retained step-history entries whenever decimation
changes a prefix, while continuing to use lengths between decimation events. An
alternative generation/index scheme is acceptable if it restores exact public results
without returning to O(n^2) snapshots.

Document the time and memory bound of the chosen representation.

**Acceptance:** exact rollback equivalence holds before and after decimation; result
counts remain bounded; first and latest retained times are preserved; no
`deepcopy(self._results)` is reintroduced on every step.

### FAC-3 — Verify nested subsystem boundary wiring

**Priority:** P0  
**Closes:** remaining LS-6 acceptance work  
**Depends on:** FAC-0

Replace or extend the narrow recursive-flattening test with a two-level model whose
signal path crosses both boundaries:

```text
external source -> outer inport -> inner inport -> gain -> inner outport
                -> outer outport -> external scope
```

Assert:

- the doubly prefixed gain appears in execution order;
- each external and internal connection is rewired to the correct flattened block and
  port;
- the compiled model executes and produces the expected gain numerically; and
- malformed recursive construction is rejected predictably.

Before adding a new depth limit, confirm whether Pydantic already makes cyclic object
graphs or excessive nesting unreachable through the API. Add the smallest protection
at the actual construction boundary.

**Acceptance:** removing recursive connection rewriting breaks the regression, and the
full compiler/simulation suites remain green.

### FAC-4 — Verify block-construction errors through the API

**Priority:** P0  
**Closes:** remaining LS-7 acceptance work  
**Depends on:** FAC-1

Add API simulations for:

- a block with `type: does_not_exist`; and
- a supported block whose constructor receives invalid parameters, if that path is
  externally reachable after Pydantic validation.

Poll `/api/simulate/status` and assert:

- terminal status is `error`;
- the message contains the offending block ID and block type; and
- no partial success result is exposed as a completed simulation.

Keep unit coverage for `_create_osk_block`, but do not treat it as a substitute for the
API regression.

**Acceptance:** both externally reachable failure paths surface actionable errors at
the API boundary.

### FAC-5 — Complete endpoint hardening coverage

**Priority:** P1  
**Closes:** remaining LS-9 acceptance work  
**Depends on:** FAC-0

Add endpoint tests for:

1. `/api/codegen/generate` with control characters, quotes, separators, Unicode, and an
   otherwise-empty `project_name`; assert a safe `Content-Disposition` filename.
2. `/api/codegen/compile` using a mocked compiler; assert the downloadable filename
   cannot reintroduce unsafe characters.
3. An existing JSON file omitted from `EXAMPLE_MANIFEST`, using a temporary examples
   directory and monkeypatch; assert 404.
4. Common traversal encodings as smoke tests, even where router matching rejects them
   before the handler.
5. A disallowed WebSocket origin; assert close code 1008 and no active connection leak.

Where practical, centralize construction of safe download headers so generation and
compilation cannot drift.

**Acceptance:** tests exercise HTTP/WebSocket endpoints rather than only sanitizer
helpers.

### FAC-6 — Restore frontend quality gates

**Priority:** P1  
**Depends on:** FAC-0

Fix the recorded ESLint and TypeScript errors in tests without weakening production
compiler settings or adding broad lint suppressions. Prefer typed mock builders and
literal types over `any` and casts. Remove genuinely unused variables.

Run:

```bash
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend npm run lint
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend npx tsc --noEmit
DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend npm test -- --run
```

**Acceptance:** all three commands pass in a clean container and the CI definitions
retain hard-fail behavior.

### FAC-7 — Restore backend static-analysis gates

**Priority:** P1  
**Depends on:** FAC-0, FAC-1 through FAC-5

Resolve Ruff and mypy findings in the touched backend. For existing `UP042` findings,
use `StrEnum` where runtime serialization and equality remain compatible. Add focused
tests before changing enum bases if behavior is relied upon.

Fix mypy errors in:

- codegen generators;
- adapter scope-state capture/restore; and
- runner compiled-model and snapshot state.

Use narrow, documented exclusions only for third-party or generated interfaces that
cannot be typed locally. Do not apply module-wide `ignore_errors` to project code.

**Acceptance:** the backend pytest, Ruff, and mypy commands from FAC-0 all pass in
Docker.

### FAC-8 — Close generated-code semantic mismatches

**Priority:** P0 for release correctness; execute after regressions stabilize  
**Depends on:** FAC-2, FAC-3, FAC-4, FAC-7

Start from the 103/156 mismatches in `docs/codegen-validation-report.md`. Extend the
validator to emit a machine-readable failure summary grouped by:

- missing or empty output sets;
- nondeterministic/random-source differences;
- unsupported block semantics;
- discrete or stateful major-step behavior;
- port mapping or vector shape differences;
- numerical integration differences; and
- language-specific generator defects.

Triage shared failures before language-specific failures. The initial order is:

1. analysis examples with empty output maps;
2. discrete/stateful blocks affected by `State.ready` semantics;
3. multi-output, vector, quaternion, navigation, and sensor-fusion port/shape mapping;
4. seeded random/noise behavior and comparison policy; and
5. individual Python/C/C++/Rust template defects.

For each family:

1. add or tighten an OSK-versus-generated regression;
2. identify the intended semantic contract from the backend behavior;
3. implement it in all applicable generators;
4. regenerate fixtures using the canonical script; and
5. run the full validator before committing.

The completion target is 100% of applicable targets. A target may be excluded only
through an explicit manifest entry with a reason, enforced by the validator and
approved by the maintainer. Excluded and output-less targets do not count as passes.

**Acceptance:** no unexplained mismatches remain, every applicable generated project
builds and runs, and the validator exits nonzero for missing outputs or unapproved
exclusions.

### FAC-9 — Decide and design instance-scoped simulation state

**Priority:** P1  
**Closes:** LS-10  
**Depends on:** FAC-1, FAC-7, FAC-8  
**Approval gate:** explicit maintainer decision required before implementation

**Completed (2026-07-16):** The maintainer selected implementation in `e536fb4`,
approved the dedicated `docs/plans/fac-9-sim-context-concurrency.md` design after
`16c97ab`, and authorized production work after the pre-FAC-9 checkpoint. Phases 0-7
are complete through `6e7f690`, including concurrent API sessions, compatibility
documentation, a separately proposed facade-deprecation plan, and the complete clean
checkout verification matrix.

Present two closeout choices:

1. **Implement:** write a dedicated design plan for an instance-scoped `SimContext`
   covering ownership, block access, adapter/kernel parity, state snapshotting, pause and
   rollback, concurrency, and migration of existing tests. Obtain approval, then execute
   that plan. The result must allow two simulations with different solvers to run
   concurrently without shared timing state.
2. **Defer:** retain serialized execution from LS-3 and record the accepted limitations:
   one simulation at a time per process, no parallel runner execution, and continued
   dependence on global kernel state. Include an owner or milestone for reconsideration.

Do not infer approval to begin the cross-cutting refactor merely from approval of this
completion plan.

**Acceptance:** LS-10 is either implemented under its approved design with concurrency
tests, or explicitly deferred in the ledger by the maintainer.

### FAC-10 — Full verification and documentation closeout

**Priority:** P0  
**Depends on:** FAC-1 through FAC-9

Run the full Docker and generated-code matrix from FAC-0 on a clean checkout of the
branch. Record exact counts, tool versions, validator classifications, and commit hashes.

Then:

1. verify the concrete LS-1 through LS-10 hashes and final statuses in
   `simulation-correctness-remediation.md` against the completed work;
2. add a new dated final remediation status while preserving
   `.claude/docs/fable-audit-remediation-status-2026-07-10.md` as a historical checkpoint;
3. mark original LS tasks complete only where their full acceptance criteria pass;
4. record the LS-10 decision;
5. move `simulation-correctness-remediation.md`,
   `fac-9-sim-context-concurrency.md`, and this plan to `docs/plans/completed/`; and
6. leave `refactoring-recommendations.md` active until its independent backlog is
   completed or intentionally superseded.

**Acceptance:** all required gates pass, residual risks are approved and explicit, and
no active plan falsely claims completion.

## 5. Task ledger

| Task | Status | Commit(s) | Verification / notes |
|---|---|---|---|
| FAC-0 | complete | | Reproduced on 2026-07-16 from clean detached `d0d3382`: backend 1,915 passed/1 skipped, numerical subset 33 passed, frontend 659 passed, Ruff 7 UP042 findings, mypy 27 errors/4 files, ESLint 7 errors, TypeScript 10 errors, and validator 53/156 with an exit status and generated summary that agreed. The reproduction exposed and corrected two command assumptions: tests require the repository examples mounted at `/examples`, and one-shot frontend checks use `--no-deps` when the development backend port is occupied. Current pre-FAC-9 readiness at `16c97ab`: backend 2,106 passed/1 skipped, numerical subset 33 passed, frontend 659 passed, Ruff/mypy/ESLint/TypeScript clean, and validator 156/156 with the canonical report byte-identical. Toolchain: Docker 29.5.2, Compose 5.1.4, Python 3.11.15, pytest 9.1.1, Ruff 0.15.22, mypy 2.3.0, Node 18.20.8, npm 10.8.2, Vitest 1.6.1, ESLint 8.57.1, TypeScript 5.9.3. |
| FAC-1 | complete | `a2cfd1c` | Deterministic API replacement tests cover scheduled-run races, `/start` versus `/step/init`, 409 preservation, and live `/step/continue` tracking. Included in the 2026-07-13 full Docker pass; strengthened focused suite passed 128 tests on 2026-07-14. |
| FAC-2 | complete | `b5e4bfa` | Committed-state/generation-aware rollback restores exact decimated results plus Scope and Scope3D state with bounded checkpoint retention. Included in the 2026-07-13 full Docker pass; strengthened focused suite passed 128 tests on 2026-07-14. |
| FAC-3 | complete | `5ed9bdf` | Nested subsystem boundary rewriting now preserves port identity, rejects malformed boundary indexes, and executes the two-level numerical regression. Pydantic rejects recursive object graphs. Strengthened focused suite passed on 2026-07-14. |
| FAC-4 | complete | `3f07404` | API-level unknown-block and constructor-failure regressions assert actionable terminal errors and no partial results. Included in the 2026-07-13 full Docker pass. |
| FAC-5 | complete | `24741bf` | Shared safe download headers and HTTP/WebSocket hardening regressions cover generation, compilation, manifest omission, traversal, and rejected origins. Included in the 2026-07-13 full Docker pass. |
| FAC-6 | complete | `9f1ebed` | ESLint and TypeScript pass; Vitest 659/659 passes in Docker. |
| FAC-7 | complete | `5079dd5`, `b5e4bfa` | Seven StrEnums converted with compatibility coverage and touched runner/adapter typing corrected. Canonical Docker verification passed on 2026-07-13: backend pytest 1,945 passed/1 skipped, Ruff reported `All checks passed!`, and mypy reported no issues in 117 source files. |
| FAC-8 | complete | `5c3899c`, `2aa06ba`, `b34d2a0`, `d7dc2d1`, `7ed9e45`, `8a73430`, `a414038`, `57c485c`, `ee853ee`, `6e1250a`, `b4487d0`, `0860cc5`, `ec19d1a`, `927376d`, `c7b851f`, `07db0e4`, `6a60e13` | Strict CSV/key-set validation and a shared, stable output schema now reject empty, malformed, duplicate, missing, unexpected, nonfinite, and shape-mismatched output instead of accepting positional or empty comparisons. Declared source-port dimensions eliminated all nine simulation-shape failures. Generated runtimes now separate the OSK major/ready update from integration stages, hold ready-only noise/discrete/observer state during RK passes, use the runtime step plus canonical parameter names for rate limiting, and propagate PI, PD, and model-reference continuous state in every target language. Python now honors the generated two-port contract for quaternion-vector rotation and implements discrete Kalman filtering instead of silently emitting passthrough blocks. All four targets now implement the OSK discrete-PID sample timing, integration methods, and filtered derivative instead of emitting passthrough blocks. C, C++, and Rust noise sources embed CPython's expanded MT19937 state and use its 53-bit random and cached Gaussian sampling contract. First-order low-pass filters now derive their coefficient from the configured simulation step, and all four targets emit OSK-compatible analog-filter biquad cascades instead of silent passthrough blocks. LQR and pole-placement controllers now infer full gain dimensions in OSK, and generated Python consumes its wired state vector instead of a disconnected zero state. Compiled blocks now preserve declared port IDs so headless simulation resolves named multi-input and multi-output ports before legacy suffix heuristics. RF budget, external-carrier AM, alpha-beta, and alpha-beta-gamma blocks now have matching OSK and four-language generated semantics; the tracking example also uses an explicit deterministic noise stream. Compiled integrators now expose live state during Runge-Kutta stages, restoring Lorenz parity. Navigation targets now share degree-based WGS84 transforms and distances, split-reference mapping, and canonical Ramp parameter names. Generated window and FFT blocks now preserve the OSK frame contract and interleaved complex spectrum in every target. Generated ZIP metadata is fixed so repeated canonical regeneration is byte-reproducible. Demux now preserves selected vector-port segments, and generated IMU, Madgwick, and complementary-filter blocks match the OSK port order, runtime-step equations, seeded Gaussian stream, vector biases, and scale errors in all four targets. Control-analysis blocks now expose their single declared scalar output through an explicit analysis schema while retaining rich visualization arrays outside generated CSV, and every target embeds the canonical OSK initialization result. The focused codegen suite passed 550/550 with Ruff clean and mypy clean across 135 source files; the focused frontend registry suite passed 25/25. Canonical regeneration completed for all 156 archives. The 2026-07-16 full matrix improved from 52/156 to 156/156 semantic passes (100.0%) with zero simulation, build, run, or output-validation failures. |
| FAC-9 | complete | `e536fb4`, `16c97ab`, `f3051b9`, `41d257e`, `9d4531a`, `68eee69`, `a450f20`, `ec15bb1`, `70dbd33`, `e33a9fd`, `66cadc0`, `3898ed5`, `959e8aa`, `5cde103`, `cc0fc70`, `4df7b63`, `e00ba89`, `6e7f690` | 2026-07-16 maintainer selected and approved concurrent simulations. Phase 0 reproduced deterministic solver/clock cross-talk. Phases 1-4 introduced instance-owned `SimContext`, bound native/adapted graphs and integrators to one owner, made native and runner execution concurrent and operation-safe, and migrated all built-in mutable timing/readiness access. Phase 5 added frozen, versioned, atomic adapter/runner checkpoints with canonical fingerprints, complete context/integrator state, all 181 built-in codecs, bounded histories, deterministic replay, and peer isolation. Phase 6 added bounded process-local session records, exact task/token ownership, leased targeting, tombstoned deletion/promotion, safe pruning, default replacement serialization, opt-in coexistence, optional targeting across read/control/step routes, and matching frontend client options. Deterministic tests cover direct/native/runner/API concurrency, unknown IDs, same-session conflicts, replacement/coexistence, deletion, capacity races, failed initialization, cancellation, snapshots, and cross-context isolation. Phase 7 documented the compatibility facade and session deployment contract and recorded facade removal as a separately approved deprecation. From a clean detached checkout of `6e7f690`, 2,185 backend tests passed with 1 skip, 664 frontend tests passed, the canonical numerical subset passed 33/33, Ruff/mypy (138 files)/ESLint/TypeScript were clean, and the validator passed 156/156 with zero simulation, build, run, or output-validation failures and a byte-identical report. |
| FAC-10 | pending | | Full matrix, final ledger verification, dated closeout status, and archival. |

## 6. Definition of done

The Fable audit is complete only when FAC-10's acceptance criteria are met. Passing the
existing 34.0% codegen floor, committing an implementation without its prescribed
regression, or recording LS-1 through LS-9 as merely "implemented" is not completion.
