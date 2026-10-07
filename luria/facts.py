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
    holds(C, F, V).               each value as a set member: stripped, and a
                                  derived alias read as the code it names —
                                  what two documents compare when a relation
                                  asserts they share a value (`members`)
    edge(C, R, T).                the typed graph `luria/edges.py` derives

    head_value(S, F, C, X).       what document C of scheme S declared in a
                                  converse-paired field F at HEAD, as the
                                  text said it — the baseline the converse
                                  fixer reads change against. Absent with no
                                  repository or no commit.

Every fact comes through the record's own readers — `load_scheme`, the
compiled contract, `edges.graph` — never a second parse, for the reason
`luria export` gives (DP-4).
"""
from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

import re
import subprocess
from pathlib import Path

from .adr_index import load_scheme, parse_frontmatter
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


def members(raw) -> set[str]:
    """A frontmatter value as a set of members: a scalar is a set of one, so
    equality and intersection are the same test, and a derived alias and the
    code it names are one value (#219) — or two documents in one area would
    share nothing when one wrote `AREA-runtime` and the other `AREA-001`.

    The one definition: the invariant check compares these, and so do the
    rules, through `holds/3`."""
    if raw in (None, ""):
        return set()
    values = raw if isinstance(raw, list) else [raw]
    from .aliases import derived_code
    return {derived_code(str(v)) or str(v).strip()
            for v in values if v not in (None, "")}


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
            for field, raw in adr.meta.items():
                for member in members(raw):
                    yield Fact("holds", (adr.code, field, member))
            for field in references:
                for target in codes_of(field, adr.meta.get(field.name)):
                    yield Fact("ref_value", (adr.code, field.name, target))
    from . import edges
    for edge in edges.graph().edges:
        yield Fact("edge", (edge.source, edge.relation, edge.target))


def listed(value) -> list[str]:
    """Codes from a raw frontmatter value, list or scalar. Deliberately not
    contract-resolved: HEAD's config is not necessarily this one's, and all
    that is wanted from the baseline is what the text said."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value]
    return [str(value).strip()]


def _paired_fields(cfg) -> dict[str, set[str]]:
    """Per scheme, the fields a declared converse pair reads on that side:
    the field on its own scheme, the converse on each scheme it names."""
    out: dict[str, set[str]] = {}
    for prefix, scheme in cfg.schemes.items():
        for ref in scheme.references:
            if not ref.converse:
                continue
            out.setdefault(prefix, set()).add(ref.field)
            for far in ref.scheme:
                if far in cfg.schemes:
                    out.setdefault(far, set()).add(ref.converse)
    return out


def head_facts(cfg=None) -> list[Fact]:
    """What each document declared at HEAD in the fields a converse pair
    reads. Narrowed with `git grep`, because the answer only depends on
    documents that declared such a field, which is a handful of a corpus.

    No baseline at all — no repository, or no commit yet — is no facts, not
    a partial set: the fixer reads that as "nothing changed"."""
    cfg = cfg or current()
    out: list[Fact] = []
    for prefix, fields in sorted(_paired_fields(cfg).items()):
        args = ["git", "grep", "-l", "-E",
                f"^({'|'.join(sorted(re.escape(f) for f in fields))}):",
                "HEAD", "--", str(cfg.schemes[prefix].dir)]
        found = subprocess.run(args, cwd=cfg.root, capture_output=True,
                               text=True)
        if found.returncode > 1:      # 1 is "no matches", which is an answer
            return []
        for line in found.stdout.splitlines():
            _, _, rel = line.partition(":")
            blob = subprocess.run(["git", "show", f"HEAD:{rel}"],
                                  cwd=cfg.root, capture_output=True, text=True)
            if blob.returncode != 0:
                continue
            meta = parse_frontmatter(blob.stdout)[0]
            for field in fields:
                for code in listed(meta.get(field)):
                    out.append(Fact("head_value",
                                    (prefix, field, Path(rel).stem, code)))
    return out


def _head(cfg) -> str:
    done = subprocess.run(["git", "rev-parse", "-q", "--verify", "HEAD"],
                          cwd=cfg.root, capture_output=True, text=True)
    return done.stdout.strip()


def fingerprint(cfg=None) -> tuple:
    """What the facts depend on, cheaply: the commit HEAD names, and every
    document's path, mtime and size. Listing the scheme directories is a few
    hundred `stat`s; reading the documents is what costs, and this is what
    says whether to."""
    cfg = cfg or current()
    out = [("HEAD", _head(cfg), 0)]
    for scheme in cfg.schemes.values():
        for path in [*scheme.documents().values(),
                     *scheme.temp_documents().values()]:
            st = path.stat()
            out.append((str(path), st.st_mtime_ns, st.st_size))
    return tuple(sorted(out))


# One run asks for the facts many times — every relation a chain or a check
# reads — and a fixer may write documents between asks. So the facts are
# kept against the config they were read under (held, so its identity cannot
# be reused) and the fingerprint of the documents; either changing reads
# them again.
_memo: dict = {"cfg": None, "print": None, "facts": None}


def facts(cfg=None) -> list[Fact]:
    """Every fact about the record, sorted, without repeats."""
    cfg = cfg or current()
    stamp = fingerprint(cfg)
    if _memo["cfg"] is cfg and _memo["print"] == stamp:
        return _memo["facts"]
    from .timing import timed
    with timed("facts") as t:
        found = sorted(set(schema_facts(cfg)) | set(document_facts(cfg))
                       | set(head_facts(cfg)))
        t["note"] = f"{len(found)} facts"
    _memo.update(cfg=cfg, print=stamp, facts=found)
    return found


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
