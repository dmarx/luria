import re
import subprocess
import sys
from pathlib import Path
from .config import current
TEMPLATE_NAME = '_template.md'
MARKER = '<!-- luria-insert-here -->'
MARKERS = (MARKER, '<!-- devlog-insert-here -->', '<!-- scriv-insert-here -->')
_COMMENT_RE = re.compile('<!--.*?-->', re.S)

def is_stub(body: str) -> bool:
    return not _COMMENT_RE.sub('', body).strip()

def find_marker(text: str) -> str | None:
    return next((m for m in MARKERS if m in text), None)

def collect(view_text: str, bodies: list[str], style: str='append', date: str='') -> str:
    marker = find_marker(view_text)
    if marker is None:
        raise ValueError(f'no insert marker — add {MARKER} where collected entries belong')
    real = [b.strip() for b in bodies if not is_stub(b)]
    if not real:
        return view_text
    head, _, tail = view_text.partition(marker)
    if style == 'changelog':
        block = f'## {date}\n\n' + '\n\n'.join(reversed(real))
        tail = tail.lstrip('\n')
        return f'{head}{marker}\n\n{block}' + ('\n\n' + tail if tail else '\n')
    block = '\n\n'.join(real)
    return f'{head.rstrip()}\n\n{block}\n\n{marker}{tail}'

def _added_at(path: Path) -> tuple[int, str]:
    try:
        out = subprocess.run(['git', 'log', '--diff-filter=A', '--format=%ct', '-1', '--', str(path)], cwd=current().root, capture_output=True, text=True, check=True).stdout.strip()
        if out:
            return (int(out), path.name)
    except (subprocess.CalledProcessError, ValueError, OSError):
        pass
    return (sys.maxsize, path.name)

def fragment_paths(fragment_dir: Path) -> list[Path]:
    if not fragment_dir.is_dir():
        return []
    return sorted((p for p in fragment_dir.glob('*.md') if p.name != TEMPLATE_NAME), key=_added_at)

def collect_dir(name: str, fragment) -> int:
    import datetime as dt
    cfg = current()
    paths = fragment_paths(cfg.root / name)
    if not paths:
        return 0
    view = cfg.root / fragment.target
    view.write_text(collect(view.read_text(), [p.read_text() for p in paths], style=fragment.style, date=dt.date.today().isoformat()))
    for p in paths:
        p.unlink()
    print(f'Collected {len(paths)} fragment(s) from {name} into {fragment.target}.')
    return len(paths)

def run(dir: str=None, commit: bool=False) -> None:
    cfg = current()
    wanted = {dir: cfg.fragments[dir]} if dir else cfg.fragments
    total = sum((collect_dir(name, frag) for name, frag in wanted.items()))
    if not total:
        print('No fragments to collect.')
        return
    if commit:
        subprocess.run(['git', 'add', '-A'], cwd=cfg.root, check=True)
        if subprocess.run(['git', 'diff', '--staged', '--quiet'], cwd=cfg.root).returncode == 0:
            print('Nothing to commit.')
            return
        subprocess.run(['git', 'commit', '-m', 'docs: collect fragments [skip ci]'], cwd=cfg.root, check=True)
if __name__ == '__main__':
    import fire
    fire.Fire(run)
