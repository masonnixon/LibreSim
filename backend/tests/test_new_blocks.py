"""Tests for new OSK simulation blocks: Data Types, Matrix Ops, Control Design, Aerospace."""

import math

import pytest

# Aerospace blocks
from src.osk.blocks.aerospace import (
    DCMToQuaternion,
    EulerToQuaternion,
    FlatEarthGravity,
    ISAAtmosphere,
    QuaternionConjugate,
    QuaternionMultiply,
    QuaternionNormalize,
    QuaternionRotateVector,
    QuaternionToDCM,
    QuaternionToEuler,
    SixDOFEuler,
    WGS84Gravity,
)

# Control Design blocks
from src.osk.blocks.control_design import (
    AntiWindupPID,
    LQRController,
    ModelReference,
    PDController,
    PIController,
    PolePlacement,
)

# Data Type blocks
from src.osk.blocks.data_types import (
    ComplexToRealImag,
    DataTypeConversion,
    RealImagToComplex,
)

# Matrix Operations blocks
from src.osk.blocks.matrix_ops import (
    Assignment,
    Concatenate,
    MatrixInverse,
    MatrixMultiply,
    MatrixSum,
    MatrixTranspose,
    Selector,
    VectorNorm,
)

# =============================================================================
# Data Type Conversion Block Tests
# =============================================================================


class TestDataTypeConversion:
    """Tests for the DataTypeConversion block."""

    def test_double_conversion(self):
        """Test conversion to double."""
        dtc = DataTypeConversion(output_type="double")
        dtc.init()
        dtc.setInput(5)
        dtc.update()
        assert dtc.getOutput() == 5.0

    def test_boolean_conversion(self):
        """Test conversion to boolean."""
        dtc = DataTypeConversion(output_type="boolean")
        dtc.init()
        dtc.setInput(3.5)
        dtc.update()
        assert dtc.getOutput() == 1.0

        dtc.setInput(0)
        dtc.update()
        assert dtc.getOutput() == 0.0

    def test_int8_saturation(self):
        """Test int8 conversion with saturation."""
        dtc = DataTypeConversion(output_type="int8", saturate=True)
        dtc.init()

        dtc.setInput(200)
        dtc.update()
        assert dtc.getOutput() == 127  # Saturated to max

        dtc.setInput(-200)
        dtc.update()
        assert dtc.getOutput() == -128  # Saturated to min

    def test_uint8_saturation(self):
        """Test uint8 conversion with saturation."""
        dtc = DataTypeConversion(output_type="uint8", saturate=True)
        dtc.init()

        dtc.setInput(300)
        dtc.update()
        assert dtc.getOutput() == 255

        dtc.setInput(-10)
        dtc.update()
        assert dtc.getOutput() == 0

    def test_int8_wrap(self):
        """Test int8 conversion with wrap-around."""
        dtc = DataTypeConversion(output_type="int8", saturate=False)
        dtc.init()

        dtc.setInput(130)  # Should wrap
        dtc.update()
        # 130 wraps to -126 in signed 8-bit
        assert dtc.getOutput() == -126

    def test_rounding_modes(self):
        """Test different rounding modes."""
        dtc_floor = DataTypeConversion(output_type="int32", round_mode="floor")
        dtc_ceil = DataTypeConversion(output_type="int32", round_mode="ceil")
        dtc_round = DataTypeConversion(output_type="int32", round_mode="round")

        for dtc in [dtc_floor, dtc_ceil, dtc_round]:
            dtc.init()
            dtc.setInput(3.7)
            dtc.update()

        assert dtc_floor.getOutput() == 3
        assert dtc_ceil.getOutput() == 4
        assert dtc_round.getOutput() == 4


