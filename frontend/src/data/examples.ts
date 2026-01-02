/**
 * Example models - metadata and API-based loading
 *
 * Examples are stored as JSON files in the examples/ directory and loaded
 * via the backend API. This file provides types and utility functions.
 */

import type { Model } from '../types/model'
import { api } from '../api/client'

export interface ExampleInfo {
  id: string
  name: string
  description: string
  category: 'basic' | 'control' | 'signal' | 'advanced' | 'aerospace' | 'control_design' | 'dsp' | 'rf' | 'navigation' | 'sensor_fusion'
}

// Cache for loaded examples
const exampleCache = new Map<string, Model>()

/**
 * Fetch the list of available examples from the API.
 * Falls back to embedded list if API fails.
 */
export async function fetchExampleList(): Promise<ExampleInfo[]> {
  try {
    const examples = await api.getExampleList()
    return examples as ExampleInfo[]
  } catch (error) {
    console.error('Failed to fetch example list from API, using fallback:', error)
    return FALLBACK_EXAMPLE_LIST
  }
}

/**
 * Fetch a specific example model from the API.
 * Uses caching to avoid repeated API calls.
 */
export async function fetchExample(id: string): Promise<Model | undefined> {
  // Check cache first
  if (exampleCache.has(id)) {
    return exampleCache.get(id)
  }

  try {
    const model = await api.getExample(id)
    exampleCache.set(id, model)
    return model
  } catch (error) {
    console.error(`Failed to fetch example '${id}':`, error)
    return undefined
  }
}

/**
 * Clear the example cache (useful for testing or when examples might have changed)
 */
export function clearExampleCache(): void {
  exampleCache.clear()
}

