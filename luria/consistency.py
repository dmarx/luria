# luria/consistency.py
"""Declarations that cannot mean what they say, refused when luria.yaml loads.

Every check here crosses a boundary the per-table parsers cannot see past:
a reference naming another scheme, a converse living on the far one, an
invariant both ends must hold, a chain walking a scheme's references. Each
one fails silently otherwise — a pair that never completes, a chain that
renders an empty page and an invariant that reports every edge all look
exactly like a record with nothing to say (DP-15).

Which declarations are wrong is decided by `luria/logic/consistency.lp`
(the ADR on a logic core in clingo). This module states the facts it reads,
words each refusal, and raises the first in the order the loader has always
checked them, so a config with several mistakes reports the same one first.

**Four things make a converse.** A relation's converse is the relation read
backwards: if A `extends` B then B is `extended_by` A, and symmetry is the
case where a relation is its own converse. The converse lives on the scheme
whose codes the field holds — the declaring scheme only when the relation
does not cross one (#253), and on each scheme a multi-scheme field names
(#160). It has to exist there, point back, name this field as its own
converse, and both sides have to take several codes, since either is
written into.

**An invariant needs both ends.** `invariant = "tags"` says the two
documents a relation joins share a tag, and a far scheme that cannot hold
`tags` makes every edge a finding.

**A chain is a sequence within one scheme.** Walking a relation that leaves
it once reached a document the walker had never loaded (#272); the refusal
says where the assertion belongs instead.
"""
from __future__ import annotations

from .facts import Fact


def _scheme_facts(schemes: dict) -> list[Fact]:
    from .config import nameable
    out: list[Fact] = []
    for prefix, scheme in schemes.items():
        out.append(Fact("scheme", (prefix,)))
        out += [Fact("nameable", (prefix, f)) for f in nameable(scheme)]
        for ref in scheme.references:
            out.append(Fact("ref", (prefix, ref.field)))
            out += [Fact("ref_target", (prefix, ref.field, t))
                    for t in ref.scheme]
            if ref.converse:
                out.append(Fact("ref_converse",
                                (prefix, ref.field, ref.converse)))
            if ref.many:
                out.append(Fact("ref_many", (prefix, ref.field)))
            if ref.invariant:
                out.append(Fact("ref_invariant",
                                (prefix, ref.field, ref.invariant)))
    return out


def _chain_facts(chains: dict[str, dict]) -> list[Fact]:
    out: list[Fact] = []
    for name, spec in chains.items():
        out.append(Fact("chain_scheme", (name, spec["scheme"])))
        out += [Fact("chain_facet", (name, f)) for f in spec["facet_by"]]
        out += [Fact("chain_walks", (name, "relation", f))
                for f in spec["relation"]]
        if spec["sibling"]:
            out.append(Fact("chain_walks", (name, "sibling", spec["sibling"])))
        if spec["output"]:
            out.append(Fact("chain_output", (name,)))
        if spec["invariant"]:
            out.append(Fact("chain_invariant", (name, spec["invariant"])))
    return out


def _derived(schemes: dict, chains: dict[str, dict]) -> dict[str, set[tuple]]:
    from . import logic
    return logic.derive("consistency",
                        found=_scheme_facts(schemes) + _chain_facts(chains))


def _at(seq, item) -> int:
    seq = list(seq)
    return seq.index(item) if item in seq else len(seq)


# ── the schemes ───────────────────────────────────────────────────────────

def unknown_targets(schemes: dict) -> dict[str, str]:
    """Per scheme, the refusal for its first reference naming a scheme that
    is not declared. Keyed by scheme, because the loader raises it between
    that scheme's own checks and the next scheme's."""
    found = sorted(
        _derived(schemes, {}).get("unknown_target", ()),
        key=lambda a: (_refs(schemes, a[0]).index(a[1]),
                       _at(_ref(schemes, a[0], a[1]).scheme, a[2])))
    out: dict[str, str] = {}
    for prefix, field, target in found:
        out.setdefault(prefix, (
            f"luria.yaml: schemes.{prefix}.references.{field} "
            f"names scheme {target!r}, which is not declared "
            f"(have: {', '.join(sorted(schemes))})"))
    return out


def _refs(schemes: dict, prefix: str) -> list[str]:
    return [r.field for r in schemes[prefix].references]


def _ref(schemes: dict, prefix: str, field: str):
    return next(r for r in schemes[prefix].references if r.field == field)


