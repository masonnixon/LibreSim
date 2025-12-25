# LibreSim

A web-based block diagram simulation tool inspired by Simulink, powered by the Object-oriented Simulation Kernel (OSK).

## Overview

LibreSim provides a graphical environment for modeling, simulating, and analyzing dynamic systems. It features a drag-and-drop block diagram editor, real-time simulation visualization, and support for importing Simulink `.mdl` files.

## Features

- **Visual Block Diagram Editor**: Drag-and-drop interface for building system models
- **Control Systems Focus**: Comprehensive library of blocks for control system design
- **Real-time Simulation**: Live visualization of simulation results with scopes and plots
- **Simulink Import**: Import existing `.mdl` model files
- **Multiple Solvers**: RK4, Euler, and Merson's method ODE solvers
- **Extensible Architecture**: Easy to add custom blocks and solvers

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend (React)                        │
│  Block Editor │ Properties Panel │ Simulation Viewer    │
└─────────────────────────┬───────────────────────────────┘
                          │ REST API / WebSocket
┌─────────────────────────▼───────────────────────────────┐
│                  Backend (FastAPI)                       │
│  Model Management │ Simulation Control │ MDL Parser     │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│           Object-oriented Simulation Kernel (OSK)        │
│  Blocks │ Signals │ Solvers │ Simulation Engine         │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Docker (optional, for containerized deployment)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/LibreSim.git
   cd LibreSim
   ```

2. **Start the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn src.main:app --reload --port 9000
   ```

3. **Start the frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Open in browser**
   Navigate to `http://localhost:4200`

### Using Docker

```bash
docker-compose up --build
```

## Project Structure

```
LibreSim/
├── frontend/           # React application
│   ├── src/
│   │   ├── components/ # UI components
│   │   ├── blocks/     # Block type definitions
│   │   ├── store/      # State management
│   │   └── api/        # API client
│   └── package.json
├── backend/            # FastAPI server
│   ├── src/
│   │   ├── api/        # REST endpoints
│   │   ├── simulation/ # OSK integration
│   │   ├── osk/        # Object-oriented Simulation Kernel
│   │   └── parsers/    # MDL file parser
│   └── requirements.txt
├── examples/           # Example models with documentation
└── docs/               # Documentation
```

---

## Block Library

LibreSim provides a comprehensive library of blocks for building dynamic system models. Each block is designed to match Simulink behavior where applicable.

### Sources

Blocks that generate signals without requiring input connections.

#### Constant
Outputs a constant value throughout the simulation.
- **Parameters**: `value` - The constant output value (supports numbers and expressions)

#### Step
Generates a step function that transitions between two values at a specified time.
- **Parameters**:
  - `stepTime` - Time of step transition
  - `initialValue` - Output before step time
  - `finalValue` - Output after step time

#### Ramp
Outputs a linearly increasing signal starting at a specified time.
- **Parameters**:
  - `slope` - Rate of change (units/second)
  - `startTime` - Time when ramp begins
  - `initialOutput` - Output before start time

#### Sine Wave
Generates a sinusoidal signal with configurable amplitude, frequency, phase, and DC bias.
- **Parameters**:
  - `amplitude` - Peak amplitude
  - `frequency` - Frequency in Hertz
  - `phase` - Phase offset in radians
  - `bias` - DC offset

#### Pulse Generator
Outputs a periodic pulse train (square wave).
- **Parameters**:
  - `amplitude` - Pulse amplitude
  - `period` - Pulse period in seconds
  - `dutyCycle` - Percentage of period at high level (0-100%)
  - `phaseDelay` - Delay before first pulse

#### Clock
Outputs the current simulation time. Useful for time-dependent calculations.

#### White Noise (AWGN)
Additive White Gaussian Noise source for modeling sensor noise, process disturbances, and communication channels.
- **Parameters**:
  - `mean` - Mean value of the noise distribution
  - `variance` - Variance (σ²) of the noise. Standard deviation = √variance
  - `seed` - Optional random seed for reproducibility
  - `sampleTime` - Sample time for discrete noise (0 = continuous)

#### Uniform Noise
Generates uniformly distributed random values between specified bounds.
- **Parameters**:
  - `minimum` - Lower bound of distribution
  - `maximum` - Upper bound of distribution
  - `seed` - Optional random seed for reproducibility
  - `sampleTime` - Sample time for discrete noise

---

### Sinks

Blocks that receive signals for visualization or data export.

#### Scope
Displays signals as time-series plots. Supports multiple input channels with automatic legend generation.
- **Parameters**: `numInputs` - Number of input channels (1-8)

