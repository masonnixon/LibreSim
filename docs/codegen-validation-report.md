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
| 05a_moving_average_filter | DIFF (5.74%) | DIFF (7.51%) | DIFF (5.84%) | DIFF (5.84%) |
| 05b_lowpass_filter | DIFF (50.97%) | DIFF (191.11%) | DIFF (285.85%) | DIFF (285.85%) |
| 06_kalman_filter_estimation | DIFF (100.00%) | PASS | PASS | PASS |
| 06b_kalman_position_velocity | DIFF (100.00%) | DIFF (3.45%) | DIFF (8.04%) | DIFF (8.04%) |
| 07_thermostat_relay_control | PASS | PASS | PASS | PASS |
| 07a_bode_plot_analysis | DIFF (0.00%) | DIFF (0.00%) | DIFF (0.00%) | DIFF (0.00%) |
| 07b_nyquist_plot_analysis | DIFF (0.00%) | DIFF (0.00%) | DIFF (0.00%) | DIFF (0.00%) |
| 07c_pole_zero_map | DIFF (0.00%) | DIFF (0.00%) | DIFF (0.00%) | DIFF (0.00%) |
| 07d_step_response_info | DIFF (0.00%) | DIFF (0.00%) | DIFF (0.00%) | DIFF (0.00%) |
| 08_lookup_table_nonlinear | PASS | PASS | PASS | PASS |
| 09_second_order_damping | PASS | PASS | PASS | PASS |
| 10_rate_limiting_quantization | DIFF (134.08%) | DIFF (134.09%) | DIFF (134.09%) | DIFF (134.08%) |
| 11_vector_signal_processing | DIFF (300.00%) | DIFF (500.00%) | DIFF (500.00%) | DIFF (500.00%) |
| 20_quaternion_attitude_propagation | DIFF (25055.33%) | DIFF (25055.33%) | DIFF (25055.33%) | DIFF (25055.33%) |
| 21_isa_atmosphere_model | PASS | PASS | PASS | PASS |
| 22_gravity_models_comparison | DIFF (983.22%) | DIFF (980.13%) | DIFF (980.13%) | DIFF (980.14%) |
| 23_dcm_quaternion_conversion | DIFF (100.00%) | DIFF (100.00%) | DIFF (100.00%) | DIFF (100.00%) |
| 24_quaternion_vector_rotation | DIFF (0.00%) | DIFF (100.00%) | DIFF (100.00%) | DIFF (100.00%) |
| 30_pid_speed_control | PASS | PASS | PASS | PASS |
| 31_discrete_pid_sampled_control | DIFF (52.45%) | DIFF (52.45%) | DIFF (52.45%) | DIFF (52.45%) |
| 32_lqr_state_feedback | DIFF (219.18%) | DIFF (100.06%) | DIFF (100.06%) | DIFF (100.06%) |
| 33_lead_lag_compensator | PASS | PASS | PASS | PASS |
| 34_anti_windup_pid | PASS | PASS | PASS | PASS |
| 35_pi_pd_controllers | DIFF (47.98%) | DIFF (47.98%) | DIFF (47.98%) | DIFF (47.98%) |
| 36_model_reference_control | DIFF (100.00%) | DIFF (100.00%) | DIFF (100.00%) | DIFF (100.00%) |
| 37_pole_placement_control | DIFF (3700.67%) | DIFF (143.24%) | DIFF (143.24%) | DIFF (143.24%) |
| 40_dsp_fft_spectrum | DIFF (14.10%) | DIFF (14.10%) | DIFF (14.10%) | DIFF (14.10%) |
| 41_dsp_fir_lowpass | PASS | DIFF (153.20%) | DIFF (72.07%) | DIFF (72.07%) |
| 42_rf_receiver_chain | DIFF (500.00%) | DIFF (500.00%) | DIFF (500.00%) | DIFF (500.00%) |
| 43_rf_am_modulation | DIFF (100.56%) | DIFF (100.56%) | DIFF (100.56%) | DIFF (100.56%) |
| 44_nav_coordinate_transform | DIFF (100.00%) | DIFF (121107.56%) | DIFF (121107.56%) | DIFF (121107.50%) |
| 45_sensor_fusion_ahrs | DIFF (100.00%) | DIFF (6818.58%) | DIFF (6796.05%) | DIFF (6802.69%) |
| 46_sensor_fusion_tracking | DIFF (19725.29%) | DIFF (3901.00%) | DIFF (3877.11%) | DIFF (3877.10%) |
| 50_lorenz_attractor_3d | PASS | DIFF (222.19%) | DIFF (222.19%) | DIFF (222.19%) |

## Statistics

- Total tests: 156
- Passed: 53 (34.0%)
- Build failures: 0
- Run failures: 0
- Value mismatches: 103

## Detailed Failures

### 05a_moving_average_filter (python)

- Max relative error: 5.7398%
- Headless final values: {'Add Noise': 1.0882062582933973, 'MAF (5 samples)': 1.015304185019112, 'MAF (10 samples)': 1.0447252723118725, 'MAF (20 samples)': 1.045023731508017}
- Codegen final values: {'Add_Noise': 1.098481049550481, 'MAF__5_samples_': 1.0505766218177839, 'MAF__10_samples_': 1.0294390558427993, 'MAF__20_samples_': 0.9850419207170609}

### 05a_moving_average_filter (cpp)

- Max relative error: 7.5120%
- Headless final values: {'Add Noise': 1.0882062582933973, 'MAF (5 samples)': 1.015304185019112, 'MAF (10 samples)': 1.0447252723118725, 'MAF (20 samples)': 1.045023731508017}
- Codegen final values: {'Add_Noise': 1.00646, 'MAF__5_samples_': 0.992215, 'MAF__10_samples_': 0.999543, 'MAF__20_samples_': 0.977594}

### 05a_moving_average_filter (c)

- Max relative error: 5.8386%
- Headless final values: {'Add Noise': 1.0882062582933973, 'MAF (5 samples)': 1.015304185019112, 'MAF (10 samples)': 1.0447252723118725, 'MAF (20 samples)': 1.045023731508017}
- Codegen final values: {'Add_Noise': 1.02467, 'MAF__5_samples_': 1.04308, 'MAF__10_samples_': 1.03505, 'MAF__20_samples_': 1.02413}

### 05a_moving_average_filter (rust)

- Max relative error: 5.8388%
- Headless final values: {'Add Noise': 1.0882062582933973, 'MAF (5 samples)': 1.015304185019112, 'MAF (10 samples)': 1.0447252723118725, 'MAF (20 samples)': 1.045023731508017}
- Codegen final values: {'Add_Noise': 1.024668, 'MAF__5_samples_': 1.043076, 'MAF__10_samples_': 1.035051, 'MAF__20_samples_': 1.024128}

### 05b_lowpass_filter (python)

- Max relative error: 50.9736%
- Headless final values: {'Clean Signal (1 Hz)': -0.0062831439655349165, 'Noisy Signal': -0.20300170558743524, '1st Order (3 Hz)': -0.08186960227202872, 'Butter 1st (3 Hz)': -0.08029235124084352, 'Butter 2nd (3 Hz)': -0.09176525316925412, 'Butter 4th (3 Hz)': -0.13790111028175747, 'Bessel 2nd (3 Hz)': -0.10367873836610352}
- Codegen final values: {'Clean_Signal__1_Hz_': -0.0062831439655349165, 'Noisy_Signal': -0.09952448581708932, '_1st_Order__3_Hz_': -0.04393891702239504, 'Butter_1st__3_Hz_': -0.09952448581708932, 'Butter_2nd__3_Hz_': -0.09952448581708932, 'Butter_4th__3_Hz_': -0.09952448581708932, 'Bessel_2nd__3_Hz_': -0.09952448581708932}

### 05b_lowpass_filter (cpp)

- Max relative error: 191.1115%
- Headless final values: {'Clean Signal (1 Hz)': -0.0062831439655349165, 'Noisy Signal': -0.20300170558743524, '1st Order (3 Hz)': -0.08186960227202872, 'Butter 1st (3 Hz)': -0.08029235124084352, 'Butter 2nd (3 Hz)': -0.09176525316925412, 'Butter 4th (3 Hz)': -0.13790111028175747, 'Bessel 2nd (3 Hz)': -0.10367873836610352}
- Codegen final values: {'Clean_Signal__1_Hz_': -0.00628314, 'Noisy_Signal': 0.0731556, '_1st_Order__3_Hz_': 0.0184871, 'Butter_1st__3_Hz_': 0.0731556, 'Butter_2nd__3_Hz_': 0.0731556, 'Butter_4th__3_Hz_': 0.0731556, 'Bessel_2nd__3_Hz_': 0.0731556}

