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
| 07a_bode_plot_analysis | MISSING OR EMPTY OUTPUT SET | MISSING OR EMPTY OUTPUT SET | MISSING OR EMPTY OUTPUT SET | MISSING OR EMPTY OUTPUT SET |
| 07b_nyquist_plot_analysis | MISSING OR EMPTY OUTPUT SET | MISSING OR EMPTY OUTPUT SET | MISSING OR EMPTY OUTPUT SET | MISSING OR EMPTY OUTPUT SET |
| 07c_pole_zero_map | MISSING OR EMPTY OUTPUT SET | MISSING OR EMPTY OUTPUT SET | MISSING OR EMPTY OUTPUT SET | MISSING OR EMPTY OUTPUT SET |
| 07d_step_response_info | MISSING OR EMPTY OUTPUT SET | MISSING OR EMPTY OUTPUT SET | MISSING OR EMPTY OUTPUT SET | MISSING OR EMPTY OUTPUT SET |
| 08_lookup_table_nonlinear | PASS | PASS | PASS | PASS |
| 09_second_order_damping | PASS | PASS | PASS | PASS |
| 10_rate_limiting_quantization | PASS | PASS | PASS | PASS |
| 11_vector_signal_processing | PASS | PASS | PASS | PASS |
| 20_quaternion_attitude_propagation | PASS | PASS | PASS | PASS |
| 21_isa_atmosphere_model | PASS | PASS | PASS | PASS |
| 22_gravity_models_comparison | PASS | PASS | PASS | PASS |
| 23_dcm_quaternion_conversion | PASS | PASS | PASS | PASS |
| 24_quaternion_vector_rotation | PASS | PASS | PASS | PASS |
| 30_pid_speed_control | PASS | PASS | PASS | PASS |
| 31_discrete_pid_sampled_control | PASS | PASS | PASS | PASS |
| 32_lqr_state_feedback | PASS | PASS | PASS | PASS |
| 33_lead_lag_compensator | PASS | PASS | PASS | PASS |
| 34_anti_windup_pid | PASS | PASS | PASS | PASS |
| 35_pi_pd_controllers | PASS | PASS | PASS | PASS |
| 36_model_reference_control | PASS | PASS | PASS | PASS |
| 37_pole_placement_control | PASS | PASS | PASS | PASS |
| 40_dsp_fft_spectrum | PASS | PASS | PASS | PASS |
| 41_dsp_fir_lowpass | PASS | PASS | PASS | PASS |
| 42_rf_receiver_chain | PASS | PASS | PASS | PASS |
| 43_rf_am_modulation | PASS | PASS | PASS | PASS |
| 44_nav_coordinate_transform | PASS | PASS | PASS | PASS |
| 45_sensor_fusion_ahrs | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH |
| 46_sensor_fusion_tracking | PASS | PASS | PASS | PASS |
| 50_lorenz_attractor_3d | PASS | PASS | PASS | PASS |

## Statistics

- Total tests: 156
- Passed: 136 (87.2%)
- Simulation failures: 0
- Build failures: 0
- Run failures: 16
- Output validation failures: 4

## Detailed Failures

### 07a_bode_plot_analysis (python)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07a_bode_plot_analysis (cpp)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07a_bode_plot_analysis (c)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07a_bode_plot_analysis (rust)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07b_nyquist_plot_analysis (python)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07b_nyquist_plot_analysis (cpp)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07b_nyquist_plot_analysis (c)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07b_nyquist_plot_analysis (rust)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07c_pole_zero_map (python)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07c_pole_zero_map (cpp)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07c_pole_zero_map (c)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07c_pole_zero_map (rust)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07d_step_response_info (python)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07d_step_response_info (cpp)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07d_step_response_info (c)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 07d_step_response_info (rust)

- Run failed: Results CSV contains no output columns
- Failure category: `missing_or_empty_output_set`

### 45_sensor_fusion_ahrs (python)

