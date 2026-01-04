"""OSK Adapter - Interface to the Object-oriented Simulation Kernel.

This module provides the bridge between LibreSim's compiled model and OSK's
simulation engine. It creates OSK block instances and manages simulation execution.
"""

import inspect
from typing import Any

from ..models.simulation import SimulationConfig, SolverType

# Import OSK components
from ..osk import Block, Sim, State
from ..osk.blocks import (
    Abs,
    AnalogFilter,
    Backlash,
    BandPassFilter,
    # Control Analysis
    BodePlot,
    Clock,
    # Sources
    Constant,
    Coulomb,
    Derivative,
    ExtendedKalmanFilter,
    Gain,
    HighPassFilter,
    # Subsystems
    Inport,
    # Continuous
    Integrator,
    LimitedIntegrator,
    SecondOrder,
    TransportDelay,
    ZeroPole,
    KalmanFilter,
    # Nonlinear
    HitCrossing,
    Hysteresis,
    LookupTable1D,
    LookupTable2D,
    LowPassFilter,
    SlewRateLimiter,
    Stiction,
    WrapToRange,
    # Observers
    LuenbergerObserver,
    MovingAverage,
    NotchFilter,
    NyquistPlot,
    Outport,
    PIDController,
    PoleZeroMap,
    Product,
    Quantizer,
    Ramp,
    # Signal Processing
    RateLimiter,
    Relay,
    Saturation,
    # Sinks
    Scope,
    SineWave,
    StateSpace,
    Step,
    StepInfo,
    Subsystem,
    # Math
    Sum,
    ToWorkspace,
    TransferFunction,
    # Discrete
    UnitDelay,
    VariableTransportDelay,
    ZeroOrderHold,
)
from ..osk.blocks.discrete import (
    DiscreteDerivative,
    DiscreteIntegrator,
    DiscretePIDController,
    DiscreteStateSpace,
    DiscreteTransferFunction,
    FirstOrderHold,
    Memory,
)
from ..osk.blocks.logic import (
    BitOperator,
    CompareToConstant,
    CompareToZero,
    LogicalOperator,
    RelationalOperator,
)
from ..osk.blocks.math_ops import (
    Atan2,
    Bias,
    ComplexToMagnitudeAngle,
    CrossProduct,
    DeadZone,
    Demux,
    Divide,
    DotProduct,
    Exp,
    Hypot,
    Log,
    Log10,
    MagnitudeAngle,
    MathFunction,
    MinMax,
    Mod,
    Mux,
    Polynomial,
    Power,
    Reciprocal,
    Reshape,
    Rounding,
    Sign,
    SliderGain,
    Sqrt,
    Square,
    Switch,
    Trigonometry,
    UnaryMinus,
    WeightedSum,
)
from ..osk.blocks.data_types import (
    DataTypeConversion,
    RealImagToComplex,
    ComplexToRealImag,
)
from ..osk.blocks.matrix_ops import (
    MatrixMultiply,
    MatrixTranspose,
    MatrixInverse,
    Selector,
    Assignment,
    Concatenate,
    MatrixSum,
    VectorNorm,
)
from ..osk.blocks.control_design import (
    LQRController,
    PolePlacement,
    LeadLagCompensator,
    PIController,
    PDController,
    AntiWindupPID,
    ModelReference,
)
from ..osk.blocks.aerospace import (
    QuaternionNormalize,
    QuaternionMultiply,
    QuaternionConjugate,
    QuaternionToEuler,
    EulerToQuaternion,
    QuaternionRotateVector,
    DCMToQuaternion,
    QuaternionToDCM,
    ISAAtmosphere,
    SixDOFEuler,
    FlatEarthGravity,
    WGS84Gravity,
)
from ..osk.blocks.dsp import (
    FFT,
    IFFT,
    FIRFilter,
    IIRFilter,
    Convolution,
    Downsampler,
    Upsampler,
    Interpolator,
    WindowFunction,
    Mean,
    Variance,
    RMS,
    PeakDetector,
    ZeroCrossingDetector,
)
from ..osk.blocks.rf import (
    RFAmplifier,
    RFMixer,
    RFFilter,
    SParameterNetwork,
    RFBudgetElement,
    Attenuator,
    AMModulator,
    FMModulator,
    PhaseNoise,
    dBmToWatts,
    WattsTodBm,
)
from ..osk.blocks.navigation import (
    CoordinateTransformationConversion,
    LLAToECEF,
    ECEFToLLA,
    ECEFToNED,
    NEDToECEF,
    WaypointFollower,
    GreatCircleDistance,
    FlatEarthPosition,
)
from ..osk.blocks.sensor_fusion import (
    IMUSensor,
    Accelerometer,
    Gyroscope,
    Magnetometer,
    GPSSensor,
    Altimeter,
    ComplementaryFilter,
    MadgwickFilter,
    MahonyFilter,
    INSGPSFusion,
    AlphaBetaFilter,
    AlphaBetaGammaFilter,
)
from ..osk.blocks.sinks import Display, Terminator
from ..osk.blocks.sources import (
    BandLimitedWhiteNoise,
    ChirpSignal,
    FromWorkspace,
    Ground,
    PulseGenerator,
    RepeatingSequence,
    SignalGenerator,
    UniformNoise,
    WhiteNoise,
)
from .compiler import CompiledBlock, CompiledModel

