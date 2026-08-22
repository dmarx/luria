from __future__ import annotations
import re
import sys
from pathlib import Path
from . import adr_pending, ci, ref_status
from .config import current
OPEN = '<!-- luria:badges -->'
CLOSE = '<!-- /luria:badges -->'
REGION_RE = re.compile(f'{re.escape(OPEN)}.*?{re.escape(CLOSE)}', re.DOTALL)
GOOD, ATTENTION = ('brightgreen', 'orange')

def counts() -> tuple[int, int]:
    docs = ref_status.load_docs()
    scan = ref_status.scan(docs=docs)
    return (len(adr_pending.pending()), len(ref_status.flagged(scan, docs)))

def badge(label: str, value: int, target: str) -> str:
    colour = GOOD if value == 0 else ATTENTION
    text = f"{label.replace(' ', '%20')}-{value}-{colour}"
    return f'[![{label}: {value}](https://img.shields.io/badge/{text})]({target})'

def report_link(filename: str) -> str:
    return current().rel(current().reports / filename)

def region() -> str:
    undecided, retired = counts()
    return '\n'.join([OPEN, badge('needs decision', undecided, report_link('pending-decisions.md')), badge('cited, not in force', retired, report_link('reference-status.md')), CLOSE])

def rewrite(text: str) -> str:
    return REGION_RE.sub(lambda _: region(), text, count=1)

def readme() -> Path:
    return current().root / 'README.md'

def run(write: bool=False, check: bool=False) -> None:
    path = readme()
    if not write and (not check):
        print(region())
        print(f'luria badges: printed only — `--write` rewrites the region in {current().rel(readme())}, `--check` fails when it is stale. In normal use `luria index` writes it with everything else.', file=sys.stderr)
        return
    if not path.exists() or OPEN not in path.read_text():
        print(f'luria badges: no {OPEN} region in {current().rel(path)} — add one where the badges belong:\n\n  {OPEN}\n  {CLOSE}\n', file=sys.stderr)
        return
    text = path.read_text()
    fresh = rewrite(text)
    if check:
        if fresh != text:
            print(f'{current().rel(path)}: badge counts are stale — {ci.regenerate_remedy()}', file=sys.stderr)
            raise SystemExit(1)
        print('luria badges: current')
        return
    path.write_text(fresh)
    undecided, retired = counts()
    print(f'badges: needs decision {undecided}, cited not in force {retired}')
if __name__ == '__main__':
    import fire
    fire.Fire(run)
