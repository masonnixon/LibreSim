---
title: Numerical Linear Algebra and Native Solver Primitives — Implementation Plan
tags:
  - libresim
  - numerical-methods
  - implementation-plan
status: draft
owner: Mason Nixon
created: 2026-09-02
proposal: libresim-features-required-for-as2-nonlinear-parity.md
scope: narrowed — see "What this plan does not build"
---

## Continuation Capsule

~~~text
REPO: /home/mason/repos/LibreSim.git
PLAN: /home/mason/repos/LibreSim.git/docs/plans/as2-nonlinear-parity-implementation.md
BRANCH: feat/matrix-signal-shapes
HEAD: 4076af703ff37c06c27409b86da2e455ea4e9be6
BASELINE: untracked docs/plans/as2-nonlinear-parity-implementation.md and
  docs/plans/libresim-features-required-for-as2-nonlinear-parity.md (preserve both)
LAST_ACCEPTED: P3 (+P3-REPAIR), commit 4076af7, GATE=PASS (backend 3827 passed 0 failed; frontend 967 passed)
ACTIVE: DONE — all phases accepted
RUN: not started
LAST_GATE: PASS
NEXT_COMMAND: /home/mason/.claude/skills/local-model-handoff/scripts/start-phase.sh /home/mason/repos/LibreSim.git local-qwen38-q3xl <RUN> <RUN>/prompt.txt
QWEN_PROMPT: Execute P3 from /home/mason/repos/LibreSim.git/docs/plans/as2-nonlinear-parity-implementation.md. Read AGENTS.md. Contract is a hard allowlist. Do only DO/CHECK, preserve KEEP, obey STOP, and end with RESULT only.
SUPERVISOR_PROMPT: Continue /home/mason/repos/LibreSim.git/docs/plans/as2-nonlinear-parity-implementation.md using local-model-handoff. Verify HEAD, BASELINE, process state, and LAST_GATE before acting. Accept nothing without deterministic gates; update this capsule before stopping.
~~~

| Phase | Depends on | Mode | State | Observable goal |
|---|---|---|---|---|
| P0-RED | none | RED | ACCEPTED (05c205d) | Shape tests exist and fail because matrix ports degrade to scalars |
| P0-GREEN | P0-RED accepted | GREEN | ACCEPTED (e41d71c) | `_OutputPortView` carries 2-D shape; tripwire raises; P0-RED tests pass |
| P1 | P0-GREEN accepted | PROOF | ACCEPTED (e6c0e50) | Real matmul, transpose, constructors, 2-D addressing |
| P2 | P1 accepted | PROOF | ACCEPTED (a74df34) | `linear_solve` with pivoting, status and failure outputs |
| P3 | P2 accepted | ACCEPT | ACCEPTED (4076af7) | Reset/no-stale-output tests plus acceptance example |

Model profile: `local-qwen38-q3xl` (Qwen 3.8 27B UD-Q3_K_XL, llama.cpp on
127.0.0.1:8042). Known capacity: safe to widen phase scope for this profile.

**Sandbox reality, learned in P0-RED.** The local model's Codex sandbox mounts
`.git` read-only and cannot reach the Docker socket, so it **edits only**. The
supervisor runs the container checks and makes the commit. Do not write a
contract that expects the local model to commit or to run Docker.

**There is no test container.** `backend/Dockerfile` installs only
`requirements.txt`; test dependencies live in the `dev` extra of
`backend/pyproject.toml:19-30`, so `pytest` is absent from the runtime image.
Use an ephemeral install, and keep the bind-mounted worktree clean
(`PYTHONDONTWRITEBYTECODE`, `-p no:cacheprovider`) or the gate's worktree check
fails.

**The mount layout matters.** Several tests resolve fixtures with
`Path(__file__).parents[2] / "examples"` (e.g.
`backend/tests/test_codegen_filters.py:103`). On a host checkout that is the
repo root. Inside the `backend` service, `backend/` is mounted at `/app`, so
`parents[2]` is `/` and the test looks for `/examples` — 48 tests fail with
`FileNotFoundError` for reasons that have nothing to do with the code.

Mount the repo so the container layout mirrors a checkout:

```bash
docker compose run --rm --no-deps \
  -v /home/mason/repos/LibreSim.git:/repo -w /repo/backend \
  -e PYTHONDONTWRITEBYTECODE=1 backend sh -c \
  "pip install -q pytest pytest-asyncio pytest-cov httpx pytest-xdist >/dev/null 2>&1; \
   python -m pytest tests -q -p no:cacheprovider --no-cov -n 4"
```

