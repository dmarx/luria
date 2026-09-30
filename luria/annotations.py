#!/usr/bin/env python3
"""A relation stated in prose, and prose owed to a relation (#333).

A reference field says *that* two documents are related; the body is where a
reader learns *why*. Until now the two never met: a citation in prose was a
mention, however plainly the sentence around it said "this builds on that",
and a relation in frontmatter could stand with nothing in the body saying
what it meant. Naming the relation on the citation joins them:

    The recovery path is [[extends::LIT-7]]'s, generalised.
    Nothing here is new (see [[extended_by::LIT-12|the follow-up]]).

`relation::` is Semantic MediaWiki's spelling of a typed link, and the name
is the frontmatter field of *this* document that holds the fact — so there
is no direction to read and no arrow to get backwards. A relation that runs
the other way is named by its converse, which is what a converse is for.
`luria link --fix` expands the wikilink into a markdown link carrying the
relation as its title, `[LIT-7](LIT-007.md "extends")`, which renders as an
ordinary link with the relation on hover; that committed form is read back
the same way, and a hand-written link may use it directly. Any reference
field works — declared ones and the built-in successor alike. A title that
is not identifier-shaped (`"the paper, 2019"`) is an ordinary tooltip.

Two directions, one fact each way:

- **Push up.** A named relation states an edge, and an edge belongs in
  frontmatter, where the index, the chains and the converse completion read
  it. The field and the code are fully determined, so one missing there is
  `unrecorded-relations` and `luria link --fix` writes it; the converse
  completion then writes the far side, as for any one-sided pair.
- **Push down.** A reference declared `explain: true` asks for the reverse:
  every code the field holds cited in the body, with the relation named. A
  plain citation of it is mechanical — `unannotated-relations`, and the fixer
  names the relation on the first one. A code the body never cites is not:
  the explanation is prose only a person can write, so it is
  `unexplained-relations`, a report, acknowledged per code with
  `<!-- unexplained-ok: LIT-012 — why this needs no prose -->`.

A named relation the record cannot hold — one the scheme does not declare,
into a scheme the field does not hold, naming no document here, or
contradicting a single-valued field that already holds another code — is
`bad-annotations`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import directives, doc_refs, relations
from .adr_index import Adr, load_scheme
from .config import TEMP_TAIL, current
from .contract import ANY_SCHEME, for_scheme, local_scheme, reference_code
from .field_edit import add_to_field

ACK = "unexplained-ok"

# A link title names a relation only when it could be a field name. Anything
# with a space or a capital is prose, and prose in a title is a tooltip.
RELATION_TITLE_RE = re.compile(r"[a-z_][\w-]*")

# What can carry a relation: a wikilink or an inline link. A bare code
# cannot, but it is still a citation push-down can annotate.
CITE_RE = re.compile(
    r"\[\[(?P<wiki>[^\][|]+?)(?:\|[^\][]+)?\]\]"
    r"|!?\[(?P<label>[^\]]*)\]\((?P<target>[^)\s]*)"
    r"(?:\s+\"(?P<title>[^\"\n]*)\")?\)"
    r"|(?<![\w/#.-])(?P<bare>[A-Z]{2,}(?:-[A-Z]+)*-(?:\d{1,4}|"
    + TEMP_TAIL + r"))(?!\w)")


@dataclass(frozen=True)
class Citation:
    """One citation in a body, and the relation it names if any."""
    code: str
    start: int
    end: int
    line: int
    kind: str              # "wiki", "link" or "bare"
    relation: str = ""

    def named(self, text: str, relation: str) -> str:
        """This citation's source text with `relation` named on it."""
        token = text[self.start:self.end]
        if self.kind == "wiki":
            return f"[[{relation}::{token[2:]}"
        if self.kind == "link":
            return f'{token[:-1]} "{relation}")'
        return f"[[{relation}::{token}]]"


@dataclass(frozen=True)
class Write:
    """One code to add to one frontmatter field."""
    path: Path
    field: str
    code: str
    many: bool


