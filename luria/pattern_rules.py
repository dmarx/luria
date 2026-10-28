# luria/pattern_rules.py
"""A parsed path pattern, lowered to clingo rules over the record's facts.

The translation is mechanical, which is why a pattern can be the notation
and the logic core can stay the engine (ADR-127):

- a node is `doc(V, "LABEL")`, and a property map adds `status/2` or
  `value/4` literals;
- a hop is `held/4` from `relations.lp` — the reading every chain and
  invariant already uses, so a hop stated only on its converse side counts —
  oriented by the arrow: `-[:f]->` is held by the node before it,
  `<-[:f]-` by the node after;
- `|` between fields is one rule per field;
- variable length is a closure that counts steps up to the bound it needs,
  so it terminates on a cycle;
- `WHERE NOT` is a helper predicate over the shared nodes, negated in the
  match — non-recursive, so the program stays stratified and has one answer
  set.

**What is shown.** Two predicates, each keyed by the pattern's name:

    pattern_edge(P, First, Last)            a whole match, by its two ends
    pattern_via(P, First, Last, Var, X)     a named inner node of that match

A view asks for one more, and only when it asks (`rows=True`), so the
programs a chain solves are unchanged (ADR-130):

    pattern_row(P, Match, Var, X)           a named node of one whole match

`Match` is the tuple of every node of the match, which only keys the row:
the atoms sharing it are one row, and a view reads each named node as a
document.

The lint asks for the last, again only when it asks (`nodes=True`), for the
patterns a record declares `report: true`:

    pattern_node(P, Match, I, X)            node I of one whole match

Positional rather than named, because a warning row names the match's first
node's document whether or not the pattern named that node.

Nothing about partial matches. Whether a path that stops partway is
unfinished depends on what the record's schema requires, which a pattern
cannot know; a record that wants that list writes it as a pattern of its own,
`WHERE NOT` and all, and gives it an `output:` for a page of its matches
(#373), which is a view over `pattern_row` like any other.

Every pattern's internal predicates are prefixed `pat<k>_` by position, and
its name only ever appears as a quoted string, so no name a record chooses
can collide with a rule or inject one.
"""
from __future__ import annotations

from .facts import _term
from .patterns import Path, Pattern


def program(patterns: dict[str, Pattern], rows: bool = False,
            nodes: bool = False) -> str:
    """The clingo text for every pattern, in declaration order. `rows` adds
    `pattern_row/4`, which only a view reads; `nodes` adds `pattern_node/4`,
    which only the lint's pattern-backed classes read."""
    out = ["% Generated from luria.yaml `patterns:` — see pattern_rules.py."]
    for k, pattern in enumerate(patterns.values()):
        out += _Lowering(f"pat{k}", pattern, rows, nodes).rules()
    out += ["#show pattern_edge/3.", "#show pattern_via/5."]
    if rows:
        out.append("#show pattern_row/4.")
    if nodes:
        out.append("#show pattern_node/4.")
    return "\n".join(out) + "\n"


def needs_values(patterns: dict[str, Pattern]) -> bool:
    """Whether any property map reads a field other than `status`, which is
    the only one the `documents` facts carry."""
    return any(key != "status"
               for p in patterns.values()
               for path in (p.path, *p.negations)
               for node in path.nodes for key, _ in node.props)


