#!/usr/bin/env python3
"""Reference-list detection: which blocks of a body are bibliography entries.

A check that asks prose to *explain* a relation (`explain:` on a reference
field) cannot count a bibliography line as the explanation. `Kingma et al.
(2014), LIT-001 — ARXIV-1412.6980.` cites the code and says nothing about
it, and in a record whose documents open with such a line, every relation
to the paper it names is satisfied before a sentence is written. Measured on
the anthology: 719 of 1427 explained relations were cited only there.

Detection reads shape, never headings. A heading is one record's
convention ("## Source", "## References", none at all); an entry's
morphology is common to all of them:

- a **lead** of names ending at a year — `Evci, Ioannou, Keskin and Dauphin
  (2020)`, `Kingma, D. P., & Ba, J. (2014).` — or a classic author list of
  initials and surnames ahead of the title;
- **identifiers** — links, record codes, arXiv ids, DOIs, URLs;
- a **title** and **venue** — the sentence after the lead, when what follows
  it is a venue or an identifier;
- and, decisively, **little prose left over** once those are removed.

The last test is what separates an entry from an annotated entry. `…, LIT-017
— ARXIV-1812.06162. Where the critical batch size is defined, and given a
measurement procedure…` starts as an entry and goes on to say what the paper
contributes; that annotation is the explanation, so the block is prose.

The unit judged is a block: a paragraph, or one list item. Headings, tables,
fenced code and comments are never entries. `regions()` returns the spans of
the blocks judged to be entries, so a caller excludes what falls inside them;
nothing here knows about relations.
"""

from __future__ import annotations

import re

from .doc_refs import COMMENT_RE, _fence_spans

# A list item's marker: bullets, `1.` and `[1]`.
_ITEM_RE = re.compile(r"^[ \t]*(?:[-*+]|\d{1,3}[.)]|\[\d{1,3}\])[ \t]+")
_YEAR_RE = re.compile(r"\(?\b(?:1[89]|20)\d{2}[a-z]?\b\)?")
_LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)\s]*(?:\s+\"[^\"]*\")?\)")
_URL_RE = re.compile(r"(?:https?://|www\.)\S+|\bdoi\.org/\S+", re.I)
_IDENT_RE = re.compile(
    r"\b[A-Z][A-Z0-9]+(?:-[A-Z]+)*[-:][\w./]+"            # LIT-001, ARXIV-1412.6980, DOI:10.…
    r"|\barXiv:\s?\d{4}\.\d{4,5}(?:v\d+)?"
    r"|\b10\.\d{4,9}/\S+", re.I)
_CODE_SPAN_RE = re.compile(r"`[^`\n]+`")

# One name in an author lead: a surname, a particle, an initial, a corporate
# word (`Kimi Team`, `The Movie Gen team`). The lead is a run of these,
# joined by commas, `and`, `&`, with `et al.` anywhere in it — an affiliation
# may follow it (`Shi et al., Meta (2023)`).
_NAME = (r"(?:(?:van|von|de|der|den|du|da|di|la|le|el|al)\s+)*"
         r"(?:[A-Z][\w'’.-]*|[A-Z]\.(?:\s?[A-Z]\.)*|team|group|lab|colleagues|others)")
# `of`/`at`/`for`/`the` join the words of an affiliation (`University of
# Texas at Austin`); a lower-case word that is not one of them ends the lead.
_JOIN = r"(?:(?:\s*(?:,|&|\band\b)\s*)+|\s+(?:(?:of|at|for|the)\s+)?)"
_ETAL = r"(?:,?\s+et\s+al\.?)"
_LEAD_RE = re.compile(
    rf"^(?:\*\*)?{_NAME}(?:{_ETAL}|{_JOIN}{_NAME}){{0,40}}{_ETAL}?"
    r",?\s*\(?(?:1[89]|20)\d{2}[a-z]?\)?(?:\*\*)?[.,]?")
# A classic author list ahead of the title: `A. Vaswani, N. Shazeer, et al.`
_INITIAL_NAME = r"(?:[A-Z]\.\s?)+[A-Z][\w'’-]+"
_CLASSIC_RE = re.compile(
    rf"^{_INITIAL_NAME}(?:\s*,\s*(?:and\s+)?{_INITIAL_NAME}){{0,40}}"
    r"(?:,?\s+et\s+al\.?)?\.?\s")

_VENUE_WORDS = (
    r"In|Proceedings|Proc\.|Conference|Workshop|Journal|Transactions|"
    r"arXiv|preprint|NeurIPS|NIPS|ICML|ICLR|CVPR|ICCV|ECCV|ACL|EMNLP|NAACL|"
    r"AAAI|IJCAI|JMLR|TMLR|COLT|AISTATS|KDD|SIGGRAPH|Nature|Science|"
    r"vol\.?|pp\.?|no\.?|pages|Press|Inc\.?|Ltd\.?|edition|ed\.|eds\.")
