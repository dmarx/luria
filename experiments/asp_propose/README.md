<!-- experiments/asp_propose/README.md -->
# Proposals from clingo: choice, constraints, optimisation

An experiment, outside the package. luria's logic core keeps clingo to
stratified Datalog with exactly one answer set, so that every view is a
function of the sources (`luria/logic/__init__.py`, ADR-127). This asks
what clingo's other half could do: propose edits. It does so without
giving up that function-of-the-sources property, by reading back the
*cautious* consequences (true in every optimal answer) and the *brave* ones
(true in some), both of which are fixed by the input.

| file | what it does |
|---|---|
| `propose_values.lp` | for documents of `scheme` with an empty vocabulary `field`: guess values from the graph, require every valued neighbour to share one, minimise the count, and report the documents with nothing to go on |
| `propose.py` | solves it twice (cautious, brave) and prints `apply` (cautious), `choose` (brave only) and `no_evidence` as JSON |

```bash
cd <record root>
PYTHONPATH=<luria> python3 <luria>/experiments/asp_propose/propose.py --scheme CASE --field line [--seed N]
```

Findings are in the devlog entry of 2026-11-01, "Proposals from clingo:
the line inference as choice, constraints and optimisation".
