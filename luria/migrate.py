from __future__ import annotations
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from . import aliases as aliases_mod
from . import doc_refs, new as new_mod, remotes
from .config import current, is_temp_tail
MIGRATIONS_DIR = 'record/migrations.d'
BLAME_IGNORE = '.git-blame-ignore-revs'

@dataclass(frozen=True)
class Pair:
    old: str
    new: str

    @property
    def old_parts(self) -> tuple[str, int]:
        return aliases_mod.split(self.old)

    @property
    def new_parts(self) -> tuple[str, str]:
        prefix, tail = self.new.rsplit('-', 1)
        return (prefix, tail)

    @property
    def new_is_provisional(self) -> bool:
        return is_temp_tail(self.new_parts[1])

    @property
    def new_anchor_tail(self) -> str:
        tail = self.new_parts[1]
        return tail if self.new_is_provisional else str(int(tail))

@dataclass
class Plan:
    title: str
    mapping: list[Pair] = field(default_factory=list)
    composed: list[Pair] = field(default_factory=list)
    path_pairs: list[tuple[str, str]] = field(default_factory=list)
    moves: list[tuple[Path, Path]] = field(default_factory=list)
    stamps: dict[Path, str] = field(default_factory=dict)
    removals: list[Path] = field(default_factory=list)
    section_renames: list[tuple[Path, str, str]] = field(default_factory=list)
    config_files: list[Path] = field(default_factory=list)
    claimed_remotes: list[str] = field(default_factory=list)
    tombstones: list[tuple[Path, str]] = field(default_factory=list)
    copies: list[tuple[Path, Path, str, str]] = field(default_factory=list)
    minted: dict[str, set[str]] = field(default_factory=dict)
    relocated: set[str] = field(default_factory=set)
    old_addresses: dict[str, str] = field(default_factory=dict)

def _spec_path(ref: str) -> Path:
    cfg = current()
    direct = Path(ref)
    if direct.exists():
        return direct.resolve()
    mig_dir = cfg.root / MIGRATIONS_DIR
    for candidate in (mig_dir / ref, mig_dir / f'{ref}.toml'):
        if candidate.exists():
            return candidate
    matches = sorted(mig_dir.glob(f'{ref}*.toml')) if mig_dir.exists() else []
    if len(matches) == 1:
        return matches[0]
    have = ', '.join((p.name for p in sorted(mig_dir.glob('*.toml')))) if mig_dir.exists() else 'none'
    raise SystemExit(f'luria migrate: no spec matches {ref!r} in {MIGRATIONS_DIR}/ (have: {have})')

def _plan_rename(plan: Plan, op: dict) -> None:
    cfg = current()
    old_prefix, new_prefix = (op['from'].upper(), op['to'].upper())
    scheme = cfg.schemes.get(old_prefix)
    if scheme is None:
        raise SystemExit(f'luria migrate: no scheme {old_prefix!r} in config')
    if new_prefix in cfg.schemes and op.get('strategy') != 'supersede':
        raise SystemExit(f'luria migrate: scheme {new_prefix!r} already exists')
    docs = scheme.documents()
    if op.get('strategy') == 'supersede':
        target = cfg.schemes.get(new_prefix)
        if target is None:
            raise SystemExit(f'luria migrate: strategy="supersede" copies into an existing scheme — add {new_prefix!r} to luria.toml first')
        for number, path in docs.items():
            new_code, old_code = (target.code(number), scheme.code(number))
            plan.copies.append((path, target.dir / target.filename(number), old_code, new_code))
            plan.tombstones.append((path, f'Superseded — by {new_code}'))
        return
    for number, path in docs.items():
        old_code, new_code = (scheme.code(number), f'{new_prefix}-{number:03d}')
        new_path = path.with_name(f'{new_code}.md')
        plan.mapping.append(Pair(old_code, new_code))
        plan.moves.append((path, new_path))
        plan.stamps[new_path] = f'{old_prefix}-{number}'
        for remote_prefix in op.get('remotes', []):
            remote = cfg.remotes.get(remote_prefix.upper())
            delim = remote.delim if remote else '-'
            plan.composed.append(Pair(f'{remote_prefix.upper()}{delim}{old_code}', f'{remote_prefix.upper()}{delim}{new_code}'))
    configs = [cfg.root / 'luria.toml'] + [cfg.root / c for c in op.get('configs', [])]
    plan.claimed_remotes += [r.upper() for r in op.get('remotes', [])]
    for config_file in configs:
        if not config_file.exists():
            raise SystemExit(f'luria migrate: {config_file} not found')
        plan.config_files.append(config_file)
        plan.section_renames.append((config_file, f'[luria.schemes.{old_prefix}]', f'[luria.schemes.{new_prefix}]'))
        for remote_prefix in op.get('remotes', []):
            plan.section_renames.append((config_file, f'[luria.remotes.{remote_prefix}.schemes.{old_prefix}]', f'[luria.remotes.{remote_prefix}.schemes.{new_prefix}]'))
    if op.get('output') and scheme.output:
        old_rel = cfg.rel(scheme.output)
        plan.path_pairs.append((old_rel, op['output']))
        plan.removals.append(scheme.output)
        old_name, new_name = (Path(old_rel).name, Path(op['output']).name)
        if old_name != new_name and Path(old_rel).parent == Path(op['output']).parent:
            plan.path_pairs.append((old_name, new_name))