### 05b_lowpass_filter (c)

- Max relative error: 285.8521%
- Headless final values: {'Clean Signal (1 Hz)': -0.0062831439655349165, 'Noisy Signal': -0.20300170558743524, '1st Order (3 Hz)': -0.08186960227202872, 'Butter 1st (3 Hz)': -0.08029235124084352, 'Butter 2nd (3 Hz)': -0.09176525316925412, 'Butter 4th (3 Hz)': -0.13790111028175747, 'Bessel 2nd (3 Hz)': -0.10367873836610352}
- Codegen final values: {'Clean_Signal__1_Hz_': -0.00628314, 'Noisy_Signal': 0.149225, '_1st_Order__3_Hz_': -0.0067009, 'Butter_1st__3_Hz_': 0.149225, 'Butter_2nd__3_Hz_': 0.149225, 'Butter_4th__3_Hz_': 0.149225, 'Bessel_2nd__3_Hz_': 0.149225}

### 05b_lowpass_filter (rust)

- Max relative error: 285.8521%
- Headless final values: {'Clean Signal (1 Hz)': -0.0062831439655349165, 'Noisy Signal': -0.20300170558743524, '1st Order (3 Hz)': -0.08186960227202872, 'Butter 1st (3 Hz)': -0.08029235124084352, 'Butter 2nd (3 Hz)': -0.09176525316925412, 'Butter 4th (3 Hz)': -0.13790111028175747, 'Bessel 2nd (3 Hz)': -0.10367873836610352}
- Codegen final values: {'Clean_Signal__1_Hz_': -0.006283, 'Noisy_Signal': 0.149225, '_1st_Order__3_Hz_': -0.006701, 'Butter_1st__3_Hz_': 0.149225, 'Butter_2nd__3_Hz_': 0.149225, 'Butter_4th__3_Hz_': 0.149225, 'Bessel_2nd__3_Hz_': 0.149225}

### 06_kalman_filter_estimation (python)

- Max relative error: 100.0000%
- Headless final values: {'True Signal': 4.999999999999916, 'Kalman Filter': 4.947437539013666}
- Codegen final values: {'True_Signal': 4.999999999999916, 'Kalman_Filter': 0.0}

### 06b_kalman_position_velocity (python)

- Max relative error: 100.0000%
- Headless final values: {'True Velocity': 1.0, 'Split State': 10.023836475305469, 'True Position': 9.999999999999831, 'Noisy Measurement': 10.444632029639543}
- Codegen final values: {'True_Velocity': 1.0, 'Split_State_1': 0.0, 'True_Position': 9.999999999999831, 'Noisy_Measurement': 10.386145707160344, 'Split_State': 0.0}

### 06b_kalman_position_velocity (cpp)

- Max relative error: 3.4480%
- Headless final values: {'True Velocity': 1.0, 'Split State': 10.023836475305469, 'True Position': 9.999999999999831, 'Noisy Measurement': 10.444632029639543}
- Codegen final values: {'True_Velocity': 1.0, 'Split_State': 10.0358, 'True_Position': 10.0, 'Noisy_Measurement': 10.0845}

### 06b_kalman_position_velocity (c)

- Max relative error: 8.0431%
- Headless final values: {'True Velocity': 1.0, 'Split State': 10.023836475305469, 'True Position': 9.999999999999831, 'Noisy Measurement': 10.444632029639543}
- Codegen final values: {'True_Velocity': 1.0, 'Split_State': 10.0426, 'True_Position': 10.0, 'Noisy_Measurement': 9.60456}

### 06b_kalman_position_velocity (rust)

- Max relative error: 8.0431%
- Headless final values: {'True Velocity': 1.0, 'Split State': 10.023836475305469, 'True Position': 9.999999999999831, 'Noisy Measurement': 10.444632029639543}
- Codegen final values: {'True_Velocity': 1.0, 'Split_State': 10.042556, 'True_Position': 10.0, 'Noisy_Measurement': 9.604561}

### 07a_bode_plot_analysis (python)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07a_bode_plot_analysis (cpp)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07a_bode_plot_analysis (c)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07a_bode_plot_analysis (rust)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07b_nyquist_plot_analysis (python)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07b_nyquist_plot_analysis (cpp)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07b_nyquist_plot_analysis (c)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07b_nyquist_plot_analysis (rust)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07c_pole_zero_map (python)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07c_pole_zero_map (cpp)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07c_pole_zero_map (c)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07c_pole_zero_map (rust)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07d_step_response_info (python)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07d_step_response_info (cpp)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07d_step_response_info (c)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 07d_step_response_info (rust)

- Max relative error: 0.0000%
- Headless final values: {}
- Codegen final values: {}

### 10_rate_limiting_quantization (python)

- Max relative error: 134.0849%
- Headless final values: {'Command': -1.3791876954540827e-11, 'Rate Limiter': -0.44965148848372394, 'Quantizer': 0.0, 'Then Quant': -0.5}
- Codegen final values: {'Command': -1.3791876954540827e-11, 'Rate_Limiter': -1.0525662138874659, 'Quantizer': 0.0, 'Then_Quant': -1.0}

### 10_rate_limiting_quantization (cpp)

- Max relative error: 134.0857%
- Headless final values: {'Command': -1.3791876954540827e-11, 'Rate Limiter': -0.44965148848372394, 'Quantizer': 0.0, 'Then Quant': -0.5}
- Codegen final values: {'Command': -1.37919e-11, 'Rate_Limiter': -1.05257, 'Quantizer': -0.0, 'Then_Quant': -1.0}

### 10_rate_limiting_quantization (c)

- Max relative error: 134.0857%
- Headless final values: {'Command': -1.3791876954540827e-11, 'Rate Limiter': -0.44965148848372394, 'Quantizer': 0.0, 'Then Quant': -0.5}
- Codegen final values: {'Command': -1.37919e-11, 'Rate_Limiter': -1.05257, 'Quantizer': -0.0, 'Then_Quant': -1.0}

### 10_rate_limiting_quantization (rust)

- Max relative error: 134.0848%
- Headless final values: {'Command': -1.3791876954540827e-11, 'Rate Limiter': -0.44965148848372394, 'Quantizer': 0.0, 'Then Quant': -0.5}
- Codegen final values: {'Command': -0.0, 'Rate_Limiter': -1.052566, 'Quantizer': -0.0, 'Then_Quant': -1.0}

### 11_vector_signal_processing (python)

- Max relative error: 300.0000%
- Headless final values: {'Split XYZ': 3.9999999999999325, '√(sum)[1]': 3.6759590373805325e-12, '√(sum)[2]': 5.196152422671577, '√(sum)[3]': 6.928203230275392}
- Codegen final values: {'Split_XYZ': -2.122315939761688e-12, 'Split_XYZ_1': 2.9999999999797615, 'Split_XYZ_2': 3.9999999999999325, 'Vector_Magnitude': 4.999999999987803}

### 11_vector_signal_processing (cpp)

- Max relative error: 500.0000%
- Headless final values: {'Split XYZ': 3.9999999999999325, '√(sum)[1]': 3.6759590373805325e-12, '√(sum)[2]': 5.196152422671577, '√(sum)[3]': 6.928203230275392}
- Codegen final values: {'Split_XYZ': 4.0, 'Vector_Magnitude': 5.0}

### 11_vector_signal_processing (c)

- Max relative error: 500.0000%
- Headless final values: {'Split XYZ': 3.9999999999999325, '√(sum)[1]': 3.6759590373805325e-12, '√(sum)[2]': 5.196152422671577, '√(sum)[3]': 6.928203230275392}
- Codegen final values: {'Split_XYZ': 4.0, 'Vector_Magnitude': 5.0}

### 11_vector_signal_processing (rust)

- Max relative error: 500.0000%
- Headless final values: {'Split XYZ': 3.9999999999999325, '√(sum)[1]': 3.6759590373805325e-12, '√(sum)[2]': 5.196152422671577, '√(sum)[3]': 6.928203230275392}
- Codegen final values: {'Split_XYZ': 4.0, 'Vector_Magnitude': 5.0}

### 20_quaternion_attitude_propagation (python)

- Max relative error: 25055.3319%
- Headless final values: {'Normalize[1]': 0.2506151135803639, 'Normalize[2]': 0.6830760322509691, 'Normalize[3]': 0.262037427322614, 'Normalize[4]': -0.6339839001832145, 'Rad→Deg[1]': 171.83004272048746, 'Rad→Deg[2]': 85.91502136024368, 'Rad→Deg[3]': 34.36600854409808}
- Codegen final values: {'Quaternion': 0.2506151135803639, 'Euler_Angles__deg_': 171.83004272048746}

