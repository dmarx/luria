#!/usr/bin/env python3
"""`luria new [kind]` — scaffold an entry anywhere the record takes one (#42).

    luria new                  # a journal entry (the devlog), at its timestamp
    luria new adr              # the next free decision number, from _template.md
    luria new dp               # the next free principle number
    luria new changelog        # a fragment named after the current branch

Prints the created path and nothing else. The identity fields a machine can
compute — filename, number, timestamp, `date:` — are computed; every other
field stays the template's placeholder, because a fragment is authored in a
markdown-aware editor, not assembled on a command line (ADR-036). A tool
driving the CLI can still set fields inline (`--title`, `--status`,
`--summary`, `--tags`); a human never has to.

**The kinds are the config.** Every journal, scheme and fragment directory in
`luria.toml` is a kind, so a project that adds a scheme gets its scaffold for
free — nothing here spells "adr". One kind is built in rather than
configured: `luria new migration` scaffolds a migration spec (ADR-040),
because migrations belong to the machinery, not to any one project's layout.
"""

from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

from . import journal as journal_mod
from .config import current

TEMPLATE_NAME = "_template.md"

# The shape written when a scheme has no _template.md of its own — enough to
# pass the lint (status, title, tag, date, agreeing heading) and nothing else.
FALLBACK = """---
status: Proposed
title: '{title}'
tags:
- record
date: '{date}'
---

# {code}: {title}

Why this needed deciding, what was decided, and what was rejected.
"""


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


def _sub_line(text: str, field: str, value: str) -> str:
    """Replace a single-line frontmatter field, or a block one (`>-` /
    list) through its indented continuation lines."""
    pattern = re.compile(rf"^{field}:.*(?:\n(?:  |- ).*)*", re.MULTILINE)
    if field == "tags":
        replacement = "tags:\n" + "\n".join(
            f"- {t.strip()}" for t in value.split(",") if t.strip())
    elif field == "summary":
        replacement = f"summary: >-\n  {value}"
    else:
        replacement = f"{field}: {value!r}"
    return pattern.sub(replacement, text, count=1)


def new_scheme_doc(scheme, fields: dict[str, str]) -> Path:
    numbers = scheme.documents()
    number = max(numbers, default=0) + 1
    code = f"{scheme.prefix}-{number:03d}"
    today = dt.date.today().isoformat()

    template = scheme.dir / TEMPLATE_NAME
    if template.exists():
        text = template.read_text()
        # The template speaks of itself as `<PREFIX>-NNN`; the copy is a real
        # document, so the code is filled in everywhere the reader would see
        # a placeholder — the body heading included.
        text = text.replace(f"{scheme.prefix}-NNN", code)
        text = re.sub(r"^date: .*$", f"date: '{today}'", text,
                      count=1, flags=re.MULTILINE)
    else:
        text = FALLBACK.format(code=code, date=today,
                               title="Stated as the thing you did")

    title = fields.pop("title", None)
    if title is not None:
        old_title = None
        m = re.search(r"^title: (.*)$", text, flags=re.MULTILINE)
        if m:
            old_title = m.group(1).strip().strip("'\"")
        text = _sub_line(text, "title", title)
        if old_title:
            text = text.replace(f"# {code}: {old_title}", f"# {code}: {title}")
    for field, value in fields.items():
        text = _sub_line(text, field, value)

    path = scheme.dir / f"{code}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def branch_slug() -> str | None:
    """The current branch, as a fragment filename — the ADR-002 convention
    of one fragment per contribution, named after its branch."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=current().root,
            capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", out.lower()).strip("-")
    return slug or None


def new_fragment(dir_name: str, name: str | None) -> Path:
    slug = name or branch_slug()
    if not slug:
        raise SystemExit(f"luria new: {Path(dir_name).name} needs a filename "
                         "and no git branch answered — pass --name <slug>")
    frag_dir = current().root / dir_name
    path = frag_dir / f"{slug.removesuffix('.md')}.md"
    if path.exists():
        # One fragment per contribution (ADR-002): the second ask on a branch
        # is the same fragment, so hand back where it already is.
        return path
    template = frag_dir / TEMPLATE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(template.read_text() if template.exists()
                    else "### Changed\n\n- \n")
    return path


MIGRATION_TEMPLATE = '''\
# A migration spec (ADR-040): the executable plan and the audit trail in one
# artifact. `luria migrate {number} --dry-run` prints what it would do.
# This file is deliberately never swept — its mapping remembers the old
# spellings, which is its job.
title = "{title}"
issue = ""

# [[operations]]
# op = "rename_scheme"
# from = "OLD"
# to = "NEW"
# output = "docs/new-view.md"       # optional: the rendered view moves too
# remotes = []                      # remotes that mirror THIS project
# configs = []                      # extra config files carrying the scheme

# [[operations]]
# op = "move_doc"
# doc = "OLD-4"
# to = "NEW"                        # auto-numbered in the target scheme
# strategy = "supersede"            # optional: copy + tombstone, no rewrite
'''


def new_migration(fields: dict[str, str], name: str | None) -> Path:
    """The next spec in record/migrations.d/ — numbered like a document,
    because execution order is information (a move can depend on a rename)."""
    from .migrate import MIGRATIONS_DIR
    mig_dir = current().root / MIGRATIONS_DIR
    taken = [int(m.group(1)) for p in
             (mig_dir.glob("*.toml") if mig_dir.exists() else [])
             if (m := re.match(r"(\d{4})-", p.name))]
    number = f"{max(taken, default=0) + 1:04d}"
    title = fields.get("title") or "What moves, and why"
    slug = name or re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    path = mig_dir / f"{number}-{slug}.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(MIGRATION_TEMPLATE.format(number=number, title=title))
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
        return new_fragment(target, name)
    if what == "migration":
        return new_migration(dict(fields), name)
    title = fields.get("title") or "A sentence-shaped title"
    return journal_mod.new(target, title, dt.datetime.now())


def run(kind: str = None, title: str = None, status: str = None,
        summary: str = None, tags: str = None, name: str = None) -> None:
    """Scaffold an entry and print its path. KIND defaults to the journal;
    the other kinds come from luria.toml (scheme prefixes, fragment dirs).
    Field flags are optional — content belongs to your editor."""
    fields = {k: v for k, v in
              [("title", title), ("status", status),
               ("summary", summary), ("tags", tags)] if v}
    print(current().rel(new_entry(kind, fields, name)))


if __name__ == "__main__":
    import fire
    fire.Fire(run)
