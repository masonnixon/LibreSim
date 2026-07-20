"""Coverage-completion tests for OSK mathematical blocks.

These cases concentrate on connection adapters, mixed scalar/vector inputs, and
defensive port handling.  Expected values are calculated from the documented
mathematical operations rather than copied from implementation branches.
"""

import math

import pytest

from src.osk.blocks.math_ops import (
    Abs,
    Atan2,
    Bias,
    ComplexToMagnitudeAngle,
    CrossProduct,
    DeadZone,
    Demux,
    Divide,
    DotProduct,
    Exp,
    Gain,
    Hypot,
    Log,
    Log10,
    MagnitudeAngle,
    MathFunction,
    MinMax,
    Mod,
    Mux,
    Polynomial,
    Product,
    Reciprocal,
    Reshape,
    Rounding,
    Saturation,
    Sign,
    SliderGain,
    Sqrt,
    Square,
    Sum,
    Switch,
    Trigonometry,
    UnaryMinus,
    WeightedSum,
)
from src.osk.context import EPS


class ScalarSource:
    def __init__(self, *values):
        self.values = values or (0.0,)

    def getOutput(self, port=0):
        return self.values[port]


class VectorSource(ScalarSource):
    def __init__(self, vector, *values):
        super().__init__(*(values or (17.0, 23.0)))
        self.vector = vector

    def getOutputVector(self):
        return self.vector


@pytest.mark.parametrize(
    ("factory", "vector", "expected"),
    [
        (Abs, [-2.0, 3.0], [2.0, 3.0]),
        (Sign, [-2.0, EPS / 2, 3.0], [-1.0, 0.0, 1.0]),
        (lambda: Saturation(2.0, -1.0), [-2.0, 1.0, 4.0], [-1.0, 1.0, 2.0]),
        (lambda: MathFunction("square"), [-2.0, 3.0], [4.0, 9.0]),
        (lambda: Trigonometry("cos"), [0.0, math.pi], [1.0, -1.0]),
        (lambda: DeadZone(-1.0, 1.0), [-3.0, 0.0, 4.0], [-2.0, 0.0, 3.0]),
        (lambda: Bias(2.5), [-2.0, 3.0], [0.5, 5.5]),
        (Sqrt, [4.0, -1.0], [2.0, 0.0]),
        (Reciprocal, [2.0, 0.0], [0.5, math.inf]),
        (Square, [-2.0, 3.0], [4.0, 9.0]),
        (Exp, [0.0, 1.0], [1.0, math.e]),
        (Log, [1.0, math.e], [0.0, 1.0]),
        (Log10, [1.0, 100.0], [0.0, 2.0]),
        (UnaryMinus, [-2.0, 3.0], [2.0, -3.0]),
    ],
)
def test_unary_blocks_accept_vector_sources_and_scalar_fallbacks(factory, vector, expected):
    block = factory()
    block.connectInput(VectorSource(vector))
    block.update()
    assert block.getOutputVector() == pytest.approx(expected)
    assert block.getOutput() == pytest.approx(expected[0])

    # A vector-capable source returning None must use its selected scalar port.
    block.connectInput(VectorSource(None, 11.0, -3.0), source_port=1)
    block.update()
    assert block.getOutputVector() is None

    # Sources without a vector protocol follow the same scalar adapter path.
    block.connectInput(ScalarSource(5.0))
    block.update()
    assert block.getOutputVector() is None


def test_empty_vector_sources_have_defined_scalar_compatibility():
    for block in (Abs(), Sign(), Saturation(), MathFunction(), Trigonometry(), DeadZone(), Bias()):
        block.connectInput(VectorSource([]))
        block.update()
        assert block.getOutput() == pytest.approx(block.output)
        assert block.getOutputVector() is None


