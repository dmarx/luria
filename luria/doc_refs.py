#!/usr/bin/env python3
"""Find (and fix) documentation references that should be markdown hyperlinks.

The docs cite three kinds of internal reference constantly — ADRs (`ADR-004`),
design principles (`design-principles #13`) and GitHub issues/PRs (`#551`). Most
were already links; a long tail was bare text, so "read the ADR I just cited"
meant grepping `docs/decisions/` by hand.

This module is the shared scanner behind two callers:

  * `scripts/lint_docs.py` — reports bare references as lint violations
    (`make lint-docs`, CI).
  * `scripts/ci/link_doc_refs.py --fix` — rewrites them into links.

Both use the same masking rules, so the linter can never demand a rewrite the
fixer wouldn't make.

Masking
-------
A reference only counts when it sits in ordinary prose. Skipped: fenced and
inline code, HTML comments, autolinks and bare URLs, the label *and* target of
an existing markdown link, reference-style link definitions, and YAML
frontmatter — except an ADR's `summary:`, which is prose. The generator renders
a summary into `docs/decisions/README.md` *and* into
`docs/decisions/tags/<tag>.md`, one directory deeper, and rebases relative
targets per output, so a link written there is correct in both (ADR-005). The
rewrite is verified against the YAML rather than assumed safe.

Link bases
----------
Links are written relative to where the text is *rendered*, which is not always
where the file lives: `changelog.d/*.md` is assembled into `/CHANGELOG.md` and
`devlog.d/*.md` into `docs/devlog.md` (ADR-002). `link_base()` maps a
path to the directory its links must resolve from.
"""

# unresolved-ok-file: ADR-019, ADR-157 — illustrative codes in this module's prose
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml  # noqa: F401  (re-exported for callers that parse frontmatter)

from . import directives, remotes
from .adr_index import parse_frontmatter
from .config import Config, current


# ── Reference patterns ───────────────────────────────────────────────────
#
# Order matters: `design-principles #13` must win over the bare `#13` that
# would otherwise be read as issue 13.

DP_RE = re.compile(
    r"\b(?:(?:design[- ])?principles?|DP)"  # the doc, however it's spelled
    r"(?:\.md)?"                         # sometimes cited by filename
    r"\s*(?P<bold>\*\*)?\s*"             # `design-principles **#17**` occurs;
    r"#(?P<num>\d{1,3})\b(?(bold)\*\*)",  # close the bold only if we opened it
    re.IGNORECASE,
)
# The tail of "design principles #17 and #18" / "#17, #18": each sibling is a
# principle, carried by the label that opened the run.
DP_CHAIN_RE = re.compile(
    r"[ \t]*(?:,|;|and|or|&|/|\+)[ \t]*"
    r"(?P<ref>(?P<bold>\*\*)?#(?P<num>\d{1,3})\b(?(bold)\*\*))"
)
# Kept as a module constant because it is the shape the code-comment scan
# expects; per-project schemes come from `config.Scheme.pattern`.
ADR_RE = re.compile(r"\bADR[- ](?P<num>\d{1,4})\b")
# 1–4 digits keeps six-digit hex colours out; `(?!\w)` keeps `#123abc` out.
ISSUE_RE = re.compile(r"(?<![\w&#/])#(?P<num>\d{1,4})(?!\w)")

# A low `#N` is ambiguous: the docs also number principles, an ADR's open
# questions, user stories and gotchas the same way ("the dual of #1", "open
# question #3", "story #2", "gotcha #2"). Above the highest principle number the
# ambiguity is gone; at or below it, only an explicit cue makes it an issue —
# optionally reached through a run of already-cued siblings ("issues #376, #387").
ISSUE_CUE_RE = re.compile(
    r"(?:\bissues?|\bPRs?|\bpull requests?|\bresolves?|\bfix(?:es|ed)?"
    r"|\bcloses?|\btracked in|\btoward)\s*"
    r"(?:#\d{1,4}[\s,;]*(?:and|or|&|/|\+)?\s*)*$",
    re.IGNORECASE,
)