# Mapping from LibreSim block types to OSK block classes
BLOCK_TYPE_MAP: dict[str, type[Block]] = {
    # Sources
    "constant": Constant,
    "step": Step,
    "ramp": Ramp,
    "sine_wave": SineWave,
    "pulse_generator": PulseGenerator,
    "clock": Clock,
    "white_noise": WhiteNoise,
    "uniform_noise": UniformNoise,
    "repeating_sequence": RepeatingSequence,
    "chirp_signal": ChirpSignal,
    "band_limited_white_noise": BandLimitedWhiteNoise,
    "ground": Ground,
    "from_workspace": FromWorkspace,
    "signal_generator": SignalGenerator,
    # Sinks
    "scope": Scope,
    "display": Display,
    "to_workspace": ToWorkspace,
    "terminator": Terminator,
    # Continuous
    "integrator": Integrator,
    "derivative": Derivative,
    "transfer_function": TransferFunction,
    "state_space": StateSpace,
    "pid_controller": PIDController,
    "transport_delay": TransportDelay,
    "second_order": SecondOrder,
    "limited_integrator": LimitedIntegrator,
    "zero_pole": ZeroPole,
    # Discrete
    "unit_delay": UnitDelay,
    "zero_order_hold": ZeroOrderHold,
    "discrete_integrator": DiscreteIntegrator,
    "discrete_derivative": DiscreteDerivative,
    "discrete_transfer_function": DiscreteTransferFunction,
    "memory": Memory,
    "discrete_state_space": DiscreteStateSpace,
    "first_order_hold": FirstOrderHold,
    "discrete_pid_controller": DiscretePIDController,
    # Math
    "sum": Sum,
    "gain": Gain,
    "product": Product,
    "abs": Abs,
    "sign": Sign,
    "bias": Bias,
    "saturation": Saturation,
    "dead_zone": DeadZone,
    "math_function": MathFunction,
    "trigonometry": Trigonometry,
    "switch": Switch,
    "mux": Mux,
    "demux": Demux,
    "reshape": Reshape,
    "divide": Divide,
    "mod": Mod,
    "atan2": Atan2,
    "rounding": Rounding,
    "minmax": MinMax,
    "dot_product": DotProduct,
    "cross_product": CrossProduct,
    "hypot": Hypot,
    "unary_minus": UnaryMinus,
    "slider_gain": SliderGain,
    "weighted_sum": WeightedSum,
    "polynomial": Polynomial,
    "magnitude_angle": MagnitudeAngle,
    "complex_to_magnitude_angle": ComplexToMagnitudeAngle,
    "sqrt": Sqrt,
    "reciprocal": Reciprocal,
    "square": Square,
    "power": Power,
    "exp": Exp,
    "log": Log,
    "log10": Log10,
    # Logic
    "compare_to_zero": CompareToZero,
    "compare_to_constant": CompareToConstant,
    "relational_operator": RelationalOperator,
    "logical_operator": LogicalOperator,
    "bit_operator": BitOperator,
    # Subsystems
    "inport": Inport,
    "outport": Outport,
    "subsystem": Subsystem,
    # Signal Processing
    "rate_limiter": RateLimiter,
    "moving_average": MovingAverage,
    "low_pass_filter": LowPassFilter,
    "high_pass_filter": HighPassFilter,
    "band_pass_filter": BandPassFilter,
    "analog_filter": AnalogFilter,
    "notch_filter": NotchFilter,
    "backlash": Backlash,
    # Nonlinear
    "lookup_table_1d": LookupTable1D,
    "lookup_table_2d": LookupTable2D,
    "quantizer": Quantizer,
    "relay": Relay,
    "coulomb_friction": Coulomb,
    "variable_transport_delay": VariableTransportDelay,
    "wrap_to_range": WrapToRange,
    "hit_crossing": HitCrossing,
    "hysteresis": Hysteresis,
    "stiction": Stiction,
    "slew_rate_limiter": SlewRateLimiter,
    # Observers
    "luenberger_observer": LuenbergerObserver,
    "kalman_filter": KalmanFilter,
    "extended_kalman_filter": ExtendedKalmanFilter,
    # Control Analysis
    "bode_plot": BodePlot,
    "nyquist_plot": NyquistPlot,
    "pole_zero_map": PoleZeroMap,
    "step_info": StepInfo,
    # Data Types
    "data_type_conversion": DataTypeConversion,
    "real_imag_to_complex": RealImagToComplex,
    "complex_to_real_imag": ComplexToRealImag,
    # Matrix Operations
    "matrix_multiply": MatrixMultiply,
    "matrix_transpose": MatrixTranspose,
    "matrix_inverse": MatrixInverse,
    "selector": Selector,
    "assignment": Assignment,
    "concatenate": Concatenate,
    "matrix_sum": MatrixSum,
    "vector_norm": VectorNorm,
    # Control Design
    "lqr_controller": LQRController,
    "pole_placement": PolePlacement,
    "lead_lag_compensator": LeadLagCompensator,
    "pi_controller": PIController,
    "pd_controller": PDController,
    "anti_windup_pid": AntiWindupPID,
    "model_reference": ModelReference,
    # Aerospace
    "quaternion_normalize": QuaternionNormalize,
    "quaternion_multiply": QuaternionMultiply,
    "quaternion_conjugate": QuaternionConjugate,
    "quaternion_to_euler": QuaternionToEuler,
    "euler_to_quaternion": EulerToQuaternion,
    "quaternion_rotate_vector": QuaternionRotateVector,
    "dcm_to_quaternion": DCMToQuaternion,
    "quaternion_to_dcm": QuaternionToDCM,
    "isa_atmosphere": ISAAtmosphere,
    "six_dof_euler": SixDOFEuler,
    "flat_earth_gravity": FlatEarthGravity,
    "wgs84_gravity": WGS84Gravity,
    # DSP
    "fft": FFT,
    "ifft": IFFT,
    "fir_filter": FIRFilter,
    "iir_filter": IIRFilter,
    "convolution": Convolution,
    "downsampler": Downsampler,
    "upsampler": Upsampler,
    "interpolator": Interpolator,
    "window_function": WindowFunction,
    "mean": Mean,
    "variance": Variance,
    "rms": RMS,
    "peak_detector": PeakDetector,
    "zero_crossing_detector": ZeroCrossingDetector,
    # RF
    "rf_amplifier": RFAmplifier,
    "rf_mixer": RFMixer,
    "rf_filter": RFFilter,
    "s_parameter_network": SParameterNetwork,
    "rf_budget_element": RFBudgetElement,
    "attenuator": Attenuator,
    "am_modulator": AMModulator,
    "fm_modulator": FMModulator,
    "phase_noise": PhaseNoise,
    "dbm_to_watts": dBmToWatts,
    "watts_to_dbm": WattsTodBm,
    # Navigation
    "coordinate_transformation": CoordinateTransformationConversion,
    "lla_to_ecef": LLAToECEF,
    "ecef_to_lla": ECEFToLLA,
    "ecef_to_ned": ECEFToNED,
    "ned_to_ecef": NEDToECEF,
    "waypoint_follower": WaypointFollower,
    "great_circle_distance": GreatCircleDistance,
    "flat_earth_position": FlatEarthPosition,
    # Sensor Fusion
    "imu_sensor": IMUSensor,
    "accelerometer": Accelerometer,
    "gyroscope": Gyroscope,
    "magnetometer": Magnetometer,
    "gps_sensor": GPSSensor,
    "altimeter": Altimeter,
    "complementary_filter": ComplementaryFilter,
    "madgwick_filter": MadgwickFilter,
    "mahony_filter": MahonyFilter,
    "ins_gps_fusion": INSGPSFusion,
    "alpha_beta_filter": AlphaBetaFilter,
    "alpha_beta_gamma_filter": AlphaBetaGammaFilter,
}

