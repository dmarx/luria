#!/usr/bin/env python3
"""Comment directives — the shared vocabulary the docs tooling reads (ADR-006, ADR-007).

Two checks take instructions from the prose they check:
`luria.ref_status` (acknowledge a deliberate reference to a retired
document) and `luria.doc_refs` (lint a region that is exempt by
default). They use one syntax, parsed here, so a contributor learns the shape
once:

    <!-- inactive-ok: ADR-012 — the decision this ADR replaced -->
    <!-- inactive-ok-block: ADR-012 — every mention in this paragraph -->
    <!-- inactive-ok-file: ADR-012 — this page is that history -->
    <!-- unexempt-block: codeblock — the snippet below cites real decisions -->
    // inactive-ok: ADR-028 — proposed, but this is what shipped

Shape
-----
`<name>[-block|-file]: <args> [— <reason>]`, and **the directive must open its
comment**, `# noqa`-style. Matching it anywhere in a comment means prose *about*
the syntax invokes it — which is not hypothetical: comments in the scanner
explaining these rules registered as directives, and a docstring example
silently annotated its own module.

Scope
-----
The suffix decides, uniformly, for every directive — there are no per-directive
defaults to remember:

- **line** (no suffix) — its own line and the line below, so it can be written
  directly above the line it governs.
- **block** (`-block`) — the run of non-blank lines it sits in. A directive
  standing alone between blank lines has no content block of its own, so the
  block it means is the one it introduces: the next one. Fenced code counts as
  one block even when it contains blank lines.
- **file** (`-file`) — the whole document.

A blank line between a directive and what it governs therefore needs `-block`:

    <!-- inactive-ok-block: ADR-061 --><!-- unexempt-block: codeblock -->

    ```python
    # implements ADR-157, fixes the problem ADR-061 caused
    ```

Written flush against the fence, with no blank line, the bare forms reach it —
line scope covers the line below, and unexempting any line of a fence unexempts
that fence.

Comments only
-------------
A directive is read from real comments: HTML comments in markdown (outside code
spans and fences), `COMMENT` tokens in Python, and text after a comment marker
elsewhere. An example inside a fence or a docstring is not a comment, and does
not fire.
"""

# unresolved-ok-file: ADR-157, ADR-061 — illustrative codes in the docstring above
from __future__ import annotations

import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path

LINE, BLOCK, FILE = "line", "block", "file"

DIRECTIVE_RE = re.compile(
    r"^(?P<name>[a-z][a-z-]*?)(?P<scope>-block|-file)?:"
    r"(?P<args>[^\n]*?)(?:—|-->|\*/|$)",
    re.IGNORECASE,
)
HTML_COMMENT_RE = re.compile(r"<!--(?:.|\n)*?-->")
# Every comment marker on the line, not just the first: `// note  // dir: x`
# has to see the second comment's body to find the directive that opens it.
# Crude on purpose — a directive inside a string literal that also contains a
# comment marker is not a case worth a parser.
COMMENT_MARKER_RE = re.compile(r"//|/\*|^\s*\*|#|--")

# Directive-shaped text ANYWHERE, live or illustrative. Used to tell a scanner
# "this is syntax, not content": a code the directive names is being *governed*,
# not cited, and an example of a directive in a fenced block or a docstring is
# no more a citation than the real one is.
SHAPED_RE = re.compile(
    r"\b[a-z][a-z-]*?(?:-block|-file)?:[^\n]*?(?=—|-->|\*/|$)",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True)
class Directive:
    name: str                 # "inactive-ok", "unexempt"
    scope: str                # LINE | BLOCK | FILE
    args: tuple[str, ...]     # whitespace/comma-separated tokens before the —
    reason: str
    path: Path
    line: int                 # 1-based, where the comment starts
    span: tuple[int, int]     # char offsets of the whole comment in the text
    lines: frozenset[int]     # every line this directive governs

    def covers(self, line: int) -> bool:
        return self.scope == FILE or line in self.lines


def _fence_line_spans(text: str) -> list[tuple[int, int]]:
    """1-based (first, last) line numbers of each fenced code block."""
    from . import doc_refs                            # local: avoids a cycle
    spans = []
    for start, end in doc_refs._fence_spans(text):
        spans.append((text.count("\n", 0, start) + 1,
                      text.count("\n", 0, max(start, end - 1)) + 1))
    return spans


