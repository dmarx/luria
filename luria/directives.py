#!/usr/bin/env python3
"""Comment directives — the shared vocabulary the docs tooling reads (ADR-006, ADR-035).

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
    # inactive-ok: ADR-012 — in a note's frontmatter, above the field it excuses

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
- **block** (`-block`) — the run of non-blank lines it sits in, extended to
  the syntactic unit the directive introduces. A directive standing alone
  between blank lines has no content block of its own, so the block it means
  is the one it introduces: the next one. Fenced code counts as one block even
  when it contains blank lines, and so does a Python docstring — one
  syntactic unit however many paragraphs it holds, counted from its `def` or
  `class` line, so this reaches a citation in a docstring:

      # inactive-ok-block: ADR-012 — the decision this function replaced
      def apply(...):
          '''First paragraph.

          A later paragraph citing ADR-012.'''

  Every language has a construct that holds a blank line, and a run of
  non-blank lines is wrong about all of them the same way. With the optional
  `luria[syntax]` extra installed, `luria.syntax` reads the real one from a
  grammar — the same rule in any language tree-sitter supports. It can only
  extend the run, never shorten it, so a directive that works without the
  extra works the same with it.

- **file** (`-file`) — the whole document.

Expiry
------
`until <YYYY-MM-DD>` anywhere in the arguments gives a directive a deadline
(#58). After it passes, `find` does not return the directive at all, so every
check behaves as if it were never written — uniform for the same reason the
scopes are, because this is the one place directives are read. The date is
inclusive: `until 2026-10-01` is the last day it holds.

    <!-- inactive-ok: ADR-028 until 2026-10-01 — revisit when the API settles -->

An expiry is a modifier, not one of the things the directive names, so it is
lifted out of `args`. `find_expired` returns what `find` dropped, because inert
is not the same as invisible — a check that starts failing again with the
acknowledgement still above it is a puzzle rather than a report. A date that
cannot be read leaves the directive live and is reported by `problems`: a typo
should not silently mean "forever", and it should not silently drop a
suppression either.

A blank line between a directive and what it governs therefore needs `-block`:

    <!-- inactive-ok-block: ADR-159 --><!-- unexempt-block: codeblock -->

    ```python
    # implements ADR-157, fixes the problem ADR-159 caused
    ```

Written flush against the fence, with no blank line, the bare forms reach it —
line scope covers the line below, and unexempting any line of a fence unexempts
that fence.

Comments only
-------------
A directive is read from real comments: HTML comments in markdown (outside code
spans and fences), `COMMENT` tokens in Python, comment nodes from a grammar
where one is installed, and text after a comment marker elsewhere. An example
inside a fence or a docstring is not a comment, and does not fire — and with a
grammar, neither is a `#` inside a shell string.
"""

# unresolved-ok-file: ADR-157, ADR-159 — illustrative codes in the docstring above
from __future__ import annotations

import datetime as dt
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


def _split_expiry(args: tuple[str, ...]) -> tuple[tuple[str, ...], "dt.date | None", str | None]:
    """Pull `until <YYYY-MM-DD>` out of a directive's arguments.

    An expiry is a modifier on the directive, not one of the things it names,
    so it leaves the argument list — otherwise every consumer that validates
    arguments would report `until` as an unknown one.

    An ISO date and nothing else. A duration ("two weeks") would need an anchor
    the file does not carry, and `2026-10-01` is the anchor written down."""
    lowered = [a.lower() for a in args]
    if "until" not in lowered:
        return args, None, None
    at = lowered.index("until")
    rest = args[at + 1:]
    kept = args[:at] + rest[1:]
    if not rest:
        return kept, None, "until"
    try:
        return kept, dt.date.fromisoformat(rest[0]), None
    except ValueError:
        return kept, None, rest[0]


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
    # `until <YYYY-MM-DD>` (#58), lifted out of `args` so the tokens that
    # remain are the ones the directive is ABOUT. None when no expiry was
    # written — and also None when one was written and could not be read,
    # which `problems` says out loud rather than letting a typo mean "forever".
    expires: dt.date | None = None
    bad_expiry: str | None = None

    def covers(self, line: int) -> bool:
        return self.scope == FILE or line in self.lines

    def expired(self, as_of: dt.date) -> bool:
        """`until 2026-10-01` is good ON the 1st — a date somebody wrote as the
        last day they meant it to hold, not the first day it stops."""
        return self.expires is not None and as_of > self.expires


def _fence_line_spans(text: str) -> list[tuple[int, int]]:
    """1-based (first, last) line numbers of each fenced code block."""
    from . import doc_refs                            # local: avoids a cycle
    spans = []
    for start, end in doc_refs._fence_spans(text):
        spans.append((text.count("\n", 0, start) + 1,
                      text.count("\n", 0, max(start, end - 1)) + 1))
    return spans


