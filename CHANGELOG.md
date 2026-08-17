# Changelog

Assembled from `changelog.d/` fragments on a cadence — never hand-edited
([ADR-002](record/decisions.d/ADR-002.md)).

<!-- luria-insert-here -->

## 2026-08-17

### Added

- An optional `statuses.yaml` in a scheme's directory, beside `tags.yaml` and
  shaped like it: which of [ADR-003](record/decisions.d/ADR-003.md)'s five statuses the scheme uses, and what
  each one means there. A record whose status the scheme does not declare fails
  the lint, and the meanings render above the index table they explain.
- `check_status_vocabulary`: a `statuses.yaml` key outside the closed five is
  an error. Narrowing the vocabulary per scheme is the point; extending it is
  what [ADR-003](record/decisions.d/ADR-003.md) bought and this does not sell it back.

### Documentation

- `docs/configuration.md` and `docs/adopting.md` describe the file, including
  the part that is easy to get backwards — the words stay closed, only their
  meanings and their per-scheme subset are yours.

### Added

- `broken-targets`: every relative markdown link target in record prose is
  resolved from where that prose *renders* — `link_base`, the same authority
  `luria link --fix` uses to write one — and reported when it does not exist.
  A warning by default, nameable in `[luria.lint] fail_on`.
- `target-ok:` acknowledges a target that deliberately resolves to nothing,
  such as a link into a build output that CI writes but does not commit. The
  first directive whose argument is a path rather than a code.

### Fixed

- The scaffolded decisions stub shipped two links that are dead in every
  project `luria init` creates: `[_template.md](_template.md)` and
  `[design-principles.md](../design-principles.md)`, both written relative to
  the stub's own directory rather than to `docs/decisions/`, where it renders.
- The scaffolded decision template wrote its supersession example as a link,
  `[ADR-NNN](ADR-NNN.md)`, so a placeholder read as a citation to a file nobody
  has. It is a code span now, matching the placeholder on the next line.

### Documentation

- `docs/directives.md` gains a `target-ok` section, and says why this one is
  about the path rather than the code every other directive governs.

### Added

- `inert-status`: a scheme where every record shares one status is reported.
  `active` is what `retired-citations` reads, so nothing is ever retired there
  and the citation checks cannot fire — the build is green because nothing is
  being judged rather than because nothing is wrong. A warning by default,
  nameable in `fail_on`. Exempt below ten records, for a `render = "document"`
  scheme, and for a scheme that declares exactly one status on purpose.

### Fixed

