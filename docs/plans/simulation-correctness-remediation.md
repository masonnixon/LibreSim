# LibreSim — Simulation Correctness Remediation Plan

> Produced 2026-07-09 on branch `uimods` by a deep-dive audit (Claude Fable 5).
> Supersedes the findings analysis in `.claude/docs/fable-audit-2026-07-07.md` where they
> disagree (that audit analyzed the wrong execution path for finding #1 — see §1.2).
> Code-quality / dead-code refactors live in `docs/plans/refactoring-recommendations.md`;
> this plan covers **correctness, concurrency, verification gates, and hardening** only.
>
> This document is written to be executed task-by-task by coding agents of varying
> capability. Each task states the capability tier it needs. Do not attempt a task
> whose tier exceeds yours; report back instead.

---

## 0. Ground rules for any agent executing this plan

1. **All tests, linters, and type checks run inside Docker — never on the host.**
   The backend image does not include dev tools (`requirements.txt` has no pytest), so use:
   ```bash
   docker compose run --rm backend sh -c "pip install -q -e '.[dev]' && pytest tests/ -q"
   docker compose run --rm backend sh -c "pip install -q -e '.[dev]' && ruff check src/ tests/ && mypy src/ --config-file=pyproject.toml"
   ```
   Frontend: `docker compose run --rm frontend npm test -- --run` and `docker compose run --rm frontend npx tsc --noEmit`.
2. **Every fix ships with its regression test in the same commit.** A bug fix without a
   test that fails on the old code is incomplete. Follow the pattern of
   `backend/tests/test_crosstalk_bug.py` (named regression test for a past bug).
3. **Commit messages**: plain human-style description only. **No AI attribution, no
   `Co-Authored-By`, no `Generated with` footers.** Do not push. Leave commits for the
   maintainer to verify.
4. One task per commit (or small commit series). Do not mix tasks. Do not reformat or
   "improve" code outside the task's stated files.
5. Work test-first where a task says "write the failing test first" — run it, confirm it
   fails for the stated reason, then fix.
6. If observed behavior contradicts this document (the code may have moved), stop and
   report the discrepancy rather than forcing the instructions through.

---

## 1. System orientation (read before any task)

### 1.1 Layer map

| Layer | Files | Role |
|---|---|---|
| OSK kernel | `backend/src/osk/state.py`, `osk/sim.py`, `osk/block.py` | Port of H.R. Sells' OSK: multi-pass integrator (`State`), orchestrator (`Sim`). Timing lives in **class attributes** (process-global). |
| Block library | `backend/src/osk/blocks/*.py` (~13.5k lines, 20 domains) | Source blocks compute outputs from `State.t` (Sine, Step, Clock, TransportDelay at `continuous.py:582`, plus rf/nonlinear/discrete/sensor_fusion). |
| Compiler | `backend/src/simulation/compiler.py` | Visual model JSON → execution order (topo sort, algebraic-loop detection, subsystem flattening). |
| Adapter | `backend/src/simulation/osk_adapter.py` (~1800 lines) | Creates OSK blocks from compiled model; **owns the app's real integration loop** (`step()`, line ~1191). |
| Runner | `backend/src/simulation/runner.py` | Async orchestration: run/pause/step-mode/step-backward; calls `adapter.step(t, dt)` per step. |
| API | `backend/src/api/routes/*.py`, `main.py` | FastAPI. `/api/simulate/start` launches `runner.run()` via `BackgroundTasks` into a **module-global `_runner`**. |
| Codegen | `backend/src/codegen/` | Generates standalone Python/C/C++/Rust projects. Integrator math templates in `codegen/integration.py`; per-language main loops in `codegen/languages/{python,c,cpp,rust}/generator.py`. |
| Verification | `tests/test_codegen_accuracy.py`, `scripts/validate_codegen.py`, `codegen_verification/*.zip` | Compares generated code against a backend reference run. |

### 1.2 The three integration loops — and which are wrong (critical context)

There are **three independent implementations** of the multi-pass integration loop.
They currently disagree:

| Loop | Where | RK4 coefficients | Stage time advanced during passes? | Who uses it |
|---|---|---|---|---|
| A. Adapter loop | `osk_adapter.py: step()` | **Correct** (classical RK4; `State.dt` stays = h; `_propagate_rk4` hardcodes the ½ factors) | **No — bug.** `State.t` pinned to step-start for all 4 passes | The application (runner → every UI simulation, step mode) |
| B. Kernel loop | `sim.py: Sim.run()` + `state.py: updateclock()` | **Wrong — bug.** `updateclock` halves `State.dt` for kpass 1 *and* `_propagate_rk4` applies dt/2 again → k2 stage uses h/4, degrading RK4 to ~2nd order | **No — bug.** `t` only advances by `dtp` on step completion | `adapter.run_simulation()` — which is the **ground truth** for `test_codegen_accuracy.py`; also `test_osk.py` |
| C. Generated code | `codegen/integration.py` templates + each language's `run_simulation` main loop | **Correct** (identical stage math in all 4 languages) | **No — bug.** Main loops call `model.step(t, dt, kpass)` with unmodified `t` for every pass (python `generator.py:436`, c/cpp `:195`, rust `:207`) | Exported user projects; CI codegen validation |

Consequences you must internalize before touching anything:

- **Loops A and C agree with each other** and implement correct RK4 *coefficients*; only
  loop B has the h/4 coefficient bug. The 2026-07-07 audit attributed that bug to "every
  RK4 simulation in the app" — that is wrong; the app uses loop A.
- **All three loops share the stage-time bug**: for any model driven by time-varying
  sources (sine, step, ramp, clock — i.e., most models), k2/k3/k4 are evaluated with the
  step-start time, collapsing effective accuracy of the drive terms to ~1st order
  regardless of method. Because all three loops share it consistently, no existing
  cross-check can see it. Only a convergence-order test against an analytic solution can.
- The codegen accuracy test's ground truth (loop B) is the buggiest loop. Its RMS-1%
  tolerance is what lets correct generated code "match" a wrong reference.

### 1.3 Stage-time reference table (used by LS-2)

Offsets from step-start time `t`, per pass `kpass` (this is when each stage's
derivatives should be evaluated — i.e., what `State.t` must be **during** that pass's
block updates):

| Method | pass 0 | pass 1 | pass 2 | pass 3 | pass 4 |
|---|---|---|---|---|---|
| Euler | 0 | | | | |
| RK2 (midpoint) | 0 | h/2 | | | |
| RK4 | 0 | h/2 | h/2 | h | |
| Merson | 0 | h/3 | h/3 | h/2 | h |

---

## 2. Task catalog

Execute in numeric order unless a task says otherwise. Capability tiers:
**T1-any** (mechanical, fully specified), **T2-mid** (multi-file, local judgment),
**T3-strong** (cross-cutting, numerical verification judgment).

---

### LS-1 — Fix RK4 h/4 coefficient bug in `State.updateclock()` (loop B)

**Priority:** P0 · **Effort:** small · **Capability:** T1-any · **Depends on:** nothing

**Files:** `backend/src/osk/state.py`, new `backend/tests/test_integration_accuracy.py`

**Why:** `updateclock()` (`state.py:165-191`) halves `State.dt` when `kpass` is 1 (the
`kpass in [0, 1]` check is post-increment, so 0 never occurs), while `_propagate_rk4`
already applies its own `dt/2` on passes 0–1. Double-halving → the k2 stage advances by
h/4 instead of h/2, silently degrading loop B's RK4 to ~2nd order. Loop B is the ground
truth for codegen accuracy tests, so this pollutes verification too. The Merson branch
is already correct (keeps `dt = dtp`); RK2 is accidentally correct.

**Steps:**
1. Write the failing test first, in a new `backend/tests/test_integration_accuracy.py`.
   Use the kernel directly (loop B), following the `SimpleBlock` pattern at the bottom of
   `backend/tests/test_osk.py`. Create a decay block whose state solves x' = −x, x(0)=1:

   ```python
   class DecayBlock(Block):
       """x' = -x integrated by the OSK State machinery."""
       def __init__(self, x0=1.0):
           super().__init__()
           self.s = State([x0, 0.0])
           self.initCount = 0
       def init(self): pass
       def update(self): self.s.x[1] = -self.s.x[0]
       def rpt(self): pass
       def getOutput(self, port=0): return self.s.x[0]
       def propagateStates(self): self.s.propagate()
   ```

   Test: for `State.method = "RK4"`, run `Sim(dts=[h], tmax=1.0, vStage=[[block]])` for
   h = 0.1 and h = 0.05; error against `exp(-1)` must shrink by ≈16× (assert ratio > 12).
   Run it; it must FAIL on current code (ratio will be ≈4, i.e., 2nd order).
2. Fix `updateclock()`: delete the per-method `dt` juggling in the `else` branch and set
   `State.dt = State.dtp` unconditionally (matching what `reset()` establishes and what
   the Merson branch already does). The RK2 conditional there is dead-in-effect
   (post-increment kpass ≥ 1 always selects `dtp`); removing it changes nothing for RK2.
3. Add the same convergence assertions for Euler (ratio ≈2), RK2 (≈4), Merson (≈16),
   with generous lower bounds (Euler > 1.7, RK2 > 3.2, RK4/Merson > 12).
4. Do NOT touch `_propagate_rk4` — its hardcoded `dt/2` factors are the correct
   convention. Do NOT touch `osk_adapter.py` or `codegen/` in this task.

**Acceptance:** new tests pass; full `pytest tests/ -q` passes in Docker;
`test_osk.py::test_state_updateclock_rk4` still passes (it asserts kpass/t transitions,
not dt values — if it broke, you changed too much).

**Pitfalls:** `State` timing is class-global — tests must set `State.method` and call
`Sim(...)`/`state.set()` in setup so leakage from other tests can't skew results.

---

### LS-2 — Advance stage-local time during integration passes (all three loops)

**Priority:** P0 · **Effort:** large · **Capability:** T3-strong · **Depends on:** LS-1

**Files:** `backend/src/simulation/osk_adapter.py` (`step()`),
`backend/src/osk/state.py` (`updateclock()`), `backend/src/codegen/integration.py`
(add stage-offset emitters), `backend/src/codegen/languages/{python,c,cpp,rust}/generator.py`
(main loops), `backend/tests/test_integration_accuracy.py` (extend),
regenerated `codegen_verification/` fixtures.

**Why:** During multi-pass integration, every source block reads the current time
(`State.t` in the backend; the `t` argument in generated code). All three loops evaluate
every pass at step-start time (§1.2), so for driven systems (x' = f(t, x) with
time-varying f) intermediate stages sample f at the wrong time and RK2/RK4/Merson lose
their order in the drive terms. Use the offsets table in §1.3.

**This change must land in all three loops in one commit series** — they are
cross-checked against each other by `test_codegen_accuracy.py` and
`scripts/validate_codegen.py`, and a partial change will make those fail (correctly).

**Steps:**
1. Failing test first (extend `test_integration_accuracy.py`): drive the **adapter loop**
   with a driven system. Build a minimal model dict inline (sine_wave source →
   integrator → scope; copy the JSON shape from `examples/01_sine_wave_basic.json` plus
   an integrator, or programmatically via `Model.model_validate`). Run through
   `ModelCompiler` + `OSKAdapter.initialize` + repeated `adapter.step(t, dt)` exactly the
   way `runner.run()` does. Analytic truth: ∫₀ᵗ sin(τ)dτ = 1 − cos(t). Assert RK4 error
   ratio between h and h/2 is > 12. Must FAIL on current code (~2–4×).
2. Adapter fix (`osk_adapter.py step()`): both the `is_first_step` branch and the normal
   branch have a `for kpass in range(num_passes):` loop. Add a module-level constant:
   ```python
   STAGE_TIME_OFFSETS = {
       "Euler": [0.0],
       "RK2": [0.0, 0.5],
       "RK4": [0.0, 0.5, 0.5, 1.0],
       "Merson": [0.0, 1.0 / 3.0, 1.0 / 3.0, 0.5, 1.0],
   }
   ```
   At the top of each pass iteration set
   `State.t = t + STAGE_TIME_OFFSETS[State.method][kpass] * dt`; after the pass loop set
   `State.t = t + dt` (state now corresponds to end-of-step). The pre-integration
   record/rpt section must keep running at `State.t = t` — don't move it.
3. Kernel fix (`state.py updateclock()`): `State.t1` currently means "previous time".
   Repurpose it as **step-start time** (verify first: `grep -rn "State.t1"` — as of this
   writing its only consumers are `state.py` itself and `osk_adapter.get_state/set_state`
   passthrough). New behavior:
   - on intermediate pass: `State.ready = 0; State.t = State.t1 + offset[kpass] * State.dtp`
   - on completion: `State.kpass = 0; State.t1 += State.dtp; State.t = State.t1; State.ready = 1`
   - `State.dt = State.dtp` always (from LS-1).
   Extend the LS-1 loop-B convergence test with the driven case (a block whose
   `update()` sets `self.s.x[1] = math.sin(State.t)`).
4. Codegen fix: in `codegen/integration.py`, emit a `get_stage_offsets(method)` (Python)
   and equivalent static tables for C/C++/Rust alongside the existing
   `get_num_passes`. In each language generator's `run_simulation`/`main` template,
   change the per-pass call from `model.step(t, dt, kpass)` to
   `model.step(t + offsets[kpass] * dt, dt, kpass)` (python `generator.py` ~line 436,
   c/cpp ~line 195-196, rust ~line 207-208). The recording branch (`if kpass == 0`)
   still records at `t` — unchanged.
5. Regenerate verification fixtures: `python scripts/regenerate_all_examples.py` then
   `python scripts/validate_codegen.py`. These need compilers; run them in a
   `python:3.11` container with `build-essential` and rustup, mirroring the
   `codegen-validation` job in `.gitlab-ci.yml` — not on the host.
6. Expect fallout in golden/expected-output tests: `tests/test_codegen.py` (240k lines,
   largely template string expectations) will break where main-loop text changed —
   update those expectations to the new template text deliberately, hunk by hunk.
   Numerical tests (`test_codegen_accuracy.py`, `test_blocks.py`, `test_simulation.py`)
   should get *closer* to analytic values; if any numerical expectation was calibrated to
   the buggy output, recompute it against the analytic solution and say so in the commit
   message.

**Acceptance:** driven and autonomous convergence tests pass at proper orders on both
loop A and loop B; `test_codegen_accuracy.py` passes with the existing tolerances
(tighten `MAX_RMS` if it passes easily); full backend suite green in Docker;
`validate_codegen.py` pass rate ≥ previous report (`docs/codegen-validation-report.md`).

**Pitfalls:**
- Discrete blocks (unit_delay, discrete transfer functions, zero_order_hold) sample
  time to decide ticks; they should act on **completed** steps only. If a discrete-block
  test starts double-ticking, gate its time-read on `State.ready == 1` semantics rather
  than reverting stage time. Investigate, don't paper over.
- `TransportDelay` (`continuous.py:582`) buffers `(State.t, value)` pairs — confirm it
  only appends when `State.ready == 1` / kpass 0, otherwise it will buffer stage-time
  duplicates.
- Step-backward: `get_state()/set_state()` save/restore `t`/`t1` — meanings unchanged
  (both are step-boundary values there), but run the step-mode tests in
  `test_simulation.py` to confirm.

---

### LS-3 — Prevent overlapping simulation runs from corrupting each other

**Priority:** P0 · **Effort:** medium · **Capability:** T2-mid · **Depends on:** nothing (parallel-safe with LS-1/2)

**Files:** `backend/src/api/routes/simulation.py`, `backend/src/simulation/runner.py`,
new test in `backend/tests/test_api.py` or a new `test_concurrent_runs.py`.

**Why:** OSK timing is class-global (`State.t/dt/kpass/method`, `Sim.*`). The runner is
async and yields every 100 steps (`runner.py:355-356, 421-422`), and `/api/simulate/start`
(`routes/simulation.py:33-80`) **replaces the module-global `_runner` without stopping
the old one** — the old `BackgroundTasks` coroutine keeps stepping, and both runs
scribble over the same `State` class attributes (worst case: different solver methods —
`initialize()` sets `State.method`, so run A silently continues with run B's method).
Clicking Run twice reproduces this today.

**Interim fix (this task): serialize runs.** The instance-based refactor is LS-10.

**Steps:**
1. Add to `SimulationRunner`:
   ```python
   async def stop_and_wait(self, timeout: float = 5.0) -> bool:
       """Request stop and wait until the run loop has actually exited."""
       self._should_stop = True
       deadline = time.time() + timeout
       while self._status in (SimulationStatus.RUNNING, SimulationStatus.COMPILING):
           if time.time() > deadline:
               return False
           await asyncio.sleep(0.05)
       return True
   ```
   (Import `asyncio`; module already imports `time`. Check the actual
   `SimulationStatus` enum members in `src/models/simulation.py` before writing this.)
2. In `/start` and `/step/init`: if the existing `_runner` is active, `await
   _runner.stop_and_wait()` before constructing the new one; return HTTP 409 if it
   refuses to die within the timeout. Guard the whole check-and-replace with a
   module-level `asyncio.Lock` so two concurrent `/start` requests cannot interleave.
3. Regression test: FastAPI `TestClient`, start a long simulation (`stop_time` large,
   `step_size` tiny, any example model), immediately `/start` a second one with a
   *different* solver, poll `/status` until the second completes, and assert results are
   the same as running the second model alone (or minimally: assert the second run
   completes without error and the first is no longer RUNNING).

**Acceptance:** new test passes; double-`/start` no longer leaves two live loops
(add a `SimulationRunner._instances`-style assertion only if trivial — otherwise the
status assertions suffice); existing `test_api.py` green.

**Pitfall:** don't hold the lock across the whole simulation — only across
stop-old/create-new. The background task itself must run unlocked.

---

### LS-4 — Make verification gates real (CI + accuracy ground truth)

**Priority:** P1 · **Effort:** medium · **Capability:** T2-mid · **Depends on:** LS-1 (ideally LS-2)

**Files:** `.github/workflows/ci.yml`, `.gitlab-ci.yml`,
`backend/tests/test_codegen_accuracy.py`, `scripts/validate_codegen.py`.

**Why:** Three gates are currently decorative:
1. GH Actions runs frontend tests with `continue-on-error: true` ("may not exist yet" —
   stale: `frontend/src/**/*.test.ts` exist and are substantial); GitLab uses `|| true`.
2. Codegen validation pass-rate is explicitly "informational" in both CIs.
3. `test_codegen_accuracy.py` uses `adapter.run_simulation()` (loop B — the buggy one)
   as ground truth, and only for Python.

**Steps:**
1. Remove `continue-on-error: true` (GH `ci.yml:126`) and the `|| true` (GitLab `:102`).
   Run the frontend suite in Docker first; if specific tests are legitimately broken,
   list them in your report — do not skip them silently.
2. In `test_codegen_accuracy.py`, switch `run_backend_simulation()` to drive the
   **adapter loop** (initialize + repeated `step(t, dt)`, mirroring `runner.run()`)
   instead of `run_simulation()`, so ground truth is what the app actually shows users.
   After LS-1/LS-2 the two loops should agree — if you land this before LS-2, keep the
   tolerance as-is and tighten after.
3. `validate_codegen.py`: make the pass-rate a hard threshold (exit nonzero below the
   current report's rate, read from `docs/codegen-validation-report.md` history), and
   fail both CI jobs on regression.

**Acceptance:** CI configs contain no soft-fail on tests; accuracy tests reference the
adapter path; both CI files stay mirrored (per the header comment in `.gitlab-ci.yml`).

---

### LS-5 — Bound result memory and fix O(n²) step-history snapshots

**Priority:** P1 · **Effort:** medium · **Capability:** T2-mid · **Depends on:** nothing

**Files:** `backend/src/simulation/runner.py`, tests in `backend/tests/test_simulation.py`.

**Why:** Two unbounded-growth problems:
- `_record_outputs` appends every sink output every step forever (`runner.py:442-447`);
  `_max_history_size` bounds only step-mode history, not `_results`.
- `_save_state()` (`runner.py:155-175`) `copy.deepcopy(self._results)` on **every step
  forward** — snapshot i copies i steps of data: O(n²) time/memory over a stepping
  session, on top of 1000 retained snapshots.

**Steps:**
1. Add `max_result_points` to `SimulationConfig` (default e.g. 100_000 per signal) and
   decimate-by-2 (keep every other point) when a signal exceeds it, recording the
   effective decimation factor in `get_results()` statistics. Straight truncation is NOT
   acceptable — users need the whole time range at reduced density.
2. In `_save_state`, stop deep-copying `_results`. Store per-signal *lengths* instead,
   and on `_restore_state` truncate `self._results` lists back to the saved lengths
   (results are append-only during forward stepping, so truncation restores exactly).
   Keep deep-copying `adapter_state` (small).
3. Tests: (a) long-run decimation keeps point count ≤ limit and preserves first/last
   times; (b) step forward ×5, backward ×3 yields identical `_results` to the old
   deepcopy behavior (write the equivalence test before refactoring, using the current
   implementation to produce the expected data).

**Acceptance:** step-mode tests in `test_simulation.py` green; new tests green; no
`copy.deepcopy(self._results)` remains.

---

### LS-6 — Nested subsystem flattening silently drops contents (verify, then fix)

**Priority:** P1 · **Effort:** medium · **Capability:** T2-mid · **Depends on:** nothing

**Files:** `backend/src/simulation/compiler.py` (`_flatten_subsystems`),
`backend/tests/test_compiler.py`.

**Why (suspected — verify first):** `_flatten_subsystems` iterates top-level blocks only.
When a subsystem's child is itself a subsystem, the child copy is constructed
(`compiler.py:302-310`) **without** `children`/`child_connections`, so the inner
subsystem's contents vanish; downstream it's neither flattened nor executable.

**Steps:**
1. Write the failing test first in `test_compiler.py`: model with subsystem A containing
   subsystem B containing (inport → gain → outport), wired through both boundaries.
   Compile; assert the gain block appears in `execution_order` with a doubly-prefixed id
   (`A__B__gain...`). Confirm it fails (block missing).
2. If it unexpectedly passes, stop — report that this finding is invalid, delete nothing.
3. Fix by making flattening recursive: recurse on `block.children` before processing the
   parent (post-order), or loop `while any(b.type == "subsystem" for b in blocks)` with a
   depth cap (e.g. 32) to avoid infinite loops on malformed self-referential input.
   Preserve the existing prefixing scheme so ids remain unique and stable.

**Acceptance:** new nested test passes; all existing `test_compiler.py` and
`test_simulation.py` subsystem tests pass unchanged.

---

### LS-7 — Unknown block types must fail compilation, not silently become `Gain(1.0)`

**Priority:** P1 · **Effort:** small · **Capability:** T1-any · **Depends on:** nothing

**Files:** `backend/src/simulation/osk_adapter.py` (`_create_osk_block`, ~lines 908-938),
tests in `backend/tests/test_simulation.py`.

**Why:** Already flagged as item #3 in `docs/plans/refactoring-recommendations.md`, but it
is a correctness bug, so it belongs in this plan's execution order: an unknown/failed
block type is silently replaced by a unity-gain pass-through with only a `print()`. The
simulation then produces confidently wrong numbers.

**Steps:** raise a `ValueError` (or the adapter's existing error convention) naming the
block id and type; let `initialize()` propagate it so the runner reports
`SimulationStatus.ERROR` and the API returns the message. Test: model containing
`"type": "does_not_exist"` → `/api/simulate/start` then `/status` shows `error` with the
block name in the message; also a direct adapter-level unit test.

**Acceptance:** no silent fallback path remains; error surfaces through `/status`.

---

### LS-8 — Kernel hygiene batch (loop B / `Sim` internals)

**Priority:** P2 · **Effort:** small-medium · **Capability:** T2-mid · **Depends on:** LS-1, LS-2

Three small items, one commit each, all in `backend/src/osk/`:

1. **`sample()` periodic branch is a no-op** (`state.py:67-80`): the non-event branch
   unconditionally sets `ready = 1`, ignoring `sdt`. Its only callers pass
   `State.EVENT` (`sim.py:68,119`). Remove the dead periodic branch and the `sdt`
   parameter *or* implement periodic sampling faithfully — decide by checking the
   original OSK C++ if available; default to removal (YAGNI) with a docstring note.
2. **Results keyed by `id(obj)`** (`sim.py:135-138`): `id()` is reuse-prone and opaque.
   Give `Block` an optional `block_id: str | None` attribute (the adapter already knows
   compiled ids — set it in `_create_osk_block`); key `results["outputs"]` by
   `getattr(obj, "block_id", None) or id(obj)`. Note: `run_simulation()` currently
   ignores `results["outputs"]` (it reads sink `getData()`), so risk is low.
3. **`Sim` mutable class-attribute defaults and dead `vObj`** (`sim.py:40-47`):
   remove `vObj`; keep the class-attribute *assignment* pattern (it's how the kernel
   works pre-LS-10) but drop the mutable defaults (`dts: list = []`) in favor of
   `None`-initialized declarations assigned in `__init__`.

**Acceptance:** `test_osk.py` green (update the tests that poke these internals);
no behavior change in adapter-path tests.

---

### LS-9 — API hardening batch

**Priority:** P2 · **Effort:** small · **Capability:** T1-any · **Depends on:** nothing

One commit per item:

1. **`Content-Disposition` filename injection** (`codegen/controller.py:106,248`): the
   sanitized name is only used when `project_name == "simulation"`; a caller-supplied
   `project_name` goes into the header raw. Always pass the final name through
   `sanitize_project_name()`. Test: request with `project_name='x"; rm -rf'`-style junk
   returns a clean filename.
2. **Example id lookup** (`routes/examples.py:288-302`): `example_id` is joined into a
   path. Traversal is largely blocked by the single-segment route + `.json` suffix, but
   make it structural: look the id up in `EXAMPLE_MANIFEST` and 404 if absent. Test:
   `GET /api/examples/../../etc/passwd` and `GET /api/examples/unknown` → 404.
3. **WebSocket** (`api/websocket.py`): note only — no origin check and
   `parameter_update` is an unimplemented stub; the refactoring plan (#4) proposes
   removing dead WS code. Do not build anything here; just ensure whichever survives
   checks `websocket.headers.get("origin")` against `settings.cors_origins_list`.

---

### LS-10 — Long-term: instance-scoped simulation context (design outline, not yet scheduled)

**Priority:** P3 (do not start without maintainer sign-off) · **Capability:** T3-strong ·
**Depends on:** LS-1, LS-2, LS-3, LS-4 all merged and green.

The proper fix for §1.2's global-state problem: a `SimContext` instance (t, t1, dt, dtp,
kpass, ready, method) owned by the adapter/runner, passed to blocks (constructor or a
`ctx` attribute set at creation), replacing every `State.<attr>` class read in
`osk/blocks/` (7 files read `State.t` today — see grep in §1.1). This unlocks true
concurrent simulations and removes LS-3's serialization. It touches every block file and
all kernel tests; treat as its own plan document when scheduled. Until then, LS-3's
serialization is the supported concurrency story.

---

## 3. Do-NOT list (things that look like bugs but are not, or are out of scope)

- **Do not** "fix" the ½ factors in `state.py:_propagate_rk4`, `codegen/integration.py`,
  or any generated-language RK4 — those coefficients are correct classical RK4. The LS-1
  bug is only the *extra* halving in `updateclock()`.
- **Do not** modify Merson coefficients anywhere; all implementations are consistent and
  correct.
- **Do not** hand-edit anything in `codegen_verification/` — regenerate via scripts
  (LS-2 step 5). (Moving these 156 zips out of git is refactoring-plan #20, not here.)
- **Do not** commit changes to `docker-compose.yml` / `frontend/vite.config.ts` host
  names — the current working-tree diffs are the maintainer's local Tailscale setup.
  (Separate nicety, ask first: move `VITE_API_URL`/`CORS_ORIGINS`/allowedHosts to an
  untracked `.env` consumed by compose.)
- **Do not** convert `State` to instance attributes as a drive-by "cleanup" — that is
  LS-10 and requires sign-off.
- The `print()` logging noise is refactoring-plan #7; don't interleave it with these
  tasks except where a task's own diff touches the line anyway.

## 4. Status ledger

Agents: update this table in the same commit as the work.

| Task | Status | Commit | Notes |
|---|---|---|---|
| LS-1 | complete | this commit | Restored RK4 fourth-order autonomous convergence. |
| LS-2 | not started | | |
| LS-3 | not started | | |
| LS-4 | not started | | |
| LS-5 | not started | | |
| LS-6 | not started | | |
| LS-7 | not started | | |
| LS-8 | not started | | |
| LS-9 | not started | | |
| LS-10 | blocked (needs sign-off) | | |