# Parameter name mapping from LibreSim to OSK constructor arguments
PARAM_MAP: dict[str, dict[str, str]] = {
    "constant": {"value": "value"},
    "step": {"stepTime": "step_time", "initialValue": "initial_value", "finalValue": "final_value"},
    "ramp": {"slope": "slope", "startTime": "start_time", "initialOutput": "initial_output"},
    "sine_wave": {"amplitude": "amplitude", "frequency": "frequency", "phase": "phase", "bias": "bias"},
    "pulse_generator": {"amplitude": "amplitude", "period": "period", "dutyCycle": "duty_cycle", "phaseDelay": "phase_delay"},
    "white_noise": {"mean": "mean", "variance": "variance", "power": "variance", "seed": "seed", "sampleTime": "sample_time"},
    "uniform_noise": {"minimum": "minimum", "maximum": "maximum", "seed": "seed", "sampleTime": "sample_time"},
    "scope": {"numInputs": "num_inputs", "num_input_ports": "num_inputs"},
    "to_workspace": {"variableName": "variable_name"},
    "integrator": {"initialCondition": "initial_condition", "limitOutput": "limit_output", "upperLimit": "upper_limit", "lowerLimit": "lower_limit", "externalIC": "external_ic"},
    "derivative": {"coefficient": "coefficient"},
    "transfer_function": {"numerator": "numerator", "denominator": "denominator"},
    "state_space": {"A": "A", "B": "B", "C": "C", "D": "D", "initialCondition": "initial_state"},
    "pid_controller": {"Kp": "Kp", "Ki": "Ki", "Kd": "Kd", "N": "N", "initialConditionI": "initial_integrator"},
    "transport_delay": {"delayTime": "delay_time", "initialOutput": "initial_output"},
    "second_order": {"naturalFrequency": "natural_frequency", "dampingRatio": "damping_ratio", "gain": "gain"},
    "limited_integrator": {"initialCondition": "initial_condition", "upperLimit": "upper_limit", "lowerLimit": "lower_limit"},
    "zero_pole": {"zeros": "zeros", "poles": "poles", "gain": "gain"},
    "unit_delay": {"initialCondition": "initial_condition", "sampleTime": "sample_time"},
    "zero_order_hold": {"sampleTime": "sample_time"},
    "discrete_integrator": {"method": "method", "sampleTime": "sample_time", "initialCondition": "initial_condition"},
    "discrete_derivative": {"sampleTime": "sample_time", "initialCondition": "initial_condition"},
    "discrete_transfer_function": {"numerator": "numerator", "denominator": "denominator", "sampleTime": "sample_time"},
    "sum": {"signs": "signs", "inputs": "signs"},
    "gain": {"gain": "gain"},
    "product": {"operations": "operations"},
    "bias": {"bias": "bias"},
    "saturation": {"upperLimit": "upper_limit", "lowerLimit": "lower_limit"},
    "dead_zone": {"start": "start", "end": "end"},
    "math_function": {"function": "function", "exponent": "exponent"},
    "trigonometry": {"function": "function"},
    "switch": {"threshold": "threshold", "criteria": "criteria"},
    "mux": {"numInputs": "num_inputs"},
    "demux": {"numOutputs": "num_outputs"},
    "reshape": {"outputDimensions": "output_dimensions"},
    "minmax": {"function": "function", "numInputs": "num_inputs"},
    "rounding": {"function": "mode"},
    "slider_gain": {"gain": "gain", "min": "min_val", "max": "max_val"},
    "weighted_sum": {"weights": "weights"},
    "polynomial": {"coefficients": "coefficients"},
    # Logic
    "compare_to_zero": {"operator": "operator"},
    "compare_to_constant": {"constant": "constant", "operator": "operator"},
    "relational_operator": {"operator": "operator"},
    "logical_operator": {"operator": "operator", "numInputs": "num_inputs"},
    "bit_operator": {"operator": "operator"},
    # New Sources
    "repeating_sequence": {"timeValues": "time_values", "outputValues": "output_values"},
    "chirp_signal": {"initialFrequency": "initial_frequency", "targetTime": "target_time", "targetFrequency": "target_frequency"},
    "band_limited_white_noise": {"noisePower": "noise_power", "sampleTime": "sample_time", "seed": "seed"},
    "from_workspace": {"timeData": "time_data", "valueData": "value_data", "interpolation": "interpolation"},
    "signal_generator": {"waveType": "wave_type", "amplitude": "amplitude", "frequency": "frequency", "units": "units"},
    # New Discrete
    "memory": {"initialCondition": "initial_condition"},
    "discrete_state_space": {"A": "A", "B": "B", "C": "C", "D": "D", "initialState": "initial_state", "sampleTime": "sample_time"},
    "first_order_hold": {"sampleTime": "sample_time"},
    "discrete_pid_controller": {"Kp": "Kp", "Ki": "Ki", "Kd": "Kd", "N": "N", "sampleTime": "sample_time", "method": "method"},
    # Subsystems
    "inport": {"portNumber": "port_number"},
    "outport": {"portNumber": "port_number"},
    "subsystem": {"numInputs": "num_inputs", "numOutputs": "num_outputs"},
    # Signal Processing
    "rate_limiter": {"risingLimit": "rising_limit", "fallingLimit": "falling_limit"},
    "moving_average": {"windowSize": "window_size"},
    "low_pass_filter": {"cutoffFrequency": "cutoff_freq"},
    "high_pass_filter": {"cutoffFrequency": "cutoff_freq"},
    "band_pass_filter": {"lowCutoff": "low_cutoff", "highCutoff": "high_cutoff"},
    "analog_filter": {
        "design": "design", "response": "response", "order": "order",
        "cutoffFrequency": "cutoff_freq", "lowCutoff": "low_cutoff", "highCutoff": "high_cutoff",
        "passbandRipple": "passband_ripple", "stopbandAtten": "stopband_atten"
    },
    "notch_filter": {"notchFrequency": "notch_freq", "bandwidth": "bandwidth", "depth": "depth"},
    "backlash": {"deadbandWidth": "deadband_width", "initialOutput": "initial_output"},
    # Nonlinear
    "lookup_table_1d": {"xData": "x_data", "yData": "y_data"},
    "lookup_table_2d": {"xData": "x_data", "yData": "y_data", "zData": "z_data"},
    "quantizer": {"interval": "interval"},
    "relay": {"switchOn": "switch_on", "switchOff": "switch_off", "outputOn": "output_on", "outputOff": "output_off"},
    "coulomb_friction": {"staticGain": "static_gain", "dynamicGain": "dynamic_gain", "velocityThreshold": "velocity_threshold"},
    "variable_transport_delay": {"maxDelay": "max_delay", "initialDelay": "initial_delay"},
    "wrap_to_range": {"lower": "lower", "upper": "upper"},
    "hit_crossing": {"threshold": "threshold", "direction": "direction"},
    "hysteresis": {"upperThreshold": "upper_threshold", "lowerThreshold": "lower_threshold", "outputHigh": "output_high", "outputLow": "output_low"},
    "stiction": {"breakawayForce": "breakaway_force", "velocityThreshold": "velocity_threshold"},
    "slew_rate_limiter": {"risingRate": "rising_rate", "fallingRate": "falling_rate", "sampleTime": "sample_time"},
    # Observers
    "luenberger_observer": {"A": "A", "B": "B", "C": "C", "L": "L", "initialState": "initial_state"},
    "kalman_filter": {"A": "A", "B": "B", "C": "C", "Q": "Q", "R": "R", "initialState": "initial_state", "initialP": "initial_P"},
    "extended_kalman_filter": {"nStates": "n_states", "Q": "Q", "R": "R", "initialState": "initial_state"},
    # Control Analysis
    "bode_plot": {"numerator": "numerator", "denominator": "denominator", "minFrequency": "minFrequency", "maxFrequency": "maxFrequency", "numPoints": "numPoints"},
    "nyquist_plot": {"numerator": "numerator", "denominator": "denominator", "minFrequency": "minFrequency", "maxFrequency": "maxFrequency", "numPoints": "numPoints"},
    "pole_zero_map": {"numerator": "numerator", "denominator": "denominator"},
    "step_info": {"numerator": "numerator", "denominator": "denominator", "simulationTime": "simulationTime", "numPoints": "numPoints", "settlingPercent": "settlingPercent"},
    # Data Types
    "data_type_conversion": {"outputType": "output_type", "saturationMode": "saturation_mode", "roundingMode": "rounding_mode"},
    "real_imag_to_complex": {},
    "complex_to_real_imag": {},
    # Matrix Operations
    "matrix_multiply": {},
    "matrix_transpose": {},
    "matrix_inverse": {},
    "selector": {"indices": "indices"},
    "assignment": {"indices": "indices"},
    "concatenate": {"numInputs": "num_inputs", "mode": "mode"},
    "matrix_sum": {},
    "vector_norm": {"normType": "norm_type"},
    # Control Design
    "lqr_controller": {"K": "K"},
    "pole_placement": {"K": "K"},
    "lead_lag_compensator": {"K": "gain", "zero": "zero", "pole": "pole"},
    "pi_controller": {"Kp": "Kp", "Ki": "Ki"},
    "pd_controller": {"Kp": "Kp", "Kd": "Kd", "N": "N"},
    "anti_windup_pid": {"Kp": "Kp", "Ki": "Ki", "Kd": "Kd", "N": "N", "Kb": "Kb", "upperLimit": "upper_limit", "lowerLimit": "lower_limit"},
    "model_reference": {"naturalFrequency": "natural_frequency", "dampingRatio": "damping_ratio"},
    # Aerospace
    "quaternion_normalize": {},
    "quaternion_multiply": {},
    "quaternion_conjugate": {},
    "quaternion_to_euler": {"sequence": "sequence"},
    "euler_to_quaternion": {"sequence": "sequence"},
    "quaternion_rotate_vector": {},
    "dcm_to_quaternion": {},
    "quaternion_to_dcm": {},
    "isa_atmosphere": {},
    "six_dof_euler": {"mass": "mass", "inertia": "inertia", "initialPosition": "initial_position", "initialVelocity": "initial_velocity", "initialEuler": "initial_euler", "initialOmega": "initial_omega"},
    "flat_earth_gravity": {"g": "g"},
    "wgs84_gravity": {},
    # DSP
    "fft": {"nPoints": "n_points"},
    "ifft": {"nPoints": "n_points"},
    "fir_filter": {"coefficients": "coefficients"},
    "iir_filter": {"numerator": "numerator", "denominator": "denominator"},
    "convolution": {},
    "downsampler": {"factor": "factor"},
    "upsampler": {"factor": "factor"},
    "interpolator": {"factor": "factor"},
    "window_function": {"windowType": "window_type", "length": "length", "beta": "beta"},
    "mean": {"windowSize": "window_size"},
    "variance": {"windowSize": "window_size"},
    "rms": {"windowSize": "window_size"},
    "peak_detector": {"threshold": "threshold"},
    "zero_crossing_detector": {"direction": "direction"},
    # RF
    "rf_amplifier": {"gainDb": "gain_db", "noiseFigureDb": "noise_figure_db", "p1dbDbm": "p1db_dbm", "oip3Dbm": "oip3_dbm"},
    "rf_mixer": {"conversionLossDb": "conversion_loss_db", "noiseFigureDb": "noise_figure_db", "iip3Dbm": "iip3_dbm", "sideband": "sideband"},
    "rf_filter": {"filterType": "filter_type", "centerFreqHz": "center_freq_hz", "bandwidthHz": "bandwidth_hz", "insertionLossDb": "insertion_loss_db", "rejectionDb": "rejection_db"},
    "s_parameter_network": {"sParams": "s_params"},
    "rf_budget_element": {"gainDb": "gain_db", "noiseFigureDb": "noise_figure_db", "oip3Dbm": "oip3_dbm", "name": "name"},
    "attenuator": {"attenuationDb": "attenuation_db"},
    "am_modulator": {"carrierFreq": "carrier_freq", "carrierAmplitude": "carrier_amplitude", "modulationIndex": "modulation_index"},
    "fm_modulator": {"carrierFreq": "carrier_freq", "carrierAmplitude": "carrier_amplitude", "freqDeviation": "freq_deviation"},
    "phase_noise": {"phaseNoiseDbcHz": "phase_noise_dbcHz", "offsetFreq": "offset_freq"},
    "dbm_to_watts": {},
    "watts_to_dbm": {},
    # Navigation
    "coordinate_transformation": {"inputType": "input_type", "outputType": "output_type", "referenceLla": "reference_lla", "eulerSequence": "euler_sequence"},
    "lla_to_ecef": {},
    "ecef_to_lla": {},
    "ecef_to_ned": {"referenceLla": "reference_lla"},
    "ned_to_ecef": {"referenceLla": "reference_lla"},
    "waypoint_follower": {"waypoints": "waypoints", "acceptanceRadius": "acceptance_radius"},
    "great_circle_distance": {},
    "flat_earth_position": {"initialPosition": "initial_position"},
    # Sensor Fusion
    "imu_sensor": {"accelNoise": "accel_noise", "gyroNoise": "gyro_noise", "accelBias": "accel_bias", "gyroBias": "gyro_bias", "accelScaleError": "accel_scale_error", "gyroScaleError": "gyro_scale_error", "seed": "seed"},
    "accelerometer": {"noise": "noise", "bias": "bias", "scaleError": "scale_error", "seed": "seed"},
    "gyroscope": {"noise": "noise", "bias": "bias", "scaleError": "scale_error", "seed": "seed"},
    "magnetometer": {"noise": "noise", "bias": "bias", "scaleError": "scale_error", "seed": "seed"},
    "gps_sensor": {"positionNoise": "position_noise", "velocityNoise": "velocity_noise", "updateRate": "update_rate", "seed": "seed"},
    "altimeter": {"noise": "noise", "bias": "bias", "seed": "seed"},
    "complementary_filter": {"alpha": "alpha"},
    "madgwick_filter": {"beta": "beta"},
    "mahony_filter": {"Kp": "Kp", "Ki": "Ki"},
    "ins_gps_fusion": {"initialPosition": "initial_position", "initialVelocity": "initial_velocity", "initialAttitude": "initial_attitude"},
    "alpha_beta_filter": {"alpha": "alpha", "beta": "beta", "sampleTime": "sample_time"},
    "alpha_beta_gamma_filter": {"alpha": "alpha", "beta": "beta", "gamma": "gamma", "sampleTime": "sample_time"},
}


