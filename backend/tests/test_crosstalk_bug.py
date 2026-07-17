"""Test to reproduce and fix the cross-talk bug in Trigonometry/Product chains.

Bug: When multiple Product blocks share the same Trigonometry block inputs,
the values get mixed up (cross-talk) between independent signal paths.

Expected behavior for theta_x=0, theta_y=5°, theta_z=0:
- sin(theta_x/2) = sin(0) = 0
- cos(theta_x/2) = cos(0) = 1
- sin(theta_y/2) = sin(0.0436) ≈ 0.0436
- cos(theta_y/2) = cos(0.0436) ≈ 0.999

q1 = sin_x * cos_y * cos_z - cos_x * sin_y * sin_z
   = 0 * 0.999 * 1 - 1 * 0.0436 * 0
   = 0

q2 = cos_x * sin_y * cos_z + sin_x * cos_y * sin_z
   = 1 * 0.0436 * 1 + 0 * 0.999 * 0
   = 0.0436 (≈ 2.5° in radians)
"""

import math
from pathlib import Path

import pytest

from src.osk.blocks.math_ops import Gain, Product, Sum, Trigonometry
from src.osk.blocks.sources import Constant
from src.osk.state import State


CUBE_EULER_MDL = Path("/examples/cube_closed_loop_euler.mdl")


