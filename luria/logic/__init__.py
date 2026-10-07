# luria/logic/__init__.py
"""The logic core: clingo rules over the record's facts.

Each ported subsystem is a `.lp` program in this directory. `derive` grounds
the named programs against the facts and returns the atoms they derive, as
plain Python tuples, for the procedural shell to turn into findings, edits
and pages. See `luria/facts.py` for the facts, and the ADR on a logic core in
clingo for why.

Programs stay in stratified Datalog: no choice rules, no disjunction, no
optimisation. Such a program has exactly one answer set, and `derive`
refuses any other count, because a generated view that depended on which
model the solver found first would not be a function of the sources.
"""
from __future__ import annotations

from collections.abc import Iterable
from importlib import resources

import clingo

from ..facts import Fact, facts as record_facts, program as facts_program


class LogicError(RuntimeError):
    """A program that does not denote exactly one set of conclusions."""


Derived = dict[str, set[tuple]]


def rules(name: str) -> str:
    """The text of `luria/logic/<name>.lp`."""
    return resources.files(__package__).joinpath(f"{name}.lp").read_text(
        encoding="utf-8")


def _python(symbol: clingo.Symbol):
    if symbol.type == clingo.SymbolType.String:
        return symbol.string
    if symbol.type == clingo.SymbolType.Number:
        return symbol.number
    if symbol.type == clingo.SymbolType.Function and not symbol.arguments:
        return symbol.name
    return str(symbol)


def solve(sources: Iterable[str], found: Iterable[Fact]) -> Derived:
    """Ground program texts against facts and return every shown atom,
    grouped by predicate, as tuples of Python values."""
    # Two models asked for, so a second one can be seen and refused: clingo
    # stops at the first by default, and a guard that cannot see the case it
    # guards against is no guard.
    control = clingo.Control(["--warn=none", "--models=2"])
    control.add("base", [], facts_program(found))
    for text in sources:
        control.add("base", [], text)
    control.ground([("base", [])])
    models: list[Derived] = []
    with control.solve(yield_=True) as handle:
        for model in handle:
            derived: Derived = {}
            for symbol in model.symbols(shown=True):
                derived.setdefault(symbol.name, set()).add(
                    tuple(_python(a) for a in symbol.arguments))
            models.append(derived)
            if len(models) > 1:
                break
    if len(models) != 1:
        raise LogicError(
            f"a logic program must have exactly one answer set, and this one "
            f"has {'none' if not models else 'several'} — luria's programs are "
            f"stratified Datalog: no choice rules, no disjunction, and no "
            f"integrity constraint a record can violate")
    return models[0]


def derive(*names: str, found: Iterable[Fact] | None = None) -> Derived:
    """Run the named programs over the record's facts (or the facts given)."""
    return solve([rules(n) for n in names],
                 record_facts() if found is None else found)
