from __future__ import annotations
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, TypeVar
T = TypeVar('T')
R = TypeVar('R')
DEFAULT_JOBS = 8

def jobs() -> int:
    raw = os.environ.get('LURIA_JOBS', '').strip()
    try:
        n = int(raw)
    except ValueError:
        n = 0
    return n if n > 0 else DEFAULT_JOBS

def pmap(fn: Callable[[T], R], items: Iterable[T]) -> list[R]:
    seq = list(items)
    width = min(jobs(), len(seq)) or 1
    if width <= 1:
        return [fn(item) for item in seq]
    with ThreadPoolExecutor(max_workers=width) as pool:
        return list(pool.map(fn, seq))
if __name__ == '__main__':
    raise SystemExit('a library, not a command')
