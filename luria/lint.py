"""The docs lint: what fails a build, and what is only reported.

    luria lint

Checks (each one fails the build):

1. **Docs index** — every markdown page under the docs directory is linked from
   its `README.md`, so the index can't silently drift from the directory.
1b. **Journals** — every entry's path agrees with its `created:` timestamp and
   carries a `title:` (ADR-020); `version:` agrees with `history:` (ADR-019).
2. **Frontmatter** — every document in a reference scheme carries a `status:`
   from the canonical vocabulary, at least one `tags:` entry (ADR-003), and a
   `title:` that agrees with its body heading (ADR-013).
3. **Generated index** — the decision index and its per-tag pages are built from
   frontmatter (ADR-004), so a stale index is a failure rather than a silent
   divergence. `luria index` regenerates.
4. **Bare references** — a document code, a design principle or an issue number
   cited in prose without being a hyperlink (ADR-005). `luria link --fix`
   writes exactly the links this check demands.
5. **Wikilinks** — a `[[CODE]]` is the author asserting a reference (ADR-025):
   resolvable ones await `luria link --fix`; unresolvable ones are an error
   the fixer cannot clear, because the request was explicit.

It also prints WARNINGS, which never affect the exit code (ADR-007): references
to retired documents, codes that resolve to no document at all, remote links
whose URL is hand-written rather than constructed, directives that no longer
apply, and a count of undecided decisions. Citing a `Rejected`
decision — or leaving one `Proposed`, or naming another project's LU-ADR-013 — is
often right, so none can be an error; all should be visible. `luria ref-status`
and `luria pending` give the detail, and an `inactive-ok:` / `unresolved-ok:` /
`url-ok:` comment acknowledges a deliberate one so only the unconsidered ones
stay listed.

Exit 0 when clean; exit 1 with one line per violation.
"""

from __future__ import annotations

import datetime as dt
import re
import sys

from . import adr_index as builder
from . import adr_pending, badges, ci, doc_refs, journal, ref_status, remotes
from .config import current

# The closed status vocabulary (ADR-003). `Active` is the in-force state; the
# rest are the ways a decision can be out of force, each meaning something a
# reader needs. An optional " — note" carries a short qualifier.
STATUS_RE = re.compile(
    r"^(Active|Proposed|Deferred|Superseded|Rejected)( — \S(?:.|\n)*\S)?$"
)

# Pages deliberately absent from the index: the index itself.
INDEX_EXEMPT = {"README.md"}


def check_docs_index(errors: list[str]) -> None:
    cfg = current()
    index = cfg.docs / "README.md"
    if not index.exists():
        return
    text = index.read_text()
    # Two kinds of directory are exempt. A *source* directory holds things a
    # writer files, not pages a reader browses — the thing a reader opens is
    # the view. A *view* directory is wholly generated and carries its own
    # index (the decision index, a journal's book list), so the docs index
    # links the entrypoint and the rest indexes itself (ADR-021).
    exempt = ({s.dir for s in cfg.schemes.values()}
              | {s.view for s in cfg.schemes.values() if s.render == "index"}
              | {s.tag_dir for s in cfg.schemes.values() if s.render == "index"}
              | {j.dir for j in cfg.journals.values()}
              | {j.output for j in cfg.journals.values()})
    pages = sorted(cfg.docs.glob("*.md"))
    for sub in sorted(p for p in cfg.docs.iterdir() if p.is_dir()):
        if sub not in exempt:
            pages += sorted(sub.glob("*.md"))
    for page in pages:
        rel = page.relative_to(cfg.docs)
        if str(rel) in INDEX_EXEMPT:
            continue
        # A page is "indexed" when README.md links its relative path.
        if f"({rel})" not in text:
            errors.append(f"{cfg.rel(index)}: missing index entry for {rel}")


def check_frontmatter(errors: list[str]) -> None:
    cfg = current()
    for scheme in cfg.schemes.values():
        for path in scheme.documents().values():
            rel = cfg.rel(path)
            meta, body = builder.parse_frontmatter(path.read_text())
            if not meta:
                errors.append(f"{rel}: no YAML frontmatter (see _template.md)")
                continue
            check_title(errors, rel, meta, body)
            status = str(meta.get("status", "")).strip()
            if not status:
                errors.append(f"{rel}: no `status:` in frontmatter")
            elif not STATUS_RE.match(status):
                errors.append(
                    f"{rel}: nonstandard status {status!r} (want: "
                    "Active|Proposed|Deferred|Superseded|Rejected, optional "
                    "' — note')")
            if not (meta.get("tags") or []):
                errors.append(f"{rel}: no `tags:` in frontmatter (see ADR-003)")