- Max relative error: 100.0000%
- Headless final values: {'sink=scope_quat|in=0|source=madgwick|out=0|element=0': 1.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=1': 0.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=2': 0.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=3': 0.0, 'sink=scope_comp|in=0|source=rad2deg_comp|out=0|element=scalar': 0.0, 'sink=scope_madgwick|in=0|source=rad2deg_madg|out=0|element=scalar': 0.0}
- Codegen final values: {'sink=scope_quat|in=0|source=madgwick|out=0|element=0': 0.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=1': 0.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=2': 0.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=3': 0.0, 'sink=scope_comp|in=0|source=rad2deg_comp|out=0|element=scalar': 0.0, 'sink=scope_madgwick|in=0|source=rad2deg_madg|out=0|element=scalar': 0.0}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_quat|in=0|source=madgwick|out=0|element=0']

### 45_sensor_fusion_ahrs (cpp)

- Max relative error: 6789.6700%
- Headless final values: {'sink=scope_quat|in=0|source=madgwick|out=0|element=0': 1.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=1': 0.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=2': 0.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=3': 0.0, 'sink=scope_comp|in=0|source=rad2deg_comp|out=0|element=scalar': 0.0, 'sink=scope_madgwick|in=0|source=rad2deg_madg|out=0|element=scalar': 0.0}
- Codegen final values: {'sink=scope_quat|in=0|source=madgwick|out=0|element=0': 0.948972, 'sink=scope_quat|in=0|source=madgwick|out=0|element=1': 0.0146123, 'sink=scope_quat|in=0|source=madgwick|out=0|element=2': -0.0069083, 'sink=scope_quat|in=0|source=madgwick|out=0|element=3': -0.314947, 'sink=scope_comp|in=0|source=rad2deg_comp|out=0|element=scalar': 67.8967, 'sink=scope_madgwick|in=0|source=rad2deg_madg|out=0|element=scalar': 1.83866}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_comp|in=0|source=rad2deg_comp|out=0|element=scalar', 'sink=scope_madgwick|in=0|source=rad2deg_madg|out=0|element=scalar', 'sink=scope_quat|in=0|source=madgwick|out=0|element=0', 'sink=scope_quat|in=0|source=madgwick|out=0|element=3']

### 45_sensor_fusion_ahrs (c)

- Max relative error: 6810.3300%
- Headless final values: {'sink=scope_quat|in=0|source=madgwick|out=0|element=0': 1.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=1': 0.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=2': 0.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=3': 0.0, 'sink=scope_comp|in=0|source=rad2deg_comp|out=0|element=scalar': 0.0, 'sink=scope_madgwick|in=0|source=rad2deg_madg|out=0|element=scalar': 0.0}
- Codegen final values: {'sink=scope_quat|in=0|source=madgwick|out=0|element=0': 0.950285, 'sink=scope_quat|in=0|source=madgwick|out=0|element=1': 0.00747159, 'sink=scope_quat|in=0|source=madgwick|out=0|element=2': -0.00969553, 'sink=scope_quat|in=0|source=madgwick|out=0|element=3': -0.311139, 'sink=scope_comp|in=0|source=rad2deg_comp|out=0|element=scalar': 68.1033, 'sink=scope_madgwick|in=0|source=rad2deg_madg|out=0|element=scalar': 1.15949}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_comp|in=0|source=rad2deg_comp|out=0|element=scalar', 'sink=scope_madgwick|in=0|source=rad2deg_madg|out=0|element=scalar', 'sink=scope_quat|in=0|source=madgwick|out=0|element=0', 'sink=scope_quat|in=0|source=madgwick|out=0|element=3']

### 45_sensor_fusion_ahrs (rust)

- Max relative error: 6798.7109%
- Headless final values: {'sink=scope_quat|in=0|source=madgwick|out=0|element=0': 1.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=1': 0.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=2': 0.0, 'sink=scope_quat|in=0|source=madgwick|out=0|element=3': 0.0, 'sink=scope_comp|in=0|source=rad2deg_comp|out=0|element=scalar': 0.0, 'sink=scope_madgwick|in=0|source=rad2deg_madg|out=0|element=scalar': 0.0}
- Codegen final values: {'sink=scope_quat|in=0|source=madgwick|out=0|element=0': 0.9502, 'sink=scope_quat|in=0|source=madgwick|out=0|element=1': 0.010249, 'sink=scope_quat|in=0|source=madgwick|out=0|element=2': -0.009641, 'sink=scope_quat|in=0|source=madgwick|out=0|element=3': -0.311323, 'sink=scope_comp|in=0|source=rad2deg_comp|out=0|element=scalar': 67.987109, 'sink=scope_madgwick|in=0|source=rad2deg_madg|out=0|element=scalar': 1.460164}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_comp|in=0|source=rad2deg_comp|out=0|element=scalar', 'sink=scope_madgwick|in=0|source=rad2deg_madg|out=0|element=scalar', 'sink=scope_quat|in=0|source=madgwick|out=0|element=0', 'sink=scope_quat|in=0|source=madgwick|out=0|element=3']
