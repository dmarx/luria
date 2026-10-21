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
says where the assertion belongs instead. A chain walking a pattern (#371)
holds the same line at the pattern's two ends, wherever its middle goes.

**A pattern names schemes and fields.** Every label a declared scheme, every
hop a reference held by the node the arrow leaves and able to land on the
node it reaches, every property a field the node can hold. A pattern that
misses any of these matches nothing, silently.
"""
from __future__ import annotations

from .facts import Fact


def _scheme_facts(schemes: dict, remotes=()) -> list[Fact]:
    from .config import nameable
    from .statuses import vocabulary
    out: list[Fact] = [Fact("remote", (r,)) for r in remotes]
    for prefix, scheme in schemes.items():
        out.append(Fact("scheme", (prefix,)))
        if scheme.successor:
            out.append(Fact("role_successor", (prefix, scheme.successor)))
        if scheme.retires_on:
            out.append(Fact("role_retires_on", (prefix, scheme.retires_on)))
        if scheme.influence:
            out.append(Fact("role_influence", (prefix, scheme.influence)))
        out += [Fact("status_word", (prefix, w)) for w in vocabulary(scheme)]
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


def _pattern_facts(patterns: dict) -> list[Fact]:
    out: list[Fact] = []
    for name, spec in patterns.items():
        pattern = spec.parsed
        out.append(Fact("pattern", (name,)))
        out.append(Fact("pat_hops", (name, len(pattern.path.hops))))
        out.append(Fact("pat_ends", (name, pattern.first.label,
                                     pattern.last.label)))
        for w, path in enumerate((pattern.path, *pattern.negations)):
            for i, node in enumerate(path.nodes):
                out.append(Fact("pat_node", (name, w, i, node.label)))
                out += [Fact("pat_prop", (name, w, i, key))
                        for key, _ in node.props]
            for h, hop in enumerate(path.hops):
                near, far = (h, h + 1) if hop.right else (h + 1, h)
                out += [Fact("pat_hop", (name, w, h, near, far, f))
                        for f in hop.fields]
                if hop.variable:
                    out.append(Fact("pat_closure", (name, w, h)))
    return out


# The scheme checks run in two passes of one load (`config._schemes` raises
# an undeclared target between other per-scheme checks, the rest after), and
# both read one answer. Kept against the schemes dict it was derived from,
# held so its identity cannot be reused.
_last: dict = {"schemes": None, "derived": None}


def _derived(schemes: dict, chains: dict[str, dict],
             remotes=(), patterns: dict | None = None
             ) -> dict[str, set[tuple]]:
    from . import logic
    if chains or patterns:
        return logic.derive("consistency",
                            found=_scheme_facts(schemes, remotes)
                            + _chain_facts(chains)
                            + _pattern_facts(patterns or {}))
    if _last["schemes"] is not schemes:
        _last.update(schemes=schemes, derived=logic.derive(
            "consistency", found=_scheme_facts(schemes, remotes)))
    return _last["derived"]


def _at(seq, item) -> int:
    seq = list(seq)
    return seq.index(item) if item in seq else len(seq)


# ── the schemes ───────────────────────────────────────────────────────────

def unknown_targets(schemes: dict, remotes=()) -> dict[str, str]:
    """Per scheme, the refusal for its first reference naming a scheme that
    is not declared. Keyed by scheme, because the loader raises it between
    that scheme's own checks and the next scheme's."""
    found = sorted(
        _derived(schemes, {}, remotes).get("unknown_target", ()),
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


def check_references(schemes: dict, remotes=()) -> None:
    """Refuse the first converse or relation invariant that cannot mean what
    it says: per scheme in declaration order, its converses before its
    invariants, each reference in order and each scheme it names in order."""
    from .config import nameable, spelled
    derived = _derived(schemes, {}, remotes)
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
    from .statuses import vocabulary
    for prefix, field in derived.get("successor_undeclared", ()):
        refs = ", ".join(_refs(schemes, prefix)) or "none"
        found.append(((order.index(prefix), 2, 0, 0, 0, 0), (
            f"luria.yaml: schemes.{prefix}.successor: names {field!r}, which "
            f"{prefix} does not declare under `references:` — the role says "
            f"which declared reference names a replacement; it does not "
            f"declare one (declared: {refs}). `luria upgrade "
            f"explicit-relations` writes the reference older versions "
            f"supplied")))
    for prefix, field in derived.get("influence_undeclared", ()):
        refs = ", ".join(_refs(schemes, prefix)) or "none"
        found.append(((order.index(prefix), 2, 2, 0, 0, 0), (
            f"luria.yaml: schemes.{prefix}.influence: names {field!r}, which "
            f"{prefix} does not declare under `references:` — the role says "
            f"which declared reference the index renders as \"shaped by\"; "
            f"it does not declare one (declared: {refs})")))
    for prefix, word in derived.get("retires_unknown", ()):
        found.append(((order.index(prefix), 2, 1, 0, 0, 0), (
            f"luria.yaml: schemes.{prefix}.retires_on: names {word!r}, which "
            f"{prefix}'s status vocabulary does not hold — the role says "
            f"which status means replaced; it does not add one (have: "
            f"{', '.join(vocabulary(schemes[prefix]))})")))
    if found:
        raise ValueError(min(found)[1])


# ── the chains ────────────────────────────────────────────────────────────

def check_chains(chains: dict[str, dict], schemes: dict,
                 patterns: dict | None = None) -> None:
    """Refuse the first chain that would render an empty or meaningless
    page: per chain in order — its scheme, each `facet_by`, each field it
    walks (spine, then sibling), its `output`, its `invariant`.

    `chains` is each chain's raw declaration, normalised: `scheme` upper-
    cased, `relation` and `facet_by` as tuples."""
    from .config import nameable, spelled
    patterns = patterns or {}
    derived = _derived(schemes, chains, patterns=patterns)
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
        what = (f"neither a reference {prefix} declares nor a declared "
                f"pattern" if patterns
                else f"not a reference {prefix} declares")
        also = (f"; patterns: {', '.join(patterns)}" if patterns else "")
        found.append(((order.index(name), 2,
                       walked(name).index((key, field)), 0), (
            f"luria.yaml: chains.{name}: `{key}` names {field!r}, which is "
            f"{what} — a chain over a field nothing types walks no edges "
            f"and renders an empty page (declared: {declared}{also})")))
    for name, key, field in derived.get("walk_pattern_ends", ()):
        prefix = chains[name]["scheme"]
        pattern = patterns[field].parsed
        found.append(((order.index(name), 2,
                       walked(name).index((key, field)), 1), (
            f"luria.yaml: chains.{name}: `{key}` names pattern {field!r}, "
            f"which runs from {pattern.first.label} to {pattern.last.label} "
            f"— a chain is a sequence of {prefix} documents, so the pattern "
            f"it walks starts and ends on {prefix}, wherever its middle "
            f"goes")))
    for name, key, field in derived.get("walk_pattern_still", ()):
        found.append(((order.index(name), 2,
                       walked(name).index((key, field)), 1), (
            f"luria.yaml: chains.{name}: `{key}` names pattern {field!r}, "
            f"which has no hop — a chain walks from one document to "
            f"another, and a single node relates nothing")))
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


# ── the patterns ──────────────────────────────────────────────────────────

def _node_text(node) -> str:
    if node.bound:
        return f"({node.var})"
    return f"({node.var}:{node.label})"


def _hop_text(hop) -> str:
    length = ""
    if hop.variable:
        high = "" if hop.high is None else str(hop.high)
        length = f"*{hop.low}..{high}"
    inner = f"[:{'|'.join(hop.fields)}{length}]"
    return f"-{inner}->" if hop.right else f"<-{inner}-"


def check_patterns(patterns: dict, schemes: dict,
                   declared_at: str = "patterns.{}") -> None:
    """Refuse the first pattern that cannot match what it says: per pattern
    in order, a name a reference already uses, then each path (the match,
    then each `WHERE NOT`) node by node and hop by hop.

    `declared_at` spells where each pattern was declared, for the patterns written
    somewhere other than `patterns.X` (`lint.inactive_ok[N]`)."""
    from .config import nameable, spelled
    derived = _derived(schemes, {}, patterns=patterns)
    order = list(patterns)
    found: list[tuple[tuple, str]] = []

    def path(name, w):
        p = patterns[name].parsed
        return (p.path, *p.negations)[w]

    def where(name):
        return f"luria.yaml: {declared_at.format(name)}: "

    for name, prefix in derived.get("pattern_shadows", ()):
        found.append(((order.index(name), -1, 0, 0, 0), where(name) + (
            f"is also a reference {prefix} declares — a chain names either "
            f"by the same key, so one name has to mean one thing")))
    for name, w, i in derived.get("pattern_label_unknown", ()):
        node = path(name, w).nodes[i]
        found.append(((order.index(name), w, i, 0, 0), where(name) + (
            f"`{_node_text(node)}`: {node.label} is not a declared scheme — "
            f"a node's label is the scheme its documents belong to "
            f"(have: {', '.join(sorted(schemes))})")))

    def hop_field(name, w, h, field):
        hop = path(name, w).hops[h]
        text = _hop_text(hop)
        return text if len(hop.fields) == 1 else f"{text}`: `{field}"

    def fields_at(name, w, h, kind):
        # A derived atom names the hop, not the field: recover which of an
        # alternation's fields is at fault, in the order they were written.
        p = path(name, w)
        hop = p.hops[h]
        near, far = p.near(h), p.far(h)
        for field in hop.fields:
            ref = next((r for r in schemes[near.label].references
                        if r.field == field), None)
            if kind == "undeclared" and ref is None:
                yield field, near, far, ref
            if (kind == "misses" and ref is not None
                    and far.label not in ref.scheme and "*" not in ref.scheme):
                yield field, near, far, ref

    for name, w, h in derived.get("pattern_hop_undeclared", ()):
        for field, near, far, _ in fields_at(name, w, h, "undeclared"):
            refs = ", ".join(_refs(schemes, near.label)) or "none"
            found.append(((order.index(name), w, h, 1, 0), where(name) + (
                f"`{hop_field(name, w, h, field)}` is not a reference "
                f"{near.label} declares — a hop follows a field held by the "
                f"node the arrow leaves, `{_node_text(near)}` "
                f"(declared: {refs})")))
            break
    for name, w, h in derived.get("pattern_hop_misses", ()):
        for field, near, far, ref in fields_at(name, w, h, "misses"):
            found.append(((order.index(name), w, h, 2, 0), where(name) + (
                f"`{hop_field(name, w, h, field)}` holds "
                f"{spelled(ref.scheme)} codes, so it never lands on "
                f"`{_node_text(far)}`")))
            break
    for name, w, h in derived.get("pattern_closure_leaves", ()):
        p = path(name, w)
        found.append(((order.index(name), w, h, 3, 0), where(name) + (
            f"`{_hop_text(p.hops[h])}` runs from {p.near(h).label} to "
            f"{p.far(h).label} — a variable-length hop stays within one "
            f"scheme, since every step between its ends is held by a "
            f"document of the same kind")))
    for name, w, i, key in derived.get("pattern_prop_unheld", ()):
        node = path(name, w).nodes[i]
        known = sorted(nameable(schemes[node.label]))
        found.append(((order.index(name), w, i, 4, 0), where(name) + (
            f"`{_node_text(node)}`: `{key}` is not a field {node.label} "
            f"declares, so the property never holds "
            f"(nameable: {', '.join(known)})")))
    if found:
        raise ValueError(min(found)[1])
