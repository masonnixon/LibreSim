# LibreSim Example Models

This directory contains example models demonstrating LibreSim's simulation capabilities. Each example includes a reference URL to corresponding MathWorks/Simulink documentation for validation comparison.

## Basic Examples

### 01. Sine Wave Basic
**File:** `01_sine_wave_basic.json` | `01_sine_wave_basic.mdl`

The simplest possible model - a sine wave source connected to a scope. Perfect for verifying your LibreSim installation is working.

**Expected Output:**
- Amplitude: 1
- Frequency: 1 Hz (2π rad/s)
- Period: 1 second
- Range: -1 to +1

**Reference:** https://www.mathworks.com/help/simulink/slref/sinewave.html

---

### 02. First-Order System Step Response
**File:** `02_first_order_step_response.json` | `02_first_order_step_response.mdl`

Step response of a first-order system (like an RC circuit). Transfer function: H(s) = 1/(s+1) with time constant τ = 1 second. Shows how a first-order system reaches 63.2% of its final value at t = τ.

**Expected Output:**
- At t=1s: output ≈ 0.632 (63.2% of final value)
- At t=3s: output ≈ 0.95 (95% - within 5%)
- At t=5s: output ≈ 0.993 (essentially at steady-state)
- Final value: 1.0

**Reference:** https://www.mathworks.com/help/simulink/slref/transferfcn.html

---

### 09. Second-Order System Damping Comparison
**File:** `09_second_order_damping.json` | `09_second_order_damping.mdl`

Compares second-order systems with different damping ratios (ωn = 1 rad/s):
- **Underdamped** (ζ=0.25): Oscillatory response with overshoot
- **Critically damped** (ζ=1.0): Fastest response without overshoot
- **Overdamped** (ζ=2.0): Slow, no-overshoot response

**Expected Output:**
- Underdamped: ~44% overshoot, oscillates before settling, settles in ~12s
- Critical: No overshoot, fastest settling to 1.0, settles in ~6s
- Overdamped: No overshoot, slowest response, settles in ~10s

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

**Expected Output:**
- Rise time: ~0.3s (fast due to high Kp)
- Overshoot: ~15-20% (derivative action limits overshoot)
- Settling time: ~1.5s (integral action eliminates steady-state error)
- Final value: 1.0 (zero steady-state error)

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

**Expected Output:**
- Position: Monotonic rise from 0 to 1m (no oscillation)
- Velocity: Rises then falls smoothly to 0
- Settling time: ~0.15s (fast due to stiff spring)
- Final position: 1m (F/k = 1000/1000)

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

**Expected Output:**
- Position: Oscillates around 1m with decaying amplitude
- Overshoot: ~73% (reaches ~1.73m peak)
- Period: ~0.63s (ωd ≈ 9.95 rad/s)
- Settling time: ~4s (to within 2% of final)

**Reference:** https://www.mathworks.com/help/simscape/ug/mass-spring-damper-in-simulink-and-simscape.html

---

### 07. Thermostat Relay Control (Bang-Bang)
**File:** `07_thermostat_relay_control.json`

Classic on-off (bang-bang) controller using a relay with hysteresis:
- Relay turns heater ON when temperature drops below 18°C
- Relay turns heater OFF when temperature rises above 22°C
- Models room thermal dynamics with an integrator

Demonstrates hysteresis behavior and limit cycling in nonlinear control.

**Expected Output:**
- Temperature: Oscillates between 18°C and 22°C (limit cycle)
- Heater output: Switches between 0 (off) and 5 (on)
- Cycle period: Depends on thermal mass and heat loss
- Steady-state: Sustained oscillation (no settling to setpoint)

**Reference:** https://www.mathworks.com/help/simulink/ug/model-a-house-heating-system.html

---

## Control Analysis Examples

### 07a. Bode Plot - Frequency Response Analysis
**File:** `07a_bode_plot_analysis.json`

Demonstrates Bode plot analysis for a second-order low-pass system:
- **Transfer function:** H(s) = 1/(s² + 0.5s + 1)
- **Natural frequency:** ωn = 1 rad/s
- **Damping ratio:** ζ = 0.25 (underdamped)

