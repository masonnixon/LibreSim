"""Continuous-time blocks for OSK-based simulation."""

from ..block import Block


class Integrator(Block):
    """Integrator block - integrates input signal.

    Supports both scalar and vector inputs. For vector inputs, each element
    is integrated independently with its own state.

    When external_ic=True, the block has two inputs:
    - Port 0: Signal to integrate
    - Port 1: External initial condition (read only at t=0)
    """

    def __init__(self, initial_condition=0.0, limit_output=False,
                 upper_limit=float('inf'), lower_limit=float('-inf'),
                 external_ic=False):
        super().__init__()
        self.limit_output = limit_output
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.external_ic = external_ic
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0

        # For external IC mode, we have two input blocks
        self.input_blocks = [None, None] if external_ic else None
        self.input_source_ports = [0, 0] if external_ic else None
        self._ic_initialized = False  # Track if we've read the external IC

        # Handle vector or scalar initial condition
        if isinstance(initial_condition, (list, tuple)):
            self._is_vector = True
            self._n = len(initial_condition)
            self.initial_condition = list(initial_condition)
            # Create integrator states for each element
            self._states = [self.addIntegrator([ic, 0.0]) for ic in initial_condition]
            self._input_vector = [0.0] * self._n
        else:
            self._is_vector = False
            self._n = 1
            self.initial_condition = initial_condition
            self.x = self.addIntegrator([initial_condition, 0.0])
            self._states = None
            self._input_vector = None

    def init(self):
        self._ic_initialized = False  # Reset IC flag on init

        if self._is_vector and self._states:
            for i, state in enumerate(self._states):
                ic = self.initial_condition[i] if isinstance(self.initial_condition, list) and i < len(self.initial_condition) else 0.0
                state[0] = ic
                state[1] = 0.0
            self._input_vector = [0.0] * self._n
        elif hasattr(self, 'x'):
            ic = self.initial_condition if not isinstance(self.initial_condition, list) else self.initial_condition[0]
            self.x[0] = ic
            self.x[1] = 0.0

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._setup_vector_mode(len(value))
            for i, v in enumerate(value):
                if i < len(self._input_vector):
                    self._input_vector[i] = v
        else:
            self.input = value

    def _setup_vector_mode(self, n):
        """Set up vector mode with n elements if not already configured."""
        if not self._is_vector or self._n != n:
            self._is_vector = True
            self._n = n
            self._input_vector = [0.0] * n
            # Create integrator states
            if isinstance(self.initial_condition, list):
                self._states = [self.addIntegrator([self.initial_condition[i] if i < len(self.initial_condition) else 0.0, 0.0]) for i in range(n)]
            else:
                self._states = [self.addIntegrator([self.initial_condition if i == 0 else 0.0, 0.0]) for i in range(n)]

    def connectInput(self, block, port=0, source_port=0):
        if self.external_ic and self.input_blocks is not None:
            # External IC mode: port 0 = signal, port 1 = initial condition
            if port < len(self.input_blocks):
                self.input_blocks[port] = block
                self.input_source_ports[port] = source_port
        else:
            # Standard mode: single input
            self.input_block = block
            self.input_source_port = source_port

    def _read_external_ic(self):
        """Read the external initial condition from port 1 and set the integrator state."""
        if not self.external_ic or self._ic_initialized:
            return

        ic_block = self.input_blocks[1] if self.input_blocks and len(self.input_blocks) > 1 else None
        if ic_block is None:
            self._ic_initialized = True
            return

        # Read the IC value from the connected block
        ic_value = ic_block.getOutput(self.input_source_ports[1] if self.input_source_ports else 0)

        # Set the integrator state to this value
        if self._is_vector and self._states:
            # For vector mode, set all states to the same IC (or handle vector IC if needed)
            for state in self._states:
                state[0] = ic_value
        elif hasattr(self, 'x'):
            self.x[0] = ic_value

        self._ic_initialized = True

    def update(self):
        # On first update, read external IC if enabled
        if self.external_ic and not self._ic_initialized:
            self._read_external_ic()

        # Get input signal (port 0 for external_ic mode, or from input_block)
        if self.external_ic and self.input_blocks is not None:
            signal_block = self.input_blocks[0]
            if signal_block is not None:
                # Check for vector output from connected block
                if hasattr(signal_block, 'getOutputVector'):
                    vec = signal_block.getOutputVector()
                    if vec is not None:
                        self._setup_vector_mode(len(vec))
                        self._input_vector = list(vec)
                    else:
                        self.input = signal_block.getOutput(self.input_source_ports[0] if self.input_source_ports else 0)
                else:
                    self.input = signal_block.getOutput(self.input_source_ports[0] if self.input_source_ports else 0)
        elif self.input_block is not None:
            # Check for vector output from connected block
            if hasattr(self.input_block, 'getOutputVector'):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._setup_vector_mode(len(vec))
                    self._input_vector = list(vec)
                else:
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._states:
            # Vector integration
            for i in range(self._n):
                inp = self._input_vector[i] if self._input_vector and i < len(self._input_vector) else 0.0
                self._states[i][1] = inp

                # Apply limits if enabled
                if self.limit_output:
                    if (self._states[i][0] >= self.upper_limit and self._states[i][1] > 0) or \
                       (self._states[i][0] <= self.lower_limit and self._states[i][1] < 0):
                        self._states[i][1] = 0.0
        elif hasattr(self, 'x'):
            # Scalar integration
            self.x[1] = self.input

            # Apply limits if enabled
            if self.limit_output:
                if (self.x[0] >= self.upper_limit and self.x[1] > 0) or \
                   (self.x[0] <= self.lower_limit and self.x[1] < 0):
                    self.x[1] = 0.0

    def getOutput(self, port=0):
        if self._is_vector and self._states:
            if port < len(self._states):
                output = self._states[port][0]
                if self.limit_output:
                    output = max(self.lower_limit, min(self.upper_limit, output))
                return output
            return 0.0
        elif hasattr(self, 'x'):
            output = self.x[0]
            if self.limit_output:
                output = max(self.lower_limit, min(self.upper_limit, output))
            return output
        return 0.0

    def getOutputVector(self):
        """Get the full output vector. Returns None for scalar operation."""
        if self._is_vector and self._states:
            outputs = []
            for state in self._states:
                output = state[0]
                if self.limit_output:
                    output = max(self.lower_limit, min(self.upper_limit, output))
                outputs.append(output)
            return outputs
        return None


