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

import argparse
from pathlib import Path

from . import doc_refs
from .config import current


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fix", action="store_true", help="write the rewrites")
    ap.add_argument("paths", nargs="*", help="limit to these files")
    args = ap.parse_args()

    files = [Path(p).resolve() for p in args.paths] or doc_refs.doc_files()
    adrs, anchors = doc_refs.adr_paths(), doc_refs.dp_anchors()

    total = 0
    for path in files:
        text = path.read_text()
        new, count = doc_refs.linkify(text, path, adrs, anchors)
        if not count:
            continue
        total += count
        print(f"{current().rel(path)}: {count} reference(s)")
        if args.fix:
            path.write_text(new)

    verb = "linked" if args.fix else "would link"
    print(f"{verb} {total} reference(s) in {len(files)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
