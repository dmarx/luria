#!/usr/bin/env python3
"""Titles that claim to transfer, checked against the project's own nouns.

A decision is *about* something specific, and naming that thing in its title is
correct. A **principle** is the opposite: one stated about the artifact it was
first noticed on is one nobody applies to the next artifact. That failure is
quiet — the principle stays true, keeps rendering, keeps passing every other
check, and simply never gets cited, because it reads as a rule about a subsystem
the next reader isn't in.

    [luria.lint]
    narrow_terms = ["node", "canvas", "toolbar"]

    [luria.schemes.DP]
    titles_generalize = true

**Luria ships no vocabulary.** The words are the project's own concrete nouns,
and a shipped list would be some other project's vocabulary wearing the
authority of a default. An empty `narrow_terms` means this class never fires —
correct for a project that has not thought about it, and the reason the check
costs nothing to nobody.

**What a clean run means.** "The title is reusable", never "the principle is
general". The vocabulary is a *symptom* detector: rewriting "toolbar" to
"mechanism" satisfies it without necessarily broadening anything, and a title
made entirely of abstract words can still be parochial. It earns its place by
being cheap and by catching the obvious case in the one line every citation
repeats — the title is what an author writes first, so it is the cheapest place
to be told "widen this".

**Titles only, deliberately.** Measured on the corpus this was built for, a
title check catches roughly a third of the genuinely narrow principles. Linting
bodies was tried and abandoned: it caught 5 of 6 but fired on 8 of the 15 that
were fine, and a check wrong more often than right gets switched off — and
deserves to be.

**Fail-open on purpose.** A noun missing from the vocabulary ships a narrow
title unflagged. Guessing at abstractions instead would fire on titles like "One
authoritative implementation", which is exactly the phrasing worth keeping. A
miss costs a review comment; a false alarm costs trust in the check.

**A word used in another sense is acknowledged, never removed from the
vocabulary** — removing it would stop it working everywhere else:

    <!-- broad-ok: overlay — a verb here ("choice overlays the baseline") -->

Same directive grammar as `inactive-ok:` and its family, so there is one shape
to learn. Place it inside the document, anywhere the directive scanner reaches.
"""

from __future__ import annotations

import re

from . import directives
from .adr_index import parse_frontmatter
from .config import current

ACK = "broad-ok"


def _pattern(terms: tuple[str, ...]) -> re.Pattern | None:
    """One alternation over the vocabulary, plural-tolerant.

    Built per call rather than cached: the vocabulary is config, and config
    resets. A stale pattern would be the hand-kept projection this project
    exists to argue against."""
    words = sorted({t.strip().lower() for t in terms if t.strip()})
    if not words:
        return None
    alt = "|".join(re.escape(w) for w in words)
    return re.compile(rf"\b({alt})s?\b", re.IGNORECASE)


def _acknowledged(path, text: str) -> set[str]:
    """Terms this document says it is using in another sense."""
    out: set[str] = set()
    for d in directives.find(path, text, {ACK}):
        out.update(a.strip().lower().rstrip("s") for a in d.args if a.strip())
    return out


def rows() -> list[str]:
    """One line per narrow title, ready for the warning report."""
    cfg = current()
    pattern = _pattern(cfg.narrow_terms)
    if pattern is None:
        return []
    found: list[str] = []
    for scheme in cfg.schemes.values():
        if not scheme.titles_generalize:
            continue
        for number, path in scheme.documents().items():
            text = path.read_text(encoding="utf-8")
            meta, _ = parse_frontmatter(text)
            title = str(meta.get("title") or "").strip()
            if not title:
                continue
            hits = {m.lower().rstrip("s") for m in pattern.findall(title)}
            hits -= _acknowledged(path, text)
            if hits:
                found.append(
                    f"{scheme.code(number)} names {', '.join(sorted(hits))} — "
                    f"state the pattern, not the artifact it was first noticed "
                    f"on ({cfg.rel(path)})")
    return sorted(found)
