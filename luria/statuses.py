from __future__ import annotations
import yaml
CLOSED = ('Active', 'Proposed', 'Deferred', 'Superseded', 'Rejected')

def declared(scheme) -> dict[str, dict]:
    path = scheme.statuses_yaml
    if not path.exists():
        return {}
    loaded = yaml.safe_load(path.read_text()) or {}
    return {k: v or {} for k, v in loaded.items()}

def problems(scheme) -> list[str]:
    from .config import current
    bad = [k for k in declared(scheme) if k not in CLOSED]
    if not bad:
        return []
    rel = current().rel(scheme.statuses_yaml)
    return [f"{rel}: {k!r} is not a status (want one of: {', '.join(CLOSED)}) — the vocabulary is closed (ADR-003)" for k in bad]

def undeclared(scheme, status: str) -> bool:
    vocab = declared(scheme)
    return bool(vocab) and status.split(' — ')[0].strip() not in vocab

def legend(scheme) -> str:
    vocab = declared(scheme)
    if not vocab:
        return ''
    rows = []
    for status, meta in vocab.items():
        label = meta.get('label', '')
        blurb = meta.get('blurb', '')
        text = f'{blurb[:1].upper()}{blurb[1:]}' if blurb else ''
        rows.append(f'| `{status}` | {label} | {text} |')
    return "What the status column means in this scheme — the words are luria's, the meanings are this project's.\n\n| Status | | Means |\n|---|---|---|\n" + '\n'.join(rows) + '\n'
FLOOR = 10

def uniform(scheme) -> tuple[str, int] | None:
    from . import adr_index
    if scheme.render == 'document':
        return None
    vocab = declared(scheme)
    if len(vocab) == 1:
        return None
    found: list[str] = []
    for path in [*scheme.documents().values(), *scheme.temp_documents().values()]:
        meta, _ = adr_index.parse_frontmatter(path.read_text())
        status = str((meta or {}).get('status', '')).strip()
        if status:
            found.append(status.split(' — ')[0].strip())
    if len(found) < FLOOR or len(set(found)) != 1:
        return None
    return (found[0], len(found))

def uniform_rows() -> list[str]:
    from .config import current
    rows = []
    for prefix, scheme in current().schemes.items():
        if (hit := uniform(scheme)):
            status, count = hit
            rows.append(f'{prefix}: {count}/{count} at `{status}`')
    return rows
