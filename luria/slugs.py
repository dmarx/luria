#!/usr/bin/env python3
"""The anchor a heading answers to, computed the way every renderer does.

Luria did not need this while its generated links pointed only at anchors it
emitted itself. It does now: a book's contents list links the heading, and a
heading's id is assigned by the publisher — `rehype-slug` on the site, the
same algorithm on GitHub, both of them `github-slugger`. So luria has to
produce the same string, and owning a fourth copy of somebody else's
algorithm is a thing to do carefully or not at all (DP-4).

Carefully, then — and carefully here did not mean reading it closely. It
meant diffing against 288 headings the site had actually published, which is
what caught the two things the obvious implementation gets wrong: `_` is a
word character and survives, and each space becomes one hyphen AFTER the
punctuation is removed, so a removed em-dash leaves two. Repeats within one
document get `-1`, `-2` appended in document order, which is why this is a
class rather than a function — the answer for "Notes" depends on how many
"Notes" came before it.

What makes owning it safe is not care, it is the check beside it: luria
renders the page it links into, so `anchors` can verify every generated
fragment resolves against the very text the generator produced. A drift
between this and the publisher's slugger becomes a lint failure rather than
a link that quietly goes nowhere (ADR-100).
"""

# inactive-ok-file: ADR-100 — Proposed. Every mention names it as
# the decision this file implements or is written against; the citation
# is to the reasoning, not a claim the decision is settled.

from __future__ import annotations

import re

# github-slugger, whole:
#
#     value.toLowerCase().replace(regex, '').replace(/ /g, '-')
#
# Read in that order, because both halves of the order matter and guessing
# got both wrong. `regex` removes punctuation and symbols; `\w` keeps the
# underscore, so `fail_on` survives as `fail_on` and not `failon`. Then EACH
# SPACE becomes a hyphen — runs are not collapsed, so "log — September",
# whose em-dash is removed and leaves two spaces, slugs to `log--september`.
# Both were found by diffing 146 real headings against what Quartz published,
# which is the only way this is worth owning at all.
_STRIP = re.compile(r"[^\w\s-]", re.UNICODE)
# An emitted anchor is html, and a heading may carry inline markup. Neither
# reaches the publisher's slugger, which reads the heading's TEXT nodes —
# and the markdown markers that wrap them (backticks, asterisks) are
# punctuation `_STRIP` removes anyway. Only tags need taking out by hand.
_TAGS = re.compile(r"<[^>]+>")


def text_of(heading: str) -> str:
    """A heading's plain text: tags removed, the way a parser sees it."""
    return _TAGS.sub("", heading).strip()


def slug(heading: str) -> str:
    """The anchor for one heading, ignoring repeats. Use `Slugger` when a
    whole document's headings are being numbered."""
    return _STRIP.sub("", text_of(heading).lower()).replace(" ", "-")


class Slugger:
    """One document's headings, in order, with repeats disambiguated.

    `github-slugger` appends `-1`, `-2`, … to the SECOND and later
    occurrences of a slug, counting per document. Two entries titled "Notes"
    in one book is not hypothetical — a journal is exactly where it
    happens — and getting the suffix wrong is a link to the wrong entry,
    which is worse than a link to nothing."""

    def __init__(self) -> None:
        self._seen: dict[str, int] = {}

    def slug(self, heading: str) -> str:
        # `github-slugger`'s loop, and the increment has to be re-read from
        # the table each time round rather than carried in a local: a
        # document with "Notes", "Notes 1" and "Notes" again makes the first
        # candidate collide with a slug already taken, and a stale counter
        # proposes the same one forever.
        base = result = slug(heading)
        while result in self._seen:
            self._seen[base] += 1
            result = f"{base}-{self._seen[base]}"
        self._seen[result] = 0
        return result


# A fenced block, so a `# comment` inside one is not read as a heading. Both
# fence characters, any length from three, and the closing fence must be at
# least as long as the opening one — which is what lets a fence contain a
# shorter one.
_FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})")
_HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")


def headings(text: str) -> list[str]:
    """Every heading's text, in document order, code fences skipped.

    In order because that is what a slug depends on: the second "Notes" in a
    document is `notes-1`, and a heading inside a shell example that got
    counted would shift every suffix after it. One implementation, because
    the generator and the check have to agree about what a heading is or the
    check is checking something else (ADR-100)."""
    out: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        if m := _FENCE.match(line):
            mark = m.group(2)
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence):
                fence = None
            continue
        if fence is None and (m := _HEADING.match(line)):
            out.append(m.group(1))
    return out


def anchors_for(text: str) -> dict[str, str]:
    """`{heading text: its slug}` for one document, in order."""
    slugger = Slugger()
    return {h: slugger.slug(h) for h in headings(text)}
