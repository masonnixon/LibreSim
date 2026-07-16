"""Shared helpers for generated DSP block templates."""

import math


def window_coefficients(window_type: str, length: int, beta: float = 5.0) -> list[float]:
    """Return coefficients matching the OSK ``WindowFunction`` implementation."""

    def bessel_i0(x: float) -> float:
        sum_value = 1.0
        term = 1.0
        for k in range(1, 25):
            term *= (x / (2 * k)) ** 2
            sum_value += term
            if term < 1e-12:
                break
        return sum_value

    normalized_type = window_type.lower()
    coefficients: list[float] = []
    for n in range(length):
        if normalized_type == "rectangular":
            coefficient = 1.0
        elif normalized_type == "hanning":
            coefficient = 0.5 * (1 - math.cos(2 * math.pi * n / (length - 1)))
        elif normalized_type == "hamming":
            coefficient = 0.54 - 0.46 * math.cos(2 * math.pi * n / (length - 1))
        elif normalized_type == "blackman":
            coefficient = (
                0.42
                - 0.5 * math.cos(2 * math.pi * n / (length - 1))
                + 0.08 * math.cos(4 * math.pi * n / (length - 1))
            )
        elif normalized_type == "kaiser":
            alpha = (length - 1) / 2
            ratio = (n - alpha) / alpha
            coefficient = (
                bessel_i0(beta * math.sqrt(1 - ratio * ratio)) / bessel_i0(beta)
                if abs(ratio) <= 1
                else 0.0
            )
        else:
            coefficient = 1.0
        coefficients.append(coefficient)
    return coefficients