def _plan_move(plan: Plan, op: dict) -> None:
    cfg = current()
    old_code = aliases_mod.canon(op['doc'])
    if old_code is None:
        raise SystemExit(f"luria migrate: {op['doc']!r} is not a code")
    old_prefix, number = aliases_mod.split(old_code)
    source = cfg.schemes.get(old_prefix)
    target = cfg.schemes.get(op['to'].upper())
    if source is None or target is None:
        raise SystemExit(f"luria migrate: move_doc needs both schemes in config (have: {', '.join(cfg.schemes)})")
    path = source.documents().get(number)
    if path is None:
        raise SystemExit(f'luria migrate: {old_code} has no document')
    seen = plan.minted.setdefault(target.prefix, set())
    while (tail := new_mod._mint_tail(target)) in seen:
        pass
    seen.add(tail)
    new_code = f'{target.prefix}-{tail}'
    new_path = target.dir / f'{new_code}.md'
    if op.get('strategy') == 'supersede':
        plan.copies.append((path, new_path, old_code, new_code))
        plan.tombstones.append((path, f'Superseded — by {new_code}'))
        return
    plan.relocated.add(new_code)
    plan.old_addresses[f'#{old_prefix.lower()}-{number}' if source.render == 'document' else path.name] = new_code
    plan.mapping.append(Pair(old_code, new_code))
    plan.moves.append((path, new_path))
    plan.stamps[new_path] = f'{old_prefix}-{number}'

def build_plan(spec: dict, title: str) -> Plan:
    plan = Plan(title=title)
    for op in spec.get('operations', []):
        kind = op.get('op')
        if kind == 'rename_scheme':
            _plan_rename(plan, op)
        elif kind == 'move_doc':
            _plan_move(plan, op)
        else:
            raise SystemExit(f'luria migrate: unknown op {kind!r} (know: rename_scheme, move_doc)')
    return plan

def _tracked_files() -> list[Path]:
    cfg = current()
    out = subprocess.run(['git', 'ls-files'], cwd=cfg.root, capture_output=True, text=True, check=True)
    keep = []
    for name in out.stdout.splitlines():
        if name.startswith(MIGRATIONS_DIR):
            continue
        keep.append(cfg.root / name)
    return keep
URL_RE = re.compile('\\b[a-z][a-z0-9+.-]*://[^\\s<>)\\]\\"\']+', re.IGNORECASE)

