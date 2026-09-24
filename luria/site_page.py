"""One staged page's frontmatter: the title Quartz shows and the properties
it renders (ADR-121).

    luria/site_page.py

Quartz 5 parses frontmatter in its `note-properties` plugin and draws a
properties panel from it. Before that plugin was configured, nothing parsed
the YAML at all: it rendered as a paragraph above the page, every page's
title was empty — so search results were blank cards, graph nodes fell back
to their paths and the explorer to filenames — and luria had been drawing its
own table of the record's facts into the body to make up for a frontmatter
that rendered as nothing (dmarx/anthology-of-the-sota#271).

So the staged frontmatter is a *view*, composed here, and Quartz renders it:

- the keys Quartz itself reads (`title`, `aliases`, `tags`, dates) are
  carried over, with the title spelled `CODE: title` so the code travels
  wherever the title does — a graph label, a search card, a backlink;
- the record's facts — status, dates, issues, influences, vocabulary values
  and the typed edges both ways — are added as properties under a reader's
  label, each link a root-relative wikilink the plugin resolves itself and
  also hands to the graph and backlinks.

The source YAML is untouched: this is the copy a generator reads, not the
record.
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import replace
from pathlib import Path

from . import doc_refs, edges, statuses
from .config import current

# Frontmatter Quartz reads for its own purposes. Carried into the staged page
# when the source has it; everything else in the source is the record's data,
# rendered — or not — as a labelled property instead.
QUARTZ_KEYS = ("title", "aliases", "alias", "tags", "tag", "date", "created",
               "modified", "lastmod", "updated", "published", "description",
               "draft", "permalink", "cssclasses", "socialImage")

# What the properties panel must not show: Quartz's own keys, including the
# ones the plugin derives (`created`, `modified`, `published`).
HIDDEN_PROPERTIES = QUARTZ_KEYS

# Invisible, and enough that neither the plugin nor luria's resolver reads a
# title's literal `[[` as a link. This project's ADR-025 is titled
# ``Wikilinks: `[[CODE]]` is a typed reference``.
_ZWSP = "​"
MD_LINK_RE = re.compile(r"\[([^\]\n]*)\]\(([^)\s]+)\)")
H1_RE = re.compile(r"^# (.+?)\s*$", re.MULTILINE)


def plain(text: str) -> str:
    """A title as data: markup read as text, and no `[[` left to be taken
    for a link by anything downstream."""
    text = MD_LINK_RE.sub(r"\1", text).replace("`", "")
    return text.replace("[[", "[" + _ZWSP + "[").strip()


def titles() -> dict[str, str]:
    """`{code: title}` for every referable document in the record.

    Read through `ref_status`, which already loads exactly this — one reader
    for "what documents are there and what are they called" rather than a
    second that could disagree (DP-4)."""
    from . import ref_status
    return {code: doc.title for code, doc in ref_status.load_docs().items()}


class Links:
    """Spells links for a property value, and remembers what it could not.

    Every target is first resolved by the record's own resolver — the fixer
    owns every target in this record, and a second speller would be the
    drift DP-4 names — and only then re-spelled as a wikilink from the vault
    root, which is the form the plugin resolves unambiguously. `prefix` is
    where a nested record is mounted in the parent's vault."""

    def __init__(self, source: Path, cfg, prefix: str = ""):
        self.source, self.cfg, self.prefix = source, cfg, prefix.strip("/")
        self.unresolved: list[str] = []

    def vault(self, label: str, target: str) -> str:
        if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target):
            return f"[{label}]({target})"
        path_part, sep, fragment = target.partition("#")
        from .site import destination
        try:
            absolute = (self.source.parent / path_part).resolve()
            rel = absolute.relative_to(self.cfg.root.resolve())
        except (ValueError, OSError):
            return label
        where = destination(self.cfg.root / rel, self.cfg).as_posix()
        where = posixpath.join(self.prefix, where) if self.prefix else where
        where = where[:-3] if where.endswith(".md") else where
        return f"[[{where}{sep}{fragment}|{label}]]"

    def text(self, text: str) -> str:
        """Prose from frontmatter — a status note — with its wikilinks and
        relative links made followable from the page."""
        expanded, _ = doc_refs.expand_wikilinks(text, self.source)
        self.unresolved += re.findall(r"\[\[[^\]]+\]\]", expanded)
        return MD_LINK_RE.sub(lambda m: self.vault(m.group(1), m.group(2)),
                              expanded)

    def code(self, code: str, known: dict[str, str]) -> str:
        """A code as a link, followed by the document's title.

        A code alone asks the reader to already know the record: `LIT-141`
        says nothing about what it is. Unknown codes render bare rather than
        guessing — a remote code, or one the lint already reports."""
        link = self.text(f"[[{code}]]")
        title = known.get(code, "")
        return f"{link} — {plain(title)}" if title else link


