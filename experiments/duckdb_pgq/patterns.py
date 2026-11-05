# experiments/duckdb_pgq/patterns.py
"""Lower luria's parsed path patterns to SQL/PGQ (DuckPGQ) and install their
matches as tables shaped like clingo's: `pattern_edge(name, first, last)`,
`pattern_via(name, first, last, var, code)` and `pattern_node(name, key, i,
code)`.

The graph: one vertex table (`v_doc`: code, scheme, status) and one edge
table per (source scheme, field set, variant), labelled `S__f`, `S__f__g`,
`S__f__rev` or `S__f__opt` (see `build_graph`). That
keying is what `held(S, F, X, Y)` means, since a field such as `rests_on`
exists on more than one scheme. A hop naming several fields gets an edge
table that is their union, because DuckPGQ does not parse `|` between
labels.

Semantics matched to `luria/pattern_rules.py`:
- a node's map and test read `status` from the vertex and every other
  field from the `value` facts, through an EXISTS in the element's WHERE;
- a variable-length hop is a walk whose length lies in [low, high]; an
  unbounded hop `*low..` is any walk of at least `low` steps. DuckPGQ's
  quantifiers do not give that, so bounded hops are unrolled and only an
  unbounded remainder is quantified (see `_hop_sql`);
- `WHERE NOT path` is its own GRAPH_TABLE over the shared variables,
  anti-joined in SQL.
"""
from __future__ import annotations

import duckdb

from luria.patterns import Path, Pattern

# DuckPGQ (1.5.x) wants every element named and every node labelled, so a
# back-reference `(a)` is spelled `(a:doc)` with the same variable.
VERTEX = "doc"