Expected at `e41d71c`: **3776 passed, 1 skipped, 0 failed**. Any failure is a
real regression — there are no known-broken tests to excuse.

`-n 4` (xdist) makes `tests/test_estimation_discrete_coverage.py` fail
occasionally through ordering; confirm any single failure by re-running that
file alone before treating it as real.

# Numerical linear algebra and native solver primitives

Narrowed from the original capability proposal to the seven items actually
required. Four phases, test-first, sized for handoff one phase at a time.

Required set:

1. General matrix–matrix and matrix–vector multiplication.
2. Native arbitrary-size linear solver with pivoting.
3. Matrix construction, slicing, concatenation, shape validation.
4. Deterministic solver failure/status outputs.
5. Correct reset and cache-invalidation behavior.
6. JSON registry/compiler/runtime support.
7. Focused tests: larger solves, singular matrices, dimensions, reset, nesting.

Items 6 and 7 are not phases. They are conditions every phase must satisfy —
see "Rules for every phase".

## The finding that shapes everything

LibreSim signals are **flat Python lists with no shape metadata**, so
`MatrixMultiply` (`backend/src/osk/blocks/matrix_ops.py:39-64`) is not matrix
multiplication: equal-length inputs produce a dot product, otherwise it
multiplies the first scalar of each.

The cause is one property in one class (`osk_adapter.py:1051-1053`):

```python
@property
def _is_vector(self) -> bool:
    return len(self._dimensions) == 1 and self._dimensions[0] > 1
```

A 2-D `[m,n]` fails `len(...) == 1`, so `getOutputVector()` returns `None` and
the consumer falls back to a scalar. **Matrix-valued signals are structurally
impossible today.** A `[1]` vector fails the `> 1` test the same way.

Items 1, 2 and 3 all sit on top of fixing this, so it is Phase 0.

## Why the fix is one class, not eighty-four sites

Two data paths already exist at step time:

- **Push, scalars only.** Blocks with no wired reference get
  `osk_block.setInput(value, i)` from `_step` (`osk_adapter.py:1557, 1616,
  1673, 1712`). Vectors cannot travel this way.
- **Pull, vectors.** Blocks with a wired reference get nothing pushed; they
  reach upstream themselves via `getOutputVector()`. 84 such call sites across
  `osk/blocks/`.

But `_setup_connections` wires **every** consumer — `connectInput`,
`input_block`, and `input_blocks` (`osk_adapter.py:1364-1382`) — to a
`_OutputPortView` wrapper, never to the raw upstream block. All 84 pull sites
already read through that one class, and it already carries declared shape
from `CompiledBlock.output_dimensions`. That is the seam.

## Design decisions

**numpy carries the shape.** `numpy>=1.26` and `scipy>=1.11` are already
dependencies (`backend/pyproject.toml:15-16`). `ndarray` gives shape, dtype,
non-broadcasting matmul, and dimension errors for free. No `Signal` class, no
shape algebra. Precedent is thin (2 of 20 files in `osk/blocks/` import numpy),
so confine it to the matrix and linear-algebra blocks; do not numpy-ify
unrelated blocks in passing.

**Additive, because the flat-list path cannot be changed.** There are 49
`isinstance(value, list)` checks in `backend/src/osk/`. An `ndarray` satisfies
none of them and would take the `else` branch **silently** — wrong numbers, no
exception. So: add `getOutputArray()` alongside `getOutputVector()`, never
widen it. This leaves a second signal path in place, which is tolerable only
because of the tripwire in Phase 0.

**LAPACK, no hand-rolled pivoting.** `scipy.linalg.lu_factor` / `lu_solve` is
LU with partial pivoting and handles multiple right-hand sides unchanged.
`np.linalg.cond` covers conditioning.

### Solver state contract (item 5)

Owner-revised in the proposal; this is the authoritative statement. The solver:

- factors `A` independently on every call;
- retains no cross-step factorization cache;
- has no cache-invalidation obligation;
- **must not emit stale outputs** after reset, failed evaluation, rejected
  steps, or repeated execution;
- treats factorization reuse as a future optimization requiring its own design
  and invalidation contract.

Do not add a factorization cache during implementation, even where it looks
like a free win. It is a scope change, not an optimization, and it pulls the
deferred invalidation work back in.

**"Rejected steps" needs a note.** LibreSim has no step-reject or retry path
today: integration is fixed-step explicit Euler/RK2/RK4/Merson
(`osk/state.py:86-147`) with no error control, and the accept/reject lifecycle
from the original proposal §7 is deferred. The nearest real mechanism is
step-mode undo in `SimulationRunner` (`runner.py:769`). Satisfy this bullet
against step-back today; do **not** build a reject/retry mechanism to have
something to test it with.