### 20_quaternion_attitude_propagation (cpp)

- Max relative error: 25055.3256%
- Headless final values: {'Normalize[1]': 0.2506151135803639, 'Normalize[2]': 0.6830760322509691, 'Normalize[3]': 0.262037427322614, 'Normalize[4]': -0.6339839001832145, 'Rad→Deg[1]': 171.83004272048746, 'Rad→Deg[2]': 85.91502136024368, 'Rad→Deg[3]': 34.36600854409808}
- Codegen final values: {'Quaternion': 0.250615, 'Euler_Angles__deg_': 171.83}

### 20_quaternion_attitude_propagation (c)

- Max relative error: 25055.3256%
- Headless final values: {'Normalize[1]': 0.2506151135803639, 'Normalize[2]': 0.6830760322509691, 'Normalize[3]': 0.262037427322614, 'Normalize[4]': -0.6339839001832145, 'Rad→Deg[1]': 171.83004272048746, 'Rad→Deg[2]': 85.91502136024368, 'Rad→Deg[3]': 34.36600854409808}
- Codegen final values: {'Quaternion': 0.250615, 'Euler_Angles__deg_': 171.83}

### 20_quaternion_attitude_propagation (rust)

- Max relative error: 25055.3319%
- Headless final values: {'Normalize[1]': 0.2506151135803639, 'Normalize[2]': 0.6830760322509691, 'Normalize[3]': 0.262037427322614, 'Normalize[4]': -0.6339839001832145, 'Rad→Deg[1]': 171.83004272048746, 'Rad→Deg[2]': 85.91502136024368, 'Rad→Deg[3]': 34.36600854409808}
- Codegen final values: {'Quaternion': 0.250615, 'Euler_Angles__deg_': 171.830043}

### 22_gravity_models_comparison (python)

- Max relative error: 983.2182%
- Headless final values: {'Latitude (deg)': 89.55000000000005, 'Flat Earth g[1]': 0.0, 'Flat Earth g[2]': 0.0, 'Flat Earth g[3]': 9.80665, 'WGS84 Gravity': 9.7803253359, 'Difference[1]': 9.7803253359, 'Difference[2]': 0.0, 'Difference[3]': -9.80665}
- Codegen final values: {'Latitude__deg_': 89.55000000000005, 'Flat_Earth_g__m_s2_': 0.0, 'WGS84_g__m_s2_': 9.832181725319519, 'Deltag__m_s2_': 9.832181725319519}

### 22_gravity_models_comparison (cpp)

- Max relative error: 980.1350%
- Headless final values: {'Latitude (deg)': 89.55000000000005, 'Flat Earth g[1]': 0.0, 'Flat Earth g[2]': 0.0, 'Flat Earth g[3]': 9.80665, 'WGS84 Gravity': 9.7803253359, 'Difference[1]': 9.7803253359, 'Difference[2]': 0.0, 'Difference[3]': -9.80665}
- Codegen final values: {'Latitude__deg_': 89.55, 'Flat_Earth_g__m_s2_': 0.0, 'WGS84_g__m_s2_': 9.80135, 'Deltag__m_s2_': 9.80135}

### 22_gravity_models_comparison (c)

- Max relative error: 980.1350%
- Headless final values: {'Latitude (deg)': 89.55000000000005, 'Flat Earth g[1]': 0.0, 'Flat Earth g[2]': 0.0, 'Flat Earth g[3]': 9.80665, 'WGS84 Gravity': 9.7803253359, 'Difference[1]': 9.7803253359, 'Difference[2]': 0.0, 'Difference[3]': -9.80665}
- Codegen final values: {'Latitude__deg_': 89.55, 'Flat_Earth_g__m_s2_': 0.0, 'WGS84_g__m_s2_': 9.80135, 'Deltag__m_s2_': 9.80135}

### 22_gravity_models_comparison (rust)

- Max relative error: 980.1351%
- Headless final values: {'Latitude (deg)': 89.55000000000005, 'Flat Earth g[1]': 0.0, 'Flat Earth g[2]': 0.0, 'Flat Earth g[3]': 9.80665, 'WGS84 Gravity': 9.7803253359, 'Difference[1]': 9.7803253359, 'Difference[2]': 0.0, 'Difference[3]': -9.80665}
- Codegen final values: {'Latitude__deg_': 89.55, 'Flat_Earth_g__m_s2_': 0.0, 'WGS84_g__m_s2_': 9.801351, 'Deltag__m_s2_': 9.801351}

### 23_dcm_quaternion_conversion (python)

- Max relative error: 100.0000%
- Headless final values: {'Euler→Q[1]': 0.9863021539517195, 'Euler→Q[2]': -0.01055386717071105, 'Euler→Q[3]': 0.14906494312860635, 'Euler→Q[4]': 0.06983065034787249, 'Rad→Deg[1]': -3.040021961321059e-11, 'Rad→Deg[2]': 17.188728399999682, 'Rad→Deg[3]': 8.099619944328689, 'Error[1]': 4.9407606077639794e-18, 'Error[2]': 0.0, 'Error[3]': 2.7755575615628914e-17}
- Codegen final values: {'Quaternion': 0.9863021539517195, 'Input_Euler__deg_': -3.039993652848024e-11, 'Conversion_Error': 4.9407606077639794e-18, 'Output_Euler__deg_': -3.040021961321059e-11}

### 23_dcm_quaternion_conversion (cpp)

- Max relative error: 100.0000%
- Headless final values: {'Euler→Q[1]': 0.9863021539517195, 'Euler→Q[2]': -0.01055386717071105, 'Euler→Q[3]': 0.14906494312860635, 'Euler→Q[4]': 0.06983065034787249, 'Rad→Deg[1]': -3.040021961321059e-11, 'Rad→Deg[2]': 17.188728399999682, 'Rad→Deg[3]': 8.099619944328689, 'Error[1]': 4.9407606077639794e-18, 'Error[2]': 0.0, 'Error[3]': 2.7755575615628914e-17}
- Codegen final values: {'Quaternion': 0.986302, 'Input_Euler__deg_': -3.03999e-11, 'Conversion_Error': 4.94076e-18, 'Output_Euler__deg_': -3.04002e-11}

### 23_dcm_quaternion_conversion (c)

- Max relative error: 100.0000%
- Headless final values: {'Euler→Q[1]': 0.9863021539517195, 'Euler→Q[2]': -0.01055386717071105, 'Euler→Q[3]': 0.14906494312860635, 'Euler→Q[4]': 0.06983065034787249, 'Rad→Deg[1]': -3.040021961321059e-11, 'Rad→Deg[2]': 17.188728399999682, 'Rad→Deg[3]': 8.099619944328689, 'Error[1]': 4.9407606077639794e-18, 'Error[2]': 0.0, 'Error[3]': 2.7755575615628914e-17}
- Codegen final values: {'Quaternion': 0.986302, 'Input_Euler__deg_': -3.03999e-11, 'Conversion_Error': 4.94076e-18, 'Output_Euler__deg_': -3.04002e-11}

### 23_dcm_quaternion_conversion (rust)

- Max relative error: 100.0000%
- Headless final values: {'Euler→Q[1]': 0.9863021539517195, 'Euler→Q[2]': -0.01055386717071105, 'Euler→Q[3]': 0.14906494312860635, 'Euler→Q[4]': 0.06983065034787249, 'Rad→Deg[1]': -3.040021961321059e-11, 'Rad→Deg[2]': 17.188728399999682, 'Rad→Deg[3]': 8.099619944328689, 'Error[1]': 4.9407606077639794e-18, 'Error[2]': 0.0, 'Error[3]': 2.7755575615628914e-17}
- Codegen final values: {'Quaternion': 0.986302, 'Input_Euler__deg_': -0.0, 'Conversion_Error': 0.0, 'Output_Euler__deg_': -0.0}

### 24_quaternion_vector_rotation (python)

- Max relative error: 0.0000%
- Headless final values: {'Rotation Angle': 6.2799999999999105, 'Normalize Q[1]': -0.9999987317275395, 'Normalize Q[2]': 0.0, 'Normalize Q[3]': 0.0, 'Normalize Q[4]': 0.0015926529165316812, 'Rotate Vector[1]': 0.9999949269133749, 'Rotate Vector[2]': -0.003185301793227696, 'Rotate Vector[3]': 0.0}
- Codegen final values: {'Rotation_Angle__rad_': 6.2799999999999105, 'Quaternion': -0.9999987317275395, 'Rotated_Vector': 0.0}