_VENUE_RE = re.compile(rf"(?<!\w)(?:{_VENUE_WORDS})(?!\w)")
_TITLE_THEN_VENUE_RE = re.compile(
    rf"^[^.?!]{{3,240}}[.?!]\s+(?=(?:{_VENUE_WORDS})(?!\w)|\S*(?:arXiv|doi|https?:))")
# Connective words a reference entry hardly uses and a sentence can hardly
# avoid.
_FUNCTION_WORDS = frozenset(
    "the a an is are was were be been being that which who whom whose this "
    "these those it its they them their we our us he she his her to of for "
    "with by as on at from into in and than then so because but not no nor "
    "or either both each if when while where why how what does do did has "
    "have had can could would should may might must will only also".split())
# Words as prose writes them: lower case. A reference is names, initials,
# acronyms and numbers, all of which this skips, so authors surviving in a
# second entry on the line (`and Chen et al.`) cost nothing.
_LOWER_RE = re.compile(r"(?<![\w'’-])[a-z][a-z'’-]+")
_NOT_PROSE = frozenset({"et", "al"})

# The leftover reads as prose at this many lower-case words, or at
# MIN_CLAUSE_WORDS when connectives tie them into a clause. Below both it is
# metadata ("read as", "accounted for by"), not an account of the work.
MIN_PROSE_WORDS = 8
MIN_CLAUSE_WORDS = 5
MIN_FUNCTION_WORDS = 2
# A block that is nothing but references (a bare link, `Read from LIT-378 —
# ARXIV-…`) may keep this many words of glue.
MAX_GLUE_WORDS = 2


def _strip_markup(text: str) -> str:
    text = _ITEM_RE.sub("", text, count=1)
    text = _LINK_RE.sub(lambda m: f" {m.group(1)} ", text)
    text = _CODE_SPAN_RE.sub(" ", text)
    return text.replace("**", "").replace("__", "")


def _without_references(text: str) -> str:
    """Identifiers, URLs and years removed: what a block says besides what
    it points at."""
    text = _URL_RE.sub(" ", text)
    text = _IDENT_RE.sub(" ", text)
    return _YEAR_RE.sub(" ", text)


def _words(text: str) -> list[str]:
    return [w for w in _LOWER_RE.findall(text) if w not in _NOT_PROSE]


def _prose(words: list[str]) -> bool:
    connectives = sum(w in _FUNCTION_WORDS for w in words)
    return (len(words) >= MIN_PROSE_WORDS or
            (len(words) >= MIN_CLAUSE_WORDS
             and connectives >= MIN_FUNCTION_WORDS))


def is_entry(block: str) -> bool:
    """Whether one block (a paragraph or a list item) is a reference entry."""
    raw = block.strip()
    if not raw:
        return False
    text = _strip_markup(raw)
    pointers = bool(_LINK_RE.search(raw) or _URL_RE.search(text)
                    or _IDENT_RE.search(text) or _CODE_SPAN_RE.search(raw))
    # Nothing but references and a word or two of glue.
    unlabelled = _strip_markup(_LINK_RE.sub(" ", raw))
    if pointers and len(_words(_without_references(unlabelled))) <= MAX_GLUE_WORDS:
        return True
    body = text.lstrip()
    lead = _LEAD_RE.match(body) or _CLASSIC_RE.match(body)
    if not lead:
        return False
    rest = body[lead.end():].lstrip(" ,.;:—–-")
    # The sentence after the lead is a title when a venue or an identifier
    # follows it; an annotation is not followed by one.
    title = _TITLE_THEN_VENUE_RE.match(rest)
    if title:
        rest = rest[title.end():]
    rest = _VENUE_RE.sub(" ", _without_references(rest))
    if not (pointers or title or _YEAR_RE.search(body)):
        return False
    return not _prose(_words(rest))


def _blocks(text: str) -> list[tuple[int, int]]:
    """Paragraphs and list items, as spans; headings, tables, fences and
    comments excluded."""
    skip = _fence_spans(text) + [m.span() for m in COMMENT_RE.finditer(text)]
    out: list[tuple[int, int]] = []
    start = None
    pos = 0
    for line in text.splitlines(keepends=True):
        a, b = pos, pos + len(line)
        pos = b
        stripped = line.strip()
        hidden = any(x <= a < y for x, y in skip)
        boundary = (not stripped or hidden or stripped.startswith(("#", "|"))
                    or _ITEM_RE.match(line))
        if boundary and start is not None:
            out.append((start, a))
            start = None
        if not stripped or hidden or stripped.startswith(("#", "|")):
            continue
        if start is None:
            start = a
    if start is not None:
        out.append((start, pos))
    return out


def regions(text: str) -> list[tuple[int, int]]:
    """The spans of `text` that are reference entries, trailing whitespace
    trimmed."""
    out = []
    for a, b in _blocks(text):
        if is_entry(text[a:b]):
            while b > a and text[b - 1].isspace():
                b -= 1
            out.append((a, b))
    return out


def within(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(a <= pos < b for a, b in spans)
