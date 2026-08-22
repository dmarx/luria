from __future__ import annotations
import os
import re
from pathlib import Path
from urllib.parse import unquote
from .config import current
TARGET_OK = 'target-ok'
LINK_RE = re.compile('\\[[^\\]\\n]*\\]\\(([^)\\s]+)\\)')
NOT_A_LOCAL_PATH = re.compile('^(?:[A-Za-z][A-Za-z0-9+.-]*:|//|/|#)')
PATTERN_CHARS = set('{}\\|()[]*?<>')

def _local_path(target: str) -> str | None:
    if NOT_A_LOCAL_PATH.match(target) or PATTERN_CHARS & set(target):
        return None
    path = unquote(target.split('#', 1)[0].split('?', 1)[0])
    return path or None

def broken(files: list[Path] | None=None) -> tuple[list[str], list[str]]:
    from . import directives, doc_refs
    cfg = current()
    flagged: list[str] = []
    stale: list[str] = []
    for path in files if files is not None else doc_refs.doc_files():
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        quoted = doc_refs.code_spans(text)
        base = cfg.link_base(path)
        found = directives.find(path, text, {TARGET_OK})
        used: set[tuple[int, str]] = set()
        for m in LINK_RE.finditer(text):
            if any((a <= m.start() < b for a, b in quoted)):
                continue
            target = m.group(1)
            rel = _local_path(target)
            if rel is None or Path(os.path.normpath(base / rel)).exists():
                continue
            line = text.count('\n', 0, m.start()) + 1
            ack = next((d for d in found if d.covers(line) and target in d.args), None)
            if ack is not None:
                used.add((ack.line, target))
                continue
            flagged.append(f'{cfg.rel(path)}:{line}: {target} resolves to nothing from {cfg.rel(base)}/, where this prose renders (`luria link --fix` writes code targets; this one is by hand)')
        for d in found:
            problem = directives.problems(d)
            for arg in d.args:
                if (d.line, arg) not in used:
                    problem = problem or f'`{TARGET_OK}: {arg}` matches no link'
                    stale.append(f'{cfg.rel(path)}:{d.line}: {problem}')
                    break
    return (flagged, stale)
