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

It also prints WARNINGS, which by default never affect the exit code
(ADR-035): references to retired documents, codes that resolve to no document
at all, remote links whose URL is hand-written rather than constructed,
directives that no longer apply, and a count of undecided decisions. Citing a
`Rejected` decision — or leaving one `Proposed`, or naming another project's
LU-ADR-013 — is often right, so none is an error unless the project says so:
a class named in `[luria.lint] fail_on` is promoted to a failure. Either way
`luria reports` writes the full detail as markdown, and an `inactive-ok:` /
`unresolved-ok:` / `url-ok:` comment acknowledges a deliberate one so only
the unconsidered ones stay listed — acknowledged rows never fail.

Exit 0 when clean; exit 1 with one line per violation.
"""

from __future__ import annotations

import datetime as dt
import re
import sys

from . import adr_index as builder
from . import (adr_pending, badges, ci, doc_refs, journal, narrow_titles,
               ref_status, remotes)
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
              | {j.output for j in cfg.journals.values()}
              | {cfg.reports})
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
        # Temporary documents (ADR-049) are first-class on their branch, so
        # they meet the same frontmatter bar as numbered ones — a temp doc
        # that would fail the lint after concretization should fail it now,
        # while its author still has the context loaded.
        for path in [*scheme.documents().values(),
                     *scheme.temp_documents().values()]:
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

            # Per-scheme requirements (ADR-040): the fields a scheme demands
            # beyond the standard set — what makes a cross-scheme move safe to
            # automate, because the moved document fails here until a human
            # supplies what the target scheme's template would have prompted
            # for. The machinery relocates; only a person vouches.
            for field in scheme.requires:
                if not meta.get(field):
                    errors.append(
                        f"{rel}: no `{field}:` in frontmatter — the "
                        f"{scheme.prefix} scheme requires it (luria.toml)")


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
                # An inferrable field names its own remedy (#33); one with no
                # witness left is a question only the author can answer.
                if journal.created_from_path(path) is not None:
                    errors.append(f"{rel}: no `created:` timestamp — "
                                  "`luria index` populates it from the path")
                else:
                    errors.append(f"{rel}: no `created:` timestamp, and the "
                                  "path doesn't imply one (see _template.md)")
                continue
            want = journal.path_for(jrnl, created)
            if path != want:
                errors.append(f"{rel}: `created:` says it belongs at "
                              f"{cfg.rel(want)} — run `luria new` to file "
                              "entries, or move it")
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
    # Computed by the generator, not recomputed here: the rules for what
    # counts as stale live in one place, so this check and `luria index
    # --check` cannot answer differently. Only the wording is this file's.
    report = builder.staleness()
    # This lint is usually read in a build log, where "run `luria index`" names
    # the one action that must not be taken here — putting the generator ahead
    # of this check makes it compare the generator's output against itself, and
    # it stops being able to fail (ADR-029). The remedy says so when it is
    # being read in CI.
    remedy = ci.regenerate_remedy()
    for path in report.stale:
        errors.append(f"{cfg.rel(path)}: stale — {remedy}")
    for path in report.orphaned:
        errors.append(f"{cfg.rel(path)}: not something the generator wrote — "
                      "a view directory holds only generated files (ADR-021); "
                      f"{remedy}, or file the content as a source")
    # The README's badge counts are derived from the same frontmatter, so a
    # stale one is the same class of failure as a stale index (ADR-018).
    if report.badges:
        errors.append(
            f"{cfg.rel(report.badges)}: badge counts are stale — {remedy}")


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


# The enforcement dial's vocabulary (ADR-035): a class named in
# `[luria.lint] fail_on` fails the build instead of printing. Only
# UNACKNOWLEDGED rows ever reach a class, so the directives stay the escape
# hatch under enforcement — the dial changes the consequence, not the
# accounting.
FAILABLE = ("retired-citations", "unresolved-codes", "hand-written-urls",
            "legacy-spellings", "narrow-titles", "stale-directives",
            "pending-documents", "unlinted-files")


def status_sections() -> list[tuple[str, str, list[str]]]:
    """Every status finding, as (class, headline, detail lines) — computed
    once, so the warning path and the `fail_on` path cannot disagree."""
    docs = ref_status.load_docs()
    result = ref_status.scan(docs=docs)
    sections: list[tuple[str, str, list[str]]] = []

    lines = ref_status.summary_lines(result, docs)
    if lines:
        sections.append((
            "retired-citations",
            f"{len(lines)} warning(s) — retired documents cited "
            "unacknowledged from current docs/code (`luria reports` for "
            "the sites, `inactive-ok:` to acknowledge one)", lines))

    # A code that resolves to nothing is a reference the reader can't follow
    # and the fixer can't link — until this existed it was silently dropped.
    loose = ref_status.dangling_lines(result, docs)
    if loose:
        sections.append((
            "unresolved-codes",
            f"{len(loose)} code(s) resolve to no document "
            "(`luria reports` for the sites, `unresolved-ok:` for the "
            "deliberate ones)", loose))

    # A whole file opting out of reference checking is legitimate and blunt
    # (#37) — blunt enough that the count surfaces even though nothing here
    # can act on it: an exemption nobody sees is how a report stops being a
    # complete account.
    if result.unlinted:
        sections.append((
            "unlinted-files",
            f"{len(result.unlinted)} file(s) opt out of reference checking "
            "(`unlinted-file:` — listed in the reference report)",
            [str(current().rel(p)) for p in sorted(result.unlinted)]))

    # A hand-written URL where one would be constructed is legitimate — and
    # frozen at writing time, so the deliberate ones are acknowledged
    # (`url-ok:`) and the rest are listed.
    hand, stale_urls = remotes.hand_links()
    if hand:
        sections.append((
            "hand-written-urls",
            f"{len(hand)} link(s) hand-written where a URL would be "
            "constructed (`url-ok:` acknowledges a deliberate one)", hand))

    # A citation still spelled with a concretized code's old temporary name
    # (ADR-040, ADR-049). The in-tree steady state is zero — the
    # concretizer's sweep is full — so a row here means an in-flight branch
    # merged after a concretization pass, and the remedy is mechanical.
    legacy = doc_refs.legacy_spellings()
    if legacy:
        sections.append((
            "legacy-spellings",
            f"{len(legacy)} citation(s) in a concretized code's old spelling "
            "(`luria link --fix` upgrades them)", legacy))

    # A title in a scheme that claims to transfer, spelled in this project's
    # own nouns. Absent entirely unless the project supplies a vocabulary AND
    # marks a scheme `titles_generalize` — luria ships neither.
    narrow = narrow_titles.rows()
    if narrow:
        sections.append((
            "narrow-titles",
            f"{len(narrow)} title(s) name a project noun in a scheme whose "
            "documents claim to transfer (`broad-ok:` acknowledges another "
            "sense)", narrow))

    # A directive that silently does nothing is worse than no directive.
    stale = ref_status.stale_annotations(result, docs) + stale_urls
    for path in doc_refs.doc_files():
        stale += doc_refs.directive_problems(path, path.read_text())
    if stale:
        sections.append((
            "stale-directives",
            f"{len(stale)} directive(s) no longer apply", sorted(stale)))

    # One line, not the table: the point is that the number is never zero
    # silently. `luria reports` ranks them by age and citation count.
    rows = adr_pending.pending()
    if rows:
        sections.append((
            "pending-documents",
            adr_pending.headline(rows, dt.date.today(), current().stale_days)
            + " (`luria reports` for the table)", []))
    return sections


def report_warnings(errors: list[str]) -> None:
    """Status findings: warnings by default, failures on request (ADR-035).

    Citing a retired document is often correct — a `Rejected` decision exists
    to be pointed at — so by default every class here is reported and none
    fails the build. A project that wants a class *enforced* names it in
    `[luria.lint] fail_on`, and its unacknowledged rows become violations;
    the acknowledgement directives keep working either way."""
    fail = set(current().fail_on)
    for name in sorted(fail - set(FAILABLE)):
        # A dial set to a notch that doesn't exist must not silently enforce
        # nothing (DP-1).
        errors.append(f"luria.toml: `fail_on` names {name!r}, which is no "
                      f"warning class (known: {', '.join(FAILABLE)})")

    for name, headline, lines in status_sections():
        if name in fail:
            errors.append(f"{headline} — failing: `fail_on` names "
                          f"{name!r} in luria.toml")
            errors.extend(lines)
        else:
            print(f"luria: {headline}", file=sys.stderr)
            for line in lines:
                print(f"  {line}", file=sys.stderr)


def run() -> None:
    """Check the record; exits 1 with one line per violation."""
    errors: list[str] = []
    check_docs_index(errors)
    check_frontmatter(errors)
    check_generated_index(errors)
    check_journals(errors)
    check_version_history(errors)
    check_bare_refs(errors)
    check_wikilinks(errors)
    report_warnings(errors)
    if errors:
        print(f"luria: {len(errors)} violation(s)", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        raise SystemExit(1)
    print("luria: docs lint clean")


if __name__ == "__main__":
    import fire
    fire.Fire(run)
