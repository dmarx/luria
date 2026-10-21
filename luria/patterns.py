# luria/patterns.py
"""A named path pattern, parsed into the shape the lowering reads (#371).

    patterns:
      follows_from: (b:CLAIM)<-[:concludes]-(i:INF)<-[:premise_of]-(a:CLAIM)

The notation is Cypher's, restricted to what a path question needs: node
labels (schemes), typed directed hops (reference fields, `|` between
several), variable length on one hop, literal equality on a node's
frontmatter, and `WHERE NOT` over a pattern. Everything else — `MATCH`,
`RETURN`, `OPTIONAL MATCH`, undirected edges, named edges, shortest path,
any write — is refused here, by name, at load. ADR-125 asks that a reader
see the rule in the line; a pattern is that, and a clause language around it
would not be.

**Why a grammar of luria's own** (the ADR's alternatives): no tool lowers
Cypher to clingo, so luria writes the lowering whatever parses, and a
general Cypher parser would hand it a whole query tree to walk down for the
path and then accept constructs this subset has to refuse in a second pass.
`patterns.lark` accepts only the subset.

**Refusals by name.** lark's own message is "unexpected token at column N",
which tells a person what the parser saw and nothing about what they meant.
So a failed parse is diagnosed first against the constructs people reach
for, and only an unrecognised mistake falls back to the column.

This module checks shape only: what a pattern *says*. Whether its labels
are schemes and its hops are declared references is the schema's question,
asked in `consistency.py` with every scheme in view.
"""
from __future__ import annotations

import functools
import re
from dataclasses import dataclass
from importlib import resources

import lark


class PatternError(ValueError):
    """A pattern outside the subset, or one that cannot mean anything."""


@dataclass(frozen=True)
class Node:
    """One position in a path. `var` is "" for an anonymous node; `bound`
    marks a bare `(c)` referring back to a node named earlier, whose label it
    carries."""
    var: str
    label: str
    props: tuple[tuple[str, str], ...]
    bound: bool = False


@dataclass(frozen=True)
class Hop:
    """One typed edge between consecutive nodes. `right` is the arrow's
    direction: `-[:f]->` leaves the node before it, `<-[:f]-` the node after.
    `high` is None for an unbounded variable-length hop."""
    fields: tuple[str, ...]
    right: bool
    low: int = 1
    high: int | None = 1

    @property
    def variable(self) -> bool:
        return (self.low, self.high) != (1, 1)


@dataclass(frozen=True)
class Path:
    nodes: tuple[Node, ...]
    hops: tuple[Hop, ...]

    def near(self, i: int) -> Node:
        """The node hop `i` leaves: the one whose field holds the code."""
        return self.nodes[i] if self.hops[i].right else self.nodes[i + 1]

    def far(self, i: int) -> Node:
        """The node hop `i` lands on."""
        return self.nodes[i + 1] if self.hops[i].right else self.nodes[i]


@dataclass(frozen=True)
class Pattern:
    name: str
    source: str
    path: Path
    negations: tuple[Path, ...]

    @property
    def first(self) -> Node:
        return self.path.nodes[0]

    @property
    def last(self) -> Node:
        return self.path.nodes[-1]


@functools.cache
def _parser() -> lark.Lark:
    grammar = resources.files(__package__).joinpath(
        "patterns.lark").read_text(encoding="utf-8")
    return lark.Lark(grammar, parser="lalr", maybe_placeholders=True)


def parse(name: str, source: str, where: str = "") -> Pattern:
    """`source` as a pattern, or a `PatternError` saying what is outside the
    subset. `where` names the key it was written at, for a pattern declared
    somewhere other than `patterns.X` (`lint.inactive_ok`)."""
    where = where or f"luria.yaml: patterns.{name}: "
    text = str(source or "")
    if not text.strip():
        raise PatternError(where + "is empty — a pattern is a path, such as "
                           "`(a:LIT)-[:extends]->(b:LIT)`")
    try:
        tree = _parser().parse(text)
    except lark.UnexpectedInput as exc:
        raise PatternError(where + _diagnose(text, exc)) from None
    paths = [_path(where, p) for p in tree.children]
    return _bind(where, name, text.strip(), paths[0], paths[1:])


# ── shape ──────────────────────────────────────────────────────────────────

def _path(where: str, tree: lark.Tree) -> tuple[list, list[Hop]]:
    nodes, hops = [], []
    for child in tree.children:
        if child.data == "node":
            var, label, props = child.children
            nodes.append((str(var or ""), str(label or ""), _props(props)))
        else:
            hops.append(_hop(where, child))
    return nodes, hops


def _props(tree) -> tuple[tuple[str, str], ...]:
    if tree is None:
        return ()
    out = []
    for prop in tree.children:
        key, value = prop.children
        text = str(value)
        out.append((str(key), text[1:-1] if value.type == "STRING" else text))
    return tuple(out)


