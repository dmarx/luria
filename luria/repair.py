#!/usr/bin/env python3
"""`luria repair` — the source repairs, apart from the views (ADR-068).

    luria repair          # write every mechanical repair to the sources

A repair is a write to a *source* that the record already implies: a bare
code in prose becomes the link the lint would otherwise demand (ADR-005), a
journal entry filed without `created:` gets the timestamp its path already
asserts (#33), and a configuration reference this project no longer renders
is removed (ADR-059). None of it is a judgement — every repair here is one
the lint reports with this command as its remedy, so the two can never
disagree about what counts.

Repairs and views are two commands because they land in two places. A
source repair touches only the files a branch itself authored, so a
generation job commits it onto the branch, where the review reads it. A view
is a shared file every branch would rewrite, so it is committed on the
default branch only (`luria index`). Idempotence is load-bearing: the job
that pushes a repair runs again on the commit it pushed, and a second run
must find nothing to do.
"""

from __future__ import annotations

from pathlib import Path

from . import config_doc, doc_refs, journal, link_refs
from .config import current


def apply() -> list[Path]:
    """Every mechanical source repair, written: the files that changed."""
    cfg = current()
    changed: list[Path] = []
    _, linked = link_refs.linkify_files(doc_refs.doc_files(), fix=True)
    changed += linked
    for j in cfg.journals.values():
        for p in journal.populate_created(j):
            print(f"populated `created:` from the path in {cfg.rel(p)}")
            changed.append(p)
    # One-time cleanup for a project upgrading past ADR-059, which stopped
    # rendering the schema reference outside Luria's own tree.
    for p in config_doc.retire():
        print(f"removed {cfg.rel(p)} — the configuration reference now "
              "renders only where its schema lives; this project's own "
              f"record is described in {cfg.rel(cfg.record_doc)}")
        changed.append(p)
    return changed


def run() -> None:
    """Write every mechanical source repair: link bare references, populate
    `created:` from a journal entry's path, retire a stale configuration
    reference. Prints what changed; a second run changes nothing. Returns
    nothing — Fire would print a return value, and a list of paths is not
    the summary a caller wants."""
    changed = apply()
    print(f"repaired {len(changed)} file(s)")


if __name__ == "__main__":
    import fire
    fire.Fire(run)
