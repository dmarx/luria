from pathlib import Path
from luria.config import current

def decision(root: Path, number: int, status: str, title: str='A decision', summary: str='') -> Path:
    scheme = current().schemes['ADR']
    assert root == current().root, 'fixture root and LURIA_ROOT disagree'
    path = scheme.dir / f'ADR-{number:03d}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    front = [f'status: {status}', f'title: {title!r}', 'tags:', '- record', "date: '2026-01-01'"]
    if summary:
        front.append(f'summary: {summary!r}')
    path.write_text('---\n' + '\n'.join(front) + f'\n---\n\n# ADR-{number:03d}: {title}\n\nBody.\n')
    return path