### 24_quaternion_vector_rotation (cpp)

- Max relative error: 99.9995%
- Headless final values: {'Rotation Angle': 6.2799999999999105, 'Normalize Q[1]': -0.9999987317275395, 'Normalize Q[2]': 0.0, 'Normalize Q[3]': 0.0, 'Normalize Q[4]': 0.0015926529165316812, 'Rotate Vector[1]': 0.9999949269133749, 'Rotate Vector[2]': -0.003185301793227696, 'Rotate Vector[3]': 0.0}
- Codegen final values: {'Rotation_Angle__rad_': 6.28, 'Quaternion': -0.999999, 'Rotated_Vector': 0.999995}

### 24_quaternion_vector_rotation (c)

- Max relative error: 99.9995%
- Headless final values: {'Rotation Angle': 6.2799999999999105, 'Normalize Q[1]': -0.9999987317275395, 'Normalize Q[2]': 0.0, 'Normalize Q[3]': 0.0, 'Normalize Q[4]': 0.0015926529165316812, 'Rotate Vector[1]': 0.9999949269133749, 'Rotate Vector[2]': -0.003185301793227696, 'Rotate Vector[3]': 0.0}
- Codegen final values: {'Rotation_Angle__rad_': 6.28, 'Quaternion': -0.999999, 'Rotated_Vector': 0.999995}

### 24_quaternion_vector_rotation (rust)

- Max relative error: 99.9995%
- Headless final values: {'Rotation Angle': 6.2799999999999105, 'Normalize Q[1]': -0.9999987317275395, 'Normalize Q[2]': 0.0, 'Normalize Q[3]': 0.0, 'Normalize Q[4]': 0.0015926529165316812, 'Rotate Vector[1]': 0.9999949269133749, 'Rotate Vector[2]': -0.003185301793227696, 'Rotate Vector[3]': 0.0}
- Codegen final values: {'Rotation_Angle__rad_': 6.28, 'Quaternion': -0.999999, 'Rotated_Vector': 0.999995}

### 31_discrete_pid_sampled_control (python)

- Max relative error: 52.4531%
- Headless final values: {'Setpoint': 1.0, 'Continuous Plant': 1.0129558168546957, 'Discrete PID': 1.0719544787179742}
- Codegen final values: {'Setpoint': 1.0, 'Continuous_Plant': 0.4902800539794087, 'Control_Signal': 0.5096816227600627}

### 31_discrete_pid_sampled_control (cpp)

- Max relative error: 52.4530%
- Headless final values: {'Setpoint': 1.0, 'Continuous Plant': 1.0129558168546957, 'Discrete PID': 1.0719544787179742}
- Codegen final values: {'Setpoint': 1.0, 'Continuous_Plant': 0.49028, 'Control_Signal': 0.509682}

### 31_discrete_pid_sampled_control (c)

- Max relative error: 52.4530%
- Headless final values: {'Setpoint': 1.0, 'Continuous Plant': 1.0129558168546957, 'Discrete PID': 1.0719544787179742}
- Codegen final values: {'Setpoint': 1.0, 'Continuous_Plant': 0.49028, 'Control_Signal': 0.509682}

### 31_discrete_pid_sampled_control (rust)

- Max relative error: 52.4530%
- Headless final values: {'Setpoint': 1.0, 'Continuous Plant': 1.0129558168546957, 'Discrete PID': 1.0719544787179742}
- Codegen final values: {'Setpoint': 1.0, 'Continuous_Plant': 0.49028, 'Control_Signal': 0.509682}

### 32_lqr_state_feedback (python)

- Max relative error: 219.1794%
- Headless final values: {'State x[1]': -0.8390715295239608, 'State x[2]': 0.5440211101863909, 'LQR (u = -Kx)': 0.8390715295239608}
- Codegen final values: {'States_x1__x2': 1.0, 'Control_u': 0.0}

### 32_lqr_state_feedback (cpp)

- Max relative error: 100.0615%
- Headless final values: {'State x[1]': -0.8390715295239608, 'State x[2]': 0.5440211101863909, 'LQR (u = -Kx)': 0.8390715295239608}
- Codegen final values: {'States_x1__x2': -0.000230227, 'Control_u': -0.000334636}

### 32_lqr_state_feedback (c)

- Max relative error: 100.0615%
- Headless final values: {'State x[1]': -0.8390715295239608, 'State x[2]': 0.5440211101863909, 'LQR (u = -Kx)': 0.8390715295239608}
- Codegen final values: {'States_x1__x2': -0.000230227, 'Control_u': -0.000334636}

### 32_lqr_state_feedback (rust)

- Max relative error: 100.0616%
- Headless final values: {'State x[1]': -0.8390715295239608, 'State x[2]': 0.5440211101863909, 'LQR (u = -Kx)': 0.8390715295239608}
- Codegen final values: {'States_x1__x2': -0.00023, 'Control_u': -0.000335}

### 35_pi_pd_controllers (python)

- Max relative error: 47.9827%
- Headless final values: {'Setpoint': 1.0, 'Plant (PI)': 0.9552494198667797, 'Plant (PD)': 0.7142857142857073, 'PI Controller': 1.9224357584016698, 'PD Controller': 1.4285714285714468}
- Codegen final values: {'Setpoint': 1.0, 'Plant__PI_': 0.49999999999999933, 'Plant__PD_': 0.9813084112149532, 'PI_Controller': 1.0000000000000013, 'PD_Controller': 1.9626168224299185}

### 35_pi_pd_controllers (cpp)

- Max relative error: 47.9827%
- Headless final values: {'Setpoint': 1.0, 'Plant (PI)': 0.9552494198667797, 'Plant (PD)': 0.7142857142857073, 'PI Controller': 1.9224357584016698, 'PD Controller': 1.4285714285714468}
- Codegen final values: {'Setpoint': 1.0, 'Plant__PI_': 0.5, 'Plant__PD_': 0.981308, 'PI_Controller': 1.0, 'PD_Controller': 1.96262}

### 35_pi_pd_controllers (c)

- Max relative error: 47.9827%
- Headless final values: {'Setpoint': 1.0, 'Plant (PI)': 0.9552494198667797, 'Plant (PD)': 0.7142857142857073, 'PI Controller': 1.9224357584016698, 'PD Controller': 1.4285714285714468}
- Codegen final values: {'Setpoint': 1.0, 'Plant__PI_': 0.5, 'Plant__PD_': 0.981308, 'PI_Controller': 1.0, 'PD_Controller': 1.96262}

### 35_pi_pd_controllers (rust)

- Max relative error: 47.9827%
- Headless final values: {'Setpoint': 1.0, 'Plant (PI)': 0.9552494198667797, 'Plant (PD)': 0.7142857142857073, 'PI Controller': 1.9224357584016698, 'PD Controller': 1.4285714285714468}
- Codegen final values: {'Setpoint': 1.0, 'Plant__PI_': 0.5, 'Plant__PD_': 0.981308, 'PI_Controller': 1.0, 'PD_Controller': 1.962617}

### 36_model_reference_control (python)

- Max relative error: 100.0000%
- Headless final values: {'Command': 1.0, 'Reference Model': 0.9999997115441777, 'Actual Plant': 0.9980620317306245, 'Tracking Error': 0.0019376798135531947}
- Codegen final values: {'Command': 1.0, 'Reference_Model': 0.0, 'Actual_Plant': 0.0, 'Tracking_Error': 0.0}

### 36_model_reference_control (cpp)

- Max relative error: 100.0000%
- Headless final values: {'Command': 1.0, 'Reference Model': 0.9999997115441777, 'Actual Plant': 0.9980620317306245, 'Tracking Error': 0.0019376798135531947}
- Codegen final values: {'Command': 1.0, 'Reference_Model': 0.0, 'Actual_Plant': 0.0, 'Tracking_Error': 0.0}

### 36_model_reference_control (c)

- Max relative error: 100.0000%
- Headless final values: {'Command': 1.0, 'Reference Model': 0.9999997115441777, 'Actual Plant': 0.9980620317306245, 'Tracking Error': 0.0019376798135531947}
- Codegen final values: {'Command': 1.0, 'Reference_Model': 0.0, 'Actual_Plant': 0.0, 'Tracking_Error': 0.0}

### 36_model_reference_control (rust)

- Max relative error: 100.0000%
- Headless final values: {'Command': 1.0, 'Reference Model': 0.9999997115441777, 'Actual Plant': 0.9980620317306245, 'Tracking Error': 0.0019376798135531947}
- Codegen final values: {'Command': 1.0, 'Reference_Model': 0.0, 'Actual_Plant': 0.0, 'Tracking_Error': 0.0}

