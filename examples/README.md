# LibreSim Example Models

This directory contains example models demonstrating LibreSim's simulation capabilities. Each example includes a reference URL to corresponding MathWorks/Simulink documentation for validation comparison.

## Basic Examples

### 01. Sine Wave Basic
**File:** `01_sine_wave_basic.json` | `01_sine_wave_basic.mdl`

The simplest possible model - a sine wave source connected to a scope. Perfect for verifying your LibreSim installation is working.

**Reference:** https://www.mathworks.com/help/simulink/slref/sinewave.html

---

### 02. First-Order System Step Response
**File:** `02_first_order_step_response.json` | `02_first_order_step_response.mdl`

Step response of a first-order system (like an RC circuit). Transfer function: H(s) = 1/(s+1) with time constant τ = 1 second. Shows how a first-order system reaches 63.2% of its final value at t = τ.

**Reference:** https://www.mathworks.com/help/simulink/slref/transferfcn.html

---

### 09. Second-Order System Damping Comparison
**File:** `09_second_order_damping.json` | `09_second_order_damping.mdl`

Compares second-order systems with different damping ratios (ωn = 1 rad/s):
- **Underdamped** (ζ=0.25): Oscillatory response with overshoot
- **Critically damped** (ζ=1.0): Fastest response without overshoot
- **Overdamped** (ζ=2.0): Slow, no-overshoot response

**Reference:** https://ctms.engin.umich.edu/CTMS/index.php?example=Introduction&section=SystemAnalysis

---

## Control Systems Examples

### 03. PID Controller
**File:** `03_pid_controller.json` | `03_pid_controller.mdl`

Classic closed-loop PID control of a second-order plant. Demonstrates:
- Feedback control loop structure
- Error computation (reference - output)
- PID controller tuning (Kp=10, Ki=5, Kd=2)
- Plant: G(s) = 1/(s² + 2s + 1)

**Reference:** https://www.mathworks.com/help/simulink/slref/pidcontroller.html

---

### 04. Mass-Spring-Damper System (Simscape Defaults)
**File:** `04_mass_spring_damper.json` | `04_mass_spring_damper.mdl`

Models a mechanical system using Newton's second law: m·x'' + c·x' + k·x = F

Uses **Simscape default parameters** for validation:
- Mass: m = 1 kg
- Damping: c = 100 N·s/m
- Spring: k = 1000 N/m
- Creates an **overdamped** system (ζ ≈ 1.58)

**Reference:** https://www.mathworks.com/help/simscape/ug/mass-spring-damper-in-simulink-and-simscape.html

---

### 04b. Mass-Spring-Damper System (Underdamped)
**File:** `04b_mass_spring_damper_underdamped.json`

Same mechanical system with parameters chosen for visible oscillation:
- Mass: m = 1 kg
- Damping: c = 2 N·s/m
- Spring: k = 100 N/m
- Creates an **underdamped** system (ζ = 0.1, ωn = 10 rad/s)

Useful for teaching oscillatory behavior and transient response.

**Reference:** https://www.mathworks.com/help/simscape/ug/mass-spring-damper-in-simulink-and-simscape.html

---

### 07. Thermostat Relay Control (Bang-Bang)
**File:** `07_thermostat_relay_control.json`

Classic on-off (bang-bang) controller using a relay with hysteresis:
- Relay turns heater ON when temperature drops below 18°C
- Relay turns heater OFF when temperature rises above 22°C
- Models room thermal dynamics with an integrator

Demonstrates hysteresis behavior and limit cycling in nonlinear control.

**Reference:** https://www.mathworks.com/help/simulink/ug/model-a-house-heating-system.html

---

## Signal Processing Examples

### 05a. Moving Average Filter - AWGN Smoothing
**File:** `05a_moving_average_filter.json`

Demonstrates Moving Average filter smoothing a step signal corrupted by Additive White Gaussian Noise (AWGN). Compares different window sizes (5, 10, 20 samples) to show the tradeoff between:
- **Smoothing quality** (larger window = smoother output)
- **Response time** (larger window = more delay)

Uses the White Noise block for realistic random noise.

**Reference:** https://www.mathworks.com/help/dsp/ref/movingaverage.html

---

### 05b. Low-Pass Filter - AWGN Noise Reduction
**File:** `05b_lowpass_filter.json`

Demonstrates Low-Pass filter removing high-frequency AWGN from a clean 1 Hz sine wave signal. Compares different cutoff frequencies (1, 3, 10 Hz) to show:
- How cutoff frequency affects noise attenuation
- Trade-off between noise reduction and signal preservation
- Lower cutoff = more noise removal but potential signal distortion

Uses the White Noise block for realistic random noise.

**Reference:** https://www.mathworks.com/help/dsp/ref/lowpassfilter.html

---

