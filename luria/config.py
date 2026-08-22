from __future__ import annotations
import os
import re
import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
CONFIG_NAME = 'luria.toml'
DEFAULTS: dict = {'issue_url': '', 'paths': {'docs': 'docs', 'decisions': 'record/decisions.d', 'design_principles': 'docs/design-principles.md', 'reports': 'docs/reports'}, 'fragments': {'record/changelog.d': 'CHANGELOG.md'}, 'code': {'globs': [], 'historical': ['CHANGELOG.md']}, 'schemes': {'ADR': {'dir': 'record/decisions.d', 'output': 'docs/decisions', 'active': 'Active', 'render': 'index'}}, 'remotes': {}, 'journals': {'devlog': {'dir': 'record/devlog.d', 'output': 'docs/devlog', 'granularity': 'month', 'title': 'Development log'}}, 'stale_days': 90, 'lint': {'fail_on': [], 'narrow_terms': []}, 'site': {'title': '', 'base_url': '', 'source_url': '', 'exclude': [], 'icon': '', 'logo': '', 'logo_dark': '', 'theme': {}}}
GITHUB_ISSUE_RE = re.compile('https?://github\\.com/([^/]+)/([^/]+)/issues\\b')

def find_root(start: Path | None=None) -> Path:
    if (env := os.environ.get('LURIA_ROOT')):
        return Path(env).resolve()
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONFIG_NAME).exists():
            return candidate
    for candidate in (here, *here.parents):
        if (candidate / '.git').exists():
            return candidate
    return here

def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out
TEMP_TAIL = 'tmp[a-z0-9]{5}'
_TEMP_TAIL_RE = re.compile(f'^{TEMP_TAIL}$')

def is_temp_tail(tail: str) -> bool:
    return bool(_TEMP_TAIL_RE.match(tail))

@dataclass(frozen=True)
class TagGroup:
    name: str
    tags: frozenset[str]
    require: str = 'any'
    excluded_by: frozenset[str] = frozenset()
REQUIRE_RULES = ('any', 'at-most-one', 'exactly-one')

@dataclass(frozen=True)
class Scheme:
    prefix: str
    dir: Path
    active: str = 'Active'
    render: str = 'index'
    output: Path | None = None
    allocate: str = 'filing'
    titles_generalize: bool = False
    requires: tuple[str, ...] = ()
    tag_groups: tuple[TagGroup, ...] = ()

    @property
    def view(self) -> Path:
        return self.output or self.dir

    @property
    def index_path(self) -> Path:
        return self.view / 'README.md'

    @property
    def tag_dir(self) -> Path:
        return self.view / 'tags'

    @property
    def stub(self) -> Path:
        return self.dir / 'README.stub'

    @property
    def tags_yaml(self) -> Path:
        return self.dir / 'tags.yaml'

    @property
    def statuses_yaml(self) -> Path:
        return self.dir / 'statuses.yaml'

    @property
    def pattern(self):
        return re.compile(f'\\b{self.prefix}[- ](?P<num>\\d{{1,4}})\\b')
    TEMP_TAIL = TEMP_TAIL

    @property
    def temp_pattern(self):
        return re.compile(f'\\b{self.prefix}-(?P<tail>{self.TEMP_TAIL})\\b')

    def temp_of(self, path: Path) -> str | None:
        m = re.fullmatch(f'{self.prefix}-({self.TEMP_TAIL})\\.md', path.name)
        return m.group(1) if m else None

    def temp_documents(self) -> dict[str, Path]:
        found: dict[str, Path] = {}
        for path in sorted(self.dir.glob('*.md')):
            tail = self.temp_of(path)
            if tail is not None:
                found[tail] = path
        return found

    def code(self, number: str | int) -> str:
        return f'{self.prefix}-{int(number):03d}'

    def filename(self, number: str | int) -> str:
        return f'{self.code(number)}.md'

    def number_of(self, path: Path) -> int | None:
        m = re.fullmatch(f'{self.prefix}-0*(\\d+)(?:-[^/]*)?\\.md', path.name, re.IGNORECASE)
        return int(m.group(1)) if m else None

    def documents(self) -> dict[int, Path]:
        found: dict[int, Path] = {}
        for path in sorted(self.dir.glob('*.md')):
            number = self.number_of(path)
            if number is not None:
                found.setdefault(number, path)
        return dict(sorted(found.items()))

@dataclass(frozen=True)
class RemoteScheme:
    prefix: str
    dir: str = ''
    document: str = ''
    anchor: str = ''
    url: str = ''

    def anchor_for(self, number: int) -> str:
        template = self.anchor or f'{self.prefix.lower()}-{{number}}'
        return template.format(number=number, prefix=self.prefix)