### 37_pole_placement_control (python)

- Max relative error: 3700.6667%
- Headless final values: {'State [x1, x2][1]': 0.24999999999999967, 'State [x1, x2][2]': 2.31291666666666, 'Pole Placement K': -0.9999999999999987}
- Codegen final values: {'States_x1__x2': 9.501666666666509, 'Control_u': -0.0}

### 37_pole_placement_control (cpp)

- Max relative error: 143.2355%
- Headless final values: {'State [x1, x2][1]': 0.24999999999999967, 'State [x1, x2][2]': 2.31291666666666, 'Pole Placement K': -0.9999999999999987}
- Codegen final values: {'States_x1__x2': 6.21151e-08, 'Control_u': -1.0}

### 37_pole_placement_control (c)

- Max relative error: 143.2355%
- Headless final values: {'State [x1, x2][1]': 0.24999999999999967, 'State [x1, x2][2]': 2.31291666666666, 'Pole Placement K': -0.9999999999999987}
- Codegen final values: {'States_x1__x2': 6.21151e-08, 'Control_u': -1.0}

### 37_pole_placement_control (rust)

- Max relative error: 143.2355%
- Headless final values: {'State [x1, x2][1]': 0.24999999999999967, 'State [x1, x2][2]': 2.31291666666666, 'Pole Placement K': -0.9999999999999987}
- Codegen final values: {'States_x1__x2': 0.0, 'Control_u': -1.0}

### 40_dsp_fft_spectrum (python)

- Max relative error: 14.1008%
- Headless final values: {'Sum': -0.14100775204932509, 'FFT[1]': 0.0, 'FFT[2]': 0.0, 'FFT[3]': 0.0, 'FFT[4]': 0.0, 'FFT[5]': 0.0, 'FFT[6]': 0.0, 'FFT[7]': 0.0, 'FFT[8]': 0.0, 'FFT[9]': 0.0, 'FFT[10]': 0.0, 'FFT[11]': 0.0, 'FFT[12]': 0.0, 'FFT[13]': 0.0, 'FFT[14]': 0.0, 'FFT[15]': 0.0, 'FFT[16]': 0.0, 'FFT[17]': 0.0, 'FFT[18]': 0.0, 'FFT[19]': 0.0, 'FFT[20]': 0.0, 'FFT[21]': 0.0, 'FFT[22]': 0.0, 'FFT[23]': 0.0, 'FFT[24]': 0.0, 'FFT[25]': 0.0, 'FFT[26]': 0.0, 'FFT[27]': 0.0, 'FFT[28]': 0.0, 'FFT[29]': 0.0, 'FFT[30]': 0.0, 'FFT[31]': 0.0, 'FFT[32]': 0.0, 'FFT[33]': 0.0, 'FFT[34]': 0.0, 'FFT[35]': 0.0, 'FFT[36]': 0.0, 'FFT[37]': 0.0, 'FFT[38]': 0.0, 'FFT[39]': 0.0, 'FFT[40]': 0.0, 'FFT[41]': 0.0, 'FFT[42]': 0.0, 'FFT[43]': 0.0, 'FFT[44]': 0.0, 'FFT[45]': 0.0, 'FFT[46]': 0.0, 'FFT[47]': 0.0, 'FFT[48]': 0.0, 'FFT[49]': 0.0, 'FFT[50]': 0.0, 'FFT[51]': 0.0, 'FFT[52]': 0.0, 'FFT[53]': 0.0, 'FFT[54]': 0.0, 'FFT[55]': 0.0, 'FFT[56]': 0.0, 'FFT[57]': 0.0, 'FFT[58]': 0.0, 'FFT[59]': 0.0, 'FFT[60]': 0.0, 'FFT[61]': 0.0, 'FFT[62]': 0.0, 'FFT[63]': 0.0, 'FFT[64]': 0.0, 'FFT[65]': 0.0, 'FFT[66]': 0.0, 'FFT[67]': 0.0, 'FFT[68]': 0.0, 'FFT[69]': 0.0, 'FFT[70]': 0.0, 'FFT[71]': 0.0, 'FFT[72]': 0.0, 'FFT[73]': 0.0, 'FFT[74]': 0.0, 'FFT[75]': 0.0, 'FFT[76]': 0.0, 'FFT[77]': 0.0, 'FFT[78]': 0.0, 'FFT[79]': 0.0, 'FFT[80]': 0.0, 'FFT[81]': 0.0, 'FFT[82]': 0.0, 'FFT[83]': 0.0, 'FFT[84]': 0.0, 'FFT[85]': 0.0, 'FFT[86]': 0.0, 'FFT[87]': 0.0, 'FFT[88]': 0.0, 'FFT[89]': 0.0, 'FFT[90]': 0.0, 'FFT[91]': 0.0, 'FFT[92]': 0.0, 'FFT[93]': 0.0, 'FFT[94]': 0.0, 'FFT[95]': 0.0, 'FFT[96]': 0.0, 'FFT[97]': 0.0, 'FFT[98]': 0.0, 'FFT[99]': 0.0, 'FFT[100]': 0.0, 'FFT[101]': 0.0, 'FFT[102]': 0.0, 'FFT[103]': 0.0, 'FFT[104]': 0.0, 'FFT[105]': 0.0, 'FFT[106]': 0.0, 'FFT[107]': 0.0, 'FFT[108]': 0.0, 'FFT[109]': 0.0, 'FFT[110]': 0.0, 'FFT[111]': 0.0, 'FFT[112]': 0.0, 'FFT[113]': 0.0, 'FFT[114]': 0.0, 'FFT[115]': 0.0, 'FFT[116]': 0.0, 'FFT[117]': 0.0, 'FFT[118]': 0.0, 'FFT[119]': 0.0, 'FFT[120]': 0.0, 'FFT[121]': 0.0, 'FFT[122]': 0.0, 'FFT[123]': 0.0, 'FFT[124]': 0.0, 'FFT[125]': 0.0, 'FFT[126]': 0.0, 'FFT[127]': 0.0, 'FFT[128]': 0.0}
- Codegen final values: {'Time_Domain': -0.14100775204932509, 'Frequency_Spectrum': -0.14100775204932509}

### 40_dsp_fft_spectrum (cpp)

- Max relative error: 14.1008%
- Headless final values: {'Sum': -0.14100775204932509, 'FFT[1]': 0.0, 'FFT[2]': 0.0, 'FFT[3]': 0.0, 'FFT[4]': 0.0, 'FFT[5]': 0.0, 'FFT[6]': 0.0, 'FFT[7]': 0.0, 'FFT[8]': 0.0, 'FFT[9]': 0.0, 'FFT[10]': 0.0, 'FFT[11]': 0.0, 'FFT[12]': 0.0, 'FFT[13]': 0.0, 'FFT[14]': 0.0, 'FFT[15]': 0.0, 'FFT[16]': 0.0, 'FFT[17]': 0.0, 'FFT[18]': 0.0, 'FFT[19]': 0.0, 'FFT[20]': 0.0, 'FFT[21]': 0.0, 'FFT[22]': 0.0, 'FFT[23]': 0.0, 'FFT[24]': 0.0, 'FFT[25]': 0.0, 'FFT[26]': 0.0, 'FFT[27]': 0.0, 'FFT[28]': 0.0, 'FFT[29]': 0.0, 'FFT[30]': 0.0, 'FFT[31]': 0.0, 'FFT[32]': 0.0, 'FFT[33]': 0.0, 'FFT[34]': 0.0, 'FFT[35]': 0.0, 'FFT[36]': 0.0, 'FFT[37]': 0.0, 'FFT[38]': 0.0, 'FFT[39]': 0.0, 'FFT[40]': 0.0, 'FFT[41]': 0.0, 'FFT[42]': 0.0, 'FFT[43]': 0.0, 'FFT[44]': 0.0, 'FFT[45]': 0.0, 'FFT[46]': 0.0, 'FFT[47]': 0.0, 'FFT[48]': 0.0, 'FFT[49]': 0.0, 'FFT[50]': 0.0, 'FFT[51]': 0.0, 'FFT[52]': 0.0, 'FFT[53]': 0.0, 'FFT[54]': 0.0, 'FFT[55]': 0.0, 'FFT[56]': 0.0, 'FFT[57]': 0.0, 'FFT[58]': 0.0, 'FFT[59]': 0.0, 'FFT[60]': 0.0, 'FFT[61]': 0.0, 'FFT[62]': 0.0, 'FFT[63]': 0.0, 'FFT[64]': 0.0, 'FFT[65]': 0.0, 'FFT[66]': 0.0, 'FFT[67]': 0.0, 'FFT[68]': 0.0, 'FFT[69]': 0.0, 'FFT[70]': 0.0, 'FFT[71]': 0.0, 'FFT[72]': 0.0, 'FFT[73]': 0.0, 'FFT[74]': 0.0, 'FFT[75]': 0.0, 'FFT[76]': 0.0, 'FFT[77]': 0.0, 'FFT[78]': 0.0, 'FFT[79]': 0.0, 'FFT[80]': 0.0, 'FFT[81]': 0.0, 'FFT[82]': 0.0, 'FFT[83]': 0.0, 'FFT[84]': 0.0, 'FFT[85]': 0.0, 'FFT[86]': 0.0, 'FFT[87]': 0.0, 'FFT[88]': 0.0, 'FFT[89]': 0.0, 'FFT[90]': 0.0, 'FFT[91]': 0.0, 'FFT[92]': 0.0, 'FFT[93]': 0.0, 'FFT[94]': 0.0, 'FFT[95]': 0.0, 'FFT[96]': 0.0, 'FFT[97]': 0.0, 'FFT[98]': 0.0, 'FFT[99]': 0.0, 'FFT[100]': 0.0, 'FFT[101]': 0.0, 'FFT[102]': 0.0, 'FFT[103]': 0.0, 'FFT[104]': 0.0, 'FFT[105]': 0.0, 'FFT[106]': 0.0, 'FFT[107]': 0.0, 'FFT[108]': 0.0, 'FFT[109]': 0.0, 'FFT[110]': 0.0, 'FFT[111]': 0.0, 'FFT[112]': 0.0, 'FFT[113]': 0.0, 'FFT[114]': 0.0, 'FFT[115]': 0.0, 'FFT[116]': 0.0, 'FFT[117]': 0.0, 'FFT[118]': 0.0, 'FFT[119]': 0.0, 'FFT[120]': 0.0, 'FFT[121]': 0.0, 'FFT[122]': 0.0, 'FFT[123]': 0.0, 'FFT[124]': 0.0, 'FFT[125]': 0.0, 'FFT[126]': 0.0, 'FFT[127]': 0.0, 'FFT[128]': 0.0}
- Codegen final values: {'Time_Domain': -0.141008, 'Frequency_Spectrum': -0.141008}