class TestCrosstalkBug:
    """Test the cross-talk bug with shared Trigonometry inputs."""

    def setup_method(self):
        """Reset state before each test."""
        State.t = 0.0
        State.dt = 0.01
        State.dtp = 0.01
        State.kpass = 0
        State.ready = 1
        State.method = "RK4"

    def test_trigonometry_independence(self):
        """Test that multiple Trigonometry blocks with same input work independently."""
        # Create a constant input (0.5 radians)
        const = Constant(value=0.5)
        const.init()
        const.update()

        # Create two trig blocks: sin and cos
        sin_block = Trigonometry(function="sin")
        cos_block = Trigonometry(function="cos")

        sin_block.connectInput(const)
        cos_block.connectInput(const)

        sin_block.init()
        cos_block.init()

        # Update both blocks
        sin_block.update()
        cos_block.update()

        expected_sin = math.sin(0.5)
        expected_cos = math.cos(0.5)

        assert abs(sin_block.getOutput() - expected_sin) < 1e-10, (
            f"Sin output {sin_block.getOutput()} != expected {expected_sin}"
        )
        assert abs(cos_block.getOutput() - expected_cos) < 1e-10, (
            f"Cos output {cos_block.getOutput()} != expected {expected_cos}"
        )

    def test_product_with_shared_inputs(self):
        """Test two Product blocks sharing some inputs - core of the bug."""
        # Create constants
        a = Constant(value=2.0)
        b = Constant(value=3.0)
        c = Constant(value=5.0)

        a.init()
        b.init()
        c.init()
        a.update()
        b.update()
        c.update()

        # Product 1: a * b = 2 * 3 = 6
        prod1 = Product(operations="**")
        prod1.connectInput(a, port=0)
        prod1.connectInput(b, port=1)
        prod1.init()

        # Product 2: a * c = 2 * 5 = 10
        prod2 = Product(operations="**")
        prod2.connectInput(a, port=0)  # Shared input!
        prod2.connectInput(c, port=1)
        prod2.init()

        # Update both products
        prod1.update()
        prod2.update()

        assert abs(prod1.getOutput() - 6.0) < 1e-10, (
            f"Product 1 output {prod1.getOutput()} != expected 6.0"
        )
        assert abs(prod2.getOutput() - 10.0) < 1e-10, (
            f"Product 2 output {prod2.getOutput()} != expected 10.0"
        )

    def test_quaternion_q1_calculation(self):
        """Test the actual quaternion q1 calculation that exhibits the bug.

        q1 = sin_x * cos_y * cos_z - cos_x * sin_y * sin_z

        For theta_x=0, theta_y=5°, theta_z=0:
        - half angles: theta_x/2=0, theta_y/2=0.0436rad, theta_z/2=0
        - sin_x=0, cos_x=1, sin_y=0.0436, cos_y=0.999, sin_z=0, cos_z=1
        - q1 = 0*0.999*1 - 1*0.0436*0 = 0
        """
        # Input: theta_y = 5 degrees, others = 0
        theta_x_deg = Constant(value=0.0)
        theta_y_deg = Constant(value=5.0)
        theta_z_deg = Constant(value=0.0)

        theta_x_deg.init()
        theta_y_deg.init()
        theta_z_deg.init()
        theta_x_deg.update()
        theta_y_deg.update()
        theta_z_deg.update()

        # Convert to half-angle radians: deg * pi/360
        deg2rad_half = math.pi / 360.0

        gain_x = Gain(gain=deg2rad_half)
        gain_y = Gain(gain=deg2rad_half)
        gain_z = Gain(gain=deg2rad_half)

        gain_x.connectInput(theta_x_deg)
        gain_y.connectInput(theta_y_deg)
        gain_z.connectInput(theta_z_deg)

        gain_x.init()
        gain_y.init()
        gain_z.init()
        gain_x.update()
        gain_y.update()
        gain_z.update()

        # Trigonometry blocks
        sin_x = Trigonometry(function="sin")
        cos_x = Trigonometry(function="cos")
        sin_y = Trigonometry(function="sin")
        cos_y = Trigonometry(function="cos")
        sin_z = Trigonometry(function="sin")
        cos_z = Trigonometry(function="cos")

        sin_x.connectInput(gain_x)
        cos_x.connectInput(gain_x)
        sin_y.connectInput(gain_y)
        cos_y.connectInput(gain_y)
        sin_z.connectInput(gain_z)
        cos_z.connectInput(gain_z)

        for trig in [sin_x, cos_x, sin_y, cos_y, sin_z, cos_z]:
            trig.init()
            trig.update()

        # Verify trig values
        print(f"sin_x = {sin_x.getOutput():.6f} (expected 0)")
        print(f"cos_x = {cos_x.getOutput():.6f} (expected 1)")
        print(f"sin_y = {sin_y.getOutput():.6f} (expected ~0.0436)")
        print(f"cos_y = {cos_y.getOutput():.6f} (expected ~0.999)")
        print(f"sin_z = {sin_z.getOutput():.6f} (expected 0)")
        print(f"cos_z = {cos_z.getOutput():.6f} (expected 1)")

        # q1_scc = sin_x * cos_y * cos_z
        q1_scc = Product(operations="***")
        q1_scc.connectInput(sin_x, port=0)
        q1_scc.connectInput(cos_y, port=1)
        q1_scc.connectInput(cos_z, port=2)
        q1_scc.init()

        # q1_css = cos_x * sin_y * sin_z
        q1_css = Product(operations="***")
        q1_css.connectInput(cos_x, port=0)
        q1_css.connectInput(sin_y, port=1)
        q1_css.connectInput(sin_z, port=2)
        q1_css.init()

        # Update products
        q1_scc.update()
        q1_css.update()

        print(f"q1_scc = {q1_scc.getOutput():.6f} (expected 0)")
        print(f"q1_css = {q1_css.getOutput():.6f} (expected 0)")

        # q1 = q1_scc - q1_css
        q1_calc = Sum(signs="+-")
        q1_calc.connectInput(q1_scc, port=0)
        q1_calc.connectInput(q1_css, port=1)
        q1_calc.init()
        q1_calc.update()

        print(f"q1 = {q1_calc.getOutput():.6f} (expected 0)")

        # Expected: q1 = 0 (since sin_x=0 and sin_z=0)
        assert abs(q1_calc.getOutput()) < 1e-6, f"q1 should be ~0 but got {q1_calc.getOutput()}"

    def test_quaternion_q2_calculation(self):
        """Test quaternion q2 calculation.

        q2 = cos_x * sin_y * cos_z + sin_x * cos_y * sin_z

        For theta_x=0, theta_y=5°, theta_z=0:
        q2 = 1 * 0.0436 * 1 + 0 * 0.999 * 0 = 0.0436
        """
        # Input: theta_y = 5 degrees, others = 0
        theta_x_deg = Constant(value=0.0)
        theta_y_deg = Constant(value=5.0)
        theta_z_deg = Constant(value=0.0)

        theta_x_deg.init()
        theta_y_deg.init()
        theta_z_deg.init()
        theta_x_deg.update()
        theta_y_deg.update()
        theta_z_deg.update()

        deg2rad_half = math.pi / 360.0

        gain_x = Gain(gain=deg2rad_half)
        gain_y = Gain(gain=deg2rad_half)
        gain_z = Gain(gain=deg2rad_half)

        gain_x.connectInput(theta_x_deg)
        gain_y.connectInput(theta_y_deg)
        gain_z.connectInput(theta_z_deg)

        gain_x.init()
        gain_y.init()
        gain_z.init()
        gain_x.update()
        gain_y.update()
        gain_z.update()

        sin_x = Trigonometry(function="sin")
        cos_x = Trigonometry(function="cos")
        sin_y = Trigonometry(function="sin")
        cos_y = Trigonometry(function="cos")
        sin_z = Trigonometry(function="sin")
        cos_z = Trigonometry(function="cos")

        sin_x.connectInput(gain_x)
        cos_x.connectInput(gain_x)
        sin_y.connectInput(gain_y)
        cos_y.connectInput(gain_y)
        sin_z.connectInput(gain_z)
        cos_z.connectInput(gain_z)

        for trig in [sin_x, cos_x, sin_y, cos_y, sin_z, cos_z]:
            trig.init()
            trig.update()

        # q2_csc = cos_x * sin_y * cos_z
        q2_csc = Product(operations="***")
        q2_csc.connectInput(cos_x, port=0)
        q2_csc.connectInput(sin_y, port=1)
        q2_csc.connectInput(cos_z, port=2)
        q2_csc.init()

        # q2_scs = sin_x * cos_y * sin_z
        q2_scs = Product(operations="***")
        q2_scs.connectInput(sin_x, port=0)
        q2_scs.connectInput(cos_y, port=1)
        q2_scs.connectInput(sin_z, port=2)
        q2_scs.init()

        q2_csc.update()
        q2_scs.update()

        print(f"q2_csc = {q2_csc.getOutput():.6f} (expected ~0.0436)")
        print(f"q2_scs = {q2_scs.getOutput():.6f} (expected 0)")

        # q2 = q2_csc + q2_scs
        q2_calc = Sum(signs="++")
        q2_calc.connectInput(q2_csc, port=0)
        q2_calc.connectInput(q2_scs, port=1)
        q2_calc.init()
        q2_calc.update()

        expected_q2 = math.sin(5.0 * math.pi / 360.0)  # sin(theta_y/2)
        print(f"q2 = {q2_calc.getOutput():.6f} (expected {expected_q2:.6f})")

        assert abs(q2_calc.getOutput() - expected_q2) < 1e-6, (
            f"q2 should be ~{expected_q2} but got {q2_calc.getOutput()}"
        )

    def test_both_q1_and_q2_together(self):
        """Test both q1 and q2 calculations together - the actual bug scenario.

        This mimics the real model where all Product blocks share trig inputs.
        """
        # Input: theta_y = 5 degrees, others = 0
        theta_x_deg = Constant(value=0.0)
        theta_y_deg = Constant(value=5.0)
        theta_z_deg = Constant(value=0.0)

        for c in [theta_x_deg, theta_y_deg, theta_z_deg]:
            c.init()
            c.update()

        deg2rad_half = math.pi / 360.0

        gain_x = Gain(gain=deg2rad_half)
        gain_y = Gain(gain=deg2rad_half)
        gain_z = Gain(gain=deg2rad_half)

        gain_x.connectInput(theta_x_deg)
        gain_y.connectInput(theta_y_deg)
        gain_z.connectInput(theta_z_deg)

        for g in [gain_x, gain_y, gain_z]:
            g.init()
            g.update()

        # All six trig blocks (shared inputs to multiple products)
        sin_x = Trigonometry(function="sin")
        cos_x = Trigonometry(function="cos")
        sin_y = Trigonometry(function="sin")
        cos_y = Trigonometry(function="cos")
        sin_z = Trigonometry(function="sin")
        cos_z = Trigonometry(function="cos")

        sin_x.connectInput(gain_x)
        cos_x.connectInput(gain_x)
        sin_y.connectInput(gain_y)
        cos_y.connectInput(gain_y)
        sin_z.connectInput(gain_z)
        cos_z.connectInput(gain_z)

        for trig in [sin_x, cos_x, sin_y, cos_y, sin_z, cos_z]:
            trig.init()
            trig.update()

        # --- Q1 calculation ---
        # q1_scc = sin_x * cos_y * cos_z
        q1_scc = Product(operations="***")
        q1_scc.connectInput(sin_x, port=0)
        q1_scc.connectInput(cos_y, port=1)
        q1_scc.connectInput(cos_z, port=2)
        q1_scc.init()

        # q1_css = cos_x * sin_y * sin_z
        q1_css = Product(operations="***")
        q1_css.connectInput(cos_x, port=0)
        q1_css.connectInput(sin_y, port=1)
        q1_css.connectInput(sin_z, port=2)
        q1_css.init()

        # --- Q2 calculation ---
        # q2_csc = cos_x * sin_y * cos_z
        q2_csc = Product(operations="***")
        q2_csc.connectInput(cos_x, port=0)
        q2_csc.connectInput(sin_y, port=1)
        q2_csc.connectInput(cos_z, port=2)
        q2_csc.init()

        # q2_scs = sin_x * cos_y * sin_z
        q2_scs = Product(operations="***")
        q2_scs.connectInput(sin_x, port=0)
        q2_scs.connectInput(cos_y, port=1)
        q2_scs.connectInput(sin_z, port=2)
        q2_scs.init()

        # Update ALL products (simulating topological order execution)
        q1_scc.update()
        q1_css.update()
        q2_csc.update()
        q2_scs.update()

        # Sum blocks for final quaternion components
        q1_calc = Sum(signs="+-")
        q1_calc.connectInput(q1_scc, port=0)
        q1_calc.connectInput(q1_css, port=1)
        q1_calc.init()
        q1_calc.update()

        q2_calc = Sum(signs="++")
        q2_calc.connectInput(q2_csc, port=0)
        q2_calc.connectInput(q2_scs, port=1)
        q2_calc.init()
        q2_calc.update()

        # Print intermediate values for debugging
        print("\n=== Trig outputs ===")
        print(f"sin_x = {sin_x.getOutput():.10f} (expected 0)")
        print(f"cos_x = {cos_x.getOutput():.10f} (expected 1)")
        print(f"sin_y = {sin_y.getOutput():.10f} (expected ~0.0436)")
        print(f"cos_y = {cos_y.getOutput():.10f} (expected ~0.999)")
        print(f"sin_z = {sin_z.getOutput():.10f} (expected 0)")
        print(f"cos_z = {cos_z.getOutput():.10f} (expected 1)")

        print("\n=== Product outputs ===")
        print(f"q1_scc (sin_x*cos_y*cos_z) = {q1_scc.getOutput():.10f} (expected 0)")
        print(f"q1_css (cos_x*sin_y*sin_z) = {q1_css.getOutput():.10f} (expected 0)")
        print(f"q2_csc (cos_x*sin_y*cos_z) = {q2_csc.getOutput():.10f} (expected ~0.0436)")
        print(f"q2_scs (sin_x*cos_y*sin_z) = {q2_scs.getOutput():.10f} (expected 0)")

        print("\n=== Final quaternion components ===")
        print(f"q1 = {q1_calc.getOutput():.10f} (expected 0)")
        print(f"q2 = {q2_calc.getOutput():.10f} (expected ~0.0436)")

        expected_q2 = math.sin(5.0 * math.pi / 360.0)

        # THE BUG: q1 should be 0, but if there's cross-talk it will be non-zero
        assert abs(q1_calc.getOutput()) < 1e-6, f"q1 should be ~0 but got {q1_calc.getOutput()}"

        assert abs(q2_calc.getOutput() - expected_q2) < 1e-6, (
            f"q2 should be ~{expected_q2} but got {q2_calc.getOutput()}"
        )


