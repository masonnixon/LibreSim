# LibreSim — FAC-9 SimContext and Concurrent Simulations

> **Status:** implementation in progress; Phases 0-4 completed through `e33a9fd`
> **Drafted:** 2026-07-16
> **Closes:** FAC-9 / LS-10
> **Parent plan:** `docs/plans/fable-audit-completion.md`

## 1. Decision requested

Approve the instance-scoped simulation-state design and migration below.

The recommended API policy is:

- independent simulations can run concurrently in one process;
- `/start` and `/step/init` keep their existing stop-and-replace behavior by default;
- callers opt into coexistence with `replaceCurrent: false`;
- control and read routes accept an optional `sessionId` so a caller can address any
  retained session; and
- omitted session IDs continue to address the most recently installed session.

This policy preserves the current frontend contract while making the `sessionId`
already returned by the API meaningful. Changing concurrent creation to the default,
or designing a distributed multi-worker session store, is not part of FAC-9.

The maintainer approved this plan and the API policy above on 2026-07-16. Production
implementation begins after the pre-FAC-9 verification checkpoint is recorded.

## 2. Problem statement and evidence

LibreSim currently gives each `SimulationRunner` and `OSKAdapter` its own model and
block graph, but not its own simulation clock:

- `State.t`, `t1`, `dt`, `dtp`, `ready`, `kpass`, `method`, and tick flags are mutable
  class attributes shared by the process;
- `Sim.stop`, `stop0`, `dts`, `tmax`, `vStage`, and `clock` are also class state;
- adapter initialization and every solver stage overwrite `State.*`; and
- blocks throughout the OSK library read `State.t`, `State.dt`, and `State.ready`
  directly.

A direct characterization probe demonstrates the failure: initialize simulation A as
Euler with `dt=0.1`, then initialize simulation B as RK4 with `dt=0.01`; the shared
method becomes RK4 for both, and stepping either adapter changes the timing snapshot
observed by the other. Separate block graphs therefore do not provide isolation.

The API adds a second limitation. It stores one module-global runner, and its lock only
serializes stop-and-replace installation. Although `/start` returns a `sessionId`, later
status, result, and control routes do not use it. This supports replacement, not
coexisting sessions.

The existing adapter checkpoint format is also too weak for instance-scoped state. It
is unversioned, omits solver method, step sizes, tick flags, and stop state, and restores
block attributes through a partial heuristic. Timing isolation and rollback cannot be
considered complete until those fields have an explicit snapshot contract.

## 3. Goals, non-goals, and invariants

### Goals

1. Give every independent runner/adapter a distinct mutable simulation context.
2. Allow runners using different solvers and step sizes to execute concurrently without
   clock, integrator, pause, result, or checkpoint cross-talk.
3. Make direct OSK `Sim` executions instance-scoped as well as adapter executions.
4. Preserve source compatibility for external/custom blocks that still read
   `State.t` during a documented migration window.
5. Expose backward-compatible, session-addressed API concurrency.
6. Replace heuristic timing snapshots with a versioned, validated state contract.
7. Retain numerical behavior and the completed 156/156 generated-code validation
   baseline.

### Non-goals

- Parallel stepping of the same runner or block graph.
- Sharing a mutable block instance between simulations.
- Cross-process session storage or coordination between multiple Uvicorn workers.
- Altering generated-code runtime architecture; generated programs already own their
  runtime variables.
- Removing the `State.*` compatibility facade in the same change.
- Supporting snapshots in the middle of a multi-pass solver step.
- Capturing arbitrary, unknown custom-block state without an explicit snapshot hook.

### Required invariants

- A mutable `SimContext` has exactly one owning runner/adapter execution graph.
- Context ownership is enforced with an owner claim; supplying one context to a second
  live graph is rejected, and lifecycle reset does not release or replace the claim.
- Reset mutates the existing context in place; it never swaps the object referenced by
  blocks and integrator states.
- Every built-in block and every `State` integrator in a graph is bound to that graph's
  context before `init()` or `update()`.
- One runner permits at most one active stepping coroutine. Different runners may step
  concurrently.
- Registry locks protect registry mutations only; they are never held while a simulation
  runs, waits, pauses, stops, or compiles.
- Snapshots are accepted only at committed step boundaries and restore atomically.
- Default creation replaces only the current session, omitted IDs resolve the current
  session, and existing endpoint-specific no-runner responses remain unchanged.
  Explicitly retained non-current sessions are not stopped by a later default creation.

