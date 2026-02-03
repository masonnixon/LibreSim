# LibreSim Refactoring Recommendations

A prioritized list of changes to improve code quality, remove dead code, and reduce maintenance burden. Only items that provide real value are included — nothing is changed for the sake of changing it.

---

## High Priority

These items address correctness risks, significant dead code, or maintainability problems that actively slow down development.

### 1. Break up Editor.tsx (2,130 lines, ~15 responsibilities)

`frontend/src/components/Editor/Editor.tsx` is the single largest pain point. It contains smart routing algorithms, keyboard shortcut handling (270-line `useEffect`), copy/paste logic, signal highlighting BFS, context menu rendering, breadcrumb navigation, and the actual React Flow canvas — all in one component.

**What to extract:**
- Smart routing functions (lines 34-503) → `utils/smartRouting.ts`
- Keyboard shortcut handler (lines 1526-1796) → `hooks/useEditorKeyboardShortcuts.ts`
- Context menu JSX + handlers → `components/Editor/ContextMenu.tsx`
- Signal highlight BFS logic → `utils/signalTraversal.ts`
- `deepCopySubsystemContents` (lines 507-568) → `utils/subsystemUtils.ts`

### 2. Break up modelStore.ts (1,862 lines, heavily duplicated hierarchy traversal)

Five nearly-identical recursive hierarchy traversal functions exist (lines 219-436) for connection operations, plus three more in the block operations section. Each follows the same `blocks.map → if subsystem → recurse` shape.

**What to do:** Extract a single generic `updateInHierarchy(blocks, subsystemPath, updater)` helper and have all five connection functions delegate to it.

### 3. Silent simulation fallback creates wrong results

`backend/src/simulation/osk_adapter.py` lines 915-938: When a block type is unknown or creation fails, it silently substitutes a `Gain(gain=1.0)` with only a `print()`. The simulation keeps running with a wrong block, producing incorrect output without any error shown to the user.

**What to do:** Raise an error or at minimum propagate a warning to the frontend instead of silently substituting.

### 4. Remove dead WebSocket code

`backend/src/api/websocket.py`:
- `connected_clients` set (line 10) — unused, the `ConnectionManager` class has its own set
- `broadcast_simulation_data()`, `broadcast_simulation_status()`, `broadcast_simulation_error()` (lines 84-101) — never called anywhere
- `parameter_update` handler (lines 73-76) — `pass` body, does nothing

### 5. Remove dead backend code across multiple files

| Location | Dead code |
|----------|-----------|
| `osk_adapter.py:1471-1592` | `run_simulation()`, `get_solver()`, `get_block()`, `get_all_blocks()` — never called |
| `codegen/generator.py:336-357` | Duplicate `LanguageGenerator` stub class — the real one is in `languages/base.py` |
| `codegen/models.py:73-100` | `BlockTemplate` and `SignalInfo` dataclasses — never instantiated |
| `codegen/models.py:119-120` | `BlockInfo.input_signals` and `output_signals` — declared, never populated |
| `codegen/generator.py:108` | `CodeGenerationConfig.optimization_level` — never read |
| `models/block.py:9-69` | `BlockCategory`, `DataType` enums and `ParameterType`, `ParameterOption`, `Parameter` models — defined but never used. The registry stores raw strings/dicts. |
| `models/simulation.py:54-68` | `SimulationStatistics` and `SimulationResults` — never instantiated |
| `services/model_service.py:140-161` | `compile_model()` — stub that returns hardcoded success |

### 6. Remove dead frontend code

| Location | Dead code |
|----------|-----------|
| `api/client.ts:14-44` | `getModels()`, `getModel()`, `deleteModel()`, `validateModel()`, `compileModel()` — never called |
| `store/uiStore.ts` | `showSimulation`, `showNewModelModal`, `showOpenModelModal`, `showImportModal` state + their toggle/open/close actions — none are connected to any UI |
| `store/uiStore.ts:160-163` | `bringPlotWindowToFront` — no-op stub |
| `data/examples.ts:119-122` | `getExample()` — deprecated, always returns `undefined` |
| `data/examples.ts:25-33` | `fetchExampleList()` — exported, never called |
| `store/simulationStore.ts:100-122` | `appendSignalData` — never called from app code |

