# luria/steps.py
"""One step of a nested page, rendered the same way wherever it appears.

A chain page (`chains.py`) and a pattern page's outline (`views.py`,
`luria:pattern.md.j2`) both list documents as indented bullets, and a reader
moving between them should not be able to tell which generator wrote a
line: `[CODE](link) — title *(facets)*`. Both call `step` here, so the two
cannot drift (DP-004).

The link points at the *source* document, rebased to the page's directory
with `prefix_for` — the convention the index has always used, since an
index-rendered scheme has no page per document to point at.

The facets are read through the compiled contract, so a field with a
`default` shows it and a `status:` carrying a note reads as its word
(ADR-076). A facet the document's scheme cannot hold is omitted: a chain
refuses such a facet at load, so it never arises there, while a pattern's
nodes may belong to several schemes and only one of them need hold it.
"""
from __future__ import annotations

from pathlib import Path

from . import statuses
from .adr_index import prefix_for
from .contract import for_scheme


def link(doc, out_dir: Path) -> str:
    """A target for `doc` that resolves from `out_dir`."""
    return prefix_for(doc.scheme, out_dir) + doc.path.name


def annotation(doc, facet_by) -> str:
    """`doc`'s value along each facet its scheme can hold, in order."""
    from .config import nameable
    held = nameable(doc.scheme)
    obligations = for_scheme(doc.scheme)
    meta = statuses.normalised(doc.meta)
    shown: list[str] = []
    for field in facet_by:
        if field in held:
            shown += [str(v) for v in (obligations.reading(field, meta) or ())]
    return ", ".join(shown)


def step(doc, out_dir: Path, facet_by, lead: str = "") -> str:
    """One line of a nested page, without its indentation and bullet: the
    code linked, the title, and the facets in parentheses when any show."""
    shown = annotation(doc, facet_by)
    return (f"{lead}[{doc.code}]({link(doc, out_dir)}) — {doc.title}"
            + (f" *({shown})*" if shown else ""))