**Expected Output:**
- DC gain = 1 (0 dB)
- Resonant peak near ω = 1 rad/s due to low damping
- Phase starts at 0° and drops to -180° at high frequencies
- -40 dB/decade rolloff above the natural frequency

**Reference:** https://www.mathworks.com/help/control/ref/lti.bode.html

---

### 07b. Nyquist Plot - Stability Analysis
**File:** `07b_nyquist_plot_analysis.json`

Demonstrates Nyquist diagram for stability analysis of an open-loop transfer function:
- **Transfer function:** G(s) = 10/(s(s+1)(s+2)) = 10/(s³ + 3s² + 2s)
- Type 1 system (one pole at origin)

**Expected Output:**
- Nyquist curve starts from -∞ on the imaginary axis (due to pole at origin)
- Encirclements of -1 point determine closed-loop stability
- For this system: 0 clockwise encirclements → closed-loop stable

**Reference:** https://www.mathworks.com/help/control/ref/lti.nyquist.html

---

### 07c. Pole-Zero Map - System Stability
**File:** `07c_pole_zero_map.json`

Demonstrates pole-zero mapping for stability analysis with three systems:

| System | Denominator | Poles | Stability |
|--------|-------------|-------|-----------|
| Stable | s² + 2s + 5 | -1 ± 2j | Stable (LHP) |
| Marginal | s² + 1 | ±j | Marginally stable (imaginary axis) |
| Unstable | s² - s - 2 | +2, -1 | Unstable (RHP pole at +2) |

**Expected Output:**
- Stable system: isStable = 1
- Marginally stable: isStable = 0 (poles on imaginary axis)
- Unstable system: isStable = 0 (pole in right-half plane)

**Reference:** https://www.mathworks.com/help/control/ref/lti.pzmap.html

---

### 07d. Step Response Info - Time Domain Analysis
**File:** `07d_step_response_info.json`

Compares step response characteristics of second-order systems with different damping:

| System | Denominator | ζ | Expected Settling Time (2%) |
|--------|-------------|---|----------------------------|
| Overdamped | s² + 4s + 1 | 2.0 | ~8-10 seconds |
| Critical | s² + 2s + 1 | 1.0 | ~5-6 seconds |
| Underdamped | s² + 0.6s + 1 | 0.3 | ~10-12 seconds (with oscillation) |

**Expected Output:**
- Overdamped: Slow, monotonic rise, no overshoot
- Critical: Fastest response without overshoot
- Underdamped: Oscillatory response with ~35% overshoot (for ζ=0.3)

**Reference:** https://www.mathworks.com/help/control/ref/lti.stepinfo.html

---

## Signal Processing Examples

### 05a. Moving Average Filter - AWGN Smoothing
**File:** `05a_moving_average_filter.json`

Demonstrates Moving Average filter smoothing a step signal corrupted by Additive White Gaussian Noise (AWGN). Compares different window sizes (5, 10, 20 samples) to show the tradeoff between:
- **Smoothing quality** (larger window = smoother output)
- **Response time** (larger window = more delay)

Uses the White Noise block for realistic random noise.

**Expected Output:**
- Noisy signal: Step with ±0.1 variance noise
- MAF-5: Faster response, more residual noise
- MAF-10: Moderate smoothing, moderate delay
- MAF-20: Smoothest output, most delay (~10ms at 0.001s step)

**Reference:** https://www.mathworks.com/help/dsp/ref/movingaverage.html

---

### 05b. Low-Pass Filter Comparison
**File:** `05b_lowpass_filter.json`

Compares 1st-order LPF with higher-order Butterworth and Bessel filters, all at 3 Hz cutoff:
- **1st Order LPF**: Simple RC-equivalent filter
- **Butterworth 1st**: Same as above (should match LPF output)
- **Butterworth 2nd**: Sharper rolloff, more phase lag
- **Butterworth 4th**: Even sharper rolloff, significant phase lag
- **Bessel 2nd**: Maximally flat group delay (less phase distortion)

Key observations:
- Higher order = better noise rejection but more phase lag
- Bessel preserves waveform shape better than Butterworth at same order
- 1st-order LPF and Butterworth 1st should produce identical results

Uses White Noise block for realistic AWGN.

