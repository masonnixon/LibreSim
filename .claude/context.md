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
- Sum, Gain, Product, Abs, Sign, Bias, Saturation, DeadZone, Switch, MathFunction, Trigonometry

### Continuous
- Integrator, Derivative, TransferFunction, StateSpace, ZeroPole, TransportDelay, SecondOrder, LimitedIntegrator

### Discrete
- UnitDelay, ZeroOrderHold, FirstOrderHold, DiscreteIntegrator, DiscreteDerivative, DiscreteTransferFunction, DiscreteStateSpace, DiscreteFilter, Memory

### Control Design
- PIDController, DiscretePIDController, LQRController, PolePlacement, LeadLagCompensator, PIController, PDController, AntiWindupPID, ModelReference

### Signal Processing
- MovingAverage, LowPassFilter, HighPassFilter, BandPassFilter

### Nonlinear
- RateLimiter, Backlash, CoulombFriction, LookupTable, Relay

### Observers
- LuenbergerObserver, KalmanFilter, ExtendedKalmanFilter

### Routing
- Subsystem (with Inport/Outport for hierarchical modeling)

### Data Types
- DataTypeConversion, RealImagToComplex, ComplexToRealImag

### Matrix Operations
- MatrixMultiply, MatrixTranspose, MatrixInverse, Selector, Assignment, Concatenate, MatrixSum, VectorNorm

### Aerospace
- QuaternionNormalize, QuaternionMultiply, QuaternionConjugate, QuaternionToEuler, EulerToQuaternion, QuaternionRotateVector, DCMToQuaternion, QuaternionToDCM, ISAAtmosphere, SixDOF, FlatEarthGravity, WGS84Gravity

### DSP (Digital Signal Processing)
- FFT, IFFT, FIRFilter, IIRFilter, Convolution, Downsampler, Upsampler, Interpolator, WindowFunction, Mean, Variance, RMS, PeakDetector, ZeroCrossingDetector

### RF (Radio Frequency)
- RFAmplifier, RFMixer, RFFilter, SParameterNetwork, RFBudgetElement, Attenuator, AMModulator, FMModulator, PhaseNoise, dBmToWatts, WattsTodBm

### Navigation
- CoordinateTransformationConversion, LLAToECEF, ECEFToLLA, ECEFToNED, NEDToECEF, WaypointFollower, GreatCircleDistance, FlatEarthPosition
- WGS84 ellipsoid geodetic transformations

### Sensor Fusion & Tracking
- IMUSensor, Accelerometer, Gyroscope, Magnetometer, GPSSensor, Altimeter
- ComplementaryFilter, MadgwickFilter, MahonyFilter (AHRS attitude estimation)
- INSGPSFusion (loosely coupled INS/GPS)
- AlphaBetaFilter, AlphaBetaGammaFilter (tracking filters)

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
- `frontend/src/components/Properties/PropertiesPanel.tsx` - Block parameter editing
- `frontend/src/components/Simulation/PlotWindow.tsx` - Draggable/resizable plot window
- `frontend/src/components/Simulation/PlotWindowManager.tsx` - Multi-window plot management
- `frontend/src/utils/mdlExporter.ts` - Export to Simulink MDL format
- `frontend/src/utils/mdlImporter.ts` - Import from Simulink MDL format
- `backend/tests/test_block_integration.py` - Frontend-backend integration tests

## Recent Changes Log