@dataclass(frozen=True)
class Rewrite:
    """One citation to replace with its annotated spelling."""
    path: Path
    start: int
    end: int
    text: str


@dataclass
class Survey:
    writes: list[Write]
    rewrites: list[Rewrite]
    unrecorded: list[str]
    unannotated: list[str]
    unexplained: list[str]
    bad: list[str]


def canonical(token: str) -> str | None:
    """The code a citation token names, spelled the way the scheme spells
    it (`ADR-12` and `ADR-012` are one document)."""
    code = reference_code(token)
    if not code:
        return None
    prefix = local_scheme(code)
    tail = code.rsplit("-", 1)[1]
    if prefix and tail.isdigit():
        return current().schemes[prefix].code(tail)
    return code


def _read(m: re.Match) -> tuple[str | None, str, str]:
    """(code, relation, kind) for one citation match."""
    if m.group("wiki") is not None:
        inner, relation = m.group("wiki"), ""
        if typed := doc_refs.RELATION_PREFIX_RE.match(inner):
            relation, inner = typed.group(1), inner[typed.end():]
        return canonical(inner), relation, "wiki"
    if m.group("bare") is not None:
        return canonical(m.group("bare")), "", "bare"
    # The label first: a remote link's target is a URL that may well end in
    # a filename shaped like a local code. A target is read only when the
    # label names nothing (`[the delivery decision](ADR-012.md)`).
    target, title = m.group("target"), m.group("title") or ""
    code = (canonical(m.group("label"))
            or (canonical(target) if "://" not in target else None))
    relation = title if RELATION_TITLE_RE.fullmatch(title) else ""
    return code, relation, "link"


def _body_start(text: str) -> int:
    if not text.startswith("---\n"):
        return 0
    end = text.find("\n---\n", 3)
    return 0 if end == -1 else end + 5


def scan(text: str) -> list[Citation]:
    """Every citation in the body. Quoted regions and comments are
    specimens, never statements."""
    start = _body_start(text)
    skip = doc_refs.code_spans(text) + [
        m.span() for m in doc_refs.COMMENT_RE.finditer(text)]
    out: list[Citation] = []
    for m in CITE_RE.finditer(text, start):
        if any(a <= m.start() < b for a, b in skip):
            continue
        code, relation, kind = _read(m)
        if code is not None:
            out.append(Citation(code, m.start(), m.end(),
                                text.count("\n", 0, m.start()) + 1,
                                kind, relation))
    return out


def _listed(raw) -> list[str]:
    if raw in (None, ""):
        return []
    return [str(v) for v in (raw if isinstance(raw, list) else [raw])]


def _values(doc: Adr, field: str) -> set[str]:
    return {c for c in (canonical(v) for v in _listed(doc.meta.get(field)))
            if c}


def _acknowledged(path: Path, text: str) -> set[str]:
    return {c for d in directives.find(path, text, {ACK})
            for c in (canonical(a) for a in d.args) if c}


def _push_up(doc: Adr, code: str, cite: Citation, docs: dict[str, Adr],
             s: Survey) -> None:
    """What one named relation asks of this document's frontmatter."""
    cfg = current()
    where = f"{cfg.rel(doc.path)}:{cite.line}"
    said = f"`{cite.relation}::{cite.code}`"
    spec = next((f for f in for_scheme(doc.scheme).fields
                 if f.name == cite.relation and f.reference), None)
    if spec is None:
        s.bad.append(f"{where}: {said} — {doc.prefix} declares no reference "
                     f"`{cite.relation}`, so {code} cannot hold it")
        return
    if cite.code not in docs:
        s.bad.append(f"{where}: {said} — {cite.code} is no document in this "
                     f"record, so there is no edge to hold")
        return
    if cite.code == code:
        s.bad.append(f"{where}: {said} relates {code} to itself")
        return
    if spec.reference != ANY_SCHEME and local_scheme(cite.code) != spec.reference:
        s.bad.append(f"{where}: {said} — `{cite.relation}` holds "
                     f"{spec.reference} codes, and {cite.code} is not one")
        return
    back = relations.converse_of(doc.prefix, cite.relation)
    if cite.code in _values(doc, cite.relation) or (
            back and code in _values(docs[cite.code], back)):
        return
    if not spec.many and _listed(doc.meta.get(cite.relation)):
        s.bad.append(f"{where}: {said} contradicts `{cite.relation}: "
                     f"{doc.meta[cite.relation]}`, which holds one code")
        return
    if spec.many:
        blocked = relations._blocked("", {}, [relations.Repair(
            doc.path, cite.relation, cite.code)])[1]
        if blocked:
            s.bad.append(f"{where}: {said} — writing it would leave this "
                         f"document in breach of its scheme "
                         f"({blocked[0][1].split(': ', 1)[-1]})")
            return
    s.writes.append(Write(doc.path, cite.relation, cite.code, spec.many))
    s.unrecorded.append(
        f"{where}: {said} is not in frontmatter — `luria link --fix` writes "
        f"`{cite.relation}: {cite.code}`")