**Expected Output:**
- Clean signal: 1 Hz sine wave, amplitude 1
- Noisy: Same sine with ±0.2 variance noise
- LPF 1st / Butter 1st: Identical outputs, minimal phase lag
- Butter 2nd: Better noise rejection, ~30° phase lag at 1 Hz
- Butter 4th: Best noise rejection, ~60° phase lag at 1 Hz
- Bessel 2nd: Similar to Butter 2nd, better transient response

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

**Expected Output:**
- Speed: Linear ramp 0→2000 RPM over 20s
- Torque: Drops from 10 N·m (stall) to 1 N·m (max speed)
- Efficiency: Peaks at ~92% around 1000 RPM
- Power: Rises, peaks around 1000 RPM, then falls

**Reference:** https://www.mathworks.com/help/simulink/slref/1dlookuptable.html

---

### 10. Rate Limiting and Quantization Effects
**File:** `10_rate_limiting_quantization.json`

Models actuator limitations commonly seen in real systems:
- **Rate limiter:** Limits slew rate (how fast signal can change)
- **Quantizer:** Models discrete resolution (like DAC outputs)

Useful for understanding servo systems and digital-to-analog converter effects.

**Expected Output:**
- Input: 5V amplitude, 2 Hz sine wave
- Rate limited: Clipped slopes (triangular shape at high frequencies)
- Quantized: Staircase output with 0.5V steps
- Rate + Quantized: Combined effects visible

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

**Expected Output:**
- True signal: Linear ramp from 0 to 5 over 10s
- Kalman estimate: Tracks the ramp with small delay
- Estimation error: Decreases over time as filter converges
- Initial transient: Estimate starts at 0, converges within ~1s

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

**Expected Output:**
- True position: Linear ramp from 0 to 10 over 10s
- Noisy measurement: Position with ±0.5 variance noise
- Position estimate: Smoothed, tracks true position closely
- Velocity estimate: Converges to 1.0 (true velocity)
- Key insight: Velocity is never measured, only estimated!

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

| # | Name | Category | Key Concept | Expected Output |
|---|------|----------|-------------|-----------------|
| 01 | Sine Wave Basic | Basic | Source + Scope | Sine wave with A=1, f=1 Hz |
| 02 | First-Order Step Response | Basic | Transfer function | 63.2% at t=1s, steady-state=1 |
| 03 | PID Controller | Control | Feedback control | Fast rise, minimal overshoot |
| 04 | Mass-Spring-Damper (Simscape) | Control | Overdamped mechanical system | Monotonic rise to 1m position |
| 04b | Mass-Spring-Damper (Underdamped) | Control | Oscillatory mechanical system | Oscillating position, decaying |
| 05a | Moving Average Filter | Signal | AWGN smoothing | Smoothed step, larger window = smoother |
| 05b | Low-Pass Filter Comparison | Signal | Filter order/design comparison | Higher order = sharper rolloff |
| 06 | Kalman Filter | Advanced | State estimation | Estimate tracks ramp signal |
| 06b | Kalman Position/Velocity | Advanced | Hidden state estimation | Velocity estimate converges to 1 |
| 07 | Thermostat Relay | Control | Bang-bang control | Temperature oscillates 18-22°C |
| 07a | Bode Plot Analysis | Control Analysis | Frequency response | DC gain=1, resonant peak at ωn |
| 07b | Nyquist Plot Analysis | Control Analysis | Stability via encirclements | 0 encirclements → stable |
| 07c | Pole-Zero Map | Control Analysis | Stability via pole locations | Stable=1, Marginal=0, Unstable=0 |
| 07d | Step Response Info | Control Analysis | Time-domain metrics | Settling times: ~8s, ~5s, ~10s |
| 08 | Lookup Table - Motor Curve | Signal | Empirical data modeling | Torque drops, efficiency peaks mid-range |
| 09 | Second-Order Damping | Basic | Damping ratio comparison | Under: oscillates, Critical: fastest, Over: slow |
| 10 | Rate Limiting | Signal | Actuator limitations | Slew-limited + quantized output |
| 20 | Quaternion Attitude | Aerospace | Quaternion propagation | Euler angles from angular rates |
| 21 | ISA Atmosphere | Aerospace | Air properties vs altitude | T, P, ρ, a vs altitude |
| 22 | Gravity Models | Aerospace | WGS84 vs Flat Earth | Gravity variation with latitude |
| 23 | DCM-Quaternion | Aerospace | Rotation representations | Round-trip conversion verification |
| 24 | Vector Rotation | Aerospace | Quaternion rotation | Circular motion of rotated vector |
| 30 | PID Speed Control | Control Design | Motor speed regulation | Fast response, zero SS error |
| 31 | Discrete PID | Control Design | Sampled-data control | Staircase control signal |
| 32 | LQR State Feedback | Control Design | Optimal control | States converge to zero |
| 33 | Lead-Lag Compensator | Control Design | Classical compensation | Faster response with lead |
| 34 | Anti-Windup PID | Control Design | Saturation handling | Smooth recovery vs windup |
| 35 | PI vs PD | Control Design | Controller comparison | Trade-off: accuracy vs speed |
| 36 | Model Reference | Control Design | Adaptive control | Plant tracks reference model |
| 37 | Pole Placement | Control Design | State feedback design | Disturbance rejection |