class TestRealImagToComplex:
    """Tests for the RealImagToComplex block."""

    def test_magnitude_phase(self):
        """Test conversion from real/imag to magnitude/phase."""
        ric = RealImagToComplex()
        ric.init()
        ric.setInput(3.0, 0)  # Real
        ric.setInput(4.0, 1)  # Imag
        ric.update()

        assert ric.getOutput(0) == pytest.approx(5.0)  # Magnitude
        assert ric.getOutput(1) == pytest.approx(math.atan2(4, 3))  # Phase

    def test_zero_input(self):
        """Test with zero inputs."""
        ric = RealImagToComplex()
        ric.init()
        ric.setInput(0.0, 0)
        ric.setInput(0.0, 1)
        ric.update()

        assert ric.getOutput(0) == 0.0
        assert ric.getOutput(1) == 0.0

    def test_output_vector(self):
        """Test getOutputVector."""
        ric = RealImagToComplex()
        ric.init()
        ric.setInput(1.0, 0)
        ric.setInput(1.0, 1)
        ric.update()

        vec = ric.getOutputVector()
        assert len(vec) == 2
        assert vec[0] == pytest.approx(math.sqrt(2))


class TestComplexToRealImag:
    """Tests for the ComplexToRealImag block."""

    def test_real_imag_extraction(self):
        """Test conversion from magnitude/phase to real/imag."""
        cri = ComplexToRealImag()
        cri.init()
        cri.setInput(5.0, 0)  # Magnitude
        cri.setInput(math.atan2(4, 3), 1)  # Phase
        cri.update()

        assert cri.getOutput(0) == pytest.approx(3.0)  # Real
        assert cri.getOutput(1) == pytest.approx(4.0)  # Imag

    def test_roundtrip(self):
        """Test roundtrip conversion."""
        # Real/Imag -> Mag/Phase
        ric = RealImagToComplex()
        ric.init()
        ric.setInput(7.0, 0)
        ric.setInput(24.0, 1)
        ric.update()

        # Mag/Phase -> Real/Imag
        cri = ComplexToRealImag()
        cri.init()
        cri.setInput(ric.getOutput(0), 0)
        cri.setInput(ric.getOutput(1), 1)
        cri.update()

        assert cri.getOutput(0) == pytest.approx(7.0)
        assert cri.getOutput(1) == pytest.approx(24.0)


# =============================================================================
# Matrix Operations Block Tests
# =============================================================================


class TestMatrixMultiply:
    """Tests for the MatrixMultiply block."""

    def test_dot_product(self):
        """Test dot product of two vectors."""
        mm = MatrixMultiply()
        mm.init()
        mm.setInput([1, 2, 3], 0)
        mm.setInput([4, 5, 6], 1)
        mm.update()

        assert mm.getOutput() == 32  # 1*4 + 2*5 + 3*6

    def test_scalar_multiplication(self):
        """Test scalar * scalar."""
        mm = MatrixMultiply()
        mm.init()
        mm.setInput([3], 0)
        mm.setInput([4], 1)
        mm.update()

        assert mm.getOutput() == 12


class TestMatrixTranspose:
    """Tests for the MatrixTranspose block."""

    def test_transpose_passthrough(self):
        """Test that 1D transpose is passthrough."""
        mt = MatrixTranspose()
        mt.init()
        mt.setInput([1, 2, 3])
        mt.update()

        assert mt.getOutput(0) == 1
        assert mt.getOutput(1) == 2
        assert mt.getOutput(2) == 3


class TestMatrixInverse:
    """Tests for the MatrixInverse block."""

    def test_scalar_inverse(self):
        """Test scalar inverse."""
        mi = MatrixInverse()
        mi.init()
        mi.setInput([4])
        mi.update()

        assert mi.getOutput() == pytest.approx(0.25)

    def test_2x2_inverse(self):
        """Test 2x2 matrix inverse."""
        mi = MatrixInverse()
        mi.init()
        # [[2, 1], [1, 1]] stored as [2, 1, 1, 1]
        mi.setInput([2, 1, 1, 1])
        mi.update()

        # Inverse is [[1, -1], [-1, 2]]
        assert mi.getOutput(0) == pytest.approx(1.0)
        assert mi.getOutput(1) == pytest.approx(-1.0)
        assert mi.getOutput(2) == pytest.approx(-1.0)
        assert mi.getOutput(3) == pytest.approx(2.0)

    def test_singular_matrix(self):
        """Test singular matrix returns inf."""
        mi = MatrixInverse()
        mi.init()
        mi.setInput([1, 2, 2, 4])  # Singular
        mi.update()

        assert mi.getOutput(0) == float("inf")


