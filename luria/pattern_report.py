# luria/pattern_report.py
"""Patterns declared `report: true`, as warning classes of their own.

    patterns:
      inverted_premise:
        match: "(c:CLAIM {status: 'Active'})-[:rests_on]->(p:CLAIM {status: 'Proposed'})"
        report: true
        blurb: An Active claim resting on a Proposed one.

A reference field checks that its target exists and is in force, and "in
force" counts `Proposed`. So an Active claim resting on a Proposed one, or an
Open question with an Active answer, was no finding at all — a blind spot no
release of luria could close for every record, because which shapes are wrong
is the record's own statement. A pattern is already how a record states a
shape (#371); `report: true` makes the shape a finding.

**One matcher.** The rows are `pattern_node/4` from the same lowering every
chain and view reads (`pattern_rules.py`), solved once for every reported
pattern — there is no second implementation of what a pattern means.

**One class per pattern, named after it.** So `lint.fail_on`, `lint.mute` and
`lint.baseline` name it the way they name `broken-chains`, and a pattern that
would shadow a built-in class is refused at load (`config._patterns`).

**A row is the first node's.** Each match is reported at the document its
first node lands on — the end the pattern is written from, which is where
the person who would fix it is looking. That document acknowledges its rows:

    <!-- pattern-ok: inverted_premise — resting on the draft is deliberate -->

Any scope; it answers for every match of that pattern whose first node is
the document, because a pattern names no single site the way a citation
does. Like every acknowledgement it is counted, and one that answers for no
row — the pattern stopped matching, or names no reported pattern — is
reported under `stale-directives`, so it cannot rot.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import directives, pattern_rules, ref_status
from .config import current

ACK = "pattern-ok"


@dataclass
class Findings:
    # pattern name → unacknowledged rows, for each reported pattern that has any
    rows: dict[str, list[str]] = field(default_factory=dict)
    acknowledged: int = 0
    stale: list[str] = field(default_factory=list)


def _acks(paths: set[Path]) -> dict[Path, list[directives.Directive]]:
    out: dict[Path, list[directives.Directive]] = {}
    for path in sorted(paths):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):        # pragma: no cover
            continue
        # Most documents carry none; the substring test spares them the
        # comment parse.
        if ACK in text and (found := directives.find(path, text, {ACK})):
            out[path] = found
    return out


def _row(path: Path, nodes: tuple[str, ...]) -> str:
    first, rest = nodes[0], list(dict.fromkeys(n for n in nodes[1:]
                                               if n != nodes[0]))
    tail = f" — with {', '.join(rest)}" if rest else ""
    return f"{current().rel(path)}: {first}{tail}"


def findings() -> Findings:
    """Every reported pattern's unacknowledged rows, the count acknowledged,
    and the `pattern-ok` directives that answer for nothing."""
    cfg = current()
    reported = {n for n, p in cfg.patterns.items() if p.report}
    out = Findings()
    docs = ref_status.load_docs()
    every = {d.path for d in docs.values()}
    acks = _acks(every)
    if not reported and not acks:
        return out
    used: set[tuple[Path, int]] = set()
    for name, matches in pattern_rules.reported(cfg).items():
        for nodes in matches:
            first = docs.get(nodes[0])
            if first is None:                       # pragma: no cover
                continue
            answering = [d for d in acks.get(first.path, ())
                         if name in d.args]
            if answering:
                out.acknowledged += 1
                used.update((d.path, d.line) for d in answering)
                continue
            out.rows.setdefault(name, []).append(_row(first.path, nodes))
    for path, found in acks.items():
        for d in found:
            where = f"{cfg.rel(path)}:{d.line}"
            if problem := directives.problems(d):
                out.stale.append(f"{where}: {problem}")
            elif unknown := sorted(set(d.args) - reported):
                out.stale.append(
                    f"{where}: `{ACK}` names {', '.join(unknown)}, which is "
                    f"no pattern declared `report: true`")
            elif (path, d.line) not in used:
                out.stale.append(
                    f"{where}: `{ACK}: {', '.join(d.args)}` answers for no "
                    f"match — the pattern no longer matches here")
    for rows in out.rows.values():
        rows.sort()
    return out


def headline(name: str, count: int) -> str:
    pattern = current().patterns[name]
    says = pattern.blurb or f"`{pattern.match}`"
    return (f"{count} match(es) of the pattern `{name}` — {says} "
            f"(`{ACK}: {name}` in the first document acknowledges one)")
