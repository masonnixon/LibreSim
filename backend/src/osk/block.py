"""Block class - Base class for simulation blocks.

Based on H.R. Sells' OSK implementation (updated 4-22-2020).
All simulation blocks should inherit from this class and implement
init(), update(), and rpt() methods.
"""

from threading import RLock

import numpy as np

from .context import SimContext, get_active_context
from .state import State

_GRAPH_BIND_LOCK = RLock()


class Block:
    """Base class for simulation blocks.

    Subclasses must implement:
    - init(): Initialize block state and parameters
    - update(): Compute derivatives (called each integration pass)
    - rpt(): Report/output data (called when State.ready is true)

    Example usage:
        class MyBlock(Block):
            def __init__(self):
                super().__init__()
                self.x = self.addIntegrator()  # Add a state variable

            def init(self):
                self.x[0] = 0.0  # Initial position
                self.gain = 1.0

            def update(self):
                # Compute derivative
                self.x[1] = -self.gain * self.x[0]

            def rpt(self):
                print(f"t={State.t:.3f}, x={self.x[0]:.3f}")
    """

    def __init__(self):
        """Initialize the block with empty state vector."""
        self.context = get_active_context()
        self._context_owner: object | None = None
        self.vState = []  # Vector of State objects (integrators)
        self.initCount = 0  # Initialization counter
        self.block_id: str | None = None

    def init(self):
        """Initialize block - override in subclass.

        Called at the start of each simulation stage.
        Set initial conditions and parameters here.
        """
        pass

    def update(self):
        """Update block - override in subclass.

        Called each integration pass. Compute derivatives here.
        For each integrator state x:
        - x[0] is the current state value (read)
        - x[1] is the derivative (write)
        """
        pass

    def rpt(self):
        """Report block outputs - override in subclass.

        Called when State.ready is true (after complete integration step).
        Output data, update displays, log results here.
        """
        pass

    def state(self):
        """Return default state vector.

        Returns:
            Default [0, 0] state vector
        """
        return [0.0, 0.0]

    def addIntegrator(self, initial=None):
        """Add an integrator (state variable) to this block.

        Args:
            initial: Initial state vector [position, velocity] or None for [0, 0]

        Returns:
            Reference to the state vector x where:
            - x[0] is the state value
            - x[1] is the derivative (set in update())
        """
        if initial is None:
            initial = [0.0, 0.0]
        state = State(initial, context=self.context)
        self.vState.append(state)
        return state.x

    def check_context_binding(self, context: SimContext, owner: object) -> None:
        """Validate a prospective graph binding without mutating this block."""
        if context.owner is not None and context.owner is not owner:
            raise ValueError("SimContext is already owned by another simulation graph")
        if self._context_owner is not None and (
            self._context_owner is not owner or self.context is not context
        ):
            raise ValueError("Block is already owned by another simulation graph")

    def bind_context(self, context: SimContext, owner: object) -> None:
        """Bind this block and its registered integrators to one graph."""
        with _GRAPH_BIND_LOCK:
            self.check_context_binding(context, owner)
            context.claim_owner(owner)
            if self._context_owner is None:
                self.context = context
                for state in self.vState:
                    state.context = context
                self._context_owner = owner

    def set_method(self, method="RK4"):
        """Set the integration method for all states.

        Args:
            method: One of 'Euler', 'RK2', 'RK4', 'Merson'
        """
        self.context.method = method

    def propagateStates(self):
        """Propagate all integrator states.

        Called after update() to advance state variables
        using the selected integration method.
        """
        for state in self.vState:
            state.propagate()

    def getOutput(self, port=0):
        """Get output value from this block.

        Override in subclass to provide specific outputs.

        Args:
            port: Output port index

        Returns:
            Output value (default: first state or 0)
        """
        if self.vState and len(self.vState) > port:
            return self.vState[port].x[0]
        return 0.0

    def setInput(self, value, port=0):
        """Set input value for this block.

        Override in subclass to handle specific inputs.

        Args:
            value: Input value
            port: Input port index
        """
        pass

    def getOutputArray(self, port=0):
        """Get this block's output as a numpy ndarray.

        Base-class bridge over the legacy flat-list signal path: blocks that
        expose a vector output return it as a one-dimensional array, and
        everything else falls back to the scalar port value. Matrix-capable
        blocks override this to return an array with their declared 2-D
        shape.
        """
        if hasattr(self, "getOutputVector"):
            vec = self.getOutputVector()
            if vec is not None:
                return np.asarray(vec, dtype=float)
        return np.asarray(self.getOutput(port), dtype=float)

    def setInputArray(self, value, port=0):
        """Set a vector/matrix input, bridging to the legacy flat-list path.

        Matrix-capable blocks override this; the default delegates to
        setInput() so existing list/tuple input handling is preserved.
        """
        self.setInput(value, port)