## 4. Target architecture

### 4.1 `SimContext`

Add an OSK-owned dataclass containing all mutable execution-wide state:

```python
@dataclass
class SimContext:
    t: float = 0.0
    t1: float = 0.0
    dt: float = 0.01
    dtp: float = 0.01
    method: str = "RK4"
    kpass: int = 0
    ready: int = 1
    tickfirst: int = 1
    ticklast: int = 0
    stop: int = 0
    stop0: int = 0
```

`EPS`, `EVENT`, and stage-offset tables remain immutable module constants. Context
methods own clock transitions such as reset, stage entry, sampling, step completion,
and stop requests so the adapter loop and native `Sim` loop use one timing contract.
Invalid stage/pass transitions fail explicitly. FAC-9 preserves the existing unknown
method fallback to RK4; changing that public behavior requires a separate decision.

### 4.2 Explicit references are authoritative

- `SimulationRunner` creates one context and passes it to its adapter.
- A directly constructed `OSKAdapter` creates its own context unless one is supplied.
- `OSKAdapter.initialize()` resets that same object in place and binds every constructed
  block to it.
- `Block` holds `self.context`; `addIntegrator()` creates a `State` bound to it. A block
  built before an owner exists uses the active/default context provisionally.
- Because many integrators are created in block constructors before adapter binding,
  `Block.bind_context()` may rebind an ownerless block and every existing `vState` entry
  exactly once. Once a graph owns it, any attempt to bind it to a different graph fails.
- `State` holds its context and reads solver/timing fields from it for propagation.
- `Sim` stores stages, time steps, limit, and context on the instance, and rejects blocks
  owned by a different context. `SimContext` itself is the clock; `Sim` does not create a
  second numerical `State` merely to advance time.

The adapter activates its context across initialization, construction, stepping,
reporting, analysis/result reads, and snapshot/restore. The native `Sim` activates its
context for its complete lifecycle.

### 4.3 Compatibility facade

Use a `ContextVar[SimContext]` to expose the active context to legacy code. A temporary
`State` metaclass/proxy maps reads and writes such as `State.t` and `State.ready` to the
active context, falling back to a default context for direct legacy tests.

This facade is a compatibility mechanism, not the ownership mechanism:

- built-in production blocks migrate to `self.context`;
- integrators always use their explicit reference;
- adapter and `Sim` boundaries activate their context even after built-ins migrate, so
  external blocks continue to work during the compatibility period; and
- legacy `State.set()`, `reset()`, `sample()`, and `updateclock()` methods delegate to
  the bound/active context, while `Block.set_method()` writes `self.context.method`;
- a static test prevents new mutable `State.*` use in built-in blocks, the adapter, or
  the runner. Immutable `State.EPS`-style references are replaced with module constants
  or explicitly exempted.

Raw threads and arbitrary executors cannot be assumed to propagate `ContextVar` state.
Explicit references therefore remain correct there. Separate native `Sim` instances are
verified in separate threads. Custom integrators must be created through
`addIntegrator()`/registered in `vState`, or accept an explicit context; an unregistered
`State()` hidden inside a custom block cannot be discovered and rebound safely.

Native `Sim` receives a parallel temporary compatibility facade: class-level
`Sim.stop`, `stop0`, `tmax`, `dts`, and `vStage`, plus `sample()` and `terminate()`,
resolve through the active/legacy-default `Sim` instance and its context. New production
code uses instance fields. This facade prevents FAC-9 from silently breaking direct OSK
callers and is deprecated on the same schedule as `State.*`.

### 4.4 Runner operation ownership

Add a per-runner exclusive operation token for every graph mutation: `run`,
`continue_from_step_mode`, `initialize_step_mode`, `enter_step_mode`, `step_forward`,
`step_backward`, `reset`, `reset_step_mode`, snapshot capture, and snapshot restore. A
conflicting operation either first stops and awaits the active operation where that is
its documented behavior, or returns a deterministic conflict. The runner exposes one
atomic `try_reserve_execution()` operation so checking, marking scheduled, and claiming
execution cannot race; every claim releases in `finally`. Snapshot boundary validation
and capture occur under the same token so `kpass` cannot change between checking and
copying.
Pause, resume, status, results, and stop must remain callable without waiting on a token
held for the full run, avoiding deadlock; their shared result/status reads must use
immutable copies or narrowly scoped synchronization. The existing `_run_finished` event
remains the shutdown/completion signal.