def _docstring_line_spans(text: str) -> list[tuple[int, int]]:
    """1-based (first, last) line numbers of each docstring in a Python source.

    Module, class and function docstrings only — a string used as a value is
    not one, and annotating it is not what anyone means. Unparseable source
    yields nothing rather than raising: a directive scope is not the place to
    discover a syntax error."""
    import ast
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return []
    spans = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if not body or not isinstance(body[0], ast.Expr):
            continue
        doc = body[0].value
        if isinstance(doc, ast.Constant) and isinstance(doc.value, str):
            # From the `def` line, so a directive written above the definition
            # governs the docstring it introduces rather than stopping at the
            # signature.
            first = getattr(node, "lineno", doc.lineno)
            spans.append((first, doc.end_lineno or doc.lineno))
    return spans


def blocks(text: str, path: Path | None = None) -> list[tuple[int, int]]:
    """Blank-line-delimited runs of lines, 1-based inclusive.

    A fenced block is atomic — a blank line inside a code sample doesn't end
    the paragraph — and so is a **Python docstring**, for the same reason and
    on the same principle (#222). A docstring is one syntactic unit however
    many paragraphs it holds, so a `-block` directive written above a
    definition governs the whole of what that definition says, not just its
    first paragraph. Without it the only annotation that reaches a citation in
    a docstring's third paragraph is `-file`, which is far too blunt for the
    case: an ordinary sentence of prose that happens to name a code."""
    fenced = _fence_line_spans(text)
    if path is not None and path.suffix.lower() == ".py":
        fenced = fenced + _docstring_line_spans(text)

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
        out += _frontmatter_comments(text)
        return sorted(out)
    if suffix == ".py":
        try:
            offsets = _line_offsets(text)
            return [(tok.start[0], offsets[tok.start[0] - 1] + tok.start[1],
                     tok.string.lstrip("#"))
                    for tok in tokenize.generate_tokens(io.StringIO(text).readline)
                    if tok.type == tokenize.COMMENT]
        except (tokenize.TokenError, IndentationError, SyntaxError):
            pass                                  # fall through to the crude scan
    # Every other language: a grammar when one is installed, the marker scan
    # otherwise. The scan's own comment admits what it cannot do — a `#` inside
    # a shell string reads as a comment to it — and this is where that stops
    # being true, without luria learning a single language's comment syntax.
    from . import syntax
    parsed = syntax.comments(path, text)
    if parsed is not None:
        return sorted(_with_inner_markers(parsed))
    out = []
    offsets = _line_offsets(text)
    for n, line in enumerate(text.splitlines(), 1):
        for m in COMMENT_MARKER_RE.finditer(line):
            out.append((n, offsets[n - 1] + m.end(), line[m.end():]))
    return out


