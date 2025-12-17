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

## Library Block System

Libraries allow importing reusable subsystem blocks from Simulink MDL files:

### How It Works
1. **Import Library**: Use "Import → Import Library" to load an MDL file
2. **Extract Subsystems**: All top-level subsystem blocks become library block definitions
3. **Reusable Blocks**: Library blocks appear in the sidebar under "Imported Libraries"
4. **Instance Creation**: Dragging a library block creates a copy with unique IDs

### Key Types
```typescript
interface LibraryBlockDefinition extends BlockDefinition {
  isLibraryBlock: true
  libraryId: string
  libraryName: string
  implementation: LibraryBlockImplementation
}

interface LibraryBlockImplementation {
  blocks: BlockInstance[]
  connections: Connection[]
  portMappings: LibraryPortMapping[]
}
```

### Architecture
- **Library Store** (`libraryStore.ts`): Manages imported libraries with localStorage persistence
- **Block Registry**: Dynamically registers library blocks for sidebar display
- **Model Store**: Copies implementation when library block is added to model
- **Backend Compiler**: Flattens library blocks same as regular subsystems

### Use Case: Quaternion Library
The quaternionLib.mdl contains:
- `Quaternion` - Base block with properties
- `Quaternion Normalize` - Method to normalize quaternion
- `Quaternion Conjugate` - Method to get conjugate
- etc.

Each becomes a reusable library block that can be dragged into any model.

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
- **New**: Create a new blank model
- **Open**: Load LibreSim JSON model files
- **Save**: Save to browser localStorage
- **Export JSON**: Download current model as JSON file
- **Export MDL**: Download as Simulink-compatible MDL file
- **Import**: Load JSON or Simulink MDL files

## File Reference

### Critical Files
- `frontend/vite.config.ts` - Vite config with proxy settings
- `backend/src/config.py` - FastAPI settings with CORS
- `backend/src/api/routes/simulation.py` - Simulation endpoints
- `backend/src/simulation/osk_adapter.py` - Converts model to OSK blocks
- `backend/src/simulation/compiler.py` - Topological sort and algebraic loop detection
- `backend/src/osk/kernel.py` - Main simulation kernel
- `frontend/src/store/modelStore.ts` - Model state management
- `frontend/src/store/uiStore.ts` - UI state including plot windows
- `frontend/src/components/Editor/Editor.tsx` - Block diagram editor with React Flow
- `frontend/src/components/Toolbar/Toolbar.tsx` - File operations and simulation controls
- `frontend/src/components/Sidebar/Sidebar.tsx` - Block library with mobile tap-to-add
- `frontend/src/components/Simulation/PlotWindow.tsx` - Draggable/resizable plot window
- `frontend/src/components/Simulation/PlotWindowManager.tsx` - Multi-window plot management
- `frontend/src/utils/mdlExporter.ts` - Export to Simulink MDL format
- `frontend/src/utils/mdlImporter.ts` - Import from Simulink MDL format

## Recent Changes Log

### Session 2024-12-14 (Library Block System)
- **Added Library Block Architecture**:
  - Library blocks are reusable subsystem definitions imported from MDL files
  - Libraries are stored separately from models and persist in localStorage
  - Library blocks appear in a dedicated "Imported Libraries" section in the sidebar
  - Dragging a library block creates a subsystem with the implementation copied

- **New Files**:
  - `frontend/src/types/library.ts` - Type definitions for Library, LibraryBlockDefinition, LibraryBlockImplementation
  - `frontend/src/store/libraryStore.ts` - Zustand store for managing imported libraries with persistence

- **Block Registry Updates** (`frontend/src/blocks/index.ts`):
  - Added `registerLibraryBlock()`, `registerLibraryBlocks()` for dynamic registration
  - Added `unregisterLibrary()` to remove all blocks from a library
  - Added `getLibraryBlocks()`, `getBlocksByLibrary()` for querying
  - Added `subscribe()` for reactive UI updates when library blocks change
  - Added `isLibraryBlock()` check

- **MDL Importer Updates** (`frontend/src/utils/mdlImporter.ts`):
  - Added `importMDLAsLibrary()` - imports MDL as library of reusable blocks
  - Added `isMDLLibrary()` - checks if MDL has multiple subsystem blocks
  - Added `subsystemToLibraryBlock()` - converts subsystem to LibraryBlockDefinition

