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

from . import config_doc, doc_refs, journal, link_refs, statuses
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
    # The same repair, for a scheme document's identity (#219): the filename
    # already asserts the number, so writing it into the frontmatter states
    # what the record implies. This is how a project migrates onto `uid:`
    # without anyone typing one — and why the field can be introduced without
    # a `luria upgrade` of its own.
    for s in cfg.schemes.values():
        for p in populate_uids(s):
            print(f"populated `uid:` from the path in {cfg.rel(p)}")
            changed.append(p)
    # A note still riding in `status:` moves to `status_note:`, and an
    # old-form `by CODE` note becomes `superseded_by:` — the same repair: the
    # file states the facts, and now says so in the fields that carry them
    # (ADR-072, ADR-071).
    for s in cfg.schemes.values():
        for p in statuses.populate(s):
            print(f"brought the status fields up to date in {cfg.rel(p)}")
            changed.append(p)
    # One-time cleanup for a project upgrading past ADR-059, which stopped
    # rendering the schema reference outside Luria's own tree.
    for p in config_doc.retire():
        print(f"removed {cfg.rel(p)} — the configuration reference now "
              "renders only where its schema lives; this project's own "
              f"record is described in {cfg.rel(cfg.record_doc)}")
        changed.append(p)
    return changed


def populate_uids(scheme) -> list[Path]:
    """Write `uid:` into every document of `scheme` that lacks one, from the
    number its filename already carries.

    A temporary document is skipped: it has no number yet by design, and
    `luria concretize` writes the field at the moment it assigns one
    (ADR-049). Idempotent, like every repair here — a second run finds the
    field present and does nothing."""
    from . import config as config_mod
    from .new import write_uid
    done: list[Path] = []
    for path in sorted(scheme.dir.glob("*.md")):
        if scheme.temp_of(path) is not None:
            continue
        number = scheme.number_of(path)
        if number is None or config_mod._declared_uid(path) is not None:
            continue
        text = path.read_text(encoding="utf-8")
        written = write_uid(text, number)
        if written != text:
            path.write_text(written, encoding="utf-8")
            done.append(path)
    return done


def run() -> None:
    """Write every mechanical source repair: link bare references, populate
    `created:` from a journal entry's path, move a note out of `status:`
    into `status_note:` and `superseded_by:`, retire a stale configuration
    reference. Prints what changed; a second run changes nothing. Returns
    nothing — Fire would print a return value, and a list of paths is not
    the summary a caller wants."""
    changed = apply()
    print(f"repaired {len(changed)} file(s)")


if __name__ == "__main__":
    import fire
    fire.Fire(run)
