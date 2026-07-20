# LibreSim — Plan to 100% Test Coverage (Unit + Regression)

> Produced 2026-07-16 on branch `uimods` @ `a450f20` from a **fresh measured baseline**
> (commands in §1). Written to be executed task-by-task by coding agents of varying
> capability, in the same style as
> `docs/plans/completed/simulation-correctness-remediation.md`
> (whose LS-1…LS-10 and FAC-9 SimContext migration are complete — see §2.4 for the
> resulting test-writing guidance).
>
> Companion docs: `docs/refs/testing.md` (how to run/write tests — note its coverage
> numbers are stale; this doc's baseline supersedes them),
> `docs/plans/refactoring-recommendations.md` (component splits that gate the frontend
> phases).

---

## 0. Ground rules (read first, every agent, every task)

1. **All tests run inside Docker — never on the host.**
   ```bash
   # Backend suite + coverage (regenerates backend/coverage.json used by every task)
   DOCKER_HOST=unix:///run/docker.sock docker compose run --rm -v "$PWD/examples:/examples:ro" backend \
     sh -c "pip install -q -e '.[dev]' && pytest tests/ -q -p no:cacheprovider --cov=src --cov-report=json:coverage.json --cov-report=term"

   # Frontend suite + coverage
   DOCKER_HOST=unix:///run/docker.sock docker compose run --rm --no-deps frontend npm run test:coverage
   ```
   Run the relevant one **once at task start** (to get your file's current missing
   lines) and **once at task end** (to prove the delta). Do not run coverage repeatedly
   in between — run only your new test file while iterating:
   `... backend sh -c "pip install -q -e '.[dev]' && pytest tests/test_yourfile.py -q"`.
2. **Tests must assert behavior, not merely execute lines.** Every test asserts specific
   observable output (return value, state change, emitted code content, HTTP status +
   body, thrown exception type + message). A test whose only effect is "the line ran" is
   rejected work. If you cannot state what a line's *correct* behavior is, stop and
   report it — that is how coverage work finds real bugs, and finding one is more
   valuable than covering it.
3. **Anti-gaming rules (hard):**
   - Never weaken an assertion, delete a test, or mark `xfail`/`skip` to make numbers move.
   - Never add `# pragma: no cover` / istanbul-ignore to dodge work. Pragmas are allowed
     **only** for the categories in §3, each with a justification comment on the same line.
   - Never mock the module under test. Mock only its externals (subprocess, Docker,
     network, plotly, ReactFlow, timers).
   - Never change product code just to make it "more coverable," except extractions
     explicitly called for in §5 (F3) or bug fixes (which then need a regression test).
4. **If a test reveals a bug, fix nothing silently.** Write the failing regression test,
   report the bug in your summary, and either fix it in a separate commit (small,
   obvious) or leave the test marked `@pytest.mark.xfail(strict=True, reason="BUG: …")`
   with a description (larger/judgment). `strict=True` so the xfail screams when fixed.
5. **Commits**: one task per commit series; plain human-style messages; **no AI
   attribution or Co-Authored-By/Generated-with footers; do not push.** Update the §7
   ledger and the §4 ratchet value in the same commit that completes a task.
6. **Follow the completed LS-10 (FAC-9) context contract.** The OSK kernel uses
   instance-owned `SimContext` (`backend/src/osk/context.py`). Before
   writing kernel-adjacent tests, read the current shape of `osk/state.py`,
   `osk/context.py`, and `osk/sim.py` — write new tests against the **SimContext API**
   where one exists, not the legacy class-attribute facade, so they survive the
   compatibility window. If unsure which API is current, check the completed FAC-9
   design and closeout through commit `6e7f690` and report rather than guess.

---

## 1. Measured baseline (2026-07-16, branch `uimods` @ `a450f20`)

### Backend — pytest, line+branch. **85.5%** (15,127 stmts, 1,687 missing, 732 partial branches). 2,137 passed, 1 skipped.

Gap concentration (missing statements, grouped — full per-file detail comes from
regenerating `backend/coverage.json` at task start; do not trust these numbers to stay
current, trust the JSON):

| Area | Files | Missing stmts (≈) | Phase |
|---|---|---|---|
| OSK block library | `src/osk/blocks/*.py` (math_ops **284**, navigation 63, dsp 61, matrix_ops 50, continuous 47, aerospace 34, nonlinear 32, signal_processing 19, rf/sensor_fusion/sources 15 ea, control_analysis/discrete 14 ea, observers 11, rest ≤5) | ~700 | B5 |
| Codegen templates | `src/codegen/languages/{c,cpp,rust,python}/blocks/*.py` (estimation at **5%** in c/cpp!), `generator.py` per language, `validation.py`, `dsp_utils.py`, `analysis.py`, `filter_design.py`, `codegen/generator.py` | ~450 | B6 |
| Compilation service | `src/codegen/compilation/docker_compiler.py` (**21%**, 79 missing) | 79 | B3 |
| Simulation layer | `osk_adapter.py` (75 + 90 partial branches), `runner.py` (37), `compiler.py` (7), `osk/sim.py` (7) | ~125 | B4 |
| API & shell | `api/routes/simulation.py` (63), `codegen/controller.py` (53), `main.py` (8), `api/websocket.py` (7), `routes/examples.py` (5), `routes/import_export.py` (2) | ~140 | B2 |
| Parsers | `parsers/mdl_parser.py` (28) | 28 | B6 |
| Branch-only residue | 732 partial branches repo-wide, dominated by `-> exit` guards in block `update()` methods | — | B7 |

### Frontend — vitest/istanbul. **40.1% stmts / 35.4% branches / 44.3% funcs.**

| Area | Files (size) | Coverage | Phase |
|---|---|---|---|
| Giant components | `Editor/Editor.tsx` (~2.1k lines, **0%**), `Editor/CustomEdge.tsx` (~880, **0%**), `Toolbar/Toolbar.tsx` (~1.2k, **16%**), `Editor/SubsystemNode.tsx` (**0%**) | ~0 | F3 (extract) + F5 |
| Modals | `Help` (558), `Examples` (330), `Properties` (307), `CodeGen` (253), `SaveAs` (168), `Settings` (149) — all **0%** | 0 | F4 |
| Plot windows | `Simulation/PlotWindow.tsx` (408), `PlotWindowManager` (302), `Scope3DWindow` (301), 4× `Analysis/*Window.tsx` (~230-254 ea) — all **0%**, all `react-plotly.js` | 0 | F5 |
| Pure logic gaps | `utils/mdlImporter.ts` (74%), `store/modelStore.ts` (88%), `store/libraryStore.ts` (92%), `mdlExporter` branches, `api/client.ts` (98%), `data/examples.ts` (0%), `App.tsx` (0%), `Sidebar.tsx` (63%), `BlockNode.tsx` (72%) | mixed | F2 |
| Config noise | `.eslintrc.cjs` counted at 0% | — | F1 |

---

## 2. Definitions, scope, and honest caveats

1. **"100%" means**: backend — 100% line **and** 100% branch for `backend/src/` as
   measured by `coverage.py` with `branch = true`; frontend — 100% statements, branches,
   functions, and lines for `frontend/src/` as measured by istanbul, after the §3
   exclusion policy is applied. Excluded-by-policy lines are the *only* tolerated gap.
2. **Coverage is a floor-finder, not a correctness proof.** The valuable output of this
   plan is (a) the behavioral assertions written along the way and (b) the bugs found in
   never-executed paths (rule 0.2/0.4). An `estimation.py` at 5% has literally never had
   its emitters run — expect to find real bugs there.
3. **Cost is back-loaded.** Backend 85.5→100 is bounded, mostly mechanical work
   (~2,400 gap points, phases B2–B7). Frontend 40→100 is dominated by three
   2,000-and-880-line components that are *designed untestable* today; the plan
   deliberately routes through the already-approved refactors
   (`refactoring-recommendations.md` #1, #10, #18) rather than brute-forcing render
   tests on monoliths. **Decision point for the maintainer:** after F4 the frontend will
   sit ≈85-90%; the remaining cost (F5: plotly/ReactFlow/canvas harnesses) is the most
   expensive slice of the whole plan. The plan targets 100% as requested; F5 is
   structured so it can be descoped without stranding earlier work.
4. **LS-10 interaction:** the SimContext migration is complete. Phases B4, B5, and B7
   may proceed against the explicit context API; tests must not add new dependencies on
   the temporary class-level `State.*`/`Sim.*` compatibility facade.

---

## 3. Exclusion policy (the only legitimate non-covered lines)

Add once in phase B1/F1, then never touch without justification.

**Backend** — `backend/pyproject.toml`:
```toml
[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
```
Inline `# pragma: no cover` is allowed only for: (a) defensive code that is provably
unreachable but kept as a guard (comment must say why it's unreachable), (b) platform-
specific branches that cannot execute in the test container. Budget: if a task wants
more than ~5 new pragmas, stop and report instead.

**Frontend** — `frontend/vite.config.ts` coverage.exclude additions: `.eslintrc.cjs`
(config file, not source), `src/main.tsx` (already excluded), `src/vite-env.d.ts`
(already). Nothing else. `/* istanbul ignore */` follows the same two-category rule as
backend pragmas.

---

## 4. Enforcement: the ratchet (do this early, keep it rising)

Coverage that isn't gated regresses. Each phase-completing commit **raises the floor to
the new measured value rounded down to the nearest whole percent**:

- **Backend**: `[tool.coverage.report] fail_under = <N>` in `backend/pyproject.toml`.
  Phase B1 sets it to **85**. CI already runs pytest with coverage (GH + GitLab, both
  hard gates since LS-4); `fail_under` makes regression a test failure everywhere.
- **Frontend**: add to the vitest `coverage` block in `frontend/vite.config.ts`:
  ```ts
  thresholds: { statements: 38, branches: 33, functions: 42, lines: 37 },
  ```
  (F1 sets these just under baseline; every F-phase raises them.) CI must call
  `npm run test:coverage` instead of plain `npm test -- --run` — change both
  `.github/workflows/ci.yml` and `.gitlab-ci.yml` in F1, keeping them mirrored.
- Never lower a threshold. If your change can't meet the floor, your change is wrong.

**Regression-test policy (permanent, not a phase):** every bug fixed in this repo gets a
named, commented regression test in the same commit — the established pattern is
`backend/tests/test_crosstalk_bug.py` / `test_integration_accuracy.py` /
`test_concurrent_runs.py`. Coverage work that uncovers a bug follows rule 0.4.

---

## 5. Task catalog

Capability tiers as in the remediation plan: **T1-any** (mechanical, fully specified),
**T2-mid** (multi-file, local judgment), **T3-strong** (cross-cutting judgment).
Within a phase, tasks are independent and parallelizable unless noted.

### Phase B1 — Lock the baseline (T1-any, small)
1. Add §3 `exclude_lines` block and `fail_under = 85` to `backend/pyproject.toml`.
2. Identify the **1 skipped test** (`pytest tests/ -rs`) — either make it run
   deterministically in Docker or convert to a documented `skipif` with a reason string
   that names the missing capability. No bare skips.
3. Regenerate `backend/coverage.json` and commit the config (not the JSON — check
   `.gitignore` covers `coverage.json`, `htmlcov/`, `.coverage`; add if missing).

### Phase B2 — API routes + app shell to 100% (T1-any → T2-mid, ~140 stmts)
FastAPI `TestClient` throughout; follow existing `tests/test_api.py` conventions.
1. `api/routes/simulation.py` (63): exercise every endpoint's error arm — `/start` with
   missing model / invalid model / invalid config; `/stop|/pause|/resume|/reset|/results|/status`
   with no runner; the full step-mode lifecycle (`/step/init` → `/step/forward` ×n →
   `/step/backward` → `/step/reset` → `/step/continue`) including `numSteps` variants and
   the 409/busy paths added by LS-3; `/debug` with each partial-payload shape.
   Concurrency-sensitive assertions belong in `test_concurrent_runs.py` — don't duplicate.
2. `codegen/controller.py` (53): `/api/codegen/generate` happy path per language +
   invalid language + invalid method + project-name sanitization (LS-9 landed it —
   assert the header quoting too); `/compile*` endpoints with `DockerCompiler`
   monkeypatched (`monkeypatch.setattr`) for: docker absent, image missing, compile
   success bytes round-trip, `CompilationError`.
3. `main.py` (8): root, `/health`, `/api/docs/readme` + `examples` readme, and the
   404 arms (monkeypatch `PROJECT_ROOT` to an empty tmp dir).
4. `api/websocket.py` (7): `TestClient(...).websocket_connect("/ws/simulation")` —
   subscribe echo, unknown message type, disconnect cleanup, `broadcast` with a dead
   connection in the set (add a stub connection whose `send_text` raises).
5. `routes/examples.py` (5) + `routes/import_export.py` (2): remaining error arms
   (unknown id 404 — LS-9 manifest check; malformed JSON example via monkeypatched
   `EXAMPLES_DIR`; import/export error paths).

### Phase B3 — `docker_compiler.py` 21% → 100% (T2-mid, 79 stmts, pure mocking)
No real Docker anywhere in unit tests. Monkeypatch `subprocess.run` with a programmable
fake recording calls; simulate: `FileNotFoundError` (no docker binary),
`TimeoutExpired`, non-zero returncode with stderr, success. Cover
`check_docker_available`, `check_image_exists`, `build_compiler_image` (both outcomes),
the compile/executable-extraction flow (`get_executable_bytes`) using `tmp_path`
fixtures for the project files, and the async executor wrapper (line ~200). Assert the
*docker command lines* the fake received — that is the behavioral contract.

### Phase B4 — Simulation layer to 100% (T3-strong; FAC-9 prerequisite complete)
1. `runner.py` (37 + 17 br): error paths in `run()`/`continue_from_step_mode`
   (adapter that raises mid-step via a stub compiled model), pause→resume→stop
   sequencing, `stop_and_wait` timeout arm, `reset()`/`reset_step_mode()` from every
   status, decimation statistics from LS-5, `get_results` single- vs multi-trace
   grouping and `parts` parsing arms.
2. `osk_adapter.py` (75 + 90 br): `get_state`/`set_state` round-trip for one block of
   each stateful family (integrator, filter `_buffer`, `_prev_*`, Scope, Scope3D) —
   assert full equality of a two-step trajectory after save/step/restore/step;
   `initialize` failure arms (LS-7 unknown-type error included); `_map_parameters` /
   `_convert_product_operations` variants; `get_scope_data`/`get_analysis_data` empty
   and populated; the remaining `step()` branch arms (consult coverage.json —
   many are `is_first_step` sub-paths with specific block-type mixes: constant-only,
   integrator-with-external-IC, manual-input wiring).
3. `compiler.py` (7) + `osk/sim.py` (7): the few residual arms (exception wrapper,
   `dts` shorter than stages, terminate codes). Straightforward; check coverage.json.

### Phase B5 — OSK block library to 100% (T2-mid, ~700 stmts, split into 8 parallel tasks)
The gaps are overwhelmingly: (a) unconnected-input guard branches (`-> exit`), (b)
vector-input variants of scalar blocks, (c) parameter-validation/error arms, (d) rarely
exercised math modes. Technique — extend the existing per-domain test files
(`test_blocks.py`, `test_dsp.py`, `test_navigation.py`, `test_rf.py`,
`test_sensor_fusion.py`, `test_new_blocks.py`) with **table-driven guard tests**: for
every block class in the file, (1) `update()` with no inputs wired → asserts output
unchanged and no exception; (2) each documented input shape (scalar, 3-vector, matrix
where supported) → assert numerically correct output computed independently in the
test (numpy reference, not copied from implementation); (3) invalid parameter arms.
Task split (one commit each, decreasing size): **B5.1** math_ops (284 — sub-split by
class groups if needed), **B5.2** navigation+matrix_ops (113), **B5.3** dsp (61),
**B5.4** continuous (47; TransportDelay time-buffer arms interact with LS-2 stage-time
guards — assert buffering only on completed steps), **B5.5** aerospace+nonlinear (66),
**B5.6** signal_processing+rf+sources (49), **B5.7** sensor_fusion+control_analysis+
discrete+observers (54), **B5.8** remainder (logic, sinks, data_types, control_design,
subsystems ≤5 each). Every numeric assertion needs an independently computed expected
value — cite the formula in a comment.

### Phase B6 — Codegen layer to 100% (T2-mid, ~450 stmts + mdl_parser 28)
1. **Emitter coverage** (`languages/*/blocks/*.py`): these are pure functions
   BlockInfo → code string. For each block family × language, build the minimal
   `BlockInfo`/model containing that block, call the emitter (or `CodeGenerator.generate`
   for the project), and assert the emitted code contains the expected function
   signature/constants. Priority: `c|cpp/blocks/estimation.py` (5% — never executed;
   expect bugs, apply rule 0.4), `cpp|c/blocks/control_design.py`, `*/blocks/aerospace.py`,
   `*/blocks/logic.py`. Where a generated-Python emitter is covered, port the same test
   to c/cpp/rust — the gaps are asymmetric across languages for identical blocks, which
   is exactly the drift the remediation plan warned about.
2. **Compile-smoke for emitters** (optional but preferred): where
   `tests/test_codegen_accuracy.py` infrastructure already compiles generated projects,
   add the uncovered block types to its example matrix instead of string-matching.
3. `codegen/generator.py`, `validation.py`, `dsp_utils.py` (38%), `analysis.py`,
   `filter_design.py`, per-language `generator.py` residue: error arms (unsupported
   block, empty model), option permutations (`include_csv_output`, `include_main`).
4. `parsers/mdl_parser.py` (28): malformed MDL fixtures — unclosed blocks, unknown
   sections, the annotation/branch arms listed in coverage.json; extend
   `test_mdl_parser.py`.

### Phase B7 — Branch-coverage sweep to 100/100 (T2-mid; after B2–B6)
Regenerate coverage.json; the remaining partial branches will be a few hundred
`-> exit` guards missed by B5's tables plus scattered `if x:` arms. Work file-by-file
from the JSON's `missing_branches`. Apply §3 pragmas only per policy. Finish by raising
`fail_under = 100`.

### Phase F1 — Frontend baseline lock (T1-any, small)
Exclude `.eslintrc.cjs`; add `thresholds` (statements 38 / branches 33 / functions 42 /
lines 37); switch both CI files to `npm run test:coverage`. Verify the suite still
passes in Docker.

### Phase F2 — Pure logic to 100% (T1-any → T2-mid)
`utils/mdlImporter.ts` (74→100: uncovered arms are unusual MDL constructs — reuse
fixture style of existing tests), `mdlExporter` residual branches,
`store/modelStore.ts` (88→100: uncovered lines are hierarchy edge ops — nested-subsystem
paths; coordinate with refactoring #2 if it lands first), `libraryStore` (92→100),
`simulationStore` line 113 branch, `api/client.ts` (2 lines), `data/examples.ts`
(0→100: assert example list shape + ids match backend manifest — this doubles as a
frontend/backend contract test), `App.tsx` (render + route smoke with mocked children).
Raise thresholds to the new floor (~55%+).

### Phase F3 — Extract, then test (T3-strong; **this is refactoring #1/#18/#10 executed with tests**)
Do not write render tests against the monoliths. Execute the already-approved splits,
moving code verbatim, then unit-test the extractions to 100%:
1. `Editor.tsx` → `utils/smartRouting.ts`, `hooks/useEditorKeyboardShortcuts.ts`,
   `utils/signalTraversal.ts`, `utils/subsystemUtils.ts`, `Editor/ContextMenu.tsx`
   (refactoring #1). Smart-routing and BFS are pure geometry/graph code — table-driven
   tests, 100% cheap.
2. `CustomEdge.tsx` → extract the ~800 lines of routing math to `utils/edgeRouting.ts`;
   test pure; leave a thin component.
3. `Toolbar.tsx` split (refactoring #18) + dedupe drag/resize into one hook
   (refactoring #10) with its own tests.
Each extraction commit must keep the frontend suite green and `tsc --noEmit` clean;
behavior-preservation is asserted by the existing Toolbar/BlockNode tests plus new
unit tests on the extracted modules.

### Phase F4 — Component tests: modals, sidebar, nodes (T2-mid, parallelizable per component)
Testing-library + the established mock patterns (`docs/refs/testing.md` §React
Component Testing Patterns — Zustand mocking, stable `useSyncExternalStore` references,
dataTransfer mocks). Targets to 100%: `HelpModal`, `ExamplesModal` (mock `api/client`),
`CodeGenModal` (mock client; assert request payload per language/option),
`PropertiesPanel` (parameter editing → store calls), `SaveAsModal`, `SettingsModal`,
`Sidebar` (63→100: drag-start payloads, category collapse, search), `BlockNode`
(72→100: port rendering arms, lines ~241-266), `SubsystemNode` (0→100). Raise
thresholds (~80%+ expected).

### Phase F5 — Plot windows, editor shell, edge component (T3-strong; most expensive slice — see §2.3 decision point)
1. Mock `react-plotly.js` as a props-capturing stub component; then the 4
   `Analysis/*Window.tsx`, `PlotWindow`, `PlotWindowManager`, `Scope3DWindow` reduce to:
   data-transform assertions (props passed to Plotly for a given signals fixture),
   window chrome behavior (drag/resize via the F3 shared hook — already tested),
   empty/error states. 100% reachable without canvas.
2. Slimmed `Editor.tsx` + `CustomEdge.tsx` render tests with a ReactFlow test harness
   (mock `reactflow` exports used; testing.md warns about the stable-reference
   requirement). Cover mount, node/edge callbacks, context-menu wiring, drop-to-add.
3. Raise thresholds to 100 and remove any interim per-glob overrides.

### Phase F6 — Frontend ratchet finalization (T1-any)
`thresholds: { statements: 100, branches: 100, functions: 100, lines: 100 }`, CI both
files verified mirrored, `docs/refs/testing.md` coverage tables updated to final state
(and its stale Windows-anaconda commands replaced with the §0 Docker commands).

---

## 6. Suggested execution order & sizing

| Order | Task | Tier | Size (≈ new tests) |
|---|---|---|---|
| 1 | B1 + F1 (ratchets live) | T1 | config only |
| 2 | B2 (API) | T1/T2 | 60–80 |
| 3 | B3 (docker_compiler) | T2 | 25–35 |
| 4 | B6 (codegen emitters) — parallel with B2/B3 | T2 | 120–180 |
| 5 | F2 (pure logic) — parallel with any B | T1/T2 | 80–120 |
| 6 | B5.1–B5.8 (blocks) | T2 | 250–400 |
| 7 | B4 (sim layer) | T3 | 40–60 |
| 8 | F3 (extractions) | T3 | 100–150 |
| 9 | F4 (components) | T2 | 120–180 |
| 10 | B7 (branch sweep) → backend 100 | T2 | 50–100 |
| 11 | F5 (plots/editor) → frontend 100 | T3 | 100–150 |
| 12 | F6 (finalize) | T1 | config only |

## 7. Status ledger (update in the same commit as the work)

| Task | Status | Commit(s) | Coverage after (B/F) | Notes |
|---|---|---|---|---|
| B1 | complete | this commit | B: 85.82% combined (89.10% lines / 74.47% branches) | 2,185 passed; external MDL fixture has a documented `skipif` |
| B2 | complete | `3b77036`, this commit | B: 87.18% combined; all B2 targets 100% line/branch | 2,270 passed; invalid language/method preserve HTTP 400 |
| B3 | complete | this commit | B: 86.33% combined; `docker_compiler.py` 100% line/branch | 2,212 passed; fixed persistent-artifact and default-path regressions |
| B4 | complete | `cbf0713`, this commit | B: 88.46% combined; all B4 targets 100% line/branch | 2,328 passed, 1 documented skip; fixed snapshot validation, step-mode finalization, and nonpositive step sizes |
| B5.1–B5.8 | not started | | | |
| B6 | not started | | | |
| B7 | not started | | | |
| F1 | complete | this commit | F: 40.34% stmts / 35.64% branches / 44.41% funcs / 39.00% lines | 664 passed; both CI pipelines use coverage command |
| F2 | complete | `00d2f3b`, `d73ad04`, this commit | F: 51.92% stmts / 51.22% branches / 53.40% funcs / 50.38% lines | 724 passed, 0 failed; modelStore, libraryStore, mdlImporter, mdlExporter, simulationStore, api/client, data/examples, and App at 100% |
| F3 | in progress | `06aa4f0`, `6ff3af8`, `2bfff43`, `3c4175c`, `3114ad0`, `97ef57a`, this commit | F: 61.91% stmts / 61.16% branches / 59.44% funcs / 60.66% lines | 790 passed, 0 failed; Editor and CustomEdge extractions complete; Toolbar scope discovery extracted and 100% covered |
| F4 | not started | | | |
| F5 | not started (maintainer descope decision point) | | | |
| F6 | not started | | | |
