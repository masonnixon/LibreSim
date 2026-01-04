# Codegen Validation Report

This report compares the outputs of generated code against the headless simulation.

## Summary

| Example | Python | C++ | C | Rust |
|---------|--------|-----|---|------|
| 01_sine_wave_basic | PASS | PASS | PASS | PASS |
| 02_first_order_step_response | PASS | PASS | PASS | PASS |
| 03_pid_controller | PASS | PASS | PASS | PASS |
| 04_mass_spring_damper | PASS | DIFF (3.84%) | DIFF (3.84%) | DIFF (100.00%) |
| 04b_mass_spring_damper_underdamped | PASS | DIFF (19.06%) | DIFF (19.06%) | DIFF (19.06%) |
| 05a_moving_average_filter | PASS | PASS | PASS | PASS |
| 05b_lowpass_filter | PASS | PASS | PASS | PASS |
| 06_kalman_filter_estimation | PASS | PASS | PASS | PASS |
| 06b_kalman_position_velocity | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 07_thermostat_relay_control | PASS | PASS | PASS | PASS |
| 07a_bode_plot_analysis | PASS | PASS | PASS | PASS |
| 07b_nyquist_plot_analysis | PASS | PASS | PASS | PASS |
| 07c_pole_zero_map | PASS | PASS | PASS | PASS |
| 07d_step_response_info | PASS | PASS | PASS | PASS |
| 08_lookup_table_nonlinear | PASS | PASS | PASS | PASS |
| 09_second_order_damping | PASS | PASS | PASS | PASS |
| 10_rate_limiting_quantization | PASS | DIFF (6.28%) | DIFF (6.28%) | DIFF (6.28%) |
| 11_vector_signal_processing | PASS | PASS | PASS | PASS |
| 20_quaternion_attitude_propagation | PASS | PASS | PASS | PASS |
| 21_isa_atmosphere_model | PASS | PASS | PASS | PASS |
| 22_gravity_models_comparison | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 23_dcm_quaternion_conversion | PASS | PASS | PASS | PASS |
| 24_quaternion_vector_rotation | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 30_pid_speed_control | DIFF (19.94%) | DIFF (126010.09%) | DIFF (126010.09%) | DIFF (126010.09%) |
| 31_discrete_pid_sampled_control | PASS | PASS | PASS | PASS |
| 32_lqr_state_feedback | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 33_lead_lag_compensator | PASS | PASS | PASS | PASS |
| 34_anti_windup_pid | PASS | PASS | PASS | PASS |
| 35_pi_pd_controllers | PASS | PASS | PASS | PASS |
| 36_model_reference_control | PASS | PASS | PASS | PASS |
| 37_pole_placement_control | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 40_dsp_fft_spectrum | PASS | PASS | PASS | PASS |
| 41_dsp_fir_lowpass | DIFF (725.68%) | DIFF (1035.04%) | DIFF (949.68%) | DIFF (949.68%) |
| 42_rf_receiver_chain | PASS | PASS | PASS | PASS |
| 43_rf_am_modulation | PASS | PASS | PASS | PASS |
| 44_nav_coordinate_transform | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 45_sensor_fusion_ahrs | PASS | BUILD FAIL | BUILD FAIL | BUILD FAIL |
| 46_sensor_fusion_tracking | PASS | PASS | PASS | PASS |

## Statistics

- Total tests: 152
- Passed: 114 (75.0%)
- Build failures: 21
- Run failures: 0
- Value mismatches: 17

## Detailed Failures

### 04_mass_spring_damper (cpp)

- Max relative error: 3.8413%
- Headless final values: {'Velocity': 2.0978867972592176e-09, 'Position': 0.9999999998138548}
- Codegen final values: {'Velocity': 2.0173e-09, 'Position': 1.0}

### 04_mass_spring_damper (c)

- Max relative error: 3.8413%
- Headless final values: {'Velocity': 2.0978867972592176e-09, 'Position': 0.9999999998138548}
- Codegen final values: {'Velocity': 2.0173e-09, 'Position': 1.0}

### 04_mass_spring_damper (rust)

- Max relative error: 100.0000%
- Headless final values: {'Velocity': 2.0978867972592176e-09, 'Position': 0.9999999998138548}
- Codegen final values: {'Velocity': 0.0, 'Position': 1.0}

### 04b_mass_spring_damper_underdamped (cpp)

- Max relative error: 19.0593%
- Headless final values: {'Velocity': -0.034037745582229564, 'Position': 0.9945076254268891}
- Codegen final values: {'Velocity': -0.0405251, 'Position': 0.992182}

### 04b_mass_spring_damper_underdamped (c)

- Max relative error: 19.0593%
- Headless final values: {'Velocity': -0.034037745582229564, 'Position': 0.9945076254268891}
- Codegen final values: {'Velocity': -0.0405251, 'Position': 0.992182}

### 04b_mass_spring_damper_underdamped (rust)

- Max relative error: 19.0590%
- Headless final values: {'Velocity': -0.034037745582229564, 'Position': 0.9945076254268891}
- Codegen final values: {'Velocity': -0.040525, 'Position': 0.992182}

### 06b_kalman_position_velocity (cpp)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 746B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 06b_kalman_position_velocity (c)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 722B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 06b_kalman_position_velocity (rust)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 542B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 10_rate_limiting_quantization (cpp)

- Max relative error: 6.2830%
- Headless final values: {'Command': -1.3791876954540827e-11, 'Rate Limiter': -1.3791876954540827e-11, 'Quantizer': 0.0, 'Then Quant': 0.0}
- Codegen final values: {'Command': -0.0628302, 'Rate_Limiter': -1.10257, 'Quantizer': -0.0, 'Then_Quant': -1.0}