@dataclass(frozen=True)
class Remote:
    prefix: str
    repo: str = ''
    ref: str = 'main'
    dir: str = 'record/decisions.d'
    name: str = ''
    url: str = ''
    delim: str = '-'
    uid: str = ''
    schemes: dict[str, RemoteScheme] = field(default_factory=dict)

    @property
    def label(self) -> str:
        return self.name or self.repo or self.prefix

    def canon(self, tail: str) -> str:
        if self.uid:
            return tail
        prefix, number = tail.rsplit('-', 1)
        return f'{prefix.upper()}-{int(number):03d}'

    def base(self, dir: str | None=None) -> str:
        return f'https://github.com/{self.repo}/blob/{self.ref}/{(self.dir if dir is None else dir)}'.rstrip('/')

    def scheme_for(self, code: str) -> RemoteScheme | None:
        return self.schemes.get(code.rsplit('-', 1)[0].upper())

    def link(self, code: str, filename: str='') -> str:
        if self.uid:
            if not self.url:
                return ''
            m = re.fullmatch(self.uid, code)
            groups = m.groups() if m else ()
            return self.url.format(code, *groups, uid=code, prefix=self.prefix)
        prefix, number = code.rsplit('-', 1)
        number = int(number)
        scheme = self.scheme_for(code)
        if scheme is not None:
            if scheme.url:
                return scheme.url.format(code=code, number=number, prefix=prefix)
            if scheme.document and self.repo:
                return f"{self.base('')}/{scheme.document}#{scheme.anchor_for(number)}"
            if scheme.dir and self.repo:
                return f"{self.base(scheme.dir)}/{filename or code + '.md'}"
        if self.url:
            return self.url.format(code=code, number=number, prefix=prefix)
        if not self.repo:
            return ''
        return f"{self.base()}/{filename or code + '.md'}"

@dataclass(frozen=True)
class Fragment:
    target: Path
    style: str = 'append'

def _tag_groups(prefix: str, raw: dict) -> tuple[TagGroup, ...]:
    groups = []
    for name, spec in raw.items():
        rule = str(spec.get('require', 'any'))
        if rule not in REQUIRE_RULES:
            raise ValueError(f'luria.toml: schemes.{prefix}.tag_groups.{name} has require = {rule!r}; expected one of {list(REQUIRE_RULES)}')
        tags = frozenset((str(x) for x in spec.get('tags', ())))
        if not tags:
            raise ValueError(f'luria.toml: schemes.{prefix}.tag_groups.{name} lists no tags, so it constrains nothing')
        groups.append(TagGroup(name=name, tags=tags, require=rule, excluded_by=frozenset((str(x) for x in spec.get('excluded_by', ())))))
    return tuple(groups)

def _fragment(spec) -> Fragment:
    if isinstance(spec, dict):
        return Fragment(Path(spec.get('file') or spec.get('target') or ''), spec.get('style', 'append'))
    return Fragment(Path(spec))

@dataclass(frozen=True)
class Journal:
    name: str
    dir: Path
    output: Path
    granularity: str = 'month'
    title: str = 'Journal'
    blurb: str = ''
    _root: Path = Path('.')

    @property
    def rel_dir(self) -> str:
        try:
            return str(self.dir.relative_to(self._root))
        except ValueError:
            return self.dir.name

@dataclass(frozen=True)
class Site:
    title: str
    base_url: str
    source_url: str
    exclude: tuple[str, ...] = ()
    icon: Path | None = None
    logo: Path | None = None
    logo_dark: Path | None = None
    theme: dict = field(default_factory=dict)

