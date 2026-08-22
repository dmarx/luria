from __future__ import annotations
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from . import adr_index as builder
from . import directives, doc_refs, remotes
from .config import current
DEFAULT_SITES = 5

def _blank(text: str, spans: list[tuple[int, int]]) -> str:
    chars = list(text)
    for start, end in spans:
        for i in range(max(0, start), min(len(chars), end)):
            if chars[i] != '\n':
                chars[i] = ' '
    return ''.join(chars)

def _rel(path: Path) -> str:
    return current().rel(path)

@dataclass(frozen=True)
class Doc:
    code: str
    status: str
    title: str
    path: Path
    active: bool

def _load_scheme(scheme) -> dict[str, Doc]:
    docs: dict[str, Doc] = {}
    for number, path in scheme.documents().items():
        doc = builder.Adr(path, scheme)
        status = re.split('\\s+—\\s+', doc.status, maxsplit=1)[0]
        code = scheme.code(number)
        docs[code] = Doc(code, status, doc.title, path, status == scheme.active)
    return docs

def schemes() -> dict:
    return current().schemes

def load_docs() -> dict[str, Doc]:
    out: dict[str, Doc] = {}
    for scheme in schemes().values():
        out.update(_load_scheme(scheme))
    return out
CODE_RE = re.compile('\\b([A-Za-z]{2,10})-(\\d{1,4})\\b')
BARE_NUMBER_RE = re.compile('(?<![\\w-])\\d{1,4}(?![\\w-])')
URL_RE = re.compile('\\b[a-z][a-z0-9+.-]*://[^\\s<>)\\]\\"\']+', re.IGNORECASE)
DIRECTIVE = 'inactive-ok'
DANGLING_DIRECTIVE = 'unresolved-ok'

def _codes(spec: str) -> tuple[set[str], str]:
    codes: set[str] = set()
    refs = remotes.references(spec)
    for ref in refs:
        codes.add(ref.composed)
    for ref in sorted(refs, key=lambda r: r.start, reverse=True):
        spec = spec[:ref.start] + ' ' * (ref.end - ref.start) + spec[ref.end:]
    codes |= {f'{p.upper()}-{int(n):03d}' for p, n in CODE_RE.findall(spec)}
    return (codes, spec)

def _exists(code: str, known: set[str]) -> bool:
    parsed = remotes.parse_code(code)
    if parsed is not None:
        remote, tail = parsed
        return bool(remotes.link(remote, tail))
    return code in known

@dataclass(frozen=True)
class Annotation:
    directive: directives.Directive
    codes: frozenset[str]
    problem: str | None = None
    kind: str = DIRECTIVE

    def __str__(self) -> str:
        return f'{_rel(self.directive.path)}:{self.directive.line}'

    @property
    def scope(self) -> str:
        return self.directive.scope

    def covers(self, line: int) -> bool:
        return self.directive.covers(line)

def annotations(path: Path, text: str, known: set[str], directive: str=DIRECTIVE) -> list[Annotation]:
    resolvable = directive != DANGLING_DIRECTIVE
    found = []
    for d in directives.find(path, text, {directive}):
        spec = ' '.join(d.args)
        codes, spec = _codes(spec)
        problem = None
        if not codes:
            problem = 'names no document code'
        elif BARE_NUMBER_RE.search(CODE_RE.sub('', spec)):
            example = f"{next(iter(schemes()), 'ADR')}-012"
            problem = f'has a bare number — write the full code (e.g. {example})'
        elif resolvable and (unknown := sorted((c for c in codes if not _exists(c, known)))):
            problem = f"names unknown document(s): {', '.join(unknown)}"
        elif not resolvable and (real := sorted((c for c in codes if _exists(c, known)))):
            problem = f"names {', '.join(real)}, which does resolve here"
        found.append(Annotation(d, frozenset(codes), problem, directive))
    return found

@dataclass(frozen=True)
class Citation:
    path: Path
    line: int
    code: str
    excused_by: Annotation | None = field(default=None, compare=False)

    def __str__(self) -> str:
        return f'{_rel(self.path)}:{self.line}'

@dataclass
class Scan:
    cited: dict[str, list[Citation]] = field(default_factory=dict)
    dangling: dict[str, list[Citation]] = field(default_factory=dict)
    annotations: list[Annotation] = field(default_factory=list)
    unlinted: list[Path] = field(default_factory=list)

    def used(self, ann: Annotation) -> bool:
        pool = self.dangling if ann.kind == DANGLING_DIRECTIVE else self.cited
        return any((c.excused_by is ann for sites in pool.values() for c in sites))

