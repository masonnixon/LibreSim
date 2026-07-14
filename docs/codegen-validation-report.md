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
| 40_dsp_fft_spectrum | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH |
| 41_dsp_fir_lowpass | PASS | PASS | PASS | PASS |
| 42_rf_receiver_chain | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH |
| 43_rf_am_modulation | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH |
| 44_nav_coordinate_transform | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH |
| 45_sensor_fusion_ahrs | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH |
| 46_sensor_fusion_tracking | PASS | PASS | PASS | PASS |
| 50_lorenz_attractor_3d | PASS | NUMERICAL MISMATCH | NUMERICAL MISMATCH | NUMERICAL MISMATCH |

## Statistics

- Total tests: 156
- Passed: 117 (75.0%)
- Simulation failures: 0
- Build failures: 0
- Run failures: 16
- Output validation failures: 23

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

### 40_dsp_fft_spectrum (python)

- Max relative error: 14.1008%
- Headless final values: {'sink=scope_time|in=0|source=sum_signals|out=0|element=scalar': -0.14100775204932509, 'sink=scope_freq|in=0|source=fft|out=0|element=scalar': 0.0}
- Codegen final values: {'sink=scope_time|in=0|source=sum_signals|out=0|element=scalar': -0.14100775204932509, 'sink=scope_freq|in=0|source=fft|out=0|element=scalar': -0.14100775204932509}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_freq|in=0|source=fft|out=0|element=scalar']

### 40_dsp_fft_spectrum (cpp)

- Max relative error: 14.1008%
- Headless final values: {'sink=scope_time|in=0|source=sum_signals|out=0|element=scalar': -0.14100775204932509, 'sink=scope_freq|in=0|source=fft|out=0|element=scalar': 0.0}
- Codegen final values: {'sink=scope_time|in=0|source=sum_signals|out=0|element=scalar': -0.141008, 'sink=scope_freq|in=0|source=fft|out=0|element=scalar': -0.141008}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_freq|in=0|source=fft|out=0|element=scalar']

### 40_dsp_fft_spectrum (c)

- Max relative error: 14.1008%
- Headless final values: {'sink=scope_time|in=0|source=sum_signals|out=0|element=scalar': -0.14100775204932509, 'sink=scope_freq|in=0|source=fft|out=0|element=scalar': 0.0}
- Codegen final values: {'sink=scope_time|in=0|source=sum_signals|out=0|element=scalar': -0.141008, 'sink=scope_freq|in=0|source=fft|out=0|element=scalar': -0.141008}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_freq|in=0|source=fft|out=0|element=scalar']

### 40_dsp_fft_spectrum (rust)

- Max relative error: 14.1008%
- Headless final values: {'sink=scope_time|in=0|source=sum_signals|out=0|element=scalar': -0.14100775204932509, 'sink=scope_freq|in=0|source=fft|out=0|element=scalar': 0.0}
- Codegen final values: {'sink=scope_time|in=0|source=sum_signals|out=0|element=scalar': -0.141008, 'sink=scope_freq|in=0|source=fft|out=0|element=scalar': -0.141008}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_freq|in=0|source=fft|out=0|element=scalar']

### 42_rf_receiver_chain (python)

- Max relative error: 396.2963%
- Headless final values: {'sink=scope_power|in=0|source=if_amp|out=0|element=scalar': 27.0, 'sink=scope_nf|in=0|source=if_amp|out=1|element=scalar': 27.0}
- Codegen final values: {'sink=scope_power|in=0|source=if_amp|out=0|element=scalar': -80.0, 'sink=scope_nf|in=0|source=if_amp|out=1|element=scalar': -80.0}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_nf|in=0|source=if_amp|out=1|element=scalar', 'sink=scope_power|in=0|source=if_amp|out=0|element=scalar']

### 42_rf_receiver_chain (cpp)

- Max relative error: 396.2963%
- Headless final values: {'sink=scope_power|in=0|source=if_amp|out=0|element=scalar': 27.0, 'sink=scope_nf|in=0|source=if_amp|out=1|element=scalar': 27.0}
- Codegen final values: {'sink=scope_power|in=0|source=if_amp|out=0|element=scalar': -80.0, 'sink=scope_nf|in=0|source=if_amp|out=1|element=scalar': -80.0}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_nf|in=0|source=if_amp|out=1|element=scalar', 'sink=scope_power|in=0|source=if_amp|out=0|element=scalar']

### 42_rf_receiver_chain (c)

