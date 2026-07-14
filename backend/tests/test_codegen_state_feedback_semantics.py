"""Regression tests for generated full-state feedback controllers."""

import pytest

from src.codegen.languages.python.blocks.control_design import (
    lqr_controller_template,
    pole_placement_template,
)
from src.codegen.models import BlockInfo
from src.osk.blocks.control_design import LQRController, PolePlacement


def _block(block_type: str, parameters: dict) -> BlockInfo:
    return BlockInfo(
        id="controller",
        type=block_type,
        name="Controller",
        parameters=parameters,
        input_connections=[],
        output_connections=[],
        execution_order=0,
        input_dimensions=[[2]],
        output_dimensions=[[1]],
    )


def test_lqr_infers_gain_matrix_dimensions() -> None:
    """Adapter-created LQR blocks must consume every column of K."""
    controller = LQRController(K=[[1.0, 1.732]])

    assert controller.num_inputs == 1
    assert controller.num_states == 2
    controller.setInput(1.0, 0)
    controller.setInput(2.0, 1)
    controller.update()
    assert controller.getOutput() == pytest.approx(-(1.0 + 1.732 * 2.0))


def test_pole_placement_infers_gain_vector_dimension() -> None:
    """Adapter-created pole-placement blocks must consume every gain."""
    controller = PolePlacement(K=[4.0, 4.0])

    assert controller.num_states == 2
    controller.setInput(1.0, 0)
    controller.setInput(2.0, 1)
    controller.update()
    assert controller.getOutput() == pytest.approx(-12.0)


@pytest.mark.parametrize(
    ("template", "parameters", "expected"),
    [
        (lqr_controller_template, {"K": [[1.0, 1.732]]}, -(1.0 + 1.732 * 2.0)),
        (pole_placement_template, {"K": [4.0, 4.0]}, -12.0),
    ],
)
def test_python_templates_read_wired_vector_input(
    template, parameters: dict, expected: float
) -> None:
    """Python wiring writes `input`, so controller equations must read that field."""
    namespace: dict[str, object] = {}
    exec(template(_block("controller", parameters), "Controller"), namespace)
    controller_type = namespace["Controller"]
    controller = controller_type()
    controller.input = [1.0, 2.0]
    controller.update(0.0)

    assert controller.get_output() == pytest.approx(expected)
