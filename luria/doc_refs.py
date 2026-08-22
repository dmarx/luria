from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
import yaml
from . import directives, remotes
from .adr_index import parse_frontmatter
from .config import Config, current
DP_RE = re.compile('\\b(?:(?:design[- ])?principles?|DP)(?:\\.md)?\\s*(?P<bold>\\*\\*)?\\s*#(?P<num>\\d{1,3})\\b(?(bold)\\*\\*)', re.IGNORECASE)
DP_CHAIN_RE = re.compile('[ \\t]*(?:,|;|and|or|&|/|\\+)[ \\t]*(?P<ref>(?P<bold>\\*\\*)?#(?P<num>\\d{1,3})\\b(?(bold)\\*\\*))')
ADR_RE = re.compile('\\bADR[- ](?P<num>\\d{1,4})\\b')
ISSUE_RE = re.compile('(?<![\\w&#/])#(?P<num>\\d{1,4})(?!\\w)')
ISSUE_CUE_RE = re.compile('(?:\\bissues?|\\bPRs?|\\bpull requests?|\\bresolves?|\\bfix(?:es|ed)?|\\bcloses?|\\btracked in|\\btoward)\\s*(?:#\\d{1,4}[\\s,;]*(?:and|or|&|/|\\+)?\\s*)*$', re.IGNORECASE)

@dataclass(frozen=True)
class Ref:
    kind: str
    num: int
    start: int
    end: int
    text: str
    line: int
    remote: str = ''
    code: str = ''
    prefix: str = ''

    def describe(self) -> str:
        if self.kind == 'scheme':
            if self.code:
                return f'{self.prefix}-{self.code}'
            return f'{self.prefix}-{self.num:03d}'
        if self.kind == 'remote':
            return self.text or f'{self.remote}-{self.code}'
        return f'#{self.num}'
FENCE_RE = re.compile('^[ \\t]{0,3}(?P<fence>```+|~~~+)', re.MULTILINE)
CODE_SPAN_RE = re.compile('(?P<ticks>`+)(?:.|\\n)*?(?P=ticks)')
COMMENT_RE = re.compile('<!--(?:.|\\n)*?-->')
AUTOLINK_RE = re.compile('<[a-zA-Z][a-zA-Z0-9+.-]*:[^<>\\s]*>')
BARE_URL_RE = re.compile('(?<![(<])\\b[a-z][a-z0-9+.-]*://[^\\s<>)\\]]+')
LINK_RE = re.compile('!?\\[(?P<label>[^\\]]*)\\]\\((?P<target>[^)]*)\\)')
REF_LINK_RE = re.compile('!?\\[(?P<label>[^\\]]*)\\]\\[[^\\]]*\\]')
LINK_DEF_RE = re.compile('^[ \\t]{0,3}\\[[^\\]]+\\]:.*$', re.MULTILINE)
LINK_DEF_LABEL_RE = re.compile('^[ \\t]{0,3}\\[([^\\]]+)\\]:', re.MULTILINE)
SHORTCUT_RE = re.compile('!?\\[([^\\]\\[]+)\\](?![(\\[:])')
HTML_ANCHOR_RE = re.compile('<a\\b[^>]*>(?:.|\\n)*?</a>', re.IGNORECASE)
HTML_TAG_RE = re.compile('<[/!]?[A-Za-z][^<>]*>')
HTML_BLOCK_TAGS = 'address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h1|h2|h3|h4|h5|h6|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|section|source|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul'
HTML_BLOCK_START_RE = re.compile(f'^ {{0,3}}</?(?:{HTML_BLOCK_TAGS})(?:[ \\t/>]|$)', re.IGNORECASE)

def _frontmatter_span(text: str) -> tuple[int, int] | None:
    if not text.startswith('---\n'):
        return None
    end = text.find('\n---\n', 3)
    return None if end == -1 else (0, end + 5)
