#!/usr/bin/env python3
"""Fragment collection — assembling a narrative view from per-contribution files.

A single long file that every substantial contribution appends to is a reliable
merge-conflict generator: two branches that touch nothing else in common still
collide at the bottom of it, and so does every rebase onto a main that has
collected since. That is [DP-2](../docs/design-principles.md#dp-2), and the fix
is structural — each contribution owns a fragment nobody else writes, and the
shared file becomes a VIEW assembled on a cadence.

A fragment directory assembles in one of two shapes (ADR-028), declared in
`[luria.fragments]`:

- **append** (the default) — the narrative shape: bodies oldest-first,
  inserted before the marker, so the marker stays at the end and the log reads
  top-down.
- **changelog** — the release shape: each collection is one batch under a
  `## <date>` heading, inserted right after the marker so the newest batch
  reads first, fragments newest-first within it. A batch of only stubs emits
  nothing — no empty date heading to accumulate.

Neither shape has categories or versions; a fragment that wants `### Added` /
`### Fixed` sections simply carries them in its body, and the batch keeps them
per-contribution rather than merging across fragments the way scriv did.

    luria collect                    # collect every fragment directory
    luria collect --dir record/changelog.d   # just one
    luria collect --commit           # collect and commit (CI mode)

Fragments are ordered by when they were COMMITTED (first commit that added the
file), not filename order: a log reads chronologically, and a fragment's name
is not required to sort that way — `luria new` stamps timestamped names now,
but an explicitly `--name`d fragment still sorts arbitrarily, and commit time
is the truth either way. Uncommitted fragments sort last, by filename — which
is what you want locally, where the fragment you just wrote is the newest
thing.

That ordering is the weak point, and it is why a *journal* is not collected:
commit order is not authoring order, and a rebase can change it. A journal
carries the timestamp in the entry itself, so nothing has to be reconstructed
(ADR-020). This collector is right where the view is genuinely append-only —
the changelog — and wrong where the entries are dated observations.
"""

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


def collect(view_text: str, bodies: list[str], style: str = "append",
            date: str = "") -> str:
    """Assemble `bodies` (oldest first) into `view_text` at the insert marker,
    in the declared `style` (ADR-028).

    Pure — the CLI does the I/O. Raises if the marker is missing rather than
    guessing where the entries belong: silently appending to the wrong place in
    a long narrative is worse than failing (DP-1). A batch of only stubs
    changes nothing — in the changelog style that is what keeps an empty
    `## <date>` heading from accumulating per quiet collection.
    """
    marker = find_marker(view_text)
    if marker is None:
        raise ValueError(
            f"no insert marker — add {MARKER} where collected entries belong")
    real = [b.strip() for b in bodies if not is_stub(b)]
    if not real:
        return view_text
    head, _, tail = view_text.partition(marker)
    if style == "changelog":
        block = f"## {date}\n\n" + "\n\n".join(reversed(real))
        tail = tail.lstrip("\n")
        return f"{head}{marker}\n\n{block}" + ("\n\n" + tail if tail else "\n")
    block = "\n\n".join(real)
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


def collect_dir(name: str, fragment) -> int:
    """Collect one fragment directory into its view. Returns the count."""
    import datetime as dt
    cfg = current()
    paths = fragment_paths(cfg.root / name)
    if not paths:
        return 0
    view = cfg.root / fragment.target
    view.write_text(collect(view.read_text(encoding="utf-8"), [p.read_text(encoding="utf-8") for p in paths],
                            style=fragment.style,
                            date=dt.date.today().isoformat()), encoding="utf-8")
    for p in paths:
        p.unlink()
    print(f"Collected {len(paths)} fragment(s) from {name} "
          f"into {fragment.target}.")
    return len(paths)


def run(dir: str = None, commit: bool = False) -> None:
    """Assemble fragment directories into their views — all of them, or just
    --dir. --commit stages and commits the result (CI mode)."""
    cfg = current()
    wanted = {dir: cfg.fragments[dir]} if dir else cfg.fragments
    total = sum(collect_dir(name, frag) for name, frag in wanted.items())
    if not total:
        print("No fragments to collect.")
        return

    if commit:
        subprocess.run(["git", "add", "-A"], cwd=cfg.root, check=True)
        if subprocess.run(["git", "diff", "--staged", "--quiet"],
                          cwd=cfg.root).returncode == 0:
            print("Nothing to commit.")
            return
        subprocess.run(["git", "commit", "-m",
                        "docs: collect fragments [skip ci]"],
                       cwd=cfg.root, check=True)


if __name__ == "__main__":
    import fire
    fire.Fire(run)