The practical effect: item 5 is one invariant — **the solver's outputs are a
pure function of the current step's inputs, never of a previous step** — plus
tests that try to violate it.

## Rules for every phase

**Registration (item 6).** A block type is only real when it appears in
`BLOCK_TYPE_MAP` (`osk_adapter.py:244-445`), `PARAM_MAP` (`:640-1040`), and
`SNAPSHOT_BLOCK_TYPES` (`:450-637`), plus a `frontend/src/blocks/` palette
entry. Follow this existing shotgun-registration idiom; do not invent a
decorator to avoid it.

`SNAPSHOT_BLOCK_TYPES` bites quietly: codecs are derived reflectively from that
set (`osk_adapter.py:636`), so a block left out has no snapshot support and
step-mode/undo (`runner.py:769`) will not restore it. Applies to any block
holding state between steps.

**Tests (item 7).** Ship with the code, not after. `backend/pyproject.toml:152`
sets `fail_under = 100`, so a phase cannot be "mostly done".

**Reset (item 5), every stateful block.** A step-back-and-replay test, and a
test proving no stale output survives a reset.

---

## Phase 0 — Shape on the signal path

Files, in order of leverage:

- `osk_adapter.py:1043-1071` (`_OutputPortView`) — accept 2-D `dimensions`,
  add `getOutputArray()` returning a shaped `ndarray`. Leave
  `getOutputVector()` returning flat lists exactly as today.
- `backend/src/osk/block.py` — add `getOutputArray(port=0)` /
  `setInputArray(value, port=0)` to the base class, defaulting to a bridge over
  `getOutputVector()`/`getOutput()`.
- `backend/src/simulation/compiler.py:23,107` — verify a 2-D `[m,n]` survives
  `_flatten_subsystems` (`compiler.py:269-421`) and JSON round-trip. Likeliest
  hidden failure.

**The tripwire — the highest-value line in this plan.** When a 2-D signal
reaches a consumer that only understands flat lists, **raise** with block name,
port, and shape. Never flatten a matrix to feed a legacy block; never degrade
it to a scalar. This converts the silent-wrong-number class into a model-build
error, and is the only reason leaving the second signal path in place is
defensible. If this check is weakened, stop and reassess.

Not in this phase: the 84 pull sites and the four `setInput` push sites.

Tests (`backend/tests/test_signal_shapes.py`):
- `[3,4]` passes between two blocks with shape intact.
- 1×1 does not degrade to a scalar.
- Shape survives JSON serialize → deserialize → compile.
- Shape survives one and two levels of subsystem nesting (item 7, nesting).
- `[3,3]` into a legacy flat-list consumer raises at model build.
- A legacy flat vector into a matrix block still works via the bridge.

**Gate:** shape tests green; full existing backend suite green with zero
changes to non-matrix blocks.

---

## Phase 1 — Matrix operations (items 1, 3)

`backend/src/osk/blocks/matrix_ops.py`, plus registration per the rules above.

- Rewrite `MatrixMultiply` as true `[m,k] × [k,n] -> [m,n]` and
  `[m,n] × [n] -> [m]` via `@`. Reject incompatible shapes; no dot-product or
  scalar fallback.
- Rewrite `MatrixTranspose` and `MatrixInverse` against real 2-D shapes.
- New: `matrix_identity`, `matrix_zeros`, `matrix_diagonal`, `matrix_reshape`.
  Constant-shape parameters.
- `Selector` / `Assignment` / `Concatenate` (`matrix_ops.py:182-344`) gain 2-D
  row/column addressing.
- No broadcasting. Shapes match exactly or it is an error.

Tests: known-answer products including non-square and matrix-vector; transpose
round-trip; each constructor block; 2-D slicing, assignment and concatenation;
every documented dimension error.

**Gate:** matrix tests green, frontend palette entries in place.

---

## Phase 2 — `linear_solve` (items 2, 4)

New `backend/src/osk/blocks/linear_algebra.py`, registered through the normal
path.

- `scipy.linalg.lu_factor` / `lu_solve`. Never `inv()`.
- Runtime `N` to at least 30; vector or matrix right-hand side with identical
  numerical semantics.
- Parameters: `method`, `pivoting`, `singularity_tolerance`, `condition_limit`,
  `failure_policy`.
- Status outputs (item 4): success/failure status, residual `||Ax-b||`,
  condition estimate, active dimension. Diagnostics must not alter the numeric
  output.
