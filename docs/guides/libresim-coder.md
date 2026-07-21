# LibreSim Coder

LibreSim Coder is a code generation feature that converts LibreSim block diagram models into standalone simulation code in multiple programming languages, similar to Simulink Coder.

## Features

- **Multi-Language Support**: Generate code in Python, C, C++, and Rust
- **Complete Project Output**: Generates full project structure with build files
- **All Blocks Supported**: Covers all 100+ LibreSim blocks
- **Docker-Based Compilation**: Consistent builds using containerized compilers
- **Standalone Executables**: Produces both library and executable with example main()

## Supported Languages

| Language | Build System | Output |
|----------|--------------|--------|
| Python | pip/setuptools | Package + script |
| C | CMake | Library + executable |
| C++ | CMake | Library + executable |
| Rust | Cargo | Crate + binary |

## Quick Start

### From the UI

1. Create or load a model in LibreSim
2. Click **Generate Code** in the toolbar
3. Select target language (Python, C, C++, or Rust)
4. Configure options (integration method, step size, etc.)
5. Click **Download Source Code** or **Build & Download Executable**

### From the API

```bash
# Generate Python code
curl -X POST http://localhost:9000/api/codegen/generate \
  -H "Content-Type: application/json" \
  -d '{"model": {...}, "config": {"language": "python"}}' \
  --output simulation.zip

# Generate and compile C executable
curl -X POST http://localhost:9000/api/codegen/compile \
  -H "Content-Type: application/json" \
  -d '{"model": {...}, "config": {"language": "c"}}' \
  --output simulation
```

## Generated Project Structure

### Python

```
my_simulation/
├── simulation.py       # Model class with step() function
├── blocks.py           # Generated block classes
├── integration.py      # RK4/Euler/Merson integration
├── main.py             # Example: runs simulation, outputs CSV
├── requirements.txt    # Dependencies (numpy)
├── setup.py            # Package installation
└── README.md           # Usage instructions
```

### C

```
my_simulation/
├── include/
│   ├── simulation.h    # Public API
│   ├── blocks.h        # Block structures
│   └── integration.h   # Integration methods
├── src/
│   ├── simulation.c    # Model implementation
│   ├── blocks.c        # Block implementations
│   ├── integration.c   # RK4/Euler/Merson
│   └── main.c          # Example executable
├── CMakeLists.txt      # CMake build configuration
└── README.md
```

### C++

```
my_simulation/
├── include/
│   ├── simulation.hpp
│   ├── blocks.hpp
│   └── integration.hpp
├── src/
│   ├── simulation.cpp
│   ├── blocks.cpp
│   └── main.cpp
├── CMakeLists.txt
└── README.md
```

### Rust

```
my_simulation/
├── src/
│   ├── lib.rs          # Library crate
│   ├── blocks.rs       # Block implementations
│   ├── integration.rs  # Integration methods
│   └── main.rs         # Binary example
├── Cargo.toml          # Package manifest
└── README.md
```

## Configuration Options

| Option | Description | Values |
|--------|-------------|--------|
| `language` | Target language | `python`, `c`, `cpp`, `rust` |
| `integrationMethod` | Numerical integration | `euler`, `rk2`, `rk4`, `merson` |
| `stepSize` | Fixed time step | e.g., `0.01` |
| `stopTime` | Simulation duration | e.g., `10.0` |
| `projectName` | Output project name | e.g., `my_simulation` |
| `includeCSVOutput` | Add CSV output to main() | `true`, `false` |

## Integration Methods

LibreSim Coder supports four numerical integration methods:

### Euler (1-pass)
Simple forward Euler method. Fast but less accurate.
```
x(t+dt) = x(t) + dt * x'(t)
```

### RK2 (2-pass)
Midpoint method (2nd order Runge-Kutta). Good balance of speed and accuracy.
```
k1 = x'(t)
k2 = x'(t + dt/2, x + dt/2 * k1)
x(t+dt) = x(t) + dt * k2
```

### RK4 (4-pass)
Classic 4th order Runge-Kutta. High accuracy, standard for most simulations.
```
k1 = x'(t)
k2 = x'(t + dt/2, x + dt/2 * k1)
k3 = x'(t + dt/2, x + dt/2 * k2)
k4 = x'(t + dt, x + dt * k3)
x(t+dt) = x(t) + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
```

### Merson (5-pass)
4th order with embedded error estimation. Useful for adaptive step sizing.

## Block Support

LibreSim Coder supports all built-in block types organized by category:

### Sources (14 blocks)
- Constant, Step, Ramp, SineWave, Pulse, Clock
- WhiteNoise, FromWorkspace, Ground
- And more...

### Sinks (4 blocks)
- Scope, ToWorkspace, Display, Terminator

### Math Operations (30 blocks)
- Sum, Gain, Product, Abs, Sign, Bias
- Saturation, DeadZone, Switch
- MathFunction, Trigonometry
- Mux, Demux
- And more...

### Continuous (9 blocks)
- Integrator, Derivative
- TransferFunction, StateSpace, ZeroPole
- TransportDelay, SecondOrder
- LimitedIntegrator

### Discrete (10 blocks)
- UnitDelay, ZeroOrderHold, FirstOrderHold
- DiscreteIntegrator, DiscreteDerivative
- DiscreteTransferFunction, DiscreteStateSpace
- Memory

### Control Design (10 blocks)
- PIDController, DiscretePIDController
- LQRController, PolePlacement
- LeadLagCompensator
- PIController, PDController
- AntiWindupPID, ModelReference

### Signal Processing (10 blocks)
- MovingAverage
- LowPassFilter, HighPassFilter, BandPassFilter