def blocks(text: str) -> list[tuple[int, int]]:
    """Blank-line-delimited runs of lines, 1-based inclusive. A fenced block is
    atomic — a blank line inside a code sample doesn't end the paragraph."""
    fenced = _fence_line_spans(text)

    def in_fence(line: int) -> bool:
        return any(a <= line <= b for a, b in fenced)

    out: list[tuple[int, int]] = []
    start = None
    for n, line in enumerate(text.splitlines(), 1):
        blank = not line.strip() and not in_fence(n)
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
    """(line, char offset, comment body) for every real comment in `path`."""
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        from . import doc_refs
        code = doc_refs.code_spans(text)
        out = []
        for m in HTML_COMMENT_RE.finditer(text):
            if any(a <= m.start() < b for a, b in code):
                continue
            out.append((text.count("\n", 0, m.start()) + 1, m.start(),
                        m.group(0)[4:-3]))
        return out
    if suffix == ".py":
        try:
            offsets = _line_offsets(text)
            return [(tok.start[0], offsets[tok.start[0] - 1] + tok.start[1],
                     tok.string.lstrip("#"))
                    for tok in tokenize.generate_tokens(io.StringIO(text).readline)
                    if tok.type == tokenize.COMMENT]
        except (tokenize.TokenError, IndentationError, SyntaxError):
            pass                                  # fall through to the crude scan
    out = []
    offsets = _line_offsets(text)
    for n, line in enumerate(text.splitlines(), 1):
        for m in COMMENT_MARKER_RE.finditer(line):
            out.append((n, offsets[n - 1] + m.end(), line[m.end():]))
    return out


def _line_offsets(text: str) -> list[int]:
    out, pos = [], 0
    for line in text.splitlines(keepends=True):
        out.append(pos)
        pos += len(line)
    return out or [0]


def find(path: Path, text: str, names: set[str] | None = None) -> list[Directive]:
    """Every directive in `path`, with the lines each one governs resolved."""
    spans = blocks(text)
    found: list[Directive] = []
    for line_no, offset, body in comment_fragments(path, text):
        m = DIRECTIVE_RE.match(body.strip())
        if not m:
            continue
        name = m.group("name").lower()
        if names is not None and name not in names:
            continue
        suffix = (m.group("scope") or "").lower()
        scope = FILE if suffix == "-file" else BLOCK if suffix == "-block" else LINE
        args = tuple(t for t in re.split(r"[,\s]+", m.group("args").strip()) if t)
        reason = body.split("—", 1)[1].strip().rstrip("->").strip() \
            if "—" in body else ""
        found.append(Directive(
            name, scope, args, reason, path, line_no,
            (offset, offset + len(body)),
            _governed(scope, line_no, spans, path, text)))
    return found


def _governed(scope: str, line: int, spans: list[tuple[int, int]],
              path: Path, text: str) -> frozenset[int]:
    if scope == FILE:
        return frozenset(range(1, len(text.splitlines()) + 1))
    if scope == LINE:
        return frozenset({line, line + 1})
    own = next((s for s in spans if s[0] <= line <= s[1]), (line, line))
    # A directive standing alone between blank lines has no content block of its
    # own, so the block it means is the one it introduces. This is the reading of
    # "block", not an exception to it — and it is the whole reason `-block`
    # exists as a separate scope from `-line`.
    if _directive_only(text, own, path):
        nxt = next((s for s in spans if s[0] > own[1]), None)
        own = nxt if nxt else own
    return frozenset(range(own[0], own[1] + 1))


def _directive_only(text: str, span: tuple[int, int], path: Path) -> bool:
    """True when a block is nothing but directives — which is what makes it an
    introduction to the block below rather than a block of its own."""
    lines = text.splitlines()[span[0] - 1:span[1]]
    body = "\n".join(lines)
    for m in HTML_COMMENT_RE.finditer(body):
        body = body.replace(m.group(0), "")
    stripped = []
    for line in body.splitlines():
        marker = COMMENT_MARKER_RE.search(line)
        candidate = line[marker.end():] if marker else line
        if marker and DIRECTIVE_RE.match(candidate.strip()):
            continue
        stripped.append(line if marker is None else line[:marker.start()])
    return not "".join(stripped).strip()


def shaped_spans(text: str, names: set[str]) -> list[tuple[int, int]]:
    """Char spans of every directive-shaped run naming one of `names`."""
    out = []
    for m in SHAPED_RE.finditer(text):
        head = m.group(0).split(":", 1)[0].lower()
        if head.removesuffix("-block").removesuffix("-file") in names:
            out.append((m.start(), m.end()))
    return out


def problems(directive: Directive, valid_args: set[str] | None = None) -> str | None:
    """A directive that can't do anything is worth saying so about."""
    if not directive.args:
        return f"`{directive.name}` names no argument"
    if valid_args is not None:
        unknown = sorted(a for a in directive.args if a.lower() not in valid_args)
        if unknown:
            return (f"`{directive.name}` names unknown "
                    f"{'argument' if len(unknown) == 1 else 'arguments'}: "
                    f"{', '.join(unknown)}")
    return None
