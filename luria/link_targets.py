"""Relative link targets, checked from where the prose renders.

A markdown link written in record prose is followed from the page it *lands
on*, not the file it was typed in. A journal entry lives in
`record/reading.d/2026/08/16/` and renders into `docs/reading/2026-08-16.md`;
those are five directories apart, so the depth that looks right beside the
source is wrong in the view, and the depth that is right in the view looks
wrong beside the source. There is no spelling that satisfies both, which is
exactly why the third ground rule says never to hand-write one.

`link_base` already owns that frame — `luria link --fix` cannot write a target
without it. What was missing is anyone checking the targets the fixer did not
write. The reference checks are about *codes*: that `CLM-007` names a record
that exists. A hand-written path wrapped around a resolvable code satisfies
every one of them while pointing at nothing, so a project could hand-write a
hundred broken targets and lint clean the whole way — which is what prompted
this (#100).

Reported rather than failed by default (ADR-035): a wrong path is always
wrong, but it is not mechanically fixable the way a bare code is. The fixer
owns codes; an arbitrary path is a typo only the author can resolve.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import unquote

from .config import current

TARGET_OK = "target-ok"

LINK_RE = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)\)")

# Anything that is not a path this repo can check: a URL scheme, a
# protocol-relative host, a root-anchored path (whose meaning depends on where
# the site is served from), or a link to a heading in the same page.
NOT_A_LOCAL_PATH = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]*:|//|/|#)")

# A target carrying a regex or format metacharacter is a *pattern* — a URL
# template's `{1}`, a uid regex's `(\d{4,5})` — and link-shaped by accident.
# Cheaper and steadier than deciding whether the surrounding lines are an
# indented code block, which markdown makes ambiguous inside a list.
PATTERN_CHARS = set("{}\\|()[]*?<>")


def _local_path(target: str) -> str | None:
    """The on-disk path a link target names, or None when it names something
    else. The fragment and query are dropped: a heading that does not exist is
    a different (and much noisier) check than a file that does not."""
    if NOT_A_LOCAL_PATH.match(target) or PATTERN_CHARS & set(target):
        return None
    path = unquote(target.split("#", 1)[0].split("?", 1)[0])
    return path or None


def broken(files: list[Path] | None = None) -> tuple[list[str], list[str]]:
    """Relative link targets that resolve to nothing, and the `target-ok:`
    directives that no longer acknowledge anything.

    Deliberate cases exist — a link into a build output that is generated but
    not committed, a path a downstream consumer creates — so each one is either
    acknowledged or reported, never silent and never an error (ADR-035).
    """
    from . import directives, doc_refs
    cfg = current()
    flagged: list[str] = []
    stale: list[str] = []
    for path in files if files is not None else doc_refs.doc_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        quoted = doc_refs.code_spans(text)
        base = cfg.link_base(path)
        found = directives.find(path, text, {TARGET_OK})
        used: set[tuple[int, str]] = set()
        for m in LINK_RE.finditer(text):
            if any(a <= m.start() < b for a, b in quoted):
                continue                      # a quotation, not a citation
            target = m.group(1)
            rel = _local_path(target)
            # Normalized textually, not by `Path.exists()` on the raw join: a
            # view directory need not exist yet (`luria index` creates it), and
            # `..` through a missing directory fails on the filesystem while
            # resolving fine for a reader. Text is also what a renderer does.
            if rel is None or Path(os.path.normpath(base / rel)).exists():
                continue
            line = text.count("\n", 0, m.start()) + 1
            ack = next((d for d in found
                        if d.covers(line) and target in d.args), None)
            if ack is not None:
                used.add((ack.line, target))
                continue
            flagged.append(
                f"{cfg.rel(path)}:{line}: {target} resolves to nothing from "
                f"{cfg.rel(base)}/, where this prose renders "
                f"(`luria link --fix` writes code targets; this one is by hand)")
        for d in found:
            problem = directives.problems(d)
            for arg in d.args:
                if (d.line, arg) not in used:
                    problem = problem or f"`{TARGET_OK}: {arg}` matches no link"
                    stale.append(f"{cfg.rel(path)}:{d.line}: {problem}")
                    break
    return flagged, stale
