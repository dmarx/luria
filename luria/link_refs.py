#!/usr/bin/env python3
"""Spell what the record left implicit: bare references become links, and
one-sided symmetric relations gain their back-reference.

    luria link                    # report what would change
    luria link --fix              # write it
    luria link --fix --links-only # links only, no relation completion

`--fix` repairs both because both are the same kind of mistake: a fact the
author stated once that the record needs written in a particular place. The
scanning and masking rules live in `doc_refs.py`, shared with `luria.lint` so
the linter and the fixer can never disagree; the relation completion lives in
`chains.py` beside the check that reports it. This is the one-shot migration
tool plus the escape hatch for "lint says I left a bare reference": run it
with `--fix` instead of hand-editing (ADR-005).

`--links-only` is that escape hatch's own escape hatch — the pre-completion
behaviour, for a run that must touch nothing but link text.
"""

from __future__ import annotations

from pathlib import Path

from . import chains, doc_refs
from .config import current


def linkify_files(paths: list[Path], fix: bool = False) -> tuple[int, list[Path]]:
    """Count the references PATHS would gain as links; --fix writes them.
    Returns the count and the files written (none without --fix)."""
    adrs, anchors = doc_refs.adr_paths(), doc_refs.dp_anchors()
    total = 0
    written: list[Path] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        new, count = doc_refs.linkify(text, path, adrs, anchors)
        if not count:
            continue
        total += count
        print(f"{current().rel(path)}: {count} reference(s)")
        if fix:
            path.write_text(new, encoding="utf-8")
            written.append(path)
    return total, written


def run(*paths: str, fix: bool = False, links_only: bool = False) -> None:
    """Rewrite bare references as links and complete symmetric relations —
    every doc, or just PATHS. Reports what would change; --fix writes it.
    --links-only skips the relation completion.

    Completion is whole-record: it reads every document of a chain's scheme
    to know what is missing, so PATHS narrows the linking only."""
    files = [Path(p).resolve() for p in paths] or doc_refs.doc_files()
    total, _ = linkify_files(files, fix)
    verb = "linked" if fix else "would link"
    print(f"{verb} {total} reference(s) in {len(files)} file(s)")
    if links_only:
        return
    filled = chains.complete(fix=fix)
    if filled:
        verb = "completed" if fix else "would complete"
        print(f"{verb} {len(filled)} back-reference(s) in "
              f"{len({str(c.path) for c in filled})} file(s)")


if __name__ == "__main__":
    import fire
    fire.Fire(run)
