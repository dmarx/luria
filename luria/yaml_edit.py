#!/usr/bin/env python3
"""Editing a config document without destroying it.

Three commands rewrite a config a person wrote: `luria init` adds a scheme,
`luria upgrade` wires up a field, `luria migrate` renames one. All three have
the same requirement and it is not the obvious one — the edit has to be
*structural*, and the comments have to survive.

Neither obvious tool does both. `OmegaConf.merge` composes values correctly
and drops every comment, which is right for building a config out of defaults
and wrong for editing one on disk. Line surgery keeps the comments and gets
the structure wrong: YAML nests by indentation, so an indented block appended
to a document attaches to whatever the last top-level key happens to be, and a
bare `FXL:` occurs under `schemes:` and under every `remotes.<R>.schemes:`.
Both failures are silent (ADR-tmp8hp25).

`ruamel.yaml` in round-trip mode does both, so these are the four operations
the commands need and the only place that knows how a config is edited.
"""

# inactive-ok-file: ADR-tmp8hp25 — Proposed. Named as the decision this module
# implements; the citation is to the reasoning, not a claim it is settled.

from __future__ import annotations

import io
from collections.abc import Iterator
from typing import Any

from ruamel.yaml import YAML


def _rt() -> YAML:
    yaml = YAML()
    yaml.preserve_quotes = True
    # Never wrap. ruamel and PyYAML break long scalars in different places,
    # so a width would make every edit rewrap somebody's blurbs; with no
    # width the emitter is idempotent, and the configs in this repo are
    # written in the shape it emits.
    yaml.width = 1 << 30
    return yaml


def load(text: str) -> Any:
    return _rt().load(text) or {}


def dump(data: Any) -> str:
    buf = io.StringIO()
    _rt().dump(data, buf)
    return buf.getvalue()


def at(data: Any, path: tuple[str, ...]) -> Any | None:
    """The mapping at `path`, or None if the document has no such place."""
    node = data
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node if isinstance(node, dict) else None


def ensure(data: Any, path: tuple[str, ...]) -> Any:
    """The mapping at `path`, creating the empty ones on the way."""
    node = data
    for key in path:
        if key not in node or not isinstance(node[key], dict):
            node[key] = {}
        node = node[key]
    return node


def merge_into(data: Any, extra: dict, path: tuple[str, ...] = ()) -> Any:
    """Fold `extra` into the document at `path`, keeping what is there.

    A deep merge rather than an assignment: setting `schemes` to a new mapping
    would silently drop every scheme the file already declared."""
    def _deep(into: Any, more: dict) -> None:
        for key, value in more.items():
            if isinstance(value, dict) and isinstance(into.get(key), dict):
                _deep(into[key], value)
            else:
                into[key] = value
    _deep(ensure(data, path) if path else data, extra)
    return data


def rename_key(data: Any, path: tuple[str, ...], old: str, new: str) -> bool:
    """Rename one key of the mapping at `path`, in place, keeping its order.

    In place because order is content in a config a person reads, and because
    the comments attached to the key belong to it rather than to its position.
    Returns whether anything was renamed."""
    node = at(data, path)
    if node is None or old not in node or new in node:
        return False
    # Rebuild the mapping in order, swapping the one key, so the renamed entry
    # stays where its author put it.
    items = [(new if k == old else k, v) for k, v in node.items()]
    for key in list(node):
        del node[key]
    for key, value in items:
        node[key] = value
    return True


def set_block(parent: Any, key: str, value: Any, before: str = "",
              indent: int = 2) -> None:
    """Add `key: value` to `parent`, with `before` as the comment above it.

    The comment goes through ruamel rather than into the text, so it lands
    above the key wherever the key lands — which is the whole difference
    between a generated block and a generated block in the right place."""
    parent[key] = value
    if before:
        parent.yaml_set_comment_before_after_key(key, before=before,
                                                 indent=indent)


def keys(data: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[tuple[str, ...], int, int]]:
    """(path, line, column) for every mapping key, in document order.

    Zero-based, as ruamel records them."""
    if not isinstance(data, dict):
        return
    where = getattr(getattr(data, "lc", None), "data", None) or {}
    for key, value in data.items():
        if key not in where:
            continue
        here = path + (str(key),)
        yield here, where[key][0], where[key][1]
        yield from keys(value, here)


def span(data: Any, path: tuple[str, ...]) -> tuple[int, int | None] | None:
    """The half-open line range the entry at `path` occupies, or None.

    From its own line to the line the next entry at or outside its
    indentation starts on; `None` for the end means the end of the document.
    Line numbers rather than a subtree because the callers that need this
    are rewriting the *text* and need to know which lines are whose."""
    found: tuple[int, int] | None = None
    for here, line, col in keys(data):
        if found is not None and col <= found[1]:
            return found[0], line
        if here == path:
            found = (line, col)
    return (found[0], None) if found else None