def scanned_files() -> list[Path]:
    cfg = current()
    docs = [p for p in doc_refs.doc_files() if not cfg.is_historical(p)]
    code: list[Path] = []
    for pattern in cfg.code_globs:
        code += [p for p in cfg.root.glob(pattern) if p.is_file()]
    return docs + sorted(set(code))

def scan(files: list[Path] | None=None, docs: dict[str, Doc] | None=None) -> Scan:
    docs = load_docs() if docs is None else docs
    known = set(docs)
    own = {doc.path: doc.code for doc in docs.values()}
    result = Scan()
    for path in files if files is not None else scanned_files():
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        if doc_refs.unlinted(path, text):
            result.unlinted.append(path)
            continue
        anns = annotations(path, text, known)
        dangling_anns = annotations(path, text, known, DANGLING_DIRECTIVE)
        result.annotations += anns + dangling_anns
        usable = [a for a in anns if not a.problem]
        usable_dangling = [a for a in dangling_anns if not a.problem]
        from . import remotes as _remotes
        text = _blank(text, directives.shaped_spans(text, {DIRECTIVE, DANGLING_DIRECTIVE, _remotes.URL_OK}))
        text = _blank(text, [m.span() for m in URL_RE.finditer(text)])
        text = _blank(text, [m.span() for m in doc_refs.FORMERLY_RE.finditer(text)])
        if current().remotes:
            spans = []
            for ref in remotes.references(text):
                spans.append((ref.start, ref.end))
                if not remotes.link(ref.remote, ref.tail):
                    code = ref.composed
                    where = text.count('\n', 0, ref.start) + 1
                    excuse = next((a for a in usable_dangling if code in a.codes and a.covers(where)), None)
                    result.dangling.setdefault(code, []).append(Citation(path, where, code, excuse))
            text = _blank(text, spans)
        for line_no, line in enumerate(text.splitlines(), 1):
            bare = line
            codes = set()
            for scheme in schemes().values():
                codes |= {scheme.code(m.group('num')) for m in scheme.pattern.finditer(bare)}
            for code in codes:
                if own.get(path) == code:
                    continue
                if code not in docs:
                    excuse = next((a for a in usable_dangling if code in a.codes and a.covers(line_no)), None)
                    result.dangling.setdefault(code, []).append(Citation(path, line_no, code, excuse))
                    continue
                excuse = None if docs[code].active else next((a for a in usable if code in a.codes and a.covers(line_no)), None)
                result.cited.setdefault(code, []).append(Citation(path, line_no, code, excuse))
    for pool in (result.cited, result.dangling):
        for sites in pool.values():
            sites.sort(key=lambda c: (str(c.path), c.line))
    return result

def _spread(sites: list[Citation], limit: int) -> list[Citation]:
    if limit <= 0:
        return sites
    by_file: dict[Path, list[Citation]] = {}
    for c in sites:
        by_file.setdefault(c.path, []).append(c)
    picked: list[Citation] = []
    while len(picked) < limit and any(by_file.values()):
        for group in by_file.values():
            if group and len(picked) < limit:
                picked.append(group.pop(0))
    return picked

def flagged(result: Scan | None=None, docs: dict[str, Doc] | None=None):
    docs = load_docs() if docs is None else docs
    result = scan(docs=docs) if result is None else result
    rows = []
    for code, sites in result.cited.items():
        doc = docs[code]
        if doc.active:
            continue
        loud = [c for c in sites if c.excused_by is None]
        if loud:
            rows.append((doc, loud, len(sites) - len(loud)))
    return sorted(rows, key=lambda r: (-len(r[1]), r[0].code))

def dangling(result: Scan | None=None, docs: dict[str, Doc] | None=None) -> list[tuple[str, list[Citation], int]]:
    result = scan(docs=docs) if result is None else result
    rows = []
    for code, sites in result.dangling.items():
        loud = [c for c in sites if c.excused_by is None]
        if loud:
            rows.append((code, loud, len(sites) - len(loud)))
    return sorted(rows, key=lambda r: (-len(r[1]), r[0]))

