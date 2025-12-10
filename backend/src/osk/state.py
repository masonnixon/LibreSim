"""State class - Numerical integrator with multiple integration methods.

Based on H.R. Sells' OSK implementation (updated 4-22-2020).
Supports Euler, RK2, RK4, and Merson's integration methods.
"""


class State:
    """Numerical integrator for state variables.

    Each State object maintains a state vector x where:
    - x[0] is the state value
    - x[1] is the derivative (set by the user's update() method)

    The propagate() method advances x[0] using the chosen integration method.
    """

    # Class-level simulation timing variables
    t = 0.0          # Current simulation time
    t1 = 0.0         # Previous time
    dt = 0.01        # Current time step
    dtp = 0.01       # Primary time step
    ready = 1        # Flag indicating when outputs are ready
    kpass = 0        # Current integration pass (0-4 depending on method)
    method = 'RK4'   # Integration method: 'Euler', 'RK2', 'RK4', 'Merson'
    EPS = 1e-10      # Small epsilon for floating point comparisons
    EVENT = -1       # Event time constant
    tickfirst = 1    # First tick flag
    ticklast = 0     # Last tick flag

    def __init__(self, x=None):
        """Initialize state with optional initial values.

        Args:
            x: Initial state vector [position, velocity] or defaults to [0, 0]
        """
        if x is None:
            x = [0.0, 0.0]
        self.x = list(x)

        # Storage for intermediate values during multi-pass integration
        self.x0 = 0.0    # Initial position for this step
        self.xd0 = 0.0   # Derivative at start
        self.xd1 = 0.0   # Derivative at pass 1
        self.xd2 = 0.0   # Derivative at pass 2
        self.xd3 = 0.0   # Derivative at pass 3
        self.xd4 = 0.0   # Derivative at pass 4 (Merson)

    def set(self):
        """Initialize simulation timing."""
        State.t = 0.0
        State.t1 = 0.0
        State.kpass = 0
        State.ready = 1

    def reset(self, dtp):
        """Reset time step parameters.

        Args:
            dtp: Primary time step
        """
        State.dtp = dtp
        State.dt = dtp
        State.kpass = 0
        State.ready = 1

    def sample(self, sdt, t_event):
        """Determine if it's time to sample based on sample time or event time.

        Args:
            sdt: Sample time interval (use State.EVENT for event-driven)
            t_event: Event time to check against
        """
        if sdt == State.EVENT:
            # Event-driven sampling
            if State.t >= t_event - State.EPS:
                State.ready = 1
        else:
            # Periodic sampling
            State.ready = 1

    def propagate(self):
        """Advance the state using the selected integration method.

        This implements multi-pass integration where each pass computes
        intermediate derivatives and the final pass combines them to
        update the state.
        """
        if State.method == 'Euler':
            self._propagate_euler()
        elif State.method == 'RK2':
            self._propagate_rk2()
        elif State.method == 'RK4':
            self._propagate_rk4()
        elif State.method == 'Merson':
            self._propagate_merson()
        else:
            # Default to RK4
            self._propagate_rk4()

    def _propagate_euler(self):
        """Euler method (1st order) - single pass."""
        if State.kpass == 0:
            self.xd0 = self.x[1]
            self.x[0] = self.x[0] + State.dt * self.xd0

    def _propagate_rk2(self):
        """RK2 method (2nd order) - two passes."""
        if State.kpass == 0:
            # Pass 0: Store initial state, compute half-step
            self.x0 = self.x[0]
            self.xd0 = self.x[1]
            self.x[0] = self.x0 + State.dt / 2.0 * self.xd0
        elif State.kpass == 1:
            # Pass 1: Full step using midpoint slope
            self.xd1 = self.x[1]
            self.x[0] = self.x0 + State.dt * self.xd1

    def _propagate_rk4(self):
        """RK4 method (4th order) - four passes."""
        if State.kpass == 0:
            # Pass 0: Store initial, half-step with initial derivative
            self.x0 = self.x[0]
            self.xd0 = self.x[1]
            self.x[0] = self.x0 + State.dt / 2.0 * self.xd0
        elif State.kpass == 1:
            # Pass 1: Half-step with k2 derivative
            self.xd1 = self.x[1]
            self.x[0] = self.x0 + State.dt / 2.0 * self.xd1
        elif State.kpass == 2:
            # Pass 2: Full-step with k3 derivative
            self.xd2 = self.x[1]
            self.x[0] = self.x0 + State.dt * self.xd2
        elif State.kpass == 3:
            # Pass 3: Combine all derivatives
            self.xd3 = self.x[1]
            self.x[0] = self.x0 + State.dt / 6.0 * (
                self.xd0 + 2.0 * self.xd1 + 2.0 * self.xd2 + self.xd3
            )

    def _propagate_merson(self):
        """Merson's method (4th order with error estimate) - five passes."""
        if State.kpass == 0:
            # k1
            self.x0 = self.x[0]
            self.xd0 = self.x[1]  # k1
            self.x[0] = self.x0 + State.dt / 3.0 * self.xd0
        elif State.kpass == 1:
            # k2
            self.xd1 = self.x[1]  # k2
            self.x[0] = self.x0 + State.dt / 6.0 * (self.xd0 + self.xd1)
        elif State.kpass == 2:
            # k3
            self.xd2 = self.x[1]  # k3
            self.x[0] = self.x0 + State.dt / 8.0 * (self.xd0 + 3.0 * self.xd2)
        elif State.kpass == 3:
            # k4
            self.xd3 = self.x[1]  # k4
            self.x[0] = self.x0 + State.dt / 2.0 * (
                self.xd0 - 3.0 * self.xd2 + 4.0 * self.xd3
            )
        elif State.kpass == 4:
            # k5 - final combination
            self.xd4 = self.x[1]  # k5
            self.x[0] = self.x0 + State.dt / 6.0 * (
                self.xd0 + 4.0 * self.xd3 + self.xd4
            )

    def updateclock(self):
        """Update simulation clock based on integration method passes."""
        # Number of passes for each method
        passes = {
            'Euler': 1,
            'RK2': 2,
            'RK4': 4,
            'Merson': 5
        }
        max_pass = passes.get(State.method, 4)

        State.kpass += 1

        if State.kpass >= max_pass:
            # All passes complete, advance time
            State.kpass = 0
            State.t1 = State.t
            State.t += State.dtp
            State.ready = 1
        else:
            State.ready = 0
            # Set appropriate dt for intermediate passes
            if State.method == 'RK2':
                State.dt = State.dtp / 2.0 if State.kpass == 0 else State.dtp
            elif State.method == 'RK4':
                if State.kpass in [0, 1]:
                    State.dt = State.dtp / 2.0
                else:
                    State.dt = State.dtp
            elif State.method == 'Merson':
                # Merson uses various fractions
                State.dt = State.dtp