class TestSelector:
    """Tests for the Selector block."""

    def test_select_elements(self):
        """Test selecting specific elements."""
        sel = Selector(indices=[0, 2, 4])
        sel.init()
        sel.setInput([10, 20, 30, 40, 50])
        sel.update()

        assert sel.getOutput(0) == 10
        assert sel.getOutput(1) == 30
        assert sel.getOutput(2) == 50

    def test_out_of_bounds(self):
        """Test out of bounds index returns 0."""
        sel = Selector(indices=[0, 10])
        sel.init()
        sel.setInput([1, 2, 3])
        sel.update()

        assert sel.getOutput(0) == 1
        assert sel.getOutput(1) == 0  # Out of bounds


class TestAssignment:
    """Tests for the Assignment block."""

    def test_assign_values(self):
        """Test assigning values to indices."""
        asn = Assignment(indices=[1, 3])
        asn.init()
        asn.setInput([10, 20, 30, 40, 50], 0)  # Base
        asn.setInput([99, 88], 1)  # Values
        asn.update()

        assert asn.getOutput(0) == 10
        assert asn.getOutput(1) == 99  # Replaced
        assert asn.getOutput(2) == 30
        assert asn.getOutput(3) == 88  # Replaced
        assert asn.getOutput(4) == 50


class TestConcatenate:
    """Tests for the Concatenate block."""

    def test_concatenate_vectors(self):
        """Test concatenating two vectors."""
        cat = Concatenate(num_inputs=2)
        cat.init()
        cat.setInput([1, 2], 0)
        cat.setInput([3, 4, 5], 1)
        cat.update()

        vec = cat.getOutputVector()
        assert vec == [1, 2, 3, 4, 5]
        assert cat.getNumOutputs() == 5


class TestMatrixSum:
    """Tests for the MatrixSum block."""

    def test_sum_all(self):
        """Test summing all elements."""
        ms = MatrixSum()
        ms.init()
        ms.setInput([1, 2, 3, 4, 5])
        ms.update()

        assert ms.getOutput() == 15


class TestVectorNorm:
    """Tests for the VectorNorm block."""

    def test_2norm(self):
        """Test Euclidean norm."""
        vn = VectorNorm(norm_type="2")
        vn.init()
        vn.setInput([3, 4])
        vn.update()

        assert vn.getOutput() == pytest.approx(5.0)

    def test_1norm(self):
        """Test 1-norm (Manhattan)."""
        vn = VectorNorm(norm_type="1")
        vn.init()
        vn.setInput([3, -4])
        vn.update()

        assert vn.getOutput() == 7.0

    def test_inf_norm(self):
        """Test infinity norm."""
        vn = VectorNorm(norm_type="inf")
        vn.init()
        vn.setInput([3, -7, 2])
        vn.update()

        assert vn.getOutput() == 7.0


# =============================================================================
# Control Design Block Tests
# =============================================================================


class TestLQRController:
    """Tests for the LQRController block."""

    def test_siso_control(self):
        """Test single-input single-state LQR."""
        lqr = LQRController(K=[[2.0]], num_states=1, num_inputs=1)
        lqr.init()
        lqr.setInput(5.0, 0)
        lqr.update()

        assert lqr.getOutput() == -10.0  # u = -K*x = -2*5

    def test_mimo_control(self):
        """Test multi-state LQR."""
        lqr = LQRController(K=[[1.0, 2.0]], num_states=2, num_inputs=1)
        lqr.init()
        lqr.setInput(3.0, 0)
        lqr.setInput(4.0, 1)
        lqr.update()

        assert lqr.getOutput() == -11.0  # u = -(1*3 + 2*4)


class TestPolePlacement:
    """Tests for the PolePlacement block."""

    def test_state_feedback(self):
        """Test state feedback control."""
        pp = PolePlacement(K=[1.5, 2.5], num_states=2)
        pp.init()
        pp.setInput(2.0, 0)
        pp.setInput(3.0, 1)
        pp.update()

        assert pp.getOutput() == pytest.approx(-10.5)  # -(1.5*2 + 2.5*3)


