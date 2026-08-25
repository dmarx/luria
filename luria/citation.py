#!/usr/bin/env python3
"""The BibTeX entry in the README, derived from `CITATION.cff`.

Two places want the same facts. GitHub reads `CITATION.cff` and renders a
"Cite this repository" button from it; a reader of the README wants a block
they can paste. Writing both by hand is the drift DP-3 names — and a citation
is a bad thing to have two versions of, because the wrong one is the one that
ends up in somebody's bibliography.

So the `.cff` is the source and the README block is a projection, rewritten by
`luria index` and checked by `luria lint`, exactly as the badges are (ADR-018).

    python -m luria.citation            # print the markdown
    python -m luria.citation --write    # rewrite the region in README.md
    python -m luria.citation --check    # exit 1 if that region is stale

Deliberately not a `.cff` validator. The Citation File Format has a schema and
tooling of its own, and reimplementing a subset here would be a second
authority on somebody else's format. This reads the handful of keys BibTeX
needs and leaves the rest alone; a file it cannot read produces no region and
says why.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .config import current

OPEN = "<!-- luria:citation -->"
CLOSE = "<!-- /luria:citation -->"
REGION_RE = re.compile(re.escape(OPEN) + r".*?" + re.escape(CLOSE), re.S)

# CFF's own spelling on the left, BibTeX's on the right. Only the fields a
# software citation actually carries: a `@software` entry with a version and a
# publisher is not more useful than one without, and every extra mapping is a
# claim about a format this module does not own.
FIELDS = (("title", "title"), ("version", "version"),
          ("repository-code", "url"), ("url", "url"),
          ("license", "license"), ("doi", "doi"))


def path() -> Path:
    return current().root / "CITATION.cff"


def readme() -> Path:
    return current().root / "README.md"


def _author(entry: dict) -> str:
    """One author, in BibTeX's `Family, Given` order.

    A CFF author is either a person (`family-names`/`given-names`) or an
    entity (`name`). Both are legal and they format differently, so the entity
    form is braced to stop BibTeX splitting a company name into a surname."""
    family = str(entry.get("family-names", "")).strip()
    given = str(entry.get("given-names", "")).strip()
    if family and given:
        return f"{family}, {given}"
    if family:
        return family
    return "{" + str(entry.get("name", "")).strip() + "}"


def _key(data: dict, authors: list[str]) -> str:
    """`marx_luria` — the surname and the title, lowercased.

    Stable across releases on purpose: a citation key that moved with the
    version would break every bibliography that had already used it, which is
    the opposite of what a citation is for."""
    first = authors[0] if authors else ""
    surname = re.sub(r"[^a-z]", "", first.split(",")[0].lower()) or "anon"
    # The first WORD of the title, not a slice of it: slicing produced
    # `luriaprojectmemoryk`, which is a key nobody would type twice.
    words = re.findall(r"[a-z0-9]+", str(data.get("title", "")).lower())
    return f"{surname}_{words[0]}" if words else surname


def entry() -> str:
    """The BibTeX entry, or "" when there is no readable `CITATION.cff`."""
    src = path()
    if not src.exists():
        return ""
    try:
        data = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return ""
    if not isinstance(data, dict):
        return ""
    authors = [_author(a) for a in data.get("authors", []) if isinstance(a, dict)]
    authors = [a for a in authors if a not in ("", "{}")]

    rows: list[tuple[str, str]] = []
    if authors:
        rows.append(("author", " and ".join(authors)))
    seen = set()
    for cff_key, bib_key in FIELDS:
        value = str(data.get(cff_key, "")).strip()
        if value and bib_key not in seen:
            rows.append((bib_key, value))
            seen.add(bib_key)
    released = str(data.get("date-released", "")).strip()
    if released[:4].isdigit():
        rows.append(("year", released[:4]))
    if not rows:
        return ""

    width = max(len(k) for k, _ in rows)
    body = "\n".join(f"  {k.ljust(width)} = {{{v}}}," for k, v in rows)
    return f"@software{{{_key(data, authors)},\n{body}\n}}"


def region() -> str:
    text = entry()
    inner = f"```bibtex\n{text}\n```" if text else \
        "*No readable `CITATION.cff`; add one and run `luria index`.*"
    return "\n".join([OPEN, inner, CLOSE])


def rewrite(text: str) -> str:
    """The README with its citation region refreshed.

    Unchanged when there is no region — a project that has not opted in is not
    nagged, which is the same bargain the badge region makes."""
    return REGION_RE.sub(lambda _: region(), text, count=1)


def run(write: bool = False, check: bool = False) -> None:
    """Print, write, or check the README's citation region."""
    import sys
    target = readme()
    if not target.exists() or OPEN not in (text := target.read_text(encoding="utf-8")):
        print(f"luria citation: no {OPEN} region in README.md; nothing to do")
        return
    fresh = rewrite(text)
    if check:
        if fresh != text:
            print("luria citation: the README's citation region is stale — "
                  "run `luria index`", file=sys.stderr)
            raise SystemExit(1)
        return
    if write:
        target.write_text(fresh, encoding="utf-8")
        return
    print(region())


if __name__ == "__main__":
    import fire
    fire.Fire(run)
