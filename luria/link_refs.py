#!/usr/bin/env python3
"""Rewrite bare ADR / design-principle / issue references in the docs as links.

    luria link            # report what would change
    luria link --fix      # write it

The scanning and masking rules live in `doc_refs.py`, shared with
`luria.lint` so the linter and the fixer can never disagree. This is
the one-shot migration tool plus the escape hatch for "lint says I left a bare
reference": run it with `--fix` instead of hand-editing (ADR-005).
"""

from __future__ import annotations

from pathlib import Path

from . import doc_refs
from .config import current


def run(*paths: str, fix: bool = False) -> None:
    """Rewrite bare references as links — every doc, or just PATHS.
    Reports what would change; --fix writes it."""
    files = [Path(p).resolve() for p in paths] or doc_refs.doc_files()
    adrs, anchors = doc_refs.adr_paths(), doc_refs.dp_anchors()

    total = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        new, count = doc_refs.linkify(text, path, adrs, anchors)
        if not count:
            continue
        total += count
        print(f"{current().rel(path)}: {count} reference(s)")
        if fix:
            path.write_text(new, encoding="utf-8")

    verb = "linked" if fix else "would link"
    print(f"{verb} {total} reference(s) in {len(files)} file(s)")


if __name__ == "__main__":
    import fire
    fire.Fire(run)