### 10_rate_limiting_quantization (c)

- Max relative error: 6.2830%
- Headless final values: {'Command': -1.3791876954540827e-11, 'Rate Limiter': -1.3791876954540827e-11, 'Quantizer': 0.0, 'Then Quant': 0.0}
- Codegen final values: {'Command': -0.0628302, 'Rate_Limiter': -1.10257, 'Quantizer': -0.0, 'Then_Quant': -1.0}

### 10_rate_limiting_quantization (rust)

- Max relative error: 6.2830%
- Headless final values: {'Command': -1.3791876954540827e-11, 'Rate Limiter': -1.3791876954540827e-11, 'Quantizer': 0.0, 'Then Quant': 0.0}
- Codegen final values: {'Command': -0.06283, 'Rate_Limiter': -1.102566, 'Quantizer': -0.0, 'Then_Quant': -1.0}

### 22_gravity_models_comparison (cpp)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 746B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 22_gravity_models_comparison (c)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 722B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 22_gravity_models_comparison (rust)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 542B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 24_quaternion_vector_rotation (cpp)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 748B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 24_quaternion_vector_rotation (c)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 724B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 24_quaternion_vector_rotation (rust)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 544B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 30_pid_speed_control (python)

- Max relative error: 19.9362%
- Headless final values: {'Speed Setpoint': 100.0, 'DC Motor': 99.92466899212954, 'Actuator Limits': 19.990832132866167, 'Error': 0.0753310078704601}
- Codegen final values: {'Speed_Setpoint': 100.0, 'DC_Motor': 99.90965082892927, 'Control_Signal': 20.00107666518958, 'Error': 0.09034917107072715}

### 30_pid_speed_control (cpp)

- Max relative error: 126010.0876%
- Headless final values: {'Speed Setpoint': 100.0, 'DC Motor': 99.92466899212954, 'Actuator Limits': 19.990832132866167, 'Error': 0.0753310078704601}
- Codegen final values: {'Speed_Setpoint': 100.0, 'DC_Motor': 5.0, 'Control_Signal': 1.0, 'Error': 95.0}

### 30_pid_speed_control (c)

- Max relative error: 126010.0876%
- Headless final values: {'Speed Setpoint': 100.0, 'DC Motor': 99.92466899212954, 'Actuator Limits': 19.990832132866167, 'Error': 0.0753310078704601}
- Codegen final values: {'Speed_Setpoint': 100.0, 'DC_Motor': 5.0, 'Control_Signal': 1.0, 'Error': 95.0}

### 30_pid_speed_control (rust)

- Max relative error: 126010.0876%
- Headless final values: {'Speed Setpoint': 100.0, 'DC Motor': 99.92466899212954, 'Actuator Limits': 19.990832132866167, 'Error': 0.0753310078704601}
- Codegen final values: {'Speed_Setpoint': 100.0, 'DC_Motor': 5.0, 'Control_Signal': 1.0, 'Error': 95.0}

### 32_lqr_state_feedback (cpp)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 732B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 32_lqr_state_feedback (c)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 708B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 32_lqr_state_feedback (rust)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 528B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 37_pole_placement_control (cpp)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 740B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 37_pole_placement_control (c)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 716B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 37_pole_placement_control (rust)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 536B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 41_dsp_fir_lowpass (python)

- Max relative error: 725.6766%
- Headless final values: {'Add Noise': 0.0, 'FIR Lowpass': 0.0, 'Running Mean': 0.0, 'RMS': 0.0}
- Codegen final values: {'Add_Noise': -10.47574445724693, 'FIR_Lowpass': 2.529173827296244, 'Running_Mean': -2.676777972355227, 'RMS': 7.256765649722918}

### 41_dsp_fir_lowpass (cpp)

- Max relative error: 1035.0400%
- Headless final values: {'Add Noise': 0.0, 'FIR Lowpass': 0.0, 'Running Mean': 0.0, 'RMS': 0.0}
- Codegen final values: {'Add_Noise': 10.8822, 'FIR_Lowpass': 12.3047, 'Running_Mean': 3.2493, 'RMS': 10.3504}

### 41_dsp_fir_lowpass (c)

- Max relative error: 949.6790%
- Headless final values: {'Add Noise': 0.0, 'FIR Lowpass': 0.0, 'Running Mean': 0.0, 'RMS': 0.0}
- Codegen final values: {'Add_Noise': -4.08612, 'FIR_Lowpass': -5.54126, 'Running_Mean': 2.05292, 'RMS': 9.49679}

### 41_dsp_fir_lowpass (rust)

- Max relative error: 949.6792%
- Headless final values: {'Add Noise': 0.0, 'FIR Lowpass': 0.0, 'Running Mean': 0.0, 'RMS': 0.0}
- Codegen final values: {'Add_Noise': -4.086119, 'FIR_Lowpass': -5.541262, 'Running_Mean': 2.052916, 'RMS': 9.496792}

### 44_nav_coordinate_transform (cpp)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 744B 0.0s done
#1 DONE 0.1s

#2 [internal] load metadata for do

### 44_nav_coordinate_transform (c)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 720B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 44_nav_coordinate_transform (rust)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 540B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 45_sensor_fusion_ahrs (cpp)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 732B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 45_sensor_fusion_ahrs (c)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 708B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do

### 45_sensor_fusion_ahrs (rust)

- Build failed: #0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 528B 0.0s done
#1 DONE 0.0s

#2 [internal] load metadata for do