def check_title(errors: list[str], rel: str, meta: dict, body: str) -> None:
    """`title:` is the source of truth, and the body's H1 repeats it.

    Two copies of one string is the drifting projection DP-3 names, and the
    filename no longer carries a third (ADR-013). The H1 can't simply be
    dropped — someone reading the file on its own needs a heading — so this is
    rung 2: keep the copy, guard the property that they agree."""
    title = str(meta.get("title") or "").strip()
    if not title:
        errors.append(f"{rel}: no `title:` in frontmatter (see ADR-013)")
        return
    first = next((ln for ln in body.splitlines() if ln.startswith("#")), "")
    heading = builder.TITLE_RE.sub("", first).strip()
    if heading and heading != title:
        errors.append(
            f"{rel}: `title:` and the body heading disagree — "
            f"{title!r} vs {heading!r}")


def check_journals(errors: list[str]) -> None:
    """A journal entry's path is derived from its `created:` timestamp, and the
    two have to agree — otherwise the ordering the whole scheme rests on says
    one thing and the frontmatter says another (ADR-020). Also: an entry needs
    a title, because the title is what the book's contents list shows."""
    cfg = current()
    for name, jrnl in cfg.journals.items():
        for path in sorted(jrnl.dir.rglob("*.md")):
            if path.name == "_template.md":
                continue
            rel = cfg.rel(path)
            meta, _ = builder.parse_frontmatter(path.read_text())
            created = journal.parse_created(meta.get("created"))
            if created is None:
                errors.append(f"{rel}: no `created:` timestamp (see _template.md)")
                continue
            want = journal.path_for(jrnl, created)
            if path != want:
                errors.append(f"{rel}: `created:` says it belongs at "
                              f"{cfg.rel(want)} — run `luria journal new` to "
                              "file entries, or move it")
            if not str(meta.get("title") or "").strip():
                errors.append(f"{rel}: no `title:` — it is what the {name} "
                              "book's contents list shows")


def check_version_history(errors: list[str]) -> None:
    """`version:` and `history:` have to agree.

    Correcting a document in place is only honest because the correction is
    visible ([ADR-019](../record/decisions.d/ADR-019.md)), and nothing was checking
    that the visible part exists. A bumped version with no history entry is a
    silent revision wearing a version number."""
    cfg = current()
    for scheme in cfg.schemes.values():
        for path in scheme.documents().values():
            meta, _ = builder.parse_frontmatter(path.read_text())
            version = int(meta.get("version", 1) or 1)
            history = meta.get("history") or []
            rel = cfg.rel(path)
            if version > 1 and not history:
                errors.append(
                    f"{rel}: version {version} with no `history:` — a "
                    "correction is only honest if it says what changed "
                    "(see ADR-019)")
            elif history:
                last = history[-1].get("version") if isinstance(history[-1], dict) else None
                if last != version:
                    errors.append(
                        f"{rel}: `history:` ends at version {last!r} but the "
                        f"document says {version}")


def check_generated_index(errors: list[str]) -> None:
    """The index is generated (ADR-004) — verify it's current, rather than
    checking each document is mentioned, which a generated file can't fail."""
    cfg = current()
    rendered = builder.outputs()
    # This lint is usually read in a build log, where "run `luria index`" names
    # the one action that must not be taken here — putting the generator ahead
    # of this check makes it compare the generator's output against itself, and
    # it stops being able to fail (ADR-029). The remedy says so when it is
    # being read in CI.
    remedy = ci.regenerate_remedy()
    for path, text in rendered.items():
        if not path.exists() or path.read_text() != text:
            errors.append(f"{cfg.rel(path)}: stale — {remedy}")
    for path in builder.orphans(rendered):
        errors.append(f"{cfg.rel(path)}: not something the generator wrote — "
                      "a view directory holds only generated files (ADR-021); "
                      f"{remedy}, or file the content as a source")
    # The README's badge counts are derived from the same frontmatter, so a
    # stale one is the same class of failure as a stale index (ADR-018).
    readme = badges.readme()
    if readme.exists() and badges.OPEN in (text := readme.read_text()) \
            and badges.rewrite(text) != text:
        errors.append(f"{cfg.rel(readme)}: badge counts are stale — {remedy}")


