#!/usr/bin/env python3
"""A relation stated in prose, and prose owed to a relation (#333).

A reference field says *that* two documents are related; the body is where a
reader learns *why*. Until now the two never met: a citation in prose was a
mention, however plainly the sentence around it said "this builds on that",
and a relation in frontmatter could stand with nothing in the body saying
what it meant. An annotation on the citation joins them:

    Nothing here is new (see [[LIT-012]]{--extended_by-->here}).
    The recovery path is [[LIT-007]]{here--extends-->}'s, generalised.

`{--F-->here}` reads left to right: the cited document stands in relation `F`
to this one. `{here--F-->}` is the other direction: this document stands in
`F` to the cited one. `F` is a reference field declared on the scheme of the
document on the arrow's tail, which is the document whose frontmatter would
hold the fact.

Two directions, one fact each way:

- **Push up.** An annotation states an edge, and an edge belongs in
  frontmatter, where the index, the chains and the converse completion read
  it. Which field and which code is fully determined by the annotation, so
  one missing there is `unrecorded-relations` and `luria link --fix` writes
  it. When the cited document is the tail and the relation has a declared
  converse, the fact is written *here*, as the converse — the document whose
  prose asserted it is the one that changes, and `relations.complete` writes
  the far side as it would for any one-sided pair.
- **Push down.** A reference declared `explain: true` asks for the reverse:
  every code the field holds cited in the body, annotated. A citation that is
  there without its annotation is mechanical — `unannotated-relations`, and
  the fixer annotates the first one. A code the body never cites is not: the
  explanation is prose only a person can write, so it is
  `unexplained-relations`, a report, acknowledged per code with
  `<!-- unexplained-ok: LIT-012 — why this needs no prose -->`.

An annotation the fixer cannot act on — attached to nothing, naming a
relation the scheme does not declare, pointing across schemes the relation
does not, contradicting a scalar field that already holds another code — is
`bad-annotations`, because each of those is a claim the record cannot hold
as written.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import directives, doc_refs, relations
from .adr_index import Adr, load_scheme
from .config import TEMP_TAIL, current
from .contract import ANY_SCHEME, local_scheme, reference_code
from .field_edit import add_to_field

ACK = "unexplained-ok"

# A relation name is a field name; the hyphen is allowed only between word
# characters, so `extends-->` never reads its arrow's first dash as part of
# the name. One dash either side is tolerated — the issue that asked for this
# wrote both `->` and `-->`.
_NAME = r"[A-Za-z_]\w*(?:-\w+)*"
ANNOTATION_RE = re.compile(
    r"\{\s*(?:(?P<out>here)\s*--?\s*(?P<of>" + _NAME + r")\s*--?>"
    r"|--?\s*(?P<if>" + _NAME + r")\s*--?>\s*(?P<in>here))\s*\}")

# What an annotation attaches to: a wikilink, an inline link, or a bare code
# (which the bare-reference lint will ask to have linked — the annotation
# survives that rewrite because it follows the link either way).
CITE_RE = re.compile(
    r"\[\[(?P<wiki>[^\][|]+?)(?:\|[^\][]+)?\]\]"
    r"|!?\[(?P<label>[^\]]*)\]\((?P<target>[^)\s]*)\)"
    r"|(?<![\w/#.-])(?P<bare>[A-Z]{2,}(?:-[A-Z]+)*-(?:\d{1,4}|"
    + TEMP_TAIL + r"))(?!\w)")


@dataclass(frozen=True)
class Citation:
    """One citation in a body, with the annotation it carries if any."""
    code: str
    end: int               # where an annotation attaches
    line: int
    relation: str = ""     # "" when unannotated
    incoming: bool = False  # `{--F-->here}` rather than `{here--F-->}`


@dataclass(frozen=True)
class Write:
    """One code to add to one frontmatter field."""
    path: Path
    field: str
    code: str
    many: bool


@dataclass(frozen=True)
class Insert:
    """One annotation to add after one citation."""
    path: Path
    at: int
    text: str


@dataclass
class Survey:
    writes: list[Write]
    inserts: list[Insert]
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


def _code_of(m: re.Match) -> str | None:
    if m.group("wiki") is not None:
        return canonical(m.group("wiki"))
    if m.group("bare") is not None:
        return canonical(m.group("bare"))
    # The label first: a remote link's target is a URL that may well end in
    # a filename shaped like a local code. A target is read only when the
    # label names nothing (`[the delivery decision](ADR-012.md)`).
    target = m.group("target")
    return (canonical(m.group("label"))
            or (canonical(target) if "://" not in target else None))


def _body_start(text: str) -> int:
    if not text.startswith("---\n"):
        return 0
    end = text.find("\n---\n", 3)
    return 0 if end == -1 else end + 5


def scan(text: str) -> tuple[list[Citation], list[int]]:
    """Every citation in the body, and the lines of annotations attached to
    none. Quoted regions and comments are specimens, never statements."""
    start = _body_start(text)
    skip = doc_refs.code_spans(text) + [
        m.span() for m in doc_refs.COMMENT_RE.finditer(text)]

    def quoted(pos: int) -> bool:
        return any(a <= pos < b for a, b in skip)

    def line(pos: int) -> int:
        return text.count("\n", 0, pos) + 1

    cites: list[Citation] = []
    attached: set[int] = set()
    for m in CITE_RE.finditer(text, start):
        if quoted(m.start()):
            continue
        code = _code_of(m)
        if code is None:
            continue
        a = ANNOTATION_RE.match(text, m.end())
        if a:
            attached.add(a.start())
            cites.append(Citation(code, m.end(), line(m.start()),
                                  a.group("of") or a.group("if"),
                                  bool(a.group("in"))))
        else:
            cites.append(Citation(code, m.end(), line(m.start())))
    orphans = [line(a.start()) for a in ANNOTATION_RE.finditer(text, start)
               if a.start() not in attached and not quoted(a.start())]
    return cites, orphans


def _listed(raw) -> list[str]:
    if raw in (None, ""):
        return []
    return [str(v) for v in (raw if isinstance(raw, list) else [raw])]


def _values(doc: Adr, field: str) -> set[str]:
    return {c for c in (canonical(v) for v in _listed(doc.meta.get(field)))
            if c}


def _reference(code: str, field: str):
    prefix = local_scheme(code)
    if prefix is None:
        return None
    return next((r for r in current().schemes[prefix].references
                 if r.field == field), None)


def _acknowledged(path: Path, text: str) -> set[str]:
    return {c for d in directives.find(path, text, {ACK})
            for c in (canonical(a) for a in d.args) if c}


def _push_up(doc: Adr, code: str, cite: Citation, docs: dict[str, Adr],
             s: Survey) -> None:
    """What one annotation asks of frontmatter."""
    rel = current().rel(doc.path)
    where = f"{rel}:{cite.line}"
    tail, head = (cite.code, code) if cite.incoming else (code, cite.code)
    arrow = (f"{{--{cite.relation}-->here}}" if cite.incoming
             else f"{{here--{cite.relation}-->}}")
    if cite.code not in docs:
        s.bad.append(f"{where}: `{cite.code}{arrow}` — {cite.code} is no "
                     f"document in this record, so there is no edge to hold")
        return
    if tail == head:
        s.bad.append(f"{where}: `{arrow}` relates {code} to itself")
        return
    ref = _reference(tail, cite.relation)
    if ref is None:
        s.bad.append(f"{where}: `{arrow}` — {local_scheme(tail)} declares no "
                     f"reference `{cite.relation}`, so {tail} cannot hold it")
        return
    if ref.scheme != ANY_SCHEME and local_scheme(head) != ref.scheme:
        s.bad.append(f"{where}: `{arrow}` — `{cite.relation}` holds "
                     f"{ref.scheme} codes, and {head} is not one")
        return
    back = relations.converse_of(local_scheme(tail), cite.relation)
    if head in _values(docs[tail], cite.relation) or (
            back and tail in _values(docs[head], back)):
        return
    # Written here, as the converse, when there is one to write: the prose
    # that asserted the edge is in this document, and the far side is the
    # converse completion's to write.
    if cite.incoming and back:
        write = Write(doc.path, back, cite.code, True)
    else:
        write = Write(docs[tail].path, cite.relation, head, ref.many)
    target = docs[tail] if write.path == docs[tail].path else doc
    if not write.many and _listed(target.meta.get(write.field)):
        s.bad.append(f"{where}: `{arrow}` contradicts "
                     f"`{write.field}: {target.meta[write.field]}` in "
                     f"{current().rel(write.path)}, which holds one code")
        return
    if write.many:
        blocked = relations._blocked(
            "", {}, [relations.Repair(write.path, write.field, write.code)])[1]
        if blocked:
            s.bad.append(f"{where}: `{arrow}` — writing `{write.field}: "
                         f"{write.code}` would leave "
                         f"{current().rel(write.path)} in breach of its "
                         f"scheme ({blocked[0][1].split(': ', 1)[-1]})")
            return
    s.writes.append(write)
    s.unrecorded.append(
        f"{where}: `{cite.code}{arrow}` is not in frontmatter — "
        f"`luria link --fix` writes `{write.field}: {write.code}` into "
        f"{current().rel(write.path)}")


def _push_down(doc: Adr, code: str, cites: list[Citation], text: str,
               s: Survey) -> None:
    """What each explained relation this document holds asks of its body."""
    rel = current().rel(doc.path)
    acked = None
    # A citation carries one annotation, so one annotated here is spent.
    spent: set[int] = set()
    for ref in doc.scheme.references:
        if not ref.explain:
            continue
        back = relations.converse_of(doc.prefix, ref.field)
        for target in sorted(_values(doc, ref.field)):
            if any(c.code == target and (
                    (not c.incoming and c.relation == ref.field)
                    or (c.incoming and back and c.relation == back))
                   for c in cites):
                continue
            plain = next((c for c in cites if c.code == target
                          and not c.relation and c.end not in spent), None)
            if plain is not None:
                spent.add(plain.end)
                note = (f"{{--{back}-->here}}" if back
                        else f"{{here--{ref.field}-->}}")
                s.inserts.append(Insert(doc.path, plain.end, note))
                s.unannotated.append(
                    f"{rel}:{plain.line}: cites {target} without saying it "
                    f"is the `{ref.field}` relation — `luria link --fix` "
                    f"annotates it `{note}`")
                continue
            if acked is None:
                acked = _acknowledged(doc.path, text)
            if target in acked:
                continue
            s.unexplained.append(
                f"{rel}: `{ref.field}: {target}` is never explained — the "
                f"body does not cite {target}; say what the relation means "
                f"there (`[[{target}]]"
                + (f"{{--{back}-->here}}" if back
                   else f"{{here--{ref.field}-->}}")
                + f"`), or acknowledge it with `{ACK}:`")


def survey() -> Survey:
    """Every annotation against frontmatter, and every explained relation
    against its body — one reading of the record."""
    s = Survey([], [], [], [], [], [])
    docs: dict[str, Adr] = {}
    for scheme in current().schemes.values():
        for doc in load_scheme(scheme):
            docs[canonical(doc.code) or doc.code] = doc
    for code, doc in sorted(docs.items()):
        text = doc.path.read_text(encoding="utf-8")
        if doc_refs.unlinted(doc.path, text):
            continue
        cites, orphans = scan(text)
        for line in orphans:
            s.bad.append(f"{current().rel(doc.path)}:{line}: a relation "
                         f"annotation follows no citation, so it names an "
                         f"edge with one end")
        for cite in cites:
            if cite.relation:
                _push_up(doc, code, cite, docs, s)
        _push_down(doc, code, cites, text, s)
    return s


def _set_scalar(text: str, name: str, code: str) -> str:
    end = text.index("\n---\n", 3) + 1
    return f"{text[:end]}{name}: {code}\n{text[end:]}"


def complete(fix: bool = False) -> Survey:
    """Write what the survey found mechanical; report it without `fix`.

    Per file, annotations first — their offsets are into the text as read —
    and frontmatter after, which only moves text below the fence."""
    s = survey()
    if not fix:
        return s
    paths = {w.path for w in s.writes} | {i.path for i in s.inserts}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for ins in sorted((i for i in s.inserts if i.path == path),
                          key=lambda i: i.at, reverse=True):
            text = text[:ins.at] + ins.text + text[ins.at:]
        # Two annotations of one edge are one write.
        for w in dict.fromkeys(w for w in s.writes if w.path == path):
            text = (add_to_field(text, w.field, w.code) if w.many
                    else _set_scalar(text, w.field, w.code))
        path.write_text(text, encoding="utf-8")
    return s
