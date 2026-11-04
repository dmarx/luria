#!/usr/bin/env python3
# luria/prune.py
"""`luria repair --prune_stale` — remove acknowledgements that excuse nothing (#385).

    luria repair --prune_stale

The default repair takes out only an `inactive-ok` code whose document is in
force (`ack.trim_settled`). It leaves a code that nothing in scope cites,
because the citation may have moved, and whether the directive should move
with it is a judgement. Leaving them is how a large record comes to carry
hundreds of directives that excuse nothing: each promotion and each edit
leaves one behind, and the lint's report of them stops being read.

This flag is a person opting in to that judgement for the whole tree at once.
It removes the codes in `inactive-ok`, `unresolved-ok` and `mention-ok`
directives that answer for nothing, and deletes a directive left naming
nothing. Removal changes no finding. A code that answers for no site
suppresses nothing, so taking it out surfaces nothing. The repair checks that
rather than trusting it: it re-scans after writing, and if any citation's
standing has changed it puts every file back and refuses (DP-6).

What counts as answering for nothing differs by kind:

- `inactive-ok` and `unresolved-ok` claim a state, so a code is idle when it
  excused no site in this scan (`Citation.excused_by`). That includes a code
  whose document is in force, `trim_settled`'s case, and a code redundant
  with an earlier directive that answers first.
- `mention-ok` claims nothing about state, and it must survive a status
  change that hands its site to another directive (ADR-105). So a code is
  idle only when no site in the directive's scope cites it at all.

It never touches a malformed directive, whose problem is already the finding,
nor an expired one, which the scan does not see, nor any other kind.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from . import ack, ref_status, writes

KINDS = (ref_status.DIRECTIVE, ref_status.DANGLING_DIRECTIVE,
         ref_status.MENTION_DIRECTIVE)


class PruneChangedFindings(RuntimeError):
    """Removing what excused nothing changed a finding, so nothing was kept."""


def _idle(ann: ref_status.Annotation, excused: set[str],
          cited: set[str]) -> frozenset[str]:
    """The codes in `ann` that answer for no site: see the module docstring."""
    if ann.kind == ref_status.MENTION_DIRECTIVE:
        return ann.codes - cited
    return ann.codes - excused


def _sites(result: ref_status.Scan):
    for pool in (result.cited, result.dangling):
        for sites in pool.values():
            yield from sites


def _loud(result: ref_status.Scan) -> Counter:
    """Every site no directive answers for, by file and code. By count and
    not by line, because deleting a directive's line moves the lines below
    it."""
    return Counter((c.path, c.code) for c in _sites(result)
                   if c.excused_by is None)


def plan(result: ref_status.Scan) -> dict[Path, list[tuple[
        ref_status.Annotation, frozenset[str]]]]:
    """For each file, the directives with idle codes and which codes they are."""
    excused: dict[int, set[str]] = {}
    in_file: dict[Path, list[ref_status.Citation]] = {}
    for c in _sites(result):
        in_file.setdefault(c.path, []).append(c)
        if c.excused_by is not None:
            excused.setdefault(id(c.excused_by), set()).add(c.code)
    by_file: dict[Path, list] = {}
    for ann in result.annotations:
        if ann.problem or ann.kind not in KINDS:
            continue
        cited = {c.code for c in in_file.get(ann.directive.path, ())
                 if c.code in ann.codes and ann.covers(c.line)}
        if idle := _idle(ann, excused.get(id(ann), set()), cited):
            by_file.setdefault(ann.directive.path, []).append((ann, idle))
    return by_file


def prune_stale() -> list[tuple[Path, list[str], bool]]:
    """Remove every idle code and every directive left naming nothing.

    Returns (file, codes removed, whether a whole directive went) per file
    changed. Raises `PruneChangedFindings`, with every file restored, if the
    re-scan finds a citation whose standing changed."""
    ref_status.forget_scan()
    docs = ref_status.load_docs()
    result = ref_status.scan(docs=docs)
    before = _loud(result)
    originals: dict[Path, str] = {}
    done = []
    for path, anns in sorted(plan(result).items()):
        text = original = path.read_text(encoding="utf-8")
        removed: list[str] = []
        whole = False
        # Bottom-up, so an edit never moves an offset still to be used.
        for ann, idle in sorted(anns, key=lambda a: -a[0].directive.span[0]):
            whole |= idle == ann.codes
            text = ack._trim_one(text, ann, set(idle))
            removed += idle
        if text != original:
            originals[path] = original
            writes.write_text(path, text)
            done.append((path, sorted(set(removed)), whole))
    if not originals:
        return done
    ref_status.forget_scan()
    after = _loud(ref_status.scan(docs=ref_status.load_docs()))
    if after != before:
        for path, text in originals.items():
            writes.write_text(path, text)
        ref_status.forget_scan()
        changed = sorted(f"{ref_status._rel(p)} {code}"
                         for p, code in (after - before) + (before - after))
        raise PruneChangedFindings(
            "removing acknowledgements that excused nothing changed a "
            f"finding, so every file was restored: {', '.join(changed)}")
    return done