def test_sum_gain_and_product_mixed_connection_modes():
    total = Sum("+-+")
    total.connectInput(VectorSource([2.0, 4.0]), 0)
    total.connectInput(ScalarSource(3.0), 1)
    total.setInput([], 2)
    total.update()
    # Scalars apply to the first element; empty vectors contribute nothing.
    assert total.getOutputVector() == pytest.approx([-1.0, 4.0])
    assert total.getOutput(9) == 0.0
    total.setInput(99.0, 9)
    total.connectInput(ScalarSource(99.0), 9)

    gain = Gain(3.0)
    gain.connectInput(VectorSource([2.0, -1.0]))
    gain.update()
    assert gain.getOutputVector() == pytest.approx([6.0, -3.0])
    gain.connectInput(VectorSource(None, 7.0, 4.0), source_port=1)
    gain.update()
    assert gain.getOutput() == 12.0
    gain.connectInput(ScalarSource(5.0))
    gain.update()
    assert gain.getOutput() == 15.0
    gain.setInput([])
    gain.update()
    assert gain.getOutputVector() is None

    product = Product("*/")
    product.setInput([6.0, 8.0], 0)
    product.setInput([2.0, 0.0], 1)
    product.update()
    assert product.getOutputVector() == pytest.approx([3.0, 8.0 / EPS])
    assert product.getOutput(8) == 0.0

    product = Product("/*")
    product.setInput([8.0], 0)
    product.setInput(0.0, 1)
    product.update()
    assert product.getOutputVector() == pytest.approx([0.0])
    product.connectInput(VectorSource(None, 2.0), 0)
    product.connectInput(ScalarSource(4.0), 1)
    product.update()
    assert product.getOutput() == pytest.approx(2.0)
    product.setInput(1.0, 9)
    product.connectInput(ScalarSource(1.0), 9)

    for divisor in (2.0, 0.0):
        product = Product("*/")
        product.setInput([8.0], 0)
        product.setInput(divisor, 1)
        product.update()
        expected = 4.0 if divisor else 8.0 / EPS
        assert product.getOutputVector() == pytest.approx([expected])
    product = Product("*")
    product.update()
    assert product.getOutputVector() is None


def test_demux_all_source_protocols_and_segment_validation():
    with pytest.raises(ValueError, match="one positive width"):
        Demux(2, [1])
    with pytest.raises(ValueError, match="one positive width"):
        Demux(2, [1, 0])

    demux = Demux(2, [2, 1])
    demux.setInput([1.0, 2.0, 3.0, 99.0])
    demux.update()
    assert demux.outputs == [1.0, 3.0]
    assert demux.getOutputPortVector(0) == [1.0, 2.0]
    assert demux.getOutputPortVector(1) == [3.0]
    assert demux.getOutputPortVector(-1) is None
    assert demux.getOutputPortVector(2) is None

    demux.connectInput(VectorSource([4.0, 5.0, 6.0, 7.0]))
    demux.update()
    assert demux.getOutputVector() == [4.0, 5.0, 6.0]

    class OutputsSource:
        outputs = [8.0, 9.0, 10.0, 11.0]

        def getOutputVector(self):
            return None

    demux.connectInput(OutputsSource())
    demux.update()
    assert demux.outputs == [8.0, 10.0]

    class ObserverSource:
        x_hat = [11.0, 12.0, 13.0]

        def getOutputVector(self):
            return None

    demux.connectInput(ObserverSource())
    demux.update()
    assert demux.outputs == [11.0, 13.0]

    demux.connectInput(ScalarSource(14.0, 15.0), source_port=1)
    demux.update()
    assert demux.outputs[0] == 15.0


@pytest.mark.parametrize(
    ("factory", "left", "right", "expected"),
    [
        (Divide, [8.0, 3.0, -4.0], [2.0, 0.0, -0.0], [4.0, 3.0 / EPS, -4.0 / EPS]),
        (Mod, [8.0, 3.0], [3.0, 0.0], [math.fmod(8.0, 3.0), 0.0]),
        (Atan2, [0.0, 1.0], [1.0, 0.0], [0.0, math.pi / 2]),
        (Hypot, [3.0, 5.0], [4.0, 12.0], [5.0, 13.0]),
    ],
)
def test_binary_vector_blocks_cover_mixed_and_connected_sources(factory, left, right, expected):
    block = factory()
    block.setInput(left, 0)
    block.setInput(right, 1)
    block.update()
    assert block.getOutputVector() == pytest.approx(expected)
    assert block.getOutput(99) == pytest.approx(expected[0])

    # A short vector broadcasts the other input's scalar compatibility value.
    block = factory()
    block.setInput([right[0]], 1)
    block.setInput([left[0], left[-1]], 0)
    block.update()
    assert len(block.getOutputVector()) == 2

    block = factory()
    block.connectInput(VectorSource(left), 0)
    block.connectInput(VectorSource(None, right[0]), 1)
    block.update()
    assert block.getOutputVector() is not None

    block = factory()
    block.connectInput(ScalarSource(left[0]), 0)
    block.connectInput(ScalarSource(right[0]), 1)
    block.update()
    assert math.isfinite(block.getOutput())
    block.setInput(123.0, 9)
    block.connectInput(ScalarSource(123.0), 9)


def test_divide_and_mod_scalar_zero_sign_rules():
    divide = Divide()
    divide.setInput(6.0, 0)
    divide.setInput(0.0, 1)
    divide.update()
    assert divide.getOutput() == pytest.approx(6.0 / EPS)
    divide.setInput(-0.0, 1)
    divide.update()
    assert divide.getOutput() == pytest.approx(6.0 / EPS)

    mod = Mod()
    mod.setInput(6.0, 0)
    mod.setInput(0.0, 1)
    mod.update()
    assert mod.getOutput() == 0.0


