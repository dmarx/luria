#!/usr/bin/env python3
"""Report references to retired documents, and the annotations that excuse them.

    luria ref-status            # grouped report, 5 sites per document
    luria ref-status --all      # every site

A reference to another document reads as "this is why things are the way they
are". That claim is only true while the referenced document is in force. A
`Deferred` ADR cited from live plugin code, or a `Proposed` one cited as settled
architecture, is the same class of drift ADR-123 found in the status field
itself — except nothing was looking for it.

These are **warnings, not errors**. Citing a retired document is often exactly
right: a `Rejected` ADR exists to be pointed at, and a `Superseded` one is the
history its successor refers back to. What's wrong is doing it *unknowingly*.

Acknowledging a deliberate reference
------------------------------------
Write the reference scheme's full code, never a bare number, inside a comment:

    <!-- inactive-ok: ADR-012 — the decision this ADR replaced -->
    // inactive-ok: ADR-028 — proposed, but this is what shipped

`inactive-ok:` is **line-scoped**: it covers its own line and the line below, so
it can sit above the sentence it excuses. `inactive-ok-file:` is
**document-scoped** and covers the whole file:

    <!-- inactive-ok-file: ADR-012, ADR-020 — this page is supersession history -->

Both are counted, never silent: the report says how many references an
annotation suppressed, and flags annotations that no longer apply (the document
went Active, or the reference they excused is gone).

Reference schemes
-----------------
`SCHEMES` maps a code prefix to how its documents are found and what "in force"
means for them. ADRs are the only scheme this repo has, but nothing above this
line is ADR-specific — the annotation vocabulary says `inactive-ok`, not
`adr-ok`, and takes a prefixed code, so a second scheme (an RFC directory, a
spec index) is a `Scheme` entry rather than a fork of this file.

Scope: the docs that state current guidance, plus the code. The dated records —
`CHANGELOG.md`, `docs/devlog.md` and the fragment directories they are collected
from — are excluded: "ADR-NNN landed" in a July entry is a true statement about
July, and would be permanent, unactionable noise. A document citing itself is
excluded for the same reason (every ADR's own title names it).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import adr_index as builder
from . import directives, doc_refs
from .config import current

DEFAULT_SITES = 5


def _blank(text: str, spans: list[tuple[int, int]]) -> str:
    chars = list(text)
    for start, end in spans:
        for i in range(max(0, start), min(len(chars), end)):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def _rel(path: Path) -> str:
    """Repo-relative when it can be; absolute otherwise (test fixtures)."""
    return current().rel(path)


# ── Reference schemes ────────────────────────────────────────────────────


@dataclass(frozen=True)
class Doc:
    """A referable document: its code, its status, and whether that's in force."""
    code: str
    status: str
    title: str
    path: Path
    active: bool


def _load_scheme(scheme) -> dict[str, Doc]:
    """Every document in one scheme's directory, with its status.

    Frontmatter-with-a-`status:` is the only contract a scheme has to meet, so
    a second scheme is a directory and a prefix — not a code change (ADR-006)."""
    docs: dict[str, Doc] = {}
    for path in sorted(scheme.dir.glob("*.md")):
        m = re.match(rf"{scheme.prefix.lower()}-(\d+)", path.name)
        if not m:
            continue
        meta, body = builder.parse_frontmatter(path.read_text())
        status = re.split(r"\s+—\s+", str(meta.get("status", "")).strip(),
                          maxsplit=1)[0]
        first = next((ln for ln in body.splitlines() if ln.startswith("#")), "")
        title = builder.TITLE_RE.sub("", first).strip()
        code = scheme.code(m.group(1))
        docs[code] = Doc(code, status, title, path, status == scheme.active)
    return docs


def schemes() -> dict:
    return current().schemes


def load_docs() -> dict[str, Doc]:
    out: dict[str, Doc] = {}
    for scheme in schemes().values():
        out.update(_load_scheme(scheme))
    return out


# ── Annotations ──────────────────────────────────────────────────────────

# Full codes only — a bare number is rejected. It reads as an ADR here and as
# something else in the next repo that borrows this; requiring the prefix is
# what lets one vocabulary serve more than one reference scheme.
CODE_RE = re.compile(r"\b([A-Za-z]{2,10})-(\d{1,4})\b")
BARE_NUMBER_RE = re.compile(r"(?<![\w-])\d{1,4}(?![\w-])")
DIRECTIVE = "inactive-ok"