- Max relative error: 396.2963%
- Headless final values: {'sink=scope_power|in=0|source=if_amp|out=0|element=scalar': 27.0, 'sink=scope_nf|in=0|source=if_amp|out=1|element=scalar': 27.0}
- Codegen final values: {'sink=scope_power|in=0|source=if_amp|out=0|element=scalar': -80.0, 'sink=scope_nf|in=0|source=if_amp|out=1|element=scalar': -80.0}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_nf|in=0|source=if_amp|out=1|element=scalar', 'sink=scope_power|in=0|source=if_amp|out=0|element=scalar']

### 42_rf_receiver_chain (rust)

- Max relative error: 396.2963%
- Headless final values: {'sink=scope_power|in=0|source=if_amp|out=0|element=scalar': 27.0, 'sink=scope_nf|in=0|source=if_amp|out=1|element=scalar': 27.0}
- Codegen final values: {'sink=scope_power|in=0|source=if_amp|out=0|element=scalar': -80.0, 'sink=scope_nf|in=0|source=if_amp|out=1|element=scalar': -80.0}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_nf|in=0|source=if_amp|out=1|element=scalar', 'sink=scope_power|in=0|source=if_amp|out=0|element=scalar']

### 43_rf_am_modulation (python)

- Max relative error: 100.5587%
- Headless final values: {'sink=scope_signals|in=0|source=message|out=0|element=scalar': -0.0050265151724279335, 'sink=scope_signals|in=1|source=carrier|out=0|element=scalar': -0.12533323356379913, 'sink=scope_am|in=0|source=am_mod|out=0|element=scalar': 0.8997334131489604}
- Codegen final values: {'sink=scope_signals|in=0|source=message|out=0|element=scalar': -0.0050265151724279335, 'sink=scope_signals|in=1|source=carrier|out=0|element=scalar': -0.12533323356379913, 'sink=scope_am|in=0|source=am_mod|out=0|element=scalar': -0.0050265151724279335}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_am|in=0|source=am_mod|out=0|element=scalar']

### 43_rf_am_modulation (cpp)

- Max relative error: 100.5587%
- Headless final values: {'sink=scope_signals|in=0|source=message|out=0|element=scalar': -0.0050265151724279335, 'sink=scope_signals|in=1|source=carrier|out=0|element=scalar': -0.12533323356379913, 'sink=scope_am|in=0|source=am_mod|out=0|element=scalar': 0.8997334131489604}
- Codegen final values: {'sink=scope_signals|in=0|source=message|out=0|element=scalar': -0.00502652, 'sink=scope_signals|in=1|source=carrier|out=0|element=scalar': -0.125333, 'sink=scope_am|in=0|source=am_mod|out=0|element=scalar': -0.00502652}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_am|in=0|source=am_mod|out=0|element=scalar']

### 43_rf_am_modulation (c)

- Max relative error: 100.5587%
- Headless final values: {'sink=scope_signals|in=0|source=message|out=0|element=scalar': -0.0050265151724279335, 'sink=scope_signals|in=1|source=carrier|out=0|element=scalar': -0.12533323356379913, 'sink=scope_am|in=0|source=am_mod|out=0|element=scalar': 0.8997334131489604}
- Codegen final values: {'sink=scope_signals|in=0|source=message|out=0|element=scalar': -0.00502652, 'sink=scope_signals|in=1|source=carrier|out=0|element=scalar': -0.125333, 'sink=scope_am|in=0|source=am_mod|out=0|element=scalar': -0.00502652}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_am|in=0|source=am_mod|out=0|element=scalar']

### 43_rf_am_modulation (rust)

- Max relative error: 100.5587%
- Headless final values: {'sink=scope_signals|in=0|source=message|out=0|element=scalar': -0.0050265151724279335, 'sink=scope_signals|in=1|source=carrier|out=0|element=scalar': -0.12533323356379913, 'sink=scope_am|in=0|source=am_mod|out=0|element=scalar': 0.8997334131489604}
- Codegen final values: {'sink=scope_signals|in=0|source=message|out=0|element=scalar': -0.005027, 'sink=scope_signals|in=1|source=carrier|out=0|element=scalar': -0.125333, 'sink=scope_am|in=0|source=am_mod|out=0|element=scalar': -0.005027}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_am|in=0|source=am_mod|out=0|element=scalar']

### 44_nav_coordinate_transform (python)