def dangling_lines(result: Scan | None=None, docs: dict[str, Doc] | None=None) -> list[str]:
    out = []
    for code, loud, excused in dangling(result, docs):
        files = len({c.path for c in loud})
        tail = f', {excused} acknowledged' if excused else ''
        out.append(f'{code} resolves to no document, cited {len(loud)}× in {files} file(s){tail}')
    return out

def acknowledged_count(result: Scan | None=None, docs: dict[str, Doc] | None=None) -> int:
    docs = load_docs() if docs is None else docs
    result = scan(docs=docs) if result is None else result
    return sum((1 for code, sites in result.cited.items() if not docs[code].active for c in sites if c.excused_by is not None))

def dangling_acknowledged_count(result: Scan | None=None, docs: dict[str, Doc] | None=None) -> int:
    result = scan(docs=docs) if result is None else result
    return sum((1 for sites in result.dangling.values() for c in sites if c.excused_by is not None))

def stale_annotations(result: Scan | None=None, docs: dict[str, Doc] | None=None) -> list[str]:
    docs = load_docs() if docs is None else docs
    result = scan(docs=docs) if result is None else result
    out = []
    for ann in result.annotations:
        if ann.problem:
            out.append(f'{ann}: annotation {ann.problem}')
        elif not result.used(ann):
            named = ', '.join(sorted(ann.codes))
            if ann.kind == DANGLING_DIRECTIVE:
                why = f'nothing in scope cites {named}'
            else:
                active = sorted((c for c in ann.codes if c in docs and docs[c].active))
                why = f"{', '.join(active)} is Active now" if active else f'nothing in scope cites {named}'
            out.append(f'{ann}: annotation no longer applies — {why}')
    return sorted(out)

def summary_lines(result: Scan | None=None, docs: dict[str, Doc] | None=None) -> list[str]:
    out = []
    for doc, loud, excused in flagged(result, docs):
        files = len({c.path for c in loud})
        tail = f', {excused} acknowledged' if excused else ''
        out.append(f'{doc.code} is {doc.status}, cited {len(loud)}× in {files} file(s){tail} — {doc.title}')
    return out

def warnings(sites: int=DEFAULT_SITES, result: Scan | None=None, docs: dict[str, Doc] | None=None) -> list[str]:
    docs = load_docs() if docs is None else docs
    result = scan(docs=docs) if result is None else result
    lines: list[str] = []
    for line, (_, loud, _) in zip(summary_lines(result, docs), flagged(result, docs)):
        lines.append(line)
        shown = _spread(loud, sites)
        lines += [f'    {c}' for c in sorted(shown, key=lambda c: (str(c.path), c.line))]
        if len(loud) > len(shown):
            lines.append(f'    … and {len(loud) - len(shown)} more (`luria reports` lists them)')
    return lines

def run(all: bool=False) -> None:
    docs = load_docs()
    result = scan(docs=docs)
    rows = flagged(result, docs)
    excused = acknowledged_count(result, docs)
    if rows:
        note = f', {excused} acknowledged reference(s)' if excused else ''
        print(f'reference status: {len(rows)} retired document(s) cited unacknowledged from current docs/code{note}', file=sys.stderr)
        for line in warnings(0 if all else DEFAULT_SITES, result, docs):
            print(f'  {line}', file=sys.stderr)
    else:
        print(f'reference status: no unacknowledged references to retired documents ({excused} acknowledged)')
    loose_excused = dangling_acknowledged_count(result, docs)
    loose = dangling(result, docs)
    if not loose:
        print(f'reference status: every code resolves ({loose_excused} acknowledged)')
    if loose:
        print(f'reference status: {len(loose)} code(s) resolve to no document', file=sys.stderr)
        for code, sites, excused in loose:
            tail = f', {excused} acknowledged' if excused else ''
            print(f'  {code} — cited {len(sites)}×{tail}', file=sys.stderr)
            shown = _spread(sites, 0 if all else DEFAULT_SITES)
            for c in sorted(shown, key=lambda c: (str(c.path), c.line)):
                print(f'      {c}', file=sys.stderr)
            if len(sites) > len(shown):
                print(f'      … and {len(sites) - len(shown)} more', file=sys.stderr)
    stale = stale_annotations(result, docs)
    if stale:
        print(f'reference status: {len(stale)} annotation(s) no longer apply', file=sys.stderr)
        for line in stale:
            print(f'  {line}', file=sys.stderr)
if __name__ == '__main__':
    import fire
    fire.Fire(run)
