"""Compatibility checks for public string-valued enums."""

import json

import pytest

from src.codegen.models import IntegrationMethod, Language
from src.models.block import BlockCategory, DataType, ParameterType, Port
from src.models.simulation import SimulationConfig, SimulationStatus, SolverType


@pytest.mark.parametrize(
    ("member", "value"),
    [
        (Language.PYTHON, "python"),
        (IntegrationMethod.RK4, "rk4"),
        (BlockCategory.SOURCES, "sources"),
        (DataType.DOUBLE, "double"),
        (ParameterType.NUMBER, "number"),
        (SolverType.RK4, "rk4"),
        (SimulationStatus.RUNNING, "running"),
    ],
)
def test_string_enums_preserve_string_equality_and_json_serialization(member: str, value: str):
    assert member == value
    assert str(member) == value
    assert json.dumps(member) == json.dumps(value)


def test_string_enums_preserve_pydantic_serialization():
    config = SimulationConfig(solver=SolverType.RK4)
    port = Port(id="in", name="Input", dataType=DataType.DOUBLE)

    assert config.model_dump(mode="json")["solver"] == "rk4"
    assert port.model_dump(mode="json", by_alias=True)["dataType"] == "double"
