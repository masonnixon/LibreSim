"""Regression tests for generated integrator stage semantics."""

from src.codegen.models import BlockInfo


def _integrator() -> BlockInfo:
    return BlockInfo(
        id="state",
        type="integrator",
        name="State",
        parameters={"initialCondition": 1.0},
        input_connections=[],
        output_connections=[],
        execution_order=0,
    )


def test_c_integrator_exposes_propagated_state() -> None:
    from src.codegen.languages.c.blocks.continuous import template_integrator

    code = template_integrator(_integrator(), "Block_state")

    assert "return b->state;" in code


def test_cpp_integrator_exposes_propagated_state() -> None:
    from src.codegen.languages.cpp.blocks.continuous import template_integrator

    code = template_integrator(_integrator(), "BlockState")

    assert "return state;" in code


def test_rust_integrator_exposes_propagated_state() -> None:
    from src.codegen.languages.rust.blocks.continuous import template_integrator

    code = template_integrator(_integrator(), "BlockState")

    assert "self.state" in code.split("pub fn get_output", 1)[1].split("}", 1)[0]