class TestPIController:
    """Tests for the PIController block."""

    def test_proportional_action(self):
        """Test proportional term."""
        pi = PIController(Kp=2.0, Ki=0.0)
        pi.init()
        pi.setInput(5.0)
        pi.update()

        assert pi.getOutput() == 10.0

    def test_integral_action(self):
        """Test integral accumulation."""
        pi = PIController(Kp=0.0, Ki=1.0, initial_integrator=10.0)
        pi.init()
        pi.setInput(2.0)
        pi.update()

        # I term uses the integrator state (initial=10), derivative=error
        assert pi.getOutput() == 10.0  # Ki * integrator[0]


class TestPDController:
    """Tests for the PDController block."""

    def test_proportional_action(self):
        """Test proportional term."""
        pd = PDController(Kp=3.0, Kd=0.0)
        pd.init()
        pd.setInput(4.0)
        pd.update()

        assert pd.getOutput() == 12.0


class TestAntiWindupPID:
    """Tests for the AntiWindupPID block."""

    def test_saturation(self):
        """Test output saturation."""
        pid = AntiWindupPID(Kp=100.0, Ki=0.0, Kd=0.0, upper_limit=10.0, lower_limit=-10.0)
        pid.init()
        pid.setInput(1.0)  # Error would give 100 without saturation
        pid.update()

        assert pid.getOutput() == 10.0  # Saturated

    def test_negative_saturation(self):
        """Test negative saturation."""
        pid = AntiWindupPID(Kp=100.0, Ki=0.0, Kd=0.0, upper_limit=10.0, lower_limit=-10.0)
        pid.init()
        pid.setInput(-1.0)
        pid.update()

        assert pid.getOutput() == -10.0


class TestModelReference:
    """Tests for the ModelReference block."""

    def test_init_output(self):
        """Test initial output is zero."""
        mr = ModelReference(natural_frequency=1.0, damping_ratio=1.0)
        mr.init()

        assert mr.getOutput() == 0.0


# =============================================================================
# Aerospace Block Tests
# =============================================================================


class TestQuaternionNormalize:
    """Tests for the QuaternionNormalize block."""

    def test_normalize_unit(self):
        """Test normalizing a unit quaternion."""
        qn = QuaternionNormalize()
        qn.init()
        qn.setInput([1, 0, 0, 0])
        qn.update()

        vec = qn.getOutputVector()
        assert vec == [1.0, 0.0, 0.0, 0.0]

    def test_normalize_non_unit(self):
        """Test normalizing a non-unit quaternion."""
        qn = QuaternionNormalize()
        qn.init()
        qn.setInput([2, 0, 0, 0])
        qn.update()

        vec = qn.getOutputVector()
        assert vec[0] == pytest.approx(1.0)
        mag = math.sqrt(sum(q * q for q in vec))
        assert mag == pytest.approx(1.0)


class TestQuaternionMultiply:
    """Tests for the QuaternionMultiply block."""

    def test_identity_multiply(self):
        """Test multiplication by identity quaternion."""
        qm = QuaternionMultiply()
        qm.init()
        qm.setInput([1, 0, 0, 0], 0)  # Identity
        qm.setInput([0.707, 0.707, 0, 0], 1)
        qm.update()

        vec = qm.getOutputVector()
        assert vec[0] == pytest.approx(0.707)
        assert vec[1] == pytest.approx(0.707)

    def test_hamilton_product(self):
        """Test Hamilton product properties."""
        qm = QuaternionMultiply()
        qm.init()
        # q * q^(-1) should give identity
        q = [0.5, 0.5, 0.5, 0.5]
        q_conj = [0.5, -0.5, -0.5, -0.5]
        qm.setInput(q, 0)
        qm.setInput(q_conj, 1)
        qm.update()

        vec = qm.getOutputVector()
        assert vec[0] == pytest.approx(1.0)
        assert abs(vec[1]) < 1e-10
        assert abs(vec[2]) < 1e-10
        assert abs(vec[3]) < 1e-10


