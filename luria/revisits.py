# luria/revisits.py
"""A version bump that left `summary:` as it was (#326, ADR-tmp4osmu).

`summary:` is what `luria index` renders into the browse tables: the line a
reader meets before opening the document, so the most-read line in the
record. It is also the line an amendment never touches. Amending means
arguing with the body, and the summary sits above the `---` with the
metadata. In the record that measured it, twelve documents were amended in a
day and one summary was left saying what the document no longer argued: a
true sentence about a superseded state.

A hand-maintained restatement of the body is a cache with no invalidation.
Nothing mechanical can say whether a summary is still accurate, so this asks
only the mechanical part: the document changed enough to earn a version, and
this field was not touched. A warning, acknowledged at the site:

    # summary-ok: v7 — a recap of what the source measured; v7 narrowed scope
    summary: >-

The version is named because the acknowledgement answers one amendment, not
every future one: the next bump is a new question.

**The previous revision is git's, and only HEAD is asked.** The working tree
against HEAD is the amendment someone is making right now, which is when a
person can still fix it. Once committed, HEAD *is* the amendment and there
is nothing to compare, so the check is silent. For the same reason an
acknowledgement is called stale only while its document's bump is still
uncommitted: afterwards the check cannot see the question it answered, and
reporting it would make every acknowledgement churn the commit after it.
No repository, no HEAD, or an untracked file: no finding.
"""

from __future__ import annotations

import subprocess

from .adr_index import parse_frontmatter, read_document
from .config import current

SUMMARY_OK = "summary-ok"


def _changed_since_head() -> set[str] | None:
    """Every path (relative to the root) the working tree has changed against
    HEAD, from one `git diff`; None when git cannot answer."""
    cfg = current()
    try:
        out = subprocess.run(["git", "diff", "--name-only", "HEAD", "--"],
                             cwd=cfg.root, capture_output=True, text=True)
    except OSError:
        return None
    if out.returncode != 0:
        return None
    return set(out.stdout.splitlines())


def _at_head(rel: str) -> dict | None:
    """The frontmatter `rel` had at HEAD, or None for a new file."""
    try:
        out = subprocess.run(["git", "show", f"HEAD:{rel}"],
                             cwd=current().root, capture_output=True,
                             text=True)
    except OSError:
        return None
    if out.returncode != 0:
        return None
    meta, _ = parse_frontmatter(out.stdout)
    return meta or None


def _version(meta: dict) -> int:
    try:
        return int(meta.get("version", 1) or 1)
    except (TypeError, ValueError):
        return 1


def _line(text: str, field: str) -> int:
    for n, line in enumerate(text.split("\n"), 1):
        if line.startswith(f"{field}:"):
            return n
    return 1


def unrevisited_summaries() -> tuple[list[str], list[str]]:
    """Documents whose working-tree version is newer than HEAD's while their
    `summary:` reads the same, and `summary-ok:` directives that answered no
    such bump. Compared parsed, not as bytes: re-wrapping a folded summary
    is not revisiting it."""
    from . import directives
    cfg = current()
    changed = _changed_since_head()
    if not changed:
        return [], []
    flagged: list[str] = []
    stale: list[str] = []
    for scheme in cfg.schemes.values():
        for path in scheme.documents().values():
            rel = cfg.rel(path)
            if rel not in changed:
                continue
            before = _at_head(rel)
            if before is None:
                continue
            meta, _ = read_document(path)
            version = _version(meta)
            # Only an uncommitted bump is a question this check can see, so
            # only then can it say an acknowledgement answers nothing.
            if version <= _version(before):
                continue
            text = path.read_text(encoding="utf-8")
            found = directives.find(path, text, {SUMMARY_OK})
            summary = str(meta.get("summary") or "").strip()
            line = _line(text, "summary")
            used = False
            if summary and summary == str(before.get("summary") or "").strip():
                ack = next((d for d in found if d.covers(line)
                            and f"v{version}" in d.args), None)
                if ack is not None:
                    used = True
                else:
                    flagged.append(
                        f"{rel}:{line}: v{version} adds a history entry and "
                        f"`summary:` is unchanged — the index shows this "
                        f"field, so an amendment that did not revisit it may "
                        f"be showing the pre-amendment claim "
                        f"(`{SUMMARY_OK}: v{version}` to acknowledge)")
            for d in found:
                if used and f"v{version}" in d.args:
                    continue
                problem = directives.problems(d) or (
                    f"`{SUMMARY_OK}: {' '.join(d.args)}` answers no "
                    f"unrevisited summary — this amendment is v{version}")
                stale.append(f"{rel}:{d.line}: {problem}")
    return flagged, stale