#### Display
Shows the current numerical value of a signal.

#### To Workspace
Exports signal data for post-processing analysis.
- **Parameters**: `variableName` - Name for the exported data

#### Terminator
Terminates an unconnected output port (prevents warnings).

---

### Continuous

Blocks for modeling continuous-time dynamics.

#### Integrator
Integrates the input signal over time: y(t) = ∫u(τ)dτ + y₀
- **Parameters**:
  - `initialCondition` - Initial output value y₀
  - `limitOutput` - Enable output saturation
  - `upperLimit` / `lowerLimit` - Saturation bounds

#### Derivative
Computes the time derivative of the input signal: y = du/dt
- **Parameters**: `coefficient` - Multiplicative factor

**Note**: Pure differentiation amplifies high-frequency noise. Consider using filtered derivative or transfer functions for noisy signals.

#### Transfer Function
Implements a continuous-time transfer function H(s) = N(s)/D(s).
- **Parameters**:
  - `numerator` - Coefficients [bₙ, bₙ₋₁, ..., b₁, b₀] (highest power first)
  - `denominator` - Coefficients [aₙ, aₙ₋₁, ..., a₁, a₀]

Example: H(s) = (s + 2)/(s² + 3s + 2) → numerator: [1, 2], denominator: [1, 3, 2]

#### State-Space
Models a system using state-space representation:
```
ẋ = Ax + Bu
y = Cx + Du
```
- **Parameters**:
  - `A` - State matrix (n×n)
  - `B` - Input matrix (n×m)
  - `C` - Output matrix (p×n)
  - `D` - Feedthrough matrix (p×m)
  - `initialCondition` - Initial state vector x₀

#### PID Controller
Implements a PID (Proportional-Integral-Derivative) controller with filtered derivative.
- **Parameters**:
  - `Kp` - Proportional gain
  - `Ki` - Integral gain
  - `Kd` - Derivative gain
  - `N` - Derivative filter coefficient (higher = less filtering)
  - `initialConditionI` - Initial integrator value

Transfer function: `C(s) = Kp + Ki/s + Kd·N·s/(s+N)`

---

### Discrete

Blocks for discrete-time (sampled) systems.

#### Unit Delay
Delays the input by one sample period: y[k] = u[k-1]
- **Parameters**:
  - `initialCondition` - Output at first time step
  - `sampleTime` - Sample period

#### Zero-Order Hold
Samples a continuous signal and holds the value constant between samples.
- **Parameters**: `sampleTime` - Sample period

#### Discrete Integrator
Discrete-time integration using forward Euler, backward Euler, or trapezoidal methods.
- **Parameters**:
  - `method` - Integration method ('forward', 'backward', 'trapezoidal')
  - `sampleTime` - Sample period
  - `initialCondition` - Initial output value

#### Discrete Derivative
Discrete-time differentiation: y[k] = (u[k] - u[k-1]) / Ts
- **Parameters**:
  - `sampleTime` - Sample period
  - `initialCondition` - Initial previous value

#### Discrete Transfer Function
Implements a discrete-time transfer function H(z).
- **Parameters**:
  - `numerator` - Numerator coefficients
  - `denominator` - Denominator coefficients
  - `sampleTime` - Sample period

---

### Math Operations

Blocks for mathematical computations.

#### Sum
Adds or subtracts multiple inputs based on a sign specification.
- **Parameters**: `signs` - String of '+' and '-' characters (e.g., "++−" for in1 + in2 - in3)

#### Gain
Multiplies the input by a constant: y = K·u
- **Parameters**: `gain` - Multiplicative constant K

#### Product
Multiplies or divides multiple inputs.
- **Parameters**: `operations` - String of '*' and '/' characters

#### Abs
Outputs the absolute value of the input: y = |u|

#### Sign
Outputs the sign of the input: y = sign(u) ∈ {-1, 0, 1}

#### Math Function
Applies various mathematical functions to the input.
- **Parameters**:
  - `function` - One of: 'exp', 'log', 'log10', 'sqrt', 'pow', 'square', 'reciprocal'
  - `exponent` - Power for 'pow' function

#### Trigonometry
Applies trigonometric functions.
- **Parameters**: `function` - One of: 'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2', 'sinh', 'cosh', 'tanh'

#### Saturation
Limits the output to specified bounds.
- **Parameters**:
  - `upperLimit` - Maximum output value
  - `lowerLimit` - Minimum output value

