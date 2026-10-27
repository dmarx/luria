# luria/reliance.py
"""What rests on a document, along the fields a record says carry dependence.

    reliance: [rests_on, grounds, uses, presupposes]
    load_bearing: 5

An undecided document is pending whatever depends on it, and the pending
report used to rank by the two things it could see: age and citation count.
Neither is reliance. A claim cited once from a ledger and rested on by forty
other claims is the most urgent decision in the record, and it sorted below a
stalled idea three people mentioned in passing. The record already says what
rests on what, in fields its schemes declare; `reliance:` names which of those
fields mean "depends on", and this module counts the closure.

**One reading of a relation.** A step is `held/4` from `relations.lp`, the
same reading every chain, invariant and pattern uses, so a dependence stated
only on its converse side counts. The closure is `logic/reliance.lp`; this
module only asks it.

Three readers:

- the pending report's dependents column and its sort (`adr_pending`);
- `load-bearing`, every undecided document with at least `load_bearing`
  transitive dependents — the count past which an open question is a
  decision the record has already built on;
- `unbounded-acknowledgements`, an `inactive-ok` directive excusing a
  retired document that the acknowledging document *depends on*, with no
  `until`. The directive is true when written ("the definition current when
  this claim was written") and then silences, forever, the one finding that
  asks whether the claim still holds in the successor's sense. A dependence
  on a retired premise is a debt with a date, so the acknowledgement needs
  one.

"Retired" here is what the pending report is not: a document out of force
that is also not undecided — `Superseded`, `Rejected`, whatever a scheme's
vocabulary retires to. A `Proposed` premise is the pending report's business,
and `load-bearing` is how it is ranked.
"""
from __future__ import annotations

from . import adr_pending, directives, ref_status
from .config import current
from .facts import _term

#: Directive kind whose rows this module checks for an expiry.
DIRECTIVE = ref_status.DIRECTIVE


def _derived() -> dict[str, set[tuple]]:
    from . import logic
    fields = current().reliance
    if not fields:
        return {}
    extra = "\n".join(f"reliance({_term(f)})." for f in fields) + "\n"
    return logic.derive("relations", "reliance", extra=extra)


def dependents() -> dict[str, int]:
    """Each document's count of distinct transitive dependents, for the
    documents that have any. Empty when `reliance` is unset."""
    return {code: n for code, n in _derived().get("dependents", ())}


def relies() -> set[tuple[str, str, str]]:
    """Every direct dependence `(dependent, premise, field)`."""
    return set(_derived().get("relies", ()))


def load_bearing_rows(rows: list | None = None) -> list[str]:
    """One line per undecided document at or past `load_bearing`
    dependents, most relied on first."""
    threshold = current().load_bearing
    if threshold is None:
        return []
    rows = adr_pending.pending() if rows is None else rows
    heavy = [r for r in rows if (r.dependents or 0) >= threshold]
    heavy.sort(key=lambda r: (-(r.dependents or 0), r.code))
    return [f"{current().rel(r.path)}: {r.code} ({r.status}) has "
            f"{r.dependents} transitive dependent(s) — at least "
            f"{threshold}, so decide it or say what holds it back"
            for r in heavy]


def _retired(doc: ref_status.Doc) -> bool:
    return not doc.active and doc.status not in adr_pending.UNDECIDED


def unbounded_rows() -> list[str]:
    """`inactive-ok` directives that excuse a retired premise the
    acknowledging document depends on, and carry no `until <date>`."""
    if not current().reliance:
        return []
    docs = ref_status.load_docs()
    scan = ref_status.scan()
    out: set[str] = set()
    for dependent, premise, field in relies():
        source, target = docs.get(dependent), docs.get(premise)
        if source is None or target is None or not _retired(target):
            continue
        for site in scan.cited.get(premise, ()):
            ann = site.excused_by
            if (site.path != source.path or ann is None
                    or ann.kind != DIRECTIVE
                    or ann.directive.expires is not None):
                continue
            d = ann.directive
            scope = "" if d.scope == directives.LINE else f"-{d.scope}"
            out.add(f"{current().rel(d.path)}:{d.line}: `{DIRECTIVE}{scope}: "
                    f"{premise}` excuses a {target.status} document "
                    f"{dependent} depends on (`{field}`) with no "
                    f"`until <date>` — give it one, so whether "
                    f"{dependent} still holds is asked again")
    return sorted(out)