def check_wikilinks(errors: list[str]) -> None:
    """A wikilink is the author asserting "this is a reference" (ADR-025), so
    both failure modes are violations, with different remedies: a resolvable
    one just hasn't been fixed yet, and an unresolvable one is a request the
    machinery cannot honour — which must be said, not skipped (DP-1)."""
    cfg = current()
    for path in doc_refs.doc_files():
        text = path.read_text()
        for w in doc_refs.wikilinks(text, path):
            rel = cfg.rel(path)
            if w.target is None:
                errors.append(
                    f"{rel}:{w.line}: [[{w.inner}]] resolves to nothing this "
                    "project can link — a typo, an unregistered prefix, or a "
                    "self-link")
            else:
                errors.append(f"{rel}:{w.line}: [[{w.inner}]] is not yet a "
                              "link — run `luria link --fix`")


def check_bare_refs(errors: list[str]) -> None:
    """A reference the reader can't follow is a reference they have to grep for.
    Document codes, design principles and issue numbers are hyperlinks in prose
    — everywhere the same rules the fixer uses say they can be (ADR-005)."""
    cfg = current()
    adrs, anchors = doc_refs.adr_paths(), doc_refs.dp_anchors()

    def scan_one(path) -> list[str]:
        text = path.read_text()
        # `rewritable_refs` is what the fixer would write — unresolvable codes,
        # self-references and rewrites the frontmatter wouldn't survive are
        # already excluded, so lint never demands something `--fix` won't do.
        return [f"{cfg.rel(path)}:{ref.line}: {ref.describe()} is not a link — "
                "run `luria link --fix`"
                for ref in doc_refs.rewritable_refs(text, path, adrs, anchors)]

    # One file, one unit, scanned wide (ADR-026); `pmap` keeps input order,
    # so the report reads the same at any width.
    from .parallel import pmap
    for found in pmap(scan_one, doc_refs.doc_files()):
        errors.extend(found)


def report_warnings() -> None:
    """Things worth seeing that can't be violations. Citing a retired document
    is often correct — a `Rejected` decision exists to be pointed at — so it is
    reported, never failed (ADR-007)."""
    lines = ref_status.summary_lines()
    if lines:
        print(f"luria: {len(lines)} warning(s) — retired documents cited "
              "unacknowledged from current docs/code (`luria ref-status` for "
              "the sites, `inactive-ok:` to acknowledge one)", file=sys.stderr)
        for line in lines:
            print(f"  {line}", file=sys.stderr)

    # A code that resolves to nothing is a reference the reader can't follow
    # and the fixer can't link — until this existed it was silently dropped.
    loose = ref_status.dangling_lines()
    if loose:
        print(f"luria: {len(loose)} code(s) resolve to no document "
              "(`luria ref-status` for the sites, `unresolved-ok:` for the "
              "deliberate ones)", file=sys.stderr)
        for line in loose:
            print(f"  {line}", file=sys.stderr)

    # A hand-written URL where one would be constructed is legitimate — and
    # frozen at writing time, so the deliberate ones are acknowledged
    # (`url-ok:`) and the rest are listed.
    hand, stale_urls = remotes.hand_links()
    if hand:
        print(f"luria: {len(hand)} link(s) hand-written where a URL would be "
              "constructed (`url-ok:` acknowledges a deliberate one)",
              file=sys.stderr)
        for line in hand:
            print(f"  {line}", file=sys.stderr)

    # A directive that silently does nothing is worse than no directive.
    stale = ref_status.stale_annotations() + stale_urls
    for path in doc_refs.doc_files():
        stale += doc_refs.directive_problems(path, path.read_text())
    if stale:
        print(f"luria: {len(stale)} directive(s) no longer apply", file=sys.stderr)
        for line in sorted(stale):
            print(f"  {line}", file=sys.stderr)

    # One line, not the table: the point is that the number is never zero
    # silently. `luria pending` ranks them by age and citation count.
    rows = adr_pending.pending()
    if rows:
        print("luria: " + adr_pending.headline(
            rows, dt.date.today(), current().stale_days)
            + " (`luria pending` for the table)", file=sys.stderr)


def main() -> int:
    errors: list[str] = []
    check_docs_index(errors)
    check_frontmatter(errors)
    check_generated_index(errors)
    check_journals(errors)
    check_version_history(errors)
    check_bare_refs(errors)
    check_wikilinks(errors)
    report_warnings()
    if errors:
        print(f"luria: {len(errors)} violation(s)", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    print("luria: docs lint clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
