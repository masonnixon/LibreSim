"""State observer blocks for OSK-based simulation.

Provides state estimation blocks for control systems including
Luenberger observers and Kalman filters.
"""

import numpy as np

from ..block import Block
from ..state import State


class LuenbergerObserver(Block):
    """Luenberger State Observer for linear systems.

    Estimates the state of a linear system given the system matrices
    and observer gain. The observer dynamics are:
        x_hat_dot = A*x_hat + B*u + L*(y - C*x_hat)

    where L is the observer gain matrix chosen to place the observer
    poles for desired convergence rate.
    """

    def __init__(self, A=None, B=None, C=None, L=None, initial_state=None):
        super().__init__()
        # System matrices (convert to numpy arrays)
        self.A = np.array(A) if A is not None else np.array([[0.0]])
        self.B = np.array(B) if B is not None else np.array([[1.0]])
        self.C = np.array(C) if C is not None else np.array([[1.0]])
        self.L = np.array(L) if L is not None else np.array([[1.0]])

        # Ensure proper dimensions
        self.n = self.A.shape[0]  # Number of states
        self.m = self.B.shape[1] if len(self.B.shape) > 1 else 1  # Number of inputs
        self.p = self.C.shape[0] if len(self.C.shape) > 1 else 1  # Number of outputs

        # Reshape matrices if needed
        if len(self.B.shape) == 1:
            self.B = self.B.reshape(-1, 1)
        if len(self.C.shape) == 1:
            self.C = self.C.reshape(1, -1)
        if len(self.L.shape) == 1:
            self.L = self.L.reshape(-1, 1)

        # State estimate
        self.x_hat = np.array(initial_state) if initial_state is not None else np.zeros(self.n)
        self.x_hat_dot = np.zeros(self.n)

        # Inputs: [u, y] - control input and measured output
        self.inputs = [0.0, 0.0]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self.output = 0.0

    def init(self):
        if hasattr(self, '_initial_state') and self._initial_state is not None:
            self.x_hat = np.array(self._initial_state)
        else:
            self.x_hat = np.zeros(self.n)
        self.x_hat_dot = np.zeros(self.n)

    def setInput(self, value, port=0):
        if port < 2:
            self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                source_port = self.input_source_ports[i] if i < len(self.input_source_ports) else 0
                self.inputs[i] = block.getOutput(source_port)

        u = np.array([self.inputs[0]]).reshape(-1, 1)  # Control input
        y = np.array([self.inputs[1]]).reshape(-1, 1)  # Measured output

        # Compute output estimate
        y_hat = self.C @ self.x_hat.reshape(-1, 1)

        # Observer dynamics: x_hat_dot = A*x_hat + B*u + L*(y - y_hat)
        innovation = y - y_hat
        self.x_hat_dot = (
            self.A @ self.x_hat.reshape(-1, 1) +
            self.B @ u +
            self.L @ innovation
        ).flatten()

        # Output is the first state estimate (can be extended to output all states)
        self.output = self.x_hat[0]

    def propagateStates(self):
        """Integrate state estimates using Euler method."""
        self.x_hat = self.x_hat + State.dt * self.x_hat_dot

    def getOutput(self, port=0):
        """Get state estimate. Port 0 returns first state, etc."""
        if port < len(self.x_hat):
            return float(self.x_hat[port])
        return self.output

    def getStateEstimate(self):
        """Get full state estimate vector."""
        return self.x_hat.copy()