class _Lowering:
    def __init__(self, prefix: str, pattern: Pattern, rows: bool = False,
                 nodes: bool = False):
        self.p = prefix
        self.rows = rows
        self.nodes = nodes
        self.pattern = pattern
        self.name = _term(pattern.name)
        self.lines: list[str] = []
        # Main-path variable per node position; a bare reference shares the
        # variable of the node it names.
        self.main = self._vars(pattern.path, "N", {})
        self.bound = {n.var: v for n, v in zip(pattern.path.nodes, self.main)
                      if n.var}

    # ── naming ─────────────────────────────────────────────────────────────

    @staticmethod
    def _vars(path: Path, stem: str, shared: dict[str, str]) -> list[str]:
        seen = dict(shared)
        out = []
        for i, node in enumerate(path.nodes):
            if node.var and node.var in seen:
                out.append(seen[node.var])
                continue
            var = f"{stem}{i}"
            if node.var:
                seen[node.var] = var
            out.append(var)
        return out

    # ── bodies ─────────────────────────────────────────────────────────────

    def _node(self, node, var: str, first: bool) -> list[str]:
        out = [f"doc({var}, {_term(node.label)})"] if first else []
        for key, value in node.props:
            out.append(f"status({var}, {_term(value)})" if key == "status"
                       else f"value({var}, {_term(key)}, _, {_term(value)})")
        return out

    def _hop(self, tag: str, path: Path, i: int) -> str:
        """Define `tag(X, Y)`: node i to node i+1 by hop i, in path order.
        Returns the predicate name."""
        hop = path.hops[i]
        near = _term(path.near(i).label)
        step = f"{tag}_s" if hop.variable else tag
        for field in hop.fields:
            held = (f"held({near}, {_term(field)}, X, Y)" if hop.right
                    else f"held({near}, {_term(field)}, Y, X)")
            self.lines.append(f"{step}(X, Y) :- {held}.")
        if hop.variable:
            r = f"{tag}_r"
            cap = hop.high if hop.high is not None else hop.low
            self.lines.append(f"{r}(X, Y, 1) :- {step}(X, Y).")
            self.lines.append(
                f"{r}(X, Z, L + 1) :- {r}(X, Y, L), {step}(Y, Z), L < {cap}.")
            if hop.high is None:
                # Saturate at the lower bound: every longer walk is as good
                # as one of exactly `low` steps, and the count stays finite.
                self.lines.append(
                    f"{r}(X, Z, {cap}) :- {r}(X, Y, {cap}), {step}(Y, Z).")
                self.lines.append(f"{tag}(X, Y) :- {r}(X, Y, {cap}).")
            else:
                self.lines.append(
                    f"{tag}(X, Y) :- {r}(X, Y, L), L >= {hop.low}.")
        return tag

    def _body(self, tag: str, path: Path, vars_: list[str],
              upto: int | None = None, start: int = 0) -> list[str]:
        """Literals for nodes `start..upto` and the hops between them."""
        end = len(path.nodes) - 1 if upto is None else upto
        out: list[str] = []
        declared: set[str] = set()
        for i in range(start, end + 1):
            node, var = path.nodes[i], vars_[i]
            # Each variable stands on its label once per rule. In a negation
            # that includes the shared nodes: redundant beside the match,
            # and what keeps the helper safe when no hop mentions them.
            out += self._node(node, var, first=var not in declared)
            declared.add(var)
            if i < end:
                out.append(f"{tag}_h{i}({var}, {vars_[i + 1]})")
        return out

    # ── rules ──────────────────────────────────────────────────────────────

    def rules(self) -> list[str]:
        path = self.pattern.path
        n = len(path.nodes) - 1
        for i in range(n):
            self._hop(f"{self.p}_h{i}", path, i)
        body = self._body(self.p, path, self.main)
        for j, neg in enumerate(self.pattern.negations):
            body.append(f"not {self._negation(j, neg)}")
        args = ", ".join(self.main)
        self.lines.append(f"{self.p}_m({args}) :- {', '.join(body)}.")
        if self.rows:
            self._rows(args)
        if self.nodes:
            self._nodes(args)
        if n == 0:
            return self.lines
        first, last = self.main[0], self.main[n]
        self.lines.append(
            f"pattern_edge({self.name}, {first}, {last}) :- {self.p}_m({args}).")
        shown = {path.nodes[0].var, path.nodes[n].var}
        for i in range(1, n):
            node = path.nodes[i]
            if node.var and node.var not in shown:
                shown.add(node.var)
                self.lines.append(
                    f"pattern_via({self.name}, {first}, {last}, "
                    f"{_term(node.var)}, {self.main[i]}) :- {self.p}_m({args}).")
        return self.lines

    def _rows(self, args: str) -> None:
        """One `pattern_row` per named node, keyed by the whole match. A
        node named twice is one variable and one row entry."""
        match = f"({args},)" if len(self.main) == 1 else f"({args})"
        for var, clingo_var in self.bound.items():
            self.lines.append(
                f"pattern_row({self.name}, {match}, {_term(var)}, "
                f"{clingo_var}) :- {self.p}_m({args}).")

    def _nodes(self, args: str) -> None:
        """One `pattern_node` per position, keyed by the whole match, so a
        match whose nodes are all anonymous is still a row."""
        match = f"({args},)" if len(self.main) == 1 else f"({args})"
        for i, clingo_var in enumerate(self.main):
            self.lines.append(
                f"pattern_node({self.name}, {match}, {i}, {clingo_var}) :- "
                f"{self.p}_m({args}).")

    def _negation(self, j: int, neg: Path) -> str:
        tag = f"{self.p}_n{j}"
        vars_ = self._vars(neg, f"M{j}_", self.bound)
        for i in range(len(neg.hops)):
            self._hop(f"{tag}_h{i}", neg, i)
        shared = list(dict.fromkeys(
            v for v in vars_ if v in self.bound.values()))
        head = f"{tag}({', '.join(shared)})" if shared else tag
        body = self._body(tag, neg, vars_)
        self.lines.append(f"{head} :- {', '.join(body)}.")
        return head


