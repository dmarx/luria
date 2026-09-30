#!/usr/bin/env python3
"""A relation stated in prose, and prose owed to a relation (#333).

A reference field says *that* two documents are related; the body is where a
reader learns *why*. Until now the two never met: a citation in prose was a
mention, however plainly the sentence around it said "this builds on that",
and a relation in frontmatter could stand with nothing in the body saying
what it meant.

A relation is stated in the body with the grammar every acknowledgement
already uses — a comment directive, in the `ref::` namespace, named by the
field that holds it:

    The recovery path is LIT-007's, generalised. <!-- ref::extends: LIT-007 -->
    <!-- ref::extended_by-block: LIT-012, LIT-015 — both carry the retry loop on -->

The name after `ref::` is a reference field of *this* document, declared or
built in, so there is no direction to choose: the other direction is the
converse's name. The namespace keeps these user-defined names apart from the
fixed vocabulary, and it is what lets a misspelt field be reported rather
than read as no directive at all. Everything a directive already has comes
with it — line, `-block` and `-file` scope, `— reason`, `until <date>` — and
so does the rule that a quoted example is not a statement.
`[[extends::LIT-7]]` is shorthand: `luria link --fix` expands it into the
link and the statement beside it,
`[LIT-7](LIT-007.md)<!-- ref::extends: LIT-007 -->`.

Two directions, one fact each way:

- **Push up.** A statement names an edge, and an edge belongs in
  frontmatter, where the index, the chains and the converse completion read
  it. The field and the code are fully determined, so one missing there is
  `unrecorded-relations` and `luria link --fix` writes it; the converse
  completion then writes the far side, as for any one-sided pair.
- **Push down.** A reference declared `explain:` asks for the reverse, at
  one of two strengths. `explain: cited` (or `true`) asks only that the body cite each
  code the field holds, and takes the citation as serving the relation; a
  code the body never cites is `unexplained-relations`, a report, because
  the explanation is prose only a person can write. `explain: stated` asks
  more: the citation must carry a statement of the relation
  (a statement governing it, or one with a `— reason`). A citation without
  one is mechanical — `unannotated-relations`, and the fixer writes the
  statement after the first one. At either strength, a statement with a
  reason is how a person says the relation needs no more prose than that —
  the acknowledgement and the statement are one directive.

  The weaker strength exists because the stronger one, run over a real
  record, mostly annotated citations whose sentence already said what the
  relation was. What earned its keep was the relation nothing in the prose
  mentioned, and `cited` finds exactly that.

A statement the record cannot hold — naming a field the document does not
have, naming no document here, a code in a scheme the field does not hold,
or contradicting a single-valued field that already holds another code — is
`bad-annotations`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import directives, doc_refs, relations
from .adr_index import Adr, load_scheme
from .config import EXPLAIN_CITED, TEMP_TAIL, current
from .contract import ANY_SCHEME, for_scheme, local_scheme, reference_code
from .field_edit import add_to_field

# The namespace a relation statement's name lives in: `<!-- ref::F: X -->`.
PREFIX = "ref::"

# What counts as citing a code: a wikilink, an inline link, or a bare code.
CITE_RE = re.compile(
    r"\[\[(?P<wiki>[^\][|]+?)(?:\|[^\][]+)?\]\]"
    r"|!?\[(?P<label>[^\]]*)\]\((?P<target>[^)\s]*)(?:\s+\"[^\"\n]*\")?\)"
    r"|(?<![\w/#.-])(?P<bare>[A-Z]{2,}(?:-[A-Z]+)*-(?:\d{1,4}|"
    + TEMP_TAIL + r"))(?!\w)")


@dataclass(frozen=True)
class Citation:
    """One citation in a body. `line` is where it ends, which is where a
    statement written after it sits."""
    code: str
    end: int
    line: int


@dataclass(frozen=True)
class Statement:
    """One relation stated in the body: `relation: code`."""
    relation: str
    code: str
    line: int
    lines: frozenset[int]  # what the statement governs
    reason: str


@dataclass(frozen=True)
class Write:
    """One code to add to one frontmatter field."""
    path: Path
    field: str
    code: str
    many: bool


@dataclass(frozen=True)
class Insert:
    """One statement to write after one citation."""
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
    """The code a token names, spelled the way the scheme spells it
    (`ADR-12` and `ADR-012` are one document)."""
    code = reference_code(token)
    if not code:
        return None
    prefix = local_scheme(code)
    if not prefix:
        return code  # a remote code's tail is opaque: `DOI:10.1109/72.238311`
    tail = code.rsplit("-", 1)[1]
    if tail.isdigit():
        return current().schemes[prefix].code(tail)
    return code


def fields_of(path: Path) -> dict:
    """The reference fields the document at `path` can hold, by name — {}
    for anything that is not a scheme document."""
    contract = relations._contract_for(path)
    if contract is None:
        return {}
    return {f.name: f for f in contract.fields if f.reference}


def holds(path: Path, relation: str) -> bool:
    """Whether a statement of `relation` in `path` has a field to land in."""
    return relation in fields_of(path)


def _code_of(m: re.Match) -> str | None:
    if m.group("wiki") is not None:
        inner = m.group("wiki")
        if typed := doc_refs.RELATION_PREFIX_RE.match(inner):
            inner = inner[typed.end():]
        return canonical(inner)
    if m.group("bare") is not None:
        return canonical(m.group("bare"))
    # The label first: a remote link's target is a URL that may well end in
    # a filename shaped like a local code.
    target = m.group("target")
    return (canonical(m.group("label"))
            or (canonical(target) if "://" not in target else None))


def _body_start(text: str) -> int:
    if not text.startswith("---\n"):
        return 0
    end = text.find("\n---\n", 3)
    return 0 if end == -1 else end + 5


def citations(text: str) -> list[Citation]:
    """Every citation in the body. Quoted regions and comments are
    specimens, never statements."""
    skip = doc_refs.code_spans(text) + [
        m.span() for m in doc_refs.COMMENT_RE.finditer(text)]
    out: list[Citation] = []
    for m in CITE_RE.finditer(text, _body_start(text)):
        if any(a <= m.start() < b for a, b in skip):
            continue
        if (code := _code_of(m)) is not None:
            out.append(Citation(code, m.end(),
                                text.count("\n", 0, m.end() - 1) + 1))
    return out


def statements(path: Path, text: str, names: set[str]
               ) -> tuple[list[Statement], list[str]]:
    """Every relation stated in the body — `ref::` directives, and typed
    wikilinks not yet expanded into one — and what is wrong with the rest:
    a field `names` does not hold, or an argument that is no code."""
    body_line = text.count("\n", 0, _body_start(text)) + 1
    out: list[Statement] = []
    junk: list[str] = []
    for d in directives.find(path, text):
        if not d.name.startswith(PREFIX) or d.line < body_line:
            continue                     # a frontmatter comment says nothing
        relation = d.name[len(PREFIX):]
        if relation not in names:
            junk.append(f"{d.line}: `{d.name}` names no reference field this "
                        f"document holds")
            continue
        for arg in d.args:
            code = canonical(arg)
            if code is None:
                junk.append(f"{d.line}: `{d.name}: {arg}` names no code")
                continue
            lines = (frozenset(range(1, text.count("\n") + 2))
                     if d.scope == directives.FILE else d.lines)
            out.append(Statement(relation, code, d.line, lines, d.reason))
    for w in doc_refs.wikilinks(text, path):
        if w.relation in names and (code := canonical(w.inner)):
            out.append(Statement(w.relation, code, w.line,
                                 frozenset({w.line, w.line + 1}), ""))
    return out, junk


def _listed(raw) -> list[str]:
    if raw in (None, ""):
        return []
    return [str(v) for v in (raw if isinstance(raw, list) else [raw])]


def _values(doc: Adr, field: str) -> set[str]:
    return {c for c in (canonical(v) for v in _listed(doc.meta.get(field)))
            if c}


def _push_up(doc: Adr, code: str, st: Statement, spec,
             docs: dict[str, Adr], s: Survey) -> None:
    """What one statement asks of this document's frontmatter."""
    where = f"{current().rel(doc.path)}:{st.line}"
    said = f"`{PREFIX}{st.relation}: {st.code}`"
    if st.code not in docs:
        s.bad.append(f"{where}: {said} — {st.code} is no document in this "
                     f"record, so there is no edge to hold")
        return
    if st.code == code:
        s.bad.append(f"{where}: {said} relates {code} to itself")
        return
    if spec.reference != ANY_SCHEME and local_scheme(st.code) != spec.reference:
        s.bad.append(f"{where}: {said} — `{st.relation}` holds "
                     f"{spec.reference} codes, and {st.code} is not one")
        return
    back = relations.converse_of(doc.prefix, st.relation)
    if st.code in _values(doc, st.relation) or (
            back and code in _values(docs[st.code], back)):
        return
    if not spec.many and _listed(doc.meta.get(st.relation)):
        s.bad.append(f"{where}: {said} contradicts `{st.relation}: "
                     f"{doc.meta[st.relation]}`, which holds one code")
        return
    if spec.many:
        blocked = relations._blocked("", {}, [relations.Repair(
            doc.path, st.relation, st.code)])[1]
        if blocked:
            s.bad.append(f"{where}: {said} — writing it would leave this "
                         f"document in breach of its scheme "
                         f"({blocked[0][1].split(': ', 1)[-1]})")
            return
    s.writes.append(Write(doc.path, st.relation, st.code, spec.many))
    s.unrecorded.append(f"{where}: {said} is stated here and not in "
                        f"frontmatter (`luria link --fix` writes it)")


