"""Versioned, immutable snapshots for OSK simulation state."""

from __future__ import annotations

import hashlib
import io
import json
import pickle  # nosec B403
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any

from ..models.simulation import SimulationConfig
from ..osk.block import Block
from ..osk.context import SimContext
from ..osk.state import State
from .compiler import CompiledModel

# Pickle payloads are created and restored only as internal, in-memory checkpoints.
SNAPSHOT_SCHEMA_VERSION = 1
BLOCK_CODEC_VERSION = 1


class SnapshotValidationError(ValueError):
    """Raised when a snapshot cannot be safely applied to a simulation."""


@dataclass(frozen=True)
class ContextSnapshot:
    """Immutable image of every mutable :class:`SimContext` field."""

    t: float
    t1: float
    dt: float
    dtp: float
    method: str
    kpass: int
    ready: int
    tickfirst: int
    ticklast: int
    stop: int
    stop0: int

    @classmethod
    def capture(cls, context: SimContext) -> ContextSnapshot:
        return cls(
            t=context.t,
            t1=context.t1,
            dt=context.dt,
            dtp=context.dtp,
            method=context.method,
            kpass=context.kpass,
            ready=context.ready,
            tickfirst=context.tickfirst,
            ticklast=context.ticklast,
            stop=context.stop,
            stop0=context.stop0,
        )

    def validate_boundary(self) -> None:
        if self.kpass != 0 or self.ready != 1:
            raise SnapshotValidationError(
                "Snapshots require a committed simulation boundary (kpass=0, ready=1)"
            )
        if self.dt <= 0 or self.dtp <= 0:
            raise SnapshotValidationError("Snapshot step sizes must be positive")

    def apply(self, context: SimContext) -> None:
        context.t = self.t
        context.t1 = self.t1
        context.dt = self.dt
        context.dtp = self.dtp
        context.method = self.method
        context.kpass = self.kpass
        context.ready = self.ready
        context.tickfirst = self.tickfirst
        context.ticklast = self.ticklast
        context.stop = self.stop
        context.stop0 = self.stop0


@dataclass(frozen=True)
class IntegratorSnapshot:
    """Immutable image of one OSK integrator, including in-flight stage memory."""

    x: tuple[Any, ...]
    x0: Any
    xd0: Any
    xd1: Any
    xd2: Any
    xd3: Any
    xd4: Any

    @classmethod
    def capture(cls, state: State) -> IntegratorSnapshot:
        return cls(
            x=tuple(state.x),
            x0=state.x0,
            xd0=state.xd0,
            xd1=state.xd1,
            xd2=state.xd2,
            xd3=state.xd3,
            xd4=state.xd4,
        )

    def prepare(self, context: SimContext) -> State:
        if len(self.x) != 2:
            raise SnapshotValidationError("Integrator state vectors must contain two values")
        state = State(list(self.x), context=context)
        state.x0 = self.x0
        state.xd0 = self.xd0
        state.xd1 = self.xd1
        state.xd2 = self.xd2
        state.xd3 = self.xd3
        state.xd4 = self.xd4
        return state


@dataclass(frozen=True)
class BlockSnapshot:
    """Opaque immutable state for one registered built-in block."""

    block_id: str
    block_type: str
    codec_version: int
    attributes: bytes
    integrators: tuple[IntegratorSnapshot, ...]
    compact_sink_lengths: tuple[int, ...] = ()


@dataclass(frozen=True)
class AdapterSnapshot:
    """Versioned, model-bound state for one initialized adapter."""

    schema_version: int
    model_fingerprint: str
    config_fingerprint: str
    compact: bool
    context: ContextSnapshot
    blocks: tuple[BlockSnapshot, ...]


@dataclass(frozen=True)
class ResultSeriesSnapshot:
    """Immutable full series or compact generation reference for one result key."""

    key: str
    generation: int
    length: int
    decimation: int
    values: tuple[tuple[float, float], ...] = ()


@dataclass(frozen=True)
class RunnerSnapshot:
    """Versioned runner-plus-adapter checkpoint at one committed boundary."""

    schema_version: int
    compact: bool
    adapter: AdapterSnapshot
    current_time: float
    progress: float
    total_steps: int
    execution_time: float
    status: str
    step_mode: bool
    next_result_generation: int
    results: tuple[ResultSeriesSnapshot, ...]