### 40_dsp_fft_spectrum (c)

- Max relative error: 14.1008%
- Headless final values: {'Sum': -0.14100775204932509, 'FFT[1]': 0.0, 'FFT[2]': 0.0, 'FFT[3]': 0.0, 'FFT[4]': 0.0, 'FFT[5]': 0.0, 'FFT[6]': 0.0, 'FFT[7]': 0.0, 'FFT[8]': 0.0, 'FFT[9]': 0.0, 'FFT[10]': 0.0, 'FFT[11]': 0.0, 'FFT[12]': 0.0, 'FFT[13]': 0.0, 'FFT[14]': 0.0, 'FFT[15]': 0.0, 'FFT[16]': 0.0, 'FFT[17]': 0.0, 'FFT[18]': 0.0, 'FFT[19]': 0.0, 'FFT[20]': 0.0, 'FFT[21]': 0.0, 'FFT[22]': 0.0, 'FFT[23]': 0.0, 'FFT[24]': 0.0, 'FFT[25]': 0.0, 'FFT[26]': 0.0, 'FFT[27]': 0.0, 'FFT[28]': 0.0, 'FFT[29]': 0.0, 'FFT[30]': 0.0, 'FFT[31]': 0.0, 'FFT[32]': 0.0, 'FFT[33]': 0.0, 'FFT[34]': 0.0, 'FFT[35]': 0.0, 'FFT[36]': 0.0, 'FFT[37]': 0.0, 'FFT[38]': 0.0, 'FFT[39]': 0.0, 'FFT[40]': 0.0, 'FFT[41]': 0.0, 'FFT[42]': 0.0, 'FFT[43]': 0.0, 'FFT[44]': 0.0, 'FFT[45]': 0.0, 'FFT[46]': 0.0, 'FFT[47]': 0.0, 'FFT[48]': 0.0, 'FFT[49]': 0.0, 'FFT[50]': 0.0, 'FFT[51]': 0.0, 'FFT[52]': 0.0, 'FFT[53]': 0.0, 'FFT[54]': 0.0, 'FFT[55]': 0.0, 'FFT[56]': 0.0, 'FFT[57]': 0.0, 'FFT[58]': 0.0, 'FFT[59]': 0.0, 'FFT[60]': 0.0, 'FFT[61]': 0.0, 'FFT[62]': 0.0, 'FFT[63]': 0.0, 'FFT[64]': 0.0, 'FFT[65]': 0.0, 'FFT[66]': 0.0, 'FFT[67]': 0.0, 'FFT[68]': 0.0, 'FFT[69]': 0.0, 'FFT[70]': 0.0, 'FFT[71]': 0.0, 'FFT[72]': 0.0, 'FFT[73]': 0.0, 'FFT[74]': 0.0, 'FFT[75]': 0.0, 'FFT[76]': 0.0, 'FFT[77]': 0.0, 'FFT[78]': 0.0, 'FFT[79]': 0.0, 'FFT[80]': 0.0, 'FFT[81]': 0.0, 'FFT[82]': 0.0, 'FFT[83]': 0.0, 'FFT[84]': 0.0, 'FFT[85]': 0.0, 'FFT[86]': 0.0, 'FFT[87]': 0.0, 'FFT[88]': 0.0, 'FFT[89]': 0.0, 'FFT[90]': 0.0, 'FFT[91]': 0.0, 'FFT[92]': 0.0, 'FFT[93]': 0.0, 'FFT[94]': 0.0, 'FFT[95]': 0.0, 'FFT[96]': 0.0, 'FFT[97]': 0.0, 'FFT[98]': 0.0, 'FFT[99]': 0.0, 'FFT[100]': 0.0, 'FFT[101]': 0.0, 'FFT[102]': 0.0, 'FFT[103]': 0.0, 'FFT[104]': 0.0, 'FFT[105]': 0.0, 'FFT[106]': 0.0, 'FFT[107]': 0.0, 'FFT[108]': 0.0, 'FFT[109]': 0.0, 'FFT[110]': 0.0, 'FFT[111]': 0.0, 'FFT[112]': 0.0, 'FFT[113]': 0.0, 'FFT[114]': 0.0, 'FFT[115]': 0.0, 'FFT[116]': 0.0, 'FFT[117]': 0.0, 'FFT[118]': 0.0, 'FFT[119]': 0.0, 'FFT[120]': 0.0, 'FFT[121]': 0.0, 'FFT[122]': 0.0, 'FFT[123]': 0.0, 'FFT[124]': 0.0, 'FFT[125]': 0.0, 'FFT[126]': 0.0, 'FFT[127]': 0.0, 'FFT[128]': 0.0}
- Codegen final values: {'Time_Domain': -0.141008, 'Frequency_Spectrum': -0.141008}

### 40_dsp_fft_spectrum (rust)