def sweep_text(text: str, plan: Plan, paths: bool=True, source: Path=doc_refs.ANY_MD) -> tuple[str, int]:
    count = 0
    claimed = {p.old for p in plan.composed}

    def masked_spans(text: str, mask_urls: bool=False) -> list[tuple[int, int]]:
        spans = [(r.start, r.end) for r in remotes.references(text) if r.composed not in claimed]
        spans += [m.span() for m in doc_refs.FORMERLY_RE.finditer(text)]
        if mask_urls:
            spans += [m.span() for m in URL_RE.finditer(text)]
        return spans

    def swap(text: str, pattern: str, repl, mask_urls: bool=False) -> str:
        nonlocal count
        spans = masked_spans(text, mask_urls)

        def guarded(m: re.Match) -> str:
            nonlocal count
            if any((a <= m.start() < b for a, b in spans)):
                return m.group(0)
            count += 1
            return repl(m) if callable(repl) else repl
        return re.sub(pattern, guarded, text)

    def swap_pair(text: str, pair: Pair) -> str:
        old_p, old_n = pair.old_parts
        new_p, new_tail = pair.new_parts

        def code_repl(m: re.Match) -> str:
            sep, digits = (m.group(1), m.group(2))
            if pair.new_is_provisional:
                return f'{new_p}{sep}{new_tail}'
            number = int(new_tail)
            spelled = f'{number:03d}' if digits != str(old_n) else str(number)
            return f'{new_p}{sep}{spelled}'
        text = swap(text, f'(?<![A-Za-z0-9-]){re.escape(old_p)}([- ])(0*{old_n})(?!\\d)', code_repl)
        if pair.new in plan.relocated:
            return text
        text = swap(text, f'(?<=#){re.escape(old_p.lower())}-0*{old_n}(?!\\d)', f'{new_p.lower()}-{pair.new_anchor_tail}')
        return swap(text, f'(?<=name=\\"){re.escape(old_p.lower())}-0*{old_n}(?=\\")', f'{new_p.lower()}-{pair.new_anchor_tail}')

    def unlink_relocated(text: str) -> str:
        for old_addr, new_code in sorted(plan.old_addresses.items()):
            text = swap(text, f'\\[[^\\]]*\\]\\([^)]*{re.escape(old_addr)}\\)', new_code)
        return text

    def respell_relocated(text: str) -> str:
        targets: dict[tuple[str, int], Pair] = {(pair.old_parts[0].upper(), pair.old_parts[1]): pair for pair in plan.mapping if pair.new in plan.relocated}
        if not targets:
            return text
        out, cursor = ([], 0)
        for ref in doc_refs.find_refs(text, source):
            if ref.kind != 'scheme' or ref.code:
                continue
            pair = targets.get((ref.prefix.upper(), ref.num))
            if pair is None:
                continue
            prefix, number = pair.old_parts
            if re.fullmatch(f'{re.escape(prefix)}[- ]0*{number}', ref.text, re.IGNORECASE):
                continue
            out.append(text[cursor:ref.start])
            out.append(pair.new)
            cursor = ref.end
            nonlocal count
            count += 1
        out.append(text[cursor:])
        return ''.join(out)
    text = unlink_relocated(text)
    text = respell_relocated(text)
    for pair in plan.composed:
        text = swap_pair(text, pair)
    for pair in plan.mapping:
        text = swap_pair(text, pair)
    if paths:
        for old, new in plan.path_pairs:
            text = swap(text, re.escape(old), new, mask_urls=True)
    return (text, count)
SECTION_RE = re.compile('^\\s*\\[([^\\]]+)\\]\\s*(?:#.*)?$')

def config_paths_pass(text: str, plan: Plan) -> str:
    out = []
    section = ''
    for line in text.splitlines(keepends=True):
        if (m := SECTION_RE.match(line)):
            section = m.group(1)
        frozen = False
        if (m2 := re.match('(?:luria\\.)?remotes\\.([A-Za-z0-9]+)', section)):
            frozen = m2.group(1).upper() not in plan.claimed_remotes
        if not frozen:
            for old, new in plan.path_pairs:
                line = line.replace(old, new)
        out.append(line)
    return ''.join(out)

def _stamp_formerly(path: Path, old_code: str) -> None:
    text = path.read_text()
    if not text.startswith('---\n'):
        raise SystemExit(f'luria migrate: {path} has no frontmatter to stamp')
    m = re.search('^formerly:\\n((?:- .*\\n)*)', text, flags=re.MULTILINE)
    if m:
        path.write_text(text[:m.end()] + f'- {old_code}\n' + text[m.end():])
    else:
        head, rest = text.split('\n', 1)
        path.write_text(f'{head}\nformerly:\n- {old_code}\n{rest}')

