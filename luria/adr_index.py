#!/usr/bin/env python3
"""Build docs/decisions/README.md and the per-tag pages from the ADRs (ADR-158, #551).

The ADR index used to be hand-maintained: every ADR-bearing PR appended a row to
the same table and a link to the same category list. That makes it the
shared-file lock design-principles #13 names — three ADRs authored in one session
all edited the same region, and a cherry-pick between two of them conflicted. It
also *drifts*, because the row duplicates data the ADR already owns: at migration
time 45 of 155 rows disagreed with their own ADR's status, and two ADRs were
listed under a category their header didn't claim.

So the index is generated. Each ADR carries YAML frontmatter — status, tags,
date, issue, summary — and this renders:

  docs/decisions/README.md        the stub's prose + category lists + the table
  docs/decisions/tags/<tag>.md    one page per tag, listing its ADRs

Adding an ADR means adding ONE file. Adding a *tag* means using it in an ADR;
`tags.yaml` only supplies ordering and a blurb, so an unlisted tag still renders.

    scripts/ci/build_adr_index.py            # write the index and tag pages
    scripts/ci/build_adr_index.py --check    # exit 1 if anything would change

`--check` is what makes idempotency enforceable: `make lint-docs` runs it, so a
stale index is a lint failure rather than a silent divergence.

The stub/placeholder shape is borrowed from dmarx/bench-warmers, which solved
the same problem for a brainstorming repo: prose lives in a `.stub`, the
generator substitutes `{placeholders}`, and tags get their own generated pages.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from .config import current

TITLE_RE = re.compile(r"^#\s*ADR-\d+\s*(?::|—|-)\s*")
NUM_RE = re.compile(r"^adr-(\d+)")
TABLE_HEAD = "| # | Title | Status |\n|---|---|---|\n"

# Used when a project has no `README.stub`. The stub exists so prose lives in
# markdown rather than in this generator; not having written one yet shouldn't
# stop the index from building.
DEFAULT_STUB = """# Architecture decision records

<!-- GENERATED below this line by `luria index` — edit README.stub instead. -->

{categories}

{table}
"""

# A markdown link with a *relative* target: not an anchor, not root-relative,
# not a URL scheme. Those are the only ones a change of output directory moves.
RELATIVE_LINK_RE = re.compile(r"(?<=\]\()(?![#/]|[A-Za-z][A-Za-z0-9+.-]*:)([^)\s]+)")


def rebase_links(text: str, prefix: str) -> str:
    """Rewrite relative link targets in `text` for output `prefix` levels away.

    Summaries are authored relative to `docs/decisions/` — the same base as the
    ADR body they were lifted from — and this index renders them both there
    (`README.md`, prefix "") and one level down (`tags/<tag>.md`, prefix "../").
    Owning the rendering is what lets a summary carry links at all: without this,
    no single relative target could be correct in both (ADR-187)."""
    if not prefix:
        return text
    return RELATIVE_LINK_RE.sub(lambda m: prefix + m.group(1), text)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split leading `---` YAML frontmatter from the body. Missing frontmatter
    yields an empty dict so a half-migrated tree still renders — lint reports
    the omission rather than the build crashing on it."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 3)
    if end == -1:
        return {}, text
    return yaml.safe_load(text[4 : end + 1]) or {}, text[end + 5 :]


class Adr:
    def __init__(self, path: Path):
        self.path = path
        self.number = int(NUM_RE.match(path.name).group(1))
        self.meta, body = parse_frontmatter(path.read_text())
        first = next((ln for ln in body.splitlines() if ln.startswith("#")), "")
        self.title = TITLE_RE.sub("", first).strip()

    @property
    def status(self) -> str:
        return str(self.meta.get("status", "")).strip()

    @property
    def tags(self) -> list[str]:
        return [str(t).strip().lower() for t in (self.meta.get("tags") or [])]

    def cell(self, prefix: str = "") -> str:
        """The table's middle column: the summary when there is one, else the
        title. A row has always been one blob, not a title plus a description —
        keeping that shape is what made the migration byte-identical.

        A summary may carry relative links, written — like the ADR's body —
        relative to `docs/decisions/`. `prefix` rebases them for output that
        renders somewhere else (ADR-187); it is the same prefix the row's own
        ADR link already took."""
        return rebase_links(str(self.meta.get("summary") or self.title).strip(), prefix)

    def row(self, prefix: str = "") -> str:
        # Every rendered field is rebased, not just the ADR's own link: a
        # "Superseded — by [ADR-100](…)" note is prose too, and its link was
        # silently broken on the tag pages (four of them) until this existed.
        return (f"| [ADR-{self.number:03d}]({prefix}{self.path.name}) "
                f"| {self.cell(prefix)} | {rebase_links(self.status, prefix)} |")


def load_adrs() -> list[Adr]:
    return sorted((Adr(p) for p in current().decisions.glob("adr-*.md")),
                  key=lambda a: a.number)


def tag_order(adrs: list[Adr]) -> list[tuple[str, dict]]:
    """Declared tags first, in tags.yaml order; then any undeclared tag an ADR
    actually uses, alphabetically. Using a new tag must never require a code
    change — that's the whole point of pushing categories down onto the ADRs."""
    tags_file = current().tags_yaml
    declared = yaml.safe_load(tags_file.read_text()) if tags_file.exists() else {}
    declared = declared or {}
    used = {t for a in adrs for t in a.tags}
    ordered = [(t, declared[t] or {}) for t in declared if t in used]
    ordered += [(t, {}) for t in sorted(used - set(declared))]
    return ordered


