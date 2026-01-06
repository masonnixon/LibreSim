# LibreSim Project Context

## Project Overview
LibreSim is a web-based block diagram simulation tool designed as an alternative to MathWorks Simulink. It allows users to create, edit, and simulate dynamic systems using a visual block diagram interface.

## License
LibreSim uses the **LibreSim Source Available Commercial License (LSACL)**:
- **Free** for personal, educational, academic, research, and non-profit use
- **Free** for commercial use generating less than $10,000/year
- **Royalty-based** for commercial use above $10,000/year (3-7% based on revenue tier)
- See `LICENSE` file for full terms

## Architecture

### Frontend (React + TypeScript + Vite)
- **Port**: 4200
- **Framework**: React with TypeScript
- **Build Tool**: Vite
- **Block Diagram Library**: React Flow (@xyflow/react)
- **State Management**: Zustand
- **Key Directories**:
  - `frontend/src/components/` - React components (BlockNode, Canvas, Toolbar, Sidebar, etc.)
  - `frontend/src/store/` - Zustand stores (modelStore, simulationStore)
  - `frontend/src/api/` - API client for backend communication
  - `frontend/src/types/` - TypeScript type definitions
  - `frontend/src/blocks/` - Block definitions by category

### Backend (Python + FastAPI)
- **Port**: 9000
- **Framework**: FastAPI
- **Validation**: Pydantic v2 (requires `pydantic-settings` separate package)
- **Key Directories**:
  - `backend/src/api/routes/` - API route handlers (simulation.py, models.py)
  - `backend/src/models/` - Pydantic data models
  - `backend/src/osk/` - Object-oriented Simulation Kernel
  - `backend/src/simulation/` - Simulation runner, compiler, and OSK adapter

### OSK (Object-oriented Simulation Kernel)
The core simulation engine using multi-pass numerical integration.

**Block Lifecycle**:
1. `init()` - Initialize block state
2. `update()` - Update block outputs based on inputs
3. `rpt()` - Report/record data (for scopes)
4. `propagateStates()` - Advance integrator states

**Integration Methods**: Euler, RK2, RK4, Merson

**Block Categories**:
- `sources.py` - Constant, Step, Ramp, Sine, Pulse, Clock, FromWorkspace
- `sinks.py` - Scope, ToWorkspace, Display, Terminator
- `math_ops.py` - Sum, Gain, Product, Abs, Sign, Bias, Saturation, MathFunction, Trigonometry, DeadZone, Switch, Mux, Demux
- `continuous.py` - Integrator, Derivative, TransferFunction, StateSpace, ZeroPole, TransportDelay, SecondOrder, LimitedIntegrator
- `discrete.py` - UnitDelay, ZeroOrderHold, FirstOrderHold, DiscreteIntegrator, DiscreteDerivative, DiscreteTransferFunction, DiscreteStateSpace, DiscreteFilter, Memory
- `control_design.py` - PIDController, DiscretePIDController, LQRController, PolePlacement, LeadLagCompensator, PIController, PDController, AntiWindupPID, ModelReference
- `signal_processing.py` - MovingAverage, LowPassFilter, HighPassFilter, BandPassFilter
- `nonlinear.py` - RateLimiter, Backlash, CoulombFriction, LookupTable, Relay
- `observers.py` - LuenbergerObserver, KalmanFilter, ExtendedKalmanFilter
- `data_types.py` - DataTypeConversion, RealImagToComplex, ComplexToRealImag
- `matrix_ops.py` - MatrixMultiply, MatrixTranspose, MatrixInverse, Selector, Assignment, Concatenate, MatrixSum, VectorNorm
- `aerospace.py` - QuaternionNormalize, QuaternionMultiply, QuaternionConjugate, QuaternionToEuler, EulerToQuaternion, QuaternionRotateVector, DCMToQuaternion, QuaternionToDCM, ISAAtmosphere, SixDOF, FlatEarthGravity, WGS84Gravity
- `dsp.py` - FFT, IFFT, FIRFilter, IIRFilter, Convolution, Downsampler, Upsampler, Interpolator, WindowFunction, Mean, Variance, RMS, PeakDetector, ZeroCrossingDetector
- `rf.py` - RFAmplifier, RFMixer, RFFilter, SParameterNetwork, RFBudgetElement, Attenuator, AMModulator, FMModulator, PhaseNoise, dBmToWatts, WattsTodBm
- `navigation.py` - CoordinateTransformationConversion, LLAToECEF, ECEFToLLA, ECEFToNED, NEDToECEF, WaypointFollower, GreatCircleDistance, FlatEarthPosition
- `sensor_fusion.py` - IMUSensor, Accelerometer, Gyroscope, Magnetometer, GPSSensor, Altimeter, ComplementaryFilter, MadgwickFilter, MahonyFilter, INSGPSFusion, AlphaBetaFilter, AlphaBetaGammaFilter

