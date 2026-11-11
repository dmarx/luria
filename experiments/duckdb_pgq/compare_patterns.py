# experiments/duckdb_pgq/compare_patterns.py
"""Every pattern the record declares, plus SYNTHETIC ones that reach the
grammar's corners, solved by clingo (luria's own lowering) and by DuckPGQ
(patterns.py), compared match for match. Run from a record root:

    PYTHONPATH=<luria>:<luria>/experiments/duckdb_pgq python3 -m compare_patterns
"""
from __future__ import annotations

import time
from pathlib import Path

from luria import logic
from luria.config import current
from luria.facts import FAMILIES, facts
from luria.pattern_rules import needs_values, program
from luria.patterns import parse

import patterns as pgq
from load import connect

HERE = Path(__file__).parent

# Written against nucleation's schemes and fields; another record needs its own.
SYNTHETIC = {
    "s_bounded": "(a:CLAIM)-[:rests_on*1..3]->(b:CLAIM)",
    "s_bounded_from_2": "(a:CLAIM)-[:rests_on*2..3]->(b:CLAIM)",
    "s_unbounded": "(a:CLAIM)-[:rests_on*]->(b:CLAIM)",
    "s_unbounded_from_2": "(a:CLAIM)-[:rests_on*2..]->(b:CLAIM)",
    "s_left_variable": "(p:CLAIM)<-[:rests_on*1..2]-(c:CLAIM {status: 'Active'})",
    "s_alternation": "(c:CLAIM)-[:rests_on|objects_to]->(x:CLAIM)",
    "s_in": "(n:NOTE)-[:paper]->(l:LIT WHERE l.status IN ['Unavailable', 'Unfetched', 'Deferred'])",
    "s_unequal": "(c:CLAIM WHERE c.status <> 'Active')-[:rests_on]->(p:CLAIM)",
    "s_value_props": "(c:CLAIM {role: 'counter'})-[:objects_to]->(t:CLAIM WHERE NOT t.role IN ['thesis'])",
    "s_back_reference": "(a:CLAIM)-[:complements]->(b:CLAIM)-[:complements]->(a)",
    "s_negated_path": "(c:CLAIM)<-[:concludes]-(g:ARG) WHERE NOT (g)<-[:undercuts]-(u:CLAIM)",
    "s_via": "(q:QUESTION)<-[:answers]-(c:CLAIM)-[:rests_on]->(p:CLAIM)",
    "s_unbounded_cyclic": "(a:CLAIM {status: 'Active'})-[:complements*]->(b:CLAIM)",
    "s_unbounded_cyclic_from_3": "(a:CLAIM {role: 'counter'})-[:complements*3..]->(b:CLAIM)",
    "s_unbounded_left": "(p:CLAIM)<-[:rests_on*]-(c:CLAIM)",
    "s_exact_2": "(a:QUESTION)-[:refines*2..2]->(b:QUESTION)",
}


def clingo_matches(parsed) -> tuple[set, float]:
    text = program(parsed, nodes=True)
    fam = frozenset({"values"}) if needs_values(parsed) else frozenset()
    t = time.perf_counter()
    d = logic.derive("relations", extra=text, families=fam)
    took = time.perf_counter() - t
    by_key: dict[tuple, dict[int, str]] = {}
    for name, key, i, code in d.get("pattern_node", ()):
        by_key.setdefault((name, key), {})[i] = code
    out = {(name, tuple(n[i] for i in sorted(n))) for (name, _), n in by_key.items()}
    return out, took, d


def main(synthetic: bool = True, show_sql: str = "") -> bool:
    parsed = {n: p.parsed for n, p in current().patterns.items()}
    if synthetic:
        parsed |= {n: parse(n, s) for n, s in SYNTHETIC.items()}
    facts(families=FAMILIES)
    want, t_clingo, d = clingo_matches(parsed)
    con, _ = connect()
    con.execute("CREATE TABLE pattern_edge (a0 VARCHAR, a1 VARCHAR, a2 VARCHAR)")
    con.execute((HERE / "rules.sql").read_text())  # held, which the graph reads
    t = time.perf_counter()
    sqls = {}
    got, errors = set(), {}
    for name, p in parsed.items():
        try:
            sql = pgq.match_sql(p)
            sqls[name] = sql
        except Exception as e:  # noqa: BLE001 — an experiment reports, never hides
            errors[name] = f"lowering: {e}"
    pgq.build_graph(con, pgq.hop_sets(parsed))
    t_graph = time.perf_counter() - t
    t = time.perf_counter()
    for name, sql in sqls.items():
        try:
            got |= {(name, tuple(r)) for r in con.execute(sql).fetchall()}
        except Exception as e:  # noqa: BLE001
            errors[name] = str(e).splitlines()[0][:200]
    t_duck = time.perf_counter() - t
    ok = True
    for name in parsed:
        a = {m for n, m in want if n == name}
        b = {m for n, m in got if n == name}
        if name in errors:
            ok = False
            print(f"ERR  {name}: {errors[name]}")
            continue
        same = a == b
        ok &= same
        print(f"{'OK ' if same else 'DIFF'} {name}: clingo {len(a)}, duckdb {len(b)}"
              + ("" if same else f"\n     only clingo {sorted(a - b)[:3]}"
                                 f"\n     only duckdb {sorted(b - a)[:3]}"))
    print(f"clingo solve (all patterns): {t_clingo:.2f}s; duckdb graph build "
          f"{t_graph:.2f}s, matches {t_duck:.2f}s")
    if show_sql:
        print(sqls.get(show_sql, errors.get(show_sql)))
    return ok


if __name__ == "__main__":
    import fire
    fire.Fire(main)
