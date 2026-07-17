# Codegen Validation Report

> **Historical validation artifact — not the current codegen result.** This archived
> report preserves the 36/156 validation state last updated on 2026-01-21 in `5d51047`.
> The authoritative generated report is `docs/codegen-validation-report.md`, which
> reached 156/156 in `6a60e13`. Retain this file for audit chronology; do not regenerate
> or use it as the current validation baseline.

This report compares the outputs of generated code against the headless simulation.

## Summary

| Example | Python | C++ | C | Rust |
|---------|--------|-----|---|------|
| 01_sine_wave_basic | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 02_first_order_step_response | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 03_pid_controller | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 04_mass_spring_damper | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 04b_mass_spring_damper_underdamped | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 05a_moving_average_filter | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 05b_lowpass_filter | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 06_kalman_filter_estimation | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 06b_kalman_position_velocity | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 07_thermostat_relay_control | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 07a_bode_plot_analysis | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 07b_nyquist_plot_analysis | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 07c_pole_zero_map | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 07d_step_response_info | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 08_lookup_table_nonlinear | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 09_second_order_damping | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 10_rate_limiting_quantization | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 11_vector_signal_processing | BUILD FAIL | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 20_quaternion_attitude_propagation | BUILD FAIL | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 21_isa_atmosphere_model | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 22_gravity_models_comparison | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 23_dcm_quaternion_conversion | BUILD FAIL | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 24_quaternion_vector_rotation | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 30_pid_speed_control | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 31_discrete_pid_sampled_control | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 32_lqr_state_feedback | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 33_lead_lag_compensator | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 34_anti_windup_pid | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 35_pi_pd_controllers | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 36_model_reference_control | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 37_pole_placement_control | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 40_dsp_fft_spectrum | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 41_dsp_fir_lowpass | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 42_rf_receiver_chain | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 43_rf_am_modulation | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 44_nav_coordinate_transform | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 45_sensor_fusion_ahrs | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 46_sensor_fusion_tracking | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 50_lorenz_attractor_3d | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |

## Statistics

- Total tests: 156
- Passed: 36 (23.1%)
- Build failures: 120
- Run failures: 0
- Value mismatches: 0

## Detailed Failures

### 01_sine_wave_basic (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 01_sine_wave_basic (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 01_sine_wave_basic (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 02_first_order_step_response (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 02_first_order_step_response (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 02_first_order_step_response (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 03_pid_controller (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 03_pid_controller (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 03_pid_controller (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 04_mass_spring_damper (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 04_mass_spring_damper (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 04_mass_spring_damper (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 04b_mass_spring_damper_underdamped (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 04b_mass_spring_damper_underdamped (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 04b_mass_spring_damper_underdamped (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 05a_moving_average_filter (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 05a_moving_average_filter (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 05a_moving_average_filter (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 05b_lowpass_filter (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 05b_lowpass_filter (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 05b_lowpass_filter (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 06_kalman_filter_estimation (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 06_kalman_filter_estimation (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 06_kalman_filter_estimation (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 06b_kalman_position_velocity (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 06b_kalman_position_velocity (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 06b_kalman_position_velocity (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07_thermostat_relay_control (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07_thermostat_relay_control (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07_thermostat_relay_control (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07a_bode_plot_analysis (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07a_bode_plot_analysis (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07a_bode_plot_analysis (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07b_nyquist_plot_analysis (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07b_nyquist_plot_analysis (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07b_nyquist_plot_analysis (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07c_pole_zero_map (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07c_pole_zero_map (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07c_pole_zero_map (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07d_step_response_info (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07d_step_response_info (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 07d_step_response_info (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 08_lookup_table_nonlinear (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 08_lookup_table_nonlinear (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 08_lookup_table_nonlinear (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 09_second_order_damping (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 09_second_order_damping (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 09_second_order_damping (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 10_rate_limiting_quantization (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 10_rate_limiting_quantization (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 10_rate_limiting_quantization (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 11_vector_signal_processing (python)

- Headless simulation failed
- Build failed: 

### 11_vector_signal_processing (cpp)

- Headless simulation failed
- Build failed: 

### 11_vector_signal_processing (c)

- Headless simulation failed
- Build failed: 

### 11_vector_signal_processing (rust)

- Headless simulation failed
- Build failed: 

### 20_quaternion_attitude_propagation (python)

- Headless simulation failed
- Build failed: 

### 20_quaternion_attitude_propagation (cpp)

- Headless simulation failed
- Build failed: 

### 20_quaternion_attitude_propagation (c)

- Headless simulation failed
- Build failed: 

### 20_quaternion_attitude_propagation (rust)

- Headless simulation failed
- Build failed: 

### 21_isa_atmosphere_model (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 21_isa_atmosphere_model (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 21_isa_atmosphere_model (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 22_gravity_models_comparison (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 22_gravity_models_comparison (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 22_gravity_models_comparison (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 23_dcm_quaternion_conversion (python)

- Headless simulation failed
- Build failed: 

### 23_dcm_quaternion_conversion (cpp)

- Headless simulation failed
- Build failed: 

### 23_dcm_quaternion_conversion (c)

- Headless simulation failed
- Build failed: 

### 23_dcm_quaternion_conversion (rust)

- Headless simulation failed
- Build failed: 

### 24_quaternion_vector_rotation (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 24_quaternion_vector_rotation (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 24_quaternion_vector_rotation (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 30_pid_speed_control (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 30_pid_speed_control (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 30_pid_speed_control (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 31_discrete_pid_sampled_control (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 31_discrete_pid_sampled_control (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 31_discrete_pid_sampled_control (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 32_lqr_state_feedback (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 32_lqr_state_feedback (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 32_lqr_state_feedback (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 33_lead_lag_compensator (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 33_lead_lag_compensator (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 33_lead_lag_compensator (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 34_anti_windup_pid (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 34_anti_windup_pid (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 34_anti_windup_pid (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 35_pi_pd_controllers (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 35_pi_pd_controllers (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 35_pi_pd_controllers (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 36_model_reference_control (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 36_model_reference_control (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 36_model_reference_control (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 37_pole_placement_control (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 37_pole_placement_control (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 37_pole_placement_control (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 40_dsp_fft_spectrum (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 40_dsp_fft_spectrum (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 40_dsp_fft_spectrum (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 41_dsp_fir_lowpass (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 41_dsp_fir_lowpass (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 41_dsp_fir_lowpass (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 42_rf_receiver_chain (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 42_rf_receiver_chain (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 42_rf_receiver_chain (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 43_rf_am_modulation (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 43_rf_am_modulation (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 43_rf_am_modulation (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 44_nav_coordinate_transform (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 44_nav_coordinate_transform (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 44_nav_coordinate_transform (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 45_sensor_fusion_ahrs (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 45_sensor_fusion_ahrs (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 45_sensor_fusion_ahrs (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 46_sensor_fusion_tracking (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 46_sensor_fusion_tracking (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 46_sensor_fusion_tracking (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 50_lorenz_attractor_3d (cpp)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 50_lorenz_attractor_3d (c)

- Build failed: mkdir: cannot create directory ‘output’: File exists


### 50_lorenz_attractor_3d (rust)

- Build failed: mkdir: cannot create directory ‘output’: File exists