def check_references(schemes: dict) -> None:
    """Refuse the first converse or relation invariant that cannot mean what
    it says: per scheme in declaration order, its converses before its
    invariants, each reference in order and each scheme it names in order."""
    from .config import nameable, spelled
    derived = _derived(schemes, {})
    order = list(schemes)
    found: list[tuple[tuple, str]] = []

    def key(prefix, group, field, target, rank, side=0):
        ref = _ref(schemes, prefix, field)
        end = -1 if target == prefix and group == 1 else _at(ref.scheme, target)
        return (order.index(prefix), group, _refs(schemes, prefix).index(field),
                end, rank, side)

    def where(prefix, field, part):
        return f"luria.yaml: schemes.{prefix}.references.{field}.{part}"

    for prefix, field, target in derived.get("converse_missing", ()):
        ref = _ref(schemes, prefix, field)
        by_name = sorted(r.field for r in schemes[target].references)
        found.append((key(prefix, 0, field, target, 0), (
            f"{where(prefix, field, 'converse')}: {ref.converse!r} is not a "
            f"reference {target} declares — {ref.field!r} holds {target} "
            f"codes, so the same relation read backwards is a field on "
            f"{target}, and it has to exist to be written into "
            f"(declared: {', '.join(by_name) or 'none'})")))
    for prefix, field, target in derived.get("converse_elsewhere", ()):
        ref = _ref(schemes, prefix, field)
        other = _ref(schemes, target, ref.converse)
        found.append((key(prefix, 0, field, target, 1), (
            f"{where(prefix, field, 'converse')}: {ref.field!r} is on {prefix} "
            f"and {target}.{ref.converse!r} holds {spelled(other.scheme)} "
            f"codes — the same relation read backwards points back at "
            f"{prefix}")))
    for prefix, field, target in derived.get("converse_unrequited", ()):
        ref = _ref(schemes, prefix, field)
        other = _ref(schemes, target, ref.converse)
        found.append((key(prefix, 0, field, target, 2), (
            f"{where(prefix, field, 'converse')}: {ref.converse!r} does not "
            f"name {ref.field!r} back — a converse is mutual, and half a "
            f"pair completes in one direction only "
            f"(saw: {ref.converse}.converse = {other.converse or 'unset'!r})")))
    for prefix, field, target, side_scheme, side_field in derived.get(
            "converse_single", ()):
        near = (side_scheme, side_field) == (prefix, field)
        found.append((key(prefix, 0, field, target, 3, 0 if near else 1), (
            f"{where(prefix, field, 'converse')}: {side_field!r} needs "
            f"`many = true` — either side of a pair is written into, and "
            f"several documents can stand in one relation to the same one")))
    for prefix, field, end in derived.get("invariant_unheld", ()):
        ref = _ref(schemes, prefix, field)
        known = sorted(nameable(schemes[end]))
        found.append((key(prefix, 1, field, end, 0), (
            f"{where(prefix, field, 'invariant')}: names {ref.invariant!r}, "
            f"which {end} does not declare — a relation asserting a shared "
            f"value in a field one end cannot hold reports every edge and "
            f"means nothing (nameable on {end}: {', '.join(known)})")))
    if found:
        raise ValueError(min(found)[1])


# ── the chains ────────────────────────────────────────────────────────────

def check_chains(chains: dict[str, dict], schemes: dict) -> None:
    """Refuse the first chain that would render an empty or meaningless
    page: per chain in order — its scheme, each `facet_by`, each field it
    walks (spine, then sibling), its `output`, its `invariant`.

    `chains` is each chain's raw declaration, normalised: `scheme` upper-
    cased, `relation` and `facet_by` as tuples."""
    from .config import nameable, spelled
    derived = _derived(schemes, chains)
    order = list(chains)
    found: list[tuple[tuple, str]] = []

    def walked(name):
        spec = chains[name]
        return [("relation", f) for f in spec["relation"]] + (
            [("sibling", spec["sibling"])] if spec["sibling"] else [])

    def listing(prefix):
        return ", ".join(sorted(nameable(schemes[prefix])))

    for (name,) in derived.get("chain_unknown", ()):
        found.append(((order.index(name), 0, 0), (
            f"luria.yaml: chains.{name}: scheme {chains[name]['scheme']!r} is "
            f"not declared (have: {', '.join(sorted(schemes))})")))
    for name, facet in derived.get("facet_unheld", ()):
        prefix = chains[name]["scheme"]
        found.append(((order.index(name), 1,
                       chains[name]["facet_by"].index(facet)), (
            f"luria.yaml: chains.{name}: `facet_by` names {facet!r}, which "
            f"{prefix} does not declare, so every step would render it blank "
            f"(nameable: {listing(prefix)})")))
    for name, key, field in derived.get("walk_undeclared", ()):
        prefix = chains[name]["scheme"]
        declared = ", ".join(sorted(_refs(schemes, prefix))) or "none"
        found.append(((order.index(name), 2,
                       walked(name).index((key, field)), 0), (
            f"luria.yaml: chains.{name}: `{key}` names {field!r}, which is "
            f"not a reference {prefix} declares — a chain over a field "
            f"nothing types walks no edges and renders an empty page "
            f"(declared: {declared})")))
    for name, key, field in derived.get("walk_leaves", ()):
        prefix = chains[name]["scheme"]
        far = _ref(schemes, prefix, field).scheme
        alone = " alone" if prefix in far else ""
        found.append(((order.index(name), 2,
                       walked(name).index((key, field)), 1), (
            f"luria.yaml: chains.{name}: `{key}` names {field!r}, which "
            f"points at {spelled(far)} rather than {prefix}{alone} — a chain "
            f"is a sequence within one scheme, so there is no line to walk "
            f"across the boundary. To assert a shared field over this "
            f"relation, declare `invariant` on "
            f"schemes.{prefix}.references.{field} instead")))
    for (name,) in derived.get("output_missing", ()):
        found.append(((order.index(name), 3, 0), (
            f"luria.yaml: chains.{name}: needs an `output` — the page the "
            f"sequences render to")))
    for name, invariant in derived.get("chain_invariant_unheld", ()):
        prefix = chains[name]["scheme"]
        found.append(((order.index(name), 4, 0), (
            f"luria.yaml: chains.{name}: `invariant` names {invariant!r}, "
            f"which {prefix} does not declare — a chain asserting a shared "
            f"value in a field nothing holds reports every line and means "
            f"nothing (nameable: {listing(prefix)})")))
    if found:
        raise ValueError(min(found)[1])
