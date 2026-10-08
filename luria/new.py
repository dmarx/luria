#!/usr/bin/env python3
"""`luria new [kind]` — scaffold an entry anywhere the record takes one (#42).

    luria new                  # a journal entry (the devlog), at its timestamp
    luria new adr              # the next free decision number, from _template.md
    luria new dp               # the next free principle number
    luria new changelog        # a fragment named for its filing moment
    luria new --draft f.json   # file the draft(s) a tool wrote to f.json

Prints the created path and nothing else. The identity fields a machine can
compute — filename, number, timestamp, `date:` — are computed; every other
field stays the template's placeholder, because a fragment is authored in a
markdown-aware editor, not assembled on a command line (ADR-036). A tool
driving the CLI can still set fields inline (`--title`, `--status`,
`--summary`, `--tags`, or any field the scheme declares) and hand over the
prose
(`--body`); a human never has to.

**The kinds are the config.** Every journal, scheme and fragment directory in
`luria.yaml` is a kind, so a project that adds a scheme gets its scaffold for
free — nothing here spells "adr". One kind is built in rather than
configured: `luria new migration` scaffolds a migration spec (ADR-040),
because migrations belong to the machinery, not to any one project's layout.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

from . import journal as journal_mod
from .config import current
from . import writes

TEMPLATE_NAME = "_template.md"

# Any `number:` line, whatever its value. Matching only the numeric shape the
# writers produce let a hand-written `number: tmpabcde` survive, so the writer
# put a second key above it — a duplicate the lint rejects, written by
# concretize on the trunk where nobody reviews (#355).
_NUMBER_LINE = re.compile(r"^number:[^\n]*\n", re.M)

# The shape written when a scheme has no _template.md of its own — enough to
# pass the lint (status, title, date, agreeing heading, and a value on the
# scheme's axis if it has one) and nothing else. Read off the scheme rather
# than assumed: the status word is one its vocabulary holds, and the axis is
# whichever field the scheme names, or none (the ADR on explicit relations).
FALLBACK_HEAD = """---
status: {status}
title: '{title}'
{axis}date: '{date}'
---

# {code}: {title}
"""

FALLBACK_BODY = """
Why this needed deciding, what was decided, and what was rejected.
"""


def fallback(scheme, code: str, date: str, title: str) -> str:
    """The fallback document for `scheme`: a starting status that is not in
    force — `Proposed` where the vocabulary has it, else the first word
    that is not the `active` one — and one placeholder value on the axis."""
    from .statuses import vocabulary
    words = vocabulary(scheme)
    status = ("Proposed" if "Proposed" in words else
              next((w for w in words if w != scheme.active), scheme.active))
    axis = f"{scheme.axis}:\n- record\n" if scheme.axis else ""
    return (FALLBACK_HEAD.format(status=status, title=title, axis=axis,
                                 date=date, code=code) + FALLBACK_BODY)


def kinds() -> dict[str, tuple[str, object]]:
    """Every place the record takes a new entry, keyed by the name `luria
    new` accepts. Derived from config, so the help text and the dispatch
    can't disagree about what this project scaffolds."""
    cfg = current()
    out: dict[str, tuple[str, object]] = {}
    for prefix, scheme in cfg.schemes.items():
        out[prefix.lower()] = ("scheme", scheme)
    for name in cfg.fragments:
        out[Path(name).name.removesuffix(".d")] = ("fragment", name)
    for name, jrnl in cfg.journals.items():
        out[name] = ("journal", jrnl)
    out.setdefault("migration", ("migration", None))
    return out


def default_kind() -> str | None:
    """The journal, when there is exactly one — `luria new` with no argument
    files a devlog entry, the commonest scaffold by far."""
    journals = list(current().journals)
    return journals[0] if len(journals) == 1 else None