KINDS = ("dp", "adr", "issue")


@dataclass(frozen=True)
class Ref:
    kind: str          # "adr" | "dp" | "issue" | "remote"
    num: int
    start: int
    end: int
    text: str          # the matched source text
    line: int          # 1-based
    # For a remote reference, the two halves of `SG-ADR-032`: which project,
    # and which code in that project's namespace (ADR-015). Empty otherwise.
    remote: str = ""
    code: str = ""

    def describe(self) -> str:
        if self.kind == "remote":
            return f"{self.remote}-{self.code}"
        return {"adr": f"ADR-{self.num:03d}",
                "dp": f"design principle #{self.num}",
                "issue": f"#{self.num}"}[self.kind]


# ── Masking ──────────────────────────────────────────────────────────────

FENCE_RE = re.compile(r"^[ \t]{0,3}(?P<fence>```+|~~~+)", re.MULTILINE)
CODE_SPAN_RE = re.compile(r"(?P<ticks>`+)(?:.|\n)*?(?P=ticks)")
COMMENT_RE = re.compile(r"<!--(?:.|\n)*?-->")
AUTOLINK_RE = re.compile(r"<[a-zA-Z][a-zA-Z0-9+.-]*:[^<>\s]*>")
BARE_URL_RE = re.compile(r"(?<![(<])\b[a-z][a-z0-9+.-]*://[^\s<>)\]]+")
LINK_RE = re.compile(r"!?\[(?P<label>[^\]]*)\]\((?P<target>[^)]*)\)")
REF_LINK_RE = re.compile(r"!?\[(?P<label>[^\]]*)\]\[[^\]]*\]")
LINK_DEF_RE = re.compile(r"^[ \t]{0,3}\[[^\]]+\]:.*$", re.MULTILINE)
LINK_DEF_LABEL_RE = re.compile(r"^[ \t]{0,3}\[([^\]]+)\]:", re.MULTILINE)
SHORTCUT_RE = re.compile(r"!?\[([^\]\[]+)\](?![(\[:])")
HTML_ANCHOR_RE = re.compile(r"<a\b[^>]*>(?:.|\n)*?</a>", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<[/!]?[A-Za-z][^<>]*>")

# CommonMark's HTML-block tag list (type 6). A line opening one of these starts
# a raw-HTML block that runs to the next blank line, and markdown inside it is
# NOT parsed — so a `[#104](…)` written there renders as literal brackets. The
# README's screenshot gallery is exactly this shape, so references inside an
# HTML block get an `<a href>` instead (see `html_block_spans`).
HTML_BLOCK_TAGS = (
    "address|article|aside|base|basefont|blockquote|body|caption|center|col|"
    "colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|"
    "footer|form|frame|frameset|h1|h2|h3|h4|h5|h6|head|header|hr|html|iframe|"
    "legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|"
    "section|source|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul"
)
HTML_BLOCK_START_RE = re.compile(
    rf"^ {{0,3}}</?(?:{HTML_BLOCK_TAGS})(?:[ \t/>]|$)", re.IGNORECASE
)


def _frontmatter_span(text: str) -> tuple[int, int] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 3)
    return None if end == -1 else (0, end + 5)


SUMMARY_KEY_RE = re.compile(r"^summary:", re.MULTILINE)
NEXT_KEY_RE = re.compile(r"^(?=[A-Za-z_][\w-]*:|---[ \t]*$)", re.MULTILINE)