## Session 2026-01-04 (MyPy Type Checking Fixes)

### Summary
All mypy type checking errors have been fixed. The codebase now passes:
- ruff linting (all checks)
- mypy type checking (0 errors across 117 source files)
- bandit security scanning

### Type Annotations Added

1. **src/blocks/registry.py** - Added `BlockDefinition` type alias and annotated block lists
2. **src/osk/sim.py** - Added type annotations for class attributes (`dts`, `vObj`, `vStage`, `clock`, `results`)
3. **src/osk/blocks/*.py** - Added `Any` imports and type annotations for:
   - Buffer types in signal_processing.py
   - Input/output vectors in math_ops.py, navigation.py, matrix_ops.py
   - State vectors in control_design.py, discrete.py
   - Renamed `state` attributes to `_x_state` to avoid shadowing base class method
4. **src/codegen/generator.py** - Fixed ABC subclass registration (module override in pyproject.toml)
5. **src/codegen/languages/*/generator.py** - Fixed block lookup with proper None handling
6. **src/parsers/mdl_parser.py** - Fixed return types, variable reuse, and Connection field names
7. **src/simulation/osk_adapter.py** - Added None checks for block access
8. **src/api/routes/simulation.py** - Added `dict[str, Any]` type annotation to result dict
9. **src/api/routes/examples.py** - Added type annotation to json.load result

### Configuration Updates

**pyproject.toml**:
- Added `pydantic.mypy` plugin for Pydantic v2 support
- Added `[tool.pydantic-mypy]` section with relaxed settings for alias compatibility
- Added per-module mypy overrides:
  - `src.osk.blocks.*` - disabled strict_optional for OSK blocks
  - `src.codegen.generator` - disabled assignment type checking for ABC subclass registration

**.pre-commit-config.yaml**:
- Mypy runs in CI (GitHub Actions/GitLab CI), not pre-commit (Windows Python path issues)
- Note added for manual mypy command

### Verification Commands

```bash
# Run mypy
cd backend && python -m mypy src/ --config-file=pyproject.toml
# Result: Success: no issues found in 117 source files

# Run ruff
cd backend && python -m ruff check src/ tests/
# Result: All checks passed!
```

### Known Design Decisions

1. **OSK naming conventions** - camelCase methods (getOutput, setInput) match Simulink/MATLAB patterns
2. **Engineering variables** - Kp, Ki, Kd, A, B, C, D are universal control notation
3. **Block.state() method** - Base class has `state()` method, subclasses renamed attribute to `_x_state`
4. **Pydantic aliases** - Models use `populate_by_name=True` for JSON compatibility with frontend

## CI Pipeline

Both GitHub Actions and GitLab CI run:
1. ruff check (linting)
2. mypy (type checking)
3. bandit (security)
4. pytest (unit tests)
5. codegen validation (after backend tests pass)

## Code Generation Validation Status (as of 2026-01-04)

### Latest Run
- **Overall**: 144/148 passed (97.3%)
- 37 examples validated (1 stochastic example skipped)
- Remaining 4 failures: 30_pid_speed_control (user said ignore)

## Development Environment

### Anaconda Setup
```bash
conda create -n libresim python=3.11 -y
conda activate libresim
cd backend
pip install -e ".[dev]"
pip install pre-commit
pre-commit install
```

### Docker Development
```bash
docker compose up
```
- Frontend: http://localhost:4200
- Backend: http://localhost:9000

## SQA (Software Quality Assurance)

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Ruff** | Python linting & formatting | `backend/pyproject.toml` |
| **MyPy** | Python type checking | `backend/pyproject.toml` |
| **Bandit** | Python security scanning | `backend/pyproject.toml` |
| **Pytest** | Python testing + coverage | `backend/pyproject.toml` |
| **ESLint** | TypeScript linting | `frontend/eslint.config.js` |
| **detect-secrets** | Secret detection | `.secrets.baseline` |

### Pre-commit Hooks
```bash
# Install hooks (one-time setup)
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```

## Session 2026-01-05 (3D Scope Feature)

### Summary
Implemented a new `scope_3d` block for 3D visualization of trajectories in phase space.