- **Toolbar Updates** (`frontend/src/components/Toolbar/Toolbar.tsx`):
  - Import dropdown now has "Import Model" and "Import Library" options
  - Library import registers blocks with registry for immediate use

- **Sidebar Updates** (`frontend/src/components/Sidebar/Sidebar.tsx`):
  - Added "Imported Libraries" section below built-in categories
  - Shows library name, block count, and expandable block list
  - Library blocks have cyan styling to distinguish from built-in blocks
  - Remove library button (X) with confirmation
  - Search filters library blocks too

- **Model Store Updates** (`frontend/src/store/modelStore.ts`):
  - `addBlock()` now handles LibraryBlockDefinition
  - Copies implementation (children, childConnections) when adding library block
  - Regenerates IDs to avoid conflicts between multiple instances

### Session 2024-12-14 (MDL Library Import)
- **Fixed MDL tokenizer** to handle square bracket arrays `[1, 2, 3]` as single tokens
  - Previously, arrays like `Position [100, 200, 300, 400]` were incorrectly parsed
- **Improved MDL parser** for Simulink Library files:
  - Added support for `Library { }` format (not just `Model { }`)
  - Handle nested `System` blocks inside subsystem definitions
  - Skip Simulink config objects (`Simulink.ConfigSet`, `*CC` classes)
  - Merge `Simulink.BlockDiagram` contents into parent
  - Added `Object`, `Array`, `Branch`, `Port`, `Annotation` to parsed elements
- **Subsystem navigation** (double-click to enter):
  - Added `currentPath` state to track navigation hierarchy
  - `enterSubsystem()`, `exitSubsystem()`, `navigateToPath()` functions
  - `getCurrentBlocks()`, `getCurrentConnections()` for current view
  - Breadcrumb navigation UI in Editor
  - Escape key to exit subsystem
- **Added missing block definitions**:
  - Routing: `reshape`, `selector`, `concatenate`, `data_type_conversion`, `terminator`, `ground`
  - Math: `dot_product`, `sqrt`, `unary_minus`, `minmax`, `bias`
- **Fixed duplicate React key warnings** with improved unique ID generation
- **Edge validation** in Editor to filter invalid connections before React Flow

### Session 2024-12-14 (continued)
- Added MDL export functionality (Simulink-compatible output)
- Added mobile tap-to-add for sidebar blocks
- Made MiniMap responsive (smaller on mobile)
- Implemented multi-window plot system:
  - PlotWindow component with drag/resize/minimize
  - PlotWindowManager for per-scope-block windows
  - Window z-ordering (click to bring to front)
- Added MDL import functionality:
  - Full MDL parser (tokenizer + hierarchical parser)
  - 30+ Simulink block type mappings
  - Parameter conversion for all block types
  - Connection/Line parsing

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

## Development Workflow
- **Wait for user confirmation** before committing changes to git. The user will test fixes before commits are made.

## Recent UI/UX Enhancements

### Mobile Support
- **Tap-to-add blocks**: On mobile devices, tapping a block in the sidebar adds it directly to the canvas (since drag-and-drop doesn't work well on touch)
- **Responsive MiniMap**: MiniMap shrinks to 100x60 on mobile screens (< 768px)
- **Auto-collapse sidebar**: Sidebar collapses after adding a block on mobile
- **Visual hints**: Blue banner and "+" icons on blocks when in mobile mode

### Multi-Window Plot System
- Each Scope/XY Graph block gets its own dedicated floating window
- Windows are **draggable** (header) and **resizable** (all edges/corners)
- Windows can be **minimized** to just the header bar
- Click any window to bring it to front (z-ordering)
- Auto-opens windows when simulation completes
- Toolbar "Scopes" button toggles all windows open/closed
- Components: `PlotWindow.tsx`, `PlotWindowManager.tsx`

### File Import/Export
- **MDL Export**: Export models to Simulink-compatible MDL format
- **MDL Import**: Import Simulink MDL files with full block/connection parsing
- Supports 30+ Simulink block types with parameter conversion
- Auto-detects MDL format from file content

## Simulink Reference Documentation
- PID Controller: https://www.mathworks.com/help/simulink/slref/pidcontroller.html
- Mass-Spring-Damper: https://www.mathworks.com/help/simscape/ug/mass-spring-damper-in-simulink-and-simscape.html
- Transfer Functions: https://www.mathworks.com/help/control/ug/step-response-of-transfer-function.html
- Second-Order Systems: https://www.mathworks.com/help/control/ug/second-order-systems.html