def _q(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _label(scheme: str, fields: tuple[str, ...], variant: str = "") -> str:
    return "__".join((scheme,) + tuple(sorted(fields))
                     + ((variant,) if variant else ()))


def build_graph(con: duckdb.DuckDBPyConnection,
                tables: set[tuple[str, tuple[str, ...], str]]) -> None:
    """The property graph over `held`: an edge table per (scheme, field set,
    variant) some pattern reads. Variants: "" the edges as held; "rev" the
    same reversed; "opt" the edges plus a self-loop on every document, so
    one hop over it is zero or one step; "rev_opt" both. `held` must
    already be a view."""
    con.execute("INSTALL duckpgq FROM community")
    con.execute("LOAD duckpgq")
    con.execute("CREATE OR REPLACE TABLE v_doc AS SELECT d.a0 AS code, "
                "d.a1 AS scheme, s.a1 AS status FROM doc d "
                "LEFT JOIN status s ON s.a0 = d.a0")
    decl = []
    for scheme, fields, variant in sorted(tables):
        label = _label(scheme, fields, variant)
        names = ", ".join(_q(f) for f in fields)
        cols = "x AS c, c AS x" if variant.startswith("rev") else "c, x"
        sql = (f"SELECT {cols} FROM held WHERE s = {_q(scheme)} "
               f"AND f IN ({names})")
        if variant.endswith("opt"):
            sql += " UNION SELECT code, code FROM v_doc"
        con.execute(f'CREATE OR REPLACE TABLE "e_{label}" AS '
                    f"SELECT DISTINCT * FROM ({sql})")
        decl.append(f'"e_{label}" SOURCE KEY (c) REFERENCES v_doc (code) '
                    f'DESTINATION KEY (x) REFERENCES v_doc (code) '
                    f'LABEL "{label}"')
    con.execute("CREATE OR REPLACE PROPERTY GRAPH g VERTEX TABLES "
                f"(v_doc LABEL {VERTEX}) EDGE TABLES ({', '.join(decl)})")


def hop_sets(patterns: dict[str, Pattern]) -> set[tuple[str, tuple[str, ...], str]]:
    """(scheme, fields, variant) for every edge table a pattern reads."""
    out = set()
    for p in patterns.values():
        for path in (p.path, *p.negations):
            for i, hop in enumerate(path.hops):
                key = (path.near(i).label, tuple(sorted(hop.fields)))
                if not hop.variable:
                    out.add(key + ("",))
                    continue
                rev = "" if hop.right else "rev"
                out.add(key + (rev,))
                if hop.high is not None and hop.high > hop.low:
                    out.add(key + ((rev + "_opt") if rev else "opt",))
    return out


def _field_holds(var: str, key: str, cond: str) -> str:
    """SQL for: document `var`'s field `key` has a value satisfying `cond`
    (a predicate over `v.a3`), or for status, the vertex's own column."""
    if key == "status":
        return cond.replace("v.a3", f"{var}.status")
    return (f"EXISTS (SELECT 1 FROM value v WHERE v.a0 = {var}.code "
            f"AND v.a1 = {_q(key)} AND {cond})")


def _node_where(node, var: str) -> str:
    conds = [f"{var}.scheme = {_q(node.label)}"]
    for key, value in node.props:
        conds.append(_field_holds(var, key, f"v.a3 = {_q(str(value))}"))
    if node.test:
        key, op, values = node.test
        within = f"v.a3 IN ({', '.join(_q(str(x)) for x in values)})"
        if op == "in":
            conds.append(_field_holds(var, key, within))
        else:  # `<>` and NOT IN: some value, and none of these
            conds.append(_field_holds(var, key, "TRUE"))
            conds.append("NOT " + _field_holds(var, key, within))
    return " AND ".join(conds)


class _Namer:
    def __init__(self, stem: str):
        self.stem, self.k = stem, 0

    def edge(self) -> str:
        self.k += 1
        return f"{self.stem}e{self.k}"


def _hop_sql(path: Path, i: int, names: _Namer) -> tuple[str, str]:
    """The edge element(s) for hop i, and the selector it needs (`ANY
    SHORTEST` for an unbounded closure, "" otherwise).

    DuckPGQ 1.5.x's quantified edges are not walk semantics, which clingo
    gives and SQL/PGQ's WALK mode defines (the experiment's report has the
    cases):
    - `{lo,hi}` keeps a pair only when its SHORTEST path length is in
      range, so a pair joined directly and by a longer walk drops out of
      `{2,3}`, and a node's walk back to itself (shortest path 0) drops
      out of `{1,3}`;
    - `{0,1}` loses its zero-length matches, though `{0,2}` keeps them;
    - a quantified left-pointing edge is not implemented.
    So a bounded hop uses no quantifier: `low` single steps over the edges,
    then `high - low` single steps over the "opt" table (edges plus a
    self-loop on every document: zero or one step each). That is walk
    semantics by construction. An unbounded `*low..` is `low` single steps
    then `*` under ANY SHORTEST: zero or more further steps exist iff a
    shortest path does, so the shortest-path reading is exact there. A
    variable hop pointing left reads the reversed tables pointing right."""
    hop = path.hops[i]
    key = (path.near(i).label, tuple(sorted(hop.fields)))
    if not hop.variable:
        left, right = ("-", "->") if hop.right else ("<-", "-")
        return f'{left}[{names.edge()}:"{_label(*key)}"]{right}', ""
    rev = "" if hop.right else "rev"
    base = _label(*key, rev)
    opt = _label(*key, (rev + "_opt") if rev else "opt")
    steps = [base] * hop.low
    if hop.high is not None:
        steps += [opt] * (hop.high - hop.low)
    parts = []
    for k, label in enumerate(steps):
        if k:
            parts.append(f"({names.stem}u{i}_{k}:{VERTEX})")
        parts.append(f'-[{names.edge()}:"{label}"]->')
    if hop.high is not None:
        return "".join(parts), ""
    if steps:
        parts.append(f"({names.stem}u{i}_{len(steps)}:{VERTEX})")
    parts.append(f'-[{names.edge()}:"{base}"]->*')
    return "".join(parts), "ANY SHORTEST"


def _path_sql(path: Path, vars_: list[str], names: _Namer
              ) -> tuple[str, str]:
    """The MATCH text for a path, and the selector it needs."""
    parts, selector, seen = [], "", set()
    for i, node in enumerate(path.nodes):
        var = vars_[i]
        where = _node_where(node, var)
        parts.append(f"({var}:{VERTEX} WHERE {where})" if var not in seen
                     else f"({var}:{VERTEX})")
        seen.add(var)
        if i < len(path.hops):
            text, sel = _hop_sql(path, i, names)
            parts.append(text)
            selector = selector or sel
    return "".join(parts), selector


def _vars(path: Path, stem: str, shared: dict[str, str]) -> list[str]:
    seen, out = dict(shared), []
    for i, node in enumerate(path.nodes):
        if node.var and node.var in seen:
            out.append(seen[node.var])
            continue
        var = f"{stem}{i}"
        if node.var:
            seen[node.var] = var
        out.append(var)
    return out


def match_sql(pattern: Pattern) -> str:
    """One SELECT returning a row per match: the code at every position of
    the main path, as columns p0..pn, DISTINCT (a set, as in clingo)."""
    path = pattern.path
    vars_ = _vars(path, "n", {})
    bound = {n.var: v for n, v in zip(path.nodes, vars_) if n.var}
    match, sel = _path_sql(path, vars_, _Namer("m"))
    distinct = list(dict.fromkeys(vars_))
    cols = ", ".join(f"{v}.code AS {v}" for v in distinct)
    main = (f"SELECT DISTINCT * FROM GRAPH_TABLE (g MATCH {sel} {match} "
            f"COLUMNS ({cols}))")
    sql = f"WITH m AS ({main})"
    conds = []
    for j, neg in enumerate(pattern.negations):
        nv = _vars(neg, f"x{j}_", bound)
        shared = list(dict.fromkeys(v for v in nv if v in bound.values()))
        nmatch, nsel = _path_sql(neg, nv, _Namer(f"x{j}_"))
        ncols = ", ".join(f"{v}.code AS {v}" for v in dict.fromkeys(nv))
        sql += (f", neg{j} AS (SELECT DISTINCT {', '.join(shared)} FROM "
                f"GRAPH_TABLE (g MATCH {nsel} {nmatch} COLUMNS ({ncols})))")
        on = " AND ".join(f"neg{j}.{v} = m.{v}" for v in shared) or "TRUE"
        conds.append(f"NOT EXISTS (SELECT 1 FROM neg{j} WHERE {on})")
    positions = ", ".join(f"m.{v} AS p{i}" for i, v in enumerate(vars_))
    sql += f" SELECT {positions} FROM m"
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    return sql


def install(con: duckdb.DuckDBPyConnection,
            patterns: dict[str, Pattern] | None = None) -> dict[str, str]:
    """Create pattern_edge, pattern_via and pattern_node from every
    pattern's matches. Returns the SQL run, by pattern name."""
    if patterns is None:
        from luria.config import current
        patterns = {n: p.parsed for n, p in current().patterns.items()}
    for t, cols in (("pattern_edge", "a0 VARCHAR, a1 VARCHAR, a2 VARCHAR"),
                    ("pattern_via", "a0 VARCHAR, a1 VARCHAR, a2 VARCHAR, "
                                    "a3 VARCHAR, a4 VARCHAR"),
                    ("pattern_node", "a0 VARCHAR, a1 VARCHAR[], a2 BIGINT, "
                                     "a3 VARCHAR")):
        # Filled, not replaced: rules.sql's views may already read them.
        con.execute(f"CREATE TABLE IF NOT EXISTS {t} ({cols})")
        con.execute(f"DELETE FROM {t}")
    if not patterns:
        return {}
    build_graph(con, hop_sets(patterns))
    out = {}
    for name, p in patterns.items():
        sql = match_sql(p)
        out[name] = sql
        n = len(p.path.nodes) - 1
        rows = con.execute(sql).fetchall()
        for row in rows:
            key = list(row)
            for i, code in enumerate(row):
                con.execute("INSERT INTO pattern_node VALUES (?, ?, ?, ?)",
                            [name, key, i, code])
            if n == 0:
                continue
            con.execute("INSERT INTO pattern_edge VALUES (?, ?, ?)",
                        [name, row[0], row[n]])
            shown = {p.path.nodes[0].var, p.path.nodes[n].var}
            for i in range(1, n):
                var = p.path.nodes[i].var
                if var and var not in shown:
                    shown.add(var)
                    con.execute("INSERT INTO pattern_via VALUES (?, ?, ?, ?, ?)",
                                [name, row[0], row[n], var, row[i]])
    return out