@dataclass
class PreparedBlockRestore:
    """Decoded block values that can be committed without further validation."""

    block: Block
    states: list[State]
    attributes: dict[str, Any]
    compact_sink_lengths: tuple[int, ...]
    compact_fields: tuple[str, ...]


@dataclass
class PreparedAdapterRestore:
    """Fully validated adapter values awaiting assignment-only commit."""

    context: ContextSnapshot
    blocks: tuple[PreparedBlockRestore, ...]


def _canonical_fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def compiled_model_fingerprint(compiled: CompiledModel) -> str:
    """Return a stable fingerprint of executable model identity and wiring."""
    return _canonical_fingerprint(
        {
            "blocks": [asdict(block) for block in compiled.blocks],
            "executionOrder": compiled.execution_order,
        }
    )


def simulation_config_fingerprint(config: SimulationConfig) -> str:
    """Return a stable fingerprint of every simulation configuration field."""
    return _canonical_fingerprint(config.model_dump(mode="json", by_alias=True))


_STRUCTURAL_FIELDS = frozenset(
    {
        "context",
        "_context_owner",
        "vState",
        "block_id",
        "input_block",
        "input_blocks",
    }
)
_COMPACT_SINK_FIELDS: dict[str, tuple[str, ...]] = {
    "scope": ("times", "values"),
    "scope_3d": ("times", "x_values", "y_values", "z_values"),
    "to_workspace": ("times", "values"),
}


def _contains_graph_reference(value: Any, seen: set[int] | None = None) -> bool:
    if isinstance(value, (Block, SimContext, State)):
        return True
    if value.__class__.__name__ == "_OutputPortView":
        return True
    if isinstance(value, (str, bytes, int, float, complex, bool, type(None))):
        return False
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return False
    seen.add(identity)
    if isinstance(value, dict):
        return any(
            _contains_graph_reference(key, seen) or _contains_graph_reference(item, seen)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple, set, frozenset, deque)):
        return any(_contains_graph_reference(item, seen) for item in value)
    return False


class _AttributePickler(pickle.Pickler):
    def __init__(self, stream: io.BytesIO, state_vectors: dict[int, int]):
        super().__init__(stream, protocol=pickle.HIGHEST_PROTOCOL)
        self._state_vectors = state_vectors

    def persistent_id(self, obj: Any) -> tuple[str, int] | None:
        index = self._state_vectors.get(id(obj))
        if index is not None:
            return ("state-vector", index)
        return None


class _AttributeUnpickler(pickle.Unpickler):
    def __init__(self, stream: io.BytesIO, states: list[State]):
        super().__init__(stream)
        self._states = states

    def persistent_load(self, persistent_id: Any) -> list[Any]:
        if (
            not isinstance(persistent_id, tuple)
            or len(persistent_id) != 2
            or persistent_id[0] != "state-vector"
            or not isinstance(persistent_id[1], int)
            or persistent_id[1] < 0
            or persistent_id[1] >= len(self._states)
        ):
            raise SnapshotValidationError("Invalid integrator reference in block snapshot")
        return self._states[persistent_id[1]].x


def _pickle_attributes(attributes: dict[str, Any], states: list[State]) -> bytes:
    stream = io.BytesIO()
    vectors = {id(state.x): index for index, state in enumerate(states)}
    _AttributePickler(stream, vectors).dump(attributes)
    return stream.getvalue()


def _unpickle_attributes(payload: bytes, states: list[State]) -> dict[str, Any]:
    try:
        value = _AttributeUnpickler(io.BytesIO(payload), states).load()
    except SnapshotValidationError:
        raise
    except Exception as exc:
        raise SnapshotValidationError("Invalid block snapshot payload") from exc
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise SnapshotValidationError("Block snapshot attributes must be a string-keyed mapping")
    if _STRUCTURAL_FIELDS.intersection(value):
        raise SnapshotValidationError("Block snapshot attempts to replace graph ownership")
    return value


