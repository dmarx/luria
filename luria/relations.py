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

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .adr_index import Adr, load_scheme, parse_frontmatter, read_document
from . import store
from .config import current
from .contract import (ANY_SCHEME, for_scheme, resolvable, values_of,
                       violations)
from .field_edit import add_to_field, drop_from_field


@dataclass(frozen=True)
class Repair:
    """One edit that makes a declared pair agree: add `code` to `path`'s
    `field`, or remove it. Which of the two depends on what *changed* — see
    `_intents`."""
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
                out.append((prefix, ref.field, ref.converse, ref.scheme))
    return sorted(set(out))


def _codes(doc: Adr, name: str, contract) -> list[str]:
    """The codes one relation field holds. A shape the contract rejects is
    the lint's finding, not this reading's."""
    spec = next((f for f in contract.fields if f.name == name), None)
    if spec is None:
        return []
    return [str(v).strip() for v in (values_of(spec, doc.meta.get(name)) or [])]


def _documents(prefix: str) -> dict[str, Adr]:
    """Every document of one scheme, by code."""
    return {d.code: d for d in load_scheme(current().schemes[prefix])}


def _reads(owner: str, field: str, target: dict[str, Adr]) -> dict[str, set[str]]:
    """What each document of `owner` declares in `field`, filtered to codes
    that land in `target` — the scheme whose codes the field holds.

    Filtering against the *target* rather than the owner is what makes this
    work when the relation crosses: a reference outside the scheme it names
    is the contract's finding, not an edge here, and which scheme that is
    depends on the field."""
    scheme = current().schemes[owner]
    contract = for_scheme(scheme)
    return {c: {x for x in _codes(d, field, contract) if x in target}
            for c, d in _documents(owner).items()}


def _held(prefix: str, field: str, back: str, far: str
          ) -> tuple[dict[str, Adr], dict[str, Adr], dict[str, dict[str, set[str]]]]:
    """Both sides of one pair: the near documents, the far documents, and
    what each side declares. For a relation that does not cross, the two
    document sets are the same object and this is the old behaviour."""
    near_docs = _documents(prefix)
    far_docs = near_docs if far == prefix else _documents(far)
    held = {field: _reads(prefix, field, far_docs),
            back: _reads(far, back, near_docs)}
    return near_docs, far_docs, held


def edges(prefix: str, field: str) -> dict[str, set[str]]:
    """One relation as declared from *either* side: what each document holds
    in `field`, plus what other documents name it in the converse.

    The union is why a one-sided declaration still reads correctly before
    anyone runs the fixer. Completion makes the two agree on disk; this makes
    them agree in every reading meanwhile. A field with no declared converse
    is simply itself."""
    spec = next((r for r in current().schemes[prefix].references
                 if r.field == field), None)
    far = spec.scheme if spec else prefix
    docs = _documents(prefix)
    far_docs = docs if far == prefix else _documents(far)

    out = _reads(prefix, field, far_docs)
    back = converse_of(prefix, field)
    if back:
        # The far side names this one, so its reading inverts into this
        # scheme's code space whether or not the relation crosses.
        for code, others in _reads(far, back, docs).items():
            for other in others:
                out.setdefault(other, set()).add(code)
    return out


def converse_of(prefix: str, field: str) -> str:
    """The field holding `field` read backwards, or "" if none is declared."""
    return next((c for p, f, c, _ in pairs() if p == prefix and f == field), "")


def converse_scheme_of(prefix: str, field: str) -> str:
    """Which scheme that converse field lives on — `prefix` itself unless the
    relation crosses."""
    return next((s for p, f, _, s in pairs() if p == prefix and f == field), "")


def _contradictions(field: str, back: str, held: dict) -> set[tuple[str, str]]:
    """Pairs already standing in both directions of one relation.

    Two shapes, and only for a directed pair — for a symmetric relation both
    documents holding the fact is the *completed* state, not a clash. A
    document naming another in both `field` and its converse says that other
    is at once before and after it; two documents each naming the other in
    `field` say the same thing from opposite ends. Either way nothing is
    missing: two incompatible things are present."""
    if back == field:
        return set()
    clash: set[tuple[str, str]] = set()
    forward, backward = held[field], held[back]
    for code, others in forward.items():
        for other in others:
            if other in backward.get(code, ()) or code in forward.get(other, ()):
                clash.add((min(code, other), max(code, other)))
    return clash


def _at_head(prefix: str, fields: set[str]) -> dict[str, str] | None:
    """The committed text of every document of this scheme that declared one
    of these fields at HEAD, keyed by path relative to the root.

    `None` means there is no baseline to compare against — no repository, or
    no commit yet. Narrowed with `git grep` because the answer only depends
    on documents that declared a relation, which is a handful of a corpus."""
    cfg = current()
    if not fields:
        return {}
    args = ["git", "grep", "-l", "-E",
            f"^({'|'.join(sorted(re.escape(f) for f in fields))}):",
            "HEAD", "--", str(cfg.schemes[prefix].dir)]
    found = subprocess.run(args, cwd=cfg.root, capture_output=True, text=True)
    if found.returncode > 1:          # 1 is "no matches", which is an answer
        return None
    out = {}
    for line in found.stdout.splitlines():
        _, _, rel = line.partition(":")
        blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=cfg.root,
                              capture_output=True, text=True)
        if blob.returncode == 0:
            out[rel] = blob.stdout
    return out


def _side_at_head(prefix: str, field: str) -> dict[str, list[str]] | None:
    """What each of one scheme's documents declared in one field at HEAD."""
    texts = _at_head(prefix, {field})
    if texts is None:
        return None
    return {Path(rel).stem: _listed(parse_frontmatter(text)[0].get(field))
            for rel, text in texts.items()}


