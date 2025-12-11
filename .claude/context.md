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

### Backend (Python + FastAPI)
- **Port**: 9000
- **Framework**: FastAPI
- **Validation**: Pydantic v2 (requires `pydantic-settings` separate package)
- **Key Directories**:
  - `backend/src/api/routes/` - API route handlers (simulation.py, models.py)
  - `backend/src/models/` - Pydantic data models
  - `backend/src/osk/` - Object-oriented Simulation Kernel
  - `backend/src/simulation/` - Simulation runner and OSK adapter

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

## Docker Configuration
- Uses Docker Compose for orchestration
- Frontend container proxies `/api` requests to backend using Docker service name `backend` (not `localhost`)
- Vite config uses `process.env.VITE_BACKEND_URL || 'http://backend:9000'`

## Key Technical Notes

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

## Current Block Types (Frontend)

### Sources
- Constant, Step, Ramp, Sine, Pulse

### Sinks
- Scope (with multi-input support)

### Math Operations
- Sum, Gain, Product

### Continuous
- Integrator, Derivative, TransferFunction

### Discrete
- UnitDelay, ZeroOrderHold, DiscreteIntegrator

## Planned Features

### Subsystems
- Allow grouping multiple blocks into a single "Subsystem" block
- Subsystems have input/output ports
- Can be expanded/collapsed in the UI
- Hierarchical model organization

### Additional Control Systems Blocks
- State Observer (Luenberger)
- Kalman Filter
- LQR Controller
- Model Reference Adaptive Control
- Bode Plot / Frequency Response
- Root Locus visualization

### Example Models
- Simple feedback control
- Mass-spring-damper system
- DC motor control
- Inverted pendulum

## Recent Changes Log

### Session 2024-12-11
- Fixed Pydantic v2 compatibility issues (model_config, pydantic-settings)
- Fixed Vite proxy to use Docker service name for backend
- Fixed OSK block method signatures (connectInput port parameter)
- Fixed Scope to accept **kwargs for extra frontend params
- Added validation script (backend/validate.py)
- Simulation now runs successfully

## File Reference

### Critical Files
- `frontend/vite.config.ts` - Vite config with proxy settings
- `backend/src/config.py` - FastAPI settings with CORS
- `backend/src/api/routes/simulation.py` - Simulation endpoints
- `backend/src/simulation/osk_adapter.py` - Converts model to OSK blocks
- `backend/src/osk/kernel.py` - Main simulation kernel
- `frontend/src/store/modelStore.ts` - Model state management
- `frontend/src/components/Canvas/Canvas.tsx` - Block diagram editor
