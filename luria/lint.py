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
2b. **Contracts** — what a scheme declares beyond the standard set, compiled
   once per scheme (`luria/contract.py`, #141): fields it `requires`
   (ADR-040), what its `references` hold (ADR-060), and which of its tags may
   combine (`tag_groups`, ADR-054). One pass, each finding saying why.
3. **View directories** — a view directory holds only generated files
   (ADR-021), so a hand-written file inside one is a failure. Whether a
   committed view is *current* is the generation job's question, answered by
   `luria index --check` on the default branch (ADR-068): the lint reads
   sources and needs no view on disk, so it runs on a branch as it is.
4. **Bare references** — a document code, a design principle or an issue number
   cited in prose without being a hyperlink (ADR-005). `luria link --fix`
   writes exactly the links this check demands.
5. **Wikilinks** — a `[[CODE]]` is the author asserting a reference (ADR-025):
   resolvable ones await `luria link --fix`; unresolvable ones are an error
   the fixer cannot clear, because the request was explicit.

It also prints WARNINGS, which by default never affect the exit code
(ADR-035): references to retired documents, codes that resolve to no document
at all, remote links whose URL is hand-written rather than constructed,
pinned remote documents whose upstream content changed since it was endorsed,
relative link targets that resolve to nothing from where the prose renders,
directives that no longer apply, and a count of undecided decisions. Citing a
`Rejected` decision — or leaving one `Proposed`, or naming another project's
LU-ADR-013 — is often right, so none is an error unless the project says so:
a class named in `[luria.lint] fail_on` is promoted to a failure. Either way
`luria reports` writes the full detail as markdown, and an `inactive-ok:` /
`unresolved-ok:` / `url-ok:` / `target-ok:` comment acknowledges a deliberate
one so only the unconsidered ones stay listed — acknowledged rows never fail.

Exit 0 when clean; exit 1 with one line per violation.
"""

from __future__ import annotations

import datetime as dt
import re
import sys

from . import adr_index as builder
from . import (adr_pending, badges, chains, ci, contract, doc_refs, journal, referents,
               link_targets, narrow_titles, pins, ref_status, remotes,
               relations, sources, statuses, templates)
from . import aliases as aliases_mod
from . import config as config_mod
from .config import current

# Pages deliberately absent from the index: the index itself.
INDEX_EXEMPT = {"README.md"}


def check_docs_index(errors: list[str]) -> None:
    cfg = current()
    index = cfg.docs / "README.md"
    if not index.exists():
        return
    text = index.read_text(encoding="utf-8")
    # Two kinds of directory are exempt. A *source* directory holds things a
    # writer files, not pages a reader browses — the thing a reader opens is
    # the view. A *view* directory is wholly generated and carries its own
    # index (the decision index, a journal's book list), so the docs index
    # links the entrypoint and the rest indexes itself (ADR-021).
    exempt = ({s.dir for s in cfg.schemes.values()}
              | {s.view for s in cfg.schemes.values() if s.render == "index"}
              | {s.tag_dir for s in cfg.schemes.values() if s.render == "index"}
              | {s.vocab_dir(v.name) for s in cfg.schemes.values()
                 if s.render == "index" for v in s.vocabularies}
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
            meta, body = builder.parse_frontmatter(path.read_text(encoding="utf-8"))
            if not meta:
                errors.append(f"{rel}: no YAML frontmatter (see _template.md)")
                continue
            check_title(errors, rel, meta, body)
            status = statuses.of(meta, scheme)
            if not status.value:
                errors.append(f"{rel}: no `status:` in frontmatter")
            elif statuses.combined(meta):
                # The tree states both facts in one scalar; the remedy is
                # the repair `luria index` already runs (ADR-031).
                errors.append(
                    f"{rel}: `status:` carries a note — `luria repair` moves "
                    f"it to `status_note:`")
            elif statuses.undeclared(scheme, status.value):
                # Only when the scheme declares no `status` vocabulary, so
                # nothing checks the word. Where it does declare one, the
                # check is the vocabulary's, in `check_contracts` with every
                # other controlled field — one implementation (DP-4).
                errors.append(
                    f"{rel}: status {status.value!r} is unchecked — the "
                    f"{scheme.prefix} scheme declares no `status` "
                    f"vocabulary, so any word passes and the absence looks "
                    f"exactly like a clean check "
                    f"(`luria upgrade statuses` writes one)")
            # "Superseded names its successor" used to be a branch here.
            # It is a `required_when` on the built-in field now, checked with
            # every other obligation in `check_contracts` (ADR-071 stated
            # with the mechanism rather than beside it).
            if not (meta.get("tags") or []):
                errors.append(f"{rel}: no `tags:` in frontmatter (see ADR-003)")



def check_form_text(errors: list[str]) -> None:
    """A prose field still saying what the scheme's `_template.md` says is
    the form's text, not the document's — a summary that reads "one-paragraph
    description of the decision" in the index. Write it, or drop the key."""
    cfg = current()
    for scheme in cfg.schemes.values():
        for path in [*scheme.documents().values(),
                     *scheme.temp_documents().values()]:
            meta, _ = builder.parse_frontmatter(path.read_text(encoding="utf-8"))
            for key in templates.form_text(scheme, meta or {}):
                fallback = (" — the index falls back to the title"
                            if key == "summary" else "")
                errors.append(
                    f"{cfg.rel(path)}: `{key}:` still says what "
                    f"{cfg.rel(scheme.dir / templates.TEMPLATE_NAME)} says — "
                    f"the form's words, not this document's; write it, or "
                    f"drop the key{fallback}")


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


def check_status_vocabulary(errors: list[str]) -> None:
    """A `statuses.yaml` key outside ADR-003's five words.

    Narrowing the vocabulary per scheme is the point; extending it is not, and
    a file naming `Accepted` would render a legend and silence nothing — it
    would look like it was working, which is the worst way for a config file to
    be wrong."""
    for scheme in current().schemes.values():
        errors.extend(statuses.problems(scheme))


def check_reserved_prefix(errors: list[str]) -> None:
    """A scheme declared in the reserved fixture namespace (ADR-tmpgody7).

    Always wrong and always mechanically fixable, which is why it is an error
    and not a report: the namespace exists so that a project's test suite can
    spell codes nobody claims, and a project that claims one has quietly taken
    that guarantee away from itself — its own fixture codes start resolving,
    and the failure looks exactly like success until a real document lands on
    the number.

    The check reads the config, not the record, so it fires at declaration
    time, before the first document makes the prefix expensive to change."""
    for prefix in current().schemes:
        if config_mod.in_fixture_namespace(prefix):
            errors.append(
                f"luria.toml: scheme {prefix} is in the reserved fixture "
                f"namespace {config_mod.FIXTURE_NAMESPACE}\u2026 — pick another "
                "prefix, or `rename_scheme` it if it already has documents")


def check_contracts(errors: list[str]) -> None:
    """Each scheme's contract, enforced — what it `requires`, what its
    `references` hold, which of its `tag_groups` combine (ADR-040, ADR-060,
    ADR-054). Compiled once per scheme and checked in one pass over its
    documents (#141), where there used to be one pass per table.

    Opt-in, all of it: a scheme declaring none of the three compiles to an
    empty contract and this is silent for it, which is every record that
    predates the tables. A breach is a hard error, not a status class — a
    malformed entry is a defect in the document, and declaring the table
    was the opt-in (ADR-054)."""
    cfg = current()
    known: dict[str, set[str]] = {}
    # One reader for the whole run: a much-cited paper is otherwise re-parsed
    # once per document that cites it (#233).
    resolve = referents.Lookup()
    for scheme in cfg.schemes.values():
        c = contract.for_scheme(scheme)
        # Not `c.empty`: that ignores the built-in `superseded_by` field,
        # which is exactly the one every scheme has to have checked.
        if not c.fields and not c.groups:
            continue
        for field in c.fields:
            if (field.reference and field.reference != contract.ANY_SCHEME
                    and field.reference not in known):
                known[field.reference] = contract.resolvable(field.reference)
        for path in [*scheme.documents().values(),
                     *scheme.temp_documents().values()]:
            meta, _ = builder.parse_frontmatter(path.read_text(encoding="utf-8"))
            if not meta:
                continue          # check_frontmatter already said so
            # A `status:` still carrying its note is one mistake with one
            # finding, raised where the repair is named. Reading it apart
            # here keeps the contract's checker generic (#181).
            meta = statuses.normalised(meta)
            errors.extend(contract.violations(c, cfg.rel(path), meta, known,
                                              resolve))


def check_numbers(errors: list[str]) -> None:
    """A document's `number:` and its filename have to agree (#219).

    The same check `check_journals` makes about `created:` and an entry's
    path, for the same reason: identity lives in the frontmatter, the name on
    disk is a projection of it, and a projection that disagrees with its
    source means every reader picks a different one. Here the stakes are
    concrete — `documents()` reads the field, while a link target is written
    from the code, so a disagreement resolves references to a filename that
    is not there.

    A violation rather than a report, and not repaired automatically: which
    of the two is right is a question only the author can answer, and
    renaming on a guess would move a document's identity. An *absent* `number:`
    is the repairable case, and `luria repair` handles it from the path."""
    cfg = current()
    for scheme in cfg.schemes.values():
        for path in sorted(scheme.dir.glob("*.md")):
            if scheme.temp_of(path) is not None:
                continue
            declared = config_mod._declared_number(path)
            named = scheme.number_in_name(path)
            if declared is None or named is None or declared == named:
                continue
            errors.append(
                f"{cfg.rel(path)}: `number: {declared}` but the filename says "
                f"{named} — identity is the field, so this document answers "
                f"to {scheme.code(declared)} while its file is named for "
                f"{scheme.code(named)}; rename the file or correct the field")


def check_alias_collisions(errors: list[str]) -> None:
    """Two documents rendering one alias (#219).

    A violation rather than a report, because a spelling that resolves to two
    documents makes every citation through it ambiguous — worse than a stale
    reference, which at least points somewhere definite.

    Not auto-disambiguated. An automatic suffix is order-dependent and would
    silently renumber when a third document arrives; the fix is the template,
    and including `{number}` in it makes collisions impossible by
    construction, since the number is what `luria concretize` guarantees
    unique."""
    cfg = current()
    for scheme in cfg.schemes.values():
        if not scheme.alias:
            continue
        rendered: dict[str, list[int]] = {}
        for number, path in scheme.documents().items():
            meta, _ = builder.parse_frontmatter(path.read_text(encoding="utf-8"))
            spelling = aliases_mod.render(scheme.alias, meta, scheme, number)
            if spelling:
                rendered.setdefault(spelling, []).append(number)
        for spelling, numbers in sorted(rendered.items()):
            if len(numbers) > 1:
                codes = ", ".join(scheme.code(n) for n in sorted(numbers))
                errors.append(
                    f"luria.toml: schemes.{scheme.prefix}.alias renders "
                    f"`{spelling}` for {codes} — one spelling cannot answer "
                    f"for {len(numbers)} documents; add `{{number}}` to the "
                    f"template, or a field that tells them apart")


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
            meta, _ = builder.parse_frontmatter(path.read_text(encoding="utf-8"))
            created = journal.parse_created(meta.get("created"))
            if created is None:
                # An inferrable field names its own remedy (#33); one with no
                # witness left is a question only the author can answer.
                if journal.created_from_path(path) is not None:
                    errors.append(f"{rel}: no `created:` timestamp — "
                                  "`luria repair` populates it from the path")
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
            meta, _ = builder.parse_frontmatter(path.read_text(encoding="utf-8"))
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


def check_view_dirs(errors: list[str]) -> None:
    """A view directory holds only generated files (ADR-021), so a
    hand-written file inside one is a violation — computed against what the
    generator would write, in memory, so the check reads sources and writes
    nothing.

    Staleness — a committed view that differs from the generator's output —
    is not checked here. It is a property of the default branch, where the
    views are committed, and `luria index --check` in the generation job
    answers it there (ADR-068); a branch carries the default branch's copies
    and has nothing to be stale against. For the same reason a file in a view
    directory that says it was generated is left alone: it is a view the
    generator no longer writes, which `luria index` deletes and `--check`
    reports, not something a person wrote."""
    cfg = current()
    for path in builder.staleness().orphaned:
        if "luria index" in path.read_text(encoding="utf-8"):
            continue
        errors.append(f"{cfg.rel(path)}: not something the generator wrote — "
                      "a view directory holds only generated files (ADR-021); "
                      "file the content as a source")


def workflow_temp_code_lines() -> list[str]:
    """A temporary code (ADR-049) cited from a workflow file, one line per
    site. `luria concretize` rewrites the code with everything else when the
    decision is numbered, and the workflow's own token cannot push a change
    under `.github/workflows/` — so on that token the generation job's
    commit is refused whole. A job pushing with a token that has workflow
    write has no such problem, which is why this is a warning class and not
    a violation: the project says which token it runs on by naming
    `workflow-temp-codes` in `fail_on`, or not."""
    cfg = current()
    patterns = [s.temp_pattern for s in cfg.schemes.values()]
    found: list[str] = []
    for path in sorted(cfg.root.glob(".github/workflows/*.y*ml")):
        text = path.read_text(encoding="utf-8")
        for regex in patterns:
            for m in regex.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                found.append(f"{cfg.rel(path)}:{line}: {m.group(0)}")
    return found


def check_wikilinks(errors: list[str]) -> None:
    """A wikilink is the author asserting "this is a reference" (ADR-025), so
    both failure modes are violations, with different remedies: a resolvable
    one just hasn't been fixed yet, and an unresolvable one is a request the
    machinery cannot honour — which must be said, not skipped (DP-1)."""
    cfg = current()
    for path in doc_refs.doc_files():
        text = path.read_text(encoding="utf-8")
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
        text = path.read_text(encoding="utf-8")
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
            "broken-targets", "remote-drift", "inert-status",
            "source-mismatch", "source-unchecked",
            "legacy-spellings", "narrow-titles", "stale-directives",
            "template-drift", "broken-chains",
            "one-sided-relations", "spent-upgrades",
            "pending-documents", "unlinted-files", "workflow-temp-codes",
            "unlinked-site")

