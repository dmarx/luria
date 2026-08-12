#!/usr/bin/env python3
"""`luria new [kind]` — scaffold an entry anywhere the record takes one (#42).

    luria new                  # a journal entry (the devlog), at its timestamp
    luria new adr              # the next free decision number, from _template.md
    luria new dp               # the next free principle number
    luria new changelog        # a fragment named for its filing moment

Prints the created path and nothing else. The identity fields a machine can
compute — filename, number, timestamp, `date:` — are computed; every other
field stays the template's placeholder, because a fragment is authored in a
markdown-aware editor, not assembled on a command line (ADR-036). A tool
driving the CLI can still set fields inline (`--title`, `--status`,
`--summary`, `--tags`); a human never has to.

**The kinds are the config.** Every journal, scheme and fragment directory in
`luria.toml` is a kind, so a project that adds a scheme gets its scaffold for
free — nothing here spells "adr".
"""

from __future__ import annotations

import datetime as dt
import re
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
    else:
        number = max(scheme.documents(), default=0) + 1
        code = f"{scheme.prefix}-{number:03d}"
        stem = code
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

    path = scheme.dir / f"{stem}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def new_fragment(dir_name: str, name: str | None) -> Path:
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
    path.write_text(template.read_text() if template.exists()
                    else "### Changed\n\n- \n")
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
