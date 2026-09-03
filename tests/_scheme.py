"""Build a scheme directory with documents of chosen statuses.

The tests that exercise retired-document reporting used to lean on whatever the
corpus happened to contain, which made them silently weaker as the corpus
changed — and impossible to write at all for a project (like this one) whose
every decision is Active. A fixture states what it needs.
"""
from pathlib import Path

from luria.config import current


def decision(root: Path, number: int, status: str, title: str = "A decision",
             summary: str = "", superseded_by=()) -> Path:
    """File a decision where the *current* config's ADR scheme reads them.

    Derived rather than hardcoded, because the conventional location moved
    once already (`docs/decisions` → `record/decisions.d`, ADR-021) and a
    fixture that spells the path writes documents the scheme can't see —
    every test downstream then passes on an empty corpus."""
    scheme = current().schemes["ADR"]
    assert root == current().root, "fixture root and LURIA_ROOT disagree"
    path = scheme.dir / f"ADR-{number:03d}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    # `Superseded — by X` in a test reads as the author means it and lands
    # in the two fields the record writes.
    from luria.statuses import parse
    parsed = parse(status)
    front = [f"status: {parsed.value}"]
    if superseded_by:
        front.append("superseded_by:")
        front += [f"- {c}" for c in ([superseded_by] if isinstance(superseded_by, str)
                                     else superseded_by)]
    if parsed.note:
        front.append(f"status_note: {parsed.note!r}")
    front += [f"title: {title!r}", "tags:", "- record", "date: '2026-01-01'"]
    if summary:
        front.append(f"summary: {summary!r}")
    path.write_text("---\n" + "\n".join(front) + "\n---\n\n"
                    f"# ADR-{number:03d}: {title}\n\nBody.\n")
    return path