### 08. Lookup Table - Motor Torque Curve
**File:** `08_lookup_table_nonlinear.json`

Demonstrates 1D lookup table modeling a DC motor torque-speed characteristic:
- **Torque vs Speed:** Shows typical motor torque dropoff at high speeds
- **Efficiency vs Speed:** Shows peak efficiency in mid-speed range
- **Power output:** Computed as Torque × Efficiency

Each signal is displayed on a separate scope for proper scaling.
Common in motor control, engine calibration, and sensor linearization.

**Reference:** https://www.mathworks.com/help/simulink/slref/1dlookuptable.html

---

### 10. Rate Limiting and Quantization Effects
**File:** `10_rate_limiting_quantization.json`

Models actuator limitations commonly seen in real systems:
- **Rate limiter:** Limits slew rate (how fast signal can change)
- **Quantizer:** Models discrete resolution (like DAC outputs)

Useful for understanding servo systems and digital-to-analog converter effects.

**Reference:** https://www.mathworks.com/help/simulink/slref/ratelimiter.html and https://www.mathworks.com/help/simulink/slref/quantizer.html

---

## Advanced Examples

### 06. Kalman Filter State Estimation
**File:** `06_kalman_filter_estimation.json`

Demonstrates Kalman filter for state estimation:
- True state: Ramp signal with constant velocity
- Kalman filter estimates position from noisy measurements
- Compare estimate vs true signal

Shows optimal state estimation principles from control theory.

**Reference:** https://www.mathworks.com/help/control/ug/kalman-filtering.html

---

### 06b. Kalman Filter - Position/Velocity Tracking
**File:** `06b_kalman_position_velocity.json`

Classic 2-state Kalman filter demonstrating estimation of hidden states:
- **State vector:** [position, velocity]
- **Measurement:** Position only (corrupted by AWGN sensor noise)
- **Key insight:** Estimates velocity without directly measuring it

System model (constant velocity):
```
x[k+1] = [1  dt] x[k]     (dt = 0.01)
         [0   1]

y[k] = [1  0] x[k] + noise
```

The filter optimally fuses noisy position measurements to estimate both position and velocity, demonstrating the power of model-based estimation.

**Reference:** https://www.mathworks.com/help/control/ug/kalman-filtering.html

---

## Noise Source Blocks

LibreSim includes noise source blocks for realistic signal modeling:

### White Noise (AWGN)
Additive White Gaussian Noise source with configurable:
- Mean and variance
- Optional seed for reproducibility
- Sample time for discrete noise

### Uniform Noise
Uniform random noise between configurable min/max bounds.

---

## File Formats

### JSON Format (LibreSim native)
- Primary format for LibreSim
- Loaded directly in the web interface
- Contains full model definition with blocks, connections, and simulation config

### MDL Format (Simulink-compatible)
- Available for some examples
- Can be imported into MATLAB/Simulink for comparison
- Useful for validating LibreSim results against Simulink

---

## Loading Examples

### In LibreSim Web Interface
1. Click "File" → "Examples"
2. Select the desired example from the categorized list
3. Examples are organized by: Basic, Control Systems, Signal Processing, Advanced

### From Files
1. Click "File" → "Open"
2. Navigate to the examples folder
3. Select the desired `.json` file

---

## Example Summary Table

| # | Name | Category | Key Concept |
|---|------|----------|-------------|
| 01 | Sine Wave Basic | Basic | Source + Scope |
| 02 | First-Order Step Response | Basic | Transfer function |
| 03 | PID Controller | Control | Feedback control |
| 04 | Mass-Spring-Damper (Simscape) | Control | Overdamped mechanical system |
| 04b | Mass-Spring-Damper (Underdamped) | Control | Oscillatory mechanical system |
| 05a | Moving Average Filter | Signal | AWGN smoothing |
| 05b | Low-Pass Filter | Signal | AWGN noise reduction |
| 06 | Kalman Filter | Advanced | State estimation |
| 06b | Kalman Position/Velocity | Advanced | Hidden state estimation |
| 07 | Thermostat Relay | Control | Bang-bang control |
| 08 | Lookup Table - Motor Curve | Signal | Empirical data modeling |
| 09 | Second-Order Damping | Basic | Damping ratio comparison |
| 10 | Rate Limiting | Signal | Actuator limitations |

---

## Creating Your Own Examples

1. Build your model in the LibreSim editor
2. Click "File" → "Export JSON"
3. Save to the examples folder
4. Add documentation to this README

Model JSON structure:
```json
{
  "id": "unique-model-id",
  "metadata": {
    "name": "Model Name",
    "description": "Description with Reference: https://..."
  },
  "blocks": [...],
  "connections": [...],
  "simulationConfig": {
    "solver": "rk4",
    "startTime": 0,
    "stopTime": 10,
    "stepSize": 0.01
  }
}
```
