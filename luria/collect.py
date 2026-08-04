#!/usr/bin/env python3
"""Fragment collection — assembling a narrative view from per-contribution files.

A single long file that every substantial contribution appends to is a reliable
merge-conflict generator: two branches that touch nothing else in common still
collide at the bottom of it, and so does every rebase onto a main that has
collected since. That is [DP-2](../docs/design-principles.md#dp-2), and the fix
is structural — each contribution owns a fragment nobody else writes, and the
shared file becomes a VIEW assembled on a cadence.

This collector is deliberately not scriv-shaped: a narrative log has no
categories, no versions and no release cadence, so collection is "append these
bodies, oldest first, at the marker". A project whose changelog *does* want
categories can point that fragment directory at scriv instead; the two coexist
because the fragment convention is the contract, not the collector (ADR-002).

    luria collect                    # collect every fragment directory
    luria collect --dir record/changelog.d   # just one
    luria collect --commit           # collect and commit (CI mode)

Fragments are appended in the order they were COMMITTED (first commit that
added the file), not filename order, because a log reads chronologically and
branch-slug filenames sort arbitrarily. Uncommitted fragments sort last, by
filename — which is what you want locally, where the fragment you just wrote is
the newest thing.

That ordering is the weak point, and it is why a *journal* is not collected:
commit order is not authoring order, and a rebase can change it. A journal
carries the timestamp in the entry itself, so nothing has to be reconstructed
(ADR-020). This collector is right where the view is genuinely append-only —
the changelog — and wrong where the entries are dated observations.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from .config import current

TEMPLATE_NAME = "_template.md"
# Collected entries are inserted immediately BEFORE this marker, so the marker
# stays at the end of the file and each batch lands after the previous one.
# (scriv inserts AFTER its marker because a changelog is newest-first; a
# narrative log is oldest-first, so the anchor works the other way round.)
MARKER = "<!-- luria-insert-here -->"
# Recognised too, so a project already using scriv's or strata-g's marker
# doesn't have to rename anything to adopt this collector.
MARKERS = (MARKER, "<!-- devlog-insert-here -->", "<!-- scriv-insert-here -->")

# A fragment whose only content is HTML comments — the stub convention
# (ADR-002), meaning "deliberately nothing to say here". It exists so that
# "every contribution files a fragment" can stay an enforceable rule even when
# the honest answer is "nothing a reader would notice".
_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def is_stub(body: str) -> bool:
    """True when a fragment carries no prose — only comments and whitespace."""
    return not _COMMENT_RE.sub("", body).strip()


def find_marker(text: str) -> str | None:
    return next((m for m in MARKERS if m in text), None)


def collect(view_text: str, bodies: list[str]) -> str:
    """Insert `bodies` (in order) immediately before the insert marker.

    Pure — the CLI does the I/O. Raises if the marker is missing rather than
    guessing where the entries belong: silently appending to the wrong place in
    a long narrative is worse than failing (DP-1).
    """
    marker = find_marker(view_text)
    if marker is None:
        raise ValueError(
            f"no insert marker — add {MARKER} where collected entries belong")
    real = [b.strip() for b in bodies if not is_stub(b)]
    if not real:
        return view_text
    block = "\n\n".join(real)
    head, _, tail = view_text.partition(marker)
    return f"{head.rstrip()}\n\n{block}\n\n{marker}{tail}"


def _added_at(path: Path) -> tuple[int, str]:
    """Sort key: commit time the fragment was added, then filename.

    Uncommitted fragments get a sentinel that sorts last — locally, the entry
    you just wrote is the newest thing in the batch.
    """
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%ct", "-1", "--", str(path)],
            cwd=current().root, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return (int(out), path.name)
    except (subprocess.CalledProcessError, ValueError, OSError):
        pass
    return (sys.maxsize, path.name)


def fragment_paths(fragment_dir: Path) -> list[Path]:
    if not fragment_dir.is_dir():
        return []
    return sorted(
        (p for p in fragment_dir.glob("*.md") if p.name != TEMPLATE_NAME),
        key=_added_at,
    )


def collect_dir(name: str, target: Path) -> int:
    """Collect one fragment directory into its view. Returns the count."""
    cfg = current()
    paths = fragment_paths(cfg.root / name)
    if not paths:
        return 0
    view = cfg.root / target
    view.write_text(collect(view.read_text(), [p.read_text() for p in paths]))
    for p in paths:
        p.unlink()
    print(f"Collected {len(paths)} fragment(s) from {name} into {target}.")
    return len(paths)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", help="collect only this fragment directory")
    ap.add_argument("--commit", action="store_true", help="commit the result (CI mode)")
    args = ap.parse_args()

    cfg = current()
    wanted = {args.dir: cfg.fragments[args.dir]} if args.dir else cfg.fragments
    total = sum(collect_dir(name, target) for name, target in wanted.items())
    if not total:
        print("No fragments to collect.")
        return 0

    if args.commit:
        subprocess.run(["git", "add", "-A"], cwd=cfg.root, check=True)
        if subprocess.run(["git", "diff", "--staged", "--quiet"],
                          cwd=cfg.root).returncode == 0:
            print("Nothing to commit.")
            return 0
        subprocess.run(["git", "commit", "-m",
                        "docs: collect fragments [skip ci]"],
                       cwd=cfg.root, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
