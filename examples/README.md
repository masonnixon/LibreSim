# LibreSim Example Models

This directory contains example models demonstrating LibreSim's simulation capabilities. These examples are inspired by classic Simulink tutorials and control systems textbooks.

## Basic Examples (Core Blocks)

### 01. Sine Wave Basic
**File:** `01_sine_wave_basic.json`

The simplest possible model - a sine wave source connected to a scope. Perfect for verifying your LibreSim installation is working.

### 02. First-Order System Step Response
**File:** `02_first_order_step_response.json`

Step response of a first-order system (like an RC circuit). Transfer function: H(s) = 1/(s+1) with time constant τ = 1 second. Shows how a first-order system reaches 63.2% of its final value at t = τ.

### 03. PID Controller
**File:** `03_pid_controller.json`

Classic closed-loop PID control of a second-order plant. Demonstrates:
- Feedback control loop structure
- Error computation (reference - output)
- PID controller tuning (Kp=10, Ki=5, Kd=2)
- Plant: G(s) = 1/(s² + 2s + 1)

### 04. Mass-Spring-Damper System
**File:** `04_mass_spring_damper.json`

Models a mechanical system using Newton's second law: m·x'' + c·x' + k·x = F

Parameters: m=1kg, c=0.5 N·s/m, k=2 N/m

Demonstrates using integrators to build physical system models from differential equations.

### 09. Second-Order System Damping Comparison
**File:** `09_second_order_damping.json`

Compares second-order systems with different damping ratios (ωn = 1 rad/s):
- **Underdamped** (ζ=0.2): Oscillatory response with overshoot
- **Critically damped** (ζ=1.0): Fastest response without overshoot
- **Overdamped** (ζ=2.0): Slow, no-overshoot response

---

## Signal Processing Examples (New Blocks)

### 05. Signal Filtering Comparison
**File:** `05_signal_filtering.json`

Demonstrates signal processing blocks by filtering a composite signal (1Hz + 10Hz):
- Low-pass filter (2Hz cutoff)
- Moving average filter

Shows how different filtering approaches attenuate high-frequency components.

### 10. Rate Limiting and Quantization Effects
**File:** `10_rate_limiting_quantization.json`

Models actuator limitations commonly seen in real systems:
- **Rate limiter:** Limits slew rate (how fast signal can change)
- **Quantizer:** Models discrete resolution (like DAC outputs)

Useful for understanding servo systems and digital-to-analog converter effects.

---

## Nonlinear Systems Examples (New Blocks)

### 07. Thermostat Relay Control (Bang-Bang)
**File:** `07_thermostat_relay_control.json`

Classic on-off (bang-bang) controller using a relay with hysteresis:
- Relay turns heater ON when temperature drops below 18°C
- Relay turns heater OFF when temperature rises above 22°C
- Models room thermal dynamics with an integrator

Demonstrates hysteresis behavior and limit cycling in nonlinear control.

### 08. Lookup Table Nonlinearity
**File:** `08_lookup_table_nonlinear.json`

Compares lookup table (soft saturation) vs hard saturation:
- Lookup table with smooth tanh-like characteristic
- Standard saturation block with sharp cutoff

Common in engine control, sensor calibration, and actuator modeling.

---

## State Estimation Examples (New Blocks)

### 06. Kalman Filter State Estimation
**File:** `06_kalman_filter_estimation.json`

Demonstrates Kalman filter for state estimation:
- True state: Ramp signal with constant velocity
- Kalman filter estimates position from measurements
- Compare estimate vs true signal

Shows optimal state estimation principles from control theory.

---

## Loading Examples

### In LibreSim Web Interface
1. Click "File" → "Open"
2. Navigate to the examples folder
3. Select the desired `.json` file

### Programmatically (API)
```python
import json
import requests

with open('examples/03_pid_controller.json') as f:
    model = json.load(f)

response = requests.post(
    'http://localhost:8000/api/models',
    json=model
)
```

---

## Comparison with Simulink

| LibreSim Example | Similar Simulink Tutorial |
|-----------------|---------------------------|
| First-Order Step Response | Getting Started with Simulink |
| PID Controller | Tuning PID Controller |
| Mass-Spring-Damper | Modeling Physical Systems |
| Second-Order Damping | Introduction to Control Design |
| Thermostat Control | Bang-Bang Control |

---

## Creating Your Own Examples

1. Build your model in the LibreSim editor
2. Click "File" → "Save As"
3. Save as JSON to the examples folder
4. Add documentation to this README

Model JSON structure:
```json
{
  "id": "unique-model-id",
  "metadata": {
    "name": "Model Name",
    "description": "Description of what the model demonstrates"
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
