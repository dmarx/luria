from __future__ import annotations
import datetime as dt
import re
import sys
from pathlib import Path
from . import journal as journal_mod
from .config import current
TEMPLATE_NAME = '_template.md'
FALLBACK = "---\nstatus: Proposed\ntitle: '{title}'\ntags:\n- record\ndate: '{date}'\n---\n\n# {code}: {title}\n\nWhy this needed deciding, what was decided, and what was rejected.\n"

def kinds() -> dict[str, tuple[str, object]]:
    cfg = current()
    out: dict[str, tuple[str, object]] = {}
    for prefix, scheme in cfg.schemes.items():
        out[prefix.lower()] = ('scheme', scheme)
    for name in cfg.fragments:
        out[Path(name).name.removesuffix('.d')] = ('fragment', name)
    for name, jrnl in cfg.journals.items():
        out[name] = ('journal', jrnl)
    out.setdefault('migration', ('migration', None))
    return out

def default_kind() -> str | None:
    journals = list(current().journals)
    return journals[0] if len(journals) == 1 else None

def _sub_line(text: str, field: str, value: str) -> str:
    pattern = re.compile(f'^{field}:.*(?:\\n(?:  |- ).*)*', re.MULTILINE)
    if field == 'tags':
        replacement = 'tags:\n' + '\n'.join((f'- {t.strip()}' for t in value.split(',') if t.strip()))
    elif field == 'summary':
        replacement = f'summary: >-\n  {value}'
    else:
        replacement = f'{field}: {value!r}'
    return pattern.sub(replacement, text, count=1)

def _mint_tail(scheme) -> str:
    import secrets
    import string
    taken = scheme.temp_documents()
    while True:
        tail = 'tmp' + ''.join((secrets.choice(string.ascii_lowercase + string.digits) for _ in range(5)))
        if tail not in taken:
            return tail

def new_scheme_doc(scheme, fields: dict[str, str]) -> Path:
    if scheme.allocate == 'merge':
        stem = f'{scheme.prefix}-{_mint_tail(scheme)}'
        code = stem
    else:
        number = max(scheme.documents(), default=0) + 1
        code = f'{scheme.prefix}-{number:03d}'
        stem = code
    today = dt.date.today().isoformat()
    template = scheme.dir / TEMPLATE_NAME
    if template.exists():
        text = template.read_text()
        text = text.replace(f'{scheme.prefix}-NNN', code)
        text = re.sub('^date: .*$', f"date: '{today}'", text, count=1, flags=re.MULTILINE)
    else:
        text = FALLBACK.format(code=code, date=today, title='Stated as the thing you did')
    title = fields.pop('title', None)
    if title is not None:
        old_title = None
        m = re.search('^title: (.*)$', text, flags=re.MULTILINE)
        if m:
            old_title = m.group(1).strip().strip('\'"')
        text = _sub_line(text, 'title', title)
        if old_title:
            text = text.replace(f'# {code}: {old_title}', f'# {code}: {title}')
    for field, value in fields.items():
        text = _sub_line(text, field, value)
    path = scheme.dir / f'{stem}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path

def new_fragment(dir_name: str, name: str | None) -> Path:
    frag_dir = current().root / dir_name
    if name:
        path = frag_dir / f"{name.removesuffix('.md')}.md"
        if path.exists():
            return path
    else:
        stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
        path = frag_dir / f'{stamp}.md'
    template = frag_dir / TEMPLATE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(template.read_text() if template.exists() else '### Changed\n\n- \n')
    return path
MIGRATION_TEMPLATE = '# A migration spec (ADR-040): the executable plan and the audit trail in one\n# artifact. `luria migrate {number} --dry-run` prints what it would do.\n# This file is deliberately never swept — its mapping remembers the old\n# spellings, which is its job.\ntitle = "{title}"\nissue = ""\n\n# [[operations]]\n# op = "rename_scheme"\n# from = "OLD"\n# to = "NEW"\n# output = "docs/new-view.md"       # optional: the rendered view moves too\n# remotes = []                      # remotes that mirror THIS project\n# configs = []                      # extra config files carrying the scheme\n\n# [[operations]]\n# op = "move_doc"\n# doc = "OLD-4"\n# to = "NEW"                        # auto-numbered in the target scheme\n# strategy = "supersede"            # optional: copy + tombstone, no rewrite\n'

def new_migration(fields: dict[str, str], name: str | None) -> Path:
    from .migrate import MIGRATIONS_DIR
    mig_dir = current().root / MIGRATIONS_DIR
    taken = [int(m.group(1)) for p in (mig_dir.glob('*.toml') if mig_dir.exists() else []) if (m := re.match('(\\d{4})-', p.name))]
    number = f'{max(taken, default=0) + 1:04d}'
    title = fields.get('title') or 'What moves, and why'
    slug = name or re.sub('[^a-z0-9]+', '-', title.lower()).strip('-')
    path = mig_dir / f'{number}-{slug}.toml'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(MIGRATION_TEMPLATE.format(number=number, title=title))
    return path

def new_entry(kind: str | None, fields: dict[str, str], name: str | None) -> Path:
    available = kinds()
    kind = kind or default_kind()
    if kind is None or kind not in available:
        raise SystemExit(f'luria new: unknown kind {kind!r} — this project scaffolds: ' + ', '.join(sorted(available)))
    what, target = available[kind]
    if what == 'scheme':
        return new_scheme_doc(target, dict(fields))
    if what == 'fragment':
        return new_fragment(target, name)
    if what == 'migration':
        return new_migration(dict(fields), name)
    title = fields.get('title') or 'A sentence-shaped title'
    return journal_mod.new(target, title, dt.datetime.now())

def run(kind: str=None, title: str=None, status: str=None, summary: str=None, tags: str=None, name: str=None) -> None:
    fields = {k: v for k, v in [('title', title), ('status', status), ('summary', summary), ('tags', tags)] if v}
    print(current().rel(new_entry(kind, fields, name)))
if __name__ == '__main__':
    import fire
    fire.Fire(run)