---

## Aerospace Blockset Examples

### 20. Quaternion Attitude Propagation
**File:** `20_quaternion_attitude_propagation.json`

Demonstrates aerospace quaternion blocks for attitude representation. Propagates attitude using angular velocity, normalizes quaternions, and converts to Euler angles for visualization.

**Blocks Used:**
- Quaternion Normalize
- Quaternion to Euler
- Mux (for building quaternion/omega vectors)
- Integrators (for quaternion kinematics)

**Expected Output:**
- Quaternion components evolve based on angular rates
- Euler angles show attitude in degrees
- Quaternion remains normalized (|q| = 1)

**Reference:** https://www.mathworks.com/help/aeroblks/quaternions.html

---

### 21. ISA Standard Atmosphere
**File:** `21_isa_atmosphere_model.json`

Demonstrates the ISA Atmosphere block computing air properties as a function of altitude:
- Temperature (K)
- Speed of Sound (m/s)
- Pressure (Pa)
- Density (kg/m³)

**Expected Output:**
- At sea level: T=288.15K, a=340.3m/s, P=101325Pa, ρ=1.225kg/m³
- Properties decrease with altitude per ISA model
- Valid up to 11km (troposphere)

**Reference:** https://www.mathworks.com/help/aeroblks/isaatmospheremodel.html

---

### 22. Gravity Models Comparison
**File:** `22_gravity_models_comparison.json`

Compares Flat Earth (constant g) vs WGS84 (latitude/altitude-dependent) gravity models:
- Sweeps latitude from 0° to 90°
- Shows gravity variation with latitude
- Highlights importance of high-fidelity models for aerospace

**Expected Output:**
- Flat Earth: Constant 9.80665 m/s²
- WGS84: Varies from ~9.78 (equator) to ~9.83 (pole)
- Difference: Up to 0.05 m/s² between models

**Reference:** https://www.mathworks.com/help/aeroblks/wgs84gravitymodel.html

---

### 23. DCM-Quaternion Conversion
**File:** `23_dcm_quaternion_conversion.json`

Demonstrates conversion between Direction Cosine Matrix (DCM) and Quaternion:
- Euler → Quaternion → DCM → Quaternion → Euler round-trip
- Verifies conversion consistency (error should be ~0)

**Blocks Used:**
- Euler to Quaternion
- Quaternion to DCM
- DCM to Quaternion
- Quaternion to Euler

**Expected Output:**
- Input and output Euler angles match exactly
- Conversion error: ~0 (machine precision)

**Reference:** https://www.mathworks.com/help/aeroblks/directioncosinematrixtoquaternion.html

---

### 24. Quaternion Vector Rotation
**File:** `24_quaternion_vector_rotation.json`

