"""Compatibility helpers for generated pseudorandom number streams."""

import random
from typing import cast

RandomSeed = int | float | str | bytes | bytearray | None


def python_mt19937_state(seed: object) -> tuple[tuple[int, ...], int]:
    """Return CPython's initialized MT19937 words and current index for ``seed``.

    CPython expands integer seeds with ``init_by_array`` rather than MT19937's
    scalar initializer. Generated compiled targets embed this snapshot so their
    ``random()`` and cached ``gauss()`` implementations consume the same stream.
    """
    internal_state = random.Random(cast(RandomSeed, seed)).getstate()[1]
    return tuple(int(word) for word in internal_state[:-1]), int(internal_state[-1])