### Session 2026-01-02 (Multi-Language Codegen Accuracy Fixes - Part 2)
- **Fixed Transfer Function templates for C, C++, Rust** (all now produce stable, accurate dynamics):
  - **Problem**: Transfer function output was exploding to astronomical values (1e+100+) in generated C/C++/Rust code
  - **Root Cause 1**: Wrong state indexing - Python uses `state[order - j]` (reverse indexing from controllable canonical form) but C/C++/Rust used `state[i]` (forward indexing)
  - **Root Cause 2**: Wrong output computation - Always added direct feedthrough `num[0] * input`, but strictly proper systems (num_len <= order) should have NO feedthrough
  - **Root Cause 3**: Missing `propagate_states()` method with RK4 integration
  - **Solution**: Fixed all three languages to match Python implementation exactly:
    - Derivative: `derivatives[order-1] -= den[j] * state[order - j]` (reverse indexing)
    - Output: `output += num[num_len - 1 - i] * state[i]` (correct coefficient ordering)
    - Feedthrough: Only when `num_len > order` (improper transfer function)
    - Added `propagate_states()` with inline RK4 integration
  - **Files Modified**:
    - `backend/src/codegen/languages/cpp/blocks/continuous.py` - template_transfer_function
    - `backend/src/codegen/languages/c/blocks/continuous.py` - template_transfer_function
    - `backend/src/codegen/languages/rust/blocks/continuous.py` - template_transfer_function
  - **Verification**: C++ generated code compiles and runs correctly, producing stable plant output (~0.9377 at t=10)

### Session 2026-01-02 (Multi-Language Codegen Accuracy Fixes - Part 1)
- **Fixed simulation loop timing for all code generators** (C, C++, Rust):
  - **Problem**: All generators recorded outputs AFTER all RK4 passes, not matching OSK behavior
  - **Root Cause**: Output recording was placed after the kpass loop instead of inside at kpass=0
  - **Solution**: Moved output recording inside the kpass loop, after update() but before propagation
  - **Files Modified**: `c/generator.py`, `cpp/generator.py`, `rust/generator.py`

- **Fixed PID controller integration for all code generators** (C, C++, Rust):
  - **Problem**: PID controller has TWO internal integrators (integral term + derivative filter) but only integral was propagated
  - **Solution**: Added `propagate_states()` method to PID templates in all languages
  - **Files Modified**:
    - `c/blocks/control_design.py` - Added `propagate_states()` that calls `propagate_integrator()` for both states
    - `cpp/blocks/control_design.py` - Added `propagate_states()` method to PID class
    - `rust/blocks/control_design.py` - Added `propagate_states()` method with correct Rust syntax
    - Added `#include "integration.h/hpp"` to blocks headers
    - Added `use crate::integration::{IntegrationMethod, propagate_integrator};` to Rust blocks.rs

- **Added integrator propagation to C generator**:
  - **Problem**: C generator had no integrator propagation at all (misleading comment said "handled in model_step")
  - **Solution**: Added `model_propagate_integrators()` function and `_generate_integrator_propagation()` method
  - **Files Modified**: `c/generator.py` - Added propagation to simulation.h/.c and main.c

- **Updated all generators to call PID propagate_states()**:
  - C: `{struct_name}_propagate_states(&model->{var_name}, dt, kpass, method);`
  - C++: `{var_name}.propagate_states(dt, kpass, method);`
  - Rust: `self.{var_name}.propagate_states(dt, kpass, method);`

- **Python accuracy tests all pass** (5/5):
  - test_01_sine_wave_basic
  - test_02_first_order_step_response
  - test_03_pid_controller
  - test_04_mass_spring_damper
  - test_09_second_order_damping

### Session 2026-01-01 (Python Codegen Multi-State Integration Fix)
- **Fixed Python code generation for multi-state blocks**:
  - **Problem**: Transfer functions, state-space, and second-order blocks produce incorrect outputs (always 0)
  - **Root Cause**: Only `self.state` (first state) was being integrated. For order>1 systems, additional states were never propagated
  - **Solution**: Added `propagate_states(dt, kpass)` method to multi-state block templates