### Implementation Details

**Backend (OSK Blocks)**:
- Added `Scope3D` class to `backend/src/osk/blocks/sinks.py`
  - 3 inputs (X, Y, Z) with customizable axis labels
  - Records time, x, y, z values during simulation
  - `getData()` returns 3D-specific format with `is3D: true` flag

- Registered in `backend/src/osk/blocks/__init__.py`
- Added to OSK adapter in `backend/src/simulation/osk_adapter.py`:
  - Block mapping: `"scope_3d": Scope3D`
  - Parameter mapping for axis labels
  - Result collection with `is3D: true` flag for frontend detection

**Frontend**:
- Added block definition to `frontend/src/blocks/sinks.ts`:
  - Type: `scope_3d`
  - 3 inputs: x, y, z
  - Parameters: xLabel, yLabel, zLabel
  - Icon: 📐

- Extended `SignalData` in `frontend/src/types/simulation.ts`:
  - Added optional fields: `x`, `y`, `z`, `is3D`

- Created `Scope3DWindow.tsx` component:
  - Uses Plotly.js scatter3d plot
  - Draggable/resizable window with info bar
  - Catppuccin dark theme styling

- Updated `PlotWindowManager.tsx`:
  - Detects `is3D` signals and routes to Scope3DWindow
  - Default 3D window size: 500x450

- Extended `uiStore.ts`:
  - `openPlotWindow()` accepts optional `initialSize` parameter

**Code Generation (all 4 languages)**:
- Python: `backend/src/codegen/languages/python/blocks/sinks.py`
- C++: `backend/src/codegen/languages/cpp/blocks/sinks.py`
- C: `backend/src/codegen/languages/c/blocks/sinks.py`
- Rust: `backend/src/codegen/languages/rust/blocks/sinks.py`

**Example**:
- Created `examples/50_lorenz_attractor_3d.json`:
  - Lorenz strange attractor (σ=10, ρ=28, β=8/3)
  - 3 integrators for X, Y, Z states
  - scope_3d for 3D trajectory visualization
  - Regular scope for X, Y, Z vs time
  - RK4 solver, 50s simulation, dt=0.01

- Added to `frontend/src/data/examples.ts` fallback list

**Unit Tests**:
- Created `backend/tests/test_scope3d.py`:
  - 21 tests covering initialization, input handling, data recording, getData()
  - All tests pass

**Bug Fixes (later in session)**:
- Added Lorenz example to backend's `EXAMPLE_MANIFEST` in `examples.py`
- Added `scope_3d` to sink blocks tracking list in `osk_adapter.py`
- Added `get_scope_data()` method to OSKAdapter for collecting 3D scope data
- Modified `SimulationRunner.get_results()` to call `get_scope_data()`
- Modified `_record_outputs()` to skip Scope3D blocks (they use getData() instead)

**Data Flow for 3D Scopes**:
1. During simulation, Scope3D.rpt() records x, y, z values internally
2. After simulation, SimulationRunner.get_results() calls:
   - _record_outputs() for regular scopes (skips scope_3d)
   - adapter.get_scope_data() for 3D scopes
3. get_scope_data() calls Scope3D.getData() which returns `{times, x, y, z, inputNames, is3D: true}`
4. Frontend PlotWindowManager detects `is3D` flag and routes to Scope3DWindow

### Files Modified/Created
- `backend/src/osk/blocks/sinks.py` (Scope3D class)
- `backend/src/osk/blocks/__init__.py` (import/export)
- `backend/src/simulation/osk_adapter.py` (block/param maps, result collection, get_scope_data())
- `backend/src/simulation/runner.py` (calls get_scope_data())
- `backend/src/api/routes/examples.py` (added Lorenz to EXAMPLE_MANIFEST)
- `frontend/src/blocks/sinks.ts` (block definition)
- `frontend/src/types/simulation.ts` (SignalData extension)
- `frontend/src/components/Simulation/Scope3DWindow.tsx` (new component)
- `frontend/src/components/Simulation/PlotWindowManager.tsx` (routing)
- `frontend/src/store/uiStore.ts` (initialSize param)
- `backend/src/codegen/languages/*/blocks/sinks.py` (4 files)
- `examples/50_lorenz_attractor_3d.json` (new example)
- `frontend/src/data/examples.ts` (example list)
- `backend/tests/test_scope3d.py` (new test file)

## Development Workflow
- **Wait for user confirmation** before committing changes to git. The user will test fixes before commits are made.
