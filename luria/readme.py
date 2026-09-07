# luria/readme.py
"""Marked regions in the README that `luria index` rewrites.

    <!-- luria:badges -->   two numbers about the record
    <!-- /luria:badges -->

    <!-- luria:site -->     where the record is published
    <!-- /luria:site -->

One module because there is one mechanism, read the same way by each region
that uses it (DP-4). The regions themselves stay separate: a project may want
the counts and not the link, or the reverse, and widening either region's
meaning to hold the other's content would make "what is this region for" a
question with two answers.

**A region is only ever rewritten where it already exists.** Luria does not
insert one into a README it was not invited into — the position would have to
be guessed, and the guess is wrong for anyone whose front page opens with a
logo block, a table, or a quote. Absence is silent here on purpose; the thing
that breaks the silence is a lint finding, not an edit (DP-10: the disclosure
opts in, the guard that reports its absence opts out).
"""

from __future__ import annotations

import re
from pathlib import Path

from .config import current


def markers(name: str) -> tuple[str, str]:
    """The opening and closing comments delimiting the `name` region."""
    return f"<!-- luria:{name} -->", f"<!-- /luria:{name} -->"


def _region_re(name: str) -> re.Pattern:
    open_, close = markers(name)
    return re.compile(rf"{re.escape(open_)}.*?{re.escape(close)}", re.DOTALL)


def has(text: str, name: str) -> bool:
    return markers(name)[0] in text


def rewrite(text: str, name: str, body: str) -> str:
    """`text` with the `name` region's contents replaced by `body`, or `text`
    unchanged where the region is absent."""
    open_, close = markers(name)
    filled = f"{open_}\n{body}\n{close}" if body else f"{open_}\n{close}"
    return _region_re(name).sub(lambda _: filled, text, count=1)


def path() -> Path:
    return current().root / "README.md"