def _push_down(doc: Adr, cites: list[Citation], stated: list[Statement],
               s: Survey) -> None:
    """What each explained relation this document holds asks of its body."""
    rel = current().rel(doc.path)
    for ref in doc.scheme.references:
        if not ref.explain:
            continue
        for target in sorted(_values(doc, ref.field)):
            mine = [st for st in stated
                    if st.relation == ref.field and st.code == target]
            cited = [c for c in cites if c.code == target]
            if any(st.reason or any(c.line in st.lines for c in cited)
                   for st in mine):
                continue
            if ref.explain == EXPLAIN_CITED:
                # The weaker strength takes a citation as serving the
                # relation. What it exists to catch is the edge the prose
                # never mentions — the one with no explanation at all.
                if cited:
                    continue
                s.unexplained.append(
                    f"{rel}: `{ref.field}: {target}` is never explained — the "
                    f"body never cites {target}. Cite it where you say why, or "
                    f"give a statement a reason "
                    f"(`<!-- {PREFIX}{ref.field}-file: {target} — why -->`)")
                continue
            if cited and not mine:
                first = cited[0]
                note = f"<!-- {PREFIX}{ref.field}: {target} -->"
                s.inserts.append(Insert(doc.path, first.end, note))
                s.unannotated.append(
                    f"{rel}:{first.line}: cites {target} without stating the "
                    f"`{ref.field}` relation — `luria link --fix` writes "
                    f"`{note}` after it")
                continue
            why = ("states it with no citation beside it and no reason"
                   if mine else "never cites it")
            s.unexplained.append(
                f"{rel}: `{ref.field}: {target}` is never explained — the "
                f"body {why}. Cite it where you say why "
                f"(`[[{ref.field}::{target}]]`), or give the statement a "
                f"reason (`<!-- {PREFIX}{ref.field}-file: {target} — why -->`)")