@dataclass(frozen=True)
class Annotation:
    directive: directives.Directive
    codes: frozenset[str]
    problem: str | None = None        # malformed: what's wrong with it

    def __str__(self) -> str:
        return f"{_rel(self.directive.path)}:{self.directive.line}"

    @property
    def scope(self) -> str:
        return self.directive.scope

    def covers(self, line: int) -> bool:
        return self.directive.covers(line)


def annotations(path: Path, text: str, known: set[str]) -> list[Annotation]:
    """Every `inactive-ok` annotation in `path`, malformed ones included — they
    are reported rather than dropped, because an annotation that silently does
    nothing is worse than no annotation."""
    found = []
    for d in directives.find(path, text, {DIRECTIVE}):
        spec = " ".join(d.args)
        codes = {f"{p.upper()}-{int(n):03d}" for p, n in CODE_RE.findall(spec)}
        problem = None
        if not codes:
            problem = "names no document code"
        elif BARE_NUMBER_RE.search(CODE_RE.sub("", spec)):
            example = f"{next(iter(schemes()), 'ADR')}-012"
            problem = f"has a bare number — write the full code (e.g. {example})"
        else:
            unknown = sorted(c for c in codes if c not in known)
            if unknown:
                problem = f"names unknown document(s): {', '.join(unknown)}"
        found.append(Annotation(d, frozenset(codes), problem))
    return found


# ── Scanning ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Citation:
    path: Path
    line: int
    code: str
    excused_by: Annotation | None = field(default=None, compare=False)

    def __str__(self) -> str:
        return f"{_rel(self.path)}:{self.line}"


@dataclass
class Scan:
    cited: dict[str, list[Citation]] = field(default_factory=dict)
    annotations: list[Annotation] = field(default_factory=list)

    def used(self, ann: Annotation) -> bool:
        return any(c.excused_by is ann
                   for sites in self.cited.values() for c in sites)


def scanned_files() -> list[Path]:
    """Current-guidance docs + code. Order is stable so the report is."""
    cfg = current()
    historical_dirs = {cfg.root / d for d in cfg.fragments}
    docs = [p for p in doc_refs.doc_files()
            if p not in cfg.historical and p.parent not in historical_dirs]
    code: list[Path] = []
    for pattern in cfg.code_globs:
        code += [p for p in cfg.root.glob(pattern) if p.is_file()]
    return docs + sorted(set(code))


def scan(files: list[Path] | None = None, docs: dict[str, Doc] | None = None) -> Scan:
    """Every citation and every annotation, with each citation pointing at the
    annotation that excuses it (if any).

    Deliberately unmasked, unlike the link lint: a reference in a code comment
    or inside a fenced block is still a claim about why the code is the way it
    is, which is the thing being checked."""
    docs = load_docs() if docs is None else docs
    known = set(docs)
    own = {doc.path: doc.code for doc in docs.values()}
    result = Scan()
    for path in files if files is not None else scanned_files():
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        anns = annotations(path, text, known)
        result.annotations += anns
        usable = [a for a in anns if not a.problem]
        # Naming a code in a directive is not citing it — true of a live
        # annotation and of an example of one alike, which is why this matches
        # the *shape* rather than the parsed directives. Without it an
        # annotation excuses itself and could never go stale, and documenting
        # the syntax would inflate the report.
        text = _blank(text, directives.shaped_spans(text, {DIRECTIVE}))
        for line_no, line in enumerate(text.splitlines(), 1):
            bare = line
            # One site per line: citing the same document twice in a sentence
            # is one place to look, not two.
            codes = set()
            for scheme in schemes().values():
                codes |= {scheme.code(m.group("num"))
                          for m in scheme.pattern.finditer(bare)}
            for code in codes:
                if own.get(path) == code or code not in docs:
                    continue
                # An annotation excuses a *retired* reference. Excusing an
                # in-force one means nothing, and counting it as "used" would
                # keep the annotation alive after its document went Active —
                # which is precisely when it should be reported as stale.
                excuse = None if docs[code].active else next(
                    (a for a in usable
                     if code in a.codes and a.covers(line_no)), None)
                result.cited.setdefault(code, []).append(
                    Citation(path, line_no, code, excuse))
    for sites in result.cited.values():
        sites.sort(key=lambda c: (str(c.path), c.line))
    return result


# ── Reporting ────────────────────────────────────────────────────────────