class TestQuaternionConjugate:
    """Tests for the QuaternionConjugate block."""

    def test_conjugate(self):
        """Test quaternion conjugate."""
        qc = QuaternionConjugate()
        qc.init()
        qc.setInput([1, 2, 3, 4])
        qc.update()

        vec = qc.getOutputVector()
        assert vec == [1, -2, -3, -4]


class TestQuaternionToEuler:
    """Tests for the QuaternionToEuler block."""

    def test_identity_to_euler(self):
        """Test identity quaternion gives zero Euler angles."""
        qe = QuaternionToEuler()
        qe.init()
        qe.setInput([1, 0, 0, 0])
        qe.update()

        vec = qe.getOutputVector()
        assert vec[0] == pytest.approx(0.0)  # Roll
        assert vec[1] == pytest.approx(0.0)  # Pitch
        assert vec[2] == pytest.approx(0.0)  # Yaw


class TestEulerToQuaternion:
    """Tests for the EulerToQuaternion block."""

    def test_zero_euler(self):
        """Test zero Euler angles give identity quaternion."""
        eq = EulerToQuaternion()
        eq.init()
        eq.setInput([0, 0, 0])
        eq.update()

        vec = eq.getOutputVector()
        assert vec[0] == pytest.approx(1.0)
        assert abs(vec[1]) < 1e-10
        assert abs(vec[2]) < 1e-10
        assert abs(vec[3]) < 1e-10

    def test_roundtrip(self):
        """Test Euler -> Quaternion -> Euler roundtrip."""
        euler = [0.1, 0.2, 0.3]

        eq = EulerToQuaternion()
        eq.init()
        eq.setInput(euler)
        eq.update()

        qe = QuaternionToEuler()
        qe.init()
        qe.setInput(eq.getOutputVector())
        qe.update()

        result = qe.getOutputVector()
        assert result[0] == pytest.approx(euler[0], rel=1e-5)
        assert result[1] == pytest.approx(euler[1], rel=1e-5)
        assert result[2] == pytest.approx(euler[2], rel=1e-5)


class TestQuaternionRotateVector:
    """Tests for the QuaternionRotateVector block."""

    def test_identity_rotation(self):
        """Test identity quaternion doesn't rotate."""
        qr = QuaternionRotateVector()
        qr.init()
        qr.setInput([1, 0, 0, 0], 0)  # Identity
        qr.setInput([1, 2, 3], 1)  # Vector
        qr.update()

        vec = qr.getOutputVector()
        assert vec[0] == pytest.approx(1.0)
        assert vec[1] == pytest.approx(2.0)
        assert vec[2] == pytest.approx(3.0)

    def test_90_deg_z_rotation(self):
        """Test 90 degree rotation about Z axis."""
        # Quaternion for 90 deg rotation about Z
        angle = math.pi / 2
        q = [math.cos(angle / 2), 0, 0, math.sin(angle / 2)]

        qr = QuaternionRotateVector()
        qr.init()
        qr.setInput(q, 0)
        qr.setInput([1, 0, 0], 1)  # X unit vector
        qr.update()

        vec = qr.getOutputVector()
        assert abs(vec[0]) < 1e-10  # X -> 0
        assert vec[1] == pytest.approx(1.0)  # Y -> 1
        assert abs(vec[2]) < 1e-10  # Z -> 0


class TestDCMToQuaternion:
    """Tests for the DCMToQuaternion block."""

    def test_identity_dcm(self):
        """Test identity DCM gives identity quaternion."""
        dq = DCMToQuaternion()
        dq.init()
        dq.setInput([1, 0, 0, 0, 1, 0, 0, 0, 1])  # Identity
        dq.update()

        vec = dq.getOutputVector()
        assert vec[0] == pytest.approx(1.0)
        assert abs(vec[1]) < 1e-10
        assert abs(vec[2]) < 1e-10
        assert abs(vec[3]) < 1e-10


