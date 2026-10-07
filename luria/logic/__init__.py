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

import threading

import clingo

from ..timing import timed
from ..facts import Fact, facts as record_facts, program as facts_program


class LogicError(RuntimeError):
    """A program that does not denote exactly one set of conclusions."""


Derived = dict[str, set[tuple]]


def rules(name: str) -> str:
    """The text of `luria/logic/<name>.lp`."""
    return resources.files(__package__).joinpath(f"{name}.lp").read_text(
        encoding="utf-8")


def needs(name: str) -> set[str]:
    """The fact families a program reads, from its `% facts:` line."""
    for line in rules(name).splitlines():
        if line.startswith("% facts:"):
            return set(line.split(":", 1)[1].split())
    raise LogicError(f"luria/logic/{name}.lp names no `% facts:` line — "
                     f"a program says which facts it reads, so a run builds "
                     f"only those")


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


_memo: dict = {"results": {}}
_lock = threading.Lock()


def derive(*names: str, found: Iterable[Fact] | None = None) -> Derived:
    """Run the named programs over the record's facts (or the facts given).

    Over the record's own facts, only the families the programs read are
    built, and the result is kept until those facts change: `facts()`
    returns the same list object while the documents are unchanged, so that
    identity is the key. Locked, because the render pool asks from several
    threads and one solve serves them all."""
    label = "solve " + "+".join(names)
    if found is not None:
        with timed(label):
            return solve([rules(n) for n in names], found)
    families = set().union(*(needs(n) for n in names))
    with _lock:
        current_facts = record_facts(families=families)
        # Each entry holds the facts it was solved against, so the identity
        # test cannot be fooled by a list reused at the same address.
        held = _memo["results"].get(names)
        if held is None or held[0] is not current_facts:
            with timed(label):
                held = (current_facts,
                        solve([rules(n) for n in names], current_facts))
            _memo["results"][names] = held
        return held[1]