def _hop(where: str, tree: lark.Tree) -> Hop:
    var, types, length = tree.children
    fields = tuple(str(t) for t in types.children)
    if var is not None:
        raise PatternError(
            where + f"`[{var}:{'|'.join(fields)}]` is a named edge, which is "
            f"not in the subset — a hop is identified by its field, so write "
            f"`[:{'|'.join(fields)}]`")
    low, high = 1, 1
    if length is not None:
        first, dots, last = length.children
        if dots is None:
            low = high = int(first) if first is not None else 1
            if first is None:
                high = None
        else:
            low = int(first) if first is not None else 1
            high = int(last) if last is not None else None
        if low < 1:
            raise PatternError(
                where + f"`*{low}..` — a variable-length hop takes at least 1 "
                f"step; a pattern whose two ends may be one document says "
                f"nothing about how they connect")
        if high is not None and high < low:
            raise PatternError(where + f"`*{low}..{high}` — the upper bound "
                               f"is below the lower, so nothing can match")
    return Hop(fields, right=tree.data == "right", low=low, high=high)


def _bind(where: str, name: str, source: str, main, negated) -> Pattern:
    """Resolve each bare `(c)` to the label bound earlier, and refuse what
    cannot mean anything: a node with no label to stand on, a name bound
    twice, a variable-length hop under `WHERE NOT`."""
    labels: dict[str, str] = {}

    def resolve(raw_nodes, shared: bool) -> tuple[Node, ...]:
        local = dict(labels)
        out = []
        for var, label, props in raw_nodes:
            if not label:
                if not var:
                    raise PatternError(where + "`()` needs a label — a node's "
                                       "label is the scheme it stands on")
                if var not in local:
                    raise PatternError(
                        where + f"`({var})` refers to `{var}`, which is not "
                        f"bound earlier in the pattern — a node needs a label "
                        f"(its scheme) the first time it appears")
                out.append(Node(var, local[var], props, bound=True))
                continue
            if var and var in local:
                raise PatternError(
                    where + f"`({var}:{label})` — `{var}` is already bound; "
                    f"refer back to it as `({var})`")
            if var:
                local[var] = label
            out.append(Node(var, label, props))
        if shared:
            labels.update(local)
        return tuple(out)

    nodes, hops = main
    path = Path(resolve(nodes, shared=True), tuple(hops))
    negations = []
    for nodes, hops in negated:
        if any(h.variable for h in hops):
            raise PatternError(
                where + "`WHERE NOT` takes a fixed path, not a "
                "variable-length one — negation over a closure is the "
                "recursion through negation the logic core cannot evaluate "
                "deterministically")
        negations.append(Path(resolve(nodes, shared=False), tuple(hops)))
    return Pattern(name, source, path, tuple(negations))


# ── refusals by name ───────────────────────────────────────────────────────

_CLAUSES = ("WITH", "UNWIND", "ORDER BY", "LIMIT", "SKIP", "UNION", "CALL")
_WRITES = ("CREATE", "MERGE", "SET", "DELETE", "DETACH", "REMOVE")


def _diagnose(text: str, exc: lark.UnexpectedInput) -> str:
    """The construct a failed parse most likely reached for, in words."""
    bare = re.sub(r"'[^']*'|\"[^\"]*\"", "''", text)

    def has(pattern: str) -> bool:
        return re.search(pattern, bare, re.IGNORECASE) is not None

    if has(r"^\s*match\b"):
        return ("write the pattern without `MATCH` — luria adds it, and the "
                "pattern is the whole query")
    if has(r"\boptional\s+match\b"):
        return ("`OPTIONAL MATCH` is not in the subset — a pattern matches "
                "whole or not at all")
    if has(r"\breturn\b"):
        return ("`RETURN` is not in the subset — a pattern's nodes are its "
                "result, and what reads it decides which it shows")
    if has(r"\b(all)?shortestpath\b"):
        return "`shortestPath` is not in the subset"
    for word in _WRITES:
        if has(rf"\b{word}\b"):
            return f"`{word}` writes, and a pattern only reads"
    for word in _CLAUSES:
        if has(r"\b" + word.replace(" ", r"\s+") + r"\b"):
            return f"`{word}` is not in the subset — a pattern is one path"
    if has(r"\bwhere\b(?!\s+not\b)"):
        return ("the only condition is `WHERE NOT` followed by a pattern; "
                "equality on a "
                "node is a property map, such as `(c:CLAIM {status: "
                "'Active'})`")
    if has(r"<-\[[^\]]*\]->") or has(r"(?<!<)-\[[^\]]*\]-(?!>)"):
        return ("an undirected edge is not in the subset — a reference is "
                "held by one end, so give the hop a direction: `-[:f]->` or "
                "`<-[:f]-`")
    if has(r"-->|<--|\)\s*--\s*\(") or has(r"\[\s*\]"):
        return ("an edge needs a type — the reference field it follows, "
                "such as `-[:extends]->`")
    if has(r"\(\s*\w*\s*:\s*\w+\s*[:|]"):
        return ("a node takes one label — the one scheme its documents "
                "belong to")
    column = getattr(exc, "column", "?")
    return (f"cannot read this at column {column} (`{text.strip()}`) — "
            f"see the configuration reference for the pattern subset")
