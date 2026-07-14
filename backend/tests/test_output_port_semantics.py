"""Regression tests for declared source-port scalar/vector semantics."""

from src.models.model import Model
from src.osk.block import Block
from src.simulation.compiler import ModelCompiler
from src.simulation.osk_adapter import _OutputPortView


class _MultiOutputBlock(Block):
    def getOutput(self, port=0):
        return [10.0, 20.0, 30.0][port]

    def getOutputVector(self):
        return [10.0, 20.0, 30.0]


def test_scalar_port_view_hides_whole_block_vector():
    view = _OutputPortView(_MultiOutputBlock(), source_port=1, dimensions=[1])

    assert view.getOutput() == 20.0
    assert view.getOutput(2) == 20.0
    assert view.getOutputVector() is None


def test_vector_port_view_exposes_element_and_vector_access():
    view = _OutputPortView(_MultiOutputBlock(), source_port=0, dimensions=[3])

    assert view.getOutput(2) == 30.0
    assert view.getOutputVector() == [10.0, 20.0, 30.0]


def test_compiler_preserves_declared_output_dimensions():
    model = Model.model_validate(
        {
            "id": "dimensions",
            "metadata": {"name": "Dimensions", "description": ""},
            "blocks": [
                {
                    "id": "constant",
                    "type": "constant",
                    "name": "Constant",
                    "position": {"x": 0, "y": 0},
                    "parameters": {"value": [1.0, 2.0, 3.0]},
                    "inputPorts": [],
                    "outputPorts": [
                        {"id": "constant-out", "name": "out", "dimensions": [3]}
                    ],
                },
                {
                    "id": "scope",
                    "type": "scope",
                    "name": "Scope",
                    "position": {"x": 100, "y": 0},
                    "parameters": {},
                    "inputPorts": [{"id": "scope-in", "name": "in", "dimensions": [3]}],
                    "outputPorts": [],
                },
            ],
            "connections": [
                {
                    "id": "connection",
                    "sourceBlockId": "constant",
                    "sourcePortId": "constant-out",
                    "targetBlockId": "scope",
                    "targetPortId": "scope-in",
                }
            ],
        }
    )

    compiled = ModelCompiler().compile(model)

    assert compiled.success
    assert next(block for block in compiled.blocks if block.id == "constant").output_dimensions == [
        [3]
    ]