The operation matrix is explicit: execution and step mutations conflict with an existing
claim and return 409; reset and rollback require a quiescent runner and otherwise return
409; stop remains a nonblocking request; pause gains a committed-boundary acknowledgment
that callers await before snapshot-dependent work; resume only changes the paused run's
gate. No operation infers safety from status alone.

`enter_step_mode` remains a transition from a paused continuous run rather than becoming
a blanket conflict: require paused state, request the run transition, await
`_run_finished`, acquire step-mode ownership, and capture the committed boundary. The
runner and route become async if needed to enforce that sequence.

### 4.5 Session registry and compatibility API

Replace the module-global runner with a small in-process registry:

```text
session_id -> SimulationRunner
current_session_id
registry lock
```

Resolution and mutation happen under the registry lock; runner operations happen after
the lock is released. A separate installation mutex preserves FAC-1 stop-and-replace
ordering across the await: concurrent replacement requests cannot both stop the same
observed runner and then race to install. Concurrent opt-in registration may use the
registry lock without taking the replacement mutex.

API behavior:

- `/start` and `/step/init` accept top-level `replaceCurrent` (default `true`).
- With `true`, installation keeps today's behavior: stop and await the current live
  runner before installing the replacement. It stops only that current runner; sessions
  previously retained by explicit opt-in continue running. The replaced current record
  is then removed, matching the legacy loss of access to the old runner.
- With `false`, the existing runner is not stopped; the new runner is registered,
  scheduled or initialized, and becomes the current session for omitted-ID calls.
- `/stop`, `/reset`, `/pause`, `/resume`, `/status`, `/results`, and `/step/*` accept an
  optional `sessionId` query parameter. An omitted value resolves the current session.
- Unknown explicit IDs return 404. Existing no-session errors and idle responses remain
  compatible.
- Targeted status/control responses include `sessionId` as an additive identity field.
- A second execution operation on the same session returns 409; operations on different
  sessions may proceed.
- Add `DELETE /sessions/{session_id}`. Mark the registry record `deleting` under the
  registry lock, reject new operations on it, stop/await outside the lock, then remove
  only that same record. Deleting the current session promotes the most recently
  installed retained session by monotonic insertion sequence, if any.

To bound memory, add a configurable maximum retained-session count with a conservative
default. After any required replacement stop completes, capacity check, safe terminal
pruning, insertion, and current-session update occur as one registry transaction. If no
safe candidate exists, return 429 rather than evicting a live session.
Document that the registry is process-local; multi-worker deployment requires sticky
routing or a future shared registry.

For synchronous `/step/init`, installation continues to precede initialization: a
failed initializer remains the current retained error session, matching current
observable ownership. Test this explicitly. The frontend API client gains optional
`sessionId` and `replaceCurrent` parameters while retaining its no-argument defaults.

Each registry value is a `SessionRecord`, not only a runner. It retains the monotonic
installation sequence, lifecycle/tombstone state, and owned `asyncio.Task` handle.
Creation atomically reserves and schedules the runner before returning. Completion,
failure, cancellation, a scheduled callable that never starts, deletion, and capacity
cleanup all finalize that record and the runner's `_run_finished` signal exactly once.

## 5. Snapshot contract

Introduce an explicit runner checkpoint envelope containing an adapter snapshot:

```text
schemaVersion: 1
modelFingerprint: <stable compiled-model identity>
configFingerprint: <stable validated SimulationConfig identity>
runner:
  currentTime, progress, totalSteps, stepMode,
  result generation/checkpoint references, retained history metadata
adapter:
  context:
    t, t1, dt, dtp, method, kpass, ready,
    tickfirst, ticklast, stop, stop0
  blocks:
    <block id>:
      type: <block type>
      codecVersion: <integer>
      state: <block-owned snapshot>
```

Fingerprints never use Python `hash()`. The model fingerprint is SHA-256 over canonical
JSON containing compiled block IDs, types, parameters, ports, connections, and execution
order. The config fingerprint is SHA-256 over canonical JSON from the complete validated
`SimulationConfig`. Schema and per-block codec versions participate in compatibility
validation.