def _sub_line(text: str, field: str, value, many: bool = False) -> str:
    """Replace a single-line frontmatter field, or a block one (`>-` /
    list) through its indented continuation lines. A field the form does not
    scaffold is appended rather than dropped — substitution on no match used
    to lose the value and report success.

    `value` may arrive as a tuple: Fire reads `--tags record,mechanism` as
    a Python literal, and that is the spelling the help text invites.

    `many` is the contract's word for the field's shape (#169). Without it
    a comma-separated value became the single string `'LIT-1, LIT-2'` — a
    list stringified and half-read, which is the finding #141 added, written
    by the tool that scaffolds the document."""
    pattern = re.compile(rf"^{field}:.*(?:\n(?:  |- ).*)*", re.MULTILINE)
    if isinstance(value, (tuple, list)):
        value = ", ".join(str(v) for v in value)
    if many:
        items = [v.strip() for v in str(value).split(",") if v.strip()]
        replacement = f"{field}:\n" + "\n".join(f"- {v}" for v in items)
    elif field == "summary":
        replacement = f"summary: >-\n  {value}"
    else:
        replacement = f"{field}: {value!r}"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return _append_field(text, replacement)


def _drop_field(text: str, field: str) -> str:
    """Remove a frontmatter field and its continuation lines — the block
    `_sub_line` would have replaced — leaving the comment above it."""
    pattern = re.compile(rf"^{field}:.*(?:\n(?:  |- ).*)*\n", re.MULTILINE)
    return pattern.sub("", text, count=1)


def _append_field(text: str, block: str) -> str:
    """Add a field at the end of the frontmatter, where a reader looks for
    what the form did not prompt for."""
    end = text.find("\n---\n", 3) if text.startswith("---\n") else -1
    if end == -1:
        return text
    return text[:end + 1] + block + "\n" + text[end + 1:]


def plural_fields(scheme) -> frozenset[str]:
    """The fields this scheme's contract declares hold a list. Read from the
    contract rather than named here, so the scaffold and the lint cannot
    disagree about a field's shape — which is the whole of #169."""
    from .contract import for_scheme
    return frozenset(f.name for f in for_scheme(scheme).fields if f.many)


def declared_fields(scheme) -> tuple[str, ...]:
    """Every field a scheme names, for `luria new` to accept as a flag and
    to refuse anything else by. The kinds are the config (ADR-036); so are
    the flags.

    A derived field is not among them (#216): its value comes off another
    field, so a flag for it would scaffold a line the lint rejects on the
    document's first read — the scaffold offering a guaranteed violation."""
    from .contract import for_scheme
    c = for_scheme(scheme)
    return tuple(f.name for f in c.fields if c.derivation(f.name) is None)


def _mint_tail(scheme) -> str:
    """A fresh temporary tail (ADR-049): the `tmp` sentinel plus five base-36
    characters — `tmp47fje` — so the code can never be read as a number AND
    reads as provisional to someone who has never met the convention. Random
    rather than derived, because the whole point is an identity that needs no
    coordination — checked against the tails already on disk, which is the
    only collision this process can see and the only one likely enough to
    matter (the space is 36⁵ per scheme)."""
    import secrets
    import string
    taken = scheme.temp_documents()
    while True:
        tail = "tmp" + "".join(
            secrets.choice(string.ascii_lowercase + string.digits)
            for _ in range(5))
        if tail not in taken:
            return tail


