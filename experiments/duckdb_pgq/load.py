# experiments/duckdb_pgq/load.py
"""Load the record's facts into DuckDB: one table per predicate.

The same `Fact` list `luria.logic.derive` hands clingo, so the two engines
see identical input. A predicate `p/n` becomes table `p` with columns
`a0..a{n-1}`, typed BIGINT where every value is an int and VARCHAR
otherwise.
"""
from __future__ import annotations

from collections import defaultdict

import duckdb
import pandas as pd

from luria.facts import FAMILIES, facts


# Every predicate luria.facts documents, with its arity. A predicate with no
# facts still needs its table: clingo reads an absent predicate as empty,
# and SQL refuses to name a table that does not exist.
ARITY = {"scheme": 1, "active": 2, "ref": 2, "ref_target": 3,
         "ref_converse": 3, "ref_derived": 2, "ref_many": 2,
         "ref_required": 2, "ref_invariant": 3, "ref_label": 3, "chain": 2,
         "chain_relation": 3, "chain_sibling": 2, "chain_invariant": 2,
         "pattern": 1, "doc": 2, "status": 2, "value": 4, "ref_value": 3,
         "holds": 3, "edge": 3, "head_value": 4}
INTS = {("value", 2)}


def connect(families=FAMILIES) -> tuple[duckdb.DuckDBPyConnection, dict]:
    """A fresh in-memory database holding the record's facts, and the
    per-predicate row counts."""
    rows: dict[str, list[tuple]] = defaultdict(list)
    for f in facts(families=families):
        rows[f.predicate].append(f.args)
    con = duckdb.connect()
    for pred, tuples in rows.items():
        arity = len(tuples[0])
        types = ["BIGINT" if all(isinstance(t[i], int) for t in tuples)
                 else "VARCHAR" for i in range(arity)]
        cols = ", ".join(f"a{i} {ty}" for i, ty in enumerate(types))
        con.execute(f'CREATE TABLE "{pred}" ({cols})')
        # Row-by-row executemany took 80 s for 164k facts; a DataFrame
        # scan takes well under one.
        frame = pd.DataFrame(
            [tuple(str(a) if ty == "VARCHAR" else a
                   for a, ty in zip(t, types)) for t in tuples],
            columns=[f"a{i}" for i in range(arity)])
        con.register("_frame", frame)
        con.execute(f'INSERT INTO "{pred}" SELECT * FROM _frame')
        con.unregister("_frame")
    for pred, arity in ARITY.items():
        if pred not in rows:
            cols = ", ".join(
                f"a{i} {'BIGINT' if (pred, i) in INTS else 'VARCHAR'}"
                for i in range(arity))
            con.execute(f'CREATE TABLE "{pred}" ({cols})')
    return con, {p: len(t) for p, t in rows.items()}