- **Files Modified**:
  - `backend/src/codegen/languages/python/blocks/continuous.py`:
    - Added `propagate_states()` method to `transfer_function_template`
    - Added `propagate_states()` method to `state_space_template`
    - Added `propagate_states()` method to `second_order_template`
    - Added integration state arrays for additional states (states_x0, states_xd0, etc.)

  - `backend/src/codegen/languages/python/generator.py`:
    - Added `multi_state_list` to track blocks with `propagate_states` method
    - Added `_multi_state_blocks` list to Model class
    - Added multi-state propagation call in simulation loop after standard propagator
    - Fixed output signal naming to use source block names instead of "Response_0", "Response_1"

- **Fixed Dockerfile CMD for all languages**:
  - **Problem**: CMD tried to copy from `/output/` which was overwritten by volume mount at runtime
  - **Solution**: Copy from build directory directly (e.g., `build/simulation`, `target/release/simulation`)
  - Files fixed: `c/generator.py`, `cpp/generator.py`, `rust/generator.py`, `python/generator.py`

- **Tests verified**:
  - PID example: Plant output reaches ~0.995 at t=10 (correct step response)
  - Second-order damping: Shows proper underdamped oscillation, critical damping, overdamped response
  - All 29 codegen unit tests pass

### Session 2026-01-01 (Examples Refactoring)
- **Refactored examples.ts to load from JSON files via API**:
  - **Backend**: Added `/api/examples` endpoints (`backend/src/api/routes/examples.py`)
    - `GET /api/examples` - Returns list of available examples with metadata
    - `GET /api/examples/{id}` - Returns full example model JSON
  - **Frontend**: Updated `frontend/src/data/examples.ts`
    - Removed 71K+ tokens of embedded model data
    - Added `fetchExampleList()` and `fetchExample(id)` async functions
    - Added example caching to avoid repeated API calls
    - Kept `exampleList` for fallback/backwards compatibility
  - **Frontend**: Updated `frontend/src/api/client.ts`
    - Added `getExampleList()` and `getExample(id)` API methods
  - **Frontend**: Updated `frontend/src/components/Toolbar/Toolbar.tsx`
    - Changed `handleLoadExample` to async function
    - Now fetches examples from backend API instead of embedded data
    - Added loading toast feedback

- **Previous Session (LibreSim Coder - Numerical Accuracy)**:
  - Added end-to-end numerical accuracy tests (`scripts/test_codegen_accuracy.py`)
  - Fixed port naming mismatch in osk_adapter.py and base.py
  - Fixed inline wiring for proper signal propagation in Python generator
  - Fixed transfer function state sync in continuous.py template
  - Fixed step parameter naming (snake_case vs camelCase) in sources.py template
  - Fixed scope template to return self.output in sinks.py template
  - All 5 accuracy tests pass, all 29 codegen unit tests pass

### Session 2024-12-31 (LibreSim Coder - Block Template Expansion)
- **Added comprehensive block templates across all 4 languages** (Python, C, C++, Rust):

- **Control Design Templates** (`control_design.py` in each language):
  - `pid_controller` - Full PID with filtered derivative
  - `pi_controller` - Proportional-Integral controller
  - `pd_controller` - Proportional-Derivative controller
  - `anti_windup_pid` - PID with back-calculation anti-windup
  - `lead_lag_compensator` - Phase lead/lag compensator
  - `lqr_controller` - Linear Quadratic Regulator
  - `pole_placement` - State feedback via pole placement
  - `model_reference` - Second-order reference model

- **Aerospace Templates** (`aerospace.py` in each language):
  - `quaternion_normalize` - Normalize quaternion to unit length
  - `quaternion_multiply` - Hamilton product of quaternions
  - `quaternion_conjugate` - Quaternion conjugate
  - `quaternion_to_euler` - Convert quaternion to Euler angles (ZYX)
  - `euler_to_quaternion` - Convert Euler angles to quaternion
  - `quaternion_rotate_vector` - Rotate 3D vector by quaternion
  - `dcm_to_quaternion` - DCM to quaternion conversion
  - `quaternion_to_dcm` - Quaternion to DCM conversion
  - `isa_atmosphere` - International Standard Atmosphere model
  - `flat_earth_gravity` - Constant gravity vector
  - `wgs84_gravity` - WGS84 gravity model
  - `six_dof_euler` - 6-DOF equations of motion with Euler angles