def new_scheme_doc(scheme, fields: dict[str, str]) -> Path:
    if scheme.allocate == "merge":
        # Merge-allocated schemes don't claim a number from a branch — that
        # claim is what collides (ADR-049). The code is temporary, and
        # `luria concretize` assigns the real number where merges serialize.
        stem = f"{scheme.prefix}-{_mint_tail(scheme)}"
        code = stem
        number = None
    else:
        number = max(scheme.documents(), default=0) + 1
        code = f"{scheme.prefix}-{number:03d}"
        stem = code
    today = dt.date.today().isoformat()

    template = scheme.dir / TEMPLATE_NAME
    if template.exists():
        text = template.read_text(encoding="utf-8")
        # The template speaks of itself as `<PREFIX>-NNN`; the copy is a real
        # document, so the code is filled in everywhere the reader would see
        # a placeholder — the body heading included.
        text = text.replace(f"{scheme.prefix}-NNN", code)
        text = re.sub(r"^date: .*$", f"date: '{today}'", text,
                      count=1, flags=re.MULTILINE)
    else:
        text = fallback(scheme, code, today, "Stated as the thing you did")

    plural = plural_fields(scheme)
    title = fields.pop("title", None)
    body = fields.pop("body", None)
    if title is not None:
        text = _sub_line(text, "title", title)
        # The heading is DERIVED from the title — the lint holds the two
        # equal — so it is rewritten by rule, whatever the form said there.
        # This used to replace `# CODE: <the form's title:>` and nothing
        # else, so a template whose title: and heading disagreed (strata-g's
        # did) scaffolded a document the lint rejected on first read (#301).
        text = re.sub(rf"^# {re.escape(code)}: .*$", f"# {code}: {title}",
                      text, count=1, flags=re.MULTILINE)
    if body is not None:
        text = replace_body(text, code, body)
    for field, value in fields.items():
        text = _sub_line(text, field, value, many=field in plural)
    # A prose field the caller did not fill still carries the form's own
    # words — "one-paragraph description of the decision" — which the lint
    # reports as the form's text, not the document's. Drop the value and keep
    # the comment above it, which is the instruction; an absent summary falls
    # back to the title until the author writes one.
    from .doc_refs import PROSE_KEYS
    for field in PROSE_KEYS:
        if field not in fields:
            text = _drop_field(text, field)

    # Identity written into the document, not left to the filename (#219).
    # Only for a scheme that allocates on filing: a merge-allocated one has
    # no number to write yet, and `luria concretize` puts it there when it
    # assigns one, which is the same moment it stops being a claim a branch
    # could collide on (ADR-049).
    if number is not None:
        text = write_number(text, number)

    path = scheme.dir / f"{stem}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    writes.write_text(path, text)
    return path


def replace_body(text: str, code: str, body: str) -> str:
    """Put `body` where the template's prose was: everything below the
    `# CODE: title` heading, which stays — it is derived from the title and
    the lint holds the two equal, so it is never the author's to write.

    A body that opens with its own level-one heading has it dropped for the
    same reason; a tool that hands over a whole document (strata-g's drop
    dialog shows one) would otherwise file two. With no heading in the text
    — a frontmatter-only scaffold — the body follows the frontmatter."""
    lines = body.replace("\r\n", "\n").strip("\n").split("\n")
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    prose = "\n".join(lines).strip("\n")
    heading = re.search(rf"^# {re.escape(code)}: .*$", text, flags=re.MULTILINE)
    if heading:
        head = text[:heading.end()]
    elif text.startswith("---\n") and (end := text.find("\n---\n", 3)) != -1:
        head = text[:end + 4]
    else:
        head = text.rstrip("\n")
    return head.rstrip("\n") + "\n\n" + prose + "\n"


def write_number(text: str, number: int) -> str:
    """Put `number: N` at the top of a document's frontmatter.

    First line, above the scaffold's comments: identity is the one field a
    reader should not have to hunt for, and `luria repair` writes it into
    existing documents at the same place, so a migrated record and a fresh
    one read alike. Text surgery rather than a YAML round-trip, for the
    reason `field_edit` gives — rewriting through a parser reflows the
    comments a scaffolded document is mostly made of."""
    line = f"number: {int(number)}\n"
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 3)
    head = text[4:end + 1] if end != -1 else ""
    if _NUMBER_LINE.search(head):
        return _NUMBER_LINE.sub(line, text, count=1)
    return text[:4] + line + text[4:]


def _frontmatter_head(text: str) -> str:
    """The frontmatter block's lines, or "" when there is none: a `number:` in
    the body is prose about identity, not a claim to one."""
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 3)
    return text[4:end + 1] if end != -1 else ""


def declares_number(text: str) -> bool:
    """Whether the frontmatter carries a `number:` line of any value."""
    return bool(_NUMBER_LINE.search(_frontmatter_head(text)))


def drop_number(text: str) -> str:
    """The document without its frontmatter `number:` line, if it has one."""
    if not declares_number(text):
        return text
    return _NUMBER_LINE.sub("", text, count=1)


