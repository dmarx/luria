# luria/timing.py
"""Where a run spends its time, on request.

    LURIA_TIMINGS=1 luria lint

prints one line per timed phase to stderr, as it finishes:

    luria: timing: facts 0.842s (39385 facts)
    luria: timing: solve relations+invariants 0.311s
    luria: timing: command lint 68.204s

The logic-core migration (the ADR on a logic core in clingo) carries a kill
criterion on speed, and "materially slower" needs a number to be said
confidently. Unset, a timed block costs one environment lookup and prints
nothing, so the markers can stay in the code for good.
"""
from __future__ import annotations

import os
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager


def enabled() -> bool:
    return os.environ.get("LURIA_TIMINGS", "") not in ("", "0")


@contextmanager
def timed(label: str) -> Iterator[dict]:
    """Time the block and, when `LURIA_TIMINGS` is set, report it. The
    yielded dict takes a `note` for what the phase produced."""
    extra: dict = {}
    start = time.perf_counter()
    try:
        yield extra
    finally:
        if enabled():
            took = time.perf_counter() - start
            note = f" ({extra['note']})" if extra.get("note") else ""
            print(f"luria: timing: {label} {took:.3f}s{note}", file=sys.stderr,
                  flush=True)
