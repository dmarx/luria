#!/usr/bin/env python3
"""Report references that don't hold up, and the annotations that excuse them.

This is a library: `luria lint` prints its summary as warnings and
`luria reports` writes the full detail as markdown (ADR-030). The standalone
console report survives for the odd interactive dig:

    python -m luria.ref_status            # grouped report, 5 sites per document
    python -m luria.ref_status --all      # every site

Two ways a reference fails to mean what it says. It can point at a document
that is no longer in force — the original subject of this module — or it can
point at **no document at all**: a typo, a number carried over from another
project, a decision that was renumbered. Both are reported here; neither fails
a build (ADR-035).

A reference to another document reads as "this is why things are the way they
are". That claim is only true while the referenced document is in force. A
`Deferred` ADR cited from live plugin code, or a `Proposed` one cited as settled
architecture, is the same class of drift ADR-003 found in the status field
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
`CHANGELOG.md`, the fragment directories it is collected from, and every journal
(entries and books alike) — are excluded: "ADR-NNN landed" in a July entry is a
true statement about July, and would be permanent, unactionable noise.
`Config.is_historical` is the one place that decides this. A document citing
itself is excluded for the same reason (every ADR's own title names it).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import adr_index as builder
from . import directives, doc_refs, remotes
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
    for number, path in scheme.documents().items():
        doc = builder.Adr(path, scheme)
        # The bare status word: `Superseded — by [ADR-011](…)` is `Superseded`.
        status = re.split(r"\s+—\s+", doc.status, maxsplit=1)[0]
        code = scheme.code(number)
        docs[code] = Doc(code, status, doc.title, path, status == scheme.active)
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
URL_RE = re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s<>)\]\"']+", re.IGNORECASE)
DIRECTIVE = "inactive-ok"
# The mirror-image acknowledgement: this code names nothing here *on purpose*.
# A fixture number in a test, or another project's decision cited as history.
DANGLING_DIRECTIVE = "unresolved-ok"


def _codes(spec: str) -> tuple[set[str], str]:
    """The document codes an annotation names, and the text with them removed.

    Composed codes come out first and whole: a remote's `DP-004` is that
    remote's principle, and reading the tail out of the middle of the composed
    code would have the validator check the wrong project (ADR-016)."""
    codes: set[str] = set()
    refs = remotes.references(spec)
    for ref in refs:
        codes.add(ref.composed)
    for ref in sorted(refs, key=lambda r: r.start, reverse=True):
        spec = spec[:ref.start] + " " * (ref.end - ref.start) + spec[ref.end:]
    codes |= {f"{p.upper()}-{int(n):03d}" for p, n in CODE_RE.findall(spec)}
    return codes, spec


def _exists(code: str, known: set[str]) -> bool:
    """Whether a code names something. A composed one asks the remote —
    parsed by the remote's own delimiter and tail shape, not by assuming a
    hyphen (ADR-024)."""
    parsed = remotes.parse_code(code)
    if parsed is not None:
        remote, tail = parsed
        return bool(remotes.link(remote, tail))
    return code in known


@dataclass(frozen=True)
class Annotation:
    directive: directives.Directive
    codes: frozenset[str]
    problem: str | None = None        # malformed: what's wrong with it
    kind: str = DIRECTIVE             # which vocabulary word wrote it

    def __str__(self) -> str:
        return f"{_rel(self.directive.path)}:{self.directive.line}"

    @property
    def scope(self) -> str:
        return self.directive.scope

    def covers(self, line: int) -> bool:
        return self.directive.covers(line)


def annotations(path: Path, text: str, known: set[str],
                directive: str = DIRECTIVE) -> list[Annotation]:
    """Every annotation of one kind in `path`, malformed ones included — they
    are reported rather than dropped, because an annotation that silently does
    nothing is worse than no annotation.

    The two kinds share every rule but one, and it is inverted: `inactive-ok`
    must name a document that exists (else it excuses nothing), while
    `unresolved-ok` must name one that doesn't (else there is nothing to
    excuse). Same check, opposite sign."""
    resolvable = directive != DANGLING_DIRECTIVE
    found = []
    for d in directives.find(path, text, {directive}):
        spec = " ".join(d.args)
        codes, spec = _codes(spec)
        problem = None
        if not codes:
            problem = "names no document code"
        elif BARE_NUMBER_RE.search(CODE_RE.sub("", spec)):
            example = f"{next(iter(schemes()), 'ADR')}-012"
            problem = f"has a bare number — write the full code (e.g. {example})"
        elif resolvable and (unknown := sorted(
                c for c in codes if not _exists(c, known))):
            problem = f"names unknown document(s): {', '.join(unknown)}"
        elif not resolvable and (real := sorted(
                c for c in codes if _exists(c, known))):
            problem = f"names {', '.join(real)}, which does resolve here"
        found.append(Annotation(d, frozenset(codes), problem, directive))
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
    # Codes cited that name no document here. Kept rather than dropped: a
    # reference that resolves to nothing is a silent no-op, and a tool that
    # refuses without saying so teaches nobody (DP-1).
    dangling: dict[str, list[Citation]] = field(default_factory=dict)
    annotations: list[Annotation] = field(default_factory=list)
    # Files that opt out of reference checking wholesale (`unlinted-file:`,
    # #37). Counted, never hidden: the blanket exemption is the one
    # suppression a report can't converge past, so it has to stay visible.
    unlinted: list[Path] = field(default_factory=list)

    def used(self, ann: Annotation) -> bool:
        pool = self.dangling if ann.kind == DANGLING_DIRECTIVE else self.cited
        return any(c.excused_by is ann for sites in pool.values() for c in sites)


def scanned_files() -> list[Path]:
    """Current-guidance docs + code. Order is stable so the report is."""
    cfg = current()
    docs = [p for p in doc_refs.doc_files() if not cfg.is_historical(p)]
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
        if doc_refs.unlinted(path, text):
            result.unlinted.append(path)
            continue
        anns = annotations(path, text, known)
        dangling_anns = annotations(path, text, known, DANGLING_DIRECTIVE)
        result.annotations += anns + dangling_anns
        usable = [a for a in anns if not a.problem]
        usable_dangling = [a for a in dangling_anns if not a.problem]
        # Naming a code in a directive is not citing it — true of a live
        # annotation and of an example of one alike, which is why this matches
        # the *shape* rather than the parsed directives. Without it an
        # annotation excuses itself and could never go stale, and documenting
        # the syntax would inflate the report.
        from . import remotes as _remotes
        text = _blank(text, directives.shaped_spans(
            text, {DIRECTIVE, DANGLING_DIRECTIVE, _remotes.URL_OK}))
        # A code inside a URL is part of an address, not a citation. Linking
        # out to another project's ADR-013 is the *correct* way to name a
        # foreign document (ADR-009), and counting it as a local reference
        # would report every such link as dangling.
        text = _blank(text, [m.span() for m in URL_RE.finditer(text)])
        # `LU-ADR-013` names the remote's decision 13, not this project's.
        # Blanking the composed span is what stops the local scheme pattern
        # reading a foreign code out of the middle of it (ADR-016) — but a
        # foreign code that resolves to nothing is still a dangling reference,
        # so it is recorded on the way past rather than dropped.
        if current().remotes:
            spans = []
            for ref in remotes.references(text):
                spans.append((ref.start, ref.end))
                if not remotes.link(ref.remote, ref.tail):
                    code = ref.composed
                    where = text.count("\n", 0, ref.start) + 1
                    excuse = next((a for a in usable_dangling
                                   if code in a.codes and a.covers(where)), None)
                    result.dangling.setdefault(code, []).append(
                        Citation(path, where, code, excuse))
            text = _blank(text, spans)
        for line_no, line in enumerate(text.splitlines(), 1):
            bare = line
            # One site per line: citing the same document twice in a sentence
            # is one place to look, not two.
            codes = set()
            for scheme in schemes().values():
                codes |= {scheme.code(m.group("num"))
                          for m in scheme.pattern.finditer(bare)}
            for code in codes:
                if own.get(path) == code:
                    continue
                if code not in docs:
                    excuse = next((a for a in usable_dangling
                                   if code in a.codes and a.covers(line_no)), None)
                    result.dangling.setdefault(code, []).append(
                        Citation(path, line_no, code, excuse))
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
    for pool in (result.cited, result.dangling):
        for sites in pool.values():
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


def dangling(result: Scan | None = None,
             docs: dict[str, Doc] | None = None) -> list[tuple[str, list[Citation], int]]:
    """(code, unexcused sites, excused count) for codes that name no document
    here — most-cited first.

    Three things look identical from here and read very differently: a typo, a
    number carried in from another project, and a fixture code in a test. Only
    a human can tell them apart, which is why this is a report and not an error
    (ADR-035) — and why `unresolved-ok` exists to retire the ones that are
    deliberate."""
    result = scan(docs=docs) if result is None else result
    rows = []
    for code, sites in result.dangling.items():
        loud = [c for c in sites if c.excused_by is None]
        if loud:
            rows.append((code, loud, len(sites) - len(loud)))
    return sorted(rows, key=lambda r: (-len(r[1]), r[0]))


def dangling_lines(result: Scan | None = None,
                   docs: dict[str, Doc] | None = None) -> list[str]:
    out = []
    for code, loud, excused in dangling(result, docs):
        files = len({c.path for c in loud})
        tail = f", {excused} acknowledged" if excused else ""
        out.append(f"{code} resolves to no document, cited {len(loud)}× in "
                   f"{files} file(s){tail}")
    return out


def acknowledged_count(result: Scan | None = None,
                       docs: dict[str, Doc] | None = None) -> int:
    """How many references to retired documents an annotation excused. Printed
    every run: a suppression nobody counts is a suppression nobody notices."""
    docs = load_docs() if docs is None else docs
    result = scan(docs=docs) if result is None else result
    return sum(1 for code, sites in result.cited.items()
               if not docs[code].active
               for c in sites if c.excused_by is not None)


def dangling_acknowledged_count(result: Scan | None = None,
                                docs: dict[str, Doc] | None = None) -> int:
    """The same count for `unresolved-ok`. Both are printed on a clean run, so
    "nothing to report" can never mean "everything was silenced"."""
    result = scan(docs=docs) if result is None else result
    return sum(1 for sites in result.dangling.values()
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
            named = ", ".join(sorted(ann.codes))
            if ann.kind == DANGLING_DIRECTIVE:
                why = f"nothing in scope cites {named}"
            else:
                active = sorted(c for c in ann.codes
                                if c in docs and docs[c].active)
                why = (f"{', '.join(active)} is Active now" if active
                       else f"nothing in scope cites {named}")
            out.append(f"{ann}: annotation no longer applies — {why}")
    return sorted(out)


def summary_lines(result: Scan | None = None,
                  docs: dict[str, Doc] | None = None) -> list[str]:
    """One line per flagged document — what `luria lint` prints. Every count
    is real; the sites are what's elided, and `luria reports` has them."""
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
                         " (`luria reports` lists them)")
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

    loose_excused = dangling_acknowledged_count(result, docs)

    loose = dangling(result, docs)
    if not loose:
        print(f"reference status: every code resolves "
              f"({loose_excused} acknowledged)")
    if loose:
        print(f"reference status: {len(loose)} code(s) resolve to no document",
              file=sys.stderr)
        for code, sites, excused in loose:
            tail = f", {excused} acknowledged" if excused else ""
            print(f"  {code} — cited {len(sites)}×{tail}", file=sys.stderr)
            shown = _spread(sites, 0 if args.all else DEFAULT_SITES)
            for c in sorted(shown, key=lambda c: (str(c.path), c.line)):
                print(f"      {c}", file=sys.stderr)
            if len(sites) > len(shown):
                print(f"      … and {len(sites) - len(shown)} more", file=sys.stderr)

    stale = stale_annotations(result, docs)
    if stale:
        print(f"reference status: {len(stale)} annotation(s) no longer apply",
              file=sys.stderr)
        for line in stale:
            print(f"  {line}", file=sys.stderr)
    return 0            # warnings never fail the build


if __name__ == "__main__":
    raise SystemExit(main())