class TestProductBlockInputHandling:
    """Detailed tests for Product block input handling."""

    def setup_method(self):
        State.t = 0.0
        State.dt = 0.01
        State.dtp = 0.01
        State.kpass = 0
        State.ready = 1

    def test_product_input_values_stored_correctly(self):
        """Test that Product stores input values correctly in self.inputs."""
        c1 = Constant(value=2.0)
        c2 = Constant(value=3.0)
        c3 = Constant(value=5.0)

        for c in [c1, c2, c3]:
            c.init()
            c.update()

        prod = Product(operations="***")
        prod.connectInput(c1, port=0)
        prod.connectInput(c2, port=1)
        prod.connectInput(c3, port=2)
        prod.init()

        # Before update
        print(f"Before update: inputs = {prod.inputs}")

        prod.update()

        # After update
        print(f"After update: inputs = {prod.inputs}")
        print(f"Output = {prod.getOutput()}")

        assert prod.inputs[0] == 2.0, f"Input 0 should be 2.0, got {prod.inputs[0]}"
        assert prod.inputs[1] == 3.0, f"Input 1 should be 3.0, got {prod.inputs[1]}"
        assert prod.inputs[2] == 5.0, f"Input 2 should be 5.0, got {prod.inputs[2]}"
        assert prod.getOutput() == 30.0, f"Output should be 30.0, got {prod.getOutput()}"

    def test_multiple_products_same_source(self):
        """Test multiple Products reading from the same source block."""
        source = Constant(value=7.0)
        source.init()
        source.update()

        # Two products both using the same source
        prod1 = Product(operations="**")
        prod1.connectInput(source, port=0)
        prod1.connectInput(source, port=1)
        prod1.init()

        prod2 = Product(operations="**")
        prod2.connectInput(source, port=0)
        prod2.connectInput(source, port=1)
        prod2.init()

        prod1.update()
        prod2.update()

        # Both should output 49 (7*7)
        assert prod1.getOutput() == 49.0, f"Prod1 should be 49.0, got {prod1.getOutput()}"
        assert prod2.getOutput() == 49.0, f"Prod2 should be 49.0, got {prod2.getOutput()}"