#### Dead Zone
Outputs zero for inputs within a specified range, otherwise passes the input shifted toward zero.
- **Parameters**:
  - `start` - Lower threshold
  - `end` - Upper threshold

#### Switch
Selects between two inputs based on a control signal.
- **Parameters**:
  - `threshold` - Switching threshold
  - `criteria` - Comparison type ('>=', '>', '~=0')

---

### Signal Routing

Blocks for combining and separating signals.

#### Mux
Combines multiple scalar inputs into a vector output.
- **Parameters**: `numInputs` - Number of inputs to combine

#### Demux
Splits a vector input into multiple scalar outputs.
- **Parameters**: `numOutputs` - Number of output signals

#### Reshape
Changes the dimensions of a signal without changing its data.
- **Parameters**: `outputDimensions` - New signal dimensions

---

### Signal Processing

Blocks for filtering and signal conditioning.

#### Moving Average Filter
Computes the running average over a sliding window. Provides smoothing with linear phase response.
- **Parameters**: `windowSize` - Number of samples to average

The moving average filter is an FIR filter that provides equal weighting to all samples in the window. Delay is (windowSize - 1) / 2 samples.

#### Low-Pass Filter
First-order IIR low-pass filter for removing high-frequency noise.
- **Parameters**: `cutoffFrequency` - -3dB cutoff frequency in Hz

**Transfer function**: H(s) = ωc / (s + ωc), where ωc = 2π·fc

**Phase Delay Tradeoff**: Lower cutoff frequencies provide better noise rejection but introduce more phase lag. The group delay is approximately τ ≈ 1/(2π·fc):
- 1 Hz cutoff → ~159 ms delay
- 3 Hz cutoff → ~53 ms delay
- 10 Hz cutoff → ~16 ms delay

This is critical in feedback control systems where excessive filter lag can destabilize the loop.

#### High-Pass Filter
First-order IIR high-pass filter for removing DC offset and low-frequency drift.
- **Parameters**: `cutoffFrequency` - -3dB cutoff frequency in Hz

#### Band-Pass Filter
Passes frequencies within a specified range, attenuating others.
- **Parameters**:
  - `lowCutoff` - Lower -3dB frequency
  - `highCutoff` - Upper -3dB frequency

#### Analog Filter (Advanced)
Configurable IIR filter supporting multiple classic filter designs. Similar to Simulink's Analog Filter Design block.
- **Parameters**:
  - `design` - Filter design method: 'butterworth', 'chebyshev1', 'chebyshev2', 'bessel'
  - `response` - Response type: 'lowpass', 'highpass', 'bandpass', 'bandstop'
  - `order` - Filter order (1-10)
  - `cutoffFrequency` - Cutoff frequency in Hz (for lowpass/highpass)
  - `lowCutoff` / `highCutoff` - Band edges for bandpass/bandstop
  - `passbandRipple` - Passband ripple in dB (Chebyshev I only)
  - `stopbandAtten` - Stopband attenuation in dB (Chebyshev II only)

**Design Method Comparison**:
| Design | Passband | Stopband | Phase | Use Case |
|--------|----------|----------|-------|----------|
| Butterworth | Maximally flat | Monotonic | Moderate | General purpose |
| Chebyshev I | Equiripple | Monotonic | More lag | Sharp cutoff needed |
| Chebyshev II | Flat | Equiripple | Less lag | Passband fidelity |
| Bessel | Flat | Gradual | Linear | Phase-critical signals |

#### Notch Filter
Rejects a specific narrow frequency band. Useful for removing power line interference (50/60 Hz), mechanical resonances, or other narrowband disturbances.
- **Parameters**:
  - `notchFrequency` - Center frequency to reject (Hz)
  - `bandwidth` - Width of the notch (3 dB bandwidth in Hz)
  - `depth` - Notch depth in dB

#### Rate Limiter
Limits the rate of change (slew rate) of a signal.
- **Parameters**:
  - `risingLimit` - Maximum positive rate of change (units/second)
  - `fallingLimit` - Maximum negative rate of change (units/second, typically negative)

Useful for modeling actuator dynamics and preventing unrealistic signal changes.

#### Backlash
Models mechanical backlash (dead band in gear systems).
- **Parameters**:
  - `deadbandWidth` - Total width of the dead band
  - `initialOutput` - Initial output value

---

### Nonlinear

Blocks implementing nonlinear behaviors.

#### Lookup Table 1D
Performs 1D interpolation using tabulated data. Useful for modeling empirical relationships like motor curves, sensor calibrations, and material properties.
- **Parameters**:
  - `xData` - Array of input breakpoints (must be monotonically increasing)
  - `yData` - Array of corresponding output values

