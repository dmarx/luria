#!/usr/bin/env python3
"""luria/syntax.py — what a grammar knows, for the directives that need it.

Two of `luria.directives`' jobs are language questions it was answering by
guessing: **where a comment is**, and **what the block below one is**. The
guesses are a marker regex and a run of non-blank lines. Both are wrong in
ways that show up in real files — a `#` inside a shell string reads as a
comment, and a function's docstring is several runs rather than one.

Tree-sitter answers both, for every language it has a grammar for, with one
rule each and no per-language table on this side:

- a comment is a node whose type contains `comment` (seven grammars checked:
  six spell it `comment`, Rust spells it `line_comment`);
- the block a comment introduces is the smallest node that starts where the
  block's content starts and still holds the whole block.

This is an **optional extra** (`pip install luria[syntax]`). Without it every
function here returns "no opinion" and the callers keep the behaviour they
have always had, which is why the growth rule is stated as a *union* with the
blank-line block: a grammar can extend what a directive governs, never narrow
it. A directive that works today cannot stop working because a grammar
disagrees with it.

Markdown is deliberately not routed through here. Its comments are HTML ones
the markdown scanner already finds exactly, and its blocks are paragraphs,
which is what the blank-line rule *is* — there is nothing for a grammar to
correct.

`LURIA_TREE_SITTER=0` turns the extra off without uninstalling it — worth
having, because the backend is a native one. `tree-sitter` 0.26.0 corrupts the
heap when trees are walked, badly enough to segfault a bare 25-line script over
this repository's own files; the extra pins below it, and the switch is the
answer to the next such release arriving before the pin does.
"""
from __future__ import annotations

import functools
import os
import re
import threading
from pathlib import Path
from typing import NamedTuple

# The first parse of a given language fetches that grammar (the pack caches it
# under the user's cache directory). Everything here treats any failure —
# missing package, no grammar for the suffix, no network on a cold cache — as
# "no opinion", so a lint never blocks on it.
#
# Cached as plain data, never as trees: a file is parsed once however many
# directives it holds, and no native object outlives the call that made it.
_PARSED: dict[tuple[str, int], list | None] = {}
_MAX_CACHED = 64

# Everything that touches the native layer happens under this. The bindings
# promise no thread-safety, luria builds its reports on a thread pool, and a
# native failure does not raise — it takes the process down somewhere else
# entirely, several files later. Parsing is a small part of a lint, so
# serialising it costs little next to that.
_LOCK = threading.RLock()

# Markdown never reaches a grammar, because it has nothing to gain from one.
# Its comments are HTML comments the markdown scanner already finds exactly,
# and its blocks *are* paragraphs — the blank-line rule is not an
# approximation of markdown's structure, it is markdown's structure. Sending
# it through a parser would risk changing a well-covered behaviour to reach
# the same answer.
_PROSE = {".md", ".markdown"}


@functools.lru_cache(maxsize=1)
def available() -> bool:
    """Whether a grammar backend is installed and switched on."""
    if os.environ.get("LURIA_TREE_SITTER", "").strip() in {"0", "off", "no"}:
        return False
    try:
        import tree_sitter_language_pack  # noqa: F401
    except Exception:
        return False
    return True


class _Node(NamedTuple):
    """A node, as plain data. Nothing native survives past `_nodes`."""
    type: str
    named: bool
    children: int
    start: tuple[int, int]          # 0-based (row, column)
    end: tuple[int, int]
    start_byte: int
    end_byte: int

    @property
    def size(self) -> int:
        return self.end_byte - self.start_byte

    @property
    def end_line(self) -> int:
        """The 1-based last line this node occupies.

        A node ending at column 0 has consumed the newline of the line before
        it and occupies nothing on the row tree-sitter reports."""
        row, column = self.end
        return row if column == 0 else row + 1