# Classes `[luria.lint] mute` may suppress: every failable class, plus
# `acknowledged-uniformity` — which is not failable (a project cannot promote
# its own acknowledgement to a failure) and is exactly the kind of standing
# note a project may reasonably not want repeated on every run.
#
# No class is exempt, which is a deliberate choice and the symmetric one:
# `fail_on` already lets a project make any class fatal and defaults to making
# none of them so, and a tool that decides for a project which of its own
# findings it is allowed to stop reading is asserting an authority it has not
# earned. The cost is that a project can hide something it should not, and
# `luria reports` still renders the full accounting either way — muting
# changes what the command prints, not what the record says.
MUTABLE = FAILABLE + ("acknowledged-uniformity",)


def unlinked_site() -> list[str]:
    """A record that publishes a site whose README never names it.

    `luria site` has always known where the record lands — `base_url` derives
    from `issue_url` — and nothing wrote it where a reader of the repository
    front page would look. An absence that reads exactly like a success is
    the case DP-15 exists for, and this is the signal.

    Satisfied by the URL appearing anywhere in the README, prose link
    included: the finding is "your front page does not point at the site you
    publish", not "you must use our marker".

    Scoped by `[luria.site] publish`, which defaults true: `base_url` derives
    for every GitHub project whether or not one is deployed, so a record that
    lives only in its repository says `publish = false` and the guard goes
    quiet — a guard opts out rather than being argued with (DP-10)."""
    from . import readme
    cfg = current()
    if not (cfg.site.publish and cfg.site.base_url):
        return []
    path = readme.path()
    if not path.exists():
        return []
    if cfg.site.base_url in path.read_text(encoding="utf-8"):
        return []
    return [f"README.md never names {cfg.site.base_url}, where `luria site` "
            f"publishes this record — add a `{readme.markers('site')[0]}` / "
            f"`{readme.markers('site')[1]}` region for `luria index` to fill, "
            f"or write the link yourself"]


