#!/usr/bin/env python3
"""`luria ack` — write an acknowledgement directive from the scan (#308).

    luria ack                                  # what can be acknowledged
    luria ack ADR-012 --reason "the decision this page replaced"
    luria ack ADR-012 --reason "..." --scope file
    luria ack ADR-012 --reason "..." --until 2026-12-01

An acknowledgement is the record's answer to a check that is right to see
something a person is right to leave: `inactive-ok:` for a deliberate citation
of a retired document, `unresolved-ok:` for a code that names nothing on
purpose. They are the escape hatch under `lint.fail_on`, so they are also the
one place where a mistake is silent — a directive naming a code that does not
exist suppresses nothing and reports nothing.

**The code comes from the scan, never from a person.** That is the whole
point, and it is not the typing it saves. Four acknowledgement failures in one
day of filing work downstream were all transcription errors between a report
that had the right answer and a file edited by hand: a directive vouching for
a document that was no longer retired, one naming a code that did not exist (a
`LIT` tail crossed with a `THEORY` prefix), one stale on arrival over an
`Active` document, and one citing a number before it was allocated. Written
from `Scan`, the first three are impossible and the fourth has nowhere to
occur.

**The reason is the one thing a person supplies**, and the command refuses
without it. A generated reason vouches for nothing, which is the failure the
directives exist to prevent — so there is no `--fix` that writes these in
bulk, and `luria repair` does not do it. `repair`'s contract is that a second
run changes nothing, which a judgement can never satisfy.
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import directives, ref_status
from .config import current

# `<!--` for prose, `#` for everything else. Crude and deliberate: a directive
# has to OPEN its comment, so the only question is which marker opens one here,
# and the two shapes cover every file a record scans. A `.js` or `.rs` file
# takes `#` wrongly — but `code.globs` naming one is a project whose config
# says so, and this fails visibly rather than writing a directive that parses
# as nothing.
def _comment(path: Path, body: str) -> str:
    if path.suffix.lower() in (".md", ".markdown", ".html"):
        return f"<!-- {body} -->"
    return f"# {body}"


def _indent_of(line: str) -> str:
    return line[:len(line) - len(line.lstrip())]


def _file_scope_line(rows: list[str]) -> int:
    """Where a `-file` directive goes: the top, but below frontmatter.

    A `<!-- -->` above the opening `---` is not a comment in a document with
    frontmatter, it is the document's first line and the frontmatter is gone.
    The scope is the whole file either way, so the directive loses nothing by
    sitting one block lower."""
    if not rows or rows[0].rstrip("\n") != "---":
        return 1
    for i, row in enumerate(rows[1:], start=2):
        if row.rstrip("\n") == "---":
            return i + 1
    return 1                    # an unterminated fence: treat it as prose


def plan(code: str, docs=None, result=None) -> tuple[str, list[ref_status.Citation], str]:
    """(directive name, unacknowledged sites, why not) for one code.

    The refusal is the feature. Three states have no acknowledgement to write
    and each fails differently if one is written anyway: a document in force
    (the directive is a `stale-directives` finding the moment it lands), a code
    with no unexcused citation (it governs nothing), and a code already
    covered (a second one is noise). Naming which is what turns a silent no-op
    into a sentence."""
    docs = ref_status.load_docs() if docs is None else docs
    result = ref_status.scan(docs=docs) if result is None else result

    if code in result.cited:
        doc = docs[code]
        if doc.active:
            return "", [], (f"{code} is {doc.status} — a directive over a "
                            f"document in force acknowledges nothing, and is "
                            f"itself a `stale-directives` finding")
        name, sites = ref_status.DIRECTIVE, result.cited[code]
    elif code in result.dangling:
        name, sites = ref_status.DANGLING_DIRECTIVE, result.dangling[code]
    else:
        return "", [], (f"{code} is not cited anywhere this record scans — "
                        f"nothing to acknowledge")

    loud = [c for c in sites if c.excused_by is None]
    if not loud:
        return "", [], (f"every citation of {code} is already acknowledged "
                        f"({len(sites)} site(s))")
    return name, loud, ""


def write(code: str, reason: str, scope: str = "line",
          until: str = "") -> list[str]:
    """Write the directive at each unacknowledged site. Returns what it wrote.

    `line` scope puts one directive directly above each citation, which is
    where an acknowledgement belongs: it is a claim about *that* sentence.
    `file` writes one per file instead, at the top, for a page whose whole
    subject is the retired thing — the blunt tool, and the report counts it as
    such."""
    if scope not in ("line", "file"):
        raise SystemExit(f"luria ack: unknown scope {scope!r} — "
                         f"write `line` or `file`")
    name, sites, refusal = plan(code)
    if refusal:
        raise SystemExit(f"luria ack: {refusal}")

    cfg = current()
    suffix = "-file" if scope == "file" else ""
    when = f" until {until}" if until else ""
    body = f"{name}{suffix}: {code}{when} — {reason}"
    written = []
    # Grouped by file and applied bottom-up, so an insertion never moves a
    # line number the scan already reported.
    by_file: dict[Path, list[int]] = {}
    for c in sites:
        by_file.setdefault(c.path, []).append(c.line)
    for path, lines in by_file.items():
        text = path.read_text(encoding="utf-8")
        rows = text.splitlines(keepends=True)
        at = ([_file_scope_line(rows)] if scope == "file"
              else sorted(set(lines), reverse=True))
        for line in at:
            indent = (_indent_of(rows[line - 1])
                      if scope == "line" and line <= len(rows) else "")
            rows.insert(line - 1, indent + _comment(path, body) + "\n")
            written.append(f"{cfg.rel(path)}:{line}")
        path.write_text("".join(rows), encoding="utf-8")
    return written


def _survey() -> None:
    """Every row an acknowledgement could take, with its sites — the report
    this command exists to be written from, printed where it is about to be
    used rather than in a file somebody has to go and open."""
    docs = ref_status.load_docs()
    result = ref_status.scan(docs=docs)
    cfg = current()
    rows = 0
    for label, codes in (
            ("cited but not in force", [d.code for d, _, _ in
                                        ref_status.flagged(result, docs)]),
            ("resolves to no document", [c for c, _, _ in
                                         ref_status.dangling(result, docs)]),
            ("not minted here", [c for c, _, _ in
                                 ref_status.dangling(result, docs, temps=True)])):
        for code in codes:
            _, sites, _ = plan(code, docs, result)
            rows += 1
            print(f"{code} — {label}, {len(sites)} unacknowledged site(s)")
            for c in sites:
                print(f"    {cfg.rel(c.path)}:{c.line}")
    if not rows:
        print("nothing to acknowledge — every citation is accounted for")
    else:
        print("\nluria ack <CODE> --reason \"...\" writes the directive at "
              "each site above.", file=sys.stderr)


def run(code: str = "", reason: str = "", scope: str = "line",
        until: str = "") -> None:
    """Write an acknowledgement directive for `code` at every site the scan
    reports unacknowledged, with `reason` as its justification.

    Called with no code, prints what could be acknowledged and writes nothing.
    `scope` is `line` (one directive per citation, the default) or `file` (one
    per file). `until` gives the directive an expiry, after which every check
    behaves as though it were never written."""
    if not code:
        _survey()
        return
    if not reason:
        raise SystemExit(
            "luria ack: --reason is required. The code is read from the scan; "
            "the reason is the part only you can supply, and a directive "
            "without one vouches for nothing.")
    written = write(code, reason, scope, until)
    for where in written:
        print(f"acknowledged {code} at {where}")
    print(f"wrote {len(written)} directive(s)")


if __name__ == "__main__":
    import fire
    fire.Fire(run)