Each integrator state includes `x`, `x0`, and `xd0` through `xd4`. Stateful blocks use
an explicit `snapshot_state()` / `restore_state()` hook or registered codec for delay
buffers, filter/observer memory, timestamps, seeded RNG state, and sink state. Stateless
blocks return an empty state. Attribute-name scraping is removed once all built-ins used
by step rollback have a codec. Because every built-in can enter step mode, a completeness
test requires every registered built-in type to declare a versioned codec/hook or
explicitly declare itself stateless.

Restore is one runner-plus-adapter transaction, not just an adapter operation. Runner
time, progress, step counts, result generations/traces, and adapter state must describe
the same committed boundary; in particular, runner `_current_time` equals `context.t`.
Inconsistent snapshots are rejected before mutation.

Restore follows validate-then-commit semantics:

1. validate schema version, model fingerprint, complete block ID/type set, value shapes,
   and solver-boundary invariants without changing live state;
2. purely decode and prepare runner, context, and block values;
3. apply through infallible assignment-only codecs, or retain a complete pre-restore
   image and roll back every already-applied runner/context/block mutation if a hook
   raises; and
4. leave the original simulation byte-for-byte/logically unchanged on any validation or
   commit error.

Detached public snapshots are deeply detached from later live mutation and are exposed
through a frozen/read-only representation. Internal per-step rollback checkpoints retain
FAC-2's compact immutable result-generation and length references; they do not deep-copy
Scope, Scope3D, or result arrays on every step. Existing bounded-history pruning and
memory/point bounds remain acceptance gates. Both forms permit capture only when
`kpass == 0` and `ready == 1`. Mid-stage serialization is rejected. A restored checkpoint
always enters quiescent paused step mode with no live task or pending operation claim;
ephemeral task handles and control requests are never restored. Restoring or rolling back
one runner cannot alter another runner's context, results, or snapshot.

## 6. Implementation sequence

Each implementation phase is a focused commit or small commit series. Characterization
tests land green with the behavior they protect. Main-thread review and the listed gate
are required before advancing.

**Progress (2026-07-16):** Phase 0 deterministically reproduced solver/clock cross-talk
for alternating adapters and step-mode runners. Phase 1 completed in `f3051b9` with an
instance-owned context kernel, active-context compatibility facade, adapter ownership,
clock-transition validation, and task/exception/cancellation restoration coverage.
Phase 2 completed in `9d4531a`: blocks and registered integrators now bind atomically to
one graph/context owner, native `Sim` fields and clock execution are instance-scoped,
and the temporary `Sim.*` facade follows the active or paired sequential-legacy
instance. Two native simulations with different solvers execute concurrently in real
threads without clock, field, write, sampling, or termination cross-talk. The Phase 2
Docker gate passed 2,130 tests with 1 skip; Ruff and mypy passed across 136 source files,
and the overlapped thread regression passed 20 consecutive repetitions. Phase 3
completed in `a450f20` and `ec15bb1`. Phase 4 completed in `e33a9fd`; Phase 5 is next.

### Phase 0 — Characterize cross-talk and freeze compatibility

- Add a failing direct-adapter regression with different solver methods and steps.
- Add a failing alternating-runner regression and isolated reference results.
- Record current legacy no-session API replacement behavior.
- Inventory mutable `State.*` reads with a static test allowlist to be driven to zero.

**Gate:** tests fail for demonstrated shared-state reasons, not timing races.

This is an uncommitted red-test verification step. The regressions are committed only
with the Phase 1/first ownership fix that makes them pass; FAC-9 never records a
deliberately red branch commit.

### Phase 1 — Add the context kernel and compatibility facade

- Add `SimContext`, clock transitions, activation context manager, and default context.
- Enforce a single graph owner claim and reset-in-place identity.
- Route `State` integration through an explicit bound context.
- Provide the temporary class-level compatibility facade.
- Preserve legacy instance methods as deprecated delegates to the bound/active context.
- Migrate kernel tests to create explicit contexts where isolation matters.

**Gate:** OSK integration accuracy tests pass for Euler, RK2, RK4, and Merson; two
contexts can alternate all stages without cross-talk. Nested activation, exceptions,
and task cancellation restore `ContextVar` tokens in `finally`, and facade writes affect
only the active context.

### Phase 2 — Bind blocks and make `Sim` instance-scoped

- Add provisional/owned `Block.context` binding and safe one-time rebinding for existing
  integrators.
- Move every mutable `Sim` field to the instance and use its context as the sole clock.
- Provide the temporary active/default `Sim.*` compatibility facade.
- Reject graph/block reuse across different contexts.
- Add two-thread native `Sim` isolation tests with a barrier inside real block updates
  so execution is proven to overlap.