def spent_upgrades() -> list[str]:
    """Upgrades this record has already run.

    A one-shot upgrade is temporary by construction, and the thing that
    makes it *stay* temporary is being asked about. Once every record has
    run one it is dead code that still has to be read, tested and
    explained — so a record that no longer needs it says so, the way
    `stale-directives` reports a directive that no longer suppresses
    anything. One user's record saying it is not proof every record has,
    which is why the row says "once every record has" rather than "now"."""
    from . import upgrade
    out = []
    for name, entry in upgrade.SUNSET.items():
        writes, lines, _ = upgrade._plan(current().root)
        if not writes and not lines:
            out.append(f"`luria upgrade {name}` has nothing left to do "
                       f"here — remove it at {entry.sunset}")
    return out


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

    # A temporary code in a workflow file is one the generation job cannot
    # rewrite on the workflow's own token; a project on that token names the
    # class in `fail_on`, one whose job pushes with workflow write leaves it.
    sites = workflow_temp_code_lines()
    if sites:
        sections.append((
            "workflow-temp-codes",
            f"{len(sites)} temporary code(s) cited from a workflow file — the "
            "workflow's own token cannot push the rewrite once the decision "
            "is numbered; cite the number when it has one, say it in prose, "
            "or give the generation job a token with workflow write and "
            "leave this class unenforced", sites))

    # A whole file opting out of reference checking is legitimate and blunt
    # (#37) — blunt enough that the count surfaces even though nothing here
    # can act on it: an exemption nobody sees is how a report stops being a
    # complete account.
    # The site the record publishes, named nowhere a reader of the front page
    # would look. An absence that reads exactly like a success (DP-15), and
    # the one thing here whose fix is a paste rather than an edit to the
    # record.
    if unlinked := unlinked_site():
        sections.append((
            "unlinked-site",
            "the published site is not linked from the README",
            unlinked))

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

    # A pinned remote document whose content moved on since a human endorsed
    # it (#135). The observation is committed state (`luria remotes --refresh`
    # writes it), so the comparison here is offline like every other check —
    # and re-endorsing IS the acknowledgement, so no comment directive exists
    # for this class: the remedy updates the lockfile, not the prose.
    drifted = pins.drift_lines()
    if drifted:
        sections.append((
            "remote-drift",
            f"{len(drifted)} content pin(s) out of step — upstream changed "
            "since endorsement, or the pin outlived its citations "
            "(`luria remotes --pin` re-endorses or prunes)", drifted))

    # A relative target that resolves to nothing from where the prose renders.
    # The code checks above cannot see it: they verify that `ADR-035` names a
    # document, not that the path someone typed around it goes anywhere (#100).
    dead, stale_targets = link_targets.broken()
    if dead:
        sections.append((
            "broken-targets",
            f"{len(dead)} relative link target(s) resolve to nothing from "
            "where the prose renders (`luria link --fix` spells code targets; "
            "`target-ok:` acknowledges a deliberate one)", dead))

    # An identifier that resolves to a different paper than the one the
    # document names (#166). Read from the committed lockfile, never fetched
    # here — `luria remotes --resolve` is what opens the socket.
    wrong, unchecked, stale_sources = sources.mismatch_lines()
    if wrong:
        sections.append((
            "source-mismatch",
            f"{len(wrong)} identifier(s) name a different document than the "
            "one recorded (`source-ok:` acknowledges a deliberate one, "
            "`luria remotes --resolve` refreshes what upstream serves)", wrong))

    # Not the same finding, and the difference is the whole point: this one
    # says nobody has ever asked. Under `network = "require"` it is a failure,
    # so a green CI run means the citations were verified rather than merely
    # remembered from whenever someone last ran the command.
    if unchecked:
        sections.append((
            "source-unchecked",
            f"{len(unchecked)} identifier(s) nothing has verified — upstream "
            "could not be reached and the lockfile has no answer "
            "(`luria remotes --resolve` when the network is back)", unchecked))

    # A status field where every record agrees is indistinguishable from no
    # status field — and `active` is what `retired-citations` reads, so the
    # build is green because nothing is being judged rather than because
    # nothing is wrong (#104).
    uniform = statuses.uniform_rows()
    if uniform:
        sections.append((
            "inert-status",
            f"{len(uniform)} scheme(s) file effectively every record at one "
            "status, so the field is predictable without reading it and the "
            "citation checks have almost nothing to fire on", uniform))

    # Schemes whose uniformity a human has vouched for with `uniform_ok`. The
    # fact is unchanged — nothing there is being judged — so it is still
    # reported, as a note carrying its reason rather than as a finding. Same
    # bargain `inactive-ok:` strikes at a citation site, and the class is
    # deliberately absent from FAILABLE: a project cannot promote its own
    # acknowledgement to a failure.
    if acknowledged := statuses.acknowledged_rows():
        sections.append((
            "acknowledged-uniformity",
            f"{len(acknowledged)} scheme(s) uniform by declaration "
            "(`uniform_ok` in luria.toml)", acknowledged))

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

    # A declared sequence contradicting itself: a succession that loops, or
    # a comparison one side declares and the other does not. Both are
    # structural, so neither needs an acknowledgement — there is no reading
    # under which either is what the author meant.
    broken = chains.rows()
    if broken:
        sections.append((
            "broken-chains",
            f"{len(broken)} succession(s) loop — a step that comes before "
            "itself, so the sequence has no earliest member", broken))

    # A relation and its declared converse are one fact written in two
    # places. One place holding it is not a disagreement to adjudicate, it
    # is a write nobody has made yet — hence the fixer in the wording.
    lopsided = relations.rows()
    if lopsided:
        sections.append((
            "one-sided-relations",
            f"{len(lopsided)} declared relation(s) are held by one side "
            "only (`luria link --fix` writes the other)", lopsided))

    # A scheme's form against the scheme's contract. The template is exempt
    # from every document check, so this is the only pass that reads it —
    # and it is the file every document is a copy of, which is why a drift
    # here is reported once and shows up as nothing at all downstream.
    drift = templates.rows()
    if drift:
        sections.append((
            "template-drift",
            f"{len(drift)} scaffolded field(s) contradict the scheme's own "
            "contract (a document copied from the form starts in the wrong "
            "shape)", drift))

    spent = spent_upgrades()
    if spent:
        sections.append((
            "spent-upgrades",
            f"{len(spent)} one-shot upgrade(s) this record no longer needs",
            spent))

    # A directive that silently does nothing is worse than no directive.
    stale = ref_status.stale_annotations(result, docs) + stale_urls \
        + stale_targets + stale_sources + pins.flag_problems()
    for path in doc_refs.doc_files():
        stale += doc_refs.directive_problems(path, path.read_text(encoding="utf-8"))
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
    # `network = "require"` is a statement about what a green build means:
    # that the references were checked, not that nobody could check them. It
    # promotes the one class that says "nobody asked", without the project
    # having to name it in `fail_on` as well — the setting already said it.
    if current().network == "require":
        fail.add("source-unchecked")
    for name in sorted(fail - set(FAILABLE)):
        # A dial set to a notch that doesn't exist must not silently enforce
        # nothing (DP-1).
        errors.append(f"luria.toml: `fail_on` names {name!r}, which is no "
                      f"warning class (known: {', '.join(FAILABLE)})")

    # A class the project has decided it does not want reported at all.
    # `fail_on` changes a finding's consequence; `mute` removes it from the
    # report. Muting is blunter than the acknowledgement directives on
    # purpose: those carry a reason at the citing site, which is the right
    # shape when the finding is about a document, and the wrong shape when a
    # project has simply decided a whole check is not useful to it.
    mute = set(current().mute)
    for name in sorted(mute - set(MUTABLE)):
        # Same rule as `fail_on`: a dial set to a notch that does not exist
        # must say so rather than silently do nothing (DP-1).
        errors.append(f"luria.toml: `mute` names {name!r}, which is no "
                      f"mutable warning class (known: {', '.join(MUTABLE)})")
    for name in sorted(mute & fail):
        # Not a precedence question. A project cannot both enforce a check
        # and refuse to hear it, and guessing which it meant would make one
        # of the two settings a lie.
        errors.append(f"luria.toml: {name!r} is named in both `fail_on` and "
                      "`mute` — a class cannot be both enforced and hidden")

    for name, headline, lines in status_sections():
        if name in mute and name not in fail:
            continue
        if name in fail:
            # Name the dial that actually did it: `network = "require"`
            # promotes one class on its own, and blaming `fail_on` would send
            # a reader to a list their project never wrote.
            why = ("`network = \"require\"`"
                   if name == "source-unchecked" and name not in set(current().fail_on)
                   else f"`fail_on` names {name!r}")
            errors.append(f"{headline} — failing: {why} in luria.toml")
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
    check_form_text(errors)
    check_status_vocabulary(errors)
    check_reserved_prefix(errors)
    check_contracts(errors)
    check_view_dirs(errors)
    check_numbers(errors)
    check_alias_collisions(errors)
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
