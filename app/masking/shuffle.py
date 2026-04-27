from __future__ import annotations

import random
from typing import Any, List


def shuffle(values: List[Any]) -> List[Any]:
    """Return a shuffled copy of *values*.

    Uses the global ``random.shuffle`` on a copy of the input list so the
    original is not mutated. Repeated calls may produce different orderings.
    """
    shuffled = list(values)
    random.shuffle(shuffled)
    return shuffled
