from __future__ import annotations
import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path
LINE, BLOCK, FILE = ('line', 'block', 'file')
DIRECTIVE_RE = re.compile('^(?P<name>[a-z][a-z-]*?)(?P<scope>-block|-file)?:(?P<args>[^\\n]*?)(?:—|-->|\\*/|$)', re.IGNORECASE)
HTML_COMMENT_RE = re.compile('<!--(?:.|\\n)*?-->')
COMMENT_MARKER_RE = re.compile('//|/\\*|^\\s*\\*|#|--')
SHAPED_RE = re.compile('\\b[a-z][a-z-]*?(?:-block|-file)?:[^\\n]*?(?=—|-->|\\*/|$)', re.IGNORECASE | re.MULTILINE)

@dataclass(frozen=True)
class Directive:
    name: str
    scope: str
    args: tuple[str, ...]
    reason: str
    path: Path
    line: int
    span: tuple[int, int]
    lines: frozenset[int]

    def covers(self, line: int) -> bool:
        return self.scope == FILE or line in self.lines

def _fence_line_spans(text: str) -> list[tuple[int, int]]:
    from . import doc_refs
    spans = []
    for start, end in doc_refs._fence_spans(text):
        spans.append((text.count('\n', 0, start) + 1, text.count('\n', 0, max(start, end - 1)) + 1))
    return spans

def blocks(text: str) -> list[tuple[int, int]]:
    fenced = _fence_line_spans(text)

    def in_fence(line: int) -> bool:
        return any((a <= line <= b for a, b in fenced))
    out: list[tuple[int, int]] = []
    start = None
    for n, line in enumerate(text.splitlines(), 1):
        blank = not line.strip() and (not in_fence(n))
        if blank:
            if start is not None:
                out.append((start, n - 1))
                start = None
        elif start is None:
            start = n
    if start is not None:
        out.append((start, len(text.splitlines())))
    return out

def comment_fragments(path: Path, text: str) -> list[tuple[int, int, str]]:
    suffix = path.suffix.lower()
    if suffix in {'.md', '.markdown'}:
        from . import doc_refs
        code = doc_refs.code_spans(text)
        out = []
        for m in HTML_COMMENT_RE.finditer(text):
            if any((a <= m.start() < b for a, b in code)):
                continue
            out.append((text.count('\n', 0, m.start()) + 1, m.start(), m.group(0)[4:-3]))
        return out
    if suffix == '.py':
        try:
            offsets = _line_offsets(text)
            return [(tok.start[0], offsets[tok.start[0] - 1] + tok.start[1], tok.string.lstrip('#')) for tok in tokenize.generate_tokens(io.StringIO(text).readline) if tok.type == tokenize.COMMENT]
        except (tokenize.TokenError, IndentationError, SyntaxError):
            pass
    out = []
    offsets = _line_offsets(text)
    for n, line in enumerate(text.splitlines(), 1):
        for m in COMMENT_MARKER_RE.finditer(line):
            out.append((n, offsets[n - 1] + m.end(), line[m.end():]))
    return out

def _line_offsets(text: str) -> list[int]:
    out, pos = ([], 0)
    for line in text.splitlines(keepends=True):
        out.append(pos)
        pos += len(line)
    return out or [0]

def find(path: Path, text: str, names: set[str] | None=None) -> list[Directive]:
    spans = blocks(text)
    found: list[Directive] = []
    for line_no, offset, body in comment_fragments(path, text):
        m = DIRECTIVE_RE.match(body.strip())
        if not m:
            continue
        name = m.group('name').lower()
        if names is not None and name not in names:
            continue
        suffix = (m.group('scope') or '').lower()
        scope = FILE if suffix == '-file' else BLOCK if suffix == '-block' else LINE
        args = tuple((t for t in re.split('[,\\s]+', m.group('args').strip()) if t))
        reason = body.split('—', 1)[1].strip().rstrip('->').strip() if '—' in body else ''
        found.append(Directive(name, scope, args, reason, path, line_no, (offset, offset + len(body)), _governed(scope, line_no, spans, path, text)))
    return found

def _governed(scope: str, line: int, spans: list[tuple[int, int]], path: Path, text: str) -> frozenset[int]:
    if scope == FILE:
        return frozenset(range(1, len(text.splitlines()) + 1))
    if scope == LINE:
        return frozenset({line, line + 1})
    own = next((s for s in spans if s[0] <= line <= s[1]), (line, line))
    if _directive_only(text, own, path):
        nxt = next((s for s in spans if s[0] > own[1]), None)
        own = nxt if nxt else own
    return frozenset(range(own[0], own[1] + 1))

def _directive_only(text: str, span: tuple[int, int], path: Path) -> bool:
    lines = text.splitlines()[span[0] - 1:span[1]]
    body = '\n'.join(lines)
    for m in HTML_COMMENT_RE.finditer(body):
        body = body.replace(m.group(0), '')
    stripped = []
    for line in body.splitlines():
        marker = COMMENT_MARKER_RE.search(line)
        candidate = line[marker.end():] if marker else line
        if marker and DIRECTIVE_RE.match(candidate.strip()):
            continue
        stripped.append(line if marker is None else line[:marker.start()])
    return not ''.join(stripped).strip()

def shaped_spans(text: str, names: set[str]) -> list[tuple[int, int]]:
    out = []
    for m in SHAPED_RE.finditer(text):
        head = m.group(0).split(':', 1)[0].lower()
        if head.removesuffix('-block').removesuffix('-file') in names:
            out.append((m.start(), m.end()))
    return out

def problems(directive: Directive, valid_args: set[str] | None=None) -> str | None:
    if not directive.args:
        return f'`{directive.name}` names no argument'
    if valid_args is not None:
        unknown = sorted((a for a in directive.args if a.lower() not in valid_args))
        if unknown:
            return f"`{directive.name}` names unknown {('argument' if len(unknown) == 1 else 'arguments')}: {', '.join(unknown)}"
    return None