- Failure: reject nonsquare `A` and mismatched `b`; detect singular and
  ill-conditioned systems; **never** emit the previous step's output; no silent
  pseudoinverse.

Tests: scalar, 2×2, 3×3, 30×30 known answers; random well-conditioned systems
against `np.linalg.solve`; multiple right-hand sides; badly scaled, singular
and near-singular inputs; residual and conditioning values; and an explicit
**stale-output test** — a successful solve followed by a singular one must not
re-emit the successful result.

**Gate:** every failure mode has a test proving it fails the documented way.

---

## Phase 3 — Reset correctness and acceptance (items 5, 7)

- Snapshot codecs for every block added in Phases 1–2, per the registration
  rule. Step-back and replay produces identical outputs.
- Reset clears the solver block's last solution and status.

**The four stale-output tests**, one per clause of the solver state contract.
Each drives a successful solve first, then the adverse condition, and asserts
the earlier result is not re-emitted:

| Clause | Test |
|---|---|
| after reset | solve, reset, read outputs before any new solve |
| after failed evaluation | good solve, then singular `A` |
| after rejected steps | good solve, step-back via `runner.py:769`, re-read |
| repeated execution | two identical runs, byte-identical outputs |
- One domain-neutral acceptance example: runtime construction of `A` and `b`
  from native signals, an `N > 2` solve, solution plus residual plus
  conditioning plus status outputs, JSON compilation, headless execution, and
  deterministic failure on singular and dimension-invalid input.

**Gate:** the example runs headless and in the GUI runtime with identical
numbers; deliberate-failure cases fail as documented.

---

## What this plan does not build

Deferred to separate future proposals, not cancelled:

- **General hybrid event framework** — event conditions, ordering for
  simultaneous events, reset maps, hysteresis, event logging (proposal §5).
- **Nonlinear algebraic-loop solver** — the `algebraic_constraint` block and
  residual iteration (proposal §6). Compile-time loop detection
  (`compiler.py:211-241`) keeps hard-failing genuine zero-delay loops, which
  remains correct.
- **Adaptive integration lifecycle** — implicit or variable-step solvers,
  zero-crossing root-finding. Explicit fixed-step Euler/RK2/RK4/Merson
  (`osk/state.py:86-147`) is unchanged, and this plan adds no integration math.
- **Broad runtime-dimension switching** — masks, mode-aware shape switching,
  declared-maximum dimensions (proposal §4).
- **Performance instrumentation** — timing outputs, factorization reuse,
  copy-avoidance (proposal §11).

Also out of scope: codegen support for the new blocks. Emitters must raise on
an unsupported block rather than emit wrong code. No linearize/trim utility.
No general symbolic or autodiff Jacobian.

Retiring the second signal path (84 pull sites, 49 `isinstance` checks) is a
separate migration, justified only if the Phase 0 tripwire proves insufficient.

---

# Phase contracts

## P0-RED

```text
PHASE: P0-RED Failing shape tests for matrix-valued ports
MODE: RED
START_HEAD: e3e32de255f14f3435d2eedf4cce7596f2490a0d
OWN: backend/tests/test_signal_shapes.py
DENY: backend/src/**, frontend/**, docs/**, docker-compose.yml, backend/pyproject.toml
KEEP: every existing test file and its behavior; no edits outside OWN
DO:
1. Create backend/tests/test_signal_shapes.py with tests asserting the DESIRED
   behavior described in "Phase 0" of this document, not current behavior.
2. Cover: a [3,4] signal passing between two blocks with shape intact; a 1x1
   signal not degrading to a scalar; shape surviving JSON serialize ->
   deserialize -> compile; shape surviving one and two levels of subsystem
   nesting; a [3,3] signal into a legacy flat-list consumer raising at model
   build; a legacy flat vector into a matrix-capable consumer still working.
3. Build models through the normal JSON/registry/compiler path used by the
   existing tests in backend/tests/. Do not construct OSK blocks directly and
   do not bypass ModelCompiler.
4. Each test must fail against current code for the RIGHT reason: 2-D
   dimensions make _OutputPortView._is_vector False
   (backend/src/simulation/osk_adapter.py:1051-1053), so getOutputVector()
   returns None and the consumer falls back to a scalar.
5. ANTI-FALSE-POSITIVE: no test may pass by asserting today's broken behavior,
   by using pytest.xfail/skip, by mocking _OutputPortView or any block, or by
   asserting only that an exception type exists. Tests must fail as assertion
   failures, not as collection or import errors.
CHECK:
- DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps backend pytest tests/test_signal_shapes.py -x -q
  Expect a NON-ZERO exit with assertion failures. Collection/import errors are a FAILED phase.
- DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps backend pytest tests -q --deselect tests/test_signal_shapes.py
  Expect exit 0: no existing test may change behavior.
COMMIT: Add failing signal shape tests for matrix-valued ports
STOP: one commit; no install; no reset/restore/clean; no edits outside OWN; do not fix src
RESULT: STATUS/PHASE/HEAD/CHECK_EXIT/CHANGED/BLOCKER only
```