- Max relative error: 100.0014%
- Headless final values: {'sink=scope_dist|in=0|source=great_circle|out=0|element=scalar': 8890.369422102835, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=0': -2695453.899675493, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=1': -4330427.782716427, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=2': 3817994.9753713165, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=0': 3817994.9753713165, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=1': -4330427.782716427, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=2': 9073590.899675492}
- Codegen final values: {'sink=scope_dist|in=0|source=great_circle|out=0|element=scalar': 37.0, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=0': 37.0, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=1': -121.9, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=2': 1000.0, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=0': 37.0, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=1': -121.9, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=2': 1000.0}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_dist|in=0|source=great_circle|out=0|element=scalar', 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=0', 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=1', 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=2', 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=0', 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=1', 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=2']

### 44_nav_coordinate_transform (cpp)

- Max relative error: 121107.5617%
- Headless final values: {'sink=scope_dist|in=0|source=great_circle|out=0|element=scalar': 8890.369422102835, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=0': -2695453.899675493, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=1': -4330427.782716427, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=2': 3817994.9753713165, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=0': 3817994.9753713165, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=1': -4330427.782716427, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=2': 9073590.899675492}
- Codegen final values: {'sink=scope_dist|in=0|source=great_circle|out=0|element=scalar': 10775800.0, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=0': 4865040.0, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=1': 488132.0, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=2': -4083400.0, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=0': -1439950.0, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=1': 3867110.0, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=2': 11217400.0}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_dist|in=0|source=great_circle|out=0|element=scalar', 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=0', 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=1', 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=2', 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=0', 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=1', 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=2']

### 44_nav_coordinate_transform (c)

- Max relative error: 121107.5617%
- Headless final values: {'sink=scope_dist|in=0|source=great_circle|out=0|element=scalar': 8890.369422102835, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=0': -2695453.899675493, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=1': -4330427.782716427, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=2': 3817994.9753713165, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=0': 3817994.9753713165, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=1': -4330427.782716427, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=2': 9073590.899675492}
- Codegen final values: {'sink=scope_dist|in=0|source=great_circle|out=0|element=scalar': 10775800.0, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=0': 4865040.0, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=1': 488132.0, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=2': -4083400.0, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=0': -1439950.0, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=1': 3867110.0, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=2': 11217400.0}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_dist|in=0|source=great_circle|out=0|element=scalar', 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=0', 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=1', 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=2', 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=0', 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=1', 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=2']

### 44_nav_coordinate_transform (rust)

- Max relative error: 121107.5030%
- Headless final values: {'sink=scope_dist|in=0|source=great_circle|out=0|element=scalar': 8890.369422102835, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=0': -2695453.899675493, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=1': -4330427.782716427, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=2': 3817994.9753713165, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=0': 3817994.9753713165, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=1': -4330427.782716427, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=2': 9073590.899675492}
- Codegen final values: {'sink=scope_dist|in=0|source=great_circle|out=0|element=scalar': 10775794.784777, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=0': 4865035.615244, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=1': 488131.75314, 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=2': -4083403.826902, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=0': -1439952.763757, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=1': 3867113.771768, 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=2': 11217399.562353}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_dist|in=0|source=great_circle|out=0|element=scalar', 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=0', 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=1', 'sink=scope_ecef|in=0|source=lla_to_ecef|out=0|element=2', 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=0', 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=1', 'sink=scope_ned|in=0|source=ecef_to_ned|out=0|element=2']

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

### 50_lorenz_attractor_3d (cpp)

- Max relative error: 123.6703%
- Headless final values: {'sink=scope_time|in=0|source=x_integrator|out=0|element=scalar': 7.536954627091343, 'sink=scope_time|in=1|source=y_integrator|out=0|element=scalar': 12.752755445113529, 'sink=scope_time|in=2|source=z_integrator|out=0|element=scalar': 15.478052380633539, 'sink=scope_3d|in=0|source=x_integrator|out=0|element=scalar': 7.536954627091343, 'sink=scope_3d|in=1|source=y_integrator|out=0|element=scalar': 12.752755445113529, 'sink=scope_3d|in=2|source=z_integrator|out=0|element=scalar': 15.478052380633539}
- Codegen final values: {'sink=scope_3d|in=0|source=x_integrator|out=0|element=scalar': 13.0873, 'sink=scope_3d|in=1|source=y_integrator|out=0|element=scalar': 11.5923, 'sink=scope_3d|in=2|source=z_integrator|out=0|element=scalar': 34.6198, 'sink=scope_time|in=0|source=x_integrator|out=0|element=scalar': 13.0873, 'sink=scope_time|in=1|source=y_integrator|out=0|element=scalar': 11.5923, 'sink=scope_time|in=2|source=z_integrator|out=0|element=scalar': 34.6198}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_3d|in=0|source=x_integrator|out=0|element=scalar', 'sink=scope_3d|in=1|source=y_integrator|out=0|element=scalar', 'sink=scope_3d|in=2|source=z_integrator|out=0|element=scalar', 'sink=scope_time|in=0|source=x_integrator|out=0|element=scalar', 'sink=scope_time|in=1|source=y_integrator|out=0|element=scalar', 'sink=scope_time|in=2|source=z_integrator|out=0|element=scalar']