class KalmanFilter(Block):
    """Discrete-time Kalman Filter for linear systems.

    Provides optimal state estimation for linear systems with
    Gaussian process and measurement noise:
        x[k+1] = A*x[k] + B*u[k] + w[k]   (process model)
        y[k] = C*x[k] + v[k]              (measurement model)

    where w ~ N(0, Q) and v ~ N(0, R).
    """

    def __init__(self, A=None, B=None, C=None, Q=None, R=None, initial_state=None, initial_P=None):
        super().__init__()
        # System matrices
        self.A = np.array(A) if A is not None else np.array([[1.0]])
        self.B = np.array(B) if B is not None else np.array([[1.0]])
        self.C = np.array(C) if C is not None else np.array([[1.0]])

        # Dimensions
        self.n = self.A.shape[0]
        self.m = self.B.shape[1] if len(self.B.shape) > 1 else 1
        self.p = self.C.shape[0] if len(self.C.shape) > 1 else 1

        # Reshape matrices if needed
        if len(self.B.shape) == 1:
            self.B = self.B.reshape(-1, 1)
        if len(self.C.shape) == 1:
            self.C = self.C.reshape(1, -1)

        # Noise covariance matrices
        self.Q = np.array(Q) if Q is not None else np.eye(self.n) * 0.01  # Process noise
        self.R = np.array(R) if R is not None else np.eye(self.p) * 0.1  # Measurement noise

        # Ensure Q and R are proper shape
        if self.Q.shape != (self.n, self.n):
            self.Q = np.eye(self.n) * (self.Q.flatten()[0] if self.Q.size > 0 else 0.01)
        if self.R.shape != (self.p, self.p):
            self.R = np.eye(self.p) * (self.R.flatten()[0] if self.R.size > 0 else 0.1)

        # State estimate and covariance
        self.x_hat = np.array(initial_state) if initial_state is not None else np.zeros(self.n)
        self.P = np.array(initial_P) if initial_P is not None else np.eye(self.n)

        # Inputs: [u, y]
        self.inputs = [0.0, 0.0]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self.output = 0.0

    def init(self):
        self.x_hat = np.zeros(self.n)
        self.P = np.eye(self.n)

    def setInput(self, value, port=0):
        if port < 2:
            self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                source_port = self.input_source_ports[i] if i < len(self.input_source_ports) else 0
                self.inputs[i] = block.getOutput(source_port)

        u = np.array([self.inputs[0]]).reshape(-1, 1)
        y = np.array([self.inputs[1]]).reshape(-1, 1)

        # Predict step
        x_pred = self.A @ self.x_hat.reshape(-1, 1) + self.B @ u
        P_pred = self.A @ self.P @ self.A.T + self.Q

        # Update step
        y_pred = self.C @ x_pred
        innovation = y - y_pred
        S = self.C @ P_pred @ self.C.T + self.R  # Innovation covariance

        # Kalman gain
        try:
            K = P_pred @ self.C.T @ np.linalg.inv(S)
        except np.linalg.LinAlgError:
            K = P_pred @ self.C.T * 0  # Fallback if singular

        # Update state estimate and covariance
        self.x_hat = (x_pred + K @ innovation).flatten()
        self.P = (np.eye(self.n) - K @ self.C) @ P_pred

        self.output = self.x_hat[0]

    def getOutput(self, port=0):
        if port < len(self.x_hat):
            return float(self.x_hat[port])
        return self.output

    def getStateEstimate(self):
        return self.x_hat.copy()

    def getCovariance(self):
        return self.P.copy()


class ExtendedKalmanFilter(Block):
    """Extended Kalman Filter for nonlinear systems.

    Uses linearization around the current estimate for nonlinear systems.
    Requires user to provide Jacobian functions for state and measurement.

    Note: This is a simplified implementation that assumes the user
    provides linearized A and C matrices that are updated externally,
    or uses a simple integrator model internally.
    """

    def __init__(self, n_states=1, Q=None, R=None, initial_state=None):
        super().__init__()
        # Ensure n_states is an integer (may come as float from JSON)
        self.n = int(n_states)

        # Noise covariances
        self.Q = np.array(Q) if Q is not None else np.eye(self.n) * 0.01
        self.R = np.array(R) if R is not None else np.array([[0.1]])

        if self.Q.shape != (self.n, self.n):
            self.Q = np.eye(self.n) * 0.01
        if len(self.R.shape) == 1:
            self.R = np.array([[self.R[0]]])

        # State estimate
        self.x_hat = np.array(initial_state) if initial_state is not None else np.zeros(self.n)
        self.P = np.eye(self.n)

        # For simple integrator model: x_dot = u
        self.A = np.eye(self.n)  # State transition (identity for discrete)
        self.C = np.zeros((1, self.n))
        self.C[0, 0] = 1.0  # Measure first state

        self.inputs = [0.0, 0.0]  # [u, y]
        self.input_blocks = [None, None]
        self.input_source_ports = [0, 0]
        self.output = 0.0

    def init(self):
        self.x_hat = np.zeros(self.n)
        self.P = np.eye(self.n)

    def setInput(self, value, port=0):
        if port < 2:
            self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        if port < 2:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                source_port = self.input_source_ports[i] if i < len(self.input_source_ports) else 0
                self.inputs[i] = block.getOutput(source_port)

        u = self.inputs[0]
        y = np.array([self.inputs[1]]).reshape(-1, 1)

        # Simple integrator prediction: x_new = x + dt * u
        x_pred = self.x_hat.copy()
        if self.n >= 1:
            x_pred[0] = self.x_hat[0] + State.dt * u

        # Linearized state transition for integrator
        F = np.eye(self.n)
        P_pred = F @ self.P @ F.T + self.Q

        # Measurement update
        y_pred = self.C @ x_pred.reshape(-1, 1)
        innovation = y - y_pred
        S = self.C @ P_pred @ self.C.T + self.R

        try:
            K = P_pred @ self.C.T @ np.linalg.inv(S)
        except np.linalg.LinAlgError:
            K = np.zeros((self.n, 1))

        self.x_hat = (x_pred.reshape(-1, 1) + K @ innovation).flatten()
        self.P = (np.eye(self.n) - K @ self.C) @ P_pred

        self.output = self.x_hat[0]

    def getOutput(self, port=0):
        if port < len(self.x_hat):
            return float(self.x_hat[port])
        return self.output