### Nonlinear (10 blocks)
- RateLimiter, Backlash
- CoulombFriction, LookupTable, Relay

### Observers (3 blocks)
- LuenbergerObserver
- KalmanFilter, ExtendedKalmanFilter

### Matrix Operations (8 blocks)
- MatrixMultiply, MatrixTranspose, MatrixInverse
- Selector, Assignment, Concatenate
- MatrixSum, VectorNorm

### DSP System Toolbox (14 blocks)
- FFT, IFFT
- FIRFilter, IIRFilter, Convolution
- Downsampler, Upsampler, Interpolator
- WindowFunction
- Mean, Variance, RMS
- PeakDetector, ZeroCrossingDetector

### RF Blockset (11 blocks)
- RFAmplifier, RFMixer, RFFilter
- SParameterNetwork, RFBudgetElement
- Attenuator
- AMModulator, FMModulator
- PhaseNoise
- dBmToWatts, WattsTodBm

### Navigation Toolbox (8 blocks)
- CoordinateTransformationConversion
- LLAToECEF, ECEFToLLA
- ECEFToNED, NEDToECEF
- WaypointFollower, GreatCircleDistance
- FlatEarthPosition

### Sensor Fusion & Tracking (12 blocks)
- IMUSensor, Accelerometer, Gyroscope, Magnetometer
- GPSSensor, Altimeter
- ComplementaryFilter, MadgwickFilter, MahonyFilter
- INSGPSFusion
- AlphaBetaFilter, AlphaBetaGammaFilter

## API Reference

### POST /api/codegen/generate

Generate source code from a model.

**Request Body:**
```json
{
  "model": {
    "id": "model-id",
    "metadata": { ... },
    "blocks": [ ... ],
    "connections": [ ... ],
    "simulationConfig": { ... }
  },
  "config": {
    "language": "python",
    "integrationMethod": "rk4",
    "stepSize": 0.01,
    "stopTime": 10.0,
    "projectName": "my_simulation",
    "includeCSVOutput": true
  }
}
```

**Response:** ZIP file containing generated project

### POST /api/codegen/compile

Generate and compile code to executable.

**Request Body:** Same as `/generate`

**Response:** Compiled binary executable

### GET /api/codegen/templates

Get list of supported block types.

**Response:**
```json
{
  "blocks": ["constant", "step", "integrator", ...],
  "languages": ["python", "c", "cpp", "rust"],
  "integrationMethods": ["euler", "rk2", "rk4", "merson"]
}
```

## Docker Compilation

LibreSim Coder uses Docker containers for consistent cross-platform compilation.

### Available Compiler Images

| Image | Base | Toolchain |
|-------|------|-----------|
| `libresim-compiler-python` | python:3.11 | pip, numpy |
| `libresim-compiler-c` | gcc:13 | gcc, cmake, make |
| `libresim-compiler-cpp` | gcc:13 | g++, cmake, make |
| `libresim-compiler-rust` | rust:1.75 | rustc, cargo |

### Building Compiler Images

```bash
cd docker/codegen
docker-compose build
```

### Manual Compilation

If you prefer to compile locally instead of using Docker:

**Python:**
```bash
cd my_simulation
pip install -e .
python main.py
```

**C:**
```bash
cd my_simulation
mkdir build && cd build
cmake ..
make
./simulation
```

**Rust:**
```bash
cd my_simulation
cargo build --release
./target/release/simulation
```

## Architecture

### Code Generation Flow

```
┌─────────────────┐
│  LibreSim Model │
│   (JSON/API)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ModelCompiler  │  ← Existing: topological sort, flattening
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CompiledModel  │  ← Execution order, connections, parameters
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LanguageGenerator│  ← Python/C/C++/Rust specific
└────────┬────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  blocks.py   │ │ integration  │ │   main.py    │ │  setup.py    │
│  (classes)   │ │   .py        │ │  (example)   │ │ (build)      │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
         │
         ▼
┌─────────────────┐
│  ZIP Download   │  ← or DockerCompiler → Binary
└─────────────────┘
```

### Block Template System

Blocks are organized by pattern to reduce code duplication:

| Pattern | Blocks | Characteristics |
|---------|--------|-----------------|
| Stateless | Gain, Sum, Trig | No state, direct I/O mapping |
| Single State | Integrator | One integrator state |
| Multi State | TransferFunction, StateSpace | Multiple integrator states |
| Buffer Based | MovingAverage, Delay | History buffer |
| Vector I/O | FFT, Mux, Demux | Vector signals |

## Examples

### Simple Sine Wave

**Model:** SineWave → Scope

**Generated Python:**
```python
from simulation import Model, run_simulation

model = Model()
results = run_simulation(model, dt=0.01, t_end=10.0)
print(f"Generated {len(results['time'])} data points")
```

### PID Controller

**Model:** Step → Sum → PID → Plant → Scope (with feedback)

**Generated C:**
```c
#include "simulation.h"

int main() {
    Model model;
    model_init(&model);

    double t = 0.0;
    while (t <= 10.0) {
        model_step(&model, t, 0.01);
        printf("%f,%f\n", t, model.scope1_output);
        t += 0.01;
    }

    return 0;
}
```

## Limitations

- **Fixed-step only**: Variable-step solvers not yet supported
- **No code optimization**: Generated code is straightforward, not optimized
- **Single-rate**: Multi-rate systems run at the fastest rate
- **No S-Function support**: Custom S-Functions cannot be exported

## Future Enhancements

- Variable-step solvers (ODE45-equivalent)
- Code optimization passes
- Multi-rate support
- HDL generation (VHDL/Verilog)
- Real-time target support
