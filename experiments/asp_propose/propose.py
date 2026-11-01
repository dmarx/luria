# experiments/asp_propose/propose.py
"""Propose values for an empty vocabulary field, from the graph.

    PYTHONPATH=<luria> python3 propose.py --scheme CASE --field line [--seed N]

Solves propose_values.lp over the record in the current directory (or
LURIA_ROOT) twice: once for the CAUTIOUS consequences (values every optimal
answer assigns: safe to apply) and once for the BRAVE ones (values some
optimal answer assigns: a choice for a person). Both are functions of the
input, whatever order the solver searches in; --seed changes that order so
the claim can be checked. Prints the proposal as JSON on stdout.
"""
from __future__ import annotations

import json
from pathlib import Path

import clingo
import fire

from luria import logic
from luria.facts import facts, program as facts_program

HERE = Path(__file__).parent


def consequences(text: str, mode: str, seed: int, consts: list[str]
                 ) -> tuple[set, list[int]]:
    ctl = clingo.Control([*consts, "--warn=none", "--opt-mode=optN",
                          f"--enum-mode={mode}", f"--seed={seed}",
                          "--rand-freq=0.5", "0"])
    ctl.add("base", [], text)
    ctl.ground([("base", [])])
    last, cost = set(), []
    with ctl.solve(yield_=True) as handle:
        for model in handle:
            last = {(s.name, tuple(a.string for a in s.arguments))
                    for s in model.symbols(shown=True)
                    if s.name in ("take", "no_evidence")}
            cost = list(model.cost)
        result = handle.get()
    if not result.satisfiable:
        raise SystemExit("unsatisfiable: no assignment meets the constraints")
    return last, cost


def propose(scheme: str = "CASE", field: str = "line", seed: int = 0) -> dict:
    found = facts(families={"schema", "documents", "values"})
    text = (facts_program(found) + logic.rules("relations")
            + (HERE / "propose_values.lp").read_text())
    consts = [f'--const=scheme="{scheme}"', f'--const=field="{field}"']
    cautious, cost = consequences(text, "cautious", seed, consts)
    brave, _ = consequences(text, "brave", seed, consts)
    out: dict = {"scheme": scheme, "field": field, "optimum": cost,
                 "apply": {}, "choose": {}, "no_evidence": []}
    for name, args in sorted(brave):
        if name == "no_evidence":
            out["no_evidence"].append(args[0])
        elif ("take", args) in cautious:
            out["apply"].setdefault(args[0], []).append(args[1])
        else:
            out["choose"].setdefault(args[0], []).append(args[1])
    return out


if __name__ == "__main__":
    fire.Fire(lambda scheme="CASE", field="line", seed=0:
              print(json.dumps(propose(scheme, field, seed), indent=2)))