class TestOSKAdapterCrosstalk:
    """Test cross-talk through the OSK adapter (full simulation pipeline)."""

    def test_quaternion_model_via_adapter(self):
        """Test the quaternion calculation through the full OSK adapter pipeline.

        This simulates what happens when the frontend sends a model to the backend.
        """
        from src.models.block import Block as ModelBlock
        from src.models.block import Connection, Port
        from src.models.model import Model, ModelMetadata
        from src.models.simulation import SimulationConfig, SolverType
        from src.simulation.compiler import ModelCompiler
        from src.simulation.osk_adapter import OSKAdapter

        # Build the model: theta_x=0, theta_y=5, theta_z=0 -> quaternion
        blocks = []
        connections = []

        # --- Source blocks ---
        theta_x = ModelBlock(
            id="theta_x",
            type="constant",
            name="theta_x_deg",
            position={"x": 0, "y": 0},
            parameters={"value": 0.0},
            input_ports=[],
            output_ports=[Port(id="theta_x-out-0", name="out", position="right")],
        )
        theta_y = ModelBlock(
            id="theta_y",
            type="constant",
            name="theta_y_deg",
            position={"x": 0, "y": 100},
            parameters={"value": 5.0},
            input_ports=[],
            output_ports=[Port(id="theta_y-out-0", name="out", position="right")],
        )
        theta_z = ModelBlock(
            id="theta_z",
            type="constant",
            name="theta_z_deg",
            position={"x": 0, "y": 200},
            parameters={"value": 0.0},
            input_ports=[],
            output_ports=[Port(id="theta_z-out-0", name="out", position="right")],
        )
        blocks.extend([theta_x, theta_y, theta_z])

        # --- Gain blocks (deg to half-rad) ---
        deg2rad_half = math.pi / 360.0
        gain_x = ModelBlock(
            id="gain_x",
            type="gain",
            name="deg2rad_half_x",
            position={"x": 100, "y": 0},
            parameters={"gain": deg2rad_half},
            input_ports=[Port(id="gain_x-in-0", name="in", position="left")],
            output_ports=[Port(id="gain_x-out-0", name="out", position="right")],
        )
        gain_y = ModelBlock(
            id="gain_y",
            type="gain",
            name="deg2rad_half_y",
            position={"x": 100, "y": 100},
            parameters={"gain": deg2rad_half},
            input_ports=[Port(id="gain_y-in-0", name="in", position="left")],
            output_ports=[Port(id="gain_y-out-0", name="out", position="right")],
        )
        gain_z = ModelBlock(
            id="gain_z",
            type="gain",
            name="deg2rad_half_z",
            position={"x": 100, "y": 200},
            parameters={"gain": deg2rad_half},
            input_ports=[Port(id="gain_z-in-0", name="in", position="left")],
            output_ports=[Port(id="gain_z-out-0", name="out", position="right")],
        )
        blocks.extend([gain_x, gain_y, gain_z])

        # Connect constants to gains
        connections.extend(
            [
                Connection(
                    id="c1",
                    source_block_id="theta_x",
                    source_port_id="theta_x-out-0",
                    target_block_id="gain_x",
                    target_port_id="gain_x-in-0",
                ),
                Connection(
                    id="c2",
                    source_block_id="theta_y",
                    source_port_id="theta_y-out-0",
                    target_block_id="gain_y",
                    target_port_id="gain_y-in-0",
                ),
                Connection(
                    id="c3",
                    source_block_id="theta_z",
                    source_port_id="theta_z-out-0",
                    target_block_id="gain_z",
                    target_port_id="gain_z-in-0",
                ),
            ]
        )

        # --- Trigonometry blocks ---
        sin_x = ModelBlock(
            id="sin_x",
            type="trigonometry",
            name="sin_half_x",
            position={"x": 200, "y": 0},
            parameters={"function": "sin"},
            input_ports=[Port(id="sin_x-in-0", name="in", position="left")],
            output_ports=[Port(id="sin_x-out-0", name="out", position="right")],
        )
        cos_x = ModelBlock(
            id="cos_x",
            type="trigonometry",
            name="cos_half_x",
            position={"x": 200, "y": 50},
            parameters={"function": "cos"},
            input_ports=[Port(id="cos_x-in-0", name="in", position="left")],
            output_ports=[Port(id="cos_x-out-0", name="out", position="right")],
        )
        sin_y = ModelBlock(
            id="sin_y",
            type="trigonometry",
            name="sin_half_y",
            position={"x": 200, "y": 100},
            parameters={"function": "sin"},
            input_ports=[Port(id="sin_y-in-0", name="in", position="left")],
            output_ports=[Port(id="sin_y-out-0", name="out", position="right")],
        )
        cos_y = ModelBlock(
            id="cos_y",
            type="trigonometry",
            name="cos_half_y",
            position={"x": 200, "y": 150},
            parameters={"function": "cos"},
            input_ports=[Port(id="cos_y-in-0", name="in", position="left")],
            output_ports=[Port(id="cos_y-out-0", name="out", position="right")],
        )
        sin_z = ModelBlock(
            id="sin_z",
            type="trigonometry",
            name="sin_half_z",
            position={"x": 200, "y": 200},
            parameters={"function": "sin"},
            input_ports=[Port(id="sin_z-in-0", name="in", position="left")],
            output_ports=[Port(id="sin_z-out-0", name="out", position="right")],
        )
        cos_z = ModelBlock(
            id="cos_z",
            type="trigonometry",
            name="cos_half_z",
            position={"x": 200, "y": 250},
            parameters={"function": "cos"},
            input_ports=[Port(id="cos_z-in-0", name="in", position="left")],
            output_ports=[Port(id="cos_z-out-0", name="out", position="right")],
        )
        blocks.extend([sin_x, cos_x, sin_y, cos_y, sin_z, cos_z])

        # Connect gains to trig
        connections.extend(
            [
                Connection(
                    id="c4",
                    source_block_id="gain_x",
                    source_port_id="gain_x-out-0",
                    target_block_id="sin_x",
                    target_port_id="sin_x-in-0",
                ),
                Connection(
                    id="c5",
                    source_block_id="gain_x",
                    source_port_id="gain_x-out-0",
                    target_block_id="cos_x",
                    target_port_id="cos_x-in-0",
                ),
                Connection(
                    id="c6",
                    source_block_id="gain_y",
                    source_port_id="gain_y-out-0",
                    target_block_id="sin_y",
                    target_port_id="sin_y-in-0",
                ),
                Connection(
                    id="c7",
                    source_block_id="gain_y",
                    source_port_id="gain_y-out-0",
                    target_block_id="cos_y",
                    target_port_id="cos_y-in-0",
                ),
                Connection(
                    id="c8",
                    source_block_id="gain_z",
                    source_port_id="gain_z-out-0",
                    target_block_id="sin_z",
                    target_port_id="sin_z-in-0",
                ),
                Connection(
                    id="c9",
                    source_block_id="gain_z",
                    source_port_id="gain_z-out-0",
                    target_block_id="cos_z",
                    target_port_id="cos_z-in-0",
                ),
            ]
        )

        # --- Product blocks for q1 ---
        # q1_scc = sin_x * cos_y * cos_z
        q1_scc = ModelBlock(
            id="q1_scc",
            type="product",
            name="q1_scc",
            position={"x": 300, "y": 0},
            parameters={"operations": "***"},
            input_ports=[
                Port(id="q1_scc-in-0", name="in1", position="left"),
                Port(id="q1_scc-in-1", name="in2", position="left"),
                Port(id="q1_scc-in-2", name="in3", position="left"),
            ],
            output_ports=[Port(id="q1_scc-out-0", name="out", position="right")],
        )
        # q1_css = cos_x * sin_y * sin_z
        q1_css = ModelBlock(
            id="q1_css",
            type="product",
            name="q1_css",
            position={"x": 300, "y": 50},
            parameters={"operations": "***"},
            input_ports=[
                Port(id="q1_css-in-0", name="in1", position="left"),
                Port(id="q1_css-in-1", name="in2", position="left"),
                Port(id="q1_css-in-2", name="in3", position="left"),
            ],
            output_ports=[Port(id="q1_css-out-0", name="out", position="right")],
        )
        blocks.extend([q1_scc, q1_css])

        # Connect trig to q1 products
        connections.extend(
            [
                Connection(
                    id="c10",
                    source_block_id="sin_x",
                    source_port_id="sin_x-out-0",
                    target_block_id="q1_scc",
                    target_port_id="q1_scc-in-0",
                ),
                Connection(
                    id="c11",
                    source_block_id="cos_y",
                    source_port_id="cos_y-out-0",
                    target_block_id="q1_scc",
                    target_port_id="q1_scc-in-1",
                ),
                Connection(
                    id="c12",
                    source_block_id="cos_z",
                    source_port_id="cos_z-out-0",
                    target_block_id="q1_scc",
                    target_port_id="q1_scc-in-2",
                ),
                Connection(
                    id="c13",
                    source_block_id="cos_x",
                    source_port_id="cos_x-out-0",
                    target_block_id="q1_css",
                    target_port_id="q1_css-in-0",
                ),
                Connection(
                    id="c14",
                    source_block_id="sin_y",
                    source_port_id="sin_y-out-0",
                    target_block_id="q1_css",
                    target_port_id="q1_css-in-1",
                ),
                Connection(
                    id="c15",
                    source_block_id="sin_z",
                    source_port_id="sin_z-out-0",
                    target_block_id="q1_css",
                    target_port_id="q1_css-in-2",
                ),
            ]
        )

        # --- Product blocks for q2 ---
        # q2_csc = cos_x * sin_y * cos_z
        q2_csc = ModelBlock(
            id="q2_csc",
            type="product",
            name="q2_csc",
            position={"x": 300, "y": 100},
            parameters={"operations": "***"},
            input_ports=[
                Port(id="q2_csc-in-0", name="in1", position="left"),
                Port(id="q2_csc-in-1", name="in2", position="left"),
                Port(id="q2_csc-in-2", name="in3", position="left"),
            ],
            output_ports=[Port(id="q2_csc-out-0", name="out", position="right")],
        )
        # q2_scs = sin_x * cos_y * sin_z
        q2_scs = ModelBlock(
            id="q2_scs",
            type="product",
            name="q2_scs",
            position={"x": 300, "y": 150},
            parameters={"operations": "***"},
            input_ports=[
                Port(id="q2_scs-in-0", name="in1", position="left"),
                Port(id="q2_scs-in-1", name="in2", position="left"),
                Port(id="q2_scs-in-2", name="in3", position="left"),
            ],
            output_ports=[Port(id="q2_scs-out-0", name="out", position="right")],
        )
        blocks.extend([q2_csc, q2_scs])

        # Connect trig to q2 products
        connections.extend(
            [
                Connection(
                    id="c16",
                    source_block_id="cos_x",
                    source_port_id="cos_x-out-0",
                    target_block_id="q2_csc",
                    target_port_id="q2_csc-in-0",
                ),
                Connection(
                    id="c17",
                    source_block_id="sin_y",
                    source_port_id="sin_y-out-0",
                    target_block_id="q2_csc",
                    target_port_id="q2_csc-in-1",
                ),
                Connection(
                    id="c18",
                    source_block_id="cos_z",
                    source_port_id="cos_z-out-0",
                    target_block_id="q2_csc",
                    target_port_id="q2_csc-in-2",
                ),
                Connection(
                    id="c19",
                    source_block_id="sin_x",
                    source_port_id="sin_x-out-0",
                    target_block_id="q2_scs",
                    target_port_id="q2_scs-in-0",
                ),
                Connection(
                    id="c20",
                    source_block_id="cos_y",
                    source_port_id="cos_y-out-0",
                    target_block_id="q2_scs",
                    target_port_id="q2_scs-in-1",
                ),
                Connection(
                    id="c21",
                    source_block_id="sin_z",
                    source_port_id="sin_z-out-0",
                    target_block_id="q2_scs",
                    target_port_id="q2_scs-in-2",
                ),
            ]
        )

        # --- Sum blocks for final quaternion ---
        q1_calc = ModelBlock(
            id="q1_calc",
            type="sum",
            name="q1_calc",
            position={"x": 400, "y": 25},
            parameters={"signs": "+-"},
            input_ports=[
                Port(id="q1_calc-in-0", name="in1", position="left"),
                Port(id="q1_calc-in-1", name="in2", position="left"),
            ],
            output_ports=[Port(id="q1_calc-out-0", name="out", position="right")],
        )
        q2_calc = ModelBlock(
            id="q2_calc",
            type="sum",
            name="q2_calc",
            position={"x": 400, "y": 125},
            parameters={"signs": "++"},
            input_ports=[
                Port(id="q2_calc-in-0", name="in1", position="left"),
                Port(id="q2_calc-in-1", name="in2", position="left"),
            ],
            output_ports=[Port(id="q2_calc-out-0", name="out", position="right")],
        )
        blocks.extend([q1_calc, q2_calc])

        connections.extend(
            [
                Connection(
                    id="c22",
                    source_block_id="q1_scc",
                    source_port_id="q1_scc-out-0",
                    target_block_id="q1_calc",
                    target_port_id="q1_calc-in-0",
                ),
                Connection(
                    id="c23",
                    source_block_id="q1_css",
                    source_port_id="q1_css-out-0",
                    target_block_id="q1_calc",
                    target_port_id="q1_calc-in-1",
                ),
                Connection(
                    id="c24",
                    source_block_id="q2_csc",
                    source_port_id="q2_csc-out-0",
                    target_block_id="q2_calc",
                    target_port_id="q2_calc-in-0",
                ),
                Connection(
                    id="c25",
                    source_block_id="q2_scs",
                    source_port_id="q2_scs-out-0",
                    target_block_id="q2_calc",
                    target_port_id="q2_calc-in-1",
                ),
            ]
        )

        # --- Scope blocks to capture output ---
        scope_q1 = ModelBlock(
            id="scope_q1",
            type="scope",
            name="Scope_q1",
            position={"x": 500, "y": 25},
            parameters={"numInputs": 1},
            input_ports=[Port(id="scope_q1-in-0", name="in", position="left")],
            output_ports=[],
        )
        scope_q2 = ModelBlock(
            id="scope_q2",
            type="scope",
            name="Scope_q2",
            position={"x": 500, "y": 125},
            parameters={"numInputs": 1},
            input_ports=[Port(id="scope_q2-in-0", name="in", position="left")],
            output_ports=[],
        )
        blocks.extend([scope_q1, scope_q2])

        connections.extend(
            [
                Connection(
                    id="c26",
                    source_block_id="q1_calc",
                    source_port_id="q1_calc-out-0",
                    target_block_id="scope_q1",
                    target_port_id="scope_q1-in-0",
                ),
                Connection(
                    id="c27",
                    source_block_id="q2_calc",
                    source_port_id="q2_calc-out-0",
                    target_block_id="scope_q2",
                    target_port_id="scope_q2-in-0",
                ),
            ]
        )

        # Create model
        model = Model(
            id="test_quaternion",
            metadata=ModelMetadata(name="Test Quaternion Model"),
            blocks=blocks,
            connections=connections,
        )

        # Compile the model
        compiler = ModelCompiler()
        compiled = compiler.compile(model)
        assert compiled.success, f"Compilation failed: {compiled.message}"

        print("\n=== Execution order ===")
        for i, block_id in enumerate(compiled.execution_order):
            print(f"{i}: {block_id}")

        # Initialize the adapter
        adapter = OSKAdapter()
        config = SimulationConfig(
            start_time=0.0,
            stop_time=0.1,
            step_size=0.01,
            solver=SolverType.RK4,
        )
        adapter.initialize(compiled, config)

        # Run one step
        adapter.step(0.0, 0.01)

        # Get the output blocks
        q1_block = adapter.get_block("q1_calc")
        q2_block = adapter.get_block("q2_calc")

        print("\n=== Results ===")
        print(f"q1_calc output: {q1_block.getOutput():.10f} (expected 0)")
        print(f"q2_calc output: {q2_block.getOutput():.10f} (expected ~0.0436)")

        # Check intermediate blocks
        sin_x_block = adapter.get_block("sin_x")
        cos_x_block = adapter.get_block("cos_x")
        sin_y_block = adapter.get_block("sin_y")
        cos_y_block = adapter.get_block("cos_y")
        sin_z_block = adapter.get_block("sin_z")
        cos_z_block = adapter.get_block("cos_z")

        print("\n=== Trig block outputs ===")
        print(f"sin_x: {sin_x_block.getOutput():.10f}")
        print(f"cos_x: {cos_x_block.getOutput():.10f}")
        print(f"sin_y: {sin_y_block.getOutput():.10f}")
        print(f"cos_y: {cos_y_block.getOutput():.10f}")
        print(f"sin_z: {sin_z_block.getOutput():.10f}")
        print(f"cos_z: {cos_z_block.getOutput():.10f}")

        q1_scc_block = adapter.get_block("q1_scc")
        q1_css_block = adapter.get_block("q1_css")
        q2_csc_block = adapter.get_block("q2_csc")
        q2_scs_block = adapter.get_block("q2_scs")

        print("\n=== Product block outputs ===")
        print(f"q1_scc: {q1_scc_block.getOutput():.10f} (sin_x*cos_y*cos_z)")
        print(f"q1_css: {q1_css_block.getOutput():.10f} (cos_x*sin_y*sin_z)")
        print(f"q2_csc: {q2_csc_block.getOutput():.10f} (cos_x*sin_y*cos_z)")
        print(f"q2_scs: {q2_scs_block.getOutput():.10f} (sin_x*cos_y*sin_z)")

        # Check Product block internal state
        print("\n=== Product block internal inputs ===")
        print(f"q1_scc.inputs: {q1_scc_block.inputs}")
        print(f"q1_css.inputs: {q1_css_block.inputs}")
        print(f"q2_csc.inputs: {q2_csc_block.inputs}")
        print(f"q2_scs.inputs: {q2_scs_block.inputs}")

        expected_q2 = math.sin(5.0 * math.pi / 360.0)

        # THE ASSERTIONS
        assert abs(q1_block.getOutput()) < 1e-6, f"q1 should be ~0 but got {q1_block.getOutput()}"

        assert abs(q2_block.getOutput() - expected_q2) < 1e-6, (
            f"q2 should be ~{expected_q2} but got {q2_block.getOutput()}"
        )