- **The published version and the git tag can no longer disagree.** 0.4.0 was
  tagged and released against a tree whose `pyproject.toml` still said
  `0.3.0`, so `python -m build` produced a *0.3.0* wheel and PyPI rejected it
  as a duplicate — after the GitHub release was already published, and with
  `twine check` and the cold-install smoke test both passing, because neither
  validates identity. `pyproject.toml` is bumped to 0.4.0, and the build job
  now asserts the built wheel's version equals the release tag (`v` prefix
  tolerated) before the publish job ever runs. The version was a
  hand-maintained projection of a source of truth kept in two places, which is
  what [DP-5](docs/design-principles.md#dp-5) predicts will drift; this is its
  rung-2 remedy — guard the property. Rung 1, deriving the version from the
  tag with `hatch-vcs`, is the better fix and needs `fetch-depth: 0` on the
  publish checkout, so it is left as a follow-up rather than bundled into a
  release-unblocking change.

### Fixed

- **`move_doc` lands a document under a temporary code, not a number.** "The
  next free number" is no more a fact inside a migration than it is on a
  branch: every operation plans against the tree as it is *now*, so two moves
  into one scheme both read the same highest number, and the second `git mv`
  silently overwrote the first. The move now mints a temp code
  ([ADR-049](record/decisions.d/ADR-049.md)) and `luria concretize` assigns the
  real number afterwards, at the serialization point — the same bargain
  `luria new` already makes, rather than a second allocator with its own
  arithmetic. The document ends up carrying both aliases: the code it migrated
  from, and the provisional one it wore in between.

- **`luria concretize` rewrites the anchor spelling too.** Its sweep was a
  case-sensitive replace, so it upgraded `ADR-tmp47fje` but walked straight
  past `#adr-tmp47fje` — leaving a live link pointing at a heading that no
  longer existed. Generated views are re-derived and were never at risk; a
  hand-written or migration-written link was.

- **`Pair` no longer returns a tail typed `int | str`.** The padded-number
  spelling and the opaque temporary identity are not the same kind of value,
  and collapsing them pushed the ambiguity out to every call site, which then
  had to test the type to learn which it had. Replaced with `old_parts`,
  `new_parts`, `new_is_provisional` and `new_anchor_tail`, so the padding
  question and the provisional question are asked separately — they are
  separate questions. A test now pins that a rename mirrors each citation's
  own spelling: `DP-004` stays padded, `DP-4` stays bare, the anchor stays
  bare.

### Fixed

- **`luria migrate`'s relink pass now stops where the hyperlink lint stops**
  ([#90](https://github.com/dmarx/luria/issues/90)). It walked every tracked
  file and linkified what it found there, while `luria link --fix` walks
  `doc_files()` — the fixer running wider than the linter checks, which is the
  disagreement `doc_refs` exists to prevent. The first real `move_doc`
  migration turned two moved documents into a 499-file working tree, 469 of
  them exactly `HEAD` plus markdown links written into Python comments,
  TypeScript comments and workflow YAML. The *sweep* still walks every tracked
  file, and should: "does this text spell a code that moved?" is a question a
  `.py` comment answers as truthfully as a document does. Only the linking half
  was scoped wrong.
- **A worded citation in a source file follows the move too.**
  [#89](https://github.com/dmarx/luria/pull/89) caught the prose-labelled form
  by the *address* it points at — which works in a document, where the citation
  is a link, and misses it entirely in code, where `(design-principles #17)` is
  normally unlinked: no code for the code swap, no address for the address
  swap. Eight of them survived the strata-g promotion, naming a document that
  had moved. The sweep now respells them using `find_refs`, the same recognizer
  that would have turned the phrase into a link in the first place, so the two
  cannot disagree about what counts as a reference.
- **A `formerly:` stamp is no longer reported as a dangling reference.** The
  reference scan is deliberately unmasked, so it read the alias the move had
  just written and reported `DP-017 resolves to no document` against the file
  the migration had created — one warning per moved document, every time, for
  the one construct whose entire purpose is to name a code that resolves to
  nothing. `sweep_text` already excluded `formerly:` blocks for the mirror
  reason (a later migration must not rewrite an earlier one's trail); the two
  exclusions now share `doc_refs.FORMERLY_RE`, because they are one exclusion.

### Fixed

- Every warning class `status_sections` can emit is now nameable in
  `[luria.lint] fail_on`, and a test asserts it over the whole vocabulary
  rather than one class. `legacy-spellings` had been emitted since rung one
  landed but was missing from `FAILABLE`, so a project asking to enforce it was
  told *"which is no warning class"* — the dial rejecting a notch it was
  already printing on, which is
  [DP-1](docs/design-principles.md#dp-1) inside the guard written to catch
  exactly that. The tuple entry itself rode in unremarked with the
  `narrow-titles` work; this is the test that would have caught the omission,
  and the changelog line it never got.

### Fixed

- **A generated view the project gitignores is no longer reported stale.** A
  project can point `[luria.paths] reports` at a build directory and publish
  the result as a CI artifact instead of committing it. A fresh clone then
  never has the file, so *missing* read as *stale* — and the remedy the
  failure printed, "regenerate and commit the result", is the one thing
  `.gitignore` forbids. Downstream that meant a docs job red on every commit
  for a day, on a check nothing could satisfy, which is
  [DP-1](docs/design-principles.md#dp-1) wearing a green hat: the tool refused
  and its explanation was impossible to act on. `--check` now excludes
  gitignored outputs from all three staleness kinds. Writing is unchanged —
  `luria index` still renders an ignored view, because *not committed* is not
  *not wanted*; that report is exactly what the artifact upload publishes.
- **`luria lint` and `luria index --check` share one staleness rule set.** They
  each had their own copy of the same three rules — stale view, orphan in a
  view directory, drifted README badges — and the fix above landed in one of
  them, so `lint` went on rejecting the identical tree the generator had just
  called current. That is the fixer/linter split this package exists to
  prevent, reproduced inside the package. `adr_index.staleness()` is now the
  single answer both consume; only the wording stayed with the linter, because
  a build log and a `--check` want different sentences. A test pins the
  invariant from outside: whatever one command says about a tree, the other
  says too.

### Fixed

- `luria migrate`'s `move_doc` no longer leaves links pointing at a moved
  document's old address. A move always crosses schemes, and a scheme's
  address is more than its code — a same-render move changes the directory, a
  cross-render move changes the whole shape (`page.md#anchor` ↔ `dir/CODE.md`).
  Swapping the code inside the old link fixed the label and left the target
  pointing at a file that does not exist, silently, with the lint clean.

  Citations of a moved document are now found by the ADDRESS they point at
  rather than by their label, replaced with the new code, and linked by the
  fixer from the resolver — the one place that knows how each scheme is
  addressed. A worded citation is rewritten too, label and all: keeping the
  label resurrects the problem, because the `#17` left behind is itself a
  reference the fixer re-links to the anchor the move just vacated.

### Added

- **`requires = [...]` on a scheme** — frontmatter fields it demands beyond the
  standard set. This is what makes a cross-scheme `luria migrate` move safe to
  automate ([ADR-040](record/decisions.d/ADR-040.md)): a document moved into a
  scheme whose template asks for fields the source never had cannot have them
  invented, so the move succeeds and the *lint* fails until a human supplies
  them. The machinery relocates a document; only a person vouches that it
  belongs.

### Changed

- **`origin:` is prose, like `summary:`** — references written there are linked
  by `luria link --fix` and checked by the lint. It was already *rendered* as
  markdown into a principle's metadata line, so a hand-written link displayed
  correctly while nothing maintained it: the worst of both, and a rot with no
  alarm. The reference machinery now reads a `PROSE_KEYS` set instead of naming
  `summary` in four places, and the membership rule is stated — a key is prose
  exactly when the generator renders its value as markdown. Deliberately not
  configurable: a project cannot make a field prose by declaring it so.

### Added

- **`luria migrate`** — execute a migration spec from `record/migrations.d/`,
  renaming a scheme or moving documents between schemes without losing the
  record's memory ([ADR-040](record/decisions.d/ADR-040.md), now Active). Two
  operations:
  - `rename_scheme` rewrites a whole code family, following the scheme's view,
    the remotes that mirror this project, and any extra config files named in
    the spec.
  - `move_doc` relocates one document to another scheme, auto-numbered in the
    target. With `strategy = "supersede"` it *copies* instead: the source stays
    where it is, tombstoned as `Superseded — by <new code>`, and is deliberately
    left out of the rewrite mapping so existing citations keep resolving to the
    original. That is the shape a promotion wants — the old document is still a
    true record of what happened, and only its *output* moved.

  `--dry-run` prints the plan and changes nothing; `--commit` commits and
  appends the migration to `.git-blame-ignore-revs` so blame reads through it.
  The sweep is mapping-driven, never prefix-driven: only enumerated pairs are
  rewritten, foreign composed codes (`SG-DP-4`) are masked because another
  project's namespace is theirs, and the spec file itself is never swept —
  its mapping is written in old spellings on purpose.

- **`luria new migration`** scaffolds a numbered spec, because execution order
  is information: a move can depend on a rename.

- **`luria/aliases.py`** — the alias map that migrations resolve through,
  derived fresh from `formerly:` frontmatter rather than hand-kept. Complements
  the concretization-flavoured alias resolution already in `doc_refs`: that one
  answers for temporary codes, this one for any renamed code.

### Added

- **`narrow-titles`**, a warning class for a title that names one of the
  project's own concrete nouns in a scheme whose documents claim to transfer.
  A principle stated about the artifact it was first noticed on stays true,
  renders, and passes every other check — it simply stops being cited, and
  nothing could see that. Two config surfaces: `[luria.lint] narrow_terms` for
  the project's vocabulary, and `titles_generalize = true` per scheme for the
  opt-in. **Luria ships no vocabulary**, so an adopter who has not configured
  one sees nothing at all — the class is absent, not empty. A word used in
  another sense is acknowledged in-document with `broad-ok:`, through the same
  directive parser as `inactive-ok:`, rather than by shrinking the vocabulary
  and stopping it protecting every other document.

- A principle carried in from strata-g, luria's first consumer: **"It's not
  mine, but I'll pick it up anyway"** — fix the debt you encounter whether or
  not it belongs to the task you came for, bounded by *repair, don't redesign*
  and *say what you picked up*. Added to this record and to the `template/`
  starter set.

### Fixed

- The `DP` scheme now uses `allocate = "merge"`, which the decisions scheme has
  had since [ADR-049](record/decisions.d/ADR-049.md). Without it two concurrent
  branches each took "the next free principle number" and both got the same one
  — a collision that had already happened here. A scheme that renders as a
  document is no less prone to it than one that renders as an index.

### Added

- **[DP-010](docs/design-principles.md#dp-10), "One decision, one thing."** A decision with two unrelated halves
  is one nobody can cite half of: the second half has no code, so nothing can
  point at it; superseding the first silently retires reasoning nobody meant to
  withdraw; and the alternatives section quietly covers whichever half the
  author found more interesting. The test is whether the two halves could have
  been decided differently.

  Earned on the second re-derivation, per the rule for adding one — three
  splits in a single session, each made for this reason and none of them by
  rule.

### Documentation

- Templates and the decisions stub now point at **`luria new <kind>`** instead
  of telling the reader to copy `_template.md` by hand. The copy instruction
  predates the command and had outlived it: `new`'s kinds are derived from
  config, so `luria new <kind>` works for a scheme the moment it is declared,
  and it assigns the identity — which hand-copying does not, and which is how
  two branches end up claiming one number. Which identity depends on the
  scheme's `allocate` mode, so the comment names the mechanism rather than one
  of its two outcomes: `filing` takes the next free number on the spot, `merge`
  mints a temporary code that `luria concretize` numbers where merges
  serialize. Fixed in both the shipped
  `template/` scaffold and this project's own record, so an adopter and a
  maintainer read the same instruction.

### Added

- **[ADR-058](record/decisions.d/ADR-058.md): luria is a truth maintenance system, and should say so.**
  Nobody could name the category, so every description reached for a new
  metaphor. The category exists and is from 1979. The documentation now leads
  with the mechanism — retract a premise, and the build names what rested on it
  — and gives TMS as the second sentence.
- `docs/concepts.md` — the model and its prior art.
- `docs/quickstart.md` — fifteen minutes ending in a real finding.
- `docs/schemes.md` — designing record families beyond decisions.
- `docs/cli.md` — every command, and the CI wiring including the version-split
  trap.
- `docs/api.md` — the Python surface, with stability marked.
- `docs/in-practice.md` — the three existing records compared: luria itself,
  strata-g, and a corpus project. What varied, what drove each choice, and
  the short list of things all three do the same way.
- `CONTRIBUTING.md`.

### Changed

- Every hand-written page rewritten from scratch: `README.md`,
  `docs/README.md`, `docs/adopting.md`, `docs/directives.md`,
  `docs/project-memory.md`. The README's four competing self-descriptions are
  replaced by one lead and one placement.

### Documentation

- An ADR (*Proposed*) for **the draft signal**: a draft pull request carrying a
  `Proposed` decision means the contribution itself is the question — the choice
  could only be weighed from the finished diff, the writeup argues the trade in
  both directions, and rejection is a live, cheap outcome. Merge flips the
  decision `Active`, close files it `Rejected`, and either way the record keeps
  the reasoning. Use it when the work exists to settle its own worth; skip it
  for agreed work, where a draft only slows the loop.

### Changed

- **A declared family replaces the shipped default** ([ADR-047](record/decisions.d/ADR-047.md)). `schemes`,
  `fragments`, `journals` and `remotes` are now yours entirely the moment
  you declare them: a record of RFCs and specs has no phantom ADR scheme,
  and a declared scheme's omitted `output` is genuinely unset — the view
  renders beside its sources, as the docs always said it would. Settings
  tables (`paths`, `code`, `lint`, `site`) still merge per key.

**Upgrading:** a config that declared *part* of a family while relying on
the rest from the defaults — say `[luria.schemes.DP]` alone, expecting `ADR`
to persist — now owns the family it declared. Add the missing entries
explicitly; the shipped template always declared its families in full, so
records scaffolded by `luria init` are unaffected.

### Added

- **`luria init --config my.toml`** ([ADR-048](record/decisions.d/ADR-048.md)): write the `luria.toml` you
  want and init installs it and scaffolds exactly that shape — a directory,
  template and view stub per scheme, templates per journal and fragment
  directory, and a docs index listing the views your record actually
  renders. A project that already has a `luria.toml` now gets *its* shape
  scaffolded rather than the template's. `--config` against a project that
  already has one is a hard error, never a silent skip.

### Fixed

- An index-rendered scheme with no `README.stub` is titled after itself
  rather than `# Architecture decision records` — the same defect the
  document render had, fixed the same way.
- A fresh `luria init` → `luria index` → `luria lint` runs clean again: two
  bare references in the template (`LU-ADR-048` in the docs index prose,
  `DP-1` in the principles stub) became visible to the scheme-driven
  reference detection and would have made every new scaffold start red. The
  three-command adoption loop is now a CI-run test, so the class stays
  closed.

### Changed (review round)

- `luria new` stamps an unnamed fragment with its filing moment
  (`20260812-021035.md`), the identity the devlog already uses, instead of
  naming it after the git branch — which collided the first time a branch
  was restarted after a squash merge and refiled ([ADR-036](record/decisions.d/ADR-036.md), v2). `--name`
  remains the explicit override and still reopens rather than duplicates.
- Generated views are marked `linguist-generated` in `.gitattributes`, so
  PR review collapses them by default and a contribution's diff reads as
  its sources. The views stay committed; only review's rendering changes.

### Proposed

- [ADR-049](record/decisions.d/ADR-049.md): schemes gain an `allocate = "merge"` mode — `luria new` issues a
  temporary code (`ADR-tmp47fje`) that is first-class on its branch, and
  `luria concretize`, run where merges serialize, assigns real numbers in
  merge order and records the temporary code as a permanent `formerly:` alias.
  Filed from the review discussion on [#76](https://github.com/dmarx/luria/issues/76); implementation to follow in its
  own PR.

### Changed

- **The published version is derived from the release tag** rather than a
  hand-written `pyproject.toml` field, completing the fix [#93](https://github.com/dmarx/luria/issues/93) began: `hatch-vcs`
  reads `git describe`, and the publish checkout fetches tags so there is
  something to describe against. [#93](https://github.com/dmarx/luria/issues/93)'s assertion that the built version matches
  the tag stays — deriving prevents the drift, the guard makes a recurrence loud.

### Fixed

- **A scaffolded project no longer starts with dangling references.** Three
  illustrative codes in shipped templates came from the real sequence and
  resolved to nothing in a fresh scaffold (`ADR-049` in two `_template.md`
  files, `ADR-001` in `CLAUDE.md`); they now use the `FX-` fixture prefix.
  Three more in the scaffolded workflows cited Luria's own decisions bare, so
  they read as the adopting project's decisions — they now compose as `LU-`.
  A fresh `init` + `index` + `lint` went from 5 unresolved codes to none.

### Fixed

- **A tag page names its own scheme.** Pages for a non-ADR scheme were headed
  "ADRs tagged `x`" and counted "N of M decisions", regardless of what the
  scheme actually holds — the same wart `DEFAULT_STUB` already avoids for the
  index.
- **A tag blurb keeps its capitals.** `str.capitalize()` lowercases everything
  after the first character, so any blurb running past one sentence, or naming
  anything capitalised, was silently downcased.

### Added

- **`[luria.schemes.X.tag_groups]`** — a scheme can declare which of its tags
  combine, and `luria lint` enforces it. A group takes `tags`, an optional
  `require` (`any`, `at-most-one`, `exactly-one`), and an optional
  `excluded_by` naming tags that forbid the group. Opt-in per scheme, so a
  record declaring no group is unconstrained. `tags.yaml` has always said what
  a tag *means*; this says which may appear together, for vocabularies that are
  axes rather than piles.

### Added

- `luria index` now renders `docs/configuration.md`, a reference for every
  `luria.toml` key generated from the config dataclasses themselves — prose
  from their docstrings, key tables from `dataclasses.fields()`. A key that
  exists in the schema is a documented row whether or not anyone remembered
  to describe it ([ADR-044](record/decisions.d/ADR-044.md)).

### Documentation

- The docs say what Luria can be configured *into*, not only what it ships
  as. `docs/adopting.md` gains "Shaping the record to your project" — worked
  examples for a second document family, a second journal, collocated views,
  fragment styles, `uid` remotes for citing things that are not Luria records
  (arXiv identifiers, ticket keys), and the `fail_on` enforcement dial.
- The README and the scaffolded `CLAUDE.md` now say plainly that the four
  shipped subsystems are a default rather than the machinery's fixed parts,
  and point at the configuration reference.
- Both documents state a limit rather than leaving it to be discovered:
  adding a scheme costs one table, but renaming one is still a manual pass
  ([ADR-040](record/decisions.d/ADR-040.md)).

### Added (examples)

- `examples/` holds four complete, working projects — RFCs beside specs, a
  collocated layout, three journals at three granularities, and `uid` remotes
  citing arXiv papers, Jira tickets and CVEs. `tests/test_examples.py` builds
  each one and runs the real `luria index` and `luria lint` against it, so
  these are configurations CI defends rather than prose ([ADR-045](record/decisions.d/ADR-045.md)).

### Fixed

- A `render = "document"` scheme with no `README.stub` no longer emits the
  heading `# Design principles` regardless of its prefix. A SPEC family
  rendered as a document is titled after itself.
- `luria init`'s scaffolded `docs/README.md` now lists the configuration
  reference, so a freshly initialized project passes `luria lint` on the first
  run as the adoption guide promises. An existing project upgrading will see
  one docs-index violation naming the missing entry; adding the line clears
  it.
- Two wrong claims in the new adoption guidance, both caught by building the
  examples: `active` selects from the closed status vocabulary and cannot
  extend it, and omitting `output` does not collocate the shipped `ADR`
  scheme (set it equal to `dir`). Both are now documented accurately and
  pinned by tests.

### Fixed (reference checking)

- **Every configured scheme is now linted and linked, not just `ADR`.**
  Reference detection matched three hardcoded patterns, so a project with an
  `RFC` or `SPEC` scheme got indexes, tag pages and `luria new rfc` — and no
  reference checking at all. `RFC-7` in prose was neither linked nor reported
  ([ADR-046](record/decisions.d/ADR-046.md)).
- The bare `DP-6` spelling is found. `CLAUDE.md` and the scaffolded template
  both tell contributors to write the bare code and let `luria link --fix`
  spell the target; for design principles that had never been true, because
  only the prose spelling (`design principles #6`) was matched. Applying the
  fix linked 38 references in this repository that had accumulated unseen.
- Cross-scheme references resolve in both directions — a file link into an
  index-rendered scheme, an anchor into a document-rendered one, each from
  the base where the citing text renders.

**Upgrading:** references your record has been carrying unchecked will become
violations in one pass. Run `luria link --fix` and read a sample of the diff
rather than trusting it wholesale.

### Fixed

- **Two acknowledgements stopped applying when the sequence reached [ADR-053](record/decisions.d/ADR-053.md).**
  The specimen lists in `ADR-014` and `tests/test_adr_index.py` borrowed a code
  from the real sequence, and a real fifty-third decision made it resolve. This
  is the second time — `ADR-032` went the same way — so `ADR-014` now records
  that trimming the list is the symptom fix and the `FX-` prefix is the cause
  fix.

### Fixed

- **A generated scheme's index no longer renders stray `{` and `}`.** The
  `README.stub` scaffolded for every non-ADR scheme carried `{{categories}}` and
  `{{table}}` — the `str.format` escaping convention — while `init.py`
  substitutes with `str.replace`, so the doubled braces survived into the file
  and every generated index carried two literal braces. The hand-shipped
  decisions stub uses single braces and was always correct, which is why this
  only affected schemes `luria init` generated.

### Changed

- **This repository's own record now allocates at merge** ([ADR-049](record/decisions.d/ADR-049.md),
  adopted): `luria new adr` mints a temporary code on the branch, and the
  push-to-main docs job runs `luria concretize` — with `concretize --check`
  guarding the same run. The shared `actions/generate` composite gained a
  `concretize` input, gated to non-PR events, and the scaffolded template
  workflow passes it the same way, so an adopter flipping `allocate =
  "merge"` gets the serialization-point wiring free.

### Added

- **The `legacy-spellings` warning class** ([ADR-040](record/decisions.d/ADR-040.md), rung 1 complete): a
  citation still written in a concretized code's old temporary spelling is
  reported with its remedy — `path:line ADR-tmpxxxxx → ADR-123` — and
  promotable to a failure via `[luria.lint] fail_on`. `luria link --fix`
  upgrades the spelling to the canonical code rather than engraving the old
  name into a fresh link. The in-tree steady state is zero, so a row means
  an in-flight branch merged after a concretization pass. The `formerly:`
  field itself is excluded — it is the alias record, not a citation.

### Decided

- [ADR-044](record/decisions.d/ADR-044.md) through [ADR-049](record/decisions.d/ADR-049.md) — the configuration reference, executable
  examples, scheme-driven reference detection, family-replacement merge
  semantics, config-planned init, and merge allocation — are now Active.

### Changed

- The decision index gains a real Title column. The middle column was one
  blob — the summary when present, else the title — under a header that
  said "Title", so any document with a summary showed its summary
  mislabelled. Rows now read code | title | summary | status, and a
  document without a summary gets an honestly empty cell rather than its
  title twice.

### Added

- **Merge-allocated schemes** ([ADR-049](record/decisions.d/ADR-049.md)): `allocate = "merge"` makes
  `luria new` issue a temporary code (`ADR-tmp47fje` — a tail that can never
  be read as a number) instead of claiming the next number from a branch.
  Temporary documents are first-class: indexed, linted, citable bare or as
  a wikilink, cross-referencable before they have a number.
- **`luria concretize`**: run wherever merges serialize, it assigns real
  numbers in merge order (commit time, the ordering the changelog collector
  already trusts), renames the files, rewrites every reference — history
  included, journals and the collected changelog too, so exactly one
  spelling of each code exists in the tree afterwards — and records each
  temporary code in the document's `formerly:` frontmatter.
- **Permanent aliases**: a code listed under `formerly:` resolves forever,
  in both the bare and wikilink spellings — for the citations no rewrite
  can reach: PR threads, commit messages, other repositories, and branches
  cut before concretization, which merge clean and modernize on their next
  `luria link --fix`.
- **`luria concretize --check`**: the trunk's guard — exits 1 naming any
  temporary code, for CI on the default branch.

The default is unchanged: schemes without `allocate = "merge"` number at
filing exactly as before.

## 2026-08-10

### Added

- **Wikilinks** ([ADR-025](record/decisions.d/ADR-025.md),
  [#9](https://github.com/dmarx/luria/issues/9)): `[[ADR-013]]`,
  `[[SG-DP-18]]`, `[[ARXIV-2403.05530|a label]]` — typed references the
  author asserts, resolved against everything the machinery can construct
  (local scheme codes including the bare `DP-3` spelling, document-scheme
  anchors, remote and uid-remote codes, issue numbers with no cue needed).
  `luria link --fix` consumes them into plain markdown links; an
  unresolvable wikilink is a lint violation with its causes named, because
  an explicit request deserves an explicit refusal.

### Fixed

- **The published front page shows its banner again**
  ([#70](https://github.com/dmarx/luria/issues/70)): `luria site` recognised
  a relative target after `](` and inside `<a href>`, but not inside
  `<img src>` — the form a README reaches its logo by, since markdown isn't
  parsed inside an HTML block
  ([ADR-005](record/decisions.d/ADR-005.md)). The image was neither staged
  nor redirected nor **counted**, so the run reported nothing to place while
  dropping one. Any project whose docs centre an image in raw HTML was
  losing it.
- **The graph view sits above the article, not below it**
  ([#71](https://github.com/dmarx/luria/issues/71)): Quartz stacks its
  sidebars under the content below 1200px, so on most windows — and on every
  phone — the graph the site exists for was the last thing on the page. It
  moves into the content column, directly under the title, uniformly at
  every width, with its parameters retuned for a column twice a sidebar's
  width. `luria site` now writes `quartz.layout.ts` as well as
  `quartz.config.ts`, so a project's layout is Luria's to decide rather than
  whatever the generator defaults to.
- **The landing page has a name.** The README is published as `index.md`,
  and a README that opens with a centred logo gives a site no title to read
  — so the front page was called `index`. It now carries the site title, and
  an alias so anything still pointing at `README.md` keeps resolving.

### Added

- **The published site can wear your brand**
  ([ADR-043](record/decisions.d/ADR-043.md),
  [#13](https://github.com/dmarx/luria/issues/13)): four optional
  `[luria.site]` keys — `icon`, `logo`, `logo_dark`, and a `theme` table that
  merges over the generator's palette by name. An unknown colour name is
  refused with the known ones listed rather than dropped, and a project that
  sets none of them gets exactly the site it had before.
  - **The favicon is rasterized during the build**, from whatever `icon`
    points at, using the `sharp` Quartz already depends on. Point it at the
    vector master: no derived PNG is committed, so none can drift
    ([DP-3](docs/design-principles.md#dp-3)).
  - **The logo replaces the site title** in the sidebar, baked once per
    theme. Artwork exposing a `--luria-ink` custom property is re-inked to
    each theme automatically; anything else needs `logo_dark` or is used as
    it stands.
- **Luria's own record wears the brainslug kit**: paper and ink from the
  kit's two colours, the horizontal lockup in the sidebar, and a new
  `luria_project_memory_icon.svg` — the mark on a paper badge, contours
  thickened so the line art still reads at 16px — as the favicon.

### Fixed

- **`actions/site` no longer fails the build for a project with no favicon**
  ([#73](https://github.com/dmarx/luria/issues/73)): the icon lookup used
  `ls … 2>/dev/null | head -1`, and under the step's own `set -euo pipefail`
  an unmatched glob ends the step before Quartz ever runs. Silencing a
  command's stderr reads as handling its failure and isn't. It could not
  bite this repository, which always configures an icon; it would have bitten
  the first adopter who didn't.

### Added

- **Another project's decision is cited as `LU-ADR-013`** — a registered remote
  prefix composed with that project's own code
  ([ADR-016](record/decisions.d/ADR-016.md)). One `[luria.remotes.LU]` entry makes
  it a **first-class reference**: `luria link --fix` writes the URL, `luria
  lint` fails on a bare one, and the citation scan no longer has to guess which
  project a code belonged to.
- **`luria remotes`** — what is configured and how each foreign reference
  resolves; `--refresh` discovers code→filename maps from a **public**
  repository into a committed `remotes.lock.json`; `--check` probes
  reachability. A remote that follows
  [ADR-013](record/decisions.d/ADR-013.md) needs no lockfile: the code *is* the
  filename.
- **Two remotes are registered, and their difference is the point.** `SG` is
  the pilot this package was extracted from — private, filenames not yet
  converted, so `--check` reports it *unverifiable*. `LU` is Luria itself,
  which the `luria init` scaffold cites instead of pasting GitHub URLs into a
  new project's templates, and which `--check` verifies for real. The mechanism
  is exercised by the package, not only by its tests — which is how the
  `*.stub` hole below was found.
- **A citation may name a document before its URL resolves**
  ([ADR-017](record/decisions.d/ADR-017.md)). `SG-ADR-032` 404s today and will land
  when strata-g's record is ported; naming the document is the durable half,
  and the whole set flips to `ok` in one `--check` run when it does.
- **`version:` is standard frontmatter for every scheme**, not just principles.
  Shown in the decision index only when it isn't 1, because a column of ones
  teaches nothing.

### Fixed

- **`*.stub` files are linted.** A stub is the hand-written prose of a
  generated view: the lint skipped it for not being markdown, and skipped the
  page it renders into for *being generated*, so a bare reference written there
  was invisible to both checks at once.
- **A code whose remote has been discovered is no longer guessed.** Once a
  lockfile has been read from a remote, its silence about a code is
  authoritative and the reference stays unlinked and reported.
- **`--check` no longer reports a private repository as a shelf of 404s.** It
  probes the repository once and says *unverifiable* — an anonymous 404 is not
  the claim "this document was deleted".

### Changed

- **Discovery reads public repositories over HTTPS only.** The local-clone
  option is gone: a resolution that depends on what happens to be on somebody's
  disk produces a committed lockfile nobody else can regenerate. A remote Luria
  can't read gets a `url` template, not a credential path
  ([ADR-016](record/decisions.d/ADR-016.md) supersedes
  [ADR-015](record/decisions.d/ADR-015.md)).

### Changed

- **The repository layout now states the read/write boundary**
  ([ADR-021](record/decisions.d/ADR-021.md),
  [#3](https://github.com/dmarx/luria/issues/3)): `docs/` holds everything a
  reader browses — prose plus every generated view — and `record/` holds
  everything a contributor files, each container inside carrying the `.d`
  suffix (`record/decisions.d/`, `record/principles.d/`,
  `record/changelog.d/`, `record/devlog.d/`). What you read at `docs/X` you
  file at `record/X.d`. `CHANGELOG.md` stays at the root, where convention
  puts it.
- A scheme's `output` is now separate from its source `dir`: the decision
  index and its tag pages render into `docs/decisions/` while the ADR files
  stay in `record/decisions.d/`, with link rebasing derived from the actual
  paths. A scheme with no `output` keeps the old collocated layout unchanged,
  so existing projects upgrade without moving anything.
- `README.stub` and `tags.yaml` live with the sources; a stub's links resolve
  from where the index renders.
- The journal's front page now inlines the current book's contents, newest
  entry first, above the shelf of older books — the newest writing is one
  click from the entrypoint instead of two.
- `luria init` scaffolds the new layout; the template's `docs/README.md` and
  `CLAUDE.md` explain the boundary.

### Added

- **A view directory holds only what the generator wrote** — anything else in
  one is a lint violation naming the file and the remedy. This generalizes the
  old orphaned-tag-page check to every view directory, and also catches a
  journal book stranded by a granularity change.
- [DP-9](docs/design-principles.md#dp-9) — structure is read before text, so
  affordances are spent deliberately: on shaping attention, on making
  locations discoverable, and as smells to read when they turn inconsistent.
  A structural signal beats a documentary one; the read/write boundary is the
  worked application.

- A new comment directive, `url-ok` — a link whose label is a composed
  foreign code (`SG-DP-18`) but whose URL is hand-written rather than
  constructed is reported as a warning until acknowledged, because a hand URL
  is frozen at writing time. Same shape and scope rules as every other
  directive; stale acknowledgements report themselves. Foreign codes only —
  [ADR-022](record/decisions.d/ADR-022.md) records why it does not widen to
  local codes or arbitrary hand-targeted links.

### Fixed

- The README badges' link target is derived from configuration instead of a
  hardcoded `docs/decisions/README.md`.

### Added

- **The record publishes as a browsable site**
  ([ADR-042](record/decisions.d/ADR-042.md),
  [#13](https://github.com/dmarx/luria/issues/13)): `luria site` stages the
  record as an Obsidian/Quartz vault — pages at their repository paths, plus
  a `quartz.config.ts` derived from `luria.toml` — and the new
  `actions/site` composite action builds it onto GitHub Pages. The citations
  the lint already guarantees are links become a graph, backlinks, full-text
  search and per-tag pages, none of it maintained by hand. Luria publishes
  its own record with the same action adopters get, and the scaffold ships
  the workflow ([ADR-029](record/decisions.d/ADR-029.md)). **One step cannot
  be scaffolded:** set Settings → Pages → Source to "GitHub Actions", or the
  deploy job fails with "Pages is not enabled" while the build stays green.
- **`[luria.site]`, and almost nobody needs it**: the site's title, its
  Pages URL, and the base a link falls back to when it points at a
  repository file the site does not publish all derive from `issue_url` for
  a GitHub project ([DP-3](docs/design-principles.md#dp-3)). Only `exclude`
  is genuinely per-project.
- **Decisions carry a record line on the site**: status, date, issue and
  `influenced_by`, rendered under the title. Those facts live in
  frontmatter, which a site renders as nothing — so without it a superseded
  decision reads on the web as current.

### Fixed

- **Generated index links are normalized**
  ([#67](https://github.com/dmarx/luria/issues/67)): a summary rebased for
  the view directory emitted
  `../../record/decisions.d/../../docs/design-principles.md#dp-2` — valid on
  GitHub, which collapses it, and a 404 under any generator that doesn't.
  Twenty links in this repo, invisible for as long as GitHub was the only
  reader. Run `luria index` to pick up the short form.

### Added

- **Published to PyPI** ([ADR-027](record/decisions.d/ADR-027.md),
  [#3](https://github.com/dmarx/luria/issues/3)): `pip install luria`.
  Publishing runs through GitHub trusted publishing — a `publish.yml`
  workflow whose `pypi` environment identity is the whole credential — on
  every GitHub release, gated by a cold-install smoke test that scaffolds a
  fresh project from the built wheel (`init → index → journal new → lint`).

### Fixed

- The scaffold ships inside the package (`luria/template/` in the wheel)
  instead of leaking a bare `template/` directory into `site-packages`,
  where it would have collided with any other package shipping one.
  `luria init` resolves the packaged location first and falls back to the
  repository top level in a checkout.
- A freshly scaffolded project now lints with zero warnings: the
  illustrative wikilinks in the template's CLAUDE.md no longer read as
  dangling codes.

### Added

- **Design principles are fragments, and `docs/design-principles.md` is
  generated from them**
  ([ADR-012](record/decisions.d/ADR-012.md)). One file
  per principle in `docs/principles/`, with frontmatter carrying a `version`
  (principles are living documents — two of Luria's eight are at v2, and now
  say so), `influenced_by` backlinks to the decisions whose experience produced
  them, `history:` for what changed between versions, and an `origin` note.
- **A scheme declares how its view is rendered.** `render = "index"` is the
  browsable shape — a table plus per-tag pages; `render = "document"`
  concatenates the bodies into one page for a set that is read as a whole. This
  is the first exercise of
  [ADR-006](record/decisions.d/ADR-006.md)'s claim
  that a second scheme is a config entry and a directory: no scanner changed.
- **`docs/principles/_template.md`**, and principles scaffolding in `luria init`
  — a fresh project now gets five seed principles as fragments rather than one
  hand-maintained document.

### Changed

- **`luria index` regenerates every scheme's view, not just the decision
  index**, so `luria lint`'s staleness check covers a newly configured scheme
  the moment it exists.
- **Links to a principle use a stable `#dp-N` anchor.** The generator emits
  `<a name="dp-N">` beside each heading, and `luria link` prefers it over the
  heading slug: a principle is a living document, so a heading-derived anchor
  stops resolving the moment the wording moves — silently, which is the
  fail-stale polarity [DP-3](docs/design-principles.md#dp-3) rules out. Projects
  whose principles are still one hand-written file keep the heading-slug
  fallback.

### Fixed

- **Tag pages no longer credit a script that doesn't exist here** — the
  generated header named `scripts/ci/build_adr_index.py`, a leftover from the
  corpus Luria was extracted from.

### Changed

- **`ADR-018` is at `v2`.** Its rejection of the endpoint-badge alternative
  cited [ADR-002](record/decisions.d/ADR-002.md)'s per-merge bot commit, which
  over-applied it — that hazard depends on a file being appended to at a marker
  and carrying assigned numbers, and a derived badge file has neither. The
  decision is unchanged; the reason it gives is now the real one (a baked-in
  URL is correct per commit, so a reviewer sees the count move in the diff).
- **Contributions to this repository go through a pull request.** A decision
  record is an interpretation of somebody's intent, and it should be read
  before it becomes what the project believes.

### Added

- **[ADR-019](record/decisions.d/ADR-019.md): a wrong *reason* is corrected in
  place and versioned; a changed *choice* is superseded.** Superseding over a
  bad argument retires a decision still in force and points every citation at
  an identical claim. "Never rewrite a body" objects to *silent* revision — a
  `version` bump with a `history:` note saying what the old version got wrong
  is the opposite of silent.

### Documentation

- **The docs no longer read as "these documents are frozen."**
  [Project memory](docs/project-memory.md) gains a section on what is and isn't
  revisable, with a table of the four shapes — choice changed, reason wrong,
  value reworded, consequence falsified — and **a live example of each from this
  repository**, because a rule a project has never applied to itself is a rule
  nobody has tested.
- **[ADR-001](record/decisions.d/ADR-001.md) is at `v2`.** Its traffic rule said a
  decision is "superseded but never rewritten", which reads as immutability and
  leaves no way to fix a wrong argument short of retiring a decision still in
  force. Narrowed to the case it governs — supersede when the *choice* changes —
  with `history:` recording the over-broad version. The rule about which layer
  holds what is unchanged.
- The decision templates, both index stubs, `CLAUDE.md` and the adoption guide
  now say the same thing, and the scaffold points a new project at Luria's
  worked examples by remote code rather than a pasted URL.

### Added

- **Per-scheme remote mappings**
  ([ADR-023](record/decisions.d/ADR-023.md),
  [#6](https://github.com/dmarx/luria/issues/6)): a remote's code families
  construct independently via `[luria.remotes.X.schemes.Y]` — `dir` for
  file-per-code schemes, `document` plus an `anchor` template for schemes
  whose documents are sections of one assembled page, or a `url` template.
  The anchor defaults to the stable shape Luria's document render emits
  (`dp-{number}`), so a remote on current conventions needs one `document`
  line: `SG-DP-18` now constructs to
  `…/docs/design-principles.md#dp-18` instead of a URL to a file that never
  existed.
- `luria remotes` labels which construction answered per code — "a document
  anchor, per the scheme" — alongside the existing rung labels.
- **uid remotes** ([ADR-024](record/decisions.d/ADR-024.md)): a remote can
  declare its references' shape outright — a `uid` regex, a configurable
  `delim`, and a `url` template that indexes the uid's capture groups by
  position — so `ARXIV-2403.05530` linkifies, lints and `url-ok`s like any
  foreign code. A uid is exact (never zero-padded), has exactly one
  resolution rung (the template; no lockfile, no convention), and an
  unconfigured prefix still never matches.

### Changed

- The lockfile's authority is scoped to what discovery can see: files. A
  document-scheme code absent from the lockfile still constructs — a section
  never appears in a directory listing, so its absence there is not evidence
  ([ADR-016](record/decisions.d/ADR-016.md) unchanged for file-per-code
  codes).
- The remote-level `dir` default moves from `docs/decisions` to
  `record/decisions.d`, following the read/write boundary
  ([ADR-021](record/decisions.d/ADR-021.md)) — defaults mirror Luria's own
  conventions. Remotes with an explicit `dir` are unaffected.
- The `url-ok` acknowledging `SG-DP-18` narrows to its residue: the
  construction now reaches the right document, and the annotation excuses
  only strata-g's legacy heading-derived anchor — the retirement loop
  [ADR-022](record/decisions.d/ADR-022.md) designed, exercised in tests in
  both directions.

### Added

- **Parallel execution** ([ADR-026](record/decisions.d/ADR-026.md),
  [#7](https://github.com/dmarx/luria/issues/7)): one ordered `pmap` over a
  thread pool, applied at three seams — render units in `luria index`
  (a scheme, a journal), per-file scans in the bare-reference lint, and
  per-URL probes in `luria remotes --check`. Results keep input order, so
  reports and rendered views are byte-identical at any width.
  `LURIA_JOBS=1` forces serial execution; `LURIA_JOBS=N` caps the pool.
  Measured: `remotes --check` 6.6s → 2.9s on this repo's citations; index
  and lint unchanged at today's cardinality (the seams there are structure
  for growth, as the issue asked).

### Added

- **A document can opt out of reference checking**
  ([ADR-033](record/decisions.d/ADR-033.md),
  [#37](https://github.com/dmarx/luria/issues/37)): `unlinted-file:` exempts
  a whole page from the bare-reference lint, wikilink handling and the
  reference-status scan — the blunt tool for a fixture-heavy or vendored
  document where a directive per code is maintenance without information.
  File-scoped only (backticks are already the narrow form; a bare
  `unlinted:` is reported as misuse), and the exemption is **counted**: the
  reference report lists every opted-out file and the lint prints the count,
  so the report stays a complete account of what nobody is checking
  ([ADR-007](record/decisions.d/ADR-007.md)).
- **Fixture codes get their own prefix**
  ([ADR-034](record/decisions.d/ADR-034.md),
  [#38](https://github.com/dmarx/luria/issues/38)): `FX` is registered as a
  remote whose every code resolves to the fixture-codes note in the
  directives doc, so an example like `FX-ADR-032` is a first-class reference
  that needs no `unresolved-ok` and can never collide with the real
  sequence. The template scaffold ships the same entry. Mechanizes what
  filing the real [ADR-032](record/decisions.d/ADR-032.md) taught the hard way, when five directives using
  that number as a specimen went stale at once.

### Added

- **A hand-filed journal entry heals itself** ([ADR-031](record/decisions.d/ADR-031.md),
  [#33](https://github.com/dmarx/luria/issues/33)): `luria index` populates an
  empty `created:` from the entry's path — the path is derived from the
  timestamp, so it is the one witness left — and the lint error names that
  remedy instead of asking a human to retype what the tree already states. A
  field that *disagrees* with the path is still an error: two witnesses in
  conflict is a judgement, not a mechanical fix.

### Changed

- **The status reports are committed views, and the README badges land on
  them** ([ADR-032](record/decisions.d/ADR-032.md),
  [#35](https://github.com/dmarx/luria/issues/35)): `luria index` renders
  `docs/reports/pending-decisions.md` and `docs/reports/reference-status.md`
  with every other view, the lint fails when they are stale, and each badge
  links to the report that explains its number. Everything a report names is
  a link — the flagged decision, every citing line, every pending code. The
  reports carry no clock (ages read "open since <date>"), because a committed
  view that embeds today's date goes stale at midnight on every branch at
  once ([DP-2](docs/design-principles.md#dp-2)). The default `reports` path
  moves from `build/doc-reports` to `docs/reports`; `luria reports` still
  writes them standalone for the CI artifact.

### Changed

- **Status enforcement is a dial** ([ADR-035](record/decisions.d/ADR-035.md),
  [#40](https://github.com/dmarx/luria/issues/40)), superseding
  [ADR-007](record/decisions.d/ADR-007.md)'s "warnings, never able to fail a
  build": the warn-first posture stays the default, and `[luria.lint]
  fail_on` promotes named warning classes — `retired-citations`,
  `unresolved-codes`, `hand-written-urls`, `stale-directives`,
  `pending-documents`, `unlinted-files` — to lint failures. Only
  unacknowledged rows ever fail, so `inactive-ok:` and its siblings become
  the way to state a deliberate exception to a rule with teeth. An unknown
  class name in `fail_on` is itself a lint error naming the vocabulary. The
  scaffolded `luria.toml` documents the knob.

### Changed

- **The CLI is a tiered eight commands instead of a flat eleven**
  ([ADR-030](record/decisions.d/ADR-030.md)): six for contributors (`lint`,
  `link`, `index`, `journal`, `remotes`, `init`) and two labelled as CI's
  (`reports`, `collect`) in `luria --help`, the README and the scaffolded
  CLAUDE.md. The surface had been one command per module — the package layout
  projected onto the interface — and three of the names claimed workflows
  nobody had.

### Removed

- **`luria badges`, `luria ref-status`, `luria pending`.** Each was already
  subsumed: `luria index` writes the badges and `luria lint` checks them
  ([ADR-029](record/decisions.d/ADR-029.md)); both status reports print as
  lint warnings and land in full in the `luria reports` artifact
  ([ADR-007](record/decisions.d/ADR-007.md), corrected to v2). Removed
  outright, not deprecated — a name that answers is a name that still
  exists, and there is no workflow to migrate. The modules keep their entry
  points (`python -m luria.ref_status --all` is still the interactive dig),
  and the `ref-status` and `pending` make targets are gone.

### Added

- **Luria: the project-memory machinery, extracted from
  [strata-g](https://github.com/dmarx/strata-g) as a reusable package.** The four
  layers ([ADR-001](record/decisions.d/ADR-001.md)), the
  fragment convention ([ADR-002](record/decisions.d/ADR-002.md)),
  the generated decision index
  ([ADR-004](record/decisions.d/ADR-004.md)), the
  reference-hyperlink lint
  ([ADR-005](record/decisions.d/ADR-005.md)), the
  retired-document and pending-decision reports
  ([ADR-007](record/decisions.d/ADR-007.md)), and the
  `inactive-ok` / `unexempt` directive vocabulary
  ([ADR-008](record/decisions.d/ADR-008.md)).
- **`luria` CLI** — `lint`, `link`, `index`, `ref-status`, `pending`, `reports`,
  `collect`, `init`. `luria lint` is the only one that can fail.
- **`luria init`** scaffolds the record into a project that has none, and never
  overwrites: a scaffolder that clobbers is one nobody dares re-run.
- **Everything project-specific is configuration**
  ([ADR-006](record/decisions.d/ADR-006.md)): paths,
  issue URL, code globs, fragment directories, and reference schemes. A second
  scheme (RFC, SPEC) is a `luria.toml` entry and a directory.

### Documentation

- **The name.** The package was very nearly `chester`, after Chesterton's Fence;
  [ADR-010](record/decisions.d/ADR-010.md) records that
  reasoning and [ADR-011](record/decisions.d/ADR-011.md)
  supersedes it — Luria, after *The Mind of a Mnemonist*, because the name should
  point at the faculty rather than at one failure it prevents, and because the
  book's cautionary half (a memory that never forgets and never abstracts becomes
  unusable) is the design brief.

### Fixed

- A literal `|` in a decision's `summary:` (or status note) no longer breaks its
  row in the generated index and tag pages — the renderer escapes cell content,
  and normalises an author's hand-escaped `\|` rather than double-escaping it
  ([#14](https://github.com/dmarx/luria/issues/14)).

### Added

- Fragment directories can declare a collection style
  ([ADR-028](record/decisions.d/ADR-028.md)): `append` (unchanged default —
  narrative order, marker at the end) or `changelog` — one `## <date>` batch
  per collection inserted right after the marker, newest batch first,
  fragments newest-first within it, and a stub-only batch emits nothing
  rather than an empty date heading. Luria's own changelog now collects in
  the changelog style.

### Added

- **Journals** — dated entries that persist, rendered into one generated book
  per period plus an index ([ADR-020](record/decisions.d/ADR-020.md)). Configure one
  with `[luria.journals.<name>]` (`dir`, `output`, `granularity` of
  `year | month | day`, `title`, `blurb`); entries live at
  `<dir>/yyyy/mm/dd/hhmmss.md`, so identity is the authoring timestamp and
  ordering is a property of the record rather than of commit order.
- `luria journal new "A title"` files an entry at the current timestamp,
  stepping forward a second on collision; bare `luria journal` reports what is
  filed and which books it renders to. `make journal` runs the latter.
- Two lint checks: a journal entry's path must agree with its `created:` and it
  must carry a `title:`; and `version:` must agree with `history:` — a bumped
  version with nothing saying what changed is a silent revision wearing a
  version number ([ADR-019](record/decisions.d/ADR-019.md)).

### Changed

- **The devlog is now a journal, not a collected view.** `docs/devlog.md` is
  replaced by `docs/devlog/README.md` and one book per month; entries are no
  longer consumed, so the view is regenerated by `luria index` and a hand edit
  to it is a lint failure. The seven existing fragments were migrated with the
  timestamps of the commits that added them.
- `luria init` scaffolds the journal: `template/luria.toml` gains
  `[luria.journals.devlog]`, and `devlog.d/_template.md` documents the entry
  shape rather than a branch-slug filename.
- `Config.is_historical()` is now the one place deciding which files are dated
  records and therefore out of scope for `luria ref-status`. It covers journals,
  whose entries are nested and which the previous `path.parent` test could not
  see.

### Documentation

- [ADR-002](record/decisions.d/ADR-002.md) and
  [ADR-012](record/decisions.d/ADR-012.md) corrected in place (v2, with `history:`):
  both cited the devlog as an example of a *collected* view. Neither choice
  changed — [ADR-012](record/decisions.d/ADR-012.md)'s distinction is precisely what
  [ADR-020](record/decisions.d/ADR-020.md) applied.
- `docs/adopting.md` gains a section on adopting into a project that already has
  a devlog, including how to recover fragments' real authoring times and the two
  traps in doing so (committer time zones, and links written for the old
  collected file's directory).

### Changed

- **The README's two record badges are counts now, not adjectives**
  ([ADR-018](record/decisions.d/ADR-018.md)). "generated index" and "versioned"
  were assertions that could never be false; they are replaced by **needs
  decision** (`Proposed` + `Deferred`) and **cited but retired** (retired
  documents still cited without an acknowledgement). Zero is green, non-zero is
  amber — neither number is a failure.
- **`luria pending` covers every scheme**, not just decisions. A `Proposed`
  principle is an open question in exactly the same way, and its rows are keyed
  by code (`ADR-012`, `DP-004`) rather than by ADR number.

### Added

- **`luria badges`**, and `luria index` regenerates the counts into a
  `<!-- luria:badges -->` region. The numbers are baked into static shields
  URLs — no endpoint to configure and no committed JSON — and `luria lint`
  fails when the region disagrees with the record. Baked in rather than served
  means the count is correct *per commit*, so a pull request shows its own
  numbers rather than the default branch's.

### Added

- **A cited code that names no document is now reported** rather than silently
  dropped ([ADR-014](record/decisions.d/ADR-014.md)). It shows up in `luria lint`,
  `luria ref-status` and the CI artifact. A warning, never an error — a typo,
  another project's decision and an illustrative code look identical to a
  scanner, and only a human can tell them apart.
- **`unresolved-ok:`** retires a deliberate one, at the same three scopes as
  `inactive-ok:` and with the validity check inverted: it is malformed when it
  names a code that *does* resolve. Both counts are printed on a clean run, so
  "nothing to report" can never mean "everything was silenced".
- **Badges** on the README: CI status, Python version, licence, and links to
  the two generated views. Plus the `LICENSE` file `pyproject.toml` has been
  claiming all along.

### Fixed

- **Ten stale references to the ancestor project's numbering**, left in ported
  docstrings — `ADR-187`, `ADR-188`, `ADR-123` and `ADR-158` each cited a
  decision that says the right thing in the wrong repo. One was a *link* to
  `adr-123-adr-status-vocabulary-docs-lint.md`, a file that has never existed
  here; the reference lint skipped it because it was already a link. All found
  by the new report on its first run.
- **A code inside a URL is no longer read as a citation.** Linking out to
  another project's decision is the correct way to name a foreign document, and
  the URL contains its code — without this, the `luria init` template failed
  its own scaffolded lint the moment its comments pointed at Luria's docs.

### Changed

- **`pip install luria` → `pip install git+https://github.com/dmarx/luria`** in
  the README and the adoption guide. The package is not on PyPI, and a README
  that ships a command which 404s is the drift this repo is about.

### Changed

- **A document's filename is its code and nothing else** — `ADR-013.md`, not
  `adr-013-a-documents-filename-is-its-code.md`
  ([ADR-013](record/decisions.d/ADR-013.md)). A slug in the filename is a third copy
  of the title that no tool reads and that a rename plus every inbound link is
  needed to correct, so it never gets corrected.
- **The title moves into a `title:` frontmatter field**, which the generated
  index and principles document prefer over the body's `#` heading. The heading
  falls back in — a project mid-adoption, or one that never adds the field,
  still renders a title rather than a blank cell.
- **Filename decoding lives on `Scheme`** (`filename()`, `number_of()`,
  `documents()`). Five separate places had grown their own regex for it.
  `number_of()` reads legacy `adr-010-a-slug.md` names too, so adopting Luria
  is not a rename-everything-first proposition.

### Added

- **`luria lint` reports a `title:` that disagrees with its body heading**, and
  a missing `title:`. The heading has to stay — someone opening the file alone
  needs one — so the two copies get a guard rather than a merge: rung 2 of
  [DP-3](docs/design-principles.md#dp-3), since rung 1 isn't available.
- **`tests/test_lint.py`**, covering the new check in both directions and
  across both schemes.

<!-- One fragment per contribution (ADR-002). -->

### Changed

- The reference-status report stops calling a Proposed document "retired"
  ([#63](https://github.com/dmarx/luria/issues/63)): the page is titled "Reference status", its first section —
  "Documents cited while not in force" — spells out the *not yet* vs *no
  longer* split, exclusions read as "Not listed: N citations someone has
  already vouched for", per-code tallies say which sites are marked
  deliberate instead of "acknowledged elsewhere", and counts pluralize as
  prose. The README badge follows: "cited, not in force".

### Changed

- **Both CLAUDE.mds are maps now, not copies**
  ([ADR-037](record/decisions.d/ADR-037.md), part of
  [#45](https://github.com/dmarx/luria/issues/45)): a short list of links to
  the authoritative docs, the invitation to run `luria --help` for the
  current API, and three one-line ground rules — plus the statement that
  when the file disagrees with the docs or the CLI, the file is the one
  that's wrong. The restated command block and doctrine walkthroughs are
  gone; they had drifted twice in one week, exactly as
  [DP-3](docs/design-principles.md#dp-3) predicts for hand-maintained
  copies. The scaffolded `template/CLAUDE.md` gets the same treatment,
  mapping an adopting project instead of this one.

### Removed

- **The Makefile** ([ADR-038](record/decisions.d/ADR-038.md)): its "run what
  CI runs is `make <target>`" doctrine stopped being true when
  [ADR-029](record/decisions.d/ADR-029.md) moved the docs jobs into composite
  actions, leaving one `make test` line wrapping pytest and a set of targets
  that restated CLI one-liners and drifted twice in a week. ci.yml runs
  pytest directly; `luria --help` is the one list of what you can run.

### Added

- **`luria init` speaks up about a kept CLAUDE.md**: it never overwrote
  existing files, but the one file an agent reads first deserved more than a
  silent skip — when CLAUDE.md exists, init now prints a pointer at the
  scaffolded map shape (links + `luria --help`) and suggests asking your
  agent to fold it in. The recommendation goes to stdout, where permission
  isn't needed; the file is never touched.

### Added

- **`luria new [kind]` scaffolds an entry anywhere the record takes one**
  ([ADR-036](record/decisions.d/ADR-036.md),
  [#42](https://github.com/dmarx/luria/issues/42)): the journal by default,
  any configured scheme by prefix (`luria new adr` copies `_template.md` to
  the next free number and stamps the date), any fragment directory by name
  (`luria new changelog` names the file after the branch). It computes only
  what a machine can know, prints the path, and leaves the content to a
  markdown-aware editor; `--title`/`--status`/`--summary`/`--tags` exist for
  tools driving the CLI, never as requirements. Kinds derive from
  `luria.toml`, so a new scheme scaffolds for free. This fragment and its
  devlog entry were created with it.

### Removed

- **`luria journal`** — subsumed by `luria new` and removed without a shim
  ([ADR-030](record/decisions.d/ADR-030.md)); `python -m luria.journal`
  remains for the interactive look at what is filed.

### Changed

- **The CLI is driven by Fire** ([ADR-039](record/decisions.d/ADR-039.md),
  proposed — this ships as a draft PR): every command is a plain typed
  function (`<module>.run`), flags and help derive from signatures and
  docstrings, and the hand-rolled dispatcher plus every module's argparse
  layer are deleted (~150 lines). Failure is signalled by `SystemExit`
  only — Fire prints return values, and a CI gate's exit code is not
  output. Every existing invocation spelling (`--fix`, `--check`,
  `--commit`, `new adr --title …`) parses identically; help output becomes
  Fire's house format. `fire>=0.7` joins PyYAML as a runtime dependency.

<!-- One fragment per contribution, named changelog.d/<branch-slug>.md. Keep
     only the headings that apply; delete the rest. Collected into CHANGELOG.md
     on a cadence, never on every merge (ADR-002).

     No user-facing changes? Replace everything with a single HTML comment
     saying why. A stub collects to nothing, which keeps "every contribution
     files a fragment" enforceable without inventing an entry. -->

### Added

- [ADR-040](record/decisions.d/ADR-040.md): the migrations doctrine — how schemes
  get renamed and documents move between them (mapping-driven sweeps,
  `formerly:` as identity, full rewrite including history, a rung ladder from
  prose relabel to `luria migrate`). Doctrine only; the machinery lands per
  the ladder, starting with rung 1.
- [ADR-041](record/decisions.d/ADR-041.md): the bug protocol — a defect enters
  the record as an issue carrying a minimal working example before any fix,
  the response is classified on the [ADR-035](record/decisions.d/ADR-035.md) ladder, and the fix PR turns the
  MWE into a regression test. First live run: the journal link-frame bug.
- [DP-010](record/principles.d/DP-010.md): defaults follow the failure mode
  — guards ship on and are opted out of visibly at the site; disclosures
  ship off and are opted into by a config line; either deviation is written
  down where it applies.

### Documentation

- Both CLAUDE.mds (this repo's and the template's) rewrite the hyperlink
  ground rule as "never hand-write a link target" — bare codes and
  `[[CODE|label]]` wikilinks, with the fixer owning every target because
  only it knows which render frame a target must resolve in — and add a
  fourth ground rule: a guard that keeps catching the same mistake is a
  bug report about the workflow, and the fix belongs upstream of the guard.
  Prompted by four wrong-frame links in one day, all hand-written, all
  wanting a prose label the (previously undocumented) labeled-wikilink
  syntax already provides.
- Both CLAUDE.mds now open with a read-this-first directive: load the full
  design-principles document into context before anything else — the
  principles are the one part of the record the map assumes rather than
  links.

### Added

- **Drop-in CI for the record** ([ADR-029](record/decisions.d/ADR-029.md)): `actions/generate` regenerates the
  views, commits and pushes them as the bot, and outputs the SHA a checking
  job must read (fork PRs get a warning and an un-regenerated SHA instead of a
  403); `actions/lint` runs `luria lint` and uploads the status reports. The
  `luria init` template workflow is now the full recommended shape built from
  those actions — it previously scaffolded a verify-only lint, handing every
  new adopter a gate with nothing keeping it satisfied — and luria's own
  `ci.yml` runs the same two actions by local path, so the scaffolded workflow
  is the one this repository lives on ([ADR-009](record/decisions.d/ADR-009.md)).
- `luria/ci.py`: luria notices when it is being read in a build. Detection is
  crude on purpose (`CI` plus the vendor variables) and only ever changes what
  is *said* — no write and no exit code depends on it.

### Fixed

- **The staleness remedy now names the half that matters: the output has to be
  committed.** `stale — run luria index` is complete advice in a working copy
  and half an answer in a build. Under CI the message names both legitimate
  routes — regenerate locally, or give CI a generation job — and warns against
  the specific broken shape: the generator dropped into a checking job with
  nothing committing its output, which discards the result *and* leaves a
  following `luria lint` comparing the generator against itself
  ([#21](https://github.com/dmarx/luria/issues/21), [#23](https://github.com/dmarx/luria/issues/23)).
- Bare `luria badges` says on **stderr** that it only printed. As a `- run:`
  step it looked exactly like a write and exited 0 having done nothing
  ([DP-1](docs/design-principles.md#dp-1)). Stdout is unchanged, so redirection still works.

### Documentation

- [`docs/adopting.md`](docs/adopting.md)'s CI section leads with the scaffolded workflow and the
  two actions, and keeps what stays in the caller's hands: the fork-safe
  checkout ref (a fork's head branch does not exist in the base repo — the
  checkout fails before any push guard can help), the `needs:` + `sha` handoff
  (a `GITHUB_TOKEN` push does not retrigger workflows), and the warning never
  to write GitHub's skip markers into a commit message you author.