### 7. Remove debug logging from production code

Significant `console.log` / `console.trace` calls exist throughout the frontend that fire on every render or user interaction:

- `Editor.tsx`: ~15 `console.log` statements including stack traces
- `modelStore.ts:682,1083`: `new Error().stack` logged on every block/connection delete
- `PlotWindow.tsx:222-271`: Full signal array data logged in `useMemo` on every render
- `Toolbar.tsx:446-462`: Full simulation results stringified on every poll
- `CustomEdge.tsx:387-447`: Logs on every mouse movement during edge dragging
- `mdlImporter.ts:32-67`: Logs on every block register/unregister

---

## Medium Priority

These improve consistency and reduce duplication but don't pose correctness risks.

### 8. Deduplicate mobile detection (4 copies)

`App.tsx`, `Editor.tsx`, `Toolbar.tsx`, and `Sidebar.tsx` each independently implement the same `window.innerWidth < 768` resize listener. Extract to a shared `useMobile()` hook.

### 9. Deduplicate simulation polling loop

`Toolbar.tsx` has two nearly identical `setInterval` polling blocks — one in `handleRun` (lines 436-476) and one in `handleResume` (lines 558-586). Extract the shared polling logic into a helper.

### 10. Deduplicate drag/resize logic across 5+ plot windows

`PlotWindow.tsx`, `Scope3DWindow.tsx`, `BodePlotWindow.tsx`, `NyquistPlotWindow.tsx`, `PoleZeroMapWindow.tsx`, and `StepResponseWindow.tsx` each independently implement drag, resize, and minimize behavior with their own `isDragging`, `isResizing`, `dragOffset` state and mouse/touch handlers. Extract to a `useDraggableWindow()` hook or a shared `FloatingWindow` wrapper component.

### 11. Consolidate `STATE_HOLDING_BLOCKS` (defined in two places with different values)

- `backend/src/simulation/compiler.py:145-166` (18 entries)
- `backend/src/codegen/generator.py:30-65` (20 entries)

These have overlapping but different members, which is a latent bug — if a block is state-holding for codegen but not for the compiler, or vice versa, behavior will diverge.

**What to do:** Define once in a shared location and import in both places.

### 12. Consolidate port ID parsing (3 places)

The same ad-hoc port-ID string parsing appears in:
- `osk_adapter.py:_setup_connections()` (lines 1033-1091)
- `codegen/languages/base.py:parse_connection()` (lines 167-213)
- `codegen/generator.py:_resolve_port_ids_in_connection()` (lines 251-312)

Extract a single `parse_port_id(port_string) -> (block_id, port_type, port_index)` utility.

### 13. Consolidate duplicate request models

`backend/src/codegen/controller.py` defines both `CompileRequest` (lines 165-175) and `CodeGenRequest` (lines 26-38) with nearly identical fields. Merge into one or have `CompileRequest` extend `CodeGenRequest`.

### 14. Fix `blocks.py` returning HTTP 200 on not-found

`backend/src/api/routes/blocks.py:33` returns `{"error": "Block type not found"}` with HTTP 200. Every other not-found case uses `HTTPException(status_code=404)`.

### 15. Unify `nanoid` import source

`Editor.tsx` imports from `'nanoid'` (npm package) while `modelStore.ts` and `libraryStore.ts` import from `'../utils/nanoid'` (custom wrapper). Pick one source.

### 16. Deduplicate `getRotatedPosition`

Defined identically in both `BlockNode.tsx:14-22` and `SubsystemNode.tsx:8-16`. Move to a shared utility.

### 17. Deduplicate `SimulationRunner.run()` and `continue_from_step_mode()`

`backend/src/simulation/runner.py` lines 317-440: These two async methods contain nearly identical simulation loops. Extract the shared loop body.

