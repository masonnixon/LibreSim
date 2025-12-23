"""OSK Block implementations for LibreSim.

This package contains simulation block implementations that use
the OSK (Object-oriented Simulation Kernel) framework.
"""

from .continuous import Derivative, Integrator, PIDController, StateSpace, TransferFunction
from .discrete import UnitDelay, ZeroOrderHold
from .math_ops import (
    Abs,
    DeadZone,
    Demux,
    Gain,
    MathFunction,
    Mux,
    Product,
    Saturation,
    Sign,
    Sum,
    Switch,
    Trigonometry,
)
from .nonlinear import (
    Coulomb,
    LookupTable1D,
    LookupTable2D,
    Quantizer,
    Relay,
    VariableTransportDelay,
)
from .observers import ExtendedKalmanFilter, KalmanFilter, LuenbergerObserver
from .signal_processing import (
    Backlash,
    BandPassFilter,
    HighPassFilter,
    LowPassFilter,
    MovingAverage,
    RateLimiter,
)
from .sinks import Scope, ToWorkspace
from .sources import Clock, Constant, Ramp, SineWave, Step
from .subsystems import Inport, Outport, Subsystem

__all__ = [
    # Sources
    "Constant", "Step", "Ramp", "SineWave", "Clock",
    # Sinks
    "Scope", "ToWorkspace",
    # Continuous
    "Integrator", "Derivative", "TransferFunction", "StateSpace", "PIDController",
    # Discrete
    "UnitDelay", "ZeroOrderHold",
    # Math
    "Sum", "Gain", "Product", "Abs", "Saturation", "Switch", "Mux", "Demux",
    "MathFunction", "Trigonometry", "Sign", "DeadZone",
    # Subsystems
    "Inport", "Outport", "Subsystem",
    # Signal Processing
    "RateLimiter", "MovingAverage", "LowPassFilter", "HighPassFilter", "BandPassFilter", "Backlash",
    # Nonlinear
    "LookupTable1D", "LookupTable2D", "Quantizer", "Relay", "Coulomb", "VariableTransportDelay",
    # Observers
    "LuenbergerObserver", "KalmanFilter", "ExtendedKalmanFilter",
]
