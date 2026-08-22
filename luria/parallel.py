"""One map, run wide: the parallelism primitive the tools share (ADR-026).

    from .parallel import pmap
    results = pmap(render_one, units)          # ordered, like map()

Everything Luria does is embarrassingly parallel at some unit — a scheme's
view, a journal's books, a file's scan, a URL's probe — and none of it shares
state: renders are pure functions of the config and the tree, scans read.
`pmap` runs a function over items on a thread pool and returns results **in
input order**, so callers keep their determinism and their code shape; going
wide is a one-word change at each call site, never a restructuring.

Threads, not processes, on purpose: the workloads are file reads and network
requests (where threads genuinely overlap), the text assembly between them is
trivial at this data size, and a process pool would add pickling and spawn
costs for no measured win — see the ADR for the numbers, and for the cue that
would revisit this (render units that measure in seconds, not milliseconds).

`LURIA_JOBS=1` forces serial execution — tracebacks read straight, profiling
is honest, and a suspected concurrency bug can be ruled in or out with an
environment variable rather than an edit. `LURIA_JOBS=N` caps the pool.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")

DEFAULT_JOBS = 8


def jobs() -> int:
    """How wide to run. `LURIA_JOBS` wins; 0/unset means the default width.

    A fixed default rather than `os.cpu_count()`, because the workloads are
    I/O-bound — the right width tracks latency overlap, not cores."""
    raw = os.environ.get("LURIA_JOBS", "").strip()
    try:
        n = int(raw)
    except ValueError:
        n = 0
    return n if n > 0 else DEFAULT_JOBS


def pmap(fn: Callable[[T], R], items: Iterable[T]) -> list[R]:
    """`list(map(fn, items))`, run on a thread pool, results in input order.

    Exceptions propagate exactly as they would serially — the first failing
    item raises when its result is collected — so a caller's error handling
    is the same either way."""
    seq = list(items)
    width = min(jobs(), len(seq)) or 1
    if width <= 1:
        return [fn(item) for item in seq]
    with ThreadPoolExecutor(max_workers=width) as pool:
        return list(pool.map(fn, seq))


if __name__ == "__main__":
    raise SystemExit("a library, not a command")