- Max relative error: 14.1008%
- Headless final values: {'Sum': -0.14100775204932509, 'FFT[1]': 0.0, 'FFT[2]': 0.0, 'FFT[3]': 0.0, 'FFT[4]': 0.0, 'FFT[5]': 0.0, 'FFT[6]': 0.0, 'FFT[7]': 0.0, 'FFT[8]': 0.0, 'FFT[9]': 0.0, 'FFT[10]': 0.0, 'FFT[11]': 0.0, 'FFT[12]': 0.0, 'FFT[13]': 0.0, 'FFT[14]': 0.0, 'FFT[15]': 0.0, 'FFT[16]': 0.0, 'FFT[17]': 0.0, 'FFT[18]': 0.0, 'FFT[19]': 0.0, 'FFT[20]': 0.0, 'FFT[21]': 0.0, 'FFT[22]': 0.0, 'FFT[23]': 0.0, 'FFT[24]': 0.0, 'FFT[25]': 0.0, 'FFT[26]': 0.0, 'FFT[27]': 0.0, 'FFT[28]': 0.0, 'FFT[29]': 0.0, 'FFT[30]': 0.0, 'FFT[31]': 0.0, 'FFT[32]': 0.0, 'FFT[33]': 0.0, 'FFT[34]': 0.0, 'FFT[35]': 0.0, 'FFT[36]': 0.0, 'FFT[37]': 0.0, 'FFT[38]': 0.0, 'FFT[39]': 0.0, 'FFT[40]': 0.0, 'FFT[41]': 0.0, 'FFT[42]': 0.0, 'FFT[43]': 0.0, 'FFT[44]': 0.0, 'FFT[45]': 0.0, 'FFT[46]': 0.0, 'FFT[47]': 0.0, 'FFT[48]': 0.0, 'FFT[49]': 0.0, 'FFT[50]': 0.0, 'FFT[51]': 0.0, 'FFT[52]': 0.0, 'FFT[53]': 0.0, 'FFT[54]': 0.0, 'FFT[55]': 0.0, 'FFT[56]': 0.0, 'FFT[57]': 0.0, 'FFT[58]': 0.0, 'FFT[59]': 0.0, 'FFT[60]': 0.0, 'FFT[61]': 0.0, 'FFT[62]': 0.0, 'FFT[63]': 0.0, 'FFT[64]': 0.0, 'FFT[65]': 0.0, 'FFT[66]': 0.0, 'FFT[67]': 0.0, 'FFT[68]': 0.0, 'FFT[69]': 0.0, 'FFT[70]': 0.0, 'FFT[71]': 0.0, 'FFT[72]': 0.0, 'FFT[73]': 0.0, 'FFT[74]': 0.0, 'FFT[75]': 0.0, 'FFT[76]': 0.0, 'FFT[77]': 0.0, 'FFT[78]': 0.0, 'FFT[79]': 0.0, 'FFT[80]': 0.0, 'FFT[81]': 0.0, 'FFT[82]': 0.0, 'FFT[83]': 0.0, 'FFT[84]': 0.0, 'FFT[85]': 0.0, 'FFT[86]': 0.0, 'FFT[87]': 0.0, 'FFT[88]': 0.0, 'FFT[89]': 0.0, 'FFT[90]': 0.0, 'FFT[91]': 0.0, 'FFT[92]': 0.0, 'FFT[93]': 0.0, 'FFT[94]': 0.0, 'FFT[95]': 0.0, 'FFT[96]': 0.0, 'FFT[97]': 0.0, 'FFT[98]': 0.0, 'FFT[99]': 0.0, 'FFT[100]': 0.0, 'FFT[101]': 0.0, 'FFT[102]': 0.0, 'FFT[103]': 0.0, 'FFT[104]': 0.0, 'FFT[105]': 0.0, 'FFT[106]': 0.0, 'FFT[107]': 0.0, 'FFT[108]': 0.0, 'FFT[109]': 0.0, 'FFT[110]': 0.0, 'FFT[111]': 0.0, 'FFT[112]': 0.0, 'FFT[113]': 0.0, 'FFT[114]': 0.0, 'FFT[115]': 0.0, 'FFT[116]': 0.0, 'FFT[117]': 0.0, 'FFT[118]': 0.0, 'FFT[119]': 0.0, 'FFT[120]': 0.0, 'FFT[121]': 0.0, 'FFT[122]': 0.0, 'FFT[123]': 0.0, 'FFT[124]': 0.0, 'FFT[125]': 0.0, 'FFT[126]': 0.0, 'FFT[127]': 0.0, 'FFT[128]': 0.0}
- Codegen final values: {'Time_Domain': -0.141008, 'Frequency_Spectrum': -0.141008}

### 41_dsp_fir_lowpass (cpp)

- Max relative error: 153.1971%
- Headless final values: {'Add Noise': -0.4467366615970011, 'FIR Lowpass': -0.6994738636579461, 'Running Mean': -0.391598954949112, 'RMS': 0.3733321866252733}
- Codegen final values: {'Add_Noise': 0.237651, 'FIR_Lowpass': -0.0258994, 'Running_Mean': 0.15501, 'RMS': 0.401037}

### 41_dsp_fir_lowpass (c)

- Max relative error: 72.0676%
- Headless final values: {'Add Noise': -0.4467366615970011, 'FIR Lowpass': -0.6994738636579461, 'Running Mean': -0.391598954949112, 'RMS': 0.3733321866252733}
- Codegen final values: {'Add_Noise': -0.370298, 'FIR_Lowpass': -0.19538, 'Running_Mean': -0.189383, 'RMS': 0.374235}

### 41_dsp_fir_lowpass (rust)

- Max relative error: 72.0676%
- Headless final values: {'Add Noise': -0.4467366615970011, 'FIR Lowpass': -0.6994738636579461, 'Running Mean': -0.391598954949112, 'RMS': 0.3733321866252733}
- Codegen final values: {'Add_Noise': -0.370298, 'FIR_Lowpass': -0.19538, 'Running_Mean': -0.189383, 'RMS': 0.374235}

### 42_rf_receiver_chain (python)

- Max relative error: 500.0000%
- Headless final values: {'IF Amplifier[1]': 27.0, 'IF Amplifier[2]': 20.0, 'IF Amplifier[3]': 4.0}
- Codegen final values: {'Power_Level__dBm_': -80.0, 'Cascaded_NF__dB_': -80.0}

### 42_rf_receiver_chain (cpp)

- Max relative error: 500.0000%
- Headless final values: {'IF Amplifier[1]': 27.0, 'IF Amplifier[2]': 20.0, 'IF Amplifier[3]': 4.0}
- Codegen final values: {'Power_Level__dBm_': -80.0, 'Cascaded_NF__dB_': -80.0}

### 42_rf_receiver_chain (c)

- Max relative error: 500.0000%
- Headless final values: {'IF Amplifier[1]': 27.0, 'IF Amplifier[2]': 20.0, 'IF Amplifier[3]': 4.0}
- Codegen final values: {'Power_Level__dBm_': -80.0, 'Cascaded_NF__dB_': -80.0}

### 42_rf_receiver_chain (rust)

- Max relative error: 500.0000%
- Headless final values: {'IF Amplifier[1]': 27.0, 'IF Amplifier[2]': 20.0, 'IF Amplifier[3]': 4.0}
- Codegen final values: {'Power_Level__dBm_': -80.0, 'Cascaded_NF__dB_': -80.0}

### 43_rf_am_modulation (python)

- Max relative error: 100.5587%
- Headless final values: {'Message (1 Hz)': -0.0050265151724279335, 'Carrier (20 Hz)': -0.12533323356379913, 'AM Modulator': 0.8997334131489604}
- Codegen final values: {'Message__1_Hz_': -0.0050265151724279335, 'Carrier__20_Hz_': -0.12533323356379913, 'AM_Signal': -0.0050265151724279335}

### 43_rf_am_modulation (cpp)

- Max relative error: 100.5587%
- Headless final values: {'Message (1 Hz)': -0.0050265151724279335, 'Carrier (20 Hz)': -0.12533323356379913, 'AM Modulator': 0.8997334131489604}
- Codegen final values: {'Message__1_Hz_': -0.00502652, 'Carrier__20_Hz_': -0.125333, 'AM_Signal': -0.00502652}

### 43_rf_am_modulation (c)

- Max relative error: 100.5587%
- Headless final values: {'Message (1 Hz)': -0.0050265151724279335, 'Carrier (20 Hz)': -0.12533323356379913, 'AM Modulator': 0.8997334131489604}
- Codegen final values: {'Message__1_Hz_': -0.00502652, 'Carrier__20_Hz_': -0.125333, 'AM_Signal': -0.00502652}

### 43_rf_am_modulation (rust)

- Max relative error: 100.5587%
- Headless final values: {'Message (1 Hz)': -0.0050265151724279335, 'Carrier (20 Hz)': -0.12533323356379913, 'AM Modulator': 0.8997334131489604}
- Codegen final values: {'Message__1_Hz_': -0.005027, 'Carrier__20_Hz_': -0.125333, 'AM_Signal': -0.005027}

### 44_nav_coordinate_transform (python)

- Max relative error: 100.0014%
- Headless final values: {'Great Circle Dist': 8890.369422102835, 'LLA to ECEF[1]': -2695453.899675493, 'LLA to ECEF[2]': -4330427.782716427, 'LLA to ECEF[3]': 3817994.9753713165, 'ECEF to NED[1]': 3817994.9753713165, 'ECEF to NED[2]': -4330427.782716427, 'ECEF to NED[3]': 9073590.899675492}
- Codegen final values: {'Distance__m_': 37.0, 'ECEF_Position': 37.0, 'NED_Position': 37.0}

### 44_nav_coordinate_transform (cpp)

- Max relative error: 121107.5617%
- Headless final values: {'Great Circle Dist': 8890.369422102835, 'LLA to ECEF[1]': -2695453.899675493, 'LLA to ECEF[2]': -4330427.782716427, 'LLA to ECEF[3]': 3817994.9753713165, 'ECEF to NED[1]': 3817994.9753713165, 'ECEF to NED[2]': -4330427.782716427, 'ECEF to NED[3]': 9073590.899675492}
- Codegen final values: {'Distance__m_': 10775800.0, 'ECEF_Position': 4865040.0, 'NED_Position': -1439950.0}

