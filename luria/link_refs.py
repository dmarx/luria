from __future__ import annotations
from pathlib import Path
from . import doc_refs
from .config import current

def run(*paths: str, fix: bool=False) -> None:
    files = [Path(p).resolve() for p in paths] or doc_refs.doc_files()
    adrs, anchors = (doc_refs.adr_paths(), doc_refs.dp_anchors())
    total = 0
    for path in files:
        text = path.read_text()
        new, count = doc_refs.linkify(text, path, adrs, anchors)
        if not count:
            continue
        total += count
        print(f'{current().rel(path)}: {count} reference(s)')
        if fix:
            path.write_text(new)
    verb = 'linked' if fix else 'would link'
    print(f'{verb} {total} reference(s) in {len(files)} file(s)')
if __name__ == '__main__':
    import fire
    fire.Fire(run)
