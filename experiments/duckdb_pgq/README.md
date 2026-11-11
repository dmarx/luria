<!-- experiments/duckdb_pgq/README.md -->
# DuckDB / DuckPGQ against clingo

An experiment, outside the package: can luria's logic core (`luria/logic/`)
and its path patterns (`luria/pattern_rules.py`) run on DuckDB, with
DuckPGQ's SQL/PGQ `MATCH` in place of luria's own lowering to clingo? The
findings, numbers and DuckPGQ's departures from SQL/PGQ are in the devlog
entry of 2026-11-01, "DuckDB and DuckPGQ as luria engine: an experiment
against clingo". Nothing here is imported by `luria`.

| file | what it does |
|---|---|
| `load.py` | `luria.facts.facts()` into DuckDB, one table per predicate |
| `rules.sql` | `relations.lp` and `invariants.lp` as SQL views |
| `patterns.py` | a parsed `Pattern` lowered to a DuckPGQ `GRAPH_TABLE` query |
| `compare.py` | the rule outputs, diffed against `logic.derive` |
| `compare_patterns.py` | every declared pattern plus `SYNTHETIC`, diffed match for match |

## Running

DuckPGQ's syntax parses on DuckDB 1.5.x and not on 2.0.0, so use a separate
environment:

```bash
python3 -m venv --system-site-packages /tmp/venv-duck
/tmp/venv-duck/bin/pip install -r experiments/duckdb_pgq/requirements.txt
```

`LOAD duckpgq` downloads the extension from DuckDB's community repository
the first time. Then, from a record's root (`SYNTHETIC` is written against
dmarx/nucleation's schemes):

```bash
PYTHONPATH=<luria>:<luria>/experiments/duckdb_pgq /tmp/venv-duck/bin/python -m compare --pattern_edges_from=duckdb
PYTHONPATH=<luria>:<luria>/experiments/duckdb_pgq /tmp/venv-duck/bin/python -m compare_patterns
```

Each prints `OK` or `DIFF` per derived predicate or pattern, and exits
truthy only if all match.