**Gate:** existing native OSK tests plus thread-isolation regressions pass repeatedly.

**Completed:** `9d4531a` (2026-07-16). Focused native/context verification passed 52
tests; the full backend passed 2,130 tests with 1 skip; Ruff and mypy were clean; and
the barrier-backed thread-isolation regression passed 20 consecutive runs. Coordinator
review found and the commit corrected a legacy `Sim.*`/`State.*` fallback pairing issue
before the final gate.

### Phase 3 — Give adapters and runners explicit ownership

- Create/pass one context per runner and adapter.
- Activate it at every construction, execution, reporting, and state boundary.
- Characterize nonzero `config.start_time`, then intentionally normalize initialization
  and every reset path to that value rather than implicit zero; treat any changed output
  as reviewed behavior.
- Add the complete operation/state matrix and atomic execution reservation.
- Prove deterministic AABB/ABAB adapter schedules and event-gated `asyncio.gather()`
  runner results equal isolated references without timing sleeps.

**Gate:** two runners with different solvers and time-varying sources run concurrently
for more than 100 steps, crossing cooperative yields, with identical normalized output.

**Completed:** `a450f20` and `ec15bb1` (2026-07-16). Runner and adapter lifecycle
initialization now honor nonzero configured start times, reset every timing/control
field consistently, and activate the owned context at reporting and state boundaries.
Deterministic AABB/ABAB adapter schedules and event-gated runners cross the 100-step
cooperative boundary and match sequential isolated references. Every runner graph
mutation now requires an exact opaque operation token; scheduled background calls pass
that token into the coroutine, stale/double releases cannot clear a newer operation,
and API conflicts return 409. Pause uses a committed-boundary acknowledgment, while
enter-step transfers ownership from the background run to an exact pending handoff
token with cancellation cleanup. The final Docker gate passed 2,147 tests with 1 skip;
Ruff and mypy were clean across 136 source files. Coordinator review found and the
implementation corrected reset bookkeeping, handoff cancellation, stop-while-paused,
early-resume, repeated-pause, and unpaused-entry edge cases before the final gate.

### Phase 4 — Migrate built-in blocks

Migrate by coherent families, with focused tests after each family:

1. sources, sinks, and continuous blocks;
2. discrete, delay, and signal-processing blocks;
3. observers, navigation, sensor-fusion, and RF blocks; and
4. remaining nonlinear, control, and analysis blocks.

Direct timing access becomes `self.context`; shared immutable constants remain module
constants. Do not change `update(ctx)` signatures across the library.

**Gate:** no mutable `State.*` access remains in built-in production blocks, adapter,
runner, or native `Sim`; timing-sensitive block tests pass under interleaving.

**Completed:** `e33a9fd` (2026-07-16). All built-in mutable timing and readiness access
now uses each block's owned context, while the shared epsilon is a module constant. The
static AST inventory is zero, and deterministic ABAB/AABB regressions cover Sine, Clock,
RateLimiter, LowPassFilter, UnitDelay, and TransportDelay with distinct step sizes and
peer-context immutability checks. The full Docker gate passed 2,159 tests with 1 skip;
Ruff and mypy were clean across 136 source files.

### Phase 5 — Version and complete snapshots

- Add the schema, fingerprint, immutable capture, and atomic validation.
- Add explicit codecs/hooks or explicit stateless declarations for every built-in block.
- Migrate complete runner-plus-adapter checkpoints to the versioned contract and enforce
  their time/step/result consistency invariants.
- Reject model mismatch, unknown schema, partial block sets, and mid-stage capture.
- Preserve FAC-2 compact result generations, pruning, and bounded history.

**Gate:** checkpoint/advance/rollback/replay is deterministic with integrators, delays,
filters, discrete timestamps, seeded noise, Scope, and Scope3D; a peer runner remains
unchanged. Injected failure after at least one prepared block assignment proves complete
rollback, the codec registry covers every built-in, and bounded-history tests retain
FAC-2's memory behavior.

### Phase 6 — Add session-addressed API concurrency

- Add the registry, `replaceCurrent`, optional session targeting, cleanup endpoint, and
  bounded retention.
- Preserve the FAC-1 stop-and-replace race protections for default calls with an
  await-safe installation mutex/reservation protocol.
- Extend the frontend client with optional targeting/coexistence parameters.
- Add deterministic API tests for concurrent creation and targeted control/read paths.

