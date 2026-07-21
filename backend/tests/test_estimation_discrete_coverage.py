"""Behavioral edge coverage for estimation, analysis, and discrete blocks."""

import math

import numpy as np
import pytest

from src.osk.blocks.control_analysis import BodePlot, NyquistPlot, PoleZeroMap, StepInfo
from src.osk.blocks.discrete import (
    DiscreteDerivative,
    DiscreteIntegrator,
    DiscretePIDController,
    DiscreteStateSpace,
    DiscreteTransferFunction,
    FirstOrderHold,
    Memory,
    UnitDelay,
)
from src.osk.blocks.observers import ExtendedKalmanFilter, KalmanFilter, LuenbergerObserver
from src.osk.blocks.sensor_fusion import (
    Accelerometer,
    AlphaBetaFilter,
    AlphaBetaGammaFilter,
    Altimeter,
    ComplementaryFilter,
    GPSSensor,
    Gyroscope,
    IMUSensor,
    INSGPSFusion,
    MadgwickFilter,
    Magnetometer,
    MahonyFilter,
)
from src.osk.context import SimContext


class Source:
    def __init__(self, value=0.0, vector=None):
        self.value = value
        self.vector = vector

    def getOutput(self, port=0):
        return self.value + port

    def getOutputVector(self):
        return self.vector


def test_sensor_sources_invalid_shapes_ports_and_connected_protocols():
    short = Source(vector=[1.0])
    full = Source(vector=[1.0, 2.0, 3.0])

    imu = IMUSensor(seed=1)
    imu.setInput(1.0)
    imu.connectInput(short, 0)
    imu.connectInput(full, 1)
    imu.connectInput(full, 2)
    imu.update()
    assert imu.true_accel == [0.0, 0.0, 0.0]
    assert imu.true_gyro == [1.0, 2.0, 3.0]

    for sensor, attr in [
        (Accelerometer(noise=0.0, seed=1), "true_accel"),
        (Gyroscope(noise=0.0, seed=1), "true_gyro"),
        (Magnetometer(noise=0.0, seed=1), "true_mag"),
    ]:
        sensor.setInput([1.0])
        sensor.connectInput(short)
        sensor.update()
        assert getattr(sensor, attr) == [0.0, 0.0, 0.0]
        assert sensor.getOutput() == 0.0

    gps = GPSSensor(seed=1)
    gps.setInput([1.0], 0)
    gps.setInput([1.0, 2.0, 3.0], 1)
    gps.connectInput(short, 0)
    gps.connectInput(full, 1)
    gps.connectInput(full, 2)
    gps.update()
    assert gps.true_position == [0.0, 0.0, 0.0]
    assert gps.true_velocity == [1.0, 2.0, 3.0]
    assert gps.getOutput() == pytest.approx(gps.output[0])
    gps.update()
    assert gps.last_update_time == 0.0

    altimeter = Altimeter(noise=0.0, bias=1.0)
    altimeter.connectInput(Source(4.0))
    altimeter.update()
    assert altimeter.getOutput() == 5.0


def test_attitude_filters_short_sources_singular_orientation_and_ports():
    short = Source(vector=[1.0])
    full = Source(vector=[0.0, 0.0, 1.0])

    complementary = ComplementaryFilter(alpha=1.0)
    complementary.context = SimContext(dt=0.1)
    complementary.setInput([1.0])
    complementary.connectInput(short, 0)
    complementary.connectInput(full, 1)
    complementary.connectInput(full, 2)
    complementary.euler[1] = math.pi / 2
    complementary.update()
    assert complementary.output[2] == 0.0
    assert complementary.getOutput() == complementary.output[0]

    madgwick = MadgwickFilter()
    madgwick.context = SimContext(dt=0.0)
    madgwick.setInput([1.0], 0)
    madgwick.setInput([1.0, 2.0, 3.0], 2)
    madgwick.connectInput(short, 0)
    madgwick.connectInput(full, 1)
    madgwick.connectInput(full, 2)
    madgwick.connectInput(full, 3)
    madgwick.q = [0.0, 0.0, 0.0, 0.0]
    madgwick.update()
    assert madgwick.getOutput() == 0.0

    mahony = MahonyFilter()
    mahony.context = SimContext(dt=0.0)
    mahony.setInput([1.0])
    mahony.connectInput(short, 0)
    mahony.connectInput(full, 1)
    mahony.connectInput(full, 2)
    mahony.q = [0.0, 0.0, 0.0, 0.0]
    mahony.update()
    assert mahony.getOutput() == 0.0


