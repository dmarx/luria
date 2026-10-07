#!/usr/bin/env python3
"""A relation and its converse: the fact stated once, written where it is
true (#178); a relation being removed propagates too (#180).

A reference field is a typed relation, and most relations have a name for
being read backwards. If A `extends` B then B is `extended_by` A. If A is
`compared_against` B then B is compared against A — the same relation, which
is what makes it symmetric. So symmetry is not a separate kind of thing; it
is the case where a relation's converse is itself.

    `schemes.LIT.references`
    extends          = { scheme = "LIT", many = true, converse = "extended_by" }
    extended_by      = { scheme = "LIT", many = true, converse = "extends" }
    compared_against = { scheme = "LIT", many = true, converse = "compared_against" }

**The declaration is what licenses the write.** Absent a declared converse
nothing is inferred and nothing is reported, because the reverse edge of an
undeclared relation is a guess, and a guess written into the record is worse
than an absence — an absence at least looks like one.

**What is never valid is mirroring a relation into its own field.** `extends`
on the document A extends would assert that B extends A, which is false, and
shows up downstream as a cycle. The first version of this mechanism read that
constraint as "directed relations must never be completed" and refused to
touch them at all. That was wrong by one step: the constraint is about the
*field written into*, not about the relation's direction. A directed relation
completes perfectly well — into its converse, where the fact is true.

So the author states the relation once, on whichever document they were
holding, and `luria link --fix` writes the other side. A one-sided pair stays
a finding, the way `legacy-spellings` is a finding with a fixer named in it.
The one thing the fixer will not touch is a *contradiction* — a document
standing in both directions of the same pair to another — because there is
no side to write and which reading was meant is not in the data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .adr_index import Adr, load_scheme, read_document
from .config import current
from .contract import for_scheme, resolvable, targets, violations
from .facts import listed
from .aliases import readable
from .field_edit import add_to_field, drop_from_field


@dataclass(frozen=True)
class Repair:
    """One edit that makes a declared pair agree: add `code` to `path`'s
    `field`, or remove it. Which of the two depends on what *changed* — see
    `_decided`."""
    path: Path
    field: str
    code: str
    op: str = "add"


def pairs() -> list[tuple[str, str, str, str]]:
    """Every declared converse, as (scheme, field, converse field, converse
    scheme).

    The fourth element is where a relation's far side lives, and it is the
    declaring scheme only when the relation does not cross one:
    `SOTA.introduced_by` holds `LIT` codes, so its converse `introduces` is a
    field on `LIT` (#253).

    Both directions appear, so a caller iterating this sees each edge from
    the side that declares it. A self-converse relation appears once."""
    out = []
    for prefix, scheme in current().schemes.items():
        for ref in scheme.references:
            if ref.converse:
                # One pair per scheme the field may name (#160): each target
                # holds its own half, and completing one says nothing about
                # the others.
                out.extend((prefix, ref.field, ref.converse, far)
                           for far in ref.scheme)
    return sorted(set(out))


def _documents(prefix: str) -> dict[str, Adr]:
    """Every document of one scheme, by code."""
    return {d.code: d for d in load_scheme(current().schemes[prefix])}


def edges(prefix: str, field: str) -> dict[str, set[str]]:
    """One relation as declared from *either* side: what each document holds
    in `field`, plus what other documents name it in the converse.

    The union is why a one-sided declaration still reads correctly before
    anyone runs the fixer. Completion makes the two agree on disk; this makes
    them agree in every reading meanwhile. A field with no declared converse
    is simply itself.

    Decided by `luria/logic/relations.lp` (`held/4`), over every relation at
    once; this keys the answer the way callers read it — every document of
    the scheme, related to nothing or to something."""
    from . import logic
    out: dict[str, set[str]] = {d.code: set()
                                for d in _documents(prefix).values()}
    for s, f, code, other in logic.derive("relations").get("held", ()):
        if s == prefix and f == field:
            out.setdefault(code, set()).add(other)
    return out


def converse_of(prefix: str, field: str) -> str:
    """The field holding `field` read backwards, or "" if none is declared."""
    return next((c for p, f, c, _ in pairs() if p == prefix and f == field), "")


Pair = tuple[str, str, str, str]


def _decided() -> dict[Pair, tuple[list[Repair],
                                  list[tuple[Path, str, str, str]]]]:
    """What to do about every edge either side of each pair declares, and
    the conflicts — per pair, as (repairs, clashes).

    The rule is about *change*, not about state. A one-sided edge means one
    of two opposite things — somebody wrote it and the other side has not
    caught up, or somebody deleted it and the other side is stale — and the
    working tree holds neither answer. What changed since the last commit
    does.

    Added on either side wins by being written to both. Removed on either
    side wins by being taken from both. Added on one side while removed on
    the other is two deliberate edits that contradict: reported, never
    resolved, because writing either loses the other. A directed relation
    asserted both ways is a contradiction whichever fields carry it — A
    extends B and B extends A leaves neither earlier — and completing it
    would only write the second half of the cycle.

    An edge nothing has touched falls through to adding, which is what a
    corpus predating the fixer needs. That reading can be wrong — a deletion
    committed before the fixer ran looks like nothing changed — but it is
    self-correcting: delete it once more and the deletion *is* a change.

    Decided by `luria/logic/converse.lp` over the working tree and HEAD's
    `head_value/4`. The two sides of a pair are kept apart by which side
    they are, never by field name, so a symmetric relation that crosses
    schemes reads both of its halves (#358). This turns the answer into
    edits in the order the fixer has always made them: by edge, the near
    side first."""
    from . import logic
    derived = logic.derive("converse")
    docs: dict[str, Adr] = {}
    for prefix in {p[i] for p in pairs() for i in (0, 3)}:
        if prefix in current().schemes:
            docs.update(_documents(prefix))
    out: dict[Pair, tuple[list, list]] = {}
    for *pair, a, x, side, op in sorted(derived.get("repair", ()),
                                         key=lambda r: (r[:6], r[6] != "near")):
        prefix, field, back, far = pair
        repair = (Repair(docs[a].path, field, x, op) if side == "near"
                  else Repair(docs[x].path, back, a, op))
        out.setdefault(tuple(pair), ([], []))[0].append(repair)
    for *pair, a, x, kind in sorted(derived.get("clash", ())):
        out.setdefault(tuple(pair), ([], []))[1].append(
            (docs[a].path, a, x, kind))
    return out


def _applied(meta: dict, entries: list[Repair]) -> dict:
    """`meta` as it would read after these repairs, without touching disk."""
    out = dict(meta)
    for entry in entries:
        held = listed(out.get(entry.field))
        if entry.op == "add":
            held = held + [entry.code]
        else:
            held = [c for c in held if c != entry.code]
        if held:
            out[entry.field] = held
        else:
            out.pop(entry.field, None)
    return out


def _contract_for(path: Path):
    """The contract of whichever scheme owns this document. A repair can now
    land in either of a pair's two schemes, so the contract that judges it is
    a property of the file, not of the relation."""
    cfg = current()
    for scheme in cfg.schemes.values():
        if path.parent == scheme.dir:
            return for_scheme(scheme)
    return None


def _blocked(prefix: str, docs: dict, repairs: list[Repair]
             ) -> tuple[list[Repair], list[tuple[Repair, str]]]:
    """Split repairs into the ones that are safe to write and the ones that
    would break the document they land in.

    The fixer edits frontmatter, and frontmatter is what the contract judges,
    so an edit can move a document from satisfying its scheme to violating
    it — a back-reference added into a field group that allows only one of
    two fields, or a stale one removed out of a field the status requires.
    Neither is the author's mistake and neither should be made silently.

    Only *new* violations block. A document already in breach somewhere else
    still gets its back-references, or one unrelated mistake would freeze
    every relation it stands in."""
    by_path: dict[Path, list[Repair]] = {}
    for entry in repairs:
        by_path.setdefault(entry.path, []).append(entry)
    safe, held_back = [], []
    for path, entries in by_path.items():
        contract = _contract_for(path)
        if contract is None:
            safe += entries
            continue
        # `superseded_by` names any scheme, which has no one set of codes to
        # resolve against — the same exemption the lint makes.
        known = {t: resolvable(t) for f in contract.fields
                 for t in targets(f)}
        rel = current().rel(path)
        meta = read_document(path)[0]
        was = set(violations(contract, rel, meta, known))
        now = violations(contract, rel, _applied(meta, entries), known)
        fresh = [v for v in now if v not in was]
        if fresh:
            held_back += [(e, fresh[0]) for e in entries]
        else:
            safe += entries
    return safe, held_back


def _all_repairs() -> tuple[list[Repair], list[tuple[Repair, str]]]:
    """Every edit the declared pairs need, and every one held back."""
    out: list[Repair] = []
    stopped: list[tuple[Repair, str]] = []
    for pair, (repairs, _) in sorted(_decided().items()):
        safe, blocked = _blocked(pair[0], {}, repairs)
        out += safe
        stopped += blocked
    return out, stopped


def completions() -> list[Repair]:
    """Every edit a declared pair needs and the contract permits, ordered so
    a run is reproducible. Empty when every pair already agrees."""
    out = _all_repairs()[0]
    return sorted(set(out), key=lambda r: (str(r.path), r.field, r.code, r.op))


def rows() -> list[str]:
    """A declared pair the two documents do not agree on, said in the
    record's own paths and naming what the fixer will do about it."""
    cfg = current()
    found: list[str] = []
    for entry, breach in _all_repairs()[1]:
        did = "writing" if entry.op == "add" else "removing"
        found.append(
            f"{cfg.rel(entry.path)}: {did} `{entry.field}: {entry.code}` "
            f"would leave this document in breach of its scheme "
            f"({breach.split(': ', 1)[-1]}), so the pair is left one-sided — "
            f"the relation and the contract disagree, and which gives is a "
            f"person's call")
    for (prefix, field, back, far), (repairs, clashes) in sorted(
            _decided().items()):
        repairs = _blocked(prefix, {}, repairs)[0]
        for where, a, b, kind in clashes:
            path = cfg.rel(where)
            if kind == "mutual":
                found.append(
                    f"{path}: {a} and {b} each stand before "
                    f"the other in `{field}`/`{back}` — one of the two "
                    f"declarations is wrong and the data does not say which")
            else:
                found.append(
                    f"{path}: `{field}: {b}` was withdrawn "
                    f"on one side and asserted on the other since the last "
                    f"commit — two deliberate edits contradict, and resolving "
                    f"it either way discards one of them")
        for repair in repairs:
            if repair.op == "add":
                found.append(
                    f"{cfg.rel(repair.path)}: does not declare "
                    f"`{repair.field}: {repair.code}`, which the other side "
                    f"of the pair holds — a relation and its converse are one "
                    f"fact (`luria link --fix` writes it)")
            else:
                found.append(
                    f"{cfg.rel(repair.path)}: `{repair.field}: "
                    f"{repair.code}` is stale — the other side of the pair "
                    f"was withdrawn since the last commit "
                    f"(`luria link --fix` removes it)")
    return sorted(set(found))


def complete(fix: bool = False) -> list[Repair]:
    """Make every declared pair agree; report the edits without `fix`.

    Grouped per file so a document needing several is written once."""
    todo = completions()
    if fix:
        by_path: dict[Path, list[Repair]] = {}
        for entry in todo:
            by_path.setdefault(entry.path, []).append(entry)
        for path, entries in by_path.items():
            text = path.read_text(encoding="utf-8")
            for entry in entries:
                # Written in the spelling a person would choose, and removed
                # in whichever spelling it was written: a derived alias and
                # its code are one value (#219).
                if entry.op == "add":
                    text = add_to_field(text, entry.field,
                                        readable(entry.code))
                else:
                    for spelling in {entry.code, readable(entry.code)}:
                        text = drop_from_field(text, entry.field, spelling)
            path.write_text(text, encoding="utf-8")
    return todo


def relation_spans(path, text: str) -> list[tuple[int, int]]:
    """Where a document declares its place in a line, as character spans.

    Not a citation site. `extends:` names the step this work builds on, and
    that step being retired is what a line *looks like* — a successor's
    predecessor is superseded by construction. Reporting it would hand back
    one "cites a retired document" finding per retired step in every chain,
    at the field whose entire job is to name it, and the only way to quiet
    them would be an acknowledgement comment per edge. `compared_against:`
    goes the same way: a comparison against a design that has since been
    retired stayed true when the design was retired.

    The codes are still checked — that a reference resolves, and resolves in
    the declared scheme, is the contract's business and unaffected. What is
    suppressed is only the reading of these fields as *citations*, the way a
    `formerly:` entry and a code inside a URL already are.

    Both halves of a declared pair, not just the one a chain names: the
    converse states the same fact from the far end, so exempting one and
    reporting the other would hand back a finding for every edge the fixer
    completes."""
    cfg = current()
    fields = {f for chain in cfg.chains.values()
              for f in (*chain.relation, chain.sibling)
              if f and path.parent == cfg.schemes[chain.scheme].dir}
    # Each side of a pair belongs to its own scheme's directory, which is the
    # same directory twice unless the relation crosses.
    for prefix, field, back, far in pairs():
        if path.parent == cfg.schemes[prefix].dir:
            fields.add(field)
        if path.parent == cfg.schemes[far].dir:
            fields.add(back)
    if not fields:
        return []
    spans, at, active = [], 0, False
    for line in text.splitlines(keepends=True):
        stripped = line.split(":", 1)[0]
        if active and not (line.startswith(("- ", "  ")) or not line.strip()):
            active = False
        if stripped in fields and line.rstrip().endswith(":"):
            active = True
        elif active:
            spans.append((at, at + len(line)))
        at += len(line)
    return spans