- **Previously Added Templates** (from earlier in session):
  - Logic blocks: `compare_to_zero`, `compare_to_constant`, `relational_operator`, `logical_operator`, `bit_operator`
  - Signal processing: `rate_limiter`, `moving_average`, `low_pass_filter`, `high_pass_filter`, `band_pass_filter`, `backlash`, `notch_filter`
  - Nonlinear: `lookup_table_1d`, `lookup_table_2d`, `quantizer`, `relay`, `coulomb_friction`, `wrap_to_range`, `hit_crossing`, `stiction`

- **Updated all `__init__.py` files** in each language's blocks directory to include new templates

- **Block template count per language**: ~75+ blocks (sources, sinks, math_ops, continuous, discrete, logic, signal_processing, nonlinear, control_design, aerospace)

### Session 2024-12-31 (LibreSim Coder - Bug Fixes)
- **Fixed Python Code Generation Bugs**:
  - **Indentation errors**: Fixed templates in `math_ops.py` (`sum_template`, `product_template`, `mux_template`) that had incorrect indentation when generating multi-line attributes
    - Changed `chr(10).join("        " + attr ...)` to `"\n        ".join(input_attrs)` to avoid double-indentation
  - **Wrong update_calls indentation**: Fixed `simulation.py` generator to use 8 spaces instead of 12 for update calls inside `step()` method
  - **Integrator state attribute error**: Separated `INTEGRATOR_BLOCKS` (blocks with state/derivative interface) from `STATE_HOLDING_BLOCKS` (blocks with internal state)
    - Only blocks like `integrator`, `transfer_function`, `state_space`, `second_order` go in `_integrators` list
    - Blocks like `pid_controller`, `kalman_filter`, etc. manage their own state internally

- **Added SQA Validation for Generated Python Code**:
  - Added `_validate_python_code()` method to `PythonCodeGenerator` that uses Python's `compile()` to check for syntax errors
  - Catches and reports indentation errors with file path, line number, and error message before returning generated project

### Session 2024-12-31 (LibreSim Coder - Complete Implementation)
- **Fixed dict to Model Conversion Bug**:
  - Updated `backend/src/codegen/generator.py` to use `Model.model_validate(model)` to convert dict to Model object
  - This fixes "dict object has no attribute blocks" error during code generation

- **Completed C++ Code Generator** (full implementation):
  - `backend/src/codegen/languages/cpp/generator.py` - CppCodeGenerator class with full implementation
  - `backend/src/codegen/languages/cpp/blocks/` - Block templates:
    - `sources.py` - Constant, Step, Ramp, SineWave, Pulse, Clock, Ground
    - `sinks.py` - Scope, Display, Terminator, ToWorkspace
    - `math_ops.py` - Sum, Gain, Product, Abs, Sign, Bias, Saturation, DeadZone, Switch, MathFunction, Trigonometry
    - `continuous.py` - Integrator, Derivative, TransferFunction, StateSpace, SecondOrder, TransportDelay
  - Added C++ header/source generation to `backend/src/codegen/integration.py`

- **Completed Rust Code Generator** (full implementation):
  - `backend/src/codegen/languages/rust/generator.py` - RustCodeGenerator class with full implementation
  - `backend/src/codegen/languages/rust/blocks/` - Block templates:
    - `sources.py` - Constant, Step, Ramp, SineWave, Pulse, Clock, Ground
    - `sinks.py` - Scope, Display, Terminator, ToWorkspace
    - `math_ops.py` - Sum, Gain, Product, Abs, Sign, Bias, Saturation, DeadZone, Switch, MathFunction, Trigonometry
    - `continuous.py` - Integrator, Derivative, TransferFunction, StateSpace, SecondOrder, TransportDelay
  - Updated Rust integration code with `from_str`, `get_num_passes`, and `propagate_integrator` functions

