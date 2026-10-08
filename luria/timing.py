# luria/timing.py
"""Where a run spends its time, on request.

    LURIA_TIMINGS=1 luria lint

prints one line per timed phase to stderr, as it finishes:

    luria: timing: facts schema+documents 0.487s, cpu 0.247s (10238 facts)
    luria: timing: solve relations 3.918s, cpu 0.188s
    luria: timing: command lint 54.987s, cpu 29.261s

Wall-clock time first, then the CPU time of the thread that ran the phase.
They differ when the phase shared the interpreter: a solve that runs while
the render pool is busy waits for the GIL, and its wall time says how long
it waited, not how much it cost. A gap between the two is contention; a
phase that is slow on both is slow. For the command line, the CPU figure is
the main thread's alone, so under the pool it undercounts the run.

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
    start, cpu = time.perf_counter(), time.thread_time()
    try:
        yield extra
    finally:
        if enabled():
            took = time.perf_counter() - start
            used = time.thread_time() - cpu
            note = f" ({extra['note']})" if extra.get("note") else ""
            print(f"luria: timing: {label} {took:.3f}s, cpu {used:.3f}s{note}",
                  file=sys.stderr, flush=True)
