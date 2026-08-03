#!/usr/bin/env python3
"""Write the docs-status reports as markdown files (ADR-188).

    luria reports               # → build/doc-reports/
    luria reports --out DIR

`make lint-docs` prints one summary line per report, which is the right size for
a passing build's console. The *detail* — which file, which line, which
acknowledgement — only existed behind `luria ref-status` and `luria pending`,
which nobody runs, so a warning that fired on every PR was never actually read
by anyone.

These files are what CI uploads as an artifact. A reviewer can open the report
for the run, and diffing two runs' artifacts shows what a PR moved: whether it
added a reference to a `Deferred` decision, or paid one off.

Written as markdown rather than JSON on purpose — the audience is a person
skimming a PR, not a program. Nothing consumes them, so nothing breaks if the
shape changes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from . import adr_pending, doc_refs, ref_status
from .config import current


def _stamp(today: dt.date) -> str:
    return f"*Generated {today.isoformat()} — this file is built, not edited.*\n"


def reference_status(today: dt.date) -> str:
    docs = ref_status.load_docs()
    result = ref_status.scan(docs=docs)
    rows = ref_status.flagged(result, docs)
    excused = ref_status.acknowledged_count(result, docs)

    out = ["# Retired documents cited from current docs and code", "",
           _stamp(today), ""]
    out += [
        "A reference reads as \"this is why things are the way they are\", and "
        "that claim holds only while the referenced document is in force. None "
        "of this is a failure — citing a `Rejected` decision is often exactly "
        "right — so nothing here fails a build. What is worth knowing is which "
        "of these nobody has looked at.", "",
        f"**{len(rows)} retired document(s) cited without acknowledgement.** "
        f"{excused} reference(s) carry an `inactive-ok` annotation and are not "
        "listed below.", "",
        "To acknowledge one, put the reason where the reference is — "
        "`inactive-ok:` covers its line and the line below, `-block` the "
        "paragraph, `-file` the page:", "",
        "```",
        "<!-- inactive-ok: ADR-012 — why this citation is right -->",
        "```", "",
    ]

    if not rows:
        out.append("Nothing unacknowledged. ✅")
    for doc, loud, acked in rows:
        files = len({c.path for c in loud})
        tail = f" · {acked} acknowledged elsewhere" if acked else ""
        out += [f"## {doc.code} — {doc.status}", "",
                f"{doc.title}", "",
                f"{len(loud)} unacknowledged reference(s) in {files} file(s)"
                f"{tail}.", ""]
        for c in loud:
            out.append(f"- `{c}`")
        out.append("")

    stale = ref_status.stale_annotations(result, docs)
    for path in doc_refs.doc_files():
        stale += doc_refs.directive_problems(path, path.read_text())
    out += ["## Directives that no longer apply", ""]
    out += ([f"- {line}" for line in sorted(stale)] if stale
            else ["None. Every annotation still governs something. ✅"])
    out.append("")
    return "\n".join(out)


def pending_decisions(today: dt.date, stale_days: int) -> str:
    rows = adr_pending.pending()
    uncited = [r for r in rows if not r.cites]

    out = ["# ADRs awaiting a decision", "", _stamp(today), ""]
    out += [
        "`Proposed` and `Deferred` both describe an open question. Neither says "
        "*how long*, and that is the signal: a decision proposed last week is "
        "pending; the same one a year later was either overdue or settled in "
        "code and never written back.", "",
        adr_pending.headline(rows, today, stale_days).split(": ", 1)[-1] + ".",
        "",
    ]
    if rows:
        out += ["| Age | Status | ADR | Cited | Unack. | Title |",
                "|--:|---|---|--:|--:|---|"]
        for r in rows:
            age = r.age(today)
            mark = " ⚠️" if r.is_stale(today, stale_days) else ""
            label = f"{age} days{mark}" if age is not None else "undated"
            rel = current().rel(r.path)
            link = f"[ADR-{r.number:03d}](../../{rel})"
            out.append(f"| {label} | {r.status} | {link} | {r.cites} | "
                       f"{r.unacknowledged} | {r.title} |")
        out.append("")
    out += [
        "The citation count is the second axis, and it flips the priority: an "
        "old proposal nothing references is a stalled idea worth closing, while "
        "an old proposal many files cite is a decision the codebase has already "
        "made and hasn't written down.", "",
    ]
    out += ["This count and the reference-status report's will differ, and that "
            "is not an off-by-one. That report covers documents something "
            "actually **cites** and hasn't acknowledged; this one covers every "
            "**undecided** ADR. An ADR here is missing from there for exactly "
            "one of two reasons: nothing cites it, or every citation carries an "
            "`inactive-ok` annotation.", ""]
    if uncited:
        codes = ", ".join(f"ADR-{r.number:03d}" for r in uncited)
        one = len(uncited) == 1
        out += [f"**Cited nowhere at all** ({len(uncited)}): {codes} — "
                f"{'this is' if one else 'these are'} the cheapest to close, "
                "since nothing depends on the answer.", ""]
    return "\n".join(out)


def write(out_dir: Path, today: dt.date, stale_days: int) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        out_dir / "reference-status.md": reference_status(today),
        out_dir / "pending-decisions.md": pending_decisions(today, stale_days),
    }
    for path, text in files.items():
        path.write_text(text)
    return sorted(files)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--as-of", help="treat this ISO date as today")
    ap.add_argument("--stale-days", type=int, default=current().stale_days)
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.as_of) if args.as_of else dt.date.today()
    out = args.out or current().reports
    for path in write(out, today, args.stale_days):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
