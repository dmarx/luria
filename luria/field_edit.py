#!/usr/bin/env python3
"""Add or remove one code in a list-valued frontmatter field, in place.

Text surgery rather than a YAML round-trip, and deliberately: rewriting a
document through a parser reflows every other field — quoting, key order,
block scalars, the comments a scaffolded document is mostly made of — and
turns a one-line change into a diff nobody can review. What is wanted is the
one line, so this edits the lines.

Two rules the callers depend on. A `many` field accepts a single code
written as a scalar, so adding widens a scalar into a list rather than
replacing it; overwriting would silently delete a relation. And a field that
loses its last entry loses its own line too — a bare `extended_by:` with
nothing under it is invalid frontmatter, not a relation held by nobody.
"""

from __future__ import annotations

import re


def add_to_field(text: str, name: str, code: str) -> str:
    """Add one code to a list-valued frontmatter field, creating the field
    when it is absent and widening a scalar rather than replacing it.

    A `many` field accepts one code written as a scalar (a list of one), so
    the scalar case is real and overwriting it would silently delete a
    relation — the quiet kind of loss this module exists to end."""
    if not text.startswith("---\n"):
        return text
    end = text.index("\n---\n", 3) + 1
    head, rest = text[4:end], text[end:]
    lines = head.splitlines(keepends=True)
    out, at, done = [], 0, False
    while at < len(lines):
        line = lines[at]
        if not done and re.match(rf"^{re.escape(name)}\s*:", line):
            value = line.split(":", 1)[1].strip()
            at += 1
            items = []
            while at < len(lines) and lines[at].startswith("- "):
                items.append(lines[at])
                at += 1
            out.append(f"{name}:\n")
            if value:
                out.append(f"- {value}\n")
            out.extend(items)
            out.append(f"- {code}\n")
            done = True
            continue
        out.append(line)
        at += 1
    if not done:
        out.append(f"{name}:\n- {code}\n")
    return "---\n" + "".join(out) + rest


def drop_from_field(text: str, name: str, code: str) -> str:
    """Take one code out of a list-valued frontmatter field, removing the
    field itself when that was its last entry.

    A field left standing with nothing under it is not a relation held by
    nobody — it is invalid frontmatter, and the next reader gets a parse
    error instead of the tidy record the deletion was meant to leave."""
    if not text.startswith("---\n"):
        return text
    end = text.index("\n---\n", 3) + 1
    head, rest = text[4:end], text[end:]
    lines, out, at = head.splitlines(keepends=True), [], 0
    while at < len(lines):
        line = lines[at]
        if not re.match(rf"^{re.escape(name)}\s*:", line):
            out.append(line)
            at += 1
            continue
        value = line.split(":", 1)[1].strip()
        at += 1
        kept = [value] if value else []
        while at < len(lines) and lines[at].startswith("- "):
            kept.append(lines[at][2:].strip())
            at += 1
        kept = [k for k in kept if k != code]
        if kept:
            out.append(f"{name}:\n")
            out += [f"- {k}\n" for k in kept]
    return "---\n" + "".join(out) + rest