# How an inbound edge reads on the page it lands on. A declared reference
# field has no built-in inverse, so it is named for the field.
#
# The successor field is the scheme's to name (ADR-085), so the label
# follows the role rather than the word: a project retiring documents into
# `supplanted_by:` still reads "Supersedes" on the page that replaced one,
# because that is what the edge means.
def _inbound_labels(scheme) -> tuple[dict[str, str], tuple[str, ...]]:
    successor = statuses.successor_field(scheme)
    return ({successor: "Supersedes", edges.INFLUENCED_BY: "Influenced"},
            (successor, edges.INFLUENCED_BY))


def _repeats_an_outbound(edge, held: set[tuple[str, str]]) -> bool:
    """Whether an inbound edge says what this page's own frontmatter already
    said, through the converse field.

    A declared converse stores the fact on both documents, so rendering the
    backlink too prints one fact twice under two labels.
    inactive-ok: ADR-084 — the decision this behaviour follows from; it is
    Proposed because nobody has marked it Active, not because it is unsettled

    Read from what the page actually holds rather than from the declaration
    alone: a one-sided relation is a lint finding, and a record mid-repair
    should still see the edge it has."""
    from .contract import local_scheme
    from .relations import converse_of
    prefix = local_scheme(edge.source)
    if prefix is None:
        return False
    back = converse_of(prefix, edge.relation)
    return bool(back) and (back, edge.source) in held


def _label(field: str) -> str:
    return field.replace("_", " ").capitalize()


def _edges(outbound, inbound, scheme, links: Links,
           known: dict[str, str]) -> list[tuple[str, list[str]]]:
    """The typed edges. Supersession and influence already read from the
    page's own frontmatter (the status, `influenced_by:`), so outbound adds
    only the declared reference fields."""
    labels, order_of = _inbound_labels(scheme)
    out: dict[str, list[str]] = {}
    for edge in outbound:
        if edge.relation not in labels:
            out.setdefault(edge.relation, []).append(edge.target)
    rows = [(_label(relation), [links.code(c, known) for c in targets])
            for relation, targets in out.items()]
    held = {(e.relation, e.target) for e in outbound}
    grouped: dict[str, list[str]] = {}
    for edge in inbound:
        if not _repeats_an_outbound(edge, held):
            grouped.setdefault(edge.relation, []).append(edge.source)

    def order(relation: str) -> tuple[int, str]:
        known_ = relation in order_of
        return (order_of.index(relation) if known_ else len(order_of), relation)

    for relation in sorted(grouped, key=order):
        label = (labels.get(relation)
                 or f"Cited as “{relation.replace('_', ' ')}” by")
        rows.append((label, [links.code(c, known)
                             for c in sorted(set(grouped[relation]))]))
    return rows


def _scheme_of(source: Path, cfg):
    """The index-rendered scheme whose directory holds this document."""
    return next((s for s in cfg.schemes.values()
                 if s.render == "index" and source.parent == s.dir), None)


