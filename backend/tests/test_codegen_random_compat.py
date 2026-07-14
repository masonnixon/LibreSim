"""Regression tests for generated pseudorandom stream compatibility."""

import random
from collections.abc import Callable

import pytest

from src.codegen.languages.c.blocks.sources import (
    template_band_limited_white_noise as c_band_limited_white_noise,
)
from src.codegen.languages.c.blocks.sources import template_white_noise as c_white_noise
from src.codegen.languages.cpp.blocks.sources import (
    template_band_limited_white_noise as cpp_band_limited_white_noise,
)
from src.codegen.languages.cpp.blocks.sources import template_white_noise as cpp_white_noise
from src.codegen.languages.rust.blocks.sources import (
    template_band_limited_white_noise as rust_band_limited_white_noise,
)
from src.codegen.languages.rust.blocks.sources import (
    template_white_noise as rust_white_noise,
)
from src.codegen.models import BlockInfo
from src.codegen.random_compat import python_mt19937_state


@pytest.mark.parametrize("seed", [0, 42, 12345, 2**40 + 17, -42])
def test_python_mt19937_state_reconstructs_seeded_gauss_stream(seed: int):
    words, index = python_mt19937_state(seed)
    reconstructed = random.Random()
    reconstructed.setstate((3, (*words, index), None))
    expected = random.Random(seed)

    assert len(words) == 624
    assert index == 624
    assert [reconstructed.gauss(0.0, 1.0) for _ in range(7)] == [
        expected.gauss(0.0, 1.0) for _ in range(7)
    ]


def test_seed_42_gaussian_reference_vector():
    words, index = python_mt19937_state(42)
    reconstructed = random.Random()
    reconstructed.setstate((3, (*words, index), None))

    assert [reconstructed.gauss(0.0, 1.0) for _ in range(6)] == pytest.approx(
        [
            -0.14409032957792836,
            -0.1729036003315193,
            -0.11131586156766246,
            0.7019837250988631,
            -0.12758828378288709,
            -1.4973534143409575,
        ],
        rel=0.0,
        abs=0.0,
    )


@pytest.mark.parametrize(
    "template",
    [
        c_white_noise,
        c_band_limited_white_noise,
        cpp_white_noise,
        cpp_band_limited_white_noise,
        rust_white_noise,
        rust_band_limited_white_noise,
    ],
)
def test_compiled_noise_templates_embed_cpython_state(
    template: Callable[[BlockInfo, str], str],
):
    block = BlockInfo(
        id="noise",
        type="white_noise",
        name="Noise",
        parameters={"seed": 42, "variance": 1.0, "sampleTime": 0.1},
        input_connections=[],
        output_connections=[],
        execution_order=1,
    )

    source = template(block, "GeneratedNoise")

    assert "2147483648" in source
    assert "normal_distribution" not in source
    assert "mt_init(" not in source