class Derivative(Block):
    """Derivative block - differentiates input signal.

    Uses filtered derivative: Ns/(s+N) to avoid noise amplification.
    Supports both scalar and vector inputs.
    """

    def __init__(self, coefficient=100.0):
        super().__init__()
        self.coefficient = coefficient  # N in Ns/(s+N)
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.x = self.addIntegrator([0.0, 0.0])
        self.output = 0.0

        # Vector mode support
        self._is_vector = False
        self._n = 1
        self._states = None
        self._input_vector = None
        self._output_vector = None

    def _setup_vector_mode(self, n):
        """Set up vector mode with n elements if not already configured."""
        if not self._is_vector or self._n != n:
            self._is_vector = True
            self._n = n
            self._input_vector = [0.0] * n
            self._output_vector = [0.0] * n
            # Create filter states for each element
            self._states = [self.addIntegrator([0.0, 0.0]) for _ in range(n)]

    def init(self):
        self.x[0] = 0.0
        self.x[1] = 0.0
        self.output = 0.0
        if self._is_vector and self._states:
            for state in self._states:
                state[0] = 0.0
                state[1] = 0.0
            self._output_vector = [0.0] * self._n

    def setInput(self, value, port=0):
        if isinstance(value, (list, tuple)):
            self._setup_vector_mode(len(value))
            for i, v in enumerate(value):
                if i < len(self._input_vector):
                    self._input_vector[i] = v
        else:
            self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            # Check for vector output from connected block
            if hasattr(self.input_block, 'getOutputVector'):
                vec = self.input_block.getOutputVector()
                if vec is not None:
                    self._setup_vector_mode(len(vec))
                    self._input_vector = list(vec)
                else:
                    self.input = self.input_block.getOutput(self.input_source_port)
            else:
                self.input = self.input_block.getOutput(self.input_source_port)

        if self._is_vector and self._states:
            # Vector derivative
            for i in range(self._n):
                inp = self._input_vector[i] if self._input_vector and i < len(self._input_vector) else 0.0
                # Filtered derivative: y = N*(u - x), x' = y
                output = self.coefficient * (inp - self._states[i][0])
                self._states[i][1] = output
                self._output_vector[i] = output
        else:
            # Scalar derivative
            # Filtered derivative: y = N*(u - x), x' = y
            # This implements transfer function Ns/(s+N)
            self.output = self.coefficient * (self.input - self.x[0])
            self.x[1] = self.output

    def getOutput(self, port=0):
        if self._is_vector and self._output_vector:
            if port < len(self._output_vector):
                return self._output_vector[port]
            return 0.0
        return self.output

    def getOutputVector(self):
        """Get the full output vector. Returns None for scalar operation."""
        if self._is_vector and self._output_vector:
            return self._output_vector.copy()
        return None


