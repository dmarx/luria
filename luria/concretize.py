#!/usr/bin/env python3
"""`luria concretize` — assign real numbers to temporary codes (ADR-049).

    luria concretize            # rename, rewrite, alias, regenerate
    luria concretize --check    # exit 1 naming any temporary code; no writes

A merge-allocated scheme's documents arrive from their branches under
temporary codes (`ADR-tmp47fje`) precisely so that no branch claims a place in
the sequence. This command is the other half of that bargain, and it runs at
the serialization point — a merge queue, the job that lands PRs on the trunk
— because that is the only place "the next free number" is a fact rather
than a race.

For each scheme's temporary documents, oldest first by when they were
committed (the same ordering the changelog collector trusts, for the same
reason: a filename is not required to sort chronologically):

1. the next free number is assigned and the file renamed to the numeric
   shape (`ADR-123.md`);
2. every occurrence of the temporary code in current files is rewritten —
   which covers link labels and link targets in one pass, since the target
   is the code plus `.md`;
3. the temporary code is recorded in the document's `formerly:` frontmatter,
   which the resolver honours forever — a citation the rewrite cannot reach
   (a PR thread, an immutable commit message, another repository's
   `LU-`-prefixed reference, a branch cut before concretization) resolves to
   the concretized document instead of going dead (ADR-014's contract,
   extended through the rename).

The sweep is **full — history included** (ADR-040's second commitment, and
ADR-049 adopted it deliberately): a temporary code is temporary relative to
the record, so wherever the tree can be rewritten to the canonical ID, it
is — journals and the collected changelog too. After a run, exactly one
spelling of each code exists in the tree; the alias exists for the
citations that live *outside* it. Immutability of what was actually written
is git's guarantee, not the working tree's job.

`--check` is the trunk's guard. A temporary code on the default branch is
always wrong and mechanically fixable — run this command — so it fails
outright, which is ADR-035's bar for a check that may fail a build.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from . import doc_refs
from .collect import _added_at
from .config import current


def pending() -> list[tuple[object, str, Path]]:
    """(scheme, tail, path) for every temporary document, in the order their
    numbers should be assigned: scheme by config order, then commit time."""
    out = []
    for scheme in current().schemes.values():
        temps = sorted(scheme.temp_documents().items(),
                       key=lambda item: _added_at(item[1]))
        out += [(scheme, tail, path) for tail, path in temps]
    return out


def _record_alias(text: str, old_code: str) -> str:
    """`old_code` appended to the document's `formerly:` frontmatter — created
    after `status:` when the field doesn't exist yet, extended in place when
    it does. Runs after the tree-wide rewrite, so the alias is the only place
    the temporary code still appears."""
    if re.search(r"^formerly:", text, flags=re.MULTILINE):
        return re.sub(r"^(formerly:(?:\n- .*)*)", rf"\1\n- {old_code}", text,
                      count=1, flags=re.MULTILINE)
    return re.sub(r"^(status:.*)$", rf"\1\nformerly:\n- {old_code}", text,
                  count=1, flags=re.MULTILINE)


def _rewrite_files(renames: list[tuple[str, str]]) -> int:
    """Every occurrence of each old code, in every file the record scans —
    history included, per ADR-040's second commitment: a spelling left behind
    in a journal is not preserved, it is a second name for the same document
    that grep and readers must both know. The collected changelog and the
    journal entries ride in `doc_files`; generated views are absent from it
    and the caller regenerates them."""
    cfg = current()
    files = list(doc_refs.doc_files())
    for pattern in cfg.code_globs:
        files += [p for p in cfg.root.glob(pattern) if p.is_file()]
    touched = 0
    seen = set()
    for path in files:
        if path in seen:
            continue
        seen.add(path)
        text = new = path.read_text()
        for old, target in renames:
            new = new.replace(old, target)
        if new != text:
            path.write_text(new)
            touched += 1
    return touched


def run(check: bool = False) -> None:
    """Concretize every temporary code — or, with --check, exit 1 naming the
    ones that exist (the trunk guard: a temp code on main means this command
    didn't run where merges serialize)."""
    cfg = current()
    todo = pending()
    if check:
        if todo:
            print(f"luria concretize: {len(todo)} temporary code(s) awaiting "
                  "concretization", file=sys.stderr)
            for scheme, tail, path in todo:
                print(f"  {scheme.prefix}-{tail}  {cfg.rel(path)}",
                      file=sys.stderr)
            raise SystemExit(1)
        print("luria concretize: no temporary codes")
        return
    if not todo:
        print("luria concretize: nothing to do")
        return

    renames: list[tuple[str, str, Path, Path]] = []
    next_free = {s.prefix: max(s.documents(), default=0) + 1
                 for s, _, _ in todo}
    for scheme, tail, path in todo:
        number = next_free[scheme.prefix]
        next_free[scheme.prefix] = number + 1
        renames.append((f"{scheme.prefix}-{tail}", scheme.code(number),
                        path, scheme.dir / scheme.filename(number)))

    _rewrite_files([(old, new) for old, new, _, _ in renames])
    for old, new, src, dest in renames:
        # The tree-wide pass already rewrote this document's own heading and
        # cross-references; what remains is its identity — the filename —
        # and the alias that keeps the old name resolving forever.
        dest.write_text(_record_alias(src.read_text(), old))
        src.unlink()
        print(f"{old} → {new}")

    # The views re-derive from the renamed sources, so the index, tag pages
    # and any assembled document pick up the new codes in the same run.
    from . import adr_index
    adr_index.run()


if __name__ == "__main__":
    import fire
    fire.Fire(run)
