#!/usr/bin/env python3
"""A relation and its converse: the fact stated once, written where it is
true (#180).

A reference field is a typed relation, and most relations have a name for
being read backwards. If A `extends` B then B is `extended_by` A. If A is
`compared_against` B then B is compared against A — the same relation, which
is what makes it symmetric. So symmetry is not a separate kind of thing; it
is the case where a relation's converse is itself.

    [luria.schemes.LIT.references]
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

from .adr_index import Adr, load_scheme, parse_frontmatter
from .config import current
from .contract import for_scheme, values_of


@dataclass(frozen=True)
class Repair:
    """One edit that makes a declared pair agree: add `code` to `path`'s
    `field`, or remove it. Which of the two depends on what *changed* — see
    `_intents`."""
    path: Path
    field: str
    code: str
    op: str = "add"


def pairs() -> list[tuple[str, str, str]]:
    """Every declared converse, as (scheme, field, converse field).

    Both directions appear, so a caller iterating this sees each edge from
    the side that declares it. A self-converse relation appears once."""
    out = []
    for prefix, scheme in current().schemes.items():
        for ref in scheme.references:
            if ref.converse:
                out.append((prefix, ref.field, ref.converse))
    return sorted(set(out))


def _codes(doc: Adr, name: str, contract) -> list[str]:
    """The codes one relation field holds. A shape the contract rejects is
    the lint's finding, not this reading's."""
    spec = next((f for f in contract.fields if f.name == name), None)
    if spec is None:
        return []
    return [str(v).strip() for v in (values_of(spec, doc.meta.get(name)) or [])]


def _held(prefix: str) -> tuple[dict[str, Adr], dict[str, dict[str, set[str]]]]:
    """Every document of one scheme, and what each declares in every field
    that has a converse — filtered to codes that land, since a reference
    outside the scheme is the contract's finding rather than an edge here."""
    scheme = current().schemes[prefix]
    docs = {d.code: d for d in load_scheme(scheme)}
    contract = for_scheme(scheme)
    fields = {f for p, f, _ in pairs() if p == prefix}
    held = {f: {c: {x for x in _codes(d, f, contract) if x in docs}
                for c, d in docs.items()} for f in sorted(fields)}
    return docs, held


def edges(prefix: str, field: str) -> dict[str, set[str]]:
    """One relation as declared from *either* side: what each document holds
    in `field`, plus what other documents name it in the converse.

    The union is why a one-sided declaration still reads correctly before
    anyone runs the fixer. Completion makes the two agree on disk; this makes
    them agree in every reading meanwhile. A field with no declared converse
    is simply itself."""
    scheme = current().schemes[prefix]
    docs = {d.code: d for d in load_scheme(scheme)}
    contract = for_scheme(scheme)

    def read(name: str) -> dict[str, set[str]]:
        return {c: {x for x in _codes(d, name, contract) if x in docs}
                for c, d in docs.items()}

    out = read(field)
    back = converse_of(prefix, field)
    if back:
        for code, others in read(back).items():
            for other in others:
                out[other].add(code)
    return out


def converse_of(prefix: str, field: str) -> str:
    """The field holding `field` read backwards, or "" if none is declared."""
    return next((c for p, f, c in pairs() if p == prefix and f == field), "")


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


def _committed(prefix: str, field: str, back: str) -> tuple[set, set] | None:
    """The two edge sets as HEAD held them: declared forward, and declared
    from the converse side. `None` when there is no baseline."""
    texts = _at_head(prefix, {field, back})
    if texts is None:
        return None
    cfg, held = current(), {}
    for rel, text in texts.items():
        meta = parse_frontmatter(text)[0]
        code = Path(rel).stem
        held[code] = {f: _listed(meta.get(f)) for f in (field, back)}
    forward = {(a, b) for a, f in held.items() for b in f[field]}
    reverse = {(a, b) for b, f in held.items() for a in f[back]}
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