### 50_lorenz_attractor_3d (c)

- Max relative error: 123.6703%
- Headless final values: {'sink=scope_time|in=0|source=x_integrator|out=0|element=scalar': 7.536954627091343, 'sink=scope_time|in=1|source=y_integrator|out=0|element=scalar': 12.752755445113529, 'sink=scope_time|in=2|source=z_integrator|out=0|element=scalar': 15.478052380633539, 'sink=scope_3d|in=0|source=x_integrator|out=0|element=scalar': 7.536954627091343, 'sink=scope_3d|in=1|source=y_integrator|out=0|element=scalar': 12.752755445113529, 'sink=scope_3d|in=2|source=z_integrator|out=0|element=scalar': 15.478052380633539}
- Codegen final values: {'sink=scope_3d|in=0|source=x_integrator|out=0|element=scalar': 13.0873, 'sink=scope_3d|in=1|source=y_integrator|out=0|element=scalar': 11.5923, 'sink=scope_3d|in=2|source=z_integrator|out=0|element=scalar': 34.6198, 'sink=scope_time|in=0|source=x_integrator|out=0|element=scalar': 13.0873, 'sink=scope_time|in=1|source=y_integrator|out=0|element=scalar': 11.5923, 'sink=scope_time|in=2|source=z_integrator|out=0|element=scalar': 34.6198}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_3d|in=0|source=x_integrator|out=0|element=scalar', 'sink=scope_3d|in=1|source=y_integrator|out=0|element=scalar', 'sink=scope_3d|in=2|source=z_integrator|out=0|element=scalar', 'sink=scope_time|in=0|source=x_integrator|out=0|element=scalar', 'sink=scope_time|in=1|source=y_integrator|out=0|element=scalar', 'sink=scope_time|in=2|source=z_integrator|out=0|element=scalar']

### 50_lorenz_attractor_3d (rust)

- Max relative error: 123.6702%
- Headless final values: {'sink=scope_time|in=0|source=x_integrator|out=0|element=scalar': 7.536954627091343, 'sink=scope_time|in=1|source=y_integrator|out=0|element=scalar': 12.752755445113529, 'sink=scope_time|in=2|source=z_integrator|out=0|element=scalar': 15.478052380633539, 'sink=scope_3d|in=0|source=x_integrator|out=0|element=scalar': 7.536954627091343, 'sink=scope_3d|in=1|source=y_integrator|out=0|element=scalar': 12.752755445113529, 'sink=scope_3d|in=2|source=z_integrator|out=0|element=scalar': 15.478052380633539}
- Codegen final values: {'sink=scope_3d|in=0|source=x_integrator|out=0|element=scalar': 13.087342, 'sink=scope_3d|in=1|source=y_integrator|out=0|element=scalar': 11.592294, 'sink=scope_3d|in=2|source=z_integrator|out=0|element=scalar': 34.619785, 'sink=scope_time|in=0|source=x_integrator|out=0|element=scalar': 13.087342, 'sink=scope_time|in=1|source=y_integrator|out=0|element=scalar': 11.592294, 'sink=scope_time|in=2|source=z_integrator|out=0|element=scalar': 34.619785}
- Failure category: `numerical_mismatch`
- Mismatched outputs: ['sink=scope_3d|in=0|source=x_integrator|out=0|element=scalar', 'sink=scope_3d|in=1|source=y_integrator|out=0|element=scalar', 'sink=scope_3d|in=2|source=z_integrator|out=0|element=scalar', 'sink=scope_time|in=0|source=x_integrator|out=0|element=scalar', 'sink=scope_time|in=1|source=y_integrator|out=0|element=scalar', 'sink=scope_time|in=2|source=z_integrator|out=0|element=scalar']