def _nodes(tree) -> list[_Node]:
    """Every node in `tree`, converted to plain data in one pass.

    Read with a cursor and copied immediately, so that no live node outlives
    this function. That is the boundary the rest of the module is written
    against: a node is a view into memory the bindings own, a failure there is
    a segfault rather than an exception, and a segfault has no traceback and
    surfaces in whatever allocates next. Copying out is cheap — a lint reads
    every node exactly once — and it means only this function has to be right
    about lifetimes."""
    out: list[_Node] = []
    cursor = tree.walk()
    visited = False
    while True:
        if not visited:
            node = cursor.node
            out.append(_Node(node.type, node.is_named, node.child_count,
                             (node.start_point.row, node.start_point.column),
                             (node.end_point.row, node.end_point.column),
                             node.start_byte, node.end_byte))
            del node
            if cursor.goto_first_child():
                continue
        if cursor.goto_next_sibling():
            visited = False
            continue
        if not cursor.goto_parent():
            return out
        visited = True


def _parse(path: Path, text: str) -> list[_Node] | None:
    """Every node in `path`, as plain data — or None for no opinion."""
    if not available() or path.suffix.lower() in _PROSE:
        return None
    key = (str(path), hash(text))
    with _LOCK:
        if key in _PARSED:
            return _PARSED[key]
        out = None
        try:
            import tree_sitter_language_pack as pack
            language = pack.detect_language_from_path(str(path))
            if language:
                tree = pack.get_parser(language).parse(text.encode())
                # A tree with errors is a grammar that does not understand
                # this file. Its comments and its blocks are both guesses at
                # that point, and the crude scan is the better guess because
                # it does not pretend to structure.
                if not tree.root_node.has_error:
                    out = _nodes(tree)
                del tree
        except Exception:
            out = None
        if len(_PARSED) >= _MAX_CACHED:
            _PARSED.clear()
        _PARSED[key] = out
        return out


# A directive opens its comment, so whatever punctuation the language uses to
# start one is not part of it. Stripping every leading non-word character is
# the whole rule: `#`, `//`, `/*`, `--`, `;`, `%`, `<!--` all fall to it, and a
# directive's own name begins with a letter.
_MARKER_RE = re.compile(r"^\W+")


def comments(path: Path, text: str) -> list[tuple[int, int, str]] | None:
    """(line, character offset, body) for every comment, or None for no opinion.

    The shape matches `directives.comment_fragments`, which is the caller."""
    nodes = _parse(path, text)
    if nodes is None:
        return None
    raw = text.encode()
    out = []
    for node in nodes:
        if "comment" not in node.type:
            continue
        body = raw[node.start_byte:node.end_byte].decode("utf-8", "replace")
        # Offsets everywhere else in luria count characters; tree-sitter counts
        # bytes, and the two part company at the first non-ASCII character.
        offset = len(raw[:node.start_byte].decode("utf-8", "replace"))
        out.append((node.start[0] + 1, offset, _MARKER_RE.sub("", body)))
    return sorted(out)


def grow(path: Path, text: str, block: tuple[int, int],
         after: int = 0) -> tuple[int, int]:
    """`block`, extended to the syntactic unit it introduces.

    `after` is the line the directive itself sits on: the unit is what the
    directive *introduces*, so the search starts below it, and a directive
    that already stands above its block (`after` before it) starts at the
    block's own first line.

    The unit is the smallest named node with children that begins at that
    first line of content and holds the whole block. Smallest, because a
    top-level comment's next sibling is often the whole document, which would
    quietly turn `-block` into `-file`. Holding the whole block, because a
    node that stops inside it is part of the block, not the block. With
    children, because a leaf is a token: `f` in `f() {` and `int` in
    `int f(void)` both start in the right place and neither is a block.

    Returns `block` unchanged when there is no grammar, no such node, or
    nothing to add. It never returns a narrower span than it was given."""
    nodes = _parse(path, text)
    if nodes is None:
        return block
    lines = text.splitlines()
    first, last = block
    start = _first_content(lines, max(first, after + 1), last)
    if start is None:
        return block
    best = None
    for node in nodes:
        if not (node.children and node.named and node.start == start):
            continue
        if node.end_line < last:
            continue
        if best is None or node.size < best.size:
            best = node
    if best is None:
        return block
    return (first, max(last, best.end_line))


def _first_content(lines: list[str], first: int,
                   last: int) -> tuple[int, int] | None:
    """The 0-based (row, column) where the block's content starts.

    Column, not just row: a node has to *begin* there to be the block's unit,
    and in an indented file the line's first non-space character is where that
    is."""
    for n in range(first, last + 1):
        if n - 1 < len(lines) and lines[n - 1].strip():
            line = lines[n - 1]
            return n - 1, len(line) - len(line.lstrip())
    return None