## P1

```text
PHASE: P1 Real matrix operations
MODE: PROOF
START_HEAD: e41d71cae1c7749144b4d79dd4bbaad31e962965
OWN: backend/src/osk/blocks/matrix_ops.py, backend/src/simulation/osk_adapter.py,
     backend/tests/test_matrix_ops.py, frontend/src/blocks/matrix_ops.ts
DENY: backend/tests/test_signal_shapes.py, backend/src/osk/block.py,
      backend/src/simulation/compiler.py, backend/src/osk/blocks/** except matrix_ops.py,
      docs/**, backend/pyproject.toml, docker-compose.yml
KEEP: all 7 tests in backend/tests/test_signal_shapes.py passing and unmodified; the
  Phase 0 tripwire behavior; getOutputVector() still returning flat lists; every other
  existing test passing
DO:
1. Rewrite MatrixMultiply (matrix_ops.py:13-75) as true matrix multiplication using the
   Phase 0 array API: [m,k] x [k,n] -> [m,n] and [m,n] x [n] -> [m]. Remove the
   equal-length dot-product branch and the scalar fallback entirely.
2. Rewrite MatrixTranspose and MatrixInverse against real 2-D shapes.
3. Add blocks matrix_identity, matrix_zeros, matrix_diagonal, matrix_reshape with
   constant shape parameters.
4. Give Selector, Assignment and Concatenate (matrix_ops.py:182-344) 2-D row/column
   addressing. Preserve their existing 1-D behavior.
5. Register every new block in BLOCK_TYPE_MAP, PARAM_MAP and SNAPSHOT_BLOCK_TYPES in
   osk_adapter.py, and add palette entries in frontend/src/blocks/matrix_ops.ts
   matching the style already in that file.
6. No broadcasting anywhere. Mismatched shapes raise with block name, port, expected
   and actual shape.
7. Write backend/tests/test_matrix_ops.py building models through the JSON/registry/
   ModelCompiler path (same style as backend/tests/test_signal_shapes.py). Use EXACTLY
   these known answers; do not invent replacements:
     [[1,2],[3,4]] @ [[5,6],[7,8]]            == [[19,22],[43,50]]
     [[1,2,3],[4,5,6]] @ [[7,8],[9,10],[11,12]] == [[58,64],[139,154]]
     [[1,2],[3,4]] @ [5,6]                    == [17,39]
     transpose([[1,2,3],[4,5,6]])             == [[1,4],[2,5],[3,6]]
     inverse([[4,7],[2,6]])                   == [[0.6,-0.7],[-0.2,0.4]]
     matrix_identity(3), matrix_zeros(2,3), matrix_diagonal([1,2,3])
     matrix_reshape([1,2,3,4,5,6] -> [2,3])   == [[1,2,3],[4,5,6]]
   Plus: [2,3] @ [2,3] raises; 2-D Selector/Assignment/Concatenate cases.
8. ANTI-FALSE-POSITIVE: no xfail, skip, or mocks; do not weaken or edit any Phase 0
   test; do not compute an expected value by calling the block under test; do not
   reintroduce a dot-product or scalar fallback to make a shape case pass.
CHECK:
- You cannot run Docker or commit in your sandbox. Do not try. Edit the OWN files and
  stop; the supervisor runs the container suite and makes the commit.
- Self-check: confirm every DO item is satisfied and no DENY path was touched.
COMMIT: (supervisor) Implement real matrix operations
STOP: no install; no reset/restore/clean; no unrelated cleanup; no edits outside OWN
RESULT: STATUS/PHASE/HEAD/CHECK_EXIT/CHANGED/BLOCKER only
```

## P2