# ── over the record ────────────────────────────────────────────────────────

def record_program(cfg=None) -> tuple[str, frozenset[str]]:
    """The lowered `patterns:` of a config, and the fact families it reads
    beyond `relations.lp`'s — ("", ∅) for a record that declares none."""
    from .config import current
    cfg = cfg or current()
    if not cfg.patterns:
        return "", frozenset()
    parsed = {name: p.parsed for name, p in cfg.patterns.items()}
    return program(parsed), (frozenset({"values"}) if needs_values(parsed)
                             else frozenset())


def derived() -> dict[str, set[tuple]]:
    """Every pattern's matches over the record, solved once per change."""
    from . import logic
    text, families = record_program()
    if not text:
        return {}
    return logic.derive("relations", extra=text, families=families)


def edges(name: str) -> dict[str, set[str]]:
    """A pattern as a chain reads a field: each first node, mapped to the
    last nodes it matches."""
    out: dict[str, set[str]] = {}
    for p, first, last in derived().get("pattern_edge", ()):
        if p == name:
            out.setdefault(first, set()).add(last)
    return out


def through(name: str) -> dict[tuple[str, str], list[str]]:
    """The named inner nodes of each match, by its two ends, in code order."""
    out: dict[tuple[str, str], set[str]] = {}
    for p, first, last, _, code in derived().get("pattern_via", ()):
        if p == name:
            out.setdefault((first, last), set()).add(code)
    return {k: sorted(v) for k, v in out.items()}


def reported(cfg=None) -> dict[str, list[tuple[str, ...]]]:
    """Every match of every pattern declared `report: true`, as the codes of
    its nodes in path order, sorted — one solve for all of them. A pattern
    that matches nothing is absent."""
    from . import logic
    from .config import current
    cfg = cfg or current()
    parsed = {name: p.parsed for name, p in cfg.patterns.items() if p.report}
    if not parsed:
        return {}
    text = program(parsed, nodes=True)
    families = (frozenset({"values"}) if needs_values(parsed)
                else frozenset())
    found: dict[tuple[str, str], dict[int, str]] = {}
    for name, key, i, code in logic.derive(
            "relations", extra=text, families=families).get("pattern_node", ()):
        found.setdefault((name, key), {})[i] = code
    out: dict[str, list[tuple[str, ...]]] = {}
    for (name, _), nodes in found.items():
        out.setdefault(name, []).append(
            tuple(nodes[i] for i in sorted(nodes)))
    return {name: sorted(rows) for name, rows in out.items()}