**Gate:** two API sessions run simultaneously, pausing or stopping one does not affect
the other, and all legacy replacement/race tests remain green.

### Phase 7 — Compatibility and closeout

- Document the process-local registry and compatibility facade.
- Record the facade's removal as a separately approved deprecation task.
- Run the complete quality, numerical, frontend, and generated-code matrix.
- Update both Fable ledgers with actual commits and verification counts.

**Gate:** all acceptance criteria in section 7 pass; FAC-9 can be marked complete.

## 7. Acceptance matrix

FAC-9 is complete only when all of the following are demonstrated:

- Two direct adapters using Euler/`0.1` and RK4/`0.01` can be interleaved and match
  isolated reference runs.
- Two runners execute under `asyncio.gather()` for enough steps to cross real
  `sleep(0)` yields and match isolated results; event gates prove both are live before
  controlled release.
- Tests include a time-varying source and an integrator so clock/method contamination is
  observable.
- Timing-sensitive Sine/Clock, RateLimiter/filter, UnitDelay, and TransportDelay cases
  remain isolated.
- Pausing, stopping, resetting, or initializing one runner does not alter its peer.
- Reset/initialize preserves each context object's identity, duplicate context ownership
  is rejected, and every block/`vState` entry in a graph references that graph's context.
- Step mode can alternate between sessions; checkpoint, advance, rollback, and replay
  one while the other remains unchanged.
- Two native `Sim` instances match isolated execution when run in separate threads.
- Every mutable context and integrator field round-trips through the snapshot schema.
- Snapshot immutability, version rejection, model mismatch, block mismatch, mid-stage
  rejection, and atomic failed restore are tested.
- Snapshot capture/restore is rejected while another operation owns the runner; codec
  coverage and FAC-2 bounded-generation history are static/dynamic gates.
- Context activation cleanup is tested after nesting, exceptions, and task cancellation.
- API tests cover distinct concurrent IDs, targeted status/results/control, unknown
  IDs, duplicate same-session execution, cleanup/retention, and omitted-ID compatibility.
- API race tests cover two default replacements, replacement versus coexistence,
  deletion versus targeted control, capacity pruning versus creation, and reset/step
  versus live same-session continuation.
- A static gate rejects mutable `State.*` use in migrated production code.
- Full backend pytest passes in Docker.
- Ruff and canonical mypy pass in Docker.
- Frontend Vitest, ESLint, and TypeScript pass in Docker.
- The numerical/kernel/codegen-accuracy subset passes.
- The full generated-code validator remains 156/156 with no build, run, simulation, or
  output-validation failures.

## 8. Risks and rollback strategy

| Risk | Mitigation / rollback boundary |
|---|---|
| Stage timing or `ready` behavior changes numerics | Centralize transitions in `SimContext`; retain convergence and timing-sensitive tests from the first context commit. |
| Constructor-created integrators retain the wrong context | Bind recursively before initialization and assert graph-wide context identity. |
| Ambient context leaks between tasks | Activate inside adapter/runner boundaries and use explicit references for correctness. |
| Same-runner concurrent mutation corrupts results | Reject duplicate execution operations per runner while leaving stop/pause/status responsive. |
| Snapshot migration corrupts rollback | Version and validate before mutation; land snapshot work after context isolation and keep each phase revertible. |
| API registry breaks the current frontend | Default `replaceCurrent` to true and keep omitted-ID routes resolving the current runner. |
| Retained sessions leak memory | Bounded registry, terminal-session pruning, explicit deletion, and deterministic capacity errors. |
| Custom blocks still depend on `State.*` | Keep an activated compatibility facade for one documented deprecation cycle. |
| Multi-worker deployment gives inconsistent registries | Document process-local scope; do not claim distributed concurrency. |

If a phase fails its gate, revert or correct that phase before proceeding. Do not hide
cross-talk by restoring a process-wide lock: serialization is retained only as the
legacy API default, not as the simulation-state correctness mechanism.

## 9. Approval record

The maintainer approved all three decisions on 2026-07-16:

1. implement one explicit `SimContext` per simulation with a temporary `State.*`
   compatibility facade;
2. implement API-level concurrent sessions through opt-in `replaceCurrent: false` and
   optional `sessionId` targeting, while replacement remains the default; and
3. include the versioned snapshot migration in FAC-9 because pause/rollback isolation
   is part of the concurrency acceptance contract.