class ReflectiveBlockCodec:
    """Complete built-in codec preserving Python, NumPy, RNG, and deque state."""

    version = BLOCK_CODEC_VERSION

    def __init__(self, block_type: str):
        self.block_type = block_type

    def capture(self, block_id: str, block: Block, *, compact: bool) -> BlockSnapshot:
        compact_fields = _COMPACT_SINK_FIELDS.get(self.block_type, ()) if compact else ()
        attributes = {
            name: value
            for name, value in block.__dict__.items()
            if name not in _STRUCTURAL_FIELDS
            and name not in compact_fields
            and not _contains_graph_reference(value)
        }
        lengths: tuple[int, ...] = ()
        if compact_fields:
            values: list[int] = []
            for name in compact_fields:
                collection = getattr(block, name)
                if name == "values" and self.block_type == "scope":
                    values.extend([len(collection), *(len(trace) for trace in collection)])
                else:
                    values.append(len(collection))
            lengths = tuple(values)
        return BlockSnapshot(
            block_id=block_id,
            block_type=self.block_type,
            codec_version=self.version,
            attributes=_pickle_attributes(attributes, block.vState),
            integrators=tuple(IntegratorSnapshot.capture(state) for state in block.vState),
            compact_sink_lengths=lengths,
        )

    def prepare(self, snapshot: BlockSnapshot, block: Block) -> PreparedBlockRestore:
        if snapshot.codec_version != self.version:
            raise SnapshotValidationError(
                f"Unsupported codec version {snapshot.codec_version} for {snapshot.block_type}"
            )
        states = [integrator.prepare(block.context) for integrator in snapshot.integrators]
        attributes = _unpickle_attributes(snapshot.attributes, states)
        compact_fields = _COMPACT_SINK_FIELDS.get(self.block_type, ())
        self._validate_compact_lengths(block, compact_fields, snapshot.compact_sink_lengths)
        return PreparedBlockRestore(
            block=block,
            states=states,
            attributes=attributes,
            compact_sink_lengths=snapshot.compact_sink_lengths,
            compact_fields=compact_fields if snapshot.compact_sink_lengths else (),
        )

    def apply(self, prepared: PreparedBlockRestore) -> None:
        block = prepared.block
        protected = _STRUCTURAL_FIELDS.union(prepared.compact_fields)
        for name, value in list(block.__dict__.items()):
            if (
                name not in protected
                and name not in prepared.attributes
                and not _contains_graph_reference(value)
            ):
                delattr(block, name)
        block.vState = prepared.states
        for name, value in prepared.attributes.items():
            setattr(block, name, value)
        self._truncate_compact_sink(prepared)

    def _validate_compact_lengths(
        self,
        block: Block,
        fields: tuple[str, ...],
        lengths: tuple[int, ...],
    ) -> None:
        if not lengths:
            return
        expected = len(fields)
        if self.block_type == "scope":
            expected += len(block.__dict__["values"])
        if len(lengths) != expected:
            raise SnapshotValidationError("Invalid compact sink length metadata")
        index = 0
        for name in fields:
            collection = getattr(block, name)
            length = lengths[index]
            index += 1
            if length < 0 or length > len(collection):
                raise SnapshotValidationError("Compact sink length exceeds live history")
            if name == "values" and self.block_type == "scope":
                if length != len(collection):
                    raise SnapshotValidationError("Scope trace count does not match snapshot")
                for trace in collection:
                    trace_length = lengths[index]
                    index += 1
                    if trace_length < 0 or trace_length > len(trace):
                        raise SnapshotValidationError(
                            "Compact Scope trace length exceeds live history"
                        )

    def _truncate_compact_sink(self, prepared: PreparedBlockRestore) -> None:
        if not prepared.compact_fields:
            return
        index = 0
        for name in prepared.compact_fields:
            collection = getattr(prepared.block, name)
            length = prepared.compact_sink_lengths[index]
            index += 1
            if name == "values" and self.block_type == "scope":
                for trace in collection:
                    trace_length = prepared.compact_sink_lengths[index]
                    index += 1
                    del trace[trace_length:]
            else:
                del collection[length:]