Rotates a 3D vector using quaternion rotation (v' = qvq*):
- Unit vector [1,0,0] rotated about z-axis
- Shows circular motion of vector tip in XY plane

**Blocks Used:**
- Quaternion Normalize
- Quaternion Rotate Vector
- Trigonometry (sin/cos for quaternion from angle)

**Expected Output:**
- Rotated vector traces a circle
- X component: cos(θ)
- Y component: sin(θ)
- Z component: 0

**Reference:** https://www.mathworks.com/help/aeroblks/rotatevectorsbyquaternion.html

---

## Control Design Examples

### 30. PID Motor Speed Control
**File:** `30_pid_speed_control.json`

Classic PID controller for DC motor speed regulation:
- Step setpoint to 100 RPM
- First-order motor model G(s) = 10/(s+2)
- Actuator saturation limits

**Expected Output:**
- Fast rise time with minimal overshoot
- Zero steady-state error
- Control signal within saturation limits

**Reference:** https://www.mathworks.com/help/control/ug/designing-pid-controllers.html

---

### 31. Discrete PID Sampled Control
**File:** `31_discrete_pid_sampled_control.json`

Demonstrates Discrete PID Controller for digital control systems:
- Zero-Order Hold for sampling
- Trapezoidal (Tustin) discretization
- Sample time = 0.1s

**Expected Output:**
- Staircase control signal (sampled)
- Good tracking despite discretization
- Compare with continuous response

**Reference:** https://www.mathworks.com/help/control/ug/discrete-time-pid-controller-design.html

---

### 32. LQR State Feedback Control
**File:** `32_lqr_state_feedback.json`

Linear Quadratic Regulator (LQR) optimal control:
- Double integrator plant (position-velocity)
- Full state feedback u = -Kx
- Optimal gains K = [1, 1.732]

**Expected Output:**
- States converge to zero from initial conditions
- Smooth, optimal control trajectory
- No overshoot with proper tuning

**Reference:** https://www.mathworks.com/help/control/ug/lqg-regulation.html

---

### 33. Lead-Lag Compensator Design
**File:** `33_lead_lag_compensator.json`

Classical lead compensator for improved transient response:
- Lead compensator: K(s+z)/(s+p) with z < p
- Compares compensated vs uncompensated response
- Phase lead for faster response

**Expected Output:**
- Compensated: Faster rise time, reduced overshoot
- Uncompensated: Slower, more oscillatory
- Lead provides phase margin improvement

**Reference:** https://www.mathworks.com/help/control/ug/lead-and-lag-compensator-design.html

---

### 34. Anti-Windup PID Controller
**File:** `34_anti_windup_pid.json`

PID with back-calculation anti-windup:
- Compares anti-windup vs standard PID during saturation
- Large setpoint causes actuator saturation
- Back-calculation prevents integrator windup

**Expected Output:**
- Anti-windup PID: Smooth recovery from saturation
- Standard PID: Prolonged overshoot (windup)
- Demonstrates importance for real actuators

**Reference:** https://www.mathworks.com/help/simulink/slref/pidcontroller.html#bsu1cxn-1

---

### 35. PI and PD Controller Comparison
**File:** `35_pi_pd_controllers.json`

Compares PI vs PD controller characteristics:
- PI: Zero steady-state error, slower response
- PD: Fast response, has steady-state error
- Same plant for fair comparison

**Expected Output:**
- PI: Eventually reaches setpoint (no error)
- PD: Fast but settles below setpoint
- Trade-off between speed and accuracy

**Reference:** https://www.mathworks.com/help/control/ug/pid-controller-types.html

---

### 36. Model Reference Control
**File:** `36_model_reference_control.json`

Model Reference Adaptive Control (MRAC) structure:
- Reference model defines desired behavior
- Controller aims to match plant output to reference
- Foundation for adaptive control

**Blocks Used:**
- Model Reference block
- PID for tracking controller

**Expected Output:**
- Plant output tracks reference model
- Tracking error converges to zero
- Reference model shapes closed-loop response

**Reference:** https://www.mathworks.com/help/control/ug/model-reference-adaptive-control.html

---

### 37. Pole Placement State Feedback
**File:** `37_pole_placement_control.json`

State feedback via pole placement:
- Places closed-loop poles at desired locations
- Double integrator with disturbance rejection
- Demonstrates state feedback structure

**Expected Output:**
- States return to zero after disturbance
- Transient determined by pole locations
- Faster poles = faster response

**Reference:** https://www.mathworks.com/help/control/ref/place.html

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
