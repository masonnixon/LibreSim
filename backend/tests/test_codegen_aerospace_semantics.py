"""Regression tests for generated aerospace block semantics."""

import pytest

from src.codegen.languages.python.blocks.aerospace import (
    quaternion_rotate_vector_template,
)
from src.codegen.languages.python.blocks.estimation import kalman_filter_template
from src.codegen.models import BlockInfo
from src.osk.blocks.observers import KalmanFilter
from src.osk.state import State


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
