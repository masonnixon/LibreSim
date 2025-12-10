"""Object-oriented Simulation Kernel (OSK) - Python Implementation.

This package provides the core simulation infrastructure based on
H.R. Sells' Object-oriented Simulation Kernel.

Core classes:
- State: Numerical integrator with multiple methods (Euler, RK2, RK4, Merson)
- Block: Base class for simulation blocks
- Sim: Simulation orchestrator
"""

from .state import State
from .block import Block
from .sim import Sim

__all__ = ["State", "Block", "Sim"]