```text
PHASE: P2 Native linear solver
MODE: PROOF
START_HEAD: e6c0e50c34c52acecb70eb32b534a862c9eb5c54
OWN: backend/src/osk/blocks/linear_algebra.py, backend/src/simulation/osk_adapter.py,
     backend/tests/test_linear_solve.py, backend/tests/test_sim_context.py,
     frontend/src/blocks/matrix_ops.ts
DENY: backend/tests/test_signal_shapes.py, backend/tests/test_matrix_ops.py,
      backend/src/osk/block.py, backend/src/simulation/compiler.py,
      backend/src/osk/blocks/** except linear_algebra.py, docs/**,
      backend/pyproject.toml, docker-compose.yml
KEEP: every test in test_signal_shapes.py and test_matrix_ops.py passing and unmodified;
  the Phase 0 tripwire; getOutputVector() still returning flat lists
DO:
1. Create backend/src/osk/blocks/linear_algebra.py with a linear_solve block solving
   A x = b via scipy.linalg.lu_factor / lu_solve (LU with partial pivoting).
   NEVER use an explicit inverse. No factorization cache: factor on every call.
2. Support arbitrary runtime N (at least 30), and a right-hand side that is either a
   vector or a matrix of multiple right-hand sides, with identical numerical semantics.
3. Parameters: method, pivoting, singularity_tolerance, condition_limit, failure_policy.
4. Status outputs, which must NOT alter the numeric solution: success/failure status,
   residual norm ||A x - b||, condition estimate (np.linalg.cond), active dimension.
5. Failure behavior: reject nonsquare A and dimension-mismatched b; detect singular and
   ill-conditioned systems; never emit the previous step's solution; never silently
   substitute a pseudoinverse.
6. Register in BLOCK_TYPE_MAP, PARAM_MAP and SNAPSHOT_BLOCK_TYPES in osk_adapter.py, add
   a palette entry in frontend/src/blocks/matrix_ops.ts, and UPDATE the hardcoded count in
   backend/tests/test_sim_context.py:242 to the new len(BLOCK_TYPE_MAP). Change only that
   integer in that file; touch nothing else there.
7. Write backend/tests/test_linear_solve.py through the JSON/registry/ModelCompiler path.
   Use EXACTLY these known answers; do not invent replacements:
     [[4]] x = [8]                                  -> x == [2]
     [[2,1],[1,3]] x = [3,5]                        -> x == [0.8, 1.4]
     [[2,1,-1],[-3,-1,2],[-2,1,2]] x = [8,-11,-3]   -> x == [2, 3, -1]
     [[2,1],[1,3]] X = [[3,1],[5,0]]                -> X == [[0.8,0.6],[1.4,-0.2]]
   Plus: a 30x30 well-conditioned system checked against np.linalg.solve; a badly scaled
   system; nonsquare A rejected; mismatched b rejected; singular [[1,2],[2,4]] reported as
   failure.
8. STALE-OUTPUT TEST (required): drive one successful solve, then feed singular A on the
   next step, and assert the block does NOT re-emit the earlier solution.
9. ANTI-FALSE-POSITIVE: no xfail, skip, or mocks; do not edit tests owned by earlier
   phases; do not compute an expected value by calling the block under test; do not catch
   a solver exception and return zeros or the last good value.
CHECK:
- You cannot run Docker or commit in your sandbox. Do not try. Edit the OWN files and stop;
  the supervisor runs the container suite and makes the commit.
- Self-check: confirm every DO item is satisfied and no DENY path was touched.
COMMIT: (supervisor) Add native linear solver block
STOP: no install; no reset/restore/clean; no unrelated cleanup; no edits outside OWN
RESULT: STATUS/PHASE/HEAD/CHECK_EXIT/CHANGED/BLOCKER only
```

## P2-REPAIR