def _push_down(doc: Adr, cites: list[Citation], text: str,
               s: Survey) -> None:
    """What each explained relation this document holds asks of its body."""
    rel = current().rel(doc.path)
    acked = None
    # A citation names one relation, so one annotated here is spent.
    spent: set[int] = set()
    for ref in doc.scheme.references:
        if not ref.explain:
            continue
        for target in sorted(_values(doc, ref.field)):
            if any(c.code == target and c.relation == ref.field
                   for c in cites):
                continue
            plain = next((c for c in cites if c.code == target
                          and not c.relation and c.start not in spent), None)
            if plain is not None:
                spent.add(plain.start)
                new = plain.named(text, ref.field)
                s.rewrites.append(Rewrite(doc.path, plain.start, plain.end,
                                          new))
                s.unannotated.append(
                    f"{rel}:{plain.line}: cites {target} without naming the "
                    f"`{ref.field}` relation — `luria link --fix` writes "
                    f"`{new}`")
                continue
            if acked is None:
                acked = _acknowledged(doc.path, text)
            if target in acked:
                continue
            s.unexplained.append(
                f"{rel}: `{ref.field}: {target}` is never explained — the "
                f"body does not cite {target}; say what the relation means "
                f"there (`[[{ref.field}::{target}]]`), or acknowledge it "
                f"with `{ACK}:`")


def survey() -> Survey:
    """Every named relation against frontmatter, and every explained
    relation against its body — one reading of the record."""
    s = Survey([], [], [], [], [], [])
    docs: dict[str, Adr] = {}
    for scheme in current().schemes.values():
        for doc in load_scheme(scheme):
            docs[canonical(doc.code) or doc.code] = doc
    for code, doc in sorted(docs.items()):
        text = doc.path.read_text(encoding="utf-8")
        if doc_refs.unlinted(doc.path, text):
            continue
        cites = scan(text)
        for cite in cites:
            if cite.relation:
                _push_up(doc, code, cite, docs, s)
        _push_down(doc, cites, text, s)
    return s


def _set_scalar(text: str, name: str, code: str) -> str:
    end = text.index("\n---\n", 3) + 1
    return f"{text[:end]}{name}: {code}\n{text[end:]}"


def complete(fix: bool = False) -> Survey:
    """Write what the survey found mechanical; report it without `fix`.

    Per file, citations first — their offsets are into the text as read —
    and frontmatter after, which only moves text below the fence."""
    s = survey()
    if not fix:
        return s
    for path in {w.path for w in s.writes} | {r.path for r in s.rewrites}:
        text = path.read_text(encoding="utf-8")
        for r in sorted((r for r in s.rewrites if r.path == path),
                        key=lambda r: r.start, reverse=True):
            text = text[:r.start] + r.text + text[r.end:]
        # Two citations naming one edge are one write.
        for w in dict.fromkeys(w for w in s.writes if w.path == path):
            text = (add_to_field(text, w.field, w.code) if w.many
                    else _set_scalar(text, w.field, w.code))
        path.write_text(text, encoding="utf-8")
    return s
