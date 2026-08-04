#!/usr/bin/env python3
"""Report ADRs still awaiting a decision, oldest first (ADR-007).

    luria pending                     # the table
    luria pending --stale-days 30     # a tighter "overdue" line
    luria pending --as-of 2026-08-03  # fixed clock, for tests

`Proposed` and `Deferred` are the two statuses that describe an *open* question:
"we haven't decided" and "we decided not to decide yet". Both are legitimate —
[ADR-003](../record/decisions.d/ADR-003.md) added `Deferred` precisely
so postponement could be stated rather than faked. What neither status records is
*how long*, and that is the whole signal: a decision proposed a week ago is
pending, the same one a year later is either overdue or was quietly settled in
code and never written down. The status field can't drift toward the truth on its
own, because nothing about "still Proposed" ever fails.

So the report supplies the missing axis — age — and one more that turns a list
into a priority: how often the ADR is cited. An old proposal nothing references
is a stalled idea; an old proposal 32 files cite is a decision the codebase has
already made without saying so.

The count here is every citation, acknowledged or not, because an acknowledged
one still means the codebase depends on the answer. `make ref-status` lists only
the unacknowledged ones, so its total is smaller — the headline names both so
the two reports visibly reconcile.

Like the non-Active reference report this ships beside, it warns and never
fails. An ADR can be legitimately open for a long time; only a human can say
which of these is overdue.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from . import adr_index as builder
from . import ref_status
from .config import current

UNDECIDED = ("Proposed", "Deferred")
DEFAULT_STALE_DAYS = 90


@dataclass(frozen=True)
class Pending:
    code: str                # `ADR-012`, `DP-004` — every scheme, not just one
    number: int
    status: str
    title: str
    date: dt.date | None
    cites: int
    unacknowledged: int      # of those, the ones `make ref-status` still lists
    path: Path

    def age(self, today: dt.date) -> int | None:
        return None if self.date is None else (today - self.date).days

    def is_stale(self, today: dt.date, stale_days: int) -> bool:
        age = self.age(today)
        return age is not None and age >= stale_days


def _date(meta: dict) -> dt.date | None:
    raw = meta.get("date")
    if isinstance(raw, dt.date):
        return raw
    try:
        return dt.date.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return None


def pending() -> list[Pending]:
    """Every undecided document in every scheme, oldest first; undated ones
    last — a document with no `date:` can't be aged, which is itself worth
    seeing.

    Not just decisions. A `Proposed` principle is an open question in exactly
    the same way, and a report that covered one scheme would go quietly blind
    the day a project configured a second (ADR-018)."""
    cited = ref_status.scan().cited
    rows = []
    for scheme in current().schemes.values():
        for doc in builder.load_scheme(scheme):
            status = re.split(r"\s+—\s+", doc.status, maxsplit=1)[0]
            if status not in UNDECIDED:
                continue
            sites = cited.get(doc.code, [])
            rows.append(Pending(doc.code, doc.number, status, doc.title,
                                _date(doc.meta), len(sites),
                                sum(1 for c in sites if c.excused_by is None),
                                doc.path))
    return sorted(rows, key=lambda r: (r.date is None, r.date, -r.cites, r.code))


def table(rows: list[Pending], today: dt.date, stale_days: int) -> list[str]:
    if not rows:
        return []
    width = max(len(r.title) for r in rows)
    code_width = max(len(r.code) for r in rows)
    lines = [f"{'age':>6}  {'status':<8}  {'code':<{code_width}}  "
             f"{'cites':>5}  title"]
    for r in rows:
        age = r.age(today)
        mark = "!" if r.is_stale(today, stale_days) else " "
        lines.append(
            f"{(f'{age}d' if age is not None else '?'):>6}{mark} {r.status:<8}  "
            f"{r.code:<{code_width}}  {r.cites:>5}  {r.title[:width]}"
        )
    return lines


def headline(rows: list[Pending], today: dt.date, stale_days: int) -> str:
    if not rows:
        return "pending decisions: none — every document is decided"
    ages = [a for a in (r.age(today) for r in rows) if a is not None]
    stale = sum(1 for r in rows if r.is_stale(today, stale_days))
    undated = sum(1 for r in rows if r.date is None)
    loud = sum(1 for r in rows if r.unacknowledged)
    parts = [f"{len(rows)} undecided document(s)"]
    if ages:
        parts.append(f"oldest {max(ages)} days")
    if stale:
        parts.append(f"{stale} over {stale_days} days")
    if undated:
        parts.append(f"{undated} undated")
    # Printed next to the reference report's count, these two look like an
    # off-by-one and are not: that report only lists documents with an
    # UNACKNOWLEDGED citation, which is exactly this number.
    if loud != len(rows):
        parts.append(f"{loud} with unacknowledged references")
    return "pending decisions: " + ", ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stale-days", type=int, default=current().stale_days,
                    help="flag rows at least this old")
    ap.add_argument("--as-of", help="treat this ISO date as today")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.as_of) if args.as_of else dt.date.today()
    rows = pending()
    print(headline(rows, today, args.stale_days), file=sys.stderr)
    for line in table(rows, today, args.stale_days):
        print(f"  {line}", file=sys.stderr)
    return 0            # a report, not a gate


if __name__ == "__main__":
    raise SystemExit(main())