```text
PHASE: P2-REPAIR Singularity test must not reject badly scaled systems
MODE: GREEN
START_HEAD: e6c0e50c34c52acecb70eb32b534a862c9eb5c54
OWN: backend/src/osk/blocks/linear_algebra.py, backend/tests/test_linear_solve.py
DENY: everything else, including backend/src/simulation/osk_adapter.py,
      backend/tests/test_sim_context.py, frontend/**, docs/**
KEEP: every other test in test_linear_solve.py passing and unmodified; no explicit
  inverse, pseudoinverse, lstsq, or factorization cache anywhere in linear_algebra.py
DO:
1. FAILING INVARIANT: a badly scaled but nonsingular system is wrongly reported
   singular. With A = [[1e-6,0],[0,1e6]], linear_algebra.py:283 computes
   min_pivot <= singularity_tolerance * max_pivot -> 1e-6 <= 1e-12 * 1e6 -> true,
   so status is 0.0 when it must be 1.0.
2. Fix the ROOT CAUSE: the relative pivot-ratio test conflates bad scaling with
   singularity. Near-singularity is already measured by the condition estimate against
   condition_limit. The pivot test must detect only EXACT/numerical singularity.
   Do not special-case this matrix, do not branch on its values, and do not simply
   delete the singularity check.
3. These must all hold after the fix:
     A = [[1e-6,0],[0,1e6]], b = [2e-6,3e6]  -> status 1.0, x == [2.0, 3.0],
                                                1e11 < condition < 1e13
     A = [[1,2],[2,4]]                        -> still reported singular, status 0.0
     every other existing case in test_linear_solve.py unchanged and passing
4. Fix test_solve_multiple_right_hand_sides, which errors with
   "TypeError: pytest.approx() does not support nested data structures". Compare the
   nested result without pytest.approx on a nested list (for example np.allclose, or
   approx on a flattened list). Keep the expected values EXACTLY
   [[0.8,0.6],[1.4,-0.2]] - do not change what the test asserts, only how it compares.
5. ANTI-FALSE-POSITIVE: do not weaken either failing test to make it pass; do not
   raise singularity_tolerance so far that [[1,2],[2,4]] stops being detected; do not
   catch a failure and emit zeros or a previous solution.
CHECK:
- You cannot run Docker or commit in your sandbox. Do not try. Edit the OWN files and
  stop; the supervisor runs the container suite and makes the commit.
COMMIT: (supervisor) Fix singularity test for badly scaled systems
STOP: no install; no reset/restore/clean; no edits outside OWN
RESULT: STATUS/PHASE/HEAD/CHECK_EXIT/CHANGED/BLOCKER only
```

## P3

```text
PHASE: P3 Reset correctness and acceptance example
MODE: ACCEPT
START_HEAD: a74df34228c83e655d9d148e4272d91111b3b29d
OWN: backend/tests/test_linear_solve_acceptance.py,
     examples/51_linear_solve_acceptance.json,
     backend/src/api/routes/examples.py,
     backend/src/osk/blocks/linear_algebra.py
DENY: backend/tests/test_signal_shapes.py, backend/tests/test_matrix_ops.py,
      backend/tests/test_linear_solve.py, backend/tests/test_sim_context.py,
      backend/src/osk/block.py, backend/src/simulation/compiler.py,
      backend/src/simulation/osk_adapter.py, backend/src/osk/blocks/matrix_ops.py,
      frontend/**, docs/**
KEEP: every existing test passing and unmodified; no explicit inverse, pseudoinverse,
  lstsq, or factorization cache in linear_algebra.py; solver outputs remain a pure
  function of the CURRENT step's inputs
DO:
1. Create examples/51_linear_solve_acceptance.json: a domain-neutral model that builds a
   3x3 A and a 3-vector b at runtime FROM NATIVE SIGNAL BLOCKS (constants/sources feeding
   matrix construction), solves with linear_solve, and exposes solution, residual,
   condition and status to sinks. No application-specific plant, controller, or physics.
   Use A = [[2,1,-1],[-3,-1,2],[-2,1,2]], b = [8,-11,-3], so x == [2, 3, -1].
2. Register it in EXAMPLE_MANIFEST in backend/src/api/routes/examples.py, matching the
   existing entry shape (id/name/description/category). Add only that entry.
3. Create backend/tests/test_linear_solve_acceptance.py covering, through the normal
   JSON/registry/ModelCompiler/headless path:
   a. the example loads, compiles, runs headless, and yields x == [2, 3, -1] with
      status success, small residual, and a finite condition estimate;
   b. determinism: two identical runs produce identical outputs;
   c. reset: after reset the solver reports no stale solution or status from before it;
   d. rejected steps: drive a solve, step back via SimulationRunner step-mode
      (see backend/src/simulation/runner.py:769), and confirm no stale solution survives;
   e. step-back replay round-trips the matrix and linear_solve block snapshots;
   f. deterministic failure: singular A and dimension-invalid input both fail the
      documented way, with no stale output and no zeros substituted for a solution.
4. If any block state needed for (d)/(e) is missing from the snapshot codec, fix it in
   linear_algebra.py only. Do not edit osk_adapter.py; if the fix requires changes there,
   stop and report BLOCKED with the exact reason.
5. ANTI-FALSE-POSITIVE: no xfail, skip, or mocks; do not weaken or edit any earlier
   phase's tests; do not compute an expected value by calling the block under test; do
   not assert only that a key exists — assert its value.
CHECK:
- You cannot run Docker or commit in your sandbox. Do not try. Edit the OWN files and
  stop; the supervisor runs the container suite and makes the commit.
COMMIT: (supervisor) Add linear solver acceptance example and reset tests
STOP: no install; no reset/restore/clean; no edits outside OWN
RESULT: STATUS/PHASE/HEAD/CHECK_EXIT/CHANGED/BLOCKER only
```