Uses linear interpolation between points and extrapolation beyond the table range.

#### Lookup Table 2D
Performs 2D interpolation for surfaces.
- **Parameters**:
  - `xData` - Row breakpoints
  - `yData` - Column breakpoints
  - `zData` - 2D array of output values

#### Quantizer
Discretizes a continuous signal to specified intervals.
- **Parameters**: `interval` - Quantization step size

Output: y = interval · round(u / interval)

#### Relay
Implements a relay (on-off) controller with hysteresis.
- **Parameters**:
  - `switchOn` - Input threshold to turn on
  - `switchOff` - Input threshold to turn off
  - `outputOn` - Output when relay is on
  - `outputOff` - Output when relay is off

#### Coulomb Friction
Models static and dynamic (Coulomb) friction.
- **Parameters**:
  - `staticGain` - Friction coefficient at low velocity
  - `dynamicGain` - Friction coefficient at high velocity
  - `velocityThreshold` - Transition velocity

#### Variable Transport Delay
Delays the input by a variable amount specified by a second input.
- **Parameters**:
  - `maxDelay` - Maximum allowable delay
  - `initialDelay` - Initial delay value

---

### Observers

Blocks for state estimation and filtering.

#### Kalman Filter
Optimal linear state estimator for systems with Gaussian noise.
- **Parameters**:
  - `A` - State transition matrix
  - `B` - Input matrix
  - `C` - Output (measurement) matrix
  - `Q` - Process noise covariance
  - `R` - Measurement noise covariance
  - `initialState` - Initial state estimate
  - `initialP` - Initial error covariance

The Kalman filter provides the minimum variance estimate by optimally balancing model predictions against noisy measurements.

#### Luenberger Observer
Deterministic state observer using pole placement.
- **Parameters**:
  - `A`, `B`, `C` - System matrices
  - `L` - Observer gain matrix
  - `initialState` - Initial state estimate

#### Extended Kalman Filter
Kalman filter for nonlinear systems using local linearization.
- **Parameters**:
  - `nStates` - Number of states
  - `Q`, `R` - Noise covariances
  - `initialState` - Initial state estimate

---

### Subsystems

Blocks for hierarchical model organization.

#### Subsystem
Encapsulates a group of blocks as a reusable component.
- **Parameters**:
  - `numInputs` - Number of input ports
  - `numOutputs` - Number of output ports

#### Inport
Defines an input port within a subsystem.
- **Parameters**: `portNumber` - Port index (1-based)

#### Outport
Defines an output port within a subsystem.
- **Parameters**: `portNumber` - Port index (1-based)

---

## Example Models

LibreSim includes example models in the `examples/` directory demonstrating various capabilities:

| Example | Category | Description |
|---------|----------|-------------|
| Sine Wave Basic | Basic | Simple source + scope |
| First-Order Step Response | Basic | Transfer function response |
| Second-Order Damping | Basic | Damping ratio comparison |
| PID Controller | Control | Closed-loop feedback control |
| Mass-Spring-Damper | Control | Mechanical system dynamics |
| Thermostat Relay | Control | Bang-bang control with hysteresis |
| Moving Average Filter | Signal | AWGN smoothing comparison |
| Low-Pass Filter | Signal | Noise reduction tradeoffs |
| Lookup Table | Signal | Motor torque curve modeling |
| Rate Limiting | Signal | Actuator limitations |
| Kalman Filter | Advanced | State estimation |

See [examples/README.md](examples/README.md) for detailed documentation and Simulink reference links.

---

## Simulink Import

LibreSim supports importing Simulink `.mdl` files:

```python
# Via API
POST /api/models/import
Content-Type: multipart/form-data
file: your_model.mdl
```

Or drag-and-drop an `.mdl` file directly into the editor.

---

## Configuration

### Simulation Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `solver` | `rk4` | ODE solver (euler, rk4, merson) |
| `startTime` | `0.0` | Simulation start time |
| `stopTime` | `10.0` | Simulation stop time |
| `stepSize` | `0.01` | Fixed step size |

### Solver Comparison

| Solver | Order | Accuracy | Speed | Use Case |
|--------|-------|----------|-------|----------|
| Euler | 1st | Low | Fast | Quick prototyping |
| RK4 | 4th | High | Medium | General purpose (default) |
| Merson | 4th | High | Medium | Stiff systems |

---

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Object-oriented Simulation Kernel (OSK) by Mason Nixon
- Inspired by MathWorks Simulink