class TestMDLImportCrosstalk:
    """Test cross-talk with an actual MDL file import."""

    @pytest.mark.skipif(
        not CUBE_EULER_MDL.exists(),
        reason="requires the external cube_closed_loop_euler.mdl regression fixture",
    )
    def test_cube_euler_mdl_import(self):
        """Test the actual cube_closed_loop_euler.mdl model."""
        from src.models.simulation import SimulationConfig, SolverType
        from src.parsers.mdl_parser import MDLParser
        from src.simulation.compiler import ModelCompiler
        from src.simulation.osk_adapter import OSKAdapter

        # Load the MDL file
        mdl_path = CUBE_EULER_MDL

        content = mdl_path.read_text()
        parser = MDLParser()
        model = parser.parse(content, mdl_path.name)

        print("\n=== Imported model ===")
        print(f"Blocks: {len(model.blocks)}")
        print(f"Connections: {len(model.connections)}")

        # Find the relevant blocks
        block_map = {b.name: b for b in model.blocks}
        print("\n=== Block names ===")
        for name in sorted(block_map.keys()):
            b = block_map[name]
            print(f"  {name}: {b.type}")

        # Compile
        compiler = ModelCompiler()
        compiled = compiler.compile(model)
        assert compiled.success, f"Compilation failed: {compiled.message}"

        print("\n=== Execution order (first 30) ===")
        for i, block_id in enumerate(compiled.execution_order[:30]):
            print(f"{i}: {block_id}")

        # Initialize adapter
        adapter = OSKAdapter()
        config = SimulationConfig(
            start_time=0.0,
            stop_time=0.01,  # Just one step
            step_size=0.001,
            solver=SolverType.RK4,
        )
        adapter.initialize(compiled, config)

        # Run one step
        adapter.step(0.0, 0.001)

        # Get key blocks
        adapter.get_all_blocks()

        # Find blocks by name (they may have been assigned IDs)
        name_to_id = {b.name: b.id for b in model.blocks}

        # Get trig blocks
        if "cos_half_x" in name_to_id:
            cos_x_block = adapter.get_block(name_to_id["cos_half_x"])
            sin_x_block = adapter.get_block(name_to_id["sin_half_x"])
            cos_y_block = adapter.get_block(name_to_id["cos_half_y"])
            sin_y_block = adapter.get_block(name_to_id["sin_half_y"])
            cos_z_block = adapter.get_block(name_to_id["cos_half_z"])
            sin_z_block = adapter.get_block(name_to_id["sin_half_z"])

            print("\n=== Trig block outputs ===")
            print(f"cos_half_x: {cos_x_block.getOutput():.10f}")
            print(f"sin_half_x: {sin_x_block.getOutput():.10f}")
            print(f"cos_half_y: {cos_y_block.getOutput():.10f}")
            print(f"sin_half_y: {sin_y_block.getOutput():.10f}")
            print(f"cos_half_z: {cos_z_block.getOutput():.10f}")
            print(f"sin_half_z: {sin_z_block.getOutput():.10f}")

        # Get q1 blocks
        if "q1_scc" in name_to_id:
            q1_scc_block = adapter.get_block(name_to_id["q1_scc"])
            q1_css_block = adapter.get_block(name_to_id["q1_css"])
            q1_calc_block = adapter.get_block(name_to_id["q1_calc"])

            print("\n=== Q1 Product block outputs ===")
            print(f"q1_scc: {q1_scc_block.getOutput():.10f}")
            print(f"q1_css: {q1_css_block.getOutput():.10f}")

            print("\n=== Q1 Product block INPUTS ===")
            print(f"q1_scc.inputs: {q1_scc_block.inputs}")
            print(f"q1_css.inputs: {q1_css_block.inputs}")

            # Debug: show connected blocks
            print("\n=== Q1 scc connected blocks ===")
            for i, blk in enumerate(q1_scc_block.input_blocks):
                if blk:
                    print(f"  Port {i}: {blk.__class__.__name__} output={blk.getOutput():.6f}")
                else:
                    print(f"  Port {i}: None")

            print("\n=== Q1 css connected blocks ===")
            for i, blk in enumerate(q1_css_block.input_blocks):
                if blk:
                    print(f"  Port {i}: {blk.__class__.__name__} output={blk.getOutput():.6f}")
                else:
                    print(f"  Port {i}: None")

            print("\n=== Q1 calc (q1_scc - q1_css) ===")
            print(f"q1_calc: {q1_calc_block.getOutput():.10f}")

        # Get q2 blocks
        if "q2_csc" in name_to_id:
            q2_csc_block = adapter.get_block(name_to_id["q2_csc"])
            q2_scs_block = adapter.get_block(name_to_id["q2_scs"])
            q2_calc_block = adapter.get_block(name_to_id["q2_calc"])

            print("\n=== Q2 Product block outputs ===")
            print(f"q2_csc: {q2_csc_block.getOutput():.10f}")
            print(f"q2_scs: {q2_scs_block.getOutput():.10f}")

            print("\n=== Q2 Product block INPUTS ===")
            print(f"q2_csc.inputs: {q2_csc_block.inputs}")
            print(f"q2_scs.inputs: {q2_scs_block.inputs}")

            print("\n=== Q2 calc (q2_csc + q2_scs) ===")
            print(f"q2_calc: {q2_calc_block.getOutput():.10f}")

        # Get state blocks (initial + integrator output)
        if "q1_state" in name_to_id:
            q1_state = adapter.get_block(name_to_id["q1_state"])
            q2_state = adapter.get_block(name_to_id["q2_state"])

            print("\n=== State sums (initial + integrated delta) ===")
            print(f"q1_state: {q1_state.getOutput():.10f}")
            print(f"q2_state: {q2_state.getOutput():.10f}")

        # Get euler approx outputs
        if "euler_x_approx" in name_to_id:
            euler_x = adapter.get_block(name_to_id["euler_x_approx"])
            euler_y = adapter.get_block(name_to_id["euler_y_approx"])

            print("\n=== Final Euler approximations (degrees) ===")
            print(f"euler_x_approx: {euler_x.getOutput():.6f} (expected ~0)")
            print(f"euler_y_approx: {euler_y.getOutput():.6f} (expected ~5)")

            # THE BUG: euler_x should be ~0 since theta_x = 0
            # But the bug report says it shows -4.998 (theta_y value, negated)

            # The bug is fixed - euler_x should now be ~0
            assert abs(euler_x.getOutput()) < 0.1, (
                f"euler_x should be ~0 but got {euler_x.getOutput():.6f}"
            )
            assert abs(euler_y.getOutput() - 5.0) < 0.1, (
                f"euler_y should be ~5 but got {euler_y.getOutput():.6f}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
