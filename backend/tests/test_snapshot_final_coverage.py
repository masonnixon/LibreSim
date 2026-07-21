"""Focused defensive-path coverage for simulation snapshot codecs."""

import io
import pickle

import pytest

from src.osk.block import Block
from src.osk.blocks.sinks import Scope
from src.osk.context import SimContext
from src.osk.state import State
from src.simulation.snapshot import (
    BlockSnapshot,
    ContextSnapshot,
    IntegratorSnapshot,
    PreparedBlockRestore,
    ReflectiveBlockCodec,
    SnapshotValidationError,
    _AttributeUnpickler,
    _contains_graph_reference,
    _pickle_attributes,
    _unpickle_attributes,
)


def test_snapshot_boundary_and_integrator_shape_validation():
    context = ContextSnapshot.capture(SimContext(dt=0.0, dtp=0.01))
    with pytest.raises(SnapshotValidationError, match="step sizes"):
        context.validate_boundary()

    invalid = IntegratorSnapshot((1.0,), 0, 0, 0, 0, 0, 0)
    with pytest.raises(SnapshotValidationError, match="two values"):
        invalid.prepare(SimContext())


def test_graph_reference_detection_handles_special_and_recursive_values():
    assert _contains_graph_reference(Block())
    assert _contains_graph_reference(type("_OutputPortView", (), {})())
    cyclic = []
    cyclic.append(cyclic)
    assert not _contains_graph_reference(cyclic)


def test_attribute_unpickling_rejects_invalid_references_and_payloads():
    state = State([1.0, 2.0], context=SimContext())
    unpickler = _AttributeUnpickler(io.BytesIO(), [state])
    invalid_ids = [
        "bad",
        ("bad", 0),
        ("state-vector", "0"),
        ("state-vector", -1),
        ("state-vector", 2),
    ]
    for persistent_id in invalid_ids:
        with pytest.raises(SnapshotValidationError, match="Invalid integrator reference"):
            unpickler.persistent_load(persistent_id)
    assert unpickler.persistent_load(("state-vector", 0)) is state.x

    payload = _pickle_attributes({"state": state.x}, [state])
    with pytest.raises(SnapshotValidationError, match="Invalid integrator reference"):
        _unpickle_attributes(payload, [])
    with pytest.raises(SnapshotValidationError, match="Invalid block snapshot payload"):
        _unpickle_attributes(b"not a pickle", [])
    with pytest.raises(SnapshotValidationError, match="string-keyed mapping"):
        _unpickle_attributes(pickle.dumps([]), [])
    with pytest.raises(SnapshotValidationError, match="graph ownership"):
        _unpickle_attributes(pickle.dumps({"context": 1}), [])


def test_reflective_codec_version_apply_and_compact_metadata_edges():
    block = Scope(num_inputs=1)
    block.times = [0.0, 1.0]
    block.values = [[1.0, 2.0]]
    codec = ReflectiveBlockCodec("scope")
    snapshot = codec.capture("scope", block, compact=True)

    with pytest.raises(SnapshotValidationError, match="Unsupported codec version"):
        codec.prepare(
            BlockSnapshot(
                snapshot.block_id,
                snapshot.block_type,
                snapshot.codec_version + 1,
                snapshot.attributes,
                snapshot.integrators,
            ),
            block,
        )

    invalid_lengths = [
        ((1,), "metadata"),
        ((3, 1, 2), "exceeds live history"),
        ((2, 0, 2), "trace count"),
        ((2, 1, 3), "trace length"),
    ]
    for lengths, message in invalid_lengths:
        with pytest.raises(SnapshotValidationError, match=message):
            codec._validate_compact_lengths(block, ("times", "values"), lengths)

    prepared = PreparedBlockRestore(
        block=block,
        states=[],
        attributes={"kept": 1},
        compact_sink_lengths=(1, 1, 1),
        compact_fields=("times", "values"),
    )
    block.obsolete = True
    codec.apply(prepared)
    assert not hasattr(block, "obsolete")
    assert block.times == [0.0]
    assert block.values == [[1.0]]