def test_ins_gps_all_inputs_guards_correction_and_tracking_setters():
    fusion = INSGPSFusion()
    fusion.context = SimContext(dt=0.1)
    fusion.setInput(1.0)
    fusion.setInput([1.0], 0)
    fusion.setInput([1.0, 2.0, 3.0], 0)
    fusion.setInput([1.0, 2.0, 3.0], 1)
    fusion.setInput([4.0, 5.0, 6.0], 2)
    fusion.connectInput(Source(vector=[1.0]), 0)
    fusion.connectInput(Source(vector=None), 1)
    fusion.connectInput(Source(vector=[7.0, 8.0, 9.0]), 2)
    fusion.connectInput(Source(), 3)
    fusion.update()
    assert fusion.gps_valid is False
    assert fusion.gps_velocity == [7.0, 8.0, 9.0]
    assert fusion.getOutput() == fusion.output[0]
    fusion.update()
    assert fusion.gps_valid is False

    alpha_beta = AlphaBetaFilter()
    alpha_beta.setInput(3.0)
    alpha_beta.update()
    assert alpha_beta.getOutput() == 0.0

    alpha_beta_gamma = AlphaBetaGammaFilter()
    alpha_beta_gamma.setInput(3.0)
    alpha_beta_gamma.update()
    assert alpha_beta_gamma.getOutput() == 0.0


def test_control_analysis_degenerate_values_crossings_and_characteristics(monkeypatch):
    bode = BodePlot(numerator=[0.0], denominator=[0.0], numPoints=2)
    assert bode._evaluate_tf(1j) == complex(1e10, 0)
    bode._compute_frequency_response()
    assert bode.magnitude_db[0] == 200.0
    bode.magnitude_db = []
    bode._compute_frequency_response()
    bode.numerator = [0.0]
    bode.denominator = [1.0]
    bode._compute_frequency_response()
    assert bode.magnitude_db == [-200, -200]

    bode.numPoints = 0
    bode._compute_frequency_response()
    assert bode.magnitude_db == []

    bode.numPoints = 2
    responses = iter(
        [
            complex(math.cos(math.radians(170)), math.sin(math.radians(170))),
            complex(math.cos(math.radians(-170)), math.sin(math.radians(-170))),
        ]
    )
    monkeypatch.setattr(bode, "_evaluate_tf", lambda value: next(responses))
    bode._compute_frequency_response()
    assert bode.phase_deg[-1] == pytest.approx(190.0)

    nyquist = NyquistPlot(numerator=[0.0], denominator=[0.0], numPoints=2)
    assert nyquist._evaluate_tf(1j) == complex(1e10, 0)
    nyquist.real_parts = [-2.0, -2.0, -2.0]
    nyquist.imag_parts = [1.0, -1.0, 1.0]
    nyquist._count_encirclements()
    assert nyquist.encirclements == 0
    nyquist.real_parts = [-0.5, -0.5, -0.5]
    nyquist._count_encirclements()
    assert nyquist.encirclements == 0

    pole_zero = PoleZeroMap()
    assert pole_zero._find_roots([1.0]) == []
    assert pole_zero._find_roots([0.0, 1.0]) == []
    monkeypatch.setattr(np, "roots", lambda coefficients: (_ for _ in ()).throw(ValueError("bad")))
    assert pole_zero._find_roots([1.0, 1.0]) == []

    info = StepInfo()
    info.response = []
    info._compute_characteristics()
    info.response = [0.0, 0.0]
    info.times = [0.0, 1.0]
    info._compute_characteristics()
    assert info.steady_state_value == 0.0
    assert info.settling_time == 0.0
    info.response = [0.0, 2.0, 1.0]
    info.times = [0.0, 1.0, 2.0]
    info._compute_characteristics()
    assert info.overshoot_percent == 100.0


def test_control_analysis_connected_transfer_functions_and_shell_methods():
    class TransferFunctionSource:
        numerator = [2.0]
        denominator = [1.0]

    class PartialSource:
        numerator = [9.0]

    source = TransferFunctionSource()
    partial = PartialSource()
    for block in [BodePlot(numPoints=2), NyquistPlot(numPoints=2), PoleZeroMap(), StepInfo()]:
        block.connectInput(partial)
        block._extract_tf_from_input()
        block.connectInput(source)
        block._extract_tf_from_input()
        assert block.numerator == [2.0]
        block.update()
        assert isinstance(block.getOutput(), float)

    pole_zero = PoleZeroMap()
    pole_zero.poles = []
    pole_zero._analyze_stability()
    assert pole_zero.is_stable is True


