# luria/facts.py
"""The record as facts: what the logic core reasons over.

luria's graph decisions — converse pairs, invariants, the edges a chain
walks, reference checks, config consistency — are relational: joins,
transitive closure, "no such edge exists". They move to Answer Set
Programming rules evaluated by clingo, one subsystem at a time (the ADR on a
logic core in clingo). This module is the procedural half's first job:
reading the configuration and every document into facts the rules can join.

    luria facts            print every fact, one per line, as clingo text

Two families, both plain ground atoms whose arguments are strings (or, for a
position, an integer), so a code like `LIT-001` needs no mangling:

    scheme(S).                    every declared scheme
    active(S, W).                 the status word that means in force
    ref(S, F).                    a reference field S declares…
    ref_target(S, F, T).          …each scheme its codes may name ("*": any)
    ref_converse(S, F, C).        …its declared converse
    ref_many(S, F). ref_required(S, F).
    ref_invariant(S, F, I).       …the field both ends must share a value in
    ref_label(S, F, L).           …what a view calls it
    chain(N, S). chain_relation(N, F, I). chain_sibling(N, F).
    chain_invariant(N, I).

    doc(C, S).                    every document, numbered or temporary
    status(C, W).                 its status word, without the note
    value(C, F, I, V).            every frontmatter value as the record reads
                                  it — derived fields included — one per list
                                  element, positioned (the `fields` table of
                                  `luria export`, from the same rows)
    ref_value(C, F, T).           each code a reference field holds, resolved
                                  through aliases; whether it lands on a
                                  document is the rules' business, not this
                                  module's
    edge(C, R, T).                the typed graph `luria/edges.py` derives

Every fact comes through the record's own readers — `load_scheme`, the
compiled contract, `edges.graph` — never a second parse, for the reason
`luria export` gives (DP-4).
"""
from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from .adr_index import load_scheme
from .config import current
from .contract import codes_of, for_scheme


@dataclass(frozen=True, order=True)
class Fact:
    """One ground atom: a predicate and its arguments, strings or ints."""
    predicate: str
    args: tuple[str | int, ...]

    def text(self) -> str:
        return f"{self.predicate}({', '.join(_term(a) for a in self.args)})."


def _term(value: str | int) -> str:
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    # A clingo string literal escapes exactly `\`, `"` and newlines.
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return '"' + text.replace("\n", "\\n") + '"'


def text(value) -> str:
    """One cell's worth of a frontmatter value. Scalars as they print; a
    mapping or a nested list as JSON, so nothing is dropped and nothing is
    guessed at. Shared with `luria export`, whose `fields` table these are."""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, default=str, ensure_ascii=False)
    return str(value)


def field_rows(code: str, meta: dict) -> list[tuple[str, str, int, str]]:
    """(code, field, position, value) for every value in a frontmatter
    mapping: a list explodes into one row per element, a scalar is position
    0, and an absent value is no row."""
    rows: list[tuple[str, str, int, str]] = []
    for name, value in meta.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            rows += [(code, name, i, text(v)) for i, v in enumerate(value)
                     if v is not None]
        else:
            rows.append((code, name, 0, text(value)))
    return rows


def schema_facts(cfg=None) -> Iterator[Fact]:
    """What `luria.yaml` declares, as facts."""
    cfg = cfg or current()
    for prefix, scheme in cfg.schemes.items():
        yield Fact("scheme", (prefix,))
        yield Fact("active", (prefix, scheme.active))
        for ref in scheme.references:
            yield Fact("ref", (prefix, ref.field))
            for target in ref.scheme:
                yield Fact("ref_target", (prefix, ref.field, target))
            if ref.converse:
                yield Fact("ref_converse", (prefix, ref.field, ref.converse))
            if ref.many:
                yield Fact("ref_many", (prefix, ref.field))
            if ref.required:
                yield Fact("ref_required", (prefix, ref.field))
            if ref.invariant:
                yield Fact("ref_invariant", (prefix, ref.field, ref.invariant))
            if ref.label:
                yield Fact("ref_label", (prefix, ref.field, ref.label))
    for name, chain in cfg.chains.items():
        yield Fact("chain", (name, chain.scheme))
        for i, field in enumerate(chain.relation):
            yield Fact("chain_relation", (name, field, i))
        if chain.sibling:
            yield Fact("chain_sibling", (name, chain.sibling))
        if chain.invariant:
            yield Fact("chain_invariant", (name, chain.invariant))


def document_facts(cfg=None) -> Iterator[Fact]:
    """What every document says, as facts."""
    cfg = cfg or current()
    for prefix, scheme in cfg.schemes.items():
        contract = for_scheme(scheme)
        references = [f for f in contract.fields if f.reference is not None]
        for adr in load_scheme(scheme):
            yield Fact("doc", (adr.code, prefix))
            yield Fact("status", (adr.code, adr.status_value))
            for code, field, i, value in field_rows(adr.code, adr.meta):
                yield Fact("value", (code, field, i, value))
            for field in references:
                for target in codes_of(field, adr.meta.get(field.name)):
                    yield Fact("ref_value", (adr.code, field.name, target))
    from . import edges
    for edge in edges.graph().edges:
        yield Fact("edge", (edge.source, edge.relation, edge.target))


def facts(cfg=None) -> list[Fact]:
    """Every fact about the record, sorted, without repeats."""
    cfg = cfg or current()
    return sorted(set(schema_facts(cfg)) | set(document_facts(cfg)))


def program(found: Iterable[Fact]) -> str:
    """Facts as clingo program text, one per line."""
    return "".join(f.text() + "\n" for f in found)


def run(*predicates: str) -> None:
    """Print the record as clingo facts, one per line.

    With predicate names (`luria facts doc edge`), only those. The output is
    a program clingo reads as it stands, so the record can be queried without
    luria: `luria facts > record.lp` and add rules of your own."""
    found = facts()
    if predicates:
        wanted = set(predicates)
        found = [f for f in found if f.predicate in wanted]
    print(program(found), end="")
