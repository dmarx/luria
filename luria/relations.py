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
from dataclasses import dataclass
from pathlib import Path

from .adr_index import Adr, load_scheme
from .config import current
from .contract import for_scheme, values_of


@dataclass(frozen=True)
class Completion:
    """One back-reference a declared pair is missing: write `code` into
    `path`'s `field`."""
    path: Path
    field: str
    code: str


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


def completions() -> list[Completion]:
    """Every back-reference a declared pair is missing, deduplicated and
    ordered so a run is reproducible.

    A contradiction is skipped rather than completed: when a document names
    another in both directions of one pair, nothing is absent — two
    incompatible things are present, and choosing between them is a person's
    job."""
    out: list[Completion] = []
    for prefix, field, back in pairs():
        docs, held = _held(prefix)
        clash = _contradictions(field, back, held)
        for code in sorted(docs):
            for other in sorted(held[field][code]):
                if (min(code, other), max(code, other)) in clash:
                    continue
                if code not in held[back].get(other, set()):
                    out.append(Completion(docs[other].path, back, code))
    return sorted(set(out), key=lambda c: (str(c.path), c.field, c.code))


def rows() -> list[str]:
    """A declared pair that only one document holds, plus the contradictions
    nothing can repair — reported in the record's own paths."""
    cfg = current()
    found: list[str] = []
    for prefix, field, back in pairs():
        docs, held = _held(prefix)
        clash = _contradictions(field, back, held)
        for both in sorted(clash):
            one, two = both
            found.append(
                f"{cfg.rel(docs[one].path)}: {one} and {two} each stand "
                f"before the other in `{field}`/`{back}` — one of the two "
                f"declarations is wrong and the data does not say which")
        for code in sorted(docs):
            for other in sorted(held[field][code]):
                if (min(code, other), max(code, other)) in clash:
                    continue
                if code not in held[back].get(other, set()):
                    found.append(
                        f"{cfg.rel(docs[other].path)}: {code} declares "
                        f"`{field}: {other}` and {other} does not declare "
                        f"`{back}: {code}` — a relation and its converse are "
                        f"one fact (`luria link --fix` writes the other side)")
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


def complete(fix: bool = False) -> list[Completion]:
    """Write every missing back-reference; report them without `fix`.

    Grouped per file so a document missing several gains them in one write."""
    todo = completions()
    if fix:
        by_path: dict[Path, list[Completion]] = {}
        for entry in todo:
            by_path.setdefault(entry.path, []).append(entry)
        for path, entries in by_path.items():
            text = path.read_text(encoding="utf-8")
            for entry in entries:
                text = _add_to_field(text, entry.field, entry.code)
            path.write_text(text, encoding="utf-8")
    return todo
