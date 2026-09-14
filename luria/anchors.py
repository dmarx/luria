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

# `<a name="x">`, and only in the empty-anchor form the generator wrote and a
# person writes by hand. An `<a name=… href=…>` is a link that happens to
# carry a legacy name, not an anchor somebody is pointing at.
NAME_ANCHOR_RE = re.compile(r'<a\s+name="([^"]+)"\s*>\s*</a>')
ID_RE = re.compile(r'<[a-zA-Z][^>]*\sid="([^"]+)"')
HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*$", re.M)
# A markdown link whose target is a relative path with a fragment. Absolute
# URLs are somebody else's page, and a bare `#frag` is this page's own, which
# the same rules cover when the page itself is scanned.
FRAGMENT_LINK_RE = re.compile(
    r"\[[^\]]*\]\((?!https?:|mailto:|#)([^)\s#]+\.md)#([^)\s]+)\)")


def slug(heading: str) -> str:
    """A heading's own anchor, GitHub's way.

    Renderers differ in the details and this is the common core — enough to
    recognise a fragment that names a heading, which is all this needs. Being
    generous here is deliberate: the finding this module exists for is about
    an anchor nothing but a real navigation can reach, and a heading is never
    that."""
    text = re.sub(r"<[^>]+>", "", heading).strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", "-", text)


def addressable(text: str) -> set[str]:
    """Every fragment this document can be reached at from anywhere."""
    return set(ID_RE.findall(text)) | {slug(h) for h in HEADING_RE.findall(text)}


def by_name_only(text: str) -> set[str]:
    """Fragments this document answers to on a real navigation and nowhere
    else."""
    return set(NAME_ANCHOR_RE.findall(text)) - addressable(text)


@dataclass(frozen=True)
class Finding:
    """A fragment link whose target anchors it by `name` alone."""
    source: Path
    line: int
    target: Path
    fragment: str
    # True when the target is a generated view. The anchor is still wrong,
    # and editing it would be erased by the next build — the repair is the
    # generator's, which emits `id`, so the remedy is `luria index`.
    generated: bool = False


def scan(files, generated=None, base=None) -> list[Finding]:
    """Every such link across `files`, with the target read once each.

    `generated` answers "is this path a view?" and `base` answers "where does
    this prose render?" — `Config.is_generated` and `Config.link_base` in
    practice. Passed in rather than reached for so the scan stays a function
    of the tree it is handed.

    `base` is not the file's own directory, and assuming it was is a bug
    this had until a real record showed it: a `render = "document"` scheme's
    prose is written to resolve from the page it assembles into, so
    `../../docs/values.md` in a source is correct there and nonsense from
    the source's own folder. `link_base` is the one place that knows."""
    generated = generated or (lambda _p: False)
    base = base or (lambda p: p.parent)
    cache: dict[Path, set[str]] = {}
    found: list[Finding] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        where = Path(base(path))
        for m in FRAGMENT_LINK_RE.finditer(text):
            # Normalized textually rather than resolved: `..` through a
            # directory `luria index` has not created yet fails on the
            # filesystem and reads fine, which is what a renderer does.
            target = Path(os.path.normpath(where / m.group(1)))
            if target not in cache:
                try:
                    cache[target] = by_name_only(
                        target.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError):
                    cache[target] = set()
            if m.group(2) in cache[target]:
                found.append(Finding(path, text.count("\n", 0, m.start()) + 1,
                                     target, m.group(2), generated(target)))
    return found


def repair(text: str, fragments: set[str]) -> str:
    """`text` with each named anchor in `fragments` rewritten to an id.

    Only the ones something links to: an unlinked `<a name=>` in prose is a
    person's own business, and rewriting it would be this tool editing a
    document to satisfy a rule nothing is currently breaking."""
    def swap(m: re.Match) -> str:
        return (f'<a id="{m.group(1)}"></a>' if m.group(1) in fragments
                else m.group(0))
    return NAME_ANCHOR_RE.sub(swap, text)
