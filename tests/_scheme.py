"""Build a scheme directory with documents of chosen statuses.

The tests that exercise retired-document reporting used to lean on whatever the
corpus happened to contain, which made them silently weaker as the corpus
changed — and impossible to write at all for a project (like this one) whose
every decision is Active. A fixture states what it needs.
"""
from pathlib import Path


def decision(root: Path, number: int, status: str, title: str = "A decision",
             summary: str = "") -> Path:
    path = root / "docs" / "decisions" / f"ADR-{number:03d}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    front = [f"status: {status}", f"title: {title!r}",
             "tags:", "- record", "date: '2026-01-01'"]
    if summary:
        front.append(f"summary: {summary!r}")
    path.write_text("---\n" + "\n".join(front) + "\n---\n\n"
                    f"# ADR-{number:03d}: {title}\n\nBody.\n")
    return path