- **Completed Unit Tests** (`backend/tests/test_codegen.py`):
  - 29 comprehensive tests for code generation module, all passing
  - `TestCodeGenerationConfig` - Tests for default and custom config values
  - `TestGeneratedProject` - Tests for file adding and retrieval with `get_file()` API
  - `TestIntegrationCodeGenerator` - Tests for all integration method generators (Python, C, C++, Rust)
  - `TestCodeGenerator` - Tests for generating projects in all 4 languages (Python, C, C++, Rust)
  - `TestBlockTemplates` - Tests for integrator block templates in all languages
  - `TestLanguageEnums` - Tests for Language and IntegrationMethod enum values
  - `TestCompiledModelInfo` - Tests for CompiledModelInfo dataclass creation

### Session 2024-12-31 (LibreSim Coder - Docker/Frontend/C Templates)
- **Completed Docker Compilation Support**:
  - `docker/codegen/docker-compose.yml` - Docker Compose for compiler containers
  - `docker/codegen/compilers/Dockerfile.{python,c,cpp,rust}` - Compiler images
  - `docker/codegen/compilers/compile-{python,c,cpp,rust}.sh` - Build scripts
  - `backend/src/codegen/compilation/docker_compiler.py` - DockerCompiler service class
  - API endpoints: `/api/codegen/compile`, `/api/codegen/compile/status`, `/api/codegen/compile/build-image/{language}`

- **Completed Frontend UI**:
  - `frontend/src/components/CodeGen/CodeGenModal.tsx` - Modal for code generation
  - Updated `frontend/src/store/uiStore.ts` - Added showCodeGenModal state
  - Updated `frontend/src/components/Toolbar/Toolbar.tsx` - Added purple "Generate" button

- **Completed C Code Generator** (full implementation):
  - `backend/src/codegen/languages/c/generator.py` - CCodeGenerator class
  - `backend/src/codegen/languages/c/blocks/` - Block templates:
    - `sources.py` - Constant, Step, Ramp, SineWave, Pulse, Clock, Ground
    - `sinks.py` - Scope, Display, Terminator, ToWorkspace
    - `math_ops.py` - Sum, Gain, Product, Abs, Sign, Bias, Saturation, DeadZone, Switch, MathFunction, Trigonometry
    - `continuous.py` - Integrator, Derivative, TransferFunction, StateSpace, SecondOrder, TransportDelay

### Session 2024-12-31 (LibreSim Coder - Initial Implementation)
- **Added LibreSim Coder** - Code generation feature similar to Simulink Coder:

- **Core Infrastructure** (`backend/src/codegen/`):
  - `generator.py` - Main CodeGenerator orchestrator
  - `models.py` - Data models (GeneratedProject, BlockInfo, etc.)
  - `integration.py` - Integration method code for all languages (Euler, RK2, RK4, Merson)
  - `controller.py` - FastAPI endpoints for code generation

- **Python Code Generator** (fully implemented):
  - Complete project generation with blocks.py, simulation.py, main.py
  - Block templates for sources, sinks, math, continuous, discrete
  - Multi-pass integration support (RK4, Merson)
  - CSV output generation

- **C/C++/Rust Generators** (stub implementations):
  - Project structure with CMakeLists.txt / Cargo.toml
  - Ready for full implementation

- **API Endpoints**:
  - `POST /api/codegen/generate` - Generate code ZIP
  - `GET /api/codegen/info` - Get supported languages/methods/blocks

- **Documentation** (`docs/libresim-coder.md`):
  - Complete user guide for code generation
  - Block support matrix
  - API reference

### Session 2024-12-31 (New Toolboxes Implementation)
- **Added four new blocksets** following the Simulink toolbox pattern:

