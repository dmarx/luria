from __future__ import annotations
import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from . import adr_index as builder
from . import ref_status
from .config import current
UNDECIDED = ('Proposed', 'Deferred')
DEFAULT_STALE_DAYS = 90

@dataclass(frozen=True)
class Pending:
    code: str
    number: int
    status: str
    title: str
    date: dt.date | None
    cites: int
    unacknowledged: int
    path: Path

    def age(self, today: dt.date) -> int | None:
        return None if self.date is None else (today - self.date).days

    def is_stale(self, today: dt.date, stale_days: int) -> bool:
        age = self.age(today)
        return age is not None and age >= stale_days

def _date(meta: dict) -> dt.date | None:
    raw = meta.get('date')
    if isinstance(raw, dt.date):
        return raw
    try:
        return dt.date.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return None

def pending() -> list[Pending]:
    cited = ref_status.scan().cited
    rows = []
    for scheme in current().schemes.values():
        for doc in builder.load_scheme(scheme):
            status = re.split('\\s+—\\s+', doc.status, maxsplit=1)[0]
            if status not in UNDECIDED:
                continue
            sites = cited.get(doc.code, [])
            rows.append(Pending(doc.code, doc.number, status, doc.title, _date(doc.meta), len(sites), sum((1 for c in sites if c.excused_by is None)), doc.path))
    return sorted(rows, key=lambda r: (r.date is None, r.date, -r.cites, r.code))

def table(rows: list[Pending], today: dt.date, stale_days: int) -> list[str]:
    if not rows:
        return []
    width = max((len(r.title) for r in rows))
    code_width = max((len(r.code) for r in rows))
    lines = [f"{'age':>6}  {'status':<8}  {'code':<{code_width}}  {'cites':>5}  title"]
    for r in rows:
        age = r.age(today)
        mark = '!' if r.is_stale(today, stale_days) else ' '
        lines.append(f"{(f'{age}d' if age is not None else '?'):>6}{mark} {r.status:<8}  {r.code:<{code_width}}  {r.cites:>5}  {r.title[:width]}")
    return lines

def headline(rows: list[Pending], today: dt.date, stale_days: int) -> str:
    if not rows:
        return 'pending decisions: none — every document is decided'
    ages = [a for a in (r.age(today) for r in rows) if a is not None]
    stale = sum((1 for r in rows if r.is_stale(today, stale_days)))
    undated = sum((1 for r in rows if r.date is None))
    loud = sum((1 for r in rows if r.unacknowledged))
    parts = [f'{len(rows)} undecided document(s)']
    if ages:
        parts.append(f'oldest {max(ages)} days')
    if stale:
        parts.append(f'{stale} over {stale_days} days')
    if undated:
        parts.append(f'{undated} undated')
    if loud != len(rows):
        parts.append(f'{loud} with unacknowledged references')
    return 'pending decisions: ' + ', '.join(parts)

def run(stale_days: int=None, as_of: str=None) -> None:
    stale_days = current().stale_days if stale_days is None else stale_days
    today = dt.date.fromisoformat(as_of) if as_of else dt.date.today()
    rows = pending()
    print(headline(rows, today, stale_days), file=sys.stderr)
    for line in table(rows, today, stale_days):
        print(f'  {line}', file=sys.stderr)
if __name__ == '__main__':
    import fire
    fire.Fire(run)
