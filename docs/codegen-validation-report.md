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
| 45_sensor_fusion_ahrs | PASS | PASS | PASS | PASS |
| 46_sensor_fusion_tracking | PASS | PASS | PASS | PASS |
| 50_lorenz_attractor_3d | PASS | PASS | PASS | PASS |

## Statistics

- Total tests: 156
- Passed: 156 (100.0%)
- Simulation failures: 0
- Build failures: 0
- Run failures: 0
- Output validation failures: 0

## Detailed Failures

No failures!