def _spread(sites: list[Citation], limit: int) -> list[Citation]:
    """Up to `limit` sites, one file at a time before repeating a file — a
    single file's five consecutive lines say much less than five files do."""
    if limit <= 0:
        return sites
    by_file: dict[Path, list[Citation]] = {}
    for c in sites:
        by_file.setdefault(c.path, []).append(c)
    picked: list[Citation] = []
    while len(picked) < limit and any(by_file.values()):
        for group in by_file.values():
            if group and len(picked) < limit:
                picked.append(group.pop(0))
    return picked


def flagged(result: Scan | None = None, docs: dict[str, Doc] | None = None):
    """(Doc, unexcused sites, excused count) for retired documents that are
    still cited without an acknowledgement — most-cited first."""
    docs = load_docs() if docs is None else docs
    result = scan(docs=docs) if result is None else result
    rows = []
    for code, sites in result.cited.items():
        doc = docs[code]
        if doc.active:
            continue
        loud = [c for c in sites if c.excused_by is None]
        if loud:
            rows.append((doc, loud, len(sites) - len(loud)))
    return sorted(rows, key=lambda r: (-len(r[1]), r[0].code))


def acknowledged_count(result: Scan | None = None,
                       docs: dict[str, Doc] | None = None) -> int:
    """How many references to retired documents an annotation excused. Printed
    every run: a suppression nobody counts is a suppression nobody notices."""
    docs = load_docs() if docs is None else docs
    result = scan(docs=docs) if result is None else result
    return sum(1 for code, sites in result.cited.items()
               if not docs[code].active
               for c in sites if c.excused_by is not None)


def stale_annotations(result: Scan | None = None,
                      docs: dict[str, Doc] | None = None) -> list[str]:
    """Annotations that no longer excuse anything — the document went Active,
    the reference moved, or the annotation is malformed. A suppression that
    rots silently is the thing acknowledgements are supposed to prevent."""
    docs = load_docs() if docs is None else docs
    result = scan(docs=docs) if result is None else result
    out = []
    for ann in result.annotations:
        if ann.problem:
            out.append(f"{ann}: annotation {ann.problem}")
        elif not result.used(ann):
            active = sorted(c for c in ann.codes
                            if c in docs and docs[c].active)
            why = (f"{', '.join(active)} is Active now" if active
                   else "nothing in scope cites "
                        f"{', '.join(sorted(ann.codes))}")
            out.append(f"{ann}: annotation no longer applies — {why}")
    return sorted(out)


def summary_lines(result: Scan | None = None,
                  docs: dict[str, Doc] | None = None) -> list[str]:
    """One line per flagged document — what `make lint-docs` prints. Every count
    is real; the sites are what's elided, and `make ref-status` has them."""
    out = []
    for doc, loud, excused in flagged(result, docs):
        files = len({c.path for c in loud})
        tail = f", {excused} acknowledged" if excused else ""
        out.append(f"{doc.code} is {doc.status}, cited {len(loud)}× in "
                   f"{files} file(s){tail} — {doc.title}")
    return out


def warnings(sites: int = DEFAULT_SITES, result: Scan | None = None,
             docs: dict[str, Doc] | None = None) -> list[str]:
    """The summary, plus where to look."""
    docs = load_docs() if docs is None else docs
    result = scan(docs=docs) if result is None else result
    lines: list[str] = []
    for line, (_, loud, _) in zip(summary_lines(result, docs),
                                  flagged(result, docs)):
        lines.append(line)
        shown = _spread(loud, sites)
        lines += [f"    {c}"
                  for c in sorted(shown, key=lambda c: (str(c.path), c.line))]
        if len(loud) > len(shown):
            lines.append(f"    … and {len(loud) - len(shown)} more"
                         " (`luria ref-status --all` lists them)")
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true", help="list every citation")
    args = ap.parse_args()

    docs = load_docs()
    result = scan(docs=docs)
    rows = flagged(result, docs)
    excused = acknowledged_count(result, docs)

    if rows:
        note = f", {excused} acknowledged reference(s)" if excused else ""
        print(f"reference status: {len(rows)} retired document(s) cited "
              f"unacknowledged from current docs/code{note}", file=sys.stderr)
        for line in warnings(0 if args.all else DEFAULT_SITES, result, docs):
            print(f"  {line}", file=sys.stderr)
    else:
        print(f"reference status: no unacknowledged references to retired "
              f"documents ({excused} acknowledged)")

    stale = stale_annotations(result, docs)
    if stale:
        print(f"reference status: {len(stale)} annotation(s) no longer apply",
              file=sys.stderr)
        for line in stale:
            print(f"  {line}", file=sys.stderr)
    return 0            # warnings never fail the build


if __name__ == "__main__":
    raise SystemExit(main())
