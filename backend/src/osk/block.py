"""Block class - Base class for simulation blocks.

Based on H.R. Sells' OSK implementation (updated 4-22-2020).
All simulation blocks should inherit from this class and implement
init(), update(), and rpt() methods.
"""

from .state import State


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
        self.vState = []      # Vector of State objects (integrators)
        self.initCount = 0    # Initialization counter

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
        state = State(initial)
        self.vState.append(state)
        return state.x

    def set_method(self, method='RK4'):
        """Set the integration method for all states.

        Args:
            method: One of 'Euler', 'RK2', 'RK4', 'Merson'
        """
        State.method = method

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
