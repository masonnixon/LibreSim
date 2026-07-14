"""Python templates for state-estimation blocks."""

from ....models import BlockInfo


def kalman_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate a discrete-time linear Kalman filter."""
    A = block.parameters.get("A", [[1.0]])
    B = block.parameters.get("B", [[1.0]])
    C = block.parameters.get("C", [[1.0]])
    Q = block.parameters.get("Q", [[0.01]])
    R = block.parameters.get("R", [[0.1]])
    initial_state = block.parameters.get("initialState", [0.0])
    initial_p = block.parameters.get("initialP", [[1.0]])

    return f'''
import numpy as np

class {class_name}:
    """Discrete-time Kalman filter block: {block.name}"""

    def __init__(self):
        self.input = 0.0
        self.input1 = 0.0
        self.A = np.array({A!r}, dtype=float)
        self.B = np.array({B!r}, dtype=float)
        self.C = np.array({C!r}, dtype=float)
        self.Q = np.array({Q!r}, dtype=float)
        self.R = np.array({R!r}, dtype=float)
        self._initial_state = np.array({initial_state!r}, dtype=float)
        self._initial_p = np.array({initial_p!r}, dtype=float)
        self.x = self._initial_state.copy()
        self.P = self._initial_p.copy()

    def init(self):
        self.input = 0.0
        self.input1 = 0.0
        self.x = self._initial_state.copy()
        self.P = self._initial_p.copy()

    def update(self, t: float):
        u = np.array([self.input], dtype=float).reshape(-1, 1)
        y = np.array([self.input1], dtype=float).reshape(-1, 1)

        x_pred = self.A @ self.x.reshape(-1, 1) + self.B @ u
        p_pred = self.A @ self.P @ self.A.T + self.Q
        innovation = y - self.C @ x_pred
        innovation_covariance = self.C @ p_pred @ self.C.T + self.R
        try:
            gain = p_pred @ self.C.T @ np.linalg.inv(innovation_covariance)
        except np.linalg.LinAlgError:
            gain = np.zeros((len(self.x), self.C.shape[0]))

        self.x = (x_pred + gain @ innovation).flatten()
        self.P = (np.eye(len(self.x)) - gain @ self.C) @ p_pred

    def get_output(self, port: int = 0) -> float:
        if 0 <= port < len(self.x):
            return float(self.x[port])
        return 0.0

    def get_output_vector(self) -> list:
        return [float(value) for value in self.x]
'''


ESTIMATION_TEMPLATES = {
    "kalman_filter": kalman_filter_template,
}
