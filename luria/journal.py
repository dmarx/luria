#!/usr/bin/env python3
"""A journal: dated entries that persist, rendered into books.

This is a library since `luria new` became the scaffold for every entry kind
(ADR-036): `luria new` files a journal entry, `luria index` renders the
books. The standalone module still runs for the odd interactive look:

    python -m luria.journal                  # what is filed, which books

The changelog and the devlog look alike and are not. A changelog entry is a
*claim about a release*, collected and consumed. A journal entry is a **dated
observation** — it was true when written and stays true, so it should no more be
deleted than a decision should (ADR-020).

So a journal is fragments that persist, plus a generated view — the same
collected-vs-generated split [ADR-012](../record/decisions.d/ADR-012.md) draws, and
the reason it matters here is that nothing is ever *appended to*. Two branches
each add a file nobody else writes; there is no shared insertion point to
conflict at, and no collection step whose absence would go unnoticed.

Identity is a timestamp
-----------------------
An entry has no number to assign, so its identity is when it was written:

    devlog.d/2026/08/03/141530.md      created: '2026-08-03T14:15:30'

The path is derived from `created` and the lint checks they agree. Ordering is
then a pure function of the tree — no `git log` call, and nothing a rebase can
change, which is what the commit-time ordering this replaces could not promise.

Books
-----
One file per period, because a single chronological document grows without
bound and the partition is already sitting there in the path. Granularity is
configured, not assumed: the right book size depends on how fast a project
writes, and that is a measurement rather than a guess.

Each book carries a generated table of contents, which is what the entry titles
buy — a listing of what happened, in the file where it happened, that cannot go
stale.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .adr_index import parse_frontmatter
from .config import Journal, current

# `2026/08/03/141530.md` — the path a `created` timestamp implies.
PATH_RE = re.compile(r"(\d{4})/(\d{2})/(\d{2})/(\d{2})(\d{2})(\d{2})\.md$")
SLUG_RE = re.compile(r"[^a-z0-9]+")


def parse_created(raw) -> dt.datetime | None:
    """`created:` as a datetime. YAML may hand back a date, a datetime or a
    string depending on quoting, so all three are accepted rather than making
    the author remember which one the parser prefers."""
    if isinstance(raw, dt.datetime):
        return raw
    if isinstance(raw, dt.date):
        return dt.datetime(raw.year, raw.month, raw.day)
    try:
        return dt.datetime.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return None


def path_for(journal: Journal, created: dt.datetime) -> Path:
    return journal.dir / created.strftime("%Y/%m/%d/%H%M%S.md")


def created_from_path(path: Path) -> dt.datetime | None:
    m = PATH_RE.search(path.as_posix())
    return dt.datetime(*(int(g) for g in m.groups())) if m else None


@dataclass(frozen=True)
class Entry:
    created: dt.datetime
    title: str
    tags: tuple[str, ...]
    body: str
    path: Path

    @property
    def anchor(self) -> str:
        """Keyed to the timestamp, not the title — a title can be corrected,
        and a heading-derived anchor would break every link to it silently."""
        return self.created.strftime("%Y%m%d%H%M%S")


def read(path: Path) -> Entry | None:
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    created = parse_created(meta.get("created")) or created_from_path(path)
    if created is None:
        return None
    return Entry(created, str(meta.get("title") or "").strip(),
                 tuple(str(t).strip() for t in (meta.get("tags") or [])),
                 body.strip(), path)


def entries(journal: Journal) -> list[Entry]:
    """Every filed entry, oldest first. Sorted by the timestamp, so the order
    is a property of the record rather than of how the branches landed."""
    found = [e for p in sorted(journal.dir.rglob("*.md"))
             if p.name != "_template.md" and (e := read(p)) is not None]
    return sorted(found, key=lambda e: (e.created, e.path.as_posix()))


_CREATED_LINE_RE = re.compile(r"^created:.*$", re.MULTILINE)


def populate_created(journal: Journal) -> list[Path]:
    """Write a missing `created:` into entries whose path already says it (#33).

    The path is derived from `created:` (ADR-020), so when the field is empty
    the path is the one witness left — populating from it writes down what the
    tree already asserts rather than inventing anything. An entry whose field
    and path *disagree* is left alone: two witnesses in conflict is a
    judgement for a human, not a mechanical fix.

    Runs from `luria repair`, which the generation job commits onto the
    branch that filed the entry (ADR-068)."""
    fixed: list[Path] = []
    for path in sorted(journal.dir.rglob("*.md")):
        if path.name == "_template.md":
            continue
        text = path.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(text)
        if parse_created(meta.get("created")) is not None:
            continue
        created = created_from_path(path)
        if created is None:
            continue
        line = f"created: '{created.isoformat(timespec='seconds')}'"
        if meta and "created" in meta:
            # The key is there but holds nothing parseable — refill it.
            new_text = _CREATED_LINE_RE.sub(line, text, count=1)
        elif text.startswith("---\n"):
            head, rest = text.split("\n", 1)
            new_text = f"{head}\n{line}\n{rest}"
        else:
            new_text = f"---\n{line}\n---\n\n{text}"
        path.write_text(new_text, encoding="utf-8")
        fixed.append(path)
    return fixed


# ── Books ────────────────────────────────────────────────────────────────

FORMATS = {"year": "%Y", "month": "%Y-%m", "day": "%Y-%m-%d"}
LABELS = {"year": "%Y", "month": "%B %Y", "day": "%-d %B %Y"}


def book_key(journal: Journal, created: dt.datetime) -> str:
    return created.strftime(FORMATS[journal.granularity])


def books(journal: Journal) -> dict[str, list[Entry]]:
    out: dict[str, list[Entry]] = {}
    for entry in entries(journal):
        out.setdefault(book_key(journal, entry.created), []).append(entry)
    return out


def render_book(journal: Journal, key: str, filed: list[Entry]) -> str:
    label = filed[0].created.strftime(LABELS[journal.granularity]).lstrip("0")
    lines = [f"<!-- GENERATED by `luria index` from {journal.rel_dir}/ — "
             "edit the entries, not this file. -->", "",
             f"# {journal.title} — {label}", "",
             f"{len(filed)} entr{'y' if len(filed) == 1 else 'ies'}. "
             f"[All books](README.md).", "", "## Contents", ""]
    for entry in filed:
        stamp = entry.created.strftime("%d %b %H:%M").lstrip("0")
        lines.append(f"- [{stamp} — {entry.title}](#{entry.anchor})")
    lines.append("")
    for entry in filed:
        lines += ["---", "", f'<a name="{entry.anchor}"></a>', "",
                  f"## {entry.title}", "",
                  f"*{entry.created.strftime('%Y-%m-%d %H:%M:%S')}"
                  + (" · " + " · ".join(entry.tags) if entry.tags else "")
                  + "*", "", entry.body, ""]
    return "\n".join(lines)


def render_index(journal: Journal, grouped: dict[str, list[Entry]]) -> str:
    """The journal's front page: the current book's contents inline, then the
    shelf. Hot on top, cold below — without this, the newest writing sits
    behind two clicks and the whole journal reads as an archive (ADR-021)."""
    lines = [f"<!-- GENERATED by `luria index` from {journal.rel_dir}/ — "
             "edit the entries, not this file. -->", "",
             f"# {journal.title}", ""]
    if journal.blurb:
        lines += [journal.blurb, ""]
    if not grouped:
        lines += ["Nothing filed yet.", ""]
        return "\n".join(lines)

    latest = max(grouped)
    label = grouped[latest][0].created.strftime(
        LABELS[journal.granularity]).lstrip("0")
    lines += [f"## Currently — [{label}]({latest}.md)", ""]
    for entry in reversed(grouped[latest]):
        stamp = entry.created.strftime("%d %b %H:%M").lstrip("0")
        lines.append(f"- [{stamp} — {entry.title}]({latest}.md#{entry.anchor})")
    lines.append("")

    total = sum(len(v) for v in grouped.values())
    lines += [f"## All books", "",
              f"{total} entr{'y' if total == 1 else 'ies'} across "
              f"{len(grouped)} book{'' if len(grouped) == 1 else 's'}, "
              "newest first.",
              "", "| Book | Entries | First | Last |", "|---|--:|---|---|"]
    for key in sorted(grouped, reverse=True):
        filed = grouped[key]
        lines.append(
            f"| [{key}]({key}.md) | {len(filed)} "
            f"| {filed[0].created:%Y-%m-%d} | {filed[-1].created:%Y-%m-%d} |")
    lines.append("")
    return "\n".join(lines)


def outputs_for(journal: Journal) -> dict[Path, str]:
    """One journal's books plus its index — the unit the parallel renderer
    runs (ADR-026). A configured-but-unused journal renders nothing: the
    default config names one, so emitting an empty index would put a
    `docs/devlog/` into every project that never files an entry."""
    if not journal.dir.exists():
        return {}
    grouped = books(journal)
    out = {journal.output / "README.md": render_index(journal, grouped)}
    for key, filed in grouped.items():
        out[journal.output / f"{key}.md"] = render_book(journal, key, filed)
    return out


def outputs() -> dict[Path, str]:
    """Every book, plus each journal's index. One place, so the staleness
    check covers a journal the moment it is configured."""
    out: dict[Path, str] = {}
    for journal in current().journals.values():
        out.update(outputs_for(journal))
    return out


# ── Filing an entry ──────────────────────────────────────────────────────


def new(journal: Journal, title: str, now: dt.datetime) -> Path:
    """Create an entry, stepping a second forward on collision.

    Not a probability argument — the filesystem already knows. A same-second
    collision is possible when a tool files several at once, and "unlikely" is
    a worse guarantee than "checked" when checking is a `path.exists()`."""
    while (path := path_for(journal, now)).exists():
        now += dt.timedelta(seconds=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f"title: {title!r}\n"
        f"created: '{now.isoformat(timespec='seconds')}'\n"
        "tags: []\n"
        "---\n\n"
        "Write the entry here: what problem was solved, what the fix was, and\n"
        "what was found along the way — the failed approaches and the traps the\n"
        "next person would otherwise rediscover.\n", encoding="utf-8")
    return path


# ── CLI ──────────────────────────────────────────────────────────────────


def run(journal: str = None) -> None:
    """What is filed, and which books it renders to (a status listing —
    `luria new` files entries)."""
    cfg = current()
    if not cfg.journals:
        # No silent refusal: say what would make this command do something.
        print("luria journal: none configured. Add one to luria.toml:\n\n"
              "  [luria.journals.devlog]\n  dir = \"devlog.d\"\n"
              "  output = \"docs/devlog\"\n", file=sys.stderr)
        return

    name = journal or next(iter(cfg.journals))
    if name not in cfg.journals:
        print(f"luria journal: unknown journal {name!r}; configured: "
              f"{', '.join(cfg.journals)}", file=sys.stderr)
        raise SystemExit(2)
    journal_cfg = cfg.journals[name]

    grouped = books(journal_cfg)
    total = sum(len(v) for v in grouped.values())
    period = {"year": "yearly", "month": "monthly", "day": "daily"}[
        journal_cfg.granularity]
    print(f"{name}: {total} entr{'y' if total == 1 else 'ies'} in "
          f"{len(grouped)} {period} book{'' if len(grouped) == 1 else 's'} → "
          f"{cfg.rel(journal_cfg.output)}/")
    for key in sorted(grouped, reverse=True):
        filed = grouped[key]
        print(f"  {key}.md  {len(filed):>3} entr{'y' if len(filed) == 1 else 'ies'}")


if __name__ == "__main__":
    import fire
    fire.Fire(run)
