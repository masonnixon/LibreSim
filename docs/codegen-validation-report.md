# Codegen Validation Report

This report compares the outputs of generated code against the headless simulation.

## Summary

| Example | Python | C++ | C | Rust |
|---------|--------|-----|---|------|
| 01_sine_wave_basic | PASS | PASS | PASS | PASS |
| 02_first_order_step_response | PASS | PASS | PASS | PASS |
| 03_pid_controller | PASS | PASS | PASS | PASS |
| 04_mass_spring_damper | PASS | PASS | PASS | PASS |
| 04b_mass_spring_damper_underdamped | PASS | PASS | PASS | PASS |
| 05a_moving_average_filter | PASS | PASS | PASS | PASS |
| 05b_lowpass_filter | PASS | PASS | PASS | PASS |
| 06_kalman_filter_estimation | PASS | PASS | PASS | PASS |
| 06b_kalman_position_velocity | PASS | PASS | PASS | PASS |
| 07_thermostat_relay_control | PASS | PASS | PASS | PASS |
| 07a_bode_plot_analysis | PASS | PASS | PASS | PASS |
| 07b_nyquist_plot_analysis | PASS | PASS | PASS | PASS |
| 07c_pole_zero_map | PASS | PASS | PASS | PASS |
| 07d_step_response_info | PASS | PASS | PASS | PASS |
| 08_lookup_table_nonlinear | PASS | PASS | PASS | PASS |
| 09_second_order_damping | PASS | PASS | PASS | PASS |
| 10_rate_limiting_quantization | PASS | PASS | PASS | PASS |
| 11_vector_signal_processing | PASS | PASS | PASS | PASS |
| 20_quaternion_attitude_propagation | PASS | PASS | PASS | PASS |
| 21_isa_atmosphere_model | PASS | PASS | PASS | PASS |
| 22_gravity_models_comparison | PASS | PASS | PASS | PASS |
| 23_dcm_quaternion_conversion | PASS | PASS | PASS | PASS |
| 24_quaternion_vector_rotation | PASS | PASS | PASS | PASS |
| 30_pid_speed_control | DIFF (19.94%) | DIFF (19.94%) | DIFF (19.94%) | DIFF (19.94%) |
| 31_discrete_pid_sampled_control | PASS | PASS | PASS | PASS |
| 32_lqr_state_feedback | PASS | PASS | PASS | PASS |
| 33_lead_lag_compensator | PASS | PASS | PASS | PASS |
| 34_anti_windup_pid | PASS | PASS | PASS | PASS |
| 35_pi_pd_controllers | PASS | PASS | PASS | PASS |
| 36_model_reference_control | PASS | PASS | PASS | PASS |
| 37_pole_placement_control | PASS | PASS | PASS | PASS |
| 40_dsp_fft_spectrum | PASS | PASS | PASS | PASS |
| 41_dsp_fir_lowpass | DIFF (4.22%) | DIFF (6.91%) | DIFF (6.03%) | DIFF (6.03%) |
| 42_rf_receiver_chain | PASS | PASS | PASS | PASS |
| 43_rf_am_modulation | PASS | PASS | PASS | PASS |
| 44_nav_coordinate_transform | PASS | PASS | PASS | PASS |
| 45_sensor_fusion_ahrs | PASS | PASS | PASS | PASS |
| 46_sensor_fusion_tracking | PASS | PASS | PASS | PASS |

## Statistics

- Total tests: 152
- Passed: 144 (94.7%)
- Build failures: 0
- Run failures: 0
- Value mismatches: 8

## Detailed Failures

### 30_pid_speed_control (python)

- Max relative error: 19.9362%
- Headless final values: {'Speed Setpoint': 100.0, 'DC Motor': 99.92466899212954, 'Actuator Limits': 19.990832132866167, 'Error': 0.0753310078704601}
- Codegen final values: {'Speed_Setpoint': 100.0, 'DC_Motor': 99.90965082892927, 'Control_Signal': 20.00107666518958, 'Error': 0.09034917107072715}

### 30_pid_speed_control (cpp)

- Max relative error: 19.9363%
- Headless final values: {'Speed Setpoint': 100.0, 'DC Motor': 99.92466899212954, 'Actuator Limits': 19.990832132866167, 'Error': 0.0753310078704601}
- Codegen final values: {'Speed_Setpoint': 100.0, 'DC_Motor': 99.9097, 'Control_Signal': 20.0011, 'Error': 0.0903492}

### 30_pid_speed_control (c)

- Max relative error: 19.9363%
- Headless final values: {'Speed Setpoint': 100.0, 'DC Motor': 99.92466899212954, 'Actuator Limits': 19.990832132866167, 'Error': 0.0753310078704601}
- Codegen final values: {'Speed_Setpoint': 100.0, 'DC_Motor': 99.9097, 'Control_Signal': 20.0011, 'Error': 0.0903492}

### 30_pid_speed_control (rust)

- Max relative error: 19.9360%
- Headless final values: {'Speed Setpoint': 100.0, 'DC Motor': 99.92466899212954, 'Actuator Limits': 19.990832132866167, 'Error': 0.0753310078704601}
- Codegen final values: {'Speed_Setpoint': 100.0, 'DC_Motor': 99.909651, 'Control_Signal': 20.001077, 'Error': 0.090349}

### 41_dsp_fir_lowpass (python)

- Max relative error: 4.2181%
- Headless final values: {'Add Noise': -0.4467366615970011, 'FIR Lowpass': -0.7151751744479324, 'Running Mean': -0.40412918169231327, 'RMS': 0.3802658731043606}
- Codegen final values: {'Add_Noise': -0.4467366615970011, 'FIR_Lowpass': -0.6197753140536535, 'Running_Mean': -0.3757196107581854, 'RMS': 0.36422570189805753}

### 41_dsp_fir_lowpass (cpp)

- Max relative error: 6.9136%
- Headless final values: {'Add Noise': -0.4467366615970011, 'FIR Lowpass': -0.7151751744479324, 'Running Mean': -0.40412918169231327, 'RMS': 0.3802658731043606}
- Codegen final values: {'Add_Noise': 0.237651, 'FIR_Lowpass': -0.0257466, 'Running_Mean': 0.152284, 'RMS': 0.406556}

### 41_dsp_fir_lowpass (c)

- Max relative error: 6.0250%
- Headless final values: {'Add Noise': -0.4467366615970011, 'FIR Lowpass': -0.7151751744479324, 'Running Mean': -0.40412918169231327, 'RMS': 0.3802658731043606}
- Codegen final values: {'Add_Noise': -0.370298, 'FIR_Lowpass': -0.0954109, 'Running_Mean': -0.200119, 'RMS': 0.403177}

### 41_dsp_fir_lowpass (rust)

- Max relative error: 6.0250%
- Headless final values: {'Add Noise': -0.4467366615970011, 'FIR Lowpass': -0.7151751744479324, 'Running Mean': -0.40412918169231327, 'RMS': 0.3802658731043606}
- Codegen final values: {'Add_Noise': -0.370298, 'FIR_Lowpass': -0.095411, 'Running_Mean': -0.200119, 'RMS': 0.403177}