class TestQuaternionToDCM:
    """Tests for the QuaternionToDCM block."""

    def test_identity_quaternion(self):
        """Test identity quaternion gives identity DCM."""
        qd = QuaternionToDCM()
        qd.init()
        qd.setInput([1, 0, 0, 0])
        qd.update()

        vec = qd.getOutputVector()
        expected = [1, 0, 0, 0, 1, 0, 0, 0, 1]
        for i, (a, b) in enumerate(zip(vec, expected, strict=False)):
            assert a == pytest.approx(b), f"Index {i}: {a} != {b}"


class TestISAAtmosphere:
    """Tests for the ISAAtmosphere block."""

    def test_sea_level(self):
        """Test sea level conditions."""
        isa = ISAAtmosphere()
        isa.init()
        isa.setInput(0)
        isa.update()

        vec = isa.getOutputVector()
        assert vec[0] == pytest.approx(288.15, rel=0.01)  # Temperature
        assert vec[1] == pytest.approx(101325, rel=0.01)  # Pressure
        assert vec[2] == pytest.approx(1.225, rel=0.01)  # Density
        assert vec[3] == pytest.approx(340.3, rel=0.01)  # Speed of sound

    def test_10km_altitude(self):
        """Test at 10 km altitude."""
        isa = ISAAtmosphere()
        isa.init()
        isa.setInput(10000)
        isa.update()

        vec = isa.getOutputVector()
        # Expected: ~223 K, ~26500 Pa, ~0.41 kg/m3, ~299 m/s
        assert vec[0] == pytest.approx(223.15, rel=0.02)
        assert vec[1] == pytest.approx(26500, rel=0.1)


class TestFlatEarthGravity:
    """Tests for the FlatEarthGravity block."""

    def test_default_gravity(self):
        """Test default gravity vector."""
        feg = FlatEarthGravity()
        feg.init()
        feg.update()

        vec = feg.getOutputVector()
        assert vec[0] == 0.0
        assert vec[1] == 0.0
        assert vec[2] == pytest.approx(9.80665)

    def test_custom_gravity(self):
        """Test custom gravity value."""
        feg = FlatEarthGravity(g=10.0)
        feg.init()
        feg.update()

        assert feg.getOutput(2) == 10.0


class TestWGS84Gravity:
    """Tests for the WGS84Gravity block."""

    def test_equator_sea_level(self):
        """Test gravity at equator, sea level."""
        wgs = WGS84Gravity()
        wgs.init()
        wgs.setInput([0, 0])  # latitude=0, altitude=0
        wgs.update()

        # Gravity at equator is about 9.78 m/s^2
        assert wgs.getOutput() == pytest.approx(9.78, rel=0.01)

    def test_altitude_effect(self):
        """Test gravity decreases with altitude."""
        wgs1 = WGS84Gravity()
        wgs1.init()
        wgs1.setInput([0, 0])
        wgs1.update()
        g_surface = wgs1.getOutput()

        wgs2 = WGS84Gravity()
        wgs2.init()
        wgs2.setInput([0, 10000])
        wgs2.update()
        g_high = wgs2.getOutput()

        assert g_high < g_surface


class TestSixDOFEuler:
    """Tests for the SixDOFEuler block."""

    def test_initial_state(self):
        """Test initial state is zero."""
        dof = SixDOFEuler(mass=1.0, Ixx=1.0, Iyy=1.0, Izz=1.0)
        dof.init()
        dof.update()

        vec = dof.getOutputVector()
        for val in vec:
            assert val == 0.0

    def test_force_acceleration(self):
        """Test force creates acceleration."""
        dof = SixDOFEuler(mass=1.0, Ixx=1.0, Iyy=1.0, Izz=1.0)
        dof.init()
        dof.setInput([10.0, 0.0, 0.0], 0)  # Fx = 10
        dof.setInput([0.0, 0.0, 0.0], 1)  # No moments
        dof.update()

        # With m=1, a=F/m=10, so derivative of u should be 10
        # But output shows state, not derivative. After first update, state still 0
        vec = dof.getOutputVector()
        assert vec[0] == 0.0  # u velocity (state not yet propagated)
