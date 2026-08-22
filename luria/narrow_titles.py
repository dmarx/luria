from __future__ import annotations
import re
from . import directives
from .adr_index import parse_frontmatter
from .config import current
ACK = 'broad-ok'

def _pattern(terms: tuple[str, ...]) -> re.Pattern | None:
    words = sorted({t.strip().lower() for t in terms if t.strip()})
    if not words:
        return None
    alt = '|'.join((re.escape(w) for w in words))
    return re.compile(f'\\b({alt})s?\\b', re.IGNORECASE)

def _acknowledged(path, text: str) -> set[str]:
    out: set[str] = set()
    for d in directives.find(path, text, {ACK}):
        out.update((a.strip().lower().rstrip('s') for a in d.args if a.strip()))
    return out

def rows() -> list[str]:
    cfg = current()
    pattern = _pattern(cfg.narrow_terms)
    if pattern is None:
        return []
    found: list[str] = []
    for scheme in cfg.schemes.values():
        if not scheme.titles_generalize:
            continue
        for number, path in scheme.documents().items():
            text = path.read_text(encoding='utf-8')
            meta, _ = parse_frontmatter(text)
            title = str(meta.get('title') or '').strip()
            if not title:
                continue
            hits = {m.lower().rstrip('s') for m in pattern.findall(title)}
            hits -= _acknowledged(path, text)
            if hits:
                found.append(f"{scheme.code(number)} names {', '.join(sorted(hits))} — state the pattern, not the artifact it was first noticed on ({cfg.rel(path)})")
    return sorted(found)
