#!/usr/bin/env python3
"""An anchor a fragment link can actually reach.

A markdown fragment — `design-principles.md#dp-3` — is resolved by whatever
renders the page, and the renderers do not agree on what counts as an anchor:

- **A heading** gets an `id` from every renderer there is. Fragile in the
  other direction (reword the heading and the link stops resolving), but
  addressable wherever the page is published.
- **`<a id="x">`** is an element with that id, so a fragment reaches it by
  navigation and `getElementById` alike.
- **`<a name="x">`** is neither. A *real navigation* falls back to `a[name]`,
  which is why it works in the repository and on GitHub — and a single-page
  app never performs one. Quartz, which is what `luria site` builds, scrolls
  with `document.getElementById(...)` and nothing else
  (v4.5.2, `components/scripts/spa.inline.ts`).

So `name` is the one spelling that is addressable where a contributor checks
and not addressable where the record is published. Luria emitted it, and 89
of the 100 fragment links in its own repository resolved that way and no
other — every devlog entry link, and every citation of a principle.

The generator emits `id` now. This module is the rest of the answer: the
check that says so about a hand-written anchor, and the repair, which edits
the TARGET — the link is spelled correctly and the thing it names cannot be
found.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from . import slugs

# `<a name="x">`, and only in the empty-anchor form the generator wrote and a
# person writes by hand. An `<a name=… href=…>` is a link that happens to
# carry a legacy name, not an anchor somebody is pointing at.
NAME_ANCHOR_RE = re.compile(r'<a\s+name="([^"]+)"\s*>\s*</a>')
ID_RE = re.compile(r'<[a-zA-Z][^>]*\sid="([^"]+)"')
# A markdown link whose target is a relative path with a fragment. Absolute
# URLs are somebody else's page, and a bare `#frag` is this page's own, which
# the same rules cover when the page itself is scanned.
FRAGMENT_LINK_RE = re.compile(
    r"\[[^\]]*\]\((?!https?:|mailto:|#)([^)\s#]+\.md)#([^)\s]+)\)")


def addressable(text: str) -> set[str]:
    """Every fragment this document can be reached at from anywhere.

    The heading half is `slugs`, which is the same function the generator
    uses to WRITE these links — deliberately, because a check computing the
    anchor a second way would agree with the generator and not with the
    publisher, which is the failure it exists to catch (ADR-100)."""
    return set(ID_RE.findall(text)) | set(slugs.anchors_for(text).values())


def by_name_only(text: str) -> set[str]:
    """Fragments this document answers to on a real navigation and nowhere
    else."""
    return set(NAME_ANCHOR_RE.findall(text)) - addressable(text)


@dataclass(frozen=True)
class Reach:
    """How a document can be reached: every fragment that resolves, the ones
    that resolve only on a real navigation, and whether it could be read."""
    addressable: set[str]
    named: set[str]
    known: bool


@dataclass(frozen=True)
class Finding:
    """A fragment link whose target anchors it by `name` alone."""
    source: Path
    line: int
    target: Path
    fragment: str
    # True when the source is a generated view — the anchor is the
    # generator's to fix, and an edit written there is erased by the next
    # build.
    generated: bool = False
    # "name-only": the target answers on a real navigation and nowhere else,
    # which `--fix` repairs. "missing": it answers nowhere at all, which only
    # a person can resolve — a typo, a reworded heading, or a link written
    # against a page that has since changed.
    kind: str = "name-only"


def scan(documents: dict[Path, str], generated=None, base=None) -> list[Finding]:
    """Every such link across `documents`, a mapping of path to content.

    Content rather than paths, and this is the whole of what CI taught this
    check. Read from disk, it reports the COMMITTED views — and a branch
    carries the default branch's copies of those and is forbidden to update
    them (ADR-018), so the check failed every pull request that touched an
    anchor and named a repair the author was not allowed to make. Handed the
    render instead, it asks the question that is actually about this source
    tree: will the views this record produces contain a fragment nothing can
    scroll to? `check_view_dirs` has always worked this way, and its
    docstring says why — "a branch carries the default branch's copies and
    has nothing to be stale against".

    `generated` answers "is this path a view?" and `base` answers "where
    does this prose render?" — `Config.is_generated` and `Config.link_base`
    in practice. `base` is not the file's own directory: a
    `render = "document"` scheme's prose is written to resolve from the page
    it assembles into, so `../../docs/values.md` in a source is correct there
    and nonsense from the source's own folder."""
    generated = generated or (lambda _p: False)
    base = base or (lambda p: p.parent)
    cache: dict[Path, Reach] = {}
    found: list[Finding] = []

    def anchors_at(target: Path) -> Reach:
        if target not in cache:
            text = documents.get(target)
            known = text is not None
            if text is None:
                try:
                    text = target.read_text(encoding="utf-8")
                    known = True
                except (OSError, UnicodeDecodeError):
                    text = ""
            cache[target] = Reach(addressable(text), by_name_only(text), known)
        return cache[target]

    for path, text in documents.items():
        where = Path(base(path))
        for m in FRAGMENT_LINK_RE.finditer(text):
            # Normalized textually rather than resolved: `..` through a
            # directory `luria index` has not created yet fails on the
            # filesystem and reads fine, which is what a renderer does.
            target = Path(os.path.normpath(where / m.group(1)))
            frag, line = m.group(2), text.count("\n", 0, m.start()) + 1
            reach = anchors_at(target)
            if frag in reach.named:
                found.append(Finding(path, line, target, frag,
                                     generated(path), "name-only"))
            elif reach.known and frag not in reach.addressable:
                # `known` guards the case where the target could not be read
                # at all: a link into a file this record does not own is not
                # this record's finding, and reporting every one of them
                # would bury the ones that are.
                found.append(Finding(path, line, target, frag,
                                     generated(path), "missing"))
    # A stub's prose is *in* the page it renders into, so the same link is
    # found twice — once where a person wrote it and once in the view. One
    # defect, reported where it can be acted on.
    authored = {(f.target, f.fragment) for f in found if not f.generated}
    return [f for f in found
            if not f.generated or (f.target, f.fragment) not in authored]


def repair(text: str, fragments: set[str]) -> str:
    """`text` with each named anchor in `fragments` rewritten to an id.

    Only the ones something links to: an unlinked `<a name=>` in prose is a
    person's own business, and rewriting it would be this tool editing a
    document to satisfy a rule nothing is currently breaking."""
    def swap(m: re.Match) -> str:
        return (f'<a id="{m.group(1)}"></a>' if m.group(1) in fragments
                else m.group(0))
    return NAME_ANCHOR_RE.sub(swap, text)


def documents(rendered: dict[Path, str] | None = None) -> dict[Path, str]:
    """What the anchor check reads: every source, and every view AS THE
    GENERATOR WOULD WRITE IT — never the committed copy.

    The motivating case is a journal index linking into a journal book, and
    both are generated, so sources alone cannot see it. The committed copies
    cannot be used either: on a branch they are the default branch's, which
    this record deliberately does not update there (ADR-018)."""
    from . import doc_refs
    from .adr_index import outputs
    out: dict[Path, str] = {}
    for path in doc_refs.doc_files():
        try:
            out[path] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    out.update(outputs() if rendered is None else rendered)
    return out