- **DSP System Toolbox** (`dsp.py`, 14 blocks):
  - Transforms: FFT, IFFT (DFT-based implementation)
  - Filters: FIRFilter, IIRFilter, Convolution
  - Sample rate conversion: Downsampler, Upsampler, Interpolator
  - Window functions: WindowFunction (hamming, hanning, blackman, rectangular, kaiser)
  - Statistics: Mean, Variance, RMS
  - Detection: PeakDetector, ZeroCrossingDetector

- **RF Blockset** (`rf.py`, 11 blocks):
  - Active components: RFAmplifier (with compression, NF, OIP3), RFMixer
  - Passive components: RFFilter, Attenuator
  - Analysis: SParameterNetwork (2-port), RFBudgetElement (Friis formula for cascaded NF)
  - Modulation: AMModulator, FMModulator, PhaseNoise
  - Power conversion: dBmToWatts, WattsTodBm

- **Navigation Toolbox** (`navigation.py`, 8 blocks):
  - Coordinate transforms: CoordinateTransformationConversion (LLA/ECEF/NED/Euler/DCM/Quaternion)
  - Geodetic: LLAToECEF, ECEFToLLA (WGS84 ellipsoid)
  - Local frames: ECEFToNED, NEDToECEF, FlatEarthPosition
  - Navigation: WaypointFollower, GreatCircleDistance (Haversine)

- **Sensor Fusion & Tracking Toolbox** (`sensor_fusion.py`, 12 blocks):
  - Sensors: IMUSensor, Accelerometer, Gyroscope, Magnetometer, GPSSensor, Altimeter
  - Attitude filters: ComplementaryFilter, MadgwickFilter (AHRS), MahonyFilter
  - Navigation: INSGPSFusion (loosely coupled)
  - Tracking: AlphaBetaFilter, AlphaBetaGammaFilter

- **Added unit tests** for all new blocks (4 test files)
- **Added 7 example models** demonstrating new toolboxes:
  - 40: DSP FFT Spectrum Analysis
  - 41: DSP FIR Lowpass Filter
  - 42: RF Receiver Chain Budget Analysis
  - 43: RF AM Modulation
  - 44: Navigation Coordinate Transformations
  - 45: Sensor Fusion AHRS Attitude Estimation
  - 46: Sensor Fusion Alpha-Beta-Gamma Tracking

- **Created blockset development guide** (`docs/blockset-development-guide.md`)
  - Complete step-by-step instructions for adding new blocksets
  - Covers backend implementation, tests, registration, frontend definitions
  - Includes templates and checklist

### Session 2024-12-30 (Product Block Operations Bug Fix)
- **Fixed critical frontend-backend parameter mismatch for Product blocks**:
  - **Root Cause**: Frontend sent `'operations': '2'` (raw MDL numeric string) instead of `'operations': '**'` (proper operation format)
  - Product block interpreted `'2'` as division operation, causing `1.0 / State.EPS = 10 billion` when inputs were 0
  - This corrupted quaternion derivative calculations, producing ~95 million instead of ~5 degrees for euler_y
  - **Fix**: Added `_convert_product_operations()` method in `backend/src/simulation/osk_adapter.py`
  - Converts numeric strings like `'2'` → `'**'`, `'3'` → `'***'`, etc.
  - Conversion happens in `_map_parameters()` ensuring both MDL and frontend API models work correctly

- **Key Lesson**: Frontend may send raw/unconverted parameter values that differ from MDL parser output
  - Always validate and convert parameters at the backend adapter level
  - Integration tests should verify parameter conversion for all block types

### Session 2024-12-28 (Bug Fixes and Integration Tests)
- **Fixed Negative Number Input Bug** (`frontend/src/components/Properties/PropertiesPanel.tsx`):
  - Created `NumberInput` component that uses local state to allow intermediate typing states like "-"
  - Previously, `parseFloat("-")` returned NaN causing the input to reset
  - Now properly handles typing negative numbers in the properties panel