### 44_nav_coordinate_transform (c)

- Max relative error: 121107.5617%
- Headless final values: {'Great Circle Dist': 8890.369422102835, 'LLA to ECEF[1]': -2695453.899675493, 'LLA to ECEF[2]': -4330427.782716427, 'LLA to ECEF[3]': 3817994.9753713165, 'ECEF to NED[1]': 3817994.9753713165, 'ECEF to NED[2]': -4330427.782716427, 'ECEF to NED[3]': 9073590.899675492}
- Codegen final values: {'Distance__m_': 10775800.0, 'ECEF_Position': 4865040.0, 'NED_Position': -1439950.0}

### 44_nav_coordinate_transform (rust)

- Max relative error: 121107.5030%
- Headless final values: {'Great Circle Dist': 8890.369422102835, 'LLA to ECEF[1]': -2695453.899675493, 'LLA to ECEF[2]': -4330427.782716427, 'LLA to ECEF[3]': 3817994.9753713165, 'ECEF to NED[1]': 3817994.9753713165, 'ECEF to NED[2]': -4330427.782716427, 'ECEF to NED[3]': 9073590.899675492}
- Codegen final values: {'Distance__m_': 10775794.784777, 'ECEF_Position': 4865035.615244, 'NED_Position': -1439952.763757}

### 45_sensor_fusion_ahrs (python)

- Max relative error: 100.0000%
- Headless final values: {'Madgwick AHRS[1]': 1.0, 'Madgwick AHRS[2]': 0.0, 'Madgwick AHRS[3]': 0.0, 'Madgwick AHRS[4]': 0.0, 'Rad to Deg[1]': 0.0, 'Rad to Deg[2]': 0.0, 'Rad to Deg[3]': 0.0}
- Codegen final values: {'Quaternion': 0.0, 'Complementary__deg_': 0.0, 'Madgwick_Attitude__deg_': 0.0}

### 45_sensor_fusion_ahrs (cpp)

- Max relative error: 6818.5800%
- Headless final values: {'Madgwick AHRS[1]': 1.0, 'Madgwick AHRS[2]': 0.0, 'Madgwick AHRS[3]': 0.0, 'Madgwick AHRS[4]': 0.0, 'Rad to Deg[1]': 0.0, 'Rad to Deg[2]': 0.0, 'Rad to Deg[3]': 0.0}
- Codegen final values: {'Quaternion': -0.928343, 'Complementary__deg_': 68.1858, 'Madgwick_Attitude__deg_': 0.625927}

### 45_sensor_fusion_ahrs (c)

- Max relative error: 6796.0500%
- Headless final values: {'Madgwick AHRS[1]': 1.0, 'Madgwick AHRS[2]': 0.0, 'Madgwick AHRS[3]': 0.0, 'Madgwick AHRS[4]': 0.0, 'Rad to Deg[1]': 0.0, 'Rad to Deg[2]': 0.0, 'Rad to Deg[3]': 0.0}
- Codegen final values: {'Quaternion': -0.927006, 'Complementary__deg_': 67.9605, 'Madgwick_Attitude__deg_': 1.06443}

### 45_sensor_fusion_ahrs (rust)

- Max relative error: 6802.6939%
- Headless final values: {'Madgwick AHRS[1]': 1.0, 'Madgwick AHRS[2]': 0.0, 'Madgwick AHRS[3]': 0.0, 'Madgwick AHRS[4]': 0.0, 'Rad to Deg[1]': 0.0, 'Rad to Deg[2]': 0.0, 'Rad to Deg[3]': 0.0}
- Codegen final values: {'Quaternion': -0.926858, 'Complementary__deg_': 68.026939, 'Madgwick_Attitude__deg_': 1.25765}

### 46_sensor_fusion_tracking (python)

- Max relative error: 19725.2911%
- Headless final values: {'Position': 198.0049999999997, 'Alpha-Beta Filter[1]': 198.77759676167926, 'Alpha-Beta Filter[2]': 4.998705077566088, 'Alpha-Beta-Gamma Filter[1]': 198.52573544112397, 'Alpha-Beta-Gamma Filter[2]': 2.260832937849581, 'Alpha-Beta-Gamma Filter[3]': -11.971374001780916, 'Velocity': 19.900000000000013, 'Acceleration (1 m/s^2)': 1.0}
- Codegen final values: {'Position': 198.0049999999997, 'Alpha_Beta_Filter': 198.25291068331236, 'Alpha_Beta_Gamma_Filter': 198.25291068331236, 'Velocity': 19.900000000000013, 'Alpha_Beta_Filter_1': 198.25291068331236, 'Alpha_Beta_Gamma_Filter_1': 198.25291068331236, 'Acceleration__1_m_s_2_': 1.0, 'Alpha_Beta_Gamma_Filter_2': 198.25291068331236}

### 46_sensor_fusion_tracking (cpp)

- Max relative error: 3900.9962%
- Headless final values: {'Position': 198.0049999999997, 'Alpha-Beta Filter[1]': 198.77759676167926, 'Alpha-Beta Filter[2]': 4.998705077566088, 'Alpha-Beta-Gamma Filter[1]': 198.52573544112397, 'Alpha-Beta-Gamma Filter[2]': 2.260832937849581, 'Alpha-Beta-Gamma Filter[3]': -11.971374001780916, 'Velocity': 19.900000000000013, 'Acceleration (1 m/s^2)': 1.0}
- Codegen final values: {'Position': 197.507, 'Alpha_Beta_Filter': 199.998, 'Alpha_Beta_Gamma_Filter': 199.998, 'Velocity': 19.9, 'Acceleration__1_m_s_2_': 1.0}

### 46_sensor_fusion_tracking (c)

- Max relative error: 3877.1100%
- Headless final values: {'Position': 198.0049999999997, 'Alpha-Beta Filter[1]': 198.77759676167926, 'Alpha-Beta Filter[2]': 4.998705077566088, 'Alpha-Beta-Gamma Filter[1]': 198.52573544112397, 'Alpha-Beta-Gamma Filter[2]': 2.260832937849581, 'Alpha-Beta-Gamma Filter[3]': -11.971374001780916, 'Velocity': 19.900000000000013, 'Acceleration (1 m/s^2)': 1.0}
- Codegen final values: {'Position': 197.507, 'Alpha_Beta_Filter': 198.804, 'Alpha_Beta_Gamma_Filter': 198.804, 'Velocity': 19.9, 'Acceleration__1_m_s_2_': 1.0}

### 46_sensor_fusion_tracking (rust)

- Max relative error: 3877.1027%
- Headless final values: {'Position': 198.0049999999997, 'Alpha-Beta Filter[1]': 198.77759676167926, 'Alpha-Beta Filter[2]': 4.998705077566088, 'Alpha-Beta-Gamma Filter[1]': 198.52573544112397, 'Alpha-Beta-Gamma Filter[2]': 2.260832937849581, 'Alpha-Beta-Gamma Filter[3]': -11.971374001780916, 'Velocity': 19.900000000000013, 'Acceleration (1 m/s^2)': 1.0}
- Codegen final values: {'Position': 197.5075, 'Alpha_Beta_Filter': 198.803637, 'Alpha_Beta_Gamma_Filter': 198.803637, 'Velocity': 19.9, 'Acceleration__1_m_s_2_': 1.0}

### 50_lorenz_attractor_3d (cpp)

- Max relative error: 222.1861%
- Headless final values: {'X Integrator': 7.536954627091343, 'Y Integrator': 12.752755445113529, 'Z Integrator': 15.478052380633539}
- Codegen final values: {'X_Integrator': -8.63395, 'Y_Integrator': -15.5821, 'Z_Integrator': 13.6358}

### 50_lorenz_attractor_3d (c)

- Max relative error: 222.1861%
- Headless final values: {'X Integrator': 7.536954627091343, 'Y Integrator': 12.752755445113529, 'Z Integrator': 15.478052380633539}
- Codegen final values: {'X_Integrator': -8.63395, 'Y_Integrator': -15.5821, 'Z_Integrator': 13.6358}

### 50_lorenz_attractor_3d (rust)

- Max relative error: 222.1861%
- Headless final values: {'X Integrator': 7.536954627091343, 'Y Integrator': 12.752755445113529, 'Z Integrator': 15.478052380633539}
- Codegen final values: {'X_Integrator': -8.633946, 'Y_Integrator': -15.582092, 'Z_Integrator': 13.635816}
