# experiments/duckdb_pgq/compare.py
"""Run luria's clingo programs and their DuckDB ports over the record in the
current directory, and diff every derived predicate. Run from a record root:

    PYTHONPATH=<luria>:<luria>/experiments/duckdb_pgq python3 -m compare
"""
from __future__ import annotations

import time
from pathlib import Path

from luria import logic
from luria.facts import FAMILIES, facts
from luria.pattern_rules import record_program

from load import connect

HERE = Path(__file__).parent


def timed(label, fn):
    t = time.perf_counter()
    out = fn()
    print(f"  {label}: {time.perf_counter() - t:.2f}s")
    return out


def diff(name, clingo_rows, duck_rows) -> bool:
    a, b = set(clingo_rows), set(duck_rows)
    same = a == b
    print(f"{'OK ' if same else 'DIFF'} {name}: clingo {len(a)}, duckdb {len(b)}"
          + ("" if same else f"; only clingo {sorted(a - b)[:5]}, "
                             f"only duckdb {sorted(b - a)[:5]}"))
    return same


def rows(con, view):
    return [tuple(r) for r in con.execute(f"SELECT * FROM {view}").fetchall()]


def main(pattern_edges_from: str = "clingo") -> bool:
    facts(families=FAMILIES)  # build once, so neither engine is charged
    text, fams = record_program()
    d = timed("clingo relations+invariants+patterns",
              lambda: logic.derive("relations", "invariants", extra=text,
                                   families=fams))
    con, _ = timed("duckdb load", connect)
    con.execute("CREATE TABLE pattern_edge (a0 VARCHAR, a1 VARCHAR, a2 VARCHAR)")
    # The views come first: patterns read `held`, and the invariants read
    # the `pattern_edge` the patterns then fill.
    timed("duckdb rules", lambda: con.execute((HERE / "rules.sql").read_text()))
    if pattern_edges_from == "clingo":
        if d.get("pattern_edge"):
            con.executemany("INSERT INTO pattern_edge VALUES (?, ?, ?)",
                            sorted(d["pattern_edge"]))
    else:
        import patterns
        timed("duckdb patterns", lambda: patterns.install(con))
    ok = True
    for view in ["held", "unbound_relation", "unbound_edge",
                 "unbound_line", "member"]:
        out = timed(f"duckdb {view}", lambda v=view: rows(con, v))
        ok &= diff(view, d.get(view, ()), out)
    if pattern_edges_from != "clingo":
        ok &= diff("pattern_edge", d.get("pattern_edge", ()),
                   rows(con, "pattern_edge"))
    return ok


if __name__ == "__main__":
    import fire
    fire.Fire(main)