def _committed(prefix: str, field: str, back: str,
               far: str) -> tuple[set, set] | None:
    """The two edge sets as HEAD held them: declared forward, and declared
    from the converse side. `None` when there is no baseline.

    Each side is read out of its own scheme's directory, which is the same
    directory twice unless the relation crosses."""
    near = _side_at_head(prefix, field)
    far_held = _side_at_head(far, back)
    if near is None or far_held is None:
        return None
    forward = {(a, b) for a, codes in near.items() for b in codes}
    reverse = {(a, b) for b, codes in far_held.items() for a in codes}
    return forward, reverse


def _listed(value) -> list[str]:
    """Codes from a raw frontmatter value, list or scalar. Deliberately not
    contract-resolved: HEAD's config is not necessarily this one's, and all
    that is wanted here is what the text said."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value]
    return [str(value).strip()]


def _now(field: str, back: str, held: dict) -> tuple[set, set]:
    """The same two edge sets as the working tree holds them."""
    forward = {(a, b) for a, others in held[field].items() for b in others}
    reverse = {(a, b) for b, others in held[back].items() for a in others}
    return forward, reverse


def _intents(prefix: str, field: str, back: str, far: str,
             docs: dict, far_docs: dict, held: dict
             ) -> tuple[list[Repair], list[tuple[str, str]]]:
    """What to do about every edge either side declares, and the conflicts.

    The rule is about *change*, not about state. A one-sided edge means one
    of two opposite things — somebody wrote it and the other side has not
    caught up, or somebody deleted it and the other side is stale — and the
    working tree holds neither answer. What changed since the last commit
    does.

    Added on either side wins by being written to both. Removed on either
    side wins by being taken from both. Added on one side while removed on
    the other is two deliberate edits that contradict: reported, never
    resolved, because writing either loses the other.

    An edge nothing has touched falls through to adding, which is what a
    corpus predating the fixer needs. That reading can be wrong — a deletion
    committed before the fixer ran looks like nothing changed — but it is
    self-correcting: delete it once more and the deletion *is* a change."""
    now_f, now_b = _now(field, back, held)
    base = _committed(prefix, field, back, far)
    was_f, was_b = base if base else (set(), set())
    repairs: list[Repair] = []
    clashes: list[tuple[str, str]] = []
    # A directed relation asserted both ways is a contradiction whichever
    # fields carry it: A extends B and B extends A leaves neither earlier.
    # Completing it would only write the second half of the cycle.
    #
    # A crossing relation cannot express one: every edge runs from a document
    # of one scheme to a document of another, so the reversed edge is never in
    # the set. Guarded on the scheme rather than left to fall out, because
    # "it happens not to match" and "it cannot match" read the same in a set
    # comprehension and only the second is a reason not to check.
    both_ways = ({e for e in now_f | now_b if e[::-1] in (now_f | now_b)}
                 if field != back and far == prefix else set())
    for a, b in sorted(now_f | now_b | was_f | was_b):
        if a not in docs or b not in far_docs:
            continue
        edge = (a, b)
        if edge in both_ways:
            if a < b:
                clashes.append(edge)
            continue
        added = ((edge in now_f and edge not in was_f)
                 or (edge in now_b and edge not in was_b))
        gone = ((edge in was_f and edge not in now_f)
                or (edge in was_b and edge not in now_b))
        if added and gone:
            clashes.append(edge)
        elif gone:
            if edge in now_f:
                repairs.append(Repair(docs[a].path, field, b, "remove"))
            if edge in now_b:
                repairs.append(Repair(far_docs[b].path, back, a, "remove"))
        else:
            if edge not in now_f:
                repairs.append(Repair(docs[a].path, field, b, "add"))
            if edge not in now_b:
                repairs.append(Repair(far_docs[b].path, back, a, "add"))
    return repairs, clashes


def _mutual(field: str, back: str, held: dict,
            edge: tuple[str, str]) -> bool:
    """Whether this clash is the relation asserted in both directions, as
    opposed to one side withdrawn while the other was asserted."""
    if field == back:
        return False
    now_f, now_b = _now(field, back, held)
    return edge[::-1] in (now_f | now_b)


def _applied(meta: dict, entries: list[Repair]) -> dict:
    """`meta` as it would read after these repairs, without touching disk."""
    out = dict(meta)
    for entry in entries:
        held = _listed(out.get(entry.field))
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
        known = {f.reference: resolvable(f.reference) for f in contract.fields
                 if f.reference and f.reference != ANY_SCHEME}
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
    for prefix, field, back, far in pairs():
        docs, far_docs, held = _held(prefix, field, back, far)
        safe, blocked = _blocked(
            prefix, docs,
            _intents(prefix, field, back, far, docs, far_docs, held)[0])
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
    for prefix, field, back, far in pairs():
        docs, far_docs, held = _held(prefix, field, back, far)
        repairs, clashes = _intents(prefix, field, back, far,
                                    docs, far_docs, held)
        repairs = _blocked(prefix, docs, repairs)[0]
        for a, b in clashes:
            if _mutual(field, back, held, (a, b)):
                found.append(
                    f"{cfg.rel(docs[a].path)}: {a} and {b} each stand before "
                    f"the other in `{field}`/`{back}` — one of the two "
                    f"declarations is wrong and the data does not say which")
            else:
                found.append(
                    f"{cfg.rel(docs[a].path)}: `{field}: {b}` was withdrawn "
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
            text = store.read_text(path)
            for entry in entries:
                text = (add_to_field(text, entry.field, entry.code)
                        if entry.op == "add"
                        else drop_from_field(text, entry.field, entry.code))
            store.write_text(path, text)
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
