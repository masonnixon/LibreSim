# LibreSim Project Context

## Project Overview
LibreSim is a web-based block diagram simulation tool designed as an open-source alternative to MathWorks Simulink. It allows users to create, edit, and simulate dynamic systems using a visual block diagram interface.

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
- `math_ops.py` - Sum, Gain, Product, Abs, Sign, Saturation, MathFunction, Trigonometry, DeadZone, Switch
- `continuous.py` - Integrator, Derivative, TransferFunction, StateSpace, PIDController
- `discrete.py` - UnitDelay, ZeroOrderHold, DiscreteIntegrator, DiscreteDerivative, DiscreteTransferFunction
- `signal_processing.py` - MovingAverage, LowPassFilter, HighPassFilter, BandPassFilter
- `nonlinear.py` - RateLimiter, Backlash, CoulombFriction, LookupTable, Relay
- `observers.py` - LuenbergerObserver, KalmanFilter, ExtendedKalmanFilter

## Docker Configuration
- Uses Docker Compose for orchestration
- Frontend container proxies `/api` requests to backend using Docker service name `backend` (not `localhost`)
- Vite config uses `process.env.VITE_BACKEND_URL || 'http://backend:9000'`

## Key Technical Notes

### Algebraic Loop Detection
The compiler detects algebraic loops (circular dependencies with no delay). State-holding blocks break these loops:
```python
STATE_HOLDING_BLOCKS = {
    "integrator", "discrete_integrator", "unit_delay",
    "transfer_function", "discrete_transfer_function", "state_space",
    "derivative", "discrete_derivative", "pid_controller",
    "zero_order_hold", "variable_transport_delay",
    "luenberger_observer", "kalman_filter", "extended_kalman_filter",
    "moving_average", "low_pass_filter", "high_pass_filter",
    "band_pass_filter", "rate_limiter", "backlash",
}
```

### Pydantic v2 Compatibility
- Use `model_config = ConfigDict(populate_by_name=True)` instead of `class Config`
- Import settings from `pydantic_settings` package
- For environment variables with lists, use string type with property converter

### OSK Block Method Signatures
All blocks must implement these methods with correct signatures:
```python
def setInput(self, value, port=0):
def connectInput(self, block, port=0):
def getOutput(self, port=0):
def update(self):
def init(self):  # optional
def rpt(self):   # optional, for recording data
```

### Frontend-Backend Communication
- Simulation starts by POSTing full model data to `/api/simulate/start`
- Frontend polls `/api/simulate/status` for progress
- Results fetched from `/api/simulate/results` when complete

## Current Block Types

### Sources
- Constant, Step, Ramp, Sine, Pulse

### Sinks
- Scope (with multi-input support and automatic signal naming)

### Math Operations
- Sum, Gain, Product, Abs, Sign, Saturation, DeadZone, Switch

### Continuous
- Integrator, Derivative, TransferFunction, StateSpace, PIDController

### Discrete
- UnitDelay, ZeroOrderHold, DiscreteIntegrator, DiscreteDerivative, DiscreteTransferFunction

### Signal Processing
- MovingAverage, LowPassFilter, HighPassFilter, BandPassFilter

### Nonlinear
- RateLimiter, Backlash, CoulombFriction, LookupTable, Relay

### Observers
- LuenbergerObserver, KalmanFilter, ExtendedKalmanFilter

### Routing
- Subsystem (with Inport/Outport for hierarchical modeling)

## Example Models

Located in `examples/` directory:

### JSON Format (LibreSim native)
1. `01_sine_wave_basic.json` - Basic sine wave visualization
2. `02_first_order_step_response.json` - First-order system step response
3. `03_pid_controller.json` - PID control of second-order plant
4. `04_mass_spring_damper.json` - Mechanical system simulation
5. `05_signal_filtering.json` - Low-pass filter demonstration
6. `06_kalman_filter_estimation.json` - State estimation with Kalman filter
7. `07_thermostat_relay_control.json` - Bang-bang/relay control
8. `08_lookup_table_nonlinear.json` - Nonlinear function via lookup table
9. `09_second_order_damping.json` - Damping ratio comparison
10. `10_rate_limiting_quantization.json` - Rate limiter and quantization effects

### MDL Format (Simulink-compatible)
- `01_sine_wave_basic.mdl`
- `02_first_order_step_response.mdl`
- `03_pid_controller.mdl`
- `04_mass_spring_damper.mdl`
- `09_second_order_damping.mdl`

## File Operations
The toolbar supports:
- **Open**: Load LibreSim JSON model files
- **Export**: Save current model as JSON
- **Import**: Load Simulink MDL files (planned)

## File Reference

### Critical Files
- `frontend/vite.config.ts` - Vite config with proxy settings
- `backend/src/config.py` - FastAPI settings with CORS
- `backend/src/api/routes/simulation.py` - Simulation endpoints
- `backend/src/simulation/osk_adapter.py` - Converts model to OSK blocks
- `backend/src/simulation/compiler.py` - Topological sort and algebraic loop detection
- `backend/src/osk/kernel.py` - Main simulation kernel
- `frontend/src/store/modelStore.ts` - Model state management
- `frontend/src/components/Canvas/Canvas.tsx` - Block diagram editor
- `frontend/src/components/Toolbar/Toolbar.tsx` - File operations and simulation controls

## Recent Changes Log

### Session 2024-12-14
- Fixed algebraic loop detection for feedback control systems (STATE_HOLDING_BLOCKS)
- Added file Open/Export functionality in Toolbar
- Created 10 example models (JSON) demonstrating LibreSim capabilities
- Created 5 Simulink MDL format example files
- Fixed Scope signal naming to show source block names

### Session 2024-12-11 (continued)
- Added Control Systems blocks:
  - Signal Processing: MovingAverage, LowPassFilter, HighPassFilter, BandPassFilter
  - Nonlinear: RateLimiter, Backlash, CoulombFriction, LookupTable, Relay
  - Observers: LuenbergerObserver, KalmanFilter, ExtendedKalmanFilter
- Added Subsystem support with Inport/Outport blocks
- Updated frontend block definitions and categories

### Session 2024-12-11
- Fixed Pydantic v2 compatibility issues (model_config, pydantic-settings)
- Fixed Vite proxy to use Docker service name for backend
- Fixed OSK block method signatures (connectInput port parameter)
- Fixed Scope to accept **kwargs for extra frontend params
- Added validation script (backend/validate.py)
- Simulation now runs successfully

## Known Issues / TODO
- PID controller example may produce incorrect results (under investigation)
- MDL import not yet implemented (export only)

## Simulink Reference Documentation
- PID Controller: https://www.mathworks.com/help/simulink/slref/pidcontroller.html
- Mass-Spring-Damper: https://www.mathworks.com/help/simscape/ug/mass-spring-damper-in-simulink-and-simscape.html
- Transfer Functions: https://www.mathworks.com/help/control/ug/step-response-of-transfer-function.html
- Second-Order Systems: https://www.mathworks.com/help/control/ug/second-order-systems.html