@dataclass(frozen=True)
class Config:
    root: Path
    issue_url: str
    docs: Path
    decisions: Path
    design_principles: Path
    reports: Path
    fragments: dict[str, Fragment]
    code_globs: tuple[str, ...]
    historical: frozenset[Path]
    schemes: dict[str, Scheme]
    remotes: dict[str, Remote]
    journals: dict[str, Journal]
    stale_days: int
    fail_on: tuple[str, ...]
    narrow_terms: tuple[str, ...]
    site: Site
    _raw: dict = field(default_factory=dict, repr=False)

    def _index_scheme(self):
        return next((s for s in self.schemes.values() if s.render == 'index'), None)

    @property
    def index(self) -> Path:
        s = self._index_scheme()
        return s.index_path if s else self.decisions / 'README.md'

    @property
    def stub(self) -> Path:
        s = self._index_scheme()
        return s.stub if s else self.decisions / 'README.stub'

    @property
    def tags_yaml(self) -> Path:
        s = self._index_scheme()
        return s.tags_yaml if s else self.decisions / 'tags.yaml'

    @property
    def tag_dir(self) -> Path:
        s = self._index_scheme()
        return s.tag_dir if s else self.decisions / 'tags'

    @property
    def config_doc(self) -> Path:
        return self.docs / 'configuration.md'

    @property
    def record_doc(self) -> Path:
        return self.docs / 'record.md'

    @property
    def owns_schema(self) -> bool:
        return (self.root / 'luria' / 'config.py').resolve() == Path(__file__).resolve()

    @property
    def remotes_lock(self) -> Path:
        return self.root / 'remotes.lock.json'

    def is_generated(self, path: Path) -> bool:
        if path.parent == self.reports:
            return True
        if path == self.config_doc:
            return True
        if path == self.record_doc:
            return True
        for s in self.schemes.values():
            if s.render == 'index' and (path == s.index_path or path.parent == s.tag_dir):
                return True
            if s.output == path:
                return True
        return any((path.parent == j.output for j in self.journals.values()))

    def is_historical(self, path: Path) -> bool:
        if path in self.historical:
            return True
        if path.parent in {self.root / d for d in self.fragments}:
            return True
        return any((j.dir in path.parents or j.output in path.parents for j in self.journals.values()))

    def link_base(self, path: Path) -> Path:
        for name, fragment in self.fragments.items():
            if path.parent == self.root / name:
                return (self.root / fragment.target).parent
        for scheme in self.schemes.values():
            if scheme.render == 'document' and scheme.output and (path.parent == scheme.dir):
                return scheme.output.parent
            if scheme.render == 'index' and path == scheme.stub:
                return scheme.view
        for journal in self.journals.values():
            if journal.dir in path.parents:
                return journal.output
        return path.parent

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)
FAMILIES = ('schemes', 'fragments', 'journals', 'remotes')

def load(root: Path | None=None, text: str | None=None) -> Config:
    root = root or find_root()
    raw = DEFAULTS
    config_file = root / CONFIG_NAME
    if text is None and config_file.exists():
        text = config_file.read_text()
    if text is not None:
        parsed = tomllib.loads(text)
        parsed = parsed.get('luria', parsed)
        raw = _merge(DEFAULTS, parsed)
        for family in FAMILIES:
            if family in parsed:
                raw[family] = parsed[family]
    paths = raw['paths']
    return Config(root=root, issue_url=raw.get('issue_url', ''), docs=root / paths['docs'], decisions=root / paths['decisions'], design_principles=root / paths['design_principles'], reports=root / paths['reports'], fragments={k: _fragment(v) for k, v in raw['fragments'].items()}, code_globs=tuple(raw['code']['globs']), historical=frozenset((root / p for p in raw['code']['historical'])), schemes={prefix: Scheme(prefix, root / spec['dir'], spec.get('active', 'Active'), spec.get('render', 'index'), root / spec['output'] if spec.get('output') else None, spec.get('allocate', 'filing'), bool(spec.get('titles_generalize', False)), tuple(spec.get('requires', ())), _tag_groups(prefix, spec.get('tag_groups', {}))) for prefix, spec in raw['schemes'].items()}, remotes={prefix.upper(): Remote(prefix.upper(), repo=spec.get('repo', ''), ref=spec.get('ref', 'main'), dir=spec.get('dir', 'record/decisions.d'), name=spec.get('name', ''), url=spec.get('url', ''), delim=spec.get('delim', '-'), uid=spec.get('uid', ''), schemes={s.upper(): RemoteScheme(s.upper(), dir=sub.get('dir', ''), document=sub.get('document', ''), anchor=sub.get('anchor', ''), url=sub.get('url', '')) for s, sub in spec.get('schemes', {}).items()}) for prefix, spec in raw.get('remotes', {}).items()}, journals={name: Journal(name, dir=root / spec['dir'], output=root / spec['output'], granularity=spec.get('granularity', 'month'), title=spec.get('title', name.title()), blurb=spec.get('blurb', ''), _root=root) for name, spec in raw.get('journals', {}).items()}, stale_days=int(raw.get('stale_days', 90)), fail_on=tuple(raw['lint']['fail_on']), narrow_terms=tuple(raw['lint'].get('narrow_terms', [])), site=_site(raw, root), _raw=raw)

def _site(raw: dict, root: Path) -> Site:
    spec = raw.get('site', {})
    m = GITHUB_ISSUE_RE.match(raw.get('issue_url', '') or '')
    owner, repo = m.groups() if m else ('', '')
    return Site(title=spec.get('title') or repo or root.name, base_url=spec.get('base_url') or (f'{owner.lower()}.github.io/{repo}' if owner else ''), source_url=spec.get('source_url') or (f'https://github.com/{owner}/{repo}/blob/HEAD' if owner else ''), exclude=tuple(spec.get('exclude', ())), icon=root / spec['icon'] if spec.get('icon') else None, logo=root / spec['logo'] if spec.get('logo') else None, logo_dark=root / spec['logo_dark'] if spec.get('logo_dark') else None, theme=spec.get('theme', {}) or {})

@lru_cache(maxsize=1)
def current() -> Config:
    return load()

def reset() -> None:
    current.cache_clear()