def summary_span(text: str) -> tuple[int, int] | None:
    """The value of an ADR's `summary:` key — the one part of frontmatter that
    is prose, and the only part that may carry links.

    The rest of the frontmatter is data (`status:`, `issue:`, `tags:`) that the
    generator reads by value; a link there would be a link in a data field. The
    summary is different: `build_adr_index.py` renders it as markdown into the
    index and the tag pages, and rebases relative targets per output (ADR-005),
    so a link written here works in every place it lands."""
    fm = _frontmatter_span(text)
    if not fm:
        return None
    head = text[:fm[1]]
    key = SUMMARY_KEY_RE.search(head)
    if not key:
        return None
    nxt = NEXT_KEY_RE.search(head, key.end())
    return key.end(), (nxt.start() if nxt else len(head))


def _fence_spans(text: str) -> list[tuple[int, int]]:
    """Spans covered by fenced code blocks, including their fence lines."""
    spans: list[tuple[int, int]] = []
    open_at: int | None = None
    marker = ""
    for m in FENCE_RE.finditer(text):
        fence = m.group("fence")
        if open_at is None:
            open_at, marker = m.start(), fence[0] * 3
        elif fence.startswith(marker):
            end = text.find("\n", m.end())
            spans.append((open_at, len(text) if end == -1 else end + 1))
            open_at = None
    if open_at is not None:            # unclosed fence runs to EOF
        spans.append((open_at, len(text)))
    return spans


def _code_span_spans(text: str) -> list[tuple[int, int]]:
    """Inline code spans, paired *within a paragraph*.

    Pairing backticks across the whole document is what a first pass did, and it
    is wrong: one unbalanced backtick — inside a fenced block, or a stray one in
    7,000 lines of devlog — inverts which side of every later backtick is code,
    and `` `#123` `` gets linked inside its own code span. Fenced blocks are cut
    out first (they are masked separately anyway) and each remaining paragraph
    pairs independently, so a desync can't outlive one paragraph. A code span
    can't contain a blank line, so nothing legitimate is lost."""
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
        # Capturing split so the separators stay in the list and offsets hold.
        for i, part in enumerate(re.split(r"((?<=\n)[ \t]*\n)", text[a:b])):
            if i % 2 == 0:
                for m in CODE_SPAN_RE.finditer(part):
                    spans.append((offset + m.start(), offset + m.end()))
            offset += len(part)
    return spans


def html_block_spans(text: str) -> list[tuple[int, int]]:
    """Character spans of raw-HTML blocks — a block-tag line through the next
    blank line. Code fences win, so a fenced `<div>` isn't one."""
    fences = _fence_spans(text)

    def fenced(pos: int) -> bool:
        return any(a <= pos < b for a, b in fences)

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
    """Fenced blocks and inline code spans — where markdown shows an example
    rather than states one. Callers that need to read HTML comments (which
    `masked` hides) mask with this instead."""
    return _fence_spans(text) + _code_span_spans(text)