def _vocabulary(meta: dict, source: Path, scheme, links: Links):
    """A vocabulary field's *written* values, each linked to its page. The
    default is deliberately not shown: a reader is never shown a field the
    file does not have (ADR-076)."""
    if scheme is None:
        return []
    rows = []
    for vocab in scheme.vocabularies:
        # The status has its own row, composed from the fields around it.
        if vocab.field == statuses.FIELD:
            continue
        raw = meta.get(vocab.field)
        values = raw if isinstance(raw, list) else (
            [] if raw in (None, "") else [raw])
        if not values:
            continue
        page = scheme.vocab_dir(vocab.field)
        rows.append((_label(vocab.field), [
            links.vault(str(v), posixpath.relpath(
                (page / f"{v}.md").as_posix(), source.parent.as_posix()))
            for v in values]))
    return rows


def properties(meta: dict, source: Path, outbound=(), inbound=(),
               known: dict[str, str] | None = None, cfg=None,
               prefix: str = "") -> tuple[dict[str, object], list[str]]:
    """The record's facts as `{label: value}`, in reading order, plus any
    reference that resolved to nothing — frontmatter is data, which the
    prose scanner never reads, so this is the only place it can be counted.

    A single value stays a string; several are a list, which the plugin
    renders item by item."""
    cfg = cfg or current()
    known = titles() if known is None else known
    links = Links(source, cfg, prefix)
    scheme = _scheme_of(source, cfg)
    rows: list[tuple[str, list[str]]] = []
    status = statuses.of(meta, scheme)
    if status.value:
        status = replace(status, note=links.text(status.note))
        rows.append(("Status", [statuses.display(
            status, link=lambda c: links.code(c, known))]))
    # Shown only when it isn't 1, the same rule the index follows (ADR-016).
    if (version := meta.get("version")) and str(version).strip() != "1":
        rows.append(("Version", [str(version)]))
    # No date row: `date:` is carried as Quartz's own key, and its page
    # header already shows it.
    # `issue: '#21, #23'` is a real shape, so the separator is read out of the
    # field rather than assumed to be a space.
    if issues := re.findall(r"#\d+", str(meta.get("issue", ""))):
        rows.append(("Issue", [links.text(f"[[{i}]]") for i in issues]))
    influenced = [str(c).strip() for c in (meta.get("influenced_by") or [])]
    if influenced := [c for c in influenced if c]:
        rows.append(("Influenced by", [links.code(c, known) for c in influenced]))
    rows += _vocabulary(meta, source, scheme, links)
    rows += _edges(outbound, inbound, scheme, links, known)
    props = {label: values[0] if len(values) == 1 else values
             for label, values in rows}
    return props, links.unresolved


def title_of(meta: dict, body: str, code: str | None) -> str | None:
    """What the page is called: `CODE: title` for a scheme document, else
    its first heading, else nothing — and Quartz falls back to the filename.

    The code is kept because the record is cited by code: a graph node or a
    search card that says only the title cannot be matched to the `LIT-001`
    in the sentence that sent the reader there."""
    if title := str(meta.get("title") or "").strip():
        if code and not title.startswith(f"{code}:"):
            title = f"{code}: {title}"
        return plain(title)
    if heading := first_heading(body):
        return plain(heading.group(1))
    return code


def first_heading(body: str) -> re.Match | None:
    """The first `# ` heading outside code — a `#` comment in a fenced shell
    block is not a title."""
    quoted = doc_refs.code_spans(body)
    for match in H1_RE.finditer(body):
        if not any(a <= match.start() < b for a, b in quoted):
            return match
    return None


def without_title(body: str, title: str | None) -> str:
    """The body minus the heading that says what the title already says.
    Quartz draws the title above the page, so a heading repeating it prints
    it twice."""
    heading = first_heading(body)
    if heading is None or title is None or plain(heading.group(1)) != title:
        return body
    return (body[:heading.start()] + body[heading.end():].lstrip("\n")).lstrip("\n")