// Fallback example list in case the API is not available
// This ensures the UI can still show examples even if the backend is down
const FALLBACK_EXAMPLE_LIST: ExampleInfo[] = [
  { id: '01_sine_wave_basic', name: 'Sine Wave Basic', description: 'Basic sine wave visualization', category: 'basic' },
  { id: '02_first_order_step_response', name: 'First-Order Step Response', description: 'First-order system step response', category: 'basic' },
  { id: '03_pid_controller', name: 'PID Controller', description: 'PID control of second-order plant', category: 'control' },
  { id: '04_mass_spring_damper', name: 'Mass-Spring-Damper (Simscape)', description: 'Overdamped mechanical system (Simscape defaults)', category: 'control' },
  { id: '04b_mass_spring_damper_underdamped', name: 'Mass-Spring-Damper (Underdamped)', description: 'Oscillatory mechanical system for teaching', category: 'control' },
  { id: '05a_moving_average_filter', name: 'Moving Average Filter', description: 'AWGN noise smoothing with different window sizes', category: 'signal' },
  { id: '05b_lowpass_filter', name: 'Low-Pass Filter Comparison', description: 'Compare 1st-order LPF with higher-order Butterworth/Bessel', category: 'signal' },
  { id: '06_kalman_filter_estimation', name: 'Kalman Filter', description: 'State estimation with Kalman filter', category: 'advanced' },
  { id: '06b_kalman_position_velocity', name: 'Kalman Position/Velocity', description: 'Hidden state estimation (velocity from position)', category: 'advanced' },
  { id: '07_thermostat_relay_control', name: 'Thermostat Relay', description: 'Bang-bang/relay control', category: 'control' },
  { id: '07a_bode_plot_analysis', name: 'Bode Plot Analysis', description: 'Frequency response analysis with magnitude and phase plots', category: 'control' },
  { id: '07b_nyquist_plot_analysis', name: 'Nyquist Plot Analysis', description: 'Stability analysis via Nyquist diagram', category: 'control' },
  { id: '07c_pole_zero_map', name: 'Pole-Zero Map', description: 'System stability via pole-zero locations', category: 'control' },
  { id: '07d_step_response_info', name: 'Step Response Info', description: 'Time-domain step response characteristics', category: 'control' },
  { id: '08_lookup_table_nonlinear', name: 'Lookup Table - Motor Curve', description: 'Motor torque/efficiency curves via lookup tables', category: 'signal' },
  { id: '09_second_order_damping', name: 'Second-Order Damping', description: 'Damping ratio comparison', category: 'basic' },
  { id: '10_rate_limiting_quantization', name: 'Rate Limiting', description: 'Rate limiter and quantization effects', category: 'signal' },
  { id: '11_vector_signal_processing', name: 'Vector Signal Processing', description: '3D vector operations with Mux, Demux, and element-wise math', category: 'advanced' },
  // Aerospace Blockset
  { id: '20_quaternion_attitude_propagation', name: 'Quaternion Attitude Propagation', description: 'Spacecraft attitude dynamics with quaternion integration', category: 'aerospace' },
  { id: '21_isa_atmosphere_model', name: 'ISA Atmosphere Model', description: 'Standard atmosphere properties vs altitude', category: 'aerospace' },
  { id: '22_gravity_models_comparison', name: 'Gravity Models Comparison', description: 'WGS84 vs flat Earth gravity models', category: 'aerospace' },
  { id: '23_dcm_quaternion_conversion', name: 'DCM/Quaternion Conversion', description: 'Direction cosine matrix and quaternion conversions', category: 'aerospace' },
  { id: '24_quaternion_vector_rotation', name: 'Quaternion Vector Rotation', description: 'Rotating vectors using quaternion operations', category: 'aerospace' },
  // Control Design
  { id: '30_pid_speed_control', name: 'PID Speed Control', description: 'Motor speed control with tuned PID controller', category: 'control_design' },
  { id: '31_discrete_pid_sampled_control', name: 'Discrete PID Sampled Control', description: 'Discrete-time PID with sample-hold effects', category: 'control_design' },
  { id: '32_lqr_state_feedback', name: 'LQR State Feedback', description: 'Optimal LQR control with state feedback', category: 'control_design' },
  { id: '33_lead_lag_compensator', name: 'Lead-Lag Compensator', description: 'Phase compensation for improved transient response', category: 'control_design' },
  { id: '34_anti_windup_pid', name: 'Anti-Windup PID', description: 'PID with back-calculation anti-windup', category: 'control_design' },
  { id: '35_pi_pd_controllers', name: 'PI vs PD Controllers', description: 'Comparing PI and PD controller characteristics', category: 'control_design' },
  { id: '36_model_reference_control', name: 'Model Reference Control', description: 'Tracking control with reference model', category: 'control_design' },
  { id: '37_pole_placement_control', name: 'Pole Placement Control', description: 'State feedback with pole placement design', category: 'control_design' },
  // DSP Toolbox
  { id: '40_dsp_fft_spectrum', name: 'FFT Spectrum Analysis', description: 'Composite signal windowing and FFT frequency analysis', category: 'dsp' },
  { id: '41_dsp_fir_lowpass', name: 'FIR Lowpass Filter', description: 'Digital FIR filtering with running statistics', category: 'dsp' },
  // RF Blockset
  { id: '42_rf_receiver_chain', name: 'RF Receiver Chain', description: 'Cascaded RF budget analysis with Friis noise figure', category: 'rf' },
  { id: '43_rf_am_modulation', name: 'AM Modulation', description: 'Amplitude modulation of carrier signal', category: 'rf' },
  // Navigation Toolbox
  { id: '44_nav_coordinate_transform', name: 'Coordinate Transformations', description: 'LLA to ECEF to NED with great circle distance', category: 'navigation' },
  // Sensor Fusion Toolbox
  { id: '45_sensor_fusion_ahrs', name: 'AHRS Attitude Estimation', description: 'IMU sensor fusion with Madgwick and Complementary filters', category: 'sensor_fusion' },
  { id: '46_sensor_fusion_tracking', name: 'Alpha-Beta-Gamma Tracking', description: 'Position/velocity/acceleration tracking filter comparison', category: 'sensor_fusion' },
]

// For backwards compatibility - sync access to the example list
// This is used by components that haven't been updated to use async loading yet
export const exampleList: ExampleInfo[] = FALLBACK_EXAMPLE_LIST

// Deprecated: Use fetchExample instead. This is kept for backwards compatibility.
// Returns undefined since examples are no longer embedded.
export function getExample(_id: string): undefined {
  console.warn('getExample is deprecated. Use fetchExample instead for async loading.')
  return undefined
}
