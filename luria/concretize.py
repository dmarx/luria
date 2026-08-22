from __future__ import annotations
import re
import sys
from pathlib import Path
from . import doc_refs
from .collect import _added_at
from .config import current

def pending() -> list[tuple[object, str, Path]]:
    out = []
    for scheme in current().schemes.values():
        temps = sorted(scheme.temp_documents().items(), key=lambda item: _added_at(item[1]))
        out += [(scheme, tail, path) for tail, path in temps]
    return out

def _record_alias(text: str, old_code: str) -> str:
    if re.search('^formerly:', text, flags=re.MULTILINE):
        return re.sub('^(formerly:(?:\\n- .*)*)', f'\\1\\n- {old_code}', text, count=1, flags=re.MULTILINE)
    return re.sub('^(status:.*)$', f'\\1\\nformerly:\\n- {old_code}', text, count=1, flags=re.MULTILINE)

def _rewrite_files(renames: list[tuple[str, str]]) -> int:
    cfg = current()
    files = list(doc_refs.doc_files())
    for pattern in cfg.code_globs:
        files += [p for p in cfg.root.glob(pattern) if p.is_file()]
    touched = 0
    seen = set()
    for path in files:
        if path in seen:
            continue
        seen.add(path)
        text = new = path.read_text()
        for old, target in renames:
            new = new.replace(old, target)
            if (low := old.lower()) != old:
                new = new.replace(low, target.lower())
        if new != text:
            path.write_text(new)
            touched += 1
    return touched

def run(check: bool=False) -> None:
    cfg = current()
    todo = pending()
    if check:
        if todo:
            print(f'luria concretize: {len(todo)} temporary code(s) awaiting concretization', file=sys.stderr)
            for scheme, tail, path in todo:
                print(f'  {scheme.prefix}-{tail}  {cfg.rel(path)}', file=sys.stderr)
            raise SystemExit(1)
        print('luria concretize: no temporary codes')
        return
    if not todo:
        print('luria concretize: nothing to do')
        return
    renames: list[tuple[str, str, Path, Path]] = []
    next_free = {s.prefix: max(s.documents(), default=0) + 1 for s, _, _ in todo}
    for scheme, tail, path in todo:
        number = next_free[scheme.prefix]
        next_free[scheme.prefix] = number + 1
        renames.append((f'{scheme.prefix}-{tail}', scheme.code(number), path, scheme.dir / scheme.filename(number)))
    _rewrite_files([(old, new) for old, new, _, _ in renames])
    for old, new, src, dest in renames:
        dest.write_text(_record_alias(src.read_text(), old))
        src.unlink()
        print(f'{old} → {new}')
    from . import adr_index
    adr_index.run()
if __name__ == '__main__':
    import fire
    fire.Fire(run)
