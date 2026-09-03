"""What a status *means* in one scheme, declared beside the records.

[ADR-003](../record/decisions.d/ADR-003.md) closed the status vocabulary to
five words and put a lint behind it, on the strength of an audit finding that
every surface guarded by an executable check had held and every surface
governed by prose convention alone had drifted.

The five words held. What that decision did not cover is the layer above them:
**a status means something different in every scheme**, and that meaning has
only ever lived in prose — a template comment and, if a project is diligent, a
decision record. Which is precisely the surface ADR-003 measured as the one
that drifts.

It drifted. A downstream project adopting luria wrote three decisions to say
what its statuses mean, and twice found the record doing something else: a
scheme where fifty-one of fifty-one records sat at the in-force status because
extraction defaulted there and nothing said otherwise, and a sibling scheme
whose template said status carried a judgment that a tag was actually carrying.
Both were caught by a person re-reading, which is what ADR-003 says not to rely
on.

So this is that decision applied one level up, and deliberately not further:

- **The five words stay closed.** Nothing here adds a status. A `statuses.yaml`
  key outside the closed set is an error, not a new word.
- **A scheme may declare which of the five it uses**, and a record whose status
  is not declared fails the lint. That narrows the vocabulary per scheme without
  reopening it.
- **A scheme may say what each one means**, and the meaning renders into the
  generated index — next to the column it explains, where a reader is, rather
  than in a template only the author of a new record ever opens.

Shaped after `tags.yaml`, which does the same job for the other browsing axis:
the vocabulary lives in YAML beside the records, and any *rule* about combining
them lives in `luria.toml`. Declaring nothing keeps today's behaviour exactly —
all five words, no legend.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import yaml

# ADR-003's vocabulary. This module narrows it and never extends it.
CLOSED = ("Active", "Proposed", "Deferred", "Superseded", "Rejected")

# ADR-003's shape: the word, then optionally an em-dash and a note.
_NOTE_RE = re.compile(r"\s+—\s+")


@dataclass(frozen=True)
class Status:
    """A status: one word from the closed vocabulary, the successor a
    superseded document names, and an optional prose note. Three fields,
    three types:

        status: Superseded
        superseded_by: FX-ADR-032
        status_note: the capital never burned after all

    The word is data, checked against the vocabulary. `superseded_by` is a
    reference — structure, checked and resolved like any declared
    reference, and the typed edge (ADR-tmpxmnac). The note is prose — a
    prose key like `summary:` (ADR-051): rendered, linked by the fixer,
    scanned for citations, for whatever the field cannot say. They used to
    share one scalar, `Superseded — by X`, split in six places with three
    spellings of one regex; that form is still read, reported by the lint,
    and moved by `luria index`."""
    value: str
    note: str = ""
    superseded_by: tuple[str, ...] = ()

    @property
    def display(self) -> str:
        return display(self)


def display(status: Status, link=None) -> str:
    """`Superseded — by X; note`: the reading a status has always had,
    composed from the fields. `link` renders a successor's code the way
    the surface it lands on wants — a relative link in the index, a
    wikilink on the site — and bare codes are the default."""
    link = link or (lambda code: code)
    parts = []
    if status.superseded_by:
        parts.append("by " + ", ".join(link(c) for c in status.superseded_by))
    if status.note:
        parts.append(status.note)
    return f"{status.value} — {'; '.join(parts)}" if parts else status.value


def parse(raw) -> Status:
    """The combined scalar — `Superseded — by ADR-035` — read apart."""
    text = str(raw or "").strip()
    word, *rest = _NOTE_RE.split(text, maxsplit=1)
    return Status(word.strip(), rest[0].strip() if rest else "")


def of(meta: dict) -> Status:
    """A document's status from its frontmatter, whichever form it wrote.

    `status_note:` wins when present; a note still riding in `status:` is
    read too, so nothing breaks between the field arriving and the file
    being moved."""
    meta = meta or {}
    parsed = parse(meta.get("status"))
    note = str(meta.get("status_note") or "").strip()
    raw = meta.get("superseded_by")
    codes = raw if isinstance(raw, list) else ([raw] if raw not in (None, "") else [])
    return Status(parsed.value, note or parsed.note,
                  tuple(str(c).strip() for c in codes if str(c).strip()))


def combined(meta: dict) -> bool:
    """True when `status:` still carries the note — the form to move."""
    return bool(parse((meta or {}).get("status")).note)


# The `status:` block and, if present, the `status_note:` and
# `superseded_by:` blocks: a scalar or list with any indented or `- `
# continuation lines.
_STATUS_BLOCK_RE = re.compile(r"^status:.*(?:\n[ \t]+.*)*", re.MULTILINE)
_NOTE_BLOCK_RE = re.compile(r"^status_note:.*(?:\n[ \t]+.*)*\n?", re.MULTILINE)
_BY_BLOCK_RE = re.compile(r"^superseded_by:.*(?:\n(?:[ \t]+|- ).*)*\n?", re.MULTILINE)
# The old canonical note, `by CODE …`: the shape `luria migrate` used to
# write, read once more so the repair can turn it into the field.
_BY_RE = re.compile(r"^by\s+")


def set_status(text: str, value: str, note: str = "",
               superseded_by=()) -> str:
    """The file text with its status written in the three-field form.

    The one writer of the fields, so the shape has one spelling: the
    migration's tombstone and the index's repair both come through here.
    Existing `status_note:` and `superseded_by:` blocks are replaced, never
    duplicated."""
    lines = f"status: {value}"
    fields = {}
    if superseded_by:
        fields["superseded_by"] = [str(c) for c in superseded_by]
    if note:
        fields["status_note"] = note
    if fields:
        dumped = yaml.safe_dump(fields, allow_unicode=True, width=10 ** 6,
                                default_flow_style=False, sort_keys=False)
        lines += "\n" + dumped.rstrip("\n")
    text = _NOTE_BLOCK_RE.sub("", text, count=1)
    text = _BY_BLOCK_RE.sub("", text, count=1)
    return _STATUS_BLOCK_RE.sub(lambda _: lines, text, count=1)


def successor_in(note: str) -> str | None:
    """The code an old-form `by CODE …` note opens with, or None.

    Read the way prose is read everywhere else — links unwrapped, then the
    scheme-driven finder (ADR-046). This is the repair's reader only: the
    relation itself lives in `superseded_by:`, and nothing infers it from
    prose at check time."""
    from . import doc_refs
    plain = doc_refs.UNLINK_RE.sub(r"\1", note or "").strip()
    opening = _BY_RE.match(plain)
    if not opening:
        return None
    refs = [r for r in doc_refs.find_refs(plain) if r.kind == "scheme"]
    if not refs or refs[0].start != opening.end():
        return None
    return refs[0].describe()


def repair(text: str) -> str | None:
    """A document's text brought to the three-field form, or None when it
    is there already: a note riding in `status:` moves to `status_note:`,
    and a Superseded document whose old-form note opens with `by CODE` gets
    `superseded_by:` — the note dropped when it said only that, kept
    verbatim when it said more. Reads the values through YAML rather than
    by eye, so a quoted multi-line note comes through intact."""
    from .adr_index import parse_frontmatter
    meta, _ = parse_frontmatter(text)
    if not meta:
        return None
    status = of(meta)
    changed = combined(meta)
    successors = status.superseded_by
    note = status.note
    if status.value == "Superseded" and not successors:
        if code := successor_in(note):
            successors = (code,)
            changed = True
            from . import doc_refs
            plain = doc_refs.UNLINK_RE.sub(r"\1", note).strip()
            if plain == f"by {code}":
                note = ""
    if not changed:
        return None
    return set_status(text, status.value, note, successors)


def split(text: str) -> str | None:
    """Kept as the name the split was introduced under; `repair` is the
    whole operation."""
    return repair(text)


def populate(scheme) -> list:
    """Bring every document to the three-field form — a source repair
    `luria index` runs, like `created:` from a journal entry's path
    (ADR-031): the file already states the facts, and the tree is made to
    say so in the fields that carry them."""
    moved = []
    for path in [*scheme.documents().values(), *scheme.temp_documents().values()]:
        text = path.read_text(encoding="utf-8")
        if (fresh := repair(text)) is not None:
            path.write_text(fresh, encoding="utf-8")
            moved.append(path)
    return moved


def declared(scheme) -> dict[str, dict]:
    """`{status: {label, blurb}}` as the scheme declares it, or `{}`.

    An empty mapping means "declares nothing", which is the default and leaves
    every check below inert — an unconfigured project must not be told it has a
    problem, and must not be told it is clean either.
    """
    path = scheme.statuses_yaml
    if not path.exists():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {k: (v or {}) for k, v in loaded.items()}


def problems(scheme) -> list[str]:
    """Keys a scheme declares that are not statuses.

    The one place this module can catch a project trying to invent a word. It
    is worth catching loudly: a `statuses.yaml` naming `Accepted` would render a
    legend and silence nothing, so the file would look like it was working.
    """
    from .config import current
    bad = [k for k in declared(scheme) if k not in CLOSED]
    if not bad:
        return []
    rel = current().rel(scheme.statuses_yaml)
    return [f"{rel}: {k!r} is not a status (want one of: "
            f"{', '.join(CLOSED)}) — the vocabulary is closed (ADR-003)"
            for k in bad]


def undeclared(scheme, status: str) -> bool:
    """True when the scheme declares a vocabulary and this status is not in it.

    `status` is the bare word: ADR-003 allows a trailing ` — note`, and the
    note is a qualifier on the word rather than part of it.
    """
    vocab = declared(scheme)
    return bool(vocab) and parse(status).value not in vocab


def legend(scheme) -> str:
    """The declared statuses as a markdown table, or `''` when none are.

    Rendered above the index table rather than behind a stub placeholder, so
    that adopting the file is enough to make the meaning visible. A legend
    nobody added a placeholder for is a legend nobody reads, which is the
    failure this exists to fix.
    """
    vocab = declared(scheme)
    if not vocab:
        return ""
    rows = []
    for status, meta in vocab.items():
        label = meta.get("label", "")
        blurb = meta.get("blurb", "")
        # Sentence-case the first letter only; `str.capitalize()` lowercases
        # everything after it and mangles anything capitalised in the blurb.
        text = f"{blurb[:1].upper()}{blurb[1:]}" if blurb else ""
        rows.append(f"| `{status}` | {label} | {text} |")
    return ("What the status column means in this scheme — the words are "
            "luria's, the meanings are this project's.\n\n"
            "| Status | | Means |\n|---|---|---|\n" + "\n".join(rows) + "\n")


# Below the floor a uniform status is not evidence of anything: three records
# that all happen to be in force is a young scheme, not an unused field.
FLOOR = 10


def uniform(scheme) -> tuple[str, int] | None:
    """`(status, count)` when every record in the scheme shares one status.

    A status field where every record agrees is indistinguishable from no
    status field, and the difference matters because other machinery reads it:
    `active` decides what counts as retired, and `retired-citations` fires off
    that. A scheme in this state has an enforcement mechanism that cannot fire,
    and the build is green *because* nothing is being judged (#104).

    `None` below the floor, for a scheme rendered as one document (a
    design-principles page where everything is in force is the expected state,
    not a smell), when the scheme declares a vocabulary of exactly one status,
    which is a project saying so on purpose, and when the scheme sets
    `uniform_ok` — the acknowledgement this finding lacked. See
    `acknowledged_rows` for where that reason surfaces instead.
    """
    from . import adr_index
    if scheme.render == "document" or scheme.uniform_ok:
        return None
    vocab = declared(scheme)
    if len(vocab) == 1:
        return None
    found: list[str] = []
    for path in [*scheme.documents().values(), *scheme.temp_documents().values()]:
        meta, _ = adr_index.parse_frontmatter(path.read_text(encoding="utf-8"))
        if status := of(meta).value:
            found.append(status)
    if len(found) < FLOOR or len(set(found)) != 1:
        return None
    return found[0], len(found)


def uniform_rows() -> list[str]:
    """One line per scheme whose status field carries no information."""
    from .config import current
    rows = []
    for prefix, scheme in current().schemes.items():
        if hit := uniform(scheme):
            status, count = hit
            rows.append(f"{prefix}: {count}/{count} at `{status}`")
    return rows


def acknowledged_rows() -> list[str]:
    """One line per scheme whose uniformity a human has vouched for.

    The counterpart to `uniform_rows`. An acknowledged scheme is still
    uniform — nothing there is being judged, and the citation checks still
    cannot fire — so the fact does not stop being true when someone explains
    it. It stops being a *finding* and becomes a note, which is the same
    bargain `inactive-ok:` strikes at a citation site: the reason is
    mandatory, and it renders where the finding would have.
    """
    from .config import current
    from . import adr_index
    rows = []
    for prefix, scheme in current().schemes.items():
        if not scheme.uniform_ok:
            continue
        found = []
        for path in [*scheme.documents().values(),
                     *scheme.temp_documents().values()]:
            meta, _ = adr_index.parse_frontmatter(path.read_text(encoding="utf-8"))
            if status := of(meta).value:
                found.append(status)
        if len(found) >= FLOOR and len(set(found)) == 1:
            rows.append(f"{prefix}: {len(found)}/{len(found)} at "
                        f"`{found[0]}` — {scheme.uniform_ok}")
    return rows