def survey() -> Survey:
    """Every stated relation against frontmatter, and every explained
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
        fields = fields_of(doc.path)
        stated, junk = statements(doc.path, text, set(fields))
        for entry in junk:
            s.bad.append(f"{current().rel(doc.path)}:{entry}")
        for st in stated:
            _push_up(doc, code, st, fields[st.relation], docs, s)
        _push_down(doc, citations(text), stated, s)
    return s


def _set_scalar(text: str, name: str, code: str) -> str:
    end = text.index("\n---\n", 3) + 1
    return f"{text[:end]}{name}: {code}\n{text[end:]}"


def complete(fix: bool = False) -> Survey:
    """Write what the survey found mechanical; report it without `fix`.

    Per file, statements first — their offsets are into the text as read —
    and frontmatter after, which only moves text below the fence."""
    s = survey()
    if not fix:
        return s
    for path in {w.path for w in s.writes} | {i.path for i in s.inserts}:
        text = path.read_text(encoding="utf-8")
        for ins in sorted((i for i in s.inserts if i.path == path),
                          key=lambda i: i.at, reverse=True):
            text = text[:ins.at] + ins.text + text[ins.at:]
        # Two statements of one edge are one write.
        for w in dict.fromkeys(w for w in s.writes if w.path == path):
            text = (add_to_field(text, w.field, w.code) if w.many
                    else _set_scalar(text, w.field, w.code))
        path.write_text(text, encoding="utf-8")
    return s