def _intents(prefix: str, field: str, back: str, docs: dict, held: dict
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
    base = _committed(prefix, field, back)
    was_f, was_b = base if base else (set(), set())
    repairs: list[Repair] = []
    clashes: list[tuple[str, str]] = []
    # A directed relation asserted both ways is a contradiction whichever
    # fields carry it: A extends B and B extends A leaves neither earlier.
    # Completing it would only write the second half of the cycle.
    both_ways = ({e for e in now_f | now_b if e[::-1] in (now_f | now_b)}
                 if field != back else set())
    for a, b in sorted(now_f | now_b | was_f | was_b):
        if a not in docs or b not in docs:
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
                repairs.append(Repair(docs[b].path, back, a, "remove"))
        else:
            if edge not in now_f:
                repairs.append(Repair(docs[a].path, field, b, "add"))
            if edge not in now_b:
                repairs.append(Repair(docs[b].path, back, a, "add"))
    return repairs, clashes


def _mutual(field: str, back: str, held: dict,
            edge: tuple[str, str]) -> bool:
    """Whether this clash is the relation asserted in both directions, as
    opposed to one side withdrawn while the other was asserted."""
    if field == back:
        return False
    now_f, now_b = _now(field, back, held)
    return edge[::-1] in (now_f | now_b)


def completions() -> list[Repair]:
    """Every edit a declared pair needs, deduplicated and ordered so a run is
    reproducible. Empty when every pair already agrees."""
    out: list[Repair] = []
    for prefix, field, back in pairs():
        docs, held = _held(prefix)
        out += _intents(prefix, field, back, docs, held)[0]
    return sorted(set(out), key=lambda r: (str(r.path), r.field, r.code, r.op))


def rows() -> list[str]:
    """A declared pair the two documents do not agree on, said in the
    record's own paths and naming what the fixer will do about it."""
    cfg = current()
    found: list[str] = []
    for prefix, field, back in pairs():
        docs, held = _held(prefix)
        repairs, clashes = _intents(prefix, field, back, docs, held)
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


def _add_to_field(text: str, name: str, code: str) -> str:
    """Add one code to a list-valued frontmatter field, creating the field
    when it is absent and widening a scalar rather than replacing it.

    A `many` field accepts one code written as a scalar (a list of one), so
    the scalar case is real and overwriting it would silently delete a
    relation — the quiet kind of loss this module exists to end."""
    if not text.startswith("---\n"):
        return text
    end = text.index("\n---\n", 3) + 1
    head, rest = text[4:end], text[end:]
    lines = head.splitlines(keepends=True)
    out, at, done = [], 0, False
    while at < len(lines):
        line = lines[at]
        if not done and re.match(rf"^{re.escape(name)}\s*:", line):
            value = line.split(":", 1)[1].strip()
            at += 1
            items = []
            while at < len(lines) and lines[at].startswith("- "):
                items.append(lines[at])
                at += 1
            out.append(f"{name}:\n")
            if value:
                out.append(f"- {value}\n")
            out.extend(items)
            out.append(f"- {code}\n")
            done = True
            continue
        out.append(line)
        at += 1
    if not done:
        out.append(f"{name}:\n- {code}\n")
    return "---\n" + "".join(out) + rest


def _drop_from_field(text: str, name: str, code: str) -> str:
    """Take one code out of a list-valued frontmatter field, removing the
    field itself when that was its last entry.

    A field left standing with nothing under it is not a relation held by
    nobody — it is invalid frontmatter, and the next reader gets a parse
    error instead of the tidy record the deletion was meant to leave."""
    if not text.startswith("---\n"):
        return text
    end = text.index("\n---\n", 3) + 1
    head, rest = text[4:end], text[end:]
    lines, out, at = head.splitlines(keepends=True), [], 0
    while at < len(lines):
        line = lines[at]
        if not re.match(rf"^{re.escape(name)}\s*:", line):
            out.append(line)
            at += 1
            continue
        value = line.split(":", 1)[1].strip()
        at += 1
        kept = [value] if value else []
        while at < len(lines) and lines[at].startswith("- "):
            kept.append(lines[at][2:].strip())
            at += 1
        kept = [k for k in kept if k != code]
        if kept:
            out.append(f"{name}:\n")
            out += [f"- {k}\n" for k in kept]
    return "---\n" + "".join(out) + rest


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
                text = (_add_to_field(text, entry.field, entry.code)
                        if entry.op == "add"
                        else _drop_from_field(text, entry.field, entry.code))
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
              for f in (chain.relation, chain.sibling)
              if f and path.parent == cfg.schemes[chain.scheme].dir}
    fields |= {f for prefix, field, back in pairs()
               for f in (field, back)
               if path.parent == cfg.schemes[prefix].dir}
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