def new_fragment(dir_name: str, name: str | None,
                 body: str | None = None) -> Path:
    """A fragment named for its filing moment, like a journal entry.

    It used to be named for the git branch — one fragment per contribution,
    addressed by where the contribution lived. That identity broke the first
    time a branch was restarted from the default branch after a squash merge:
    the same branch name filed a second contribution, `luria new changelog`
    reopened the *merged* fragment, and two PRs' entries muddled into one
    batch (#76). A timestamp is the identity the devlog already uses, and it
    cannot collide; flat rather than `yyyy/mm/dd/` nested, because the
    collector and the lint glob a fragment directory one level deep. Two
    fragments from one contribution is fine — they collect into the same
    dated batch. `--name` remains the explicit override, and an existing
    named fragment is reopened rather than duplicated."""
    frag_dir = current().root / dir_name
    if name:
        path = frag_dir / f"{name.removesuffix('.md')}.md"
        if path.exists():
            return path
    else:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        path = frag_dir / f"{stamp}.md"
    template = frag_dir / TEMPLATE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    if body is not None:
        text = body.strip("\n") + "\n"
    elif template.exists():
        text = template.read_text(encoding="utf-8")
    else:
        text = "### Changed\n\n- \n"
    writes.write_text(path, text)
    return path


MIGRATION_TEMPLATE = '''\
# A migration spec (ADR-040): the executable plan and the audit trail in one
# artifact. `luria migrate {number} --dry-run` prints what it would do.
# This file is deliberately never swept — its mapping remembers the old
# spellings, which is its job. Uncomment the operations you need.
title: "{title}"
issue: ""

# operations:
# - op: rename_scheme
#   from: OLD
#   to: NEW
#   output: docs/new-view.md        # optional: the rendered view moves too
#   remotes: []                     # remotes that mirror THIS project
#   configs: []                     # extra config files carrying the scheme
# - op: move_doc
#   doc: OLD-4
#   to: NEW                         # auto-numbered in the target scheme
#   strategy: supersede             # optional: copy + tombstone, no rewrite
# - op: promote_vocabulary
#   vocabulary: area                # a vocabulary that needs to say more
#   to: AREA                        # the scheme it becomes, one doc per value
#   dir: record/areas.d             # optional: defaults from the prefix
#   output: docs/areas              # optional: defaults from the prefix
'''


def new_migration(fields: dict[str, str], name: str | None) -> Path:
    """The next spec in record/migrations.d/ — numbered like a document,
    because execution order is information (a move can depend on a rename)."""
    from .migrate import MIGRATIONS_DIR
    mig_dir = current().root / MIGRATIONS_DIR
    taken = [int(m.group(1)) for p in
             (mig_dir.glob("*.yaml") if mig_dir.exists() else [])
             if (m := re.match(r"(\d{4})-", p.name))]
    number = f"{max(taken, default=0) + 1:04d}"
    title = fields.get("title") or "What moves, and why"
    slug = name or re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    path = mig_dir / f"{number}-{slug}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    writes.write_text(path, MIGRATION_TEMPLATE.format(number=number, title=title))
    return path


def new_entry(kind: str | None, fields: dict[str, str],
              name: str | None) -> Path:
    available = kinds()
    kind = kind or default_kind()
    if kind is None or kind not in available:
        raise SystemExit(
            f"luria new: unknown kind {kind!r} — this project scaffolds: "
            + ", ".join(sorted(available)))
    what, target = available[kind]
    if what == "scheme":
        return new_scheme_doc(target, dict(fields))
    if what == "fragment":
        return new_fragment(target, name, fields.get("body"))
    if what == "migration":
        return new_migration(dict(fields), name)
    title = fields.get("title") or "A sentence-shaped title"
    return journal_mod.new(target, title, dt.datetime.now(),
                           body=fields.get("body"))


UNIVERSAL = ("title", "status", "summary", "tags", "body")

# What each non-scheme kind reads from its flags, as `new_entry` uses them:
# a journal entry takes a title and prose, a fragment only prose, a
# migration spec only a title. `--name` names the file of the two that are
# named rather than numbered or stamped.
KIND_FIELDS = {"journal": ("title", "body"), "fragment": ("body", "name"),
               "migration": ("title", "name")}