def test_discrete_stage_guards_connections_methods_and_buffer_bounds():
    source = Source(2.0)
    staged = SimContext(t=0.0, ready=0)
    delay = UnitDelay(initial_condition=1.0)
    delay.context = staged
    delay.setInput(2.0)
    delay.update()
    delay.rpt()
    assert delay.getOutput() == 1.0
    for block in [
        DiscreteIntegrator(sample_time=0.1),
        DiscreteDerivative(sample_time=0.1),
        DiscreteTransferFunction([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]),
    ]:
        block.context = staged
        block.connectInput(source, source_port=2)
        block.update()
        assert block.getOutput() == 0.0

    integrator = DiscreteIntegrator(sample_time=0.1, method="trapezoidal")
    integrator.context = SimContext(t=0.0, ready=1)
    integrator.setInput(2.0)
    integrator.update()
    assert integrator.getOutput() == pytest.approx(0.1)

    transfer = DiscreteTransferFunction([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    transfer.context = SimContext(t=0.0, ready=1)
    transfer.setInput(2.0)
    transfer.update()
    assert transfer.getOutput() == 2.0

    memory = Memory(initial_condition=1.0)
    memory.context = staged
    memory.connectInput(source, source_port=2)
    memory.update()
    memory.rpt()
    assert memory.getOutput() == 1.0
    memory.context.ready = 1
    memory.rpt()
    assert memory._prev_value == 4.0


def test_discrete_state_space_hold_and_pid_edge_modes():
    source = Source(2.0)
    state_space = DiscreteStateSpace(A=[[1.0]], B=[[1.0]], C=[[1.0]], D=[[0.0]])
    state_space.connectInput(source, source_port=1)
    state_space.context = SimContext(t=0.0, ready=1)
    state_space.update()
    assert state_space.getOutput() == 0.0
    state_space.context.ready = 0
    state_space.update()
    assert state_space.getOutput() == 0.0

    hold = FirstOrderHold(sample_time=0.0)
    hold.connectInput(source, source_port=1)
    hold.context = SimContext(t=0.0, ready=1)
    hold.update()
    assert hold.getOutput() == 3.0
    hold.context.ready = 0
    hold.update()
    assert hold.getOutput() == 3.0

    unknown = DiscreteIntegrator(sample_time=0.1, method="unknown")
    unknown.context = SimContext(t=0.0, ready=1)
    unknown.setInput(2.0)
    unknown.update()
    assert unknown.getOutput() == 0.0

    for method, expected_integral in [("backward", 0.1), ("trapezoidal", 0.05)]:
        pid = DiscretePIDController(Kp=1.0, Ki=1.0, Kd=0.0, sample_time=0.1, method=method)
        pid.connectInput(Source(1.0), source_port=0)
        pid.context = SimContext(t=0.0, ready=1)
        pid.update()
        assert pid._integral == pytest.approx(expected_integral)

    unfiltered = DiscretePIDController(Kp=0.0, Ki=0.0, Kd=1.0, N=0.0, sample_time=0.1)
    unfiltered.context = SimContext(t=0.0, ready=1)
    unfiltered.setInput(1.0)
    unfiltered.update()
    assert unfiltered.getOutput() == 10.0
    unfiltered.context.ready = 0
    unfiltered.update()
    assert unfiltered.getOutput() == 10.0


def test_observer_vector_matrices_invalid_ports_stage_guards_and_singular_gain():
    source = Source(2.0)
    observer = LuenbergerObserver(B=[1.0], C=[1.0], L=[1.0])
    assert observer.B.shape == (1, 1)
    assert observer.C.shape == (1, 1)
    assert observer.L.shape == (1, 1)
    observer.setInput(9.0, 2)
    observer.connectInput(source, 0, source_port=1)
    observer.connectInput(source, 2)
    observer.update()
    assert observer.inputs[0] == 3.0

    kalman = KalmanFilter(B=[1.0], C=[1.0], A=[[0.0]], Q=[[0.0]], R=[[0.0]], initial_P=[[0.0]])
    kalman.setInput(1.0, 2)
    kalman.connectInput(source, 2)
    kalman.context = SimContext(ready=0)
    kalman.update()
    assert kalman.getOutput() == 0.0
    kalman.context.ready = 1
    kalman.update()
    assert kalman.getOutput() == 0.0

    extended = ExtendedKalmanFilter(Q=[[0.0]], R=[[0.0]])
    extended.setInput(1.0, 2)
    extended.connectInput(source, 2)
    extended.context = SimContext(dt=0.1, ready=0)
    extended.update()
    assert extended.getOutput() == 0.0
    extended.context.ready = 1
    extended.P = np.zeros((1, 1))
    extended.update()
    assert extended.getOutput() == 0.0
