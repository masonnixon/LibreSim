"""Shared coefficient design helpers for generated signal-processing blocks."""

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BiquadCoefficients:
    """Normalized direct-form coefficients for one filter cascade section."""

    b0: float
    b1: float
    b2: float
    a1: float
    a2: float


def _butterworth_poles(order: int) -> list[complex]:
    return [
        complex(
            math.cos(math.pi * (2 * k + order + 1) / (2 * order)),
            math.sin(math.pi * (2 * k + order + 1) / (2 * order)),
        )
        for k in range(order)
    ]


def _chebyshev1_poles(order: int, ripple_db: float) -> list[complex]:
    epsilon = math.sqrt(10 ** (ripple_db / 10) - 1)
    v0 = math.asinh(1 / epsilon) / order
    sinh_v0 = math.sinh(v0)
    cosh_v0 = math.cosh(v0)
    poles = []
    for k in range(order):
        theta = math.pi * (2 * k + 1) / (2 * order)
        poles.append(complex(-sinh_v0 * math.sin(theta), cosh_v0 * math.cos(theta)))
    return poles


def _chebyshev2_poles(order: int, stopband_db: float) -> list[complex]:
    epsilon = 1 / math.sqrt(10 ** (stopband_db / 10) - 1)
    v0 = math.asinh(1 / epsilon) / order
    sinh_v0 = math.sinh(v0)
    cosh_v0 = math.cosh(v0)
    poles = []
    for k in range(order):
        theta = math.pi * (2 * k + 1) / (2 * order)
        sigma = -sinh_v0 * math.sin(theta)
        omega = cosh_v0 * math.cos(theta)
        denominator = sigma**2 + omega**2
        poles.append(
            complex(sigma / denominator, -omega / denominator)
            if abs(denominator) > 1e-10
            else complex(-1, 0)
        )
    return poles


def _bessel_poles(order: int) -> list[complex]:
    tables = {
        1: [complex(-1.0, 0.0)],
        2: [complex(-1.1030, 0.6368), complex(-1.1030, -0.6368)],
        3: [
            complex(-1.0509, 0.9991),
            complex(-1.0509, -0.9991),
            complex(-1.3270, 0.0),
        ],
        4: [
            complex(-0.9952, 1.2571),
            complex(-0.9952, -1.2571),
            complex(-1.3700, 0.4103),
            complex(-1.3700, -0.4103),
        ],
        5: [
            complex(-0.9576, 1.4711),
            complex(-0.9576, -1.4711),
            complex(-1.3809, 0.7179),
            complex(-1.3809, -0.7179),
            complex(-1.5023, 0.0),
        ],
    }
    if order in tables:
        return tables[order]
    radius = 1.0 + 0.2 * order
    return [
        complex(
            radius * math.cos(math.pi * (2 * k + order + 1) / (2 * order)),
            radius * math.sin(math.pi * (2 * k + order + 1) / (2 * order)),
        )
        for k in range(order)
    ]


def design_analog_filter(parameters: dict[str, Any], step_size: float) -> list[BiquadCoefficients]:
    """Reproduce the OSK AnalogFilter cascade for a fixed simulation step."""
    design = str(parameters.get("design", "butterworth"))
    response = str(parameters.get("response", "lowpass"))
    order = max(1, min(10, int(parameters.get("order", 2))))
    cutoff = float(parameters.get("cutoffFrequency", 10.0))
    low_cutoff = float(parameters.get("lowCutoff", 1.0))
    high_cutoff = float(parameters.get("highCutoff", 10.0))
    ripple = float(parameters.get("passbandRipple", 1.0))
    attenuation = float(parameters.get("stopbandAtten", 40.0))

    if step_size <= 0:
        return [BiquadCoefficients(1.0, 0.0, 0.0, 0.0, 0.0)]
    if design == "butterworth":
        poles = _butterworth_poles(order)
    elif design == "chebyshev1":
        poles = _chebyshev1_poles(order, ripple)
    elif design == "chebyshev2":
        poles = _chebyshev2_poles(order, attenuation)
    elif design == "bessel":
        poles = _bessel_poles(order)
    else:
        poles = _butterworth_poles(order)

    if response in ("lowpass", "highpass"):
        angular_cutoff = 2 * math.pi * cutoff
    else:
        angular_cutoff = math.sqrt((2 * math.pi * low_cutoff) * (2 * math.pi * high_cutoff))

    sections: list[BiquadCoefficients] = []
    k_transform = 2 / step_size
    index = 0
    while index < len(poles):
        pole = poles[index]
        if abs(pole.imag) < 1e-10:
            scaled_pole = pole.real * angular_cutoff
            a0 = k_transform - scaled_pole
            if abs(a0) > 1e-10:
                b0 = -scaled_pole if response == "lowpass" else k_transform
                b1 = -scaled_pole if response == "lowpass" else -k_transform
                sections.append(
                    BiquadCoefficients(
                        b0 / a0,
                        b1 / a0,
                        0.0,
                        (-k_transform - scaled_pole) / a0,
                        0.0,
                    )
                )
            index += 1
            continue

        sigma = pole.real * angular_cutoff
        omega = pole.imag * angular_cutoff
        w0_squared = sigma**2 + omega**2
        a0 = k_transform**2 - 2 * sigma * k_transform + w0_squared
        a1 = 2 * w0_squared - 2 * k_transform**2
        a2 = k_transform**2 + 2 * sigma * k_transform + w0_squared
        if response == "lowpass":
            b0, b1, b2 = w0_squared, 2 * w0_squared, w0_squared
        elif response == "highpass":
            b0, b1, b2 = k_transform**2, -2 * k_transform**2, k_transform**2
        else:
            bandwidth = abs(omega) * 2
            b0, b1, b2 = bandwidth * k_transform, 0.0, -bandwidth * k_transform
        if abs(a0) > 1e-10:
            sections.append(BiquadCoefficients(b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0))
        index += 2

    return sections or [BiquadCoefficients(1.0, 0.0, 0.0, 0.0, 0.0)]