def render_categories(adrs: list[Adr], tags: list[tuple[str, dict]]) -> str:
    blocks = []
    for tag, meta in tags:
        listed = [a for a in adrs if tag in a.tags]
        label = meta.get("label", tag.title())
        blurb = f" — {meta['blurb']}" if meta.get("blurb") else ""
        links = " · ".join(f"[{a.number:03d}]({a.path.name})" for a in listed)
        blocks.append(f"**[{label}](tags/{tag}.md)** ({len(listed)}){blurb}:\n{links}")
    return "\n\n".join(blocks)


def render_index(adrs: list[Adr], tags: list[tuple[str, dict]]) -> str:
    table = TABLE_HEAD + "\n".join(a.row() for a in adrs) + "\n"
    stub = current().stub
    prose = stub.read_text() if stub.exists() else DEFAULT_STUB
    return (prose.replace("{categories}", render_categories(adrs, tags))
                 .replace("{table}", table))


def render_tag_page(tag: str, meta: dict, adrs: list[Adr]) -> str:
    label = meta.get("label", tag.title())
    listed = [a for a in adrs if tag in a.tags]
    blurb = f"\n{meta['blurb'].capitalize()}.\n" if meta.get("blurb") else ""
    return (
        f"<!-- GENERATED by scripts/ci/build_adr_index.py — do not edit. -->\n\n"
        f"# ADRs tagged `{tag}`\n"
        f"{blurb}\n"
        f"{len(listed)} of {len(adrs)} decisions. Back to the [full index](../README.md).\n\n"
        + TABLE_HEAD
        + "\n".join(a.row(prefix="../") for a in listed)
        + "\n"
    )


def outputs() -> dict[Path, str]:
    adrs = load_adrs()
    tags = tag_order(adrs)
    cfg = current()
    out = {cfg.index: render_index(adrs, tags)}
    for tag, meta in tags:
        out[cfg.tag_dir / f"{tag}.md"] = render_tag_page(tag, meta, adrs)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 if anything is stale")
    args = ap.parse_args()

    rendered = outputs()
    if args.check:
        stale = [p for p, text in rendered.items()
                 if not p.exists() or p.read_text() != text]
        # A tag page whose tag no longer exists is stale too.
        stale += [p for p in current().tag_dir.glob("*.md") if p not in rendered]
        if stale:
            print("stale (run `luria index`):", file=sys.stderr)
            for p in sorted(stale):
                print(f"  {current().rel(p)}", file=sys.stderr)
            return 1
        print("ADR index: current")
        return 0

    cfg = current()
    cfg.tag_dir.mkdir(parents=True, exist_ok=True)
    for p in cfg.tag_dir.glob("*.md"):
        if p not in rendered:
            p.unlink()
    for p, text in rendered.items():
        p.write_text(text)
    print(f"Wrote {len(rendered)} file(s) from {len(load_adrs())} ADRs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