def accepted_flags(what: str, target) -> tuple[str, ...]:
    """The flags one kind takes, in the order help lists them. A scheme's
    are the universal five plus its declared fields, once each — a scheme
    declaring `status` and `tags` does not take them twice."""
    if what == "scheme":
        return tuple(dict.fromkeys((*UNIVERSAL, *declared_fields(target))))
    return KIND_FIELDS[what]


def help_text(kind: str | None = None) -> str:
    """`luria new --help`: the kinds this record scaffolds and each one's
    flags, read from luria.yaml like the dispatch (ADR-036) — the one place
    a reader learns that a kind is the lowercased prefix (#328). With a
    kind, that kind alone."""
    from .migrate import MIGRATIONS_DIR
    available = kinds()
    default = default_kind()
    if kind is not None and kind.lower() not in available:
        raise SystemExit(
            f"luria new: unknown kind {kind!r} — this project scaffolds: "
            + ", ".join(sorted(available)))
    names = [kind.lower()] if kind else sorted(available)
    cfg = current()
    rows = []
    for name in names:
        what, target = available[name]
        where = {"scheme": lambda t: f"a scheme, filed in {cfg.rel(t.dir)}/",
                 "fragment": lambda t: f"a fragment directory, {t}/",
                 "journal": lambda t: f"a journal, filed in {cfg.rel(t.dir)}/",
                 "migration": lambda t: f"a migration spec, {MIGRATIONS_DIR}/",
                 }[what](target)
        note = " (the default)" if name == default else ""
        flags = " ".join(f"--{f}" for f in accepted_flags(what, target))
        rows.append(f"  {name:<12} {where}{note}\n  {'':<12} {flags}")
    lead = (run.__doc__ or "").strip().split("\n\n")[0]
    return ("usage: luria new [KIND] [--FIELD VALUE ...]\n"
            "       luria new [KIND] --draft FILE\n\n"
            f"{' '.join(lead.split())}\n\n"
            "Kinds this record scaffolds (from luria.yaml), and the flags "
            "each takes:\n" + "\n".join(rows) + "\n\n"
            "--draft FILE files what a tool wrote instead of taking flags.\n")

# What a drafts file carries that is not a field of the document: the
# canvas's own bookkeeping (strata-g's exporter writes these beside the
# fields, and nothing here has an opinion about them).
DRAFT_BOOKKEEPING = frozenset({"id", "scheme", "command", "unresolved"})


def _read_drafts(path: str) -> list[dict]:
    # unresolved-ok-block: ADR-tmpiylaq — another project's code, quoted to
    # show what its export writes; this record neither mints nor resolves it.
    """The draft objects in a JSON file: one object, or a `luria-drafts`
    document (`{"format": "luria-drafts", "drafts": [...]}`) as strata-g's
    *Record — luria drafts* export writes it (SG-ADR-tmpiylaq there)."""
    import json
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"luria new: no such file {path!r}")
    except json.JSONDecodeError as e:
        sys.exit(f"luria new: {path} is not JSON ({e})")
    if isinstance(data, dict) and isinstance(data.get("drafts"), list):
        drafts = data["drafts"]
    elif isinstance(data, dict):
        drafts = [data]
    else:
        sys.exit(f"luria new: {path} holds neither a draft object nor a "
                 "luria-drafts document")
    bad = [d for d in drafts if not isinstance(d, dict)]
    if bad:
        sys.exit(f"luria new: {path}: every draft must be an object")
    return drafts