- **Fixed Bias Block (Frontend-Backend Integration)**:
  - The Bias block was defined in frontend but completely missing from backend
  - Added `Bias` class to `backend/src/osk/blocks/math_ops.py` with full vector support
  - Added to exports in `backend/src/osk/blocks/__init__.py`
  - Added to `BLOCK_TYPE_MAP` and `PARAM_MAP` in `backend/src/simulation/osk_adapter.py`
  - Added block definition to `backend/src/blocks/registry.py`

- **Added UI Enhancements** (from previous session):
  - Settings modal for simulation configuration (solver, step size, start/stop time, model info)
  - Model name display in toolbar with dirty indicator
  - Undo/Redo functionality with Ctrl+Z/Ctrl+Y hotkeys
  - Block rotation with Ctrl+R (90-degree increments)
  - Block spread/retract with Ctrl+]/Ctrl+[ hotkeys
  - Ctrl+S for saving

- **Created Integration Test Suite** (`backend/tests/test_block_integration.py`):
  - `TestBlockRegistration`: Verifies all frontend blocks have backend implementations
  - `TestBiasBlock`: Specific tests for Bias block functionality
  - `TestBlockSimulationIntegration`: Tests blocks through the OSK adapter
  - `TestAllMathBlocks`: Comprehensive tests for all math operation blocks
  - `TestAllSourceBlocks`: Tests for all source blocks
  - `TestAllRoutingBlocks`: Tests for Mux/Demux routing blocks
  - Prevents "silent failure" bugs where blocks exist in UI but don't work in simulation
  - 629 backend tests passing with 91% coverage

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
- Multi-language accuracy tests (C/C++/Rust) need Docker-based end-to-end testing framework
- Python codegen accuracy tests pass (5/5), C++ tested manually in Docker and verified working

## Development Environment

### Anaconda Setup
The project uses Anaconda for Python environment management. Create and activate the `libresim` environment:

```bash
# Create the conda environment
conda create -n libresim python=3.11 -y

# Activate the environment
conda activate libresim

# Install backend dependencies
cd backend
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Docker Development
For running the full application stack:
```bash
docker compose up
```
- Frontend: http://localhost:4200
- Backend: http://localhost:9000

## SQA (Software Quality Assurance)

### Overview
LibreSim uses a comprehensive SQA toolkit for maintaining code quality:

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Ruff** | Python linting & formatting | `backend/pyproject.toml` |
| **MyPy** | Python type checking | `backend/pyproject.toml` |
| **Bandit** | Python security scanning | `backend/pyproject.toml` |
| **Pytest** | Python testing + coverage | `backend/pyproject.toml` |
| **ESLint** | TypeScript linting | `frontend/eslint.config.js` |
| **detect-secrets** | Secret detection | `.secrets.baseline` |

### Pre-commit Hooks
Pre-commit hooks run automatically before each commit:
```bash
# Install hooks (one-time setup)
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
```

**Configured hooks** (`.pre-commit-config.yaml`):
- Ruff (lint + format) for Python
- MyPy for Python type checking
- Bandit for security scanning
- ESLint + TSC for frontend
- detect-secrets for secret detection
- General file checks (large files, merge conflicts, trailing whitespace)

### Running Tests
```bash
# Activate conda environment
conda activate libresim
cd backend

# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_blocks.py

# Run with parallel execution
pytest -n auto

# Run with verbose output
pytest -v
```

### GitLab CI Pipeline
The `.gitlab-ci.yml` defines automated CI/CD:
- **Lint stage**: ruff-lint, ruff-format, eslint, typescript-check
- **Test stage**: mypy, pytest (with coverage), frontend-test
- **Security stage**: bandit, dependency-check, npm-audit
- **Build stage**: build-frontend, build-docker

### SQA Documentation
Full documentation in `docs/SQA.md` covers:
- Tool configurations and usage
- Test writing conventions
- Continuous improvement guidelines
- Troubleshooting common issues

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