class OSKAdapter:
    """Adapter for the Object-oriented Simulation Kernel.

    Creates OSK block instances from compiled LibreSim models and
    manages simulation execution using OSK's Sim class.
    """

    def __init__(self):
        self._compiled_model: CompiledModel | None = None
        self._config: SimulationConfig | None = None
        self._osk_blocks: dict[str, Block] = {}
        self._block_map: dict[str, CompiledBlock] = {}
        self._sink_blocks: list[str] = []
        self._analysis_blocks: list[str] = []  # Track control analysis blocks
        # Track source block names for each scope input: scope_id -> [source_name, ...]
        self._scope_input_names: dict[str, list[str]] = {}

    def initialize(self, compiled_model: CompiledModel, config: SimulationConfig):
        """Initialize the simulation with a compiled model.

        Args:
            compiled_model: The compiled model from ModelCompiler
            config: Simulation configuration (solver, step size, etc.)
        """
        self._compiled_model = compiled_model
        self._config = config
        self._osk_blocks = {}
        self._block_map = {}
        self._sink_blocks = []
        self._analysis_blocks = []
        self._scope_input_names = {}

        # Reset global State for fresh simulation
        State.t = 0.0
        State.t1 = 0.0
        State.kpass = 0
        State.ready = 1
        State.tickfirst = 1
        State.ticklast = 0

        # Set the integration method
        solver_method = self._get_solver_method(config.solver)
        State.method = solver_method

        # Create OSK block instances
        for block in compiled_model.blocks:
            self._create_osk_block(block)
            self._block_map[block.id] = block

        # Set up connections between blocks
        self._setup_connections()

        # Initialize all blocks (must be done after connections are set up)
        # This is important for blocks like BodePlot, NyquistPlot, PoleZeroMap, StepInfo
        # that compute their outputs during init()
        State.dt = config.step_size
        State.dtp = config.step_size
        for osk_block in self._osk_blocks.values():
            osk_block.init()

    def _get_solver_method(self, solver: SolverType) -> str:
        """Convert SolverType to OSK method name."""
        return {
            SolverType.EULER: "Euler",
            SolverType.RK4: "RK4",
            SolverType.MERSON: "Merson",
        }.get(solver, "RK4")

    def _create_osk_block(self, compiled_block: CompiledBlock):
        """Create an OSK block instance from a compiled block."""
        block_type = compiled_block.type
        block_class = BLOCK_TYPE_MAP.get(block_type)

        if not block_class:
            # Unknown block type, create a pass-through block
            print(f"Warning: Unknown block type '{block_type}', using pass-through")
            self._osk_blocks[compiled_block.id] = Gain(gain=1.0)
            return

        # Map parameters
        osk_params = self._map_parameters(block_type, compiled_block.parameters)

        # Create the block instance
        try:
            osk_block = block_class(**osk_params)
            self._osk_blocks[compiled_block.id] = osk_block

            # Track sink blocks for output recording
            if block_type in ["scope", "display", "to_workspace"]:
                self._sink_blocks.append(compiled_block.id)

            # Track analysis blocks for visualization data collection
            if block_type in ["bode_plot", "nyquist_plot", "pole_zero_map", "step_info"]:
                self._analysis_blocks.append(compiled_block.id)

        except Exception as e:
            print(f"Error creating block '{compiled_block.name}': {e}")
            # Create a default block as fallback
            self._osk_blocks[compiled_block.id] = Gain(gain=1.0)

    def _map_parameters(self, block_type: str, params: dict[str, Any]) -> dict[str, Any]:
        """Map LibreSim parameter names to OSK constructor arguments.

        Only parameters that are explicitly mapped will be passed to the block constructor.
        Unknown parameters are filtered out to avoid constructor errors.
        """
        param_mapping = PARAM_MAP.get(block_type, {})
        osk_params = {}

        for libresim_name, value in params.items():
            if libresim_name in param_mapping:
                # Only include explicitly mapped parameters
                osk_name = param_mapping[libresim_name]
                osk_params[osk_name] = value
            # Skip unknown parameters - they likely aren't supported by the OSK block

        # Special handling for Product block operations
        # The frontend may pass a numeric string like "2" instead of "**"
        # Convert numeric values to the proper operation string
        if block_type == "product" and "operations" in osk_params:
            osk_params["operations"] = self._convert_product_operations(osk_params["operations"])

        return osk_params

    def _convert_product_operations(self, value: Any) -> str:
        """Convert Product block operations parameter to proper format.

        The frontend may pass:
        - A number like 2 or "2" -> "**" (2 multiply operations)
        - An operation string like "**/" -> "**/" (unchanged)
        """
        if value is None:
            return "**"  # Default to 2 multiply inputs

        # Convert to string if needed
        value_str = str(value)

        # If it's a pure number, convert to that many '*' characters
        try:
            num_inputs = int(value_str)
            return "*" * max(1, num_inputs)
        except ValueError:
            pass

        # Otherwise, it should already be an operation string
        # Validate it contains only valid characters
        valid_ops = {'*', '/'}
        if all(c in valid_ops for c in value_str):
            return value_str

        # Invalid format, default to multiply operations based on string length
        return "*" * max(1, len(value_str))

    def _setup_connections(self):
        """Set up connections between OSK blocks."""
        if not self._compiled_model:
            return

        for block in self._compiled_model.blocks:
            osk_block = self._osk_blocks.get(block.id)
            if not osk_block:
                continue

            # For scope blocks, track the source block names for each input
            if block.type == "scope":
                # Get the actual number of inputs from the block parameters
                # Support both 'numInputs' (frontend) and 'num_input_ports' (MDL import)
                num_inputs = int(block.parameters.get('numInputs',
                                 block.parameters.get('num_input_ports', 1)))
                self._scope_input_names[block.id] = [""] * num_inputs

            # Connect inputs
            # Connection format: "source_block_id:source_port_id@target_port_id"
            for conn in block.input_connections:
                # Parse the connection string to get source and target port info
                if "@" in conn:
                    source_part, target_port_id = conn.split("@")
                    source_block_id, source_port = source_part.split(":")
                else:
                    # Fallback for old format without target port
                    source_block_id, source_port = conn.split(":")
                    target_port_id = None

                source_osk_block = self._osk_blocks.get(source_block_id)
                source_compiled_block = self._block_map.get(source_block_id)

                # Extract the port index from target_port_id
                # Handles formats like:
                #   "block-in-0", "block-in-1" (numeric suffix, 0-indexed)
                #   "sum1-in1", "sum1-in2" (named suffix like in1/in2, 1-indexed)
                target_port_index = 0
                if target_port_id:
                    # Parse port index from ID
                    parts = target_port_id.rsplit("-", 1)
                    if len(parts) == 2:
                        suffix = parts[1]
                        if suffix.isdigit():
                            # Pure numeric: "block-in-0" -> index 0
                            target_port_index = int(suffix)
                        elif suffix.startswith("in") and len(suffix) > 2 and suffix[2:].isdigit():
                            # Named format: "sum1-in1" -> index 0, "sum1-in2" -> index 1
                            # But also support 0-indexed: "in0" -> index 0, "in1" -> index 1
                            port_num = int(suffix[2:])
                            # If port_num is 0, it's 0-indexed; otherwise assume 1-indexed
                            target_port_index = port_num if port_num == 0 else port_num - 1
                        elif suffix.startswith("out") and len(suffix) > 3 and suffix[3:].isdigit():
                            # Output format: "block-out1" -> index 0
                            target_port_index = int(suffix[3:]) - 1
                    elif target_port_id.startswith("in") and len(target_port_id) > 2 and target_port_id[2:].isdigit():
                        # Simple format: "in0", "in1", "in2"
                        # If port_num is 0, it's 0-indexed; otherwise assume 1-indexed
                        port_num = int(target_port_id[2:])
                        target_port_index = port_num if port_num == 0 else port_num - 1
                    elif target_port_id.startswith("in") and len(target_port_id) == 2:
                        # Format: "in" (single input port)
                        target_port_index = 0

                # Extract the source port index from source_port
                # Handles formats like:
                #   "demux1-out2" (block-out# format, 1-indexed)
                #   "block-out-0" (block-out-# format, 0-indexed)
                #   "out1", "out2" (simple format, 1-indexed)
                source_port_index = 0
                if source_port:
                    # Parse the port suffix from the source_port ID
                    parts = source_port.rsplit("-", 1)
                    if len(parts) == 2:
                        suffix = parts[1]
                        if suffix.isdigit():
                            # Format: "block-out-0" -> index 0
                            source_port_index = int(suffix)
                        elif suffix.startswith("out") and suffix[3:].isdigit():
                            # Format: "demux1-out2" -> index 1
                            source_port_index = int(suffix[3:]) - 1
                    elif source_port.startswith("out") and source_port[3:].isdigit():
                        # Format: "out1", "out2" (1-indexed)
                        source_port_index = int(source_port[3:]) - 1

                if source_osk_block:
                    # Use connectInput if available, otherwise we'll handle in step()
                    if hasattr(osk_block, 'connectInput'):
                        # Pass source_port_index to all blocks that accept it
                        # This allows blocks connected to multi-output sources
                        # (like Demux) to read from the correct port
                        sig = inspect.signature(osk_block.connectInput)
                        if 'source_port' in sig.parameters:
                            osk_block.connectInput(source_osk_block, target_port_index, source_port_index)
                        else:
                            osk_block.connectInput(source_osk_block, target_port_index)
                    elif hasattr(osk_block, 'input_block'):
                        osk_block.input_block = source_osk_block
                        # Also store source port for single-input blocks
                        if hasattr(osk_block, 'input_source_port'):
                            osk_block.input_source_port = source_port_index
                    elif hasattr(osk_block, 'input_blocks') and osk_block.input_blocks is not None:
                        if target_port_index < len(osk_block.input_blocks):
                            osk_block.input_blocks[target_port_index] = source_osk_block
                            # Also store source port for multi-input blocks
                            if hasattr(osk_block, 'input_source_ports') and osk_block.input_source_ports is not None:
                                if target_port_index < len(osk_block.input_source_ports):
                                    osk_block.input_source_ports[target_port_index] = source_port_index

                # Track source name for scope inputs and set on the scope block
                if block.type == "scope" and source_compiled_block:
                    if target_port_index < len(self._scope_input_names[block.id]):
                        self._scope_input_names[block.id][target_port_index] = source_compiled_block.name
                    # Also set the input name on the scope block itself for legend display
                    if hasattr(osk_block, 'setInputName'):
                        osk_block.setInputName(source_compiled_block.name, target_port_index)

    def _record_outputs(self) -> dict[str, float]:
        """Record outputs from all sink blocks.

        Returns:
            Dictionary mapping signal keys to values
        """
        recorded_outputs: dict[str, float] = {}

        for block_id in self._sink_blocks:
            osk_block = self._osk_blocks.get(block_id)
            compiled_block = self._block_map.get(block_id)

            if not osk_block or not compiled_block:
                continue

            # For scopes with multiple inputs or vector inputs, record each trace separately
            if block_id in self._scope_input_names and hasattr(osk_block, 'inputs'):
                input_names = self._scope_input_names[block_id]
                input_blocks = getattr(osk_block, 'input_blocks', [])

                trace_idx = 0
                for i in range(len(osk_block.inputs)):
                    # Skip unconnected inputs
                    if i < len(input_blocks) and input_blocks[i] is None:
                        continue

                    base_name = input_names[i] if i < len(input_names) else f"Input {i+1}"
                    # Check if this input is a vector (from Mux)
                    if hasattr(osk_block, '_vector_inputs') and i in osk_block._vector_inputs:
                        vec = osk_block._vector_inputs[i]
                        for j, val in enumerate(vec):
                            signal_name = f"{base_name}[{j+1}]"
                            key = f"{block_id}:{trace_idx}:{signal_name}"
                            if isinstance(val, (int, float)):
                                recorded_outputs[key] = float(val)
                            trace_idx += 1
                    else:
                        # Scalar input
                        value = osk_block.inputs[i] if i < len(osk_block.inputs) else 0.0
                        key = f"{block_id}:{trace_idx}:{base_name}"
                        if isinstance(value, (int, float)):
                            recorded_outputs[key] = float(value)
                        trace_idx += 1
            else:
                # Single-input sink block
                output = osk_block.getOutput()
                key = f"{block_id}:out:{compiled_block.name if compiled_block else block_id}"
                if isinstance(output, (int, float)):
                    recorded_outputs[key] = float(output)

        return recorded_outputs

    def step(self, t: float, dt: float) -> dict[str, float]:
        """Execute one simulation step.

        This method manually steps through the simulation, updating
        the OSK State class timing and calling block methods.

        For multi-pass integration methods (RK4, RK2, Merson), this runs
        all required passes to complete one time step.

        Args:
            t: Current simulation time
            dt: Time step size

        Returns:
            Dictionary of outputs from sink blocks (for recording)
        """
        if not self._compiled_model:
            return {}

        # Set OSK timing
        State.t = t
        State.dt = dt
        State.dtp = dt
        State.kpass = 0
        State.ready = 1

        # Number of passes for each integration method
        passes = {'Euler': 1, 'RK2': 2, 'RK4': 4, 'Merson': 5}
        num_passes = passes.get(State.method, 1)

        recorded_outputs: dict[str, float] = {}

        # At t=0, we need to record initial conditions BEFORE any propagation
        # This matches how OSK's Sim.run() works - first report happens before first propagation
        is_first_step = t < dt / 2.0  # Use dt/2 as tolerance for floating point

        # For the first step (t=0), we need to:
        # 1. Update all blocks once to establish initial values (read external ICs, etc.)
        # 2. Record initial condition outputs BEFORE any propagation
        # 3. Then run the full integration cycle
        if is_first_step:
            # Initial update pass to read external ICs and establish initial state
            State.kpass = 0
            State.ready = 1  # Ready to record

            # At t=0, we need a special initialization order:
            # 1. First, update all source blocks (constants) to output their values
            # 2. Then, have integrators read their external ICs (but NOT their derivatives yet)
            # 3. Finally, update all other blocks that depend on integrator outputs
            #
            # The normal execution order puts integrator-dependent blocks FIRST
            # (because integrators are state-holding and excluded from dependencies),
            # which is wrong for initialization.

            # Pass 1: Update constants and other source blocks
            for block_id in self._compiled_model.execution_order:
                compiled_block = self._block_map.get(block_id)
                osk_block = self._osk_blocks.get(block_id)
                if compiled_block and compiled_block.type == 'constant':
                    osk_block.update()

            # Pass 2: Have integrators read their external ICs
            # We call _read_external_ic directly to avoid also reading garbage derivatives
            for block_id in self._compiled_model.execution_order:
                compiled_block = self._block_map.get(block_id)
                osk_block = self._osk_blocks.get(block_id)
                if compiled_block and compiled_block.type == 'integrator':
                    # Only read external IC, don't update derivative yet
                    if hasattr(osk_block, '_read_external_ic'):
                        osk_block._read_external_ic()

            # Pass 3: Update all non-integrator blocks in execution order
            # These will read the initialized integrator states
            for block_id in self._compiled_model.execution_order:
                osk_block = self._osk_blocks.get(block_id)
                compiled_block = self._block_map.get(block_id)

                if not osk_block or not compiled_block:
                    continue

                # Skip constants (already updated) and integrators (will be updated after)
                if compiled_block.type in ('constant', 'integrator'):
                    continue

                # Set inputs manually for blocks without automatic connection
                has_input_block = hasattr(osk_block, 'input_block') and osk_block.input_block is not None
                has_input_blocks = hasattr(osk_block, 'input_blocks') and osk_block.input_blocks is not None and any(b is not None for b in osk_block.input_blocks)
                if not has_input_block and not has_input_blocks:
                    for i, conn in enumerate(compiled_block.input_connections):
                        source_block_id, _ = conn.split(":")
                        source_block = self._osk_blocks.get(source_block_id)
                        if source_block:
                            value = source_block.getOutput()
                            osk_block.setInput(value, i)

                # Update block to compute initial outputs
                osk_block.update()

            # Pass 4: Now update integrators to read their derivatives
            # (computed by the blocks updated in Pass 3)
            for block_id in self._compiled_model.execution_order:
                compiled_block = self._block_map.get(block_id)
                osk_block = self._osk_blocks.get(block_id)
                if compiled_block and compiled_block.type == 'integrator':
                    osk_block.update()

            # Record initial condition outputs BEFORE any propagation
            recorded_outputs = self._record_outputs()

            # Report for all blocks
            for osk_block in self._osk_blocks.values():
                osk_block.rpt()

            # Now run the full integration cycle to compute state for next step
            # But don't record outputs again - we already recorded the ICs
            #
            # During integration passes, we need proper execution order:
            # 1. Integrators output their current state (no update needed, just getOutput works)
            # 2. All non-integrator blocks update (computing derivatives for integrators)
            # 3. Integrators read their derivative inputs
            # 4. Propagate all states

            for kpass in range(num_passes):
                State.kpass = kpass
                State.ready = 0  # Don't record during integration passes

                # First pass: Update all non-integrator blocks
                # They will read integrator outputs (which reflect current state)
                for block_id in self._compiled_model.execution_order:
                    osk_block = self._osk_blocks.get(block_id)
                    compiled_block = self._block_map.get(block_id)

                    if not osk_block or not compiled_block:
                        continue

                    # Skip integrators in first pass
                    if compiled_block.type == 'integrator':
                        continue

                    has_input_block = hasattr(osk_block, 'input_block') and osk_block.input_block is not None
                    has_input_blocks = hasattr(osk_block, 'input_blocks') and osk_block.input_blocks is not None and any(b is not None for b in osk_block.input_blocks)
                    if not has_input_block and not has_input_blocks:
                        for i, conn in enumerate(compiled_block.input_connections):
                            source_block_id, _ = conn.split(":")
                            source_block = self._osk_blocks.get(source_block_id)
                            if source_block:
                                value = source_block.getOutput()
                                osk_block.setInput(value, i)

                    osk_block.update()

                # Second pass: Update integrators (they read derivatives from upstream blocks)
                for block_id in self._compiled_model.execution_order:
                    osk_block = self._osk_blocks.get(block_id)
                    compiled_block = self._block_map.get(block_id)

                    if not osk_block or not compiled_block:
                        continue

                    if compiled_block.type == 'integrator':
                        osk_block.update()

                # Propagate states after each pass
                for osk_block in self._osk_blocks.values():
                    osk_block.propagateStates()
        else:
            # Normal step (t > 0):
            # 1. Record outputs BEFORE integration (integrator states reflect current time t)
            # 2. Run integration passes to advance state for next step
            #
            # This is important because during multi-pass integration (RK4, Merson),
            # the integrator state x[0] is modified to intermediate values that don't
            # represent the actual system state at any real time point.

            State.kpass = 0
            State.ready = 1  # Ready to record

            # First, update all non-integrator blocks to read current integrator outputs
            for block_id in self._compiled_model.execution_order:
                osk_block = self._osk_blocks.get(block_id)
                compiled_block = self._block_map.get(block_id)

                if not osk_block or not compiled_block:
                    continue

                # Skip integrators - their outputs already reflect current state
                if compiled_block.type == 'integrator':
                    continue

                # For blocks without automatic input connection, set inputs manually
                has_input_block = hasattr(osk_block, 'input_block') and osk_block.input_block is not None
                has_input_blocks = hasattr(osk_block, 'input_blocks') and osk_block.input_blocks is not None and any(b is not None for b in osk_block.input_blocks)
                if not has_input_block and not has_input_blocks:
                    for i, conn in enumerate(compiled_block.input_connections):
                        source_block_id, _ = conn.split(":")
                        source_block = self._osk_blocks.get(source_block_id)
                        if source_block:
                            value = source_block.getOutput()
                            osk_block.setInput(value, i)

                # Update block to compute outputs
                osk_block.update()

            # Record outputs and report BEFORE integration
            recorded_outputs = self._record_outputs()
            for osk_block in self._osk_blocks.values():
                osk_block.rpt()

            # Now run the integration passes to advance state
            for kpass in range(num_passes):
                State.kpass = kpass
                State.ready = 0  # Don't record during integration

                # Update non-integrator blocks (compute derivative inputs for integrators)
                for block_id in self._compiled_model.execution_order:
                    osk_block = self._osk_blocks.get(block_id)
                    compiled_block = self._block_map.get(block_id)

                    if not osk_block or not compiled_block:
                        continue

                    if compiled_block.type == 'integrator':
                        continue

                    has_input_block = hasattr(osk_block, 'input_block') and osk_block.input_block is not None
                    has_input_blocks = hasattr(osk_block, 'input_blocks') and osk_block.input_blocks is not None and any(b is not None for b in osk_block.input_blocks)
                    if not has_input_block and not has_input_blocks:
                        for i, conn in enumerate(compiled_block.input_connections):
                            source_block_id, _ = conn.split(":")
                            source_block = self._osk_blocks.get(source_block_id)
                            if source_block:
                                value = source_block.getOutput()
                                osk_block.setInput(value, i)

                    osk_block.update()

                # Update integrators (they read derivatives from upstream blocks)
                for block_id in self._compiled_model.execution_order:
                    osk_block = self._osk_blocks.get(block_id)
                    compiled_block = self._block_map.get(block_id)

                    if not osk_block or not compiled_block:
                        continue

                    if compiled_block.type == 'integrator':
                        osk_block.update()

                # Propagate states for all blocks after each pass
                for osk_block in self._osk_blocks.values():
                    osk_block.propagateStates()

        # Reset kpass to 0 for next step (avoid polluting global state)
        State.kpass = 0

        return recorded_outputs

    def run_simulation(self) -> dict[str, Any]:
        """Run a complete simulation using OSK's Sim class.

        This is an alternative to using step() repeatedly,
        using OSK's native simulation loop.

        Returns:
            Simulation results with signals and statistics
        """
        if not self._compiled_model or not self._config:
            return {"signals": [], "statistics": {}}

        # Create stage with all blocks in execution order
        stage = [
            self._osk_blocks[bid]
            for bid in self._compiled_model.execution_order
            if bid in self._osk_blocks
        ]

        # Create and run simulation
        sim = Sim(
            dts=[self._config.step_size],
            tmax=self._config.stop_time,
            vStage=[stage]
        )

        results = sim.run()

        # Collect results from sink blocks
        signals = []
        for block_id in self._sink_blocks:
            osk_block = self._osk_blocks.get(block_id)
            if osk_block and hasattr(osk_block, 'getData'):
                data = osk_block.getData()
                num_inputs = data.get("numInputs", 1)
                input_names = data.get("inputNames", [])
                values = data.get("values", [])
                times = data.get("times", [])

                if num_inputs > 1 and isinstance(values, list) and len(values) == num_inputs:
                    # Multi-input scope: create a signal entry with all traces
                    signals.append({
                        "blockId": block_id,
                        "portId": "out",
                        "name": data.get("name", block_id),
                        "times": times,
                        "values": values,  # List of lists, one per input
                        "inputNames": input_names,
                        "numInputs": num_inputs
                    })
                else:
                    # Single-input scope or backward compatibility
                    signals.append({
                        "blockId": block_id,
                        "portId": "out",
                        "name": data.get("name", block_id),
                        "times": times,
                        "values": values[0] if isinstance(values, list) and len(values) > 0 and isinstance(values[0], list) else values
                    })

        return {
            "signals": signals,
            "statistics": {
                "totalSteps": len(results.get("times", [])),
                "executionTime": 0,  # Would need to measure
                "finalTime": results.get("times", [0])[-1] if results.get("times") else 0
            }
        }

    def get_solver(self, solver_type: SolverType) -> str:
        """Get OSK solver method name.

        Args:
            solver_type: The solver type enum

        Returns:
            OSK solver method name string
        """
        return self._get_solver_method(solver_type)

    def get_block(self, block_id: str) -> Block | None:
        """Get an OSK block instance by ID.

        Args:
            block_id: The block ID

        Returns:
            The OSK block instance or None
        """
        return self._osk_blocks.get(block_id)

    def get_all_blocks(self) -> dict[str, Block]:
        """Get all OSK block instances.

        Returns:
            Dictionary mapping block IDs to OSK block instances
        """
        return self._osk_blocks.copy()

    def get_analysis_data(self) -> dict[str, Any]:
        """Get analysis data from all control analysis blocks.

        Returns:
            Dictionary mapping block IDs to analysis data
        """
        analyses = {}
        for block_id in self._analysis_blocks:
            osk_block = self._osk_blocks.get(block_id)
            compiled_block = self._block_map.get(block_id)
            if osk_block and hasattr(osk_block, 'getData'):
                data = osk_block.getData()
                # Add block name for display
                if compiled_block:
                    data['name'] = compiled_block.name
                analyses[block_id] = data
        return analyses