def _file_drafts(kind: str | None, drafts: list[dict], where: str) -> None:
    """File every draft, each into the kind its `scheme` names (or KIND when
    it names none), with the same field validation the flags get: a key the
    scheme has no opinion about is refused by name, not written."""
    kinds_ = kinds()
    for i, draft in enumerate(drafts, 1):
        scheme = str(draft.get("scheme") or "").lower()
        resolved = scheme or (kind or default_kind() or "").lower()
        if kind and scheme and scheme != kind.lower():
            sys.exit(f"luria new {kind}: draft {i} in {where} is for "
                     f"{scheme!r}, not {kind!r}")
        entry = kinds_.get(resolved)
        if entry is None:
            sys.exit(f"luria new: draft {i} in {where} names kind "
                     f"{resolved!r} — this project scaffolds: "
                     + ", ".join(sorted(kinds_)))
        accepted = declared_fields(entry[1]) if entry[0] == "scheme" else ()
        fields = {k: v for k, v in draft.items()
                  if k not in DRAFT_BOOKKEEPING and v not in (None, "", [], ())}
        unknown = [f for f in fields if f not in UNIVERSAL and f not in accepted]
        if unknown:
            known = ", ".join(f for f in (*UNIVERSAL, *accepted))
            sys.exit(f"luria new {resolved}: draft {i} in {where} carries "
                     f"{', '.join(repr(u) for u in unknown)} "
                     f"(this kind accepts: {known})")
        print(current().rel(new_entry(resolved, fields, None)))


def run(kind: str = None, title: str = None, status: str = None,
        summary: str = None, tags: str = None,
        body: str = None, name: str = None, draft: str = None,
        **declared) -> None:
    """Scaffold an entry and print its path. KIND defaults to the journal;
    the other kinds come from luria.yaml (scheme prefixes, fragment dirs).
    Field flags are optional — content belongs to your editor.

    `--body TEXT` is the prose: it replaces the template's body below the
    `# CODE: title` heading (a scheme document), the placeholder paragraph
    (a journal entry) or the whole fragment. The heading stays luria's — it
    is derived from the title — so a body that opens with one has it
    dropped rather than doubled. Multi-line text is ordinary shell quoting;
    a tool that authored the prose elsewhere hands it over in a draft's
    `body` key instead.

    Beyond the five universal flags, a scheme's own declared fields are
    accepted by name — `--source LIT-134,LIT-140` where the SOTA scheme
    declares `source` — and written in the shape the contract declares
    (#169). An undeclared flag is refused rather than written, because a key
    the scheme has no opinion about, scaffolded by a script, is exactly the
    kind of thing nothing downstream would ever report.

    `--draft FILE` files what a tool wrote instead: one draft object, or a
    `luria-drafts` document holding several, each with the fields above and
    the kind its `scheme` names (#301). Same validation, one path printed
    per draft.

    `--help` (or `-h`) lists the kinds and each kind's flags; with a KIND,
    that kind's alone."""
    # The declared-field catch-all would otherwise take `--help` as a field
    # named 'help' and refuse it (#328).
    if declared.pop("help", False) or declared.pop("h", False):
        print(help_text(kind), end="")
        return
    if draft is not None:
        if any(v for v in (title, status, summary, tags, name)) or declared:
            sys.exit("luria new: --draft takes its fields from the file; "
                     "no other field flag applies")
        _file_drafts(kind, _read_drafts(draft), draft)
        return
    fields = {k: v for k, v in
              [("title", title), ("status", status),
               ("summary", summary), ("tags", tags), ("body", body)] if v}
    # Every flag is checked against what the kind takes — the list `--help`
    # prints. A scheme's declared fields were always refused when unknown;
    # a flag the kind would simply ignore (`luria new changelog --title`)
    # was accepted and dropped, with nothing saying so (#330).
    resolved = (kind or default_kind() or "").lower()
    entry = kinds().get(resolved)
    if entry is not None:
        accepted = accepted_flags(*entry)
        given = [*fields, *(["name"] if name else []),
                 *(k for k, v in declared.items() if v)]
        unknown = [f for f in given if f not in accepted]
        if unknown:
            known = ", ".join(f"--{f}" for f in accepted)
            sys.exit(f"luria new {resolved}: no such flag "
                     f"{', '.join(f'--{u}' for u in unknown)} "
                     f"(this kind accepts: {known})")
    fields.update({k: v for k, v in declared.items() if v})
    print(current().rel(new_entry(kind, fields, name)))


if __name__ == "__main__":
    import fire
    fire.Fire(run)
