"""Regression tests for generated aerospace block semantics."""

import pytest

from src.codegen.languages.python.blocks.aerospace import (
    ecef_to_ned_template,
    great_circle_distance_template,
    lla_to_ecef_template,
    quaternion_rotate_vector_template,
)
from src.codegen.languages.python.blocks.estimation import kalman_filter_template
from src.codegen.models import BlockInfo
from src.osk.blocks.navigation import ECEFToNED, GreatCircleDistance, LLAToECEF
from src.osk.blocks.observers import KalmanFilter
from src.osk.state import State


def _navigation_block(block_type: str, parameters: dict | None = None) -> BlockInfo:
    return BlockInfo(
        id=block_type,
        type=block_type,
        name=block_type,
        parameters=parameters or {},
        input_connections=[],
        output_connections=[],
        execution_order=0,
    )


def _generated_block(template, block_type: str, parameters: dict | None = None):
    namespace: dict[str, object] = {}
    exec(template(_navigation_block(block_type, parameters), "GeneratedBlock"), namespace)
    return namespace["GeneratedBlock"]()


def test_python_generated_lla_to_ecef_matches_osk():
    coordinates = [37.0, -121.9, 1000.0]
    generated = _generated_block(lla_to_ecef_template, "lla_to_ecef")
    osk = LLAToECEF()
    generated.input = coordinates
    osk.setInput(coordinates)

    generated.update(0.0)
    osk.update()

    assert generated.get_output_vector() == pytest.approx(osk.getOutputVector())


def test_python_generated_ecef_to_ned_matches_osk():
    reference = [37.0, -122.0, 0.0]
    coordinates = [-2695453.899675, -4330427.782716, 3817994.975371]
    parameters = {"referenceLat": 37.0, "referenceLon": -122.0, "referenceAlt": 0.0}
    generated = _generated_block(ecef_to_ned_template, "ecef_to_ned", parameters)
    osk = ECEFToNED(reference)
    generated.input = coordinates
    osk.setInput(coordinates)

    generated.update(0.0)
    osk.update()

    assert generated.get_output_vector() == pytest.approx(osk.getOutputVector())


def test_python_generated_great_circle_distance_matches_osk():
    point1 = [37.0, -122.0]
    point2 = [37.0, -121.9]
    generated = _generated_block(great_circle_distance_template, "great_circle_distance")
    osk = GreatCircleDistance()
    generated.input = point1
    generated.input1 = point2
    osk.setInput(point1, 0)
    osk.setInput(point2, 1)

    generated.update(0.0)
    osk.update()

    assert generated.get_output() == pytest.approx(osk.getOutput())


def test_compiled_navigation_templates_convert_degree_inputs():
    from src.codegen.languages.c.blocks.aerospace import (
        great_circle_distance_template as c_distance,
    )
    from src.codegen.languages.c.blocks.aerospace import lla_to_ecef_template as c_lla
    from src.codegen.languages.cpp.blocks.aerospace import (
        great_circle_distance_template as cpp_distance,
    )
    from src.codegen.languages.cpp.blocks.aerospace import lla_to_ecef_template as cpp_lla
    from src.codegen.languages.rust.blocks.aerospace import (
        great_circle_distance_template as rust_distance,
    )
    from src.codegen.languages.rust.blocks.aerospace import lla_to_ecef_template as rust_lla

    lla_block = _navigation_block("lla_to_ecef")
    distance_block = _navigation_block("great_circle_distance")

    for code in (c_lla(lla_block, "Lla"), cpp_lla(lla_block, "Lla")):
        assert "M_PI / 180.0" in code
    for code in (c_distance(distance_block, "Distance"), cpp_distance(distance_block, "Distance")):
        assert "M_PI / 180.0" in code
        assert "6378137.0" in code
    for code in (rust_lla(lla_block, "Lla"), rust_distance(distance_block, "Distance")):
        assert ".to_radians()" in code
        assert "6378137.0" in code


def test_compiled_ramp_templates_honor_json_parameter_names():
    from src.codegen.languages.c.blocks.sources import template_ramp as c_ramp
    from src.codegen.languages.cpp.blocks.sources import template_ramp as cpp_ramp
    from src.codegen.languages.rust.blocks.sources import template_ramp as rust_ramp

    block = _navigation_block("ramp", {"slope": 0.001, "startTime": 2.5, "initialOutput": -122.0})

    for code in (
        c_ramp(block, "Ramp"),
        cpp_ramp(block, "Ramp"),
        rust_ramp(block, "Ramp"),
    ):
        assert "2.5" in code
        assert "-122.0" in code


def test_python_quaternion_vector_rotation_uses_generated_input_contract():
    """Both generated input ports feed the quaternion rotation calculation."""
    block = BlockInfo(
        id="rotate",
        type="quaternion_rotate_vector",
        name="Rotate Vector",
        parameters={},
        input_connections=[],
        output_connections=[],
        execution_order=1,
    )
    namespace: dict[str, object] = {}
    exec(quaternion_rotate_vector_template(block, "GeneratedRotation"), namespace)
    generated = namespace["GeneratedRotation"]()

    generated.init()
    generated.input = [2**-0.5, 0.0, 0.0, 2**-0.5]
    generated.input1 = [1.0, 0.0, 0.0]
    generated.update(0.0)

    assert generated.get_output_vector() == pytest.approx([0.0, 1.0, 0.0])


def test_python_generated_kalman_filter_matches_osk():
    """The generated two-state filter follows OSK's discrete update semantics."""
    parameters = {
        "A": [[1.0, 0.01], [0.0, 1.0]],
        "B": [[0.0], [0.0]],
        "C": [[1.0, 0.0]],
        "Q": [[0.0001, 0.0], [0.0, 0.0001]],
        "R": [[0.25]],
        "initialState": [0.0, 0.0],
        "initialP": [[1.0, 0.0], [0.0, 1.0]],
    }
    block = BlockInfo(
        id="kalman",
        type="kalman_filter",
        name="Kalman Filter",
        parameters=parameters,
        input_connections=[],
        output_connections=[],
        execution_order=1,
    )
    namespace: dict[str, object] = {}
    exec(kalman_filter_template(block, "GeneratedKalman"), namespace)
    generated = namespace["GeneratedKalman"]()
    osk = KalmanFilter(
        parameters["A"],
        parameters["B"],
        parameters["C"],
        parameters["Q"],
        parameters["R"],
        parameters["initialState"],
        parameters["initialP"],
    )
    generated.init()
    osk.init()
    State.ready = 1

    for step in range(100):
        measurement = step * 0.01 + (-0.1 if step % 2 else 0.1)
        generated.input = 0.0
        generated.input1 = measurement
        osk.setInput(0.0, 0)
        osk.setInput(measurement, 1)

        generated.update(step * 0.01)
        osk.update()

        assert generated.get_output_vector() == pytest.approx(osk.getOutputVector())