### 18. Break up Toolbar.tsx (1,181 lines)

Handles file operations, simulation control, polling, settings, help, and examples modals — all in one component. At minimum, simulation control (run/pause/stop/step) could be its own component or hook.

---

## Lower Priority

Nice-to-have cleanups. Do these opportunistically when touching nearby code.

### 19. Clean up project root

- `PID Controller.json` — untracked stray file, should be moved to `examples/` or deleted
- `dualQuaternionLib.mdl` and `quaternionLib.mdl` — gitignored reference files cluttering the root

### 20. Untrack committed artifacts

- `backend/coverage.xml` — generated on every pytest run, should be untracked (`git rm --cached`)
- `docs/codegen-validation-report.md` — generated by `scripts/validate_codegen.py`, is a CI artifact

### 21. Remove dead Docker volume declaration

`docker-compose.yml` declares a named `node_modules:` volume at the bottom that is never referenced by any service.

### 22. Consolidate or remove duplicate CI configs

`.github/workflows/ci.yml` and `.gitlab-ci.yml` run the same pipeline with minor divergences. If only one CI system is in use, remove the other. The `continue-on-error: true` on frontend tests in GitHub Actions and `|| true` in GitLab CI are both outdated now that 659 tests exist.

### 23. Clean up scripts directory

`scripts/quick_validate_codegen.py` substantially overlaps with `scripts/validate_codegen.py` and isn't wired into CI. Either consolidate or remove. `scripts/test_codegen_accuracy.py` requires a live server and isn't wired into CI — consider whether it's still useful.

### 24. Add missing type hints in OSK layer

`OSKAdapter.__init__`, `Sim.__init__`, `Block.state()`, and the `vObj`/`vStage`/`vState` variables throughout `osk/` use Hungarian notation from the original C++ port. Add type annotations as these files are touched.

### 25. Move `inline traceback import` to top of file

`backend/src/simulation/runner.py` has `import traceback` repeated four times inside `except` blocks. Move to a single top-level import.

### 26. Remove empty `services/__init__.py`

`backend/src/services/__init__.py` contains only a docstring, provides no re-exports, and serves no purpose since the service is imported directly.

### 27. Update README example list

`README.md` lists 26 examples but `examples/` contains 47 JSON files. The 40-50 series additions are not documented.

### 28. Address `SQA.md` / `testing.md` overlap

`docs/SQA.md` is incomplete and duplicates install steps from `docs/testing.md`. Either complete it as its own document or merge the relevant content into `testing.md` and remove it.

### 29. Move planning docs out of `codegen_verification/`

`codegen_verification/VERIFICATION_REPORT.md` and `codegen_verification/IMPROVEMENT_PLAN.md` are planning/status documents committed inside a verification data directory. They belong in `docs/` if kept.

### 30. Direct state mutation in paste handler

`Editor.tsx:1718-1726` directly mutates Zustand store objects (`blockToUpdate.children = children`) instead of going through the store's immutable update pattern. This can cause missed re-renders. Fix when refactoring Editor.tsx.

---

## What NOT to change

- **OSK kernel naming** (`vObj`, `kpass`, `dtp`, etc.) — These come from the original H.R. Sells C++ codebase. Renaming them would break the connection to the reference implementation and make it harder to cross-reference. Leave as-is unless the OSK layer gets a ground-up rewrite.
- **`codegen_verification/` zip files** — These are intentionally committed as a pre-built cache. The `.gitignore` inside that directory explicitly documents this design decision.
- **Separate block definition files in `frontend/src/blocks/`** — One file per block type is the right pattern for this kind of registry. The number of files is fine.
- **`mdlImporter.ts` complexity** — This file is large (~1,400 lines) but it's doing a genuinely complex job (parsing Simulink MDL format). The complexity is inherent to the problem, not accidental.
- **Pydantic models in `models/`** — The model layer structure is sound. The issue is specific unused models (called out above), not the pattern itself.