def _with_inner_markers(
        fragments: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    """Each comment, plus what follows any further marker on its first line.

    A grammar reads `// note  // dir: x` as one comment, which is true, and
    would leave the appended directive un-opened and so unread. The marker
    scan splits there and the split is a spelling people use, so a grammar's
    precision is applied to *finding* comments and not to re-litigating what
    counts as the start of one. Only the first line: in a block comment a
    marker further down is at a line this fragment cannot name."""
    out = list(fragments)
    for line, offset, body in fragments:
        head = body.split("\n", 1)[0]
        for m in COMMENT_MARKER_RE.finditer(head):
            out.append((line, offset + m.end(), head[m.end():]))
    return out


# A whole-line YAML comment: `#` first on the line. A `#` inside a value is
# data (`title: 'Issue #12'`), and a `#` in the body is a heading — the scan
# never leaves the frontmatter, so neither is ever read as a comment.
_YAML_COMMENT_RE = re.compile(r"^[ \t]*#(.*)$")


def _frontmatter_comments(text: str) -> list[tuple[int, int, str]]:
    """YAML comments in a markdown file's frontmatter, as comment fragments.

    A reference field is a citation site — `superseded_by:` naming a retired
    document is reported at its line like any sentence would be — but the
    only comment the markdown scan read was an HTML one, and frontmatter
    is YAML. The directive that could answer the finding in place had no
    place to stand, and the file-scoped one was the only spelling left. The
    frontmatter has its own comment syntax; this reads it, so a line-scoped
    directive works there the way it does in a `.py` file:

        # inactive-ok: ADR-012 — the successor was itself later retired
        superseded_by: ADR-012
    """
    from . import doc_refs
    span = doc_refs._frontmatter_span(text)
    if span is None:
        return []
    out = []
    offsets = _line_offsets(text)
    for n, line in enumerate(text[:span[1]].splitlines(), 1):
        m = _YAML_COMMENT_RE.match(line)
        if m:
            out.append((n, offsets[n - 1] + m.start(1), m.group(1)))
    return out


def _line_offsets(text: str) -> list[int]:
    out, pos = [], 0
    for line in text.splitlines(keepends=True):
        out.append(pos)
        pos += len(line)
    return out or [0]


def find(path: Path, text: str, names: set[str] | None = None,
         as_of: dt.date | None = None) -> list[Directive]:
    """Every LIVE directive in `path`, with the lines each one governs resolved.

    An expired one (`until <date>`, #58) is simply absent: the linter behaves
    as if it were never written, which is what an expiry is for. Dropping it
    here rather than at each consumer is what makes that uniform — `find` is
    the one place directives are read, so nothing downstream has to know the
    feature exists. `find_expired` is how they stay reportable."""
    today = as_of or dt.date.today()
    return [d for d in _parse(path, text, names) if not d.expired(today)]


def _parse(path: Path, text: str, names: set[str] | None = None) -> list[Directive]:
    """Every directive in `path`, expired or not — one parser, two views."""
    spans = blocks(text, path)
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
        args, expires, bad_expiry = _split_expiry(args)
        reason = body.split("—", 1)[1].strip().rstrip("->").strip() \
            if "—" in body else ""
        found.append(Directive(
            name, scope, args, reason, path, line_no,
            (offset, offset + len(body)),
            _governed(scope, line_no, spans, path, text),
            expires, bad_expiry))
    return found


def find_expired(path: Path, text: str, names: set[str] | None = None,
                 as_of: dt.date | None = None) -> list[Directive]:
    """The directives `find` dropped because their date has passed.

    Inert is not the same as invisible. A check that starts failing again with
    no word about the acknowledgement sitting right above it is a puzzle rather
    than a report, so the expiry is worth naming where the failure appears."""
    today = as_of or dt.date.today()
    return [d for d in _parse(path, text, names) if d.expired(today)]


def _governed(scope: str, line: int, spans: list[tuple[int, int]],
              path: Path, text: str) -> frozenset[int]:
    if scope == FILE:
        return frozenset(range(1, len(text.splitlines()) + 1))
    if scope == LINE:
        return frozenset({line} | _entry_below(text, line))
    own = next((s for s in spans if s[0] <= line <= s[1]), (line, line))
    # A directive standing alone between blank lines has no content block of its
    # own, so the block it means is the one it introduces. This is the reading of
    # "block", not an exception to it — and it is the whole reason `-block`
    # exists as a separate scope from `-line`.
    if _directive_only(text, own, path):
        nxt = next((s for s in spans if s[0] > own[1]), None)
        own = nxt if nxt else own
    # A run of non-blank lines is a guess at where a block ends, and it is
    # wrong wherever a language lets one construct hold a blank line. A
    # grammar, when one is installed, extends the run to the syntactic unit
    # the directive introduces — never narrows it, so a directive that works
    # without the extra works the same with it.
    from . import syntax
    own = syntax.grow(path, text, own, after=line)
    return frozenset(range(own[0], own[1] + 1))


def _entry_below(text: str, line: int) -> set[int]:
    """The lines "the next line" means: one, in prose — but in frontmatter a
    field is an entry, and a `superseded_by:` written as a list carries its
    code on the line after its key. A comment above the key that reached
    only the key would excuse nothing, and `luria repair` writes exactly
    that list shape. So inside the frontmatter the line below extends over
    the entry's continuation lines: indented ones, and `- ` items."""
    from . import doc_refs
    lines = text.splitlines()
    below = {line + 1}
    span = doc_refs._frontmatter_span(text)
    if span is None or line + 1 > text.count("\n", 0, span[1]):
        return below
    n = line + 1                                  # 1-based; lines[n] is n+1
    while n < len(lines) and re.match(r"[ \t]+\S|- ", lines[n]):
        n += 1
        below.add(n)
    return below


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
    if directive.bad_expiry is not None:
        # Checked first: an expiry nobody can read is the problem that makes a
        # directive outlive its author's intent, which is the exact rot `until`
        # exists to stop. The directive stays LIVE meanwhile — dropping a
        # suppression over a typo breaks a build for a reason the failure would
        # not explain, and this report is the one that does.
        got = ("`until` names no date" if directive.bad_expiry == "until"
               else f"`until {directive.bad_expiry}` is not a date")
        return f"`{directive.name}`: {got} — write it as `until YYYY-MM-DD`"
    if not directive.args:
        return f"`{directive.name}` names no argument"
    if valid_args is not None:
        unknown = sorted(a for a in directive.args if a.lower() not in valid_args)
        if unknown:
            return (f"`{directive.name}` names unknown "
                    f"{'argument' if len(unknown) == 1 else 'arguments'}: "
                    f"{', '.join(unknown)}")
    return None