def _git(args: list[str]) -> str:
    out = subprocess.run(['git', *args], cwd=current().root, capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"luria migrate: git {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout.strip()

def apply(plan: Plan) -> tuple[int, int]:
    cfg = current()
    for old_path, new_path in plan.moves:
        _git(['mv', str(old_path), str(new_path)])
    for new_path, old_code in plan.stamps.items():
        _stamp_formerly(new_path, old_code)
    for source, new_path, old_code, new_code in plan.copies:
        text = source.read_text().replace(old_code, new_code)
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.write_text(text)
    for source, status in plan.tombstones:
        text = source.read_text()
        text = re.sub('^status: .*$', f'status: {status}', text, count=1, flags=re.MULTILINE)
        source.write_text(text)
    for config_file, old_header, new_header in plan.section_renames:
        text = config_file.read_text()
        if old_header in text:
            config_file.write_text(text.replace(old_header, new_header))
    for config_file in plan.config_files:
        config_file.write_text(config_paths_pass(config_file.read_text(), plan))
    for stale_view in plan.removals:
        if stale_view.exists():
            _git(['rm', '-q', str(stale_view)])
    files = swept = 0
    if plan.mapping or plan.composed or plan.path_pairs:
        for path in _tracked_files():
            live = path
            for old_path, new_path in plan.moves:
                if path == old_path:
                    live = new_path
            if not live.exists():
                continue
            try:
                text = live.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            if doc_refs.unlinted(live, text):
                continue
            new, count = sweep_text(text, plan, paths=live not in plan.config_files, source=live)
            if count:
                live.write_text(new)
                files += 1
                swept += count
    aliases_mod.reset()
    if plan.relocated:
        adrs, anchors = (doc_refs.adr_paths(), doc_refs.dp_anchors())
        for path in doc_refs.doc_files():
            if not path.exists():
                continue
            try:
                text = path.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            if doc_refs.unlinted(path, text):
                continue
            linked, n = doc_refs.linkify(text, path, adrs, anchors)
            if n:
                path.write_text(linked)
    return (files, swept)

def describe(plan: Plan) -> list[str]:
    lines = [f'migration: {plan.title}']
    for pair in plan.mapping:
        lines.append(f'  {pair.old} -> {pair.new}')
    for pair in plan.composed:
        lines.append(f'  {pair.old} -> {pair.new}  (composed)')
    for old, new in plan.path_pairs:
        lines.append(f'  {old} -> {new}  (path)')
    for old_path, new_path in plan.moves:
        lines.append(f'  git mv {current().rel(old_path)} {current().rel(new_path)}')
    for source, new_path, old_code, new_code in plan.copies:
        lines.append(f'  copy {current().rel(source)} -> {current().rel(new_path)}  ({old_code} superseded by {new_code})')
    for config_file, old_header, new_header in plan.section_renames:
        lines.append(f'  {current().rel(config_file)}: {old_header} -> {new_header}')
    return lines

def _blame_ignore(sha: str, title: str) -> None:
    path = current().root / BLAME_IGNORE
    stamp = f'# luria migrate: {title}\n{sha}\n'
    path.write_text((path.read_text() if path.exists() else '# Commits git blame should read through.\n') + stamp)

def run(spec: str, dry_run: bool=False, commit: bool=False) -> None:
    spec_path = _spec_path(str(spec))
    parsed = tomllib.loads(spec_path.read_text())
    title = parsed.get('title') or spec_path.stem
    plan = build_plan(parsed, title)
    if dry_run:
        would = 0
        for path in _tracked_files():
            try:
                _, count = sweep_text(path.read_text(), plan, source=path)
            except (UnicodeDecodeError, OSError):
                continue
            would += 1 if count else 0
        for line in describe(plan) + [f'  would sweep {would} file(s)']:
            print(line)
        return
    files, swept = apply(plan)
    print(f'migrated: {len(plan.moves)} move(s), {len(plan.copies)} cop(y/ies), {swept} rewrite(s) in {files} file(s)')
    if commit:
        _git(['add', '-A'])
        _git(['commit', '-m', f'Migration: {title}\n\nExecuted by `luria migrate` from {current().rel(spec_path)} (ADR-040).'])
        sha = _git(['rev-parse', 'HEAD'])
        _blame_ignore(sha, title)
        _git(['add', BLAME_IGNORE])
        _git(['commit', '-m', f'Blame reads through the {title!r} migration'])
        print(f'committed {sha[:12]} and appended it to {BLAME_IGNORE}')
    else:
        print(f'next: `luria index`, `luria lint`, review the diff, then commit — and append the migration commit to {BLAME_IGNORE} (or rerun with --commit)')
if __name__ == '__main__':
    import fire
    fire.Fire(run)