@pytest.mark.parametrize("mode", ["floor", "ceil", "round", "fix", "unknown"])
def test_rounding_vector_and_connection_modes(mode):
    block = Rounding(mode)
    block.setInput([-1.7, 1.7])
    block.update()
    functions = {
        "floor": math.floor,
        "ceil": math.ceil,
        "round": round,
        "fix": math.trunc,
        "unknown": lambda value: value,
    }
    assert block.getOutputVector() == [float(functions[mode](v)) for v in [-1.7, 1.7]]
    block.connectInput(VectorSource(None, 2.6))
    block.update()
    assert block.getOutputVector() is None
    block.connectInput(ScalarSource(-2.6))
    block.update()
    assert block.getOutput() == float(functions[mode](-2.6))


@pytest.mark.parametrize("function", ["min", "max"])
def test_minmax_vectors_mixed_lengths_and_source_protocols(function):
    block = MinMax(function, 3)
    block.setInput([1.0], 1)
    block.setInput(2.0, 2)
    block.setInput([3.0, -2.0], 0)
    block.update()
    op = min if function == "min" else max
    assert block.getOutputVector() == [op(3.0, 1.0, 2.0), op(-2.0, 1.0, 2.0)]

    block = MinMax(function, 2)
    block.connectInput(VectorSource([5.0, 1.0]), 0)
    block.connectInput(VectorSource(None, 3.0), 1)
    block.update()
    assert block.getOutputVector() == [op(5.0, 3.0), op(1.0, 3.0)]

    empty = MinMax(function, 0)
    empty.update()
    assert empty.getOutput() == 0.0


def test_dot_and_cross_products_cover_scalar_vector_adapters():
    dot = DotProduct()
    dot.setInput([1.0, 2.0, 3.0], 0)
    dot.setInput([4.0, 5.0], 1)
    dot.update()
    assert dot.getOutput() == 14.0
    dot.setInput(2.0, 1)
    dot.update()
    assert dot.getOutput() == 12.0
    dot.setInput(3.0, 0)
    dot.setInput([4.0, 5.0], 1)
    dot.update()
    assert dot.getOutput() == 27.0
    dot.connectInput(VectorSource(None, 6.0), 0)
    dot.connectInput(ScalarSource(7.0), 1)
    dot.update()
    assert dot.getOutput() == 42.0

    cross = CrossProduct()
    cross.setInput(2.0, 0)
    cross.setInput([0.0, 3.0], 1)
    cross.update()
    assert cross.getOutputVector() == [0.0, 0.0, 6.0]
    assert cross.getOutput(9) == 0.0
    cross.connectInput(VectorSource(None, 4.0), 0)
    cross.connectInput(ScalarSource(5.0), 1)
    cross.update()
    assert cross.getOutputVector() == [0.0, 0.0, 0.0]


def test_reshape_connected_empty_vector_and_scalar_adapters():
    reshape = Reshape([2])
    reshape.connectInput(VectorSource([1.0, 2.0]))
    reshape.update()
    assert reshape.getOutputVector() == [1.0, 2.0]
    reshape.connectInput(VectorSource([]))
    reshape.update()
    assert reshape.getOutputVector() is None
    reshape.connectInput(VectorSource(None, 8.0))
    reshape.update()
    assert reshape.getOutput() == 8.0
    reshape.connectInput(ScalarSource(9.0))
    reshape.update()
    assert reshape.getOutput() == 9.0


def test_trigonometry_domain_and_overflow_errors_are_deterministic():
    asin = Trigonometry("asin")
    asin.setInput(2.0)
    asin.update()
    assert asin.getOutput() == 0.0
    cosh = Trigonometry("cosh")
    cosh.setInput(1e308)
    cosh.update()
    assert cosh.getOutput() == 0.0
    fallback = Trigonometry("not-a-function")
    fallback.setInput(math.pi / 2)
    fallback.update()
    assert fallback.getOutput() == pytest.approx(1.0)