PROSE_KEYS = ('summary', 'origin')
FORMERLY_RE = re.compile('^formerly:\\n(?:- .*\\n)*', re.MULTILINE)
PROSE_KEY_RE = re.compile('^(?:' + '|'.join(PROSE_KEYS) + '):', re.MULTILINE)
NEXT_KEY_RE = re.compile('^(?=[A-Za-z_][\\w-]*:|---[ \\t]*$)', re.MULTILINE)

def prose_spans(text: str) -> list[tuple[int, int]]:
    fm = _frontmatter_span(text)
    if not fm:
        return []
    head = text[:fm[1]]
    spans = []
    for key in PROSE_KEY_RE.finditer(head):
        nxt = NEXT_KEY_RE.search(head, key.end())
        spans.append((key.end(), nxt.start() if nxt else len(head)))
    return spans

def in_prose(spans: list[tuple[int, int]], pos: int) -> bool:
    return any((a <= pos < b for a, b in spans))

def _fence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    open_at: int | None = None
    marker = ''
    for m in FENCE_RE.finditer(text):
        fence = m.group('fence')
        if open_at is None:
            open_at, marker = (m.start(), fence[0] * 3)
        elif fence.startswith(marker):
            end = text.find('\n', m.end())
            spans.append((open_at, len(text) if end == -1 else end + 1))
            open_at = None
    if open_at is not None:
        spans.append((open_at, len(text)))
    return spans

def _code_span_spans(text: str) -> list[tuple[int, int]]:
    fences = _fence_spans(text)
    regions: list[tuple[int, int]] = []
    cursor = 0
    for a, b in fences:
        if cursor < a:
            regions.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < len(text):
        regions.append((cursor, len(text)))
    spans: list[tuple[int, int]] = []
    for a, b in regions:
        offset = a
        for i, part in enumerate(re.split('((?<=\\n)[ \\t]*\\n)', text[a:b])):
            if i % 2 == 0:
                for m in CODE_SPAN_RE.finditer(part):
                    spans.append((offset + m.start(), offset + m.end()))
            offset += len(part)
    return spans

def html_block_spans(text: str) -> list[tuple[int, int]]:
    fences = _fence_spans(text)

    def fenced(pos: int) -> bool:
        return any((a <= pos < b for a, b in fences))
    spans: list[tuple[int, int]] = []
    pos = 0
    open_at: int | None = None
    for line in text.splitlines(keepends=True):
        blank = not line.strip()
        if open_at is None:
            if not fenced(pos) and HTML_BLOCK_START_RE.match(line):
                open_at = pos
        elif blank:
            spans.append((open_at, pos))
            open_at = None
        pos += len(line)
    if open_at is not None:
        spans.append((open_at, len(text)))
    return spans

def code_spans(text: str) -> list[tuple[int, int]]:
    return _fence_spans(text) + _code_span_spans(text)

