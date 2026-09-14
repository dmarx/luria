#!/usr/bin/env python3
"""What a project wrote about its own config, and where it wrote it.

`tomllib` returns values. A config's *documentation* is its comments, and the
first version of `luria upgrade yaml` parsed the one and dropped the other
without saying so — 273 lines of reasoning in one record, 85 in another, gone
in a command that reported only what it folded.

Values have to be re-encoded rather than copied: a regex in a `uid` escapes
differently in the two formats, which is why `convert_config` goes through a
parser at all. Comments are not values. They are prose attached to a place,
so carrying them needs only the place — which is what this module recovers.

A block is a run of comment lines together with the path of the first key or
table that follows it. Blank lines between the run and that key do not break
the attachment; a blank line inside a run does. What the caller does with a
path that no longer exists is the caller's problem — `convert_config` knows
which keys it moved and this module does not.
"""

from __future__ import annotations

import re

_TABLE = re.compile(r"^\s*\[\[?\s*([^\]]+?)\s*\]\]?\s*$")
_KEY = re.compile(r"""^\s*((?:[A-Za-z0-9_.\-]+|"[^"]*"|'[^']*'))\s*=""")


def _bare(line: str) -> str:
    """The line with quoted strings and any trailing comment removed.

    Only used for counting brackets, so the replacement need not be valid
    TOML — it needs the same bracket balance outside strings."""
    out, i, n = [], 0, len(line)
    while i < n:
        ch = line[i]
        if ch in "\"'":
            quote = ch
            i += 1
            while i < n and line[i] != quote:
                i += 2 if line[i] == "\\" and quote == '"' else 1
            i += 1
            continue
        if ch == "#":
            break
        out.append(ch)
        i += 1
    return "".join(out)


def _path(name: str) -> tuple[str, ...]:
    """A dotted table name as a path, with the `luria` root dropped."""
    parts = [p.strip().strip("\"'") for p in name.split(".")]
    if parts and parts[0] == "luria":
        parts = parts[1:]
    return tuple(p for p in parts if p)


def blocks(text: str) -> list[tuple[tuple[str, ...], str]]:
    """(path, comment text) for every comment block, in document order.

    The text is the comment lines with their `#` and one following space
    stripped, joined by newlines — the shape ruamel wants to write it back.
    A block before the first table has the empty path: it is the document's
    own header rather than any key's."""
    found: list[tuple[tuple[str, ...], str]] = []
    table: tuple[str, ...] = ()
    run: list[str] = []
    depth = 0
    for line in text.splitlines():
        stripped = line.strip()
        if depth > 0:
            # Inside a multi-line value. Nothing here is a key, and a comment
            # inside a list belongs to the value rather than to a place.
            depth += _bare(line).count("[") - _bare(line).count("]")
            depth += _bare(line).count("{") - _bare(line).count("}")
            continue
        if stripped.startswith("#"):
            run.append(re.sub(r"^#\s?", "", stripped))
            continue
        if not stripped:
            continue
        if m := _TABLE.match(line):
            table = _path(m.group(1))
            if run:
                found.append((table, "\n".join(run)))
        elif m := _KEY.match(line):
            if run:
                # A dotted key is a path, not a name: `uris.title = "..."`
                # nests exactly as `[remotes.ARXIV.uris]` + `title` would, so
                # it has to be split or the comment lands on a key called
                # "uris.title" that no parser ever produces.
                found.append((table + _path("x." + m.group(1))[1:],
                              "\n".join(run)))
            bare = _bare(line)
            depth = (bare.count("[") - bare.count("]")
                     + bare.count("{") - bare.count("}"))
        run = []
    if run:
        # Trailing prose with nothing after it. It documents the file, and the
        # empty path is where the caller puts that.
        found.append(((), "\n".join(run)))
    return found


def rejoin(text: str) -> str:
    """Restore the bare `#` lines a paragraph break inside a block becomes.

    ruamel writes an empty comment line as an empty *line*, which is not a
    comment: it detaches the prose below it from the key it documents, and in
    a long config that is the exact confusion the carry exists to prevent.
    A blank line between two comments at the same indentation was a `#`."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip() or not 0 < i < len(lines) - 1:
            continue
        before, after = lines[i - 1], lines[i + 1]
        if not (before.lstrip().startswith("#")
                and after.lstrip().startswith("#")):
            continue
        indent = len(before) - len(before.lstrip())
        if indent == len(after) - len(after.lstrip()):
            lines[i] = " " * indent + "#"
    return "\n".join(lines)