def test_residual_ports_initializers_and_vector_accessors():
    total = Sum("+")
    total.setInput([])
    total.update()
    assert total.getOutputVector() == [0.0]
    total.init()
    assert total.getOutputVector() is None

    product = Product("/")
    product.setInput([], 0)
    product.update()
    assert product.getOutput(0) == pytest.approx(1.0)
    assert product.getOutputVector() == [1.0]

    trig = Trigonometry()
    trig.setInput([0.0])
    trig.update()
    assert trig.getOutput(4) == 0.0

    dead_zone = DeadZone()
    dead_zone.init()
    dead_zone.setInput([2.0])
    dead_zone.update()
    assert dead_zone.getOutput(4) == 0.0

    for block in (Switch(), Mux(2)):
        block.setInput(99.0, 9)
        block.connectInput(ScalarSource(99.0), 9)

    empty_demux = Demux(0)
    empty_demux.setInput(3.0)
    empty_demux.connectInput(ScalarSource(4.0))
    empty_demux.update()
    assert empty_demux.getOutputVector() == []

    bias = Bias(2.0)
    bias.setInput(3.0)
    bias.update()
    assert bias.getOutput() == 5.0
    bias.setInput([1.0])
    bias.update()
    assert bias.getOutput(4) == 0.0

    for factory in (Divide, Mod, Atan2, Hypot):
        block = factory()
        block.setInput([2.0, 4.0], 0)
        block.setInput([1.0, 2.0], 1)
        block.update()
        assert math.isfinite(block.getOutput(1))
        block = factory()
        block.setInput(2.0, 0)
        block.setInput(1.0, 1)
        block.update()
        assert block.getOutputVector() is None

    rounding = Rounding("floor")
    rounding.connectInput(VectorSource([1.8, -1.2]))
    rounding.update()
    assert rounding.getOutput(1) == -2

    minimum = MinMax("min", 2)
    minimum.setInput([4.0, 2.0], 0)
    minimum.setInput([3.0, 1.0], 1)
    minimum.update()
    assert minimum.getOutput(1) == 1.0
    minimum = MinMax("min", 2)
    minimum.setInput(1.0, 0)
    minimum.setInput(2.0, 1)
    minimum.update()
    assert minimum.getOutputVector() is None
    minimum.setInput(9.0, 8)
    minimum.connectInput(ScalarSource(9.0), 8)
    minimum.connectInput(ScalarSource(4.0), 0)
    minimum.update()
    assert minimum.getOutput() == 2.0

    cross = CrossProduct()
    cross.setInput([1.0], 0)
    cross.setInput([0.0, 1.0, 0.0], 1)
    cross.update()
    assert cross.getOutputVector() == [0.0, 0.0, 1.0]
    cross.setInput(1.0, 8)
    cross.connectInput(ScalarSource(1.0), 8)

    dot = DotProduct()
    dot.setInput(1.0, 8)
    dot.connectInput(ScalarSource(1.0), 8)

    hypot = Hypot()
    hypot.setInput([3.0, 5.0], 0)
    hypot.setInput([4.0, 12.0], 1)
    hypot.update()
    assert hypot.getOutput(1) == 13.0
    hypot = Hypot()
    hypot.update()
    assert hypot.getOutputVector() is None


def test_slider_weighted_polynomial_and_complex_adapters():
    slider = SliderGain(2.0)
    slider.connectInput(ScalarSource(3.0))
    slider.update()
    assert slider.getOutput() == 6.0
    slider.connectInput(VectorSource([2.0, 4.0]))
    slider.update()
    assert slider.getOutputVector() == [4.0, 8.0]
    slider.connectInput(VectorSource(None, 5.0))
    slider.update()
    assert slider.getOutputVector() is None

    weighted = WeightedSum([2.0, -1.0])
    weighted.connectInput(ScalarSource(3.0), 0)
    weighted.connectInput(VectorSource([4.0, 6.0]), 1)
    weighted.update()
    assert weighted.getOutputVector() == [2.0, 0.0]
    assert weighted.getOutput(1) == 0.0
    weighted.setInput(3.0, 9)
    weighted.connectInput(ScalarSource(3.0), 9)

    polynomial = Polynomial([2.0, 3.0, 4.0])
    polynomial.connectInput(ScalarSource(2.0))
    polynomial.update()
    # Horner form: (2*2 + 3)*2 + 4 = 18.
    assert polynomial.getOutput() == 18.0
    polynomial.connectInput(VectorSource([1.0, 2.0]))
    polynomial.update()
    assert polynomial.getOutputVector() == [9.0, 18.0]
    polynomial.connectInput(VectorSource(None, 3.0))
    polynomial.update()
    assert polynomial.getOutput() == 31.0

    for block_type in (MagnitudeAngle, ComplexToMagnitudeAngle):
        block = block_type()
        block.setInput(1.0, 9)
        block.connectInput(ScalarSource(1.0), 9)
        block.setInput(3.0, 0)
        block.setInput(math.pi / 2 if block_type is MagnitudeAngle else 4.0, 1)
        block.update()
        expected = [0.0, 3.0] if block_type is MagnitudeAngle else [5.0, math.atan2(4.0, 3.0)]
        assert [block.getOutput(0), block.getOutput(1)] == pytest.approx(expected, abs=1e-12)
        assert block.getOutput(9) == 0.0