def in_html_block(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(a <= pos < b for a, b in spans)


# What an `unexempt:` directive can switch back on, and the spans it governs.
UNEXEMPT_REGIONS = {
    "codeblock": _fence_spans,
    "inline-code": _code_span_spans,
}
ANY_MD = Path("prose.md")           # suffix is all the directive parser needs


def link_base(path: Path) -> Path:
    """Back-compat shim: the rule lives on the config (`Config.link_base`)."""
    return current().link_base(path)


def unexempt_spans(text: str, path: Path) -> list[tuple[int, int]]:
    """Character spans an `unexempt:` directive puts back under the linter.

    Code is exempt because code is quoted, not asserted — but a snippet in the
    docs can be quasi-prose, citing decisions the reader should be able to
    follow. `<!-- unexempt: codeblock -->` above a fence says so for that block.
    The caveat is inherent, not a bug: markdown inside a fence renders
    literally, so the link the linter then demands shows as `[ADR-157](…)` in
    the sample. That is the trade the directive exists to let an author make."""
    out: list[tuple[int, int]] = []
    for d in directives.find(path, text, {"unexempt"}):
        for arg in d.args:
            spans = UNEXEMPT_REGIONS.get(arg.lower())
            if spans is None:
                continue
            for start, end in spans(text):
                first = text.count("\n", 0, start) + 1
                last = text.count("\n", 0, max(start, end - 1)) + 1
                if any(d.covers(n) for n in range(first, last + 1)):
                    out.append((start, end))
    return out


def directive_problems(path: Path, text: str) -> list[str]:
    """Unexempt directives that name a region that doesn't exist — a directive
    that silently does nothing is worse than no directive."""
    out = []
    for d in directives.find(path, text, {"unexempt"}):
        problem = directives.problems(d, set(UNEXEMPT_REGIONS))
        if problem:
            out.append(f"{path.name}:{d.line}: {problem} "
                       f"(known: {', '.join(sorted(UNEXEMPT_REGIONS))})")
    return out


def masked(text: str, path: Path = ANY_MD) -> list[bool]:
    """One flag per character: True where a reference must be ignored."""
    mask = [False] * len(text)

    def cover(start: int, end: int) -> None:
        for i in range(max(0, start), min(len(text), end)):
            mask[i] = True

    fm = _frontmatter_span(text)
    if fm:
        cover(*fm)
        summary = summary_span(text)
        if summary:                       # …except the summary, which is prose
            for i in range(*summary):
                mask[i] = False
    for span in _fence_spans(text):
        cover(*span)
    for span in _code_span_spans(text):
        cover(*span)
    for regex in (COMMENT_RE, AUTOLINK_RE, BARE_URL_RE,
                  REF_LINK_RE, LINK_DEF_RE, HTML_ANCHOR_RE, HTML_TAG_RE):
        for m in regex.finditer(text):
            cover(m.start(), m.end())
    # An inline link: both halves are off-limits. The label already *is* the
    # hyperlink's text, and the target is a URL/path.
    for m in LINK_RE.finditer(text):
        cover(m.start(), m.end())
    # Shortcut reference links — `[ADR-019]` with an `[ADR-019]: …` definition
    # further down. Already a hyperlink; only the *undefined* ones are bare.
    labels = {m.group(1).strip().lower() for m in LINK_DEF_LABEL_RE.finditer(text)}
    for m in SHORTCUT_RE.finditer(text):
        if m.group(1).strip().lower() in labels:
            cover(m.start(), m.end())
    # …and last, put back whatever an `unexempt:` directive asked for.
    for start, end in unexempt_spans(text, path):
        for i in range(max(0, start), min(len(text), end)):
            mask[i] = False
    return mask


def find_refs(text: str, path: Path = ANY_MD) -> list[Ref]:
    """All unlinked references in `text`, in source order."""
    mask = masked(text, path)
    line_of = _line_index(text)
    claimed = [False] * len(text)
    refs: list[Ref] = []

    def take(kind: str, num: int, start: int, end: int) -> bool:
        if any(mask[i] or claimed[i] for i in range(start, end)):
            return False
        for i in range(start, end):
            claimed[i] = True
        refs.append(Ref(kind, num, start, end, text[start:end], line_of(start)))
        return True

    # Remotes first: `SG-ADR-032` must claim its whole span before the local
    # ADR pattern reads the tail out of the middle of it and links a foreign
    # reference to a local file (ADR-015).
    if (remote_re := remotes.pattern()) is not None:
        for m in remote_re.finditer(text):
            span = range(m.start(), m.end())
            if any(mask[i] or claimed[i] for i in span):
                continue
            for i in span:
                claimed[i] = True
            code = remotes.normalise(m.group("code"))
            refs.append(Ref("remote", int(code.rsplit("-", 1)[1]),
                            m.start(), m.end(), m.group(0), line_of(m.start()),
                            remote=m.group("remote"), code=code))

    for kind, regex in (("dp", DP_RE), ("adr", ADR_RE), ("issue", ISSUE_RE)):
        for m in regex.finditer(text):
            if not take(kind, int(m.group("num")), m.start(), m.end()):
                continue
            if kind != "dp":
                continue
            # "design principles #17 and #18" — the label governs the whole run,
            # so the siblings are principles too, not issues 18 and 19.
            cursor = m.end()
            while (chain := DP_CHAIN_RE.match(text, cursor)) and take(
                    "dp", int(chain.group("num")), chain.start("ref"),
                    chain.end("ref")):
                cursor = chain.end()
    refs.sort(key=lambda r: r.start)
    return refs


def _line_index(text: str):
    starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            starts.append(i + 1)

    def line_of(pos: int) -> int:
        lo, hi = 0, len(starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if starts[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    return line_of


# ── Resolution ───────────────────────────────────────────────────────────


def adr_paths() -> dict[int, Path]:
    return current().schemes["ADR"].documents()


EXPLICIT_ANCHOR_RE = re.compile(r'^<a name="[a-z]+-(\d+)"></a>\s*$')
HEADING_ANCHOR_RE = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")


def dp_anchors() -> dict[int, str]:
    """Principle number → the anchor a link to it should use.

    An explicit `<a name="dp-13"></a>` wins over the heading's own slug, because
    a principle is a living document: reword one and every heading-derived link
    to it stops resolving, silently. The generator emits explicit anchors
    (ADR-012), but a project whose principles are still one hand-written file
    has only headings, and those still work."""
    anchors: dict[int, str] = {}
    principles = current().design_principles
    if not principles.exists():
        return {}
    for line in principles.read_text().splitlines():
        if m := EXPLICIT_ANCHOR_RE.match(line):
            anchors[int(m.group(1))] = line.split('"')[1]
        elif m := HEADING_ANCHOR_RE.match(line):
            num = int(m.group(1))
            if num in anchors:                     # explicit anchor already won
                continue
            slug = re.sub(r"[^a-z0-9 -]", "", f"{num}. {m.group(2)}".lower())
            anchors[num] = slug.replace(" ", "-")
    return anchors


def _relative(target: Path, base: Path) -> str:
    import os
    return os.path.relpath(target, base).replace(os.sep, "/")


def is_ambiguous_issue(ref: Ref, text: str, anchors: dict[int, str]) -> bool:
    """A `#N` small enough to be a principle number (or an ADR's third open
    question, or story 2) and with no cue saying otherwise. Left alone — a
    confidently wrong link is worse than a number the reader has to look up."""
    if ref.kind != "issue" or ref.num > max(anchors, default=0):
        return False
    return not ISSUE_CUE_RE.search(text[max(0, ref.start - 120):ref.start])


def resolve(ref: Ref, source: Path, adrs: dict[int, Path],
            anchors: dict[int, str], text: str | None = None) -> str | None:
    """The link target for `ref` as cited from `source`, or None when the
    reference can't be resolved (an ADR number with no file), would be a
    self-link (an ADR citing itself, a principle citing itself), or is an
    ambiguous low `#N` (needs `text` to judge)."""
    cfg = current()
    base = cfg.link_base(source)
    if ref.kind == "remote":
        # A URL, never a relative path — it is a different repository, so no
        # `link_base` applies and the same target is right from every file.
        return remotes.resolve(ref.remote, ref.code) or None
    if ref.kind == "issue":
        if text is not None and is_ambiguous_issue(ref, text, anchors):
            return None
        # No `issue_url` configured means issue numbers aren't linkable here,
        # which is a legitimate project shape — say nothing rather than guess.
        return cfg.issue_url.format(n=ref.num) if cfg.issue_url else None
    if ref.kind == "adr":
        target = adrs.get(ref.num)
        if target is None or target == source:
            return None
        return _relative(target, base)
    anchor = anchors.get(ref.num)
    if anchor is None:
        return None
    if source == cfg.design_principles:
        return f"#{anchor}"
    return f"{_relative(cfg.design_principles, base)}#{anchor}"


def _absorb_brackets(text: str, ref: Ref) -> tuple[int, int]:
    """`[ADR-019]` — a shortcut reference link with no definition, so it renders
    as literal brackets. Swallow them rather than nesting a link inside, which
    would render as `[ADR-019]` with the text linked."""
    if (ref.start > 0 and text[ref.start - 1] == "["
            and ref.end < len(text) and text[ref.end] == "]"):
        return ref.start - 1, ref.end + 1
    return ref.start, ref.end


UNLINK_RE = re.compile(r"\[([^\]]+)\]\([^)\s]*\)")


def _frontmatter_survives(old: str, new: str) -> bool:
    """True when rewriting the summary only *added links* — the YAML still
    parses, every other key is untouched, and stripping the new links yields the
    original summary back.

    A summary can be a quoted scalar, a folded block, or a plain multi-line
    scalar, and only the last of those has characters a link could disturb.
    Rather than enumerate which styles are safe, the rewrite is checked. The
    check lives here, not in the fixer, because the linter calls it too: a
    reference the fixer would decline to write must not be one the linter
    demands."""
    try:
        before, _ = parse_frontmatter(old)
        after, _ = parse_frontmatter(new)
    except yaml.YAMLError:
        return False
    if not before or not after:
        return False
    if {k: v for k, v in before.items() if k != "summary"} != \
       {k: v for k, v in after.items() if k != "summary"}:
        return False
    return UNLINK_RE.sub(r"\1", str(after.get("summary", ""))) == \
        str(before.get("summary", ""))


def rewritable_refs(text: str, source: Path, adrs: dict[int, Path],
                    anchors: dict[int, str]) -> list[Ref]:
    """The references `linkify` will actually turn into links — what the linter
    reports, so the two can never disagree."""
    refs = [r for r in find_refs(text, source)
            if resolve(r, source, adrs, anchors, text) is not None]
    span = summary_span(text)
    if not span or not any(span[0] <= r.start < span[1] for r in refs):
        return refs
    if _frontmatter_survives(text, _apply(text, refs, source, adrs, anchors)):
        return refs
    return [r for r in refs if not span[0] <= r.start < span[1]]


def linkify(text: str, source: Path, adrs: dict[int, Path] | None = None,
            anchors: dict[int, str] | None = None) -> tuple[str, int]:
    """Rewrite every resolvable bare reference in `text` as a link.
    Returns the new text and the number of rewrites."""
    adrs = adr_paths() if adrs is None else adrs
    anchors = dp_anchors() if anchors is None else anchors
    refs = rewritable_refs(text, source, adrs, anchors)
    return _apply(text, refs, source, adrs, anchors), len(refs)


def _apply(text: str, refs: list[Ref], source: Path, adrs: dict[int, Path],
           anchors: dict[int, str]) -> str:
    html = html_block_spans(text)
    out, cursor = [], 0
    for ref in refs:
        target = resolve(ref, source, adrs, anchors, text)
        if target is None:
            continue
        start, end = _absorb_brackets(text, ref)
        out.append(text[cursor:start])
        if in_html_block(start, html):
            out.append(f'<a href="{target}">{ref.text}</a>')
        else:
            out.append(f"[{ref.text}]({target})")
        cursor = end
    out.append(text[cursor:])
    return "".join(out)


def doc_files() -> list[Path]:
    """Every markdown file the reference rules apply to."""
    cfg = current()
    paths = [cfg.root / name for name in ("README.md", "CLAUDE.md", "AGENTS.md")]
    paths += [cfg.root / target for target in cfg.fragments.values()]
    paths += sorted(cfg.docs.rglob("*.md"))
    for fragment_dir in cfg.fragments:
        paths += sorted((cfg.root / fragment_dir).glob("*.md"))
    seen, out = set(), []
    for path in paths:
        if path.exists() and path not in seen and not cfg.is_generated(path):
            seen.add(path)
            out.append(path)
    return out