## P3-REPAIR

```text
PHASE: P3-REPAIR Snapshot restore must not size sink metadata from live block state
MODE: GREEN
START_HEAD: a74df34228c83e655d9d148e4272d91111b3b29d
OWN: backend/src/simulation/snapshot.py
DENY: everything else, including all test files, backend/src/simulation/osk_adapter.py,
      backend/src/osk/blocks/**, examples/**, frontend/**, docs/**
KEEP: every currently passing test still passing and unmodified, especially the existing
  snapshot and step-mode tests in backend/tests/; the validation must still REJECT
  genuinely malformed snapshot metadata
DO:
1. FAILING INVARIANT: stepping forward then backward with a scope fed a 3-element vector
   raises SnapshotValidationError("Invalid compact sink length metadata") from
   snapshot.py:386, via runner step_backward -> prepare_snapshot_restore.
   Reproduce with: pytest tests/test_linear_solve_acceptance.py::test_step_back_leaves_no_stale_solution
2. ROOT CAUSE: _validate_compact_lengths (snapshot.py:374-386) computes
       expected = len(fields); if block_type == "scope": expected += len(block.values)
   using the LIVE block's current channel count. Scope.values starts empty
   (backend/src/osk/blocks/sinks.py:28) and channels are allocated lazily on first update
   (sinks.py:119-120). A snapshot taken at t=0 therefore records 0 channels while the live
   block has 3 by restore time, so a VALID snapshot is rejected.
3. Fix so the expected length is derived from the SNAPSHOT's own recorded metadata rather
   than the live block's current channel count, and so restoring a snapshot whose channel
   count differs from the live block works correctly (including _truncate_compact_sink).
   Do not simply delete the check, do not blanket try/except, and do not special-case the
   "scope" block type away.
4. Malformed metadata must STILL be rejected: a snapshot whose compact_sink_lengths is
   inconsistent with its own recorded fields/channels must still raise
   SnapshotValidationError.
5. ANTI-FALSE-POSITIVE: do not edit, weaken, xfail or skip any test; do not relax the
   check to accept any length; do not make restore silently ignore a length mismatch.
CHECK:
- You cannot run Docker or commit in your sandbox. Do not try. Edit snapshot.py and stop;
  the supervisor runs the container suite and makes the commit.
COMMIT: (supervisor) Fix snapshot restore for sinks with lazily allocated channels
STOP: no install; no reset/restore/clean; no edits outside OWN
RESULT: STATUS/PHASE/HEAD/CHECK_EXIT/CHANGED/BLOCKER only
```

## P0-GREEN

```text
PHASE: P0-GREEN Shape on the signal path
MODE: GREEN
START_HEAD: 05c205da54c7b7218960091a2f50b9dfaf82197a
OWN: backend/src/simulation/osk_adapter.py, backend/src/osk/block.py, backend/src/simulation/compiler.py
DENY: backend/tests/**, frontend/**, docs/**, backend/src/osk/blocks/**
KEEP: backend/tests/test_signal_shapes.py exactly as committed in P0-RED; all
  existing tests passing; getOutputVector() continues to return flat lists
DO:
1. Widen _OutputPortView (osk_adapter.py:1043-1071) to carry 2-D dimensions and
   add getOutputArray() returning a shaped numpy ndarray.
2. Add getOutputArray(port=0) and setInputArray(value, port=0) to the base Block
   (backend/src/osk/block.py), defaulting to a bridge over getOutputVector()/getOutput().
3. Implement the tripwire: a 2-D signal reaching a consumer that only understands
   flat lists RAISES at model build with block name, port, and shape in the message.
   Never flatten a matrix and never degrade it to a scalar.
4. Ensure a 2-D [m,n] survives _flatten_subsystems (compiler.py:269-421) and
   JSON round-trip.
5. ANTI-FALSE-POSITIVE: do not edit or weaken any test; do not add xfail/skip;
   do not special-case test model names; do not touch the 84 getOutputVector()
   pull sites in backend/src/osk/blocks/ or the four setInput push sites in _step.
CHECK:
- You cannot run Docker or commit in your sandbox. Do not try. Edit the OWN files
  and stop; the supervisor runs the container suite and makes the commit.
- Self-check instead: re-read your edits and confirm every DO item is satisfied and
  no DENY path was touched.
COMMIT: (supervisor) Carry matrix shape through the signal path
STOP: no install; no reset/restore/clean; no unrelated cleanup; no edits outside OWN
RESULT: STATUS/PHASE/HEAD/CHECK_EXIT/CHANGED/BLOCKER only
```