class TransferFunction(Block):
    """Transfer function block - continuous-time transfer function.

    Implements H(s) = num(s)/den(s) using state-space realization.
    """

    def __init__(self, numerator=None, denominator=None):
        super().__init__()
        self.numerator = numerator if numerator else [1.0]
        self.denominator = denominator if denominator else [1.0, 1.0]
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0

        # Create state variables for controllable canonical form
        self.order = len(self.denominator) - 1
        self.states = []
        for _ in range(self.order):
            self.states.append(self.addIntegrator([0.0, 0.0]))

    def init(self):
        for state in self.states:
            state[0] = 0.0
            state[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        if self.order == 0:
            # Static gain
            self.output = self.numerator[0] / self.denominator[0] * self.input
            return

        # Normalize coefficients
        a0 = self.denominator[0]
        num = [n / a0 for n in self.numerator]
        den = [d / a0 for d in self.denominator]

        # Pad numerator if needed
        while len(num) < len(den):
            num.insert(0, 0.0)

        # Controllable canonical form state equations
        # x' = Ax + Bu, y = Cx + Du
        for i in range(self.order):
            if i < self.order - 1:
                # x_i' = x_{i+1}
                self.states[i][1] = self.states[i + 1][0]
            else:
                # Last state derivative
                deriv = self.input
                for j in range(self.order):
                    deriv -= den[j + 1] * self.states[self.order - 1 - j][0]
                self.states[i][1] = deriv

        # Compute output: y = D*u + C*x
        # D = num[0] (leading coefficient, 0 for strictly proper transfer functions)
        # C_i = b_i - D*a_i where b_i = num[order-i], a_i = den[order-i]
        d = num[0]  # Direct feedthrough (0 for strictly proper)
        self.output = d * self.input
        for i in range(self.order):
            c_i = num[self.order - i] - d * den[self.order - i]
            self.output += c_i * self.states[i][0]

    def getOutput(self, port=0):
        return self.output


class StateSpace(Block):
    """State-space model block.

    Implements: x' = Ax + Bu, y = Cx + Du
    """

    def __init__(self, A=None, B=None, C=None, D=None, initial_state=None):
        super().__init__()
        self.A = A if A else [[0.0]]
        self.B = B if B else [[1.0]]
        self.C = C if C else [[1.0]]
        self.D = D if D else [[0.0]]

        self.n = len(self.A)  # Number of states
        self.initial_state = initial_state if initial_state else [0.0] * self.n

        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0

        # Create state variables
        self.states = []
        for i in range(self.n):
            self.states.append(self.addIntegrator([self.initial_state[i], 0.0]))

    def init(self):
        for i, state in enumerate(self.states):
            state[0] = self.initial_state[i] if i < len(self.initial_state) else 0.0
            state[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        # State derivatives: x' = Ax + Bu
        for i in range(self.n):
            deriv = 0.0
            for j in range(self.n):
                deriv += self.A[i][j] * self.states[j][0]
            deriv += self.B[i][0] * self.input
            self.states[i][1] = deriv

        # Output: y = Cx + Du
        self.output = 0.0
        for i in range(self.n):
            self.output += self.C[0][i] * self.states[i][0]
        self.output += self.D[0][0] * self.input

    def getOutput(self, port=0):
        return self.output


class PIDController(Block):
    """PID Controller block.

    Implements: u = Kp*e + Ki*integral(e) + Kd*de/dt
    with filtered derivative.
    """

    def __init__(self, Kp=1.0, Ki=0.0, Kd=0.0, N=100.0, initial_integrator=0.0):
        super().__init__()
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.N = N  # Derivative filter coefficient
        self.initial_integrator = initial_integrator

        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0

        # Integrator state
        self.integral = self.addIntegrator([initial_integrator, 0.0])

        # Derivative filter state
        self.deriv_state = self.addIntegrator([0.0, 0.0])

    def init(self):
        self.integral[0] = self.initial_integrator
        self.integral[1] = 0.0
        self.deriv_state[0] = 0.0
        self.deriv_state[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        error = self.input

        # Proportional term
        p_term = self.Kp * error

        # Integral term
        self.integral[1] = error
        i_term = self.Ki * self.integral[0]

        # Derivative term (filtered)
        # Using: d/dt filter state = N * (error - filter state)
        # derivative output = N * (error - filter state)
        d_term = self.Kd * self.N * (error - self.deriv_state[0])
        self.deriv_state[1] = self.N * (error - self.deriv_state[0])

        self.output = p_term + i_term + d_term

    def getOutput(self, port=0):
        return self.output


class TransportDelay(Block):
    """Transport Delay block - delays signal by fixed time.

    Uses a circular buffer to store past signal values.
    """

    def __init__(self, delay_time=1.0, initial_output=0.0):
        super().__init__()
        self.delay_time = delay_time
        self.initial_output = initial_output
        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = initial_output

        # Buffer for storing past values
        # Size will be determined based on sample time at runtime
        self.buffer = []
        self.time_buffer = []
        self._buffer_initialized = False

    def init(self):
        self.output = self.initial_output
        self.buffer = []
        self.time_buffer = []
        self._buffer_initialized = False

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        from ..state import State

        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        current_time = State.t

        # Add current value to buffer
        self.buffer.append(self.input)
        self.time_buffer.append(current_time)

        # Calculate delayed time
        delayed_time = current_time - self.delay_time

        if delayed_time < 0:
            # During initial delay period, output initial value
            self.output = self.initial_output
        else:
            # Find the value at delayed_time using linear interpolation
            # Remove old entries that are no longer needed
            while len(self.time_buffer) > 2 and self.time_buffer[1] < delayed_time:
                self.time_buffer.pop(0)
                self.buffer.pop(0)

            if len(self.time_buffer) == 0:
                self.output = self.initial_output
            elif len(self.time_buffer) == 1:
                self.output = self.buffer[0]
            else:
                # Linear interpolation
                for i in range(len(self.time_buffer) - 1):
                    t1, t2 = self.time_buffer[i], self.time_buffer[i + 1]
                    if t1 <= delayed_time <= t2:
                        if t2 > t1:
                            alpha = (delayed_time - t1) / (t2 - t1)
                            self.output = self.buffer[i] * (1 - alpha) + self.buffer[i + 1] * alpha
                        else:
                            self.output = self.buffer[i]
                        break
                else:
                    # If delayed_time is beyond buffer, use last value
                    self.output = self.buffer[-1] if self.buffer else self.initial_output

    def getOutput(self, port=0):
        return self.output


class SecondOrder(Block):
    """Second Order system block.

    Implements: G(s) = K * wn^2 / (s^2 + 2*zeta*wn*s + wn^2)

    Where:
    - wn = natural frequency (rad/s)
    - zeta = damping ratio
    - K = DC gain
    """

    def __init__(self, natural_frequency=1.0, damping_ratio=0.7, gain=1.0):
        super().__init__()
        self.wn = natural_frequency
        self.zeta = damping_ratio
        self.gain = gain

        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0

        # Two state variables for second-order system
        self.x1 = self.addIntegrator([0.0, 0.0])  # Position/output
        self.x2 = self.addIntegrator([0.0, 0.0])  # Velocity

    def init(self):
        self.x1[0] = 0.0
        self.x1[1] = 0.0
        self.x2[0] = 0.0
        self.x2[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        wn = self.wn
        zeta = self.zeta
        wn2 = wn * wn

        # State space form:
        # x1' = x2
        # x2' = -wn^2*x1 - 2*zeta*wn*x2 + wn^2*K*u
        # y = x1

        self.x1[1] = self.x2[0]
        self.x2[1] = -wn2 * self.x1[0] - 2 * zeta * wn * self.x2[0] + wn2 * self.gain * self.input

        self.output = self.x1[0]

    def getOutput(self, port=0):
        return self.output


class LimitedIntegrator(Block):
    """Limited Integrator block - integrator with saturation.

    Identical to Integrator with limit_output=True, but provided
    as a separate block for convenience.
    """

    def __init__(self, initial_condition=0.0, upper_limit=1.0, lower_limit=-1.0):
        super().__init__()
        self.initial_condition = initial_condition
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit

        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.x = self.addIntegrator([initial_condition, 0.0])

    def init(self):
        self.x[0] = self.initial_condition
        self.x[1] = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        self.x[1] = self.input

        # Anti-windup: stop integrating if at limits
        if (self.x[0] >= self.upper_limit and self.x[1] > 0) or \
           (self.x[0] <= self.lower_limit and self.x[1] < 0):
            self.x[1] = 0.0

    def getOutput(self, port=0):
        output = self.x[0]
        return max(self.lower_limit, min(self.upper_limit, output))


class ZeroPole(Block):
    """Zero-Pole block - transfer function defined by zeros and poles.

    Implements transfer function defined by:
    H(s) = K * (s - z1)(s - z2)... / (s - p1)(s - p2)...

    Currently only supports real poles and zeros.
    """

    def __init__(self, zeros=None, poles=None, gain=1.0):
        super().__init__()
        self.zeros = zeros if zeros else []
        self.poles = poles if poles else [-1.0]
        self.gain = gain

        self.input = 0.0
        self.input_block = None
        self.input_source_port = 0
        self.output = 0.0

        # Convert to transfer function coefficients and use state-space
        self._build_state_space()

    def _poly_coeffs(self, roots):
        """Compute polynomial coefficients from roots."""
        coeffs = [1.0]
        for r in roots:
            # Multiply by (s - r)
            new_coeffs = [0.0] * (len(coeffs) + 1)
            for i, c in enumerate(coeffs):
                new_coeffs[i] += c
                new_coeffs[i + 1] -= r * c
            coeffs = new_coeffs
        return coeffs

    def _build_state_space(self):
        """Build state-space realization from zeros and poles."""
        num = self._poly_coeffs(self.zeros)
        den = self._poly_coeffs(self.poles)

        # Apply gain
        num = [c * self.gain for c in num]

        # Pad numerator
        while len(num) < len(den):
            num.insert(0, 0.0)

        self.order = len(den) - 1
        self.num = num
        self.den = den

        # Create state variables
        self.states = []
        for _ in range(self.order):
            self.states.append(self.addIntegrator([0.0, 0.0]))

    def init(self):
        for state in self.states:
            state[0] = 0.0
            state[1] = 0.0
        self.output = 0.0

    def setInput(self, value, port=0):
        self.input = value

    def connectInput(self, block, port=0, source_port=0):
        self.input_block = block
        self.input_source_port = source_port

    def update(self):
        if self.input_block is not None:
            self.input = self.input_block.getOutput(self.input_source_port)

        if self.order == 0:
            self.output = self.num[0] / self.den[0] * self.input
            return

        # Normalize
        a0 = self.den[0]
        num = [n / a0 for n in self.num]
        den = [d / a0 for d in self.den]

        # State equations (controllable canonical form)
        for i in range(self.order):
            if i < self.order - 1:
                self.states[i][1] = self.states[i + 1][0]
            else:
                deriv = self.input
                for j in range(self.order):
                    deriv -= den[j + 1] * self.states[self.order - 1 - j][0]
                self.states[i][1] = deriv

        # Output
        d = num[0]
        self.output = d * self.input
        for i in range(self.order):
            c_i = num[self.order - i] - d * den[self.order - i]
            self.output += c_i * self.states[i][0]

    def getOutput(self, port=0):
        return self.output
