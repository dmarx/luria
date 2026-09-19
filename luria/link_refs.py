#!/usr/bin/env python3
"""Spell what the record left implicit: bare references become links, and
a relation held by one side gains its converse.

    luria link                    # report what would change
    luria link --fix              # write it
    luria link --fix --links-only # links only, no relation completion

`--fix` repairs both because both are the same kind of mistake: a fact the
author stated once that the record needs written in a particular place. The
scanning and masking rules live in `doc_refs.py`, shared with `luria.lint` so
the linter and the fixer can never disagree; the relation completion lives in
`relations.py` beside the check that reports it. This is the one-shot migration
tool plus the escape hatch for "lint says I left a bare reference": run it
with `--fix` instead of hand-editing (ADR-005).

`--links-only` is that escape hatch's own escape hatch — the pre-completion
behaviour, for a run that must touch nothing but link text.
"""

from __future__ import annotations

from pathlib import Path

from . import doc_refs, relations
from . import store
from .config import current


def linkify_files(paths: list[Path], fix: bool = False) -> tuple[int, list[Path]]:
    """Count the references PATHS would gain as links; --fix writes them.
    Returns the count and the files written (none without --fix)."""
    adrs, anchors = doc_refs.adr_paths(), doc_refs.dp_anchors()
    total = 0
    written: list[Path] = []
    for path in paths:
        text = store.read_text(path)
        new, count = doc_refs.linkify(text, path, adrs, anchors)
        # Two mechanical passes over the same text, reported as one number
        # because they are one question to the author: "is every reference in
        # this file spelled the way the config says?" The first spells bare
        # references; the second moves links that still point into a
        # document-rendered scheme's assembled view for a scheme that now
        # cites pages (`cite`, config.Scheme). A project that never changes
        # `cite` never sees the second one do anything.
        new, moved = doc_refs.retarget_view_citations(new, path)
        count += moved
        if not count:
            continue
        total += count
        print(f"{current().rel(path)}: {count} reference(s)")
        if fix:
            store.write_text(path, new)
            written.append(path)
    return total, written


def fix_anchors(fix: bool = False) -> int:
    """Rewrite every `<a name=>` something links to into an `<a id=>`.

    Whole-record rather than per-path, because it edits the file holding the
    ANCHOR: the link is spelled correctly and the thing it names cannot be
    found, so narrowing to the paths on the command line would repair the
    half of a pair the defect is not in (ADR-099).

    Which file that is cannot be read off the link's target. A stub is the
    authored part of a generated page, so a `<a name=>` written in one is
    reported against the VIEW it renders into — and the view is not the
    thing to edit, since the next build overwrites it. So this repairs every
    authored document carrying a reported fragment. Loose, and safe to be:
    `repair` only touches anchors some link actually named, and turning
    `name` into `id` is an improvement in any file it lands in.

    Returns the number of files changed — or that would change."""
    from . import anchors as anchors_mod
    cfg = current()
    docs = anchors_mod.documents()
    fragments = {f.fragment for f in anchors_mod.scan(
        docs, cfg.is_generated, cfg.link_base)}
    if not fragments:
        return 0
    changed = 0
    for path, text in docs.items():
        # Never a view: the next `luria index` overwrites it, so a repair
        # written there is a repair that vanishes. The generator emits `id`.
        if cfg.is_generated(path):
            continue
        fresh = anchors_mod.repair(text, fragments)
        if fresh == text:
            continue
        changed += 1
        if fix:
            store.write_text(path, fresh)
    return changed


def run(*paths: str, fix: bool = False, links_only: bool = False) -> None:
    """Rewrite bare references as links and complete declared relations —
    every doc, or just PATHS. Reports what would change; --fix writes it.
    --links-only skips the relation completion.

    Completion is whole-record: it reads every document of a scheme to know
    what is missing, so PATHS narrows the linking only."""
    files = [Path(p).resolve() for p in paths] or doc_refs.doc_files()
    total, _ = linkify_files(files, fix)
    verb = "linked" if fix else "would link"
    print(f"{verb} {total} reference(s) in {len(files)} file(s)")
    if repaired := fix_anchors(fix):
        did = "rewrote" if fix else "would rewrite"
        print(f"{did} a reachable anchor in {repaired} file(s) — "
              f"`<a name=>` is addressable on a real navigation and not in a "
              f"published site's router")
    if links_only:
        return
    repairs = relations.complete(fix=fix)
    if repairs:
        files = len({str(r.path) for r in repairs})
        added = sum(1 for r in repairs if r.op == "add")
        dropped = len(repairs) - added
        did = "wrote" if fix else "would write"
        parts = ([f"{did} {added} back-reference(s)"] if added else [])
        if dropped:
            parts.append(f"{'removed' if fix else 'would remove'} "
                         f"{dropped} stale one(s)")
        print(f"{' and '.join(parts)} in {files} file(s)")


if __name__ == "__main__":
    import fire
    fire.Fire(run)