def in_html_block(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any((a <= pos < b for a, b in spans))
UNEXEMPT_REGIONS = {'codeblock': _fence_spans, 'inline-code': _code_span_spans}
ANY_MD = Path('prose.md')
UNLINTED = 'unlinted'

def unlinted(path: Path, text: str) -> bool:
    return any((d.scope == directives.FILE for d in directives.find(path, text, {UNLINTED})))

def link_base(path: Path) -> Path:
    return current().link_base(path)

def unexempt_spans(text: str, path: Path) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for d in directives.find(path, text, {'unexempt'}):
        for arg in d.args:
            spans = UNEXEMPT_REGIONS.get(arg.lower())
            if spans is None:
                continue
            for start, end in spans(text):
                first = text.count('\n', 0, start) + 1
                last = text.count('\n', 0, max(start, end - 1)) + 1
                if any((d.covers(n) for n in range(first, last + 1))):
                    out.append((start, end))
    return out

def directive_problems(path: Path, text: str) -> list[str]:
    out = []
    for d in directives.find(path, text, {'unexempt'}):
        problem = directives.problems(d, set(UNEXEMPT_REGIONS))
        if problem:
            out.append(f"{path.name}:{d.line}: {problem} (known: {', '.join(sorted(UNEXEMPT_REGIONS))})")
    for d in directives.find(path, text, {UNLINTED}):
        if d.scope != directives.FILE:
            out.append(f'{path.name}:{d.line}: `unlinted` is file-scoped by design — write `unlinted-file:`')
    return out

def masked(text: str, path: Path=ANY_MD) -> list[bool]:
    mask = [False] * len(text)

    def cover(start: int, end: int) -> None:
        for i in range(max(0, start), min(len(text), end)):
            mask[i] = True
    fm = _frontmatter_span(text)
    if fm:
        cover(*fm)
        for span in prose_spans(text):
            for i in range(*span):
                mask[i] = False
    for span in _fence_spans(text):
        cover(*span)
    for span in _code_span_spans(text):
        cover(*span)
    for regex in (COMMENT_RE, AUTOLINK_RE, BARE_URL_RE, REF_LINK_RE, LINK_DEF_RE, HTML_ANCHOR_RE, HTML_TAG_RE):
        for m in regex.finditer(text):
            cover(m.start(), m.end())
    for m in LINK_RE.finditer(text):
        cover(m.start(), m.end())
    for m in WIKILINK_RE.finditer(text):
        cover(m.start(), m.end())
    labels = {m.group(1).strip().lower() for m in LINK_DEF_LABEL_RE.finditer(text)}
    for m in SHORTCUT_RE.finditer(text):
        if m.group(1).strip().lower() in labels:
            cover(m.start(), m.end())
    for start, end in unexempt_spans(text, path):
        for i in range(max(0, start), min(len(text), end)):
            mask[i] = False
    return mask

def find_refs(text: str, path: Path=ANY_MD) -> list[Ref]:
    mask = masked(text, path)
    line_of = _line_index(text)
    claimed = [False] * len(text)
    refs: list[Ref] = []

    def take(kind: str, num: int, start: int, end: int, prefix: str='') -> bool:
        if any((mask[i] or claimed[i] for i in range(start, end))):
            return False
        for i in range(start, end):
            claimed[i] = True
        refs.append(Ref(kind, num, start, end, text[start:end], line_of(start), prefix=prefix))
        return True
    for rref in remotes.references(text):
        span = range(rref.start, rref.end)
        if any((mask[i] or claimed[i] for i in span)):
            continue
        for i in span:
            claimed[i] = True
        tail_num = rref.tail.rsplit('-', 1)[-1]
        refs.append(Ref('remote', int(tail_num) if tail_num.isdigit() else 0, rref.start, rref.end, rref.text, line_of(rref.start), remote=rref.prefix, code=rref.tail))
    schemes = current().schemes
    dp_prefix = next((s.prefix for s in schemes.values() if s.render == 'document'), '')
    patterns: list[tuple[str, str, re.Pattern]] = [('scheme', dp_prefix, DP_RE)] if dp_prefix else []
    patterns += [('scheme', s.prefix, s.pattern) for s in schemes.values()]
    patterns += [('scheme', s.prefix, s.temp_pattern) for s in schemes.values()]
    patterns += [('issue', '', ISSUE_RE)]
    for kind, prefix, regex in patterns:
        for m in regex.finditer(text):
            start, end = (m.start(), m.end())
            if any((mask[i] or claimed[i] for i in range(start, end))):
                continue
            for i in range(start, end):
                claimed[i] = True
            tail = m.groupdict().get('tail') or ''
            refs.append(Ref(kind, 0 if tail else int(m.group('num')), start, end, text[start:end], line_of(start), prefix=prefix, code=tail))
            if regex is not DP_RE:
                continue
            cursor = m.end()
            while (chain := DP_CHAIN_RE.match(text, cursor)) and take('scheme', int(chain.group('num')), chain.start('ref'), chain.end('ref'), prefix):
                cursor = chain.end()
    refs.sort(key=lambda r: r.start)
    return refs

def _line_index(text: str):
    starts = [0]
    for i, ch in enumerate(text):
        if ch == '\n':
            starts.append(i + 1)

    def line_of(pos: int) -> int:
        lo, hi = (0, len(starts) - 1)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if starts[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1
    return line_of
WIKILINK_RE = re.compile('\\[\\[([^\\][|]+?)(?:\\|([^\\][]+))?\\]\\]')

@dataclass(frozen=True)
class Wikilink:
    inner: str
    label: str
    start: int
    end: int
    line: int
    target: str | None

def wikilink_target(inner: str, source: Path) -> str | None:
    cfg = current()
    base = cfg.link_base(source)
    parsed = remotes.parse_code(inner)
    if parsed is not None:
        return remotes.link(*parsed) or None
    for scheme in cfg.schemes.values():
        t = re.fullmatch(f'{scheme.prefix}-({scheme.TEMP_TAIL})', inner)
        if t:
            return _temp_target(scheme, t.group(1), source, base)
        m = re.fullmatch(f'{scheme.prefix}[- ]0*(\\d+)', inner, re.IGNORECASE)
        if not m:
            continue
        n = int(m.group(1))
        if scheme.render == 'document' and scheme.output:
            anchor = f'{scheme.prefix.lower()}-{n}'
            if scheme.output == cfg.design_principles:
                anchor = dp_anchors().get(n) or anchor
            if source == scheme.output:
                return f'#{anchor}'
            return f'{_relative(scheme.output, base)}#{anchor}'
        target = scheme.documents().get(n)
        if target is None or target == source:
            return None
        return _relative(target, base)
    if (m := re.fullmatch('#(\\d+)', inner)):
        return cfg.issue_url.format(n=int(m.group(1))) if cfg.issue_url else None
    return None

def wikilinks(text: str, source: Path=ANY_MD) -> list[Wikilink]:
    if unlinted(source, text):
        return []
    skip = code_spans(text)
    skip += [m.span() for m in COMMENT_RE.finditer(text)]
    if (fm := _frontmatter_span(text)):
        cursor = fm[0]
        for a, b in prose_spans(text):
            skip.append((cursor, a))
            cursor = b
        skip.append((cursor, fm[1]))
    out = []
    for m in WIKILINK_RE.finditer(text):
        if any((a <= m.start() < b for a, b in skip)):
            continue
        inner = m.group(1).strip()
        label = (m.group(2) or inner).strip()
        out.append(Wikilink(inner, label, m.start(), m.end(), text.count('\n', 0, m.start()) + 1, wikilink_target(inner, source)))
    return out

def expand_wikilinks(text: str, source: Path) -> tuple[str, int]:
    html = html_block_spans(text)
    out, cursor, n = ([], 0, 0)
    for w in wikilinks(text, source):
        if w.target is None:
            continue
        out.append(text[cursor:w.start])
        if in_html_block(w.start, html):
            out.append(f'<a href="{w.target}">{w.label}</a>')
        else:
            out.append(f'[{w.label}]({w.target})')
        cursor = w.end
        n += 1
    out.append(text[cursor:])
    return (''.join(out), n)

def adr_paths() -> dict[int, Path]:
    scheme = current().schemes.get('ADR')
    return scheme.documents() if scheme else {}
EXPLICIT_ANCHOR_RE = re.compile('^<a name="[a-z]+-(\\d+)"></a>\\s*$')
HEADING_ANCHOR_RE = re.compile('^##\\s+(\\d+)\\.\\s+(.+?)\\s*$')

def dp_anchors() -> dict[int, str]:
    anchors: dict[int, str] = {}
    principles = current().design_principles
    if not principles.exists():
        return {}
    for line in principles.read_text().splitlines():
        if (m := EXPLICIT_ANCHOR_RE.match(line)):
            anchors[int(m.group(1))] = line.split('"')[1]
        elif (m := HEADING_ANCHOR_RE.match(line)):
            num = int(m.group(1))
            if num in anchors:
                continue
            slug = re.sub('[^a-z0-9 -]', '', f'{num}. {m.group(2)}'.lower())
            anchors[num] = slug.replace(' ', '-')
    return anchors

def _relative(target: Path, base: Path) -> str:
    import os
    return os.path.relpath(target, base).replace(os.sep, '/')

def is_ambiguous_issue(ref: Ref, text: str, anchors: dict[int, str]) -> bool:
    if ref.kind != 'issue' or ref.num > max(anchors, default=0):
        return False
    return not ISSUE_CUE_RE.search(text[max(0, ref.start - 120):ref.start])

def legacy_spellings() -> list[str]:
    cfg = current()
    files = list(doc_files())
    for pattern in cfg.code_globs:
        files += [p for p in cfg.root.glob(pattern) if p.is_file()]
    known: dict[tuple[str, str], int | None] = {}
    rows: list[str] = []
    seen: set[Path] = set()
    for path in files:
        if path in seen:
            continue
        seen.add(path)
        text = path.read_text()
        formerly = [m.span() for m in re.finditer('^formerly:(?:\\n- .*)*', text, re.MULTILINE)]
        for scheme in cfg.schemes.values():
            live = None
            for m in scheme.temp_pattern.finditer(text):
                if any((a <= m.start() < b for a, b in formerly)):
                    continue
                tail = m.group('tail')
                key = (scheme.prefix, tail)
                if key not in known:
                    if live is None:
                        live = scheme.temp_documents()
                    known[key] = None if tail in live else alias_number(scheme, tail)
                number = known[key]
                if number is None:
                    continue
                line = text.count('\n', 0, m.start()) + 1
                rows.append(f'{cfg.rel(path)}:{line} {m.group(0)} → {scheme.code(number)}')
    return sorted(rows)

def alias_number(scheme, tail: str) -> int | None:
    code = f'{scheme.prefix}-{tail}'
    for number, path in scheme.documents().items():
        meta, _ = parse_frontmatter(path.read_text())
        if any((str(a).strip() == code for a in meta.get('formerly') or [])):
            return number
    return None

def _temp_target(scheme, tail: str, source: Path, base: Path) -> str | None:
    cfg = current()
    live = scheme.temp_documents()
    documents = scheme.documents()
    page = scheme.output or cfg.design_principles
    target = live.get(tail)
    number = None
    if target is None:
        number = alias_number(scheme, tail)
        if number is None:
            return None
        target = documents.get(number)
    if target == source:
        return None
    if scheme.render != 'document':
        return _relative(target, base)
    if number is not None:
        anchor = f'{scheme.prefix.lower()}-{number}'
        if page == cfg.design_principles:
            anchor = dp_anchors().get(number) or anchor
    else:
        anchor = f'{scheme.prefix.lower()}-{tail}'
    if source == page:
        return f'#{anchor}'
    return f'{_relative(page, base)}#{anchor}'

def resolve(ref: Ref, source: Path, adrs: dict[int, Path], anchors: dict[int, str], text: str | None=None) -> str | None:
    cfg = current()
    base = cfg.link_base(source)
    if ref.kind == 'remote':
        return remotes.resolve(ref.remote, ref.code) or None
    if ref.kind == 'issue':
        if text is not None and is_ambiguous_issue(ref, text, anchors):
            return None
        return cfg.issue_url.format(n=ref.num) if cfg.issue_url else None
    scheme = cfg.schemes.get(ref.prefix)
    if scheme is None:
        return None
    if ref.code:
        return _temp_target(scheme, ref.code, source, base)
    if scheme.render != 'document':
        target = (adrs if ref.prefix == 'ADR' else scheme.documents()).get(ref.num)
        if target is None or target == source:
            return None
        return _relative(target, base)
    page = scheme.output or cfg.design_principles
    documents = scheme.documents()
    if documents.get(ref.num) == source:
        return None
    anchor = anchors.get(ref.num) if page == cfg.design_principles else None
    if anchor is None:
        if ref.num not in documents:
            return None
        anchor = f'{scheme.prefix.lower()}-{ref.num}'
    if source == page:
        return f'#{anchor}'
    return f'{_relative(page, base)}#{anchor}'

def _absorb_brackets(text: str, ref: Ref) -> tuple[int, int]:
    if ref.start > 0 and text[ref.start - 1] == '[' and (ref.end < len(text)) and (text[ref.end] == ']'):
        return (ref.start - 1, ref.end + 1)
    return (ref.start, ref.end)
UNLINK_RE = re.compile('\\[([^\\]]+)\\]\\([^)\\s]*\\)')

def _frontmatter_survives(old: str, new: str) -> bool:
    try:
        before, _ = parse_frontmatter(old)
        after, _ = parse_frontmatter(new)
    except yaml.YAMLError:
        return False
    if not before or not after:
        return False
    if {k: v for k, v in before.items() if k not in PROSE_KEYS} != {k: v for k, v in after.items() if k not in PROSE_KEYS}:
        return False
    return all((UNLINK_RE.sub('\\1', str(after.get(k, ''))) == str(before.get(k, '')) for k in PROSE_KEYS))

def rewritable_refs(text: str, source: Path, adrs: dict[int, Path], anchors: dict[int, str]) -> list[Ref]:
    if unlinted(source, text):
        return []
    refs = [r for r in find_refs(text, source) if resolve(r, source, adrs, anchors, text) is not None]
    spans = prose_spans(text)
    if not spans or not any((in_prose(spans, r.start) for r in refs)):
        return refs
    if _frontmatter_survives(text, _apply(text, refs, source, adrs, anchors)):
        return refs
    return [r for r in refs if not in_prose(spans, r.start)]

def linkify(text: str, source: Path, adrs: dict[int, Path] | None=None, anchors: dict[int, str] | None=None) -> tuple[str, int]:
    adrs = adr_paths() if adrs is None else adrs
    anchors = dp_anchors() if anchors is None else anchors
    text, expanded = expand_wikilinks(text, source)
    refs = rewritable_refs(text, source, adrs, anchors)
    return (_apply(text, refs, source, adrs, anchors), len(refs) + expanded)

def _label(ref: Ref) -> str:
    if ref.kind == 'scheme' and ref.code:
        scheme = current().schemes.get(ref.prefix)
        if scheme is not None and ref.code not in scheme.temp_documents():
            number = alias_number(scheme, ref.code)
            if number is not None:
                return scheme.code(number)
    return ref.text

def _apply(text: str, refs: list[Ref], source: Path, adrs: dict[int, Path], anchors: dict[int, str]) -> str:
    html = html_block_spans(text)
    out, cursor = ([], 0)
    for ref in refs:
        target = resolve(ref, source, adrs, anchors, text)
        if target is None:
            continue
        start, end = _absorb_brackets(text, ref)
        out.append(text[cursor:start])
        label = _label(ref)
        if in_html_block(start, html):
            out.append(f'<a href="{target}">{label}</a>')
        else:
            out.append(f'[{label}]({target})')
        cursor = end
    out.append(text[cursor:])
    return ''.join(out)

def doc_files() -> list[Path]:
    cfg = current()
    paths = [cfg.root / name for name in ('README.md', 'CLAUDE.md', 'AGENTS.md')]
    paths += [cfg.root / f.target for f in cfg.fragments.values()]
    paths += sorted(cfg.docs.rglob('*.md')) + sorted(cfg.docs.rglob('*.stub'))
    for scheme in cfg.schemes.values():
        paths += sorted(scheme.dir.glob('*.md')) + sorted(scheme.dir.glob('*.stub'))
    for fragment_dir in cfg.fragments:
        paths += sorted((cfg.root / fragment_dir).glob('*.md'))
    for journal in cfg.journals.values():
        paths += sorted(journal.dir.rglob('*.md'))
    seen, out = (set(), [])
    for path in paths:
        if path.exists() and path not in seen and (not cfg.is_generated(path)):
            seen.add(path)
            out.append(path)
    return out
