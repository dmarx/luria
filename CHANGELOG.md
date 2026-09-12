# Changelog

Assembled from `changelog.d/` fragments on a cadence — never hand-edited
([ADR-002](record/decisions.d/ADR-002.md)).

<!-- luria-insert-here -->

## 2026-09-07

### Changed

- A remote's code now relates to a set of *named URIs* rendered through one
  template vocabulary ([ADR-067](record/decisions.d/ADR-067.md)): `url` and `pin_url` are the short
  spellings of `uris.read` and `uris.bytes`, a `[luria.remotes.X.uris]`
  table names further relations, and {filename} is an ordinary template
  variable fed by the discovered lockfile map, authority semantics
  included — so a GitLab-style raw scheme with slug filenames is two
  template lines. The GitHub blob→raw rebase regex is gone, replaced by
  shipped default templates; the one behavioral change is that a `url`
  template rendering a blob-shaped URL no longer implies pinnable bytes —
  declare `uris.bytes` (or `pin_url`) instead.

### Fixed

- `luria lint` checks the standing of references to merge-allocated
  documents. `ref_status` loaded a scheme by number and matched codes by
  digits, so a temporary code ([ADR-049](record/decisions.d/ADR-049.md)) was neither a document nor a citation
  site: for the whole life of the pull request that files them, citations
  among merge-allocated documents went unchecked, and the findings surfaced
  only after the merge that concretized the codes — on the trunk, in files
  nobody was editing ([#203](https://github.com/dmarx/luria/issues/203)). `luria link --fix` had handled temporary codes
  all along; the two halves of the reference system disagreed about whether a
  temporary code is a code, and only one of them said so.

### Changed

- Five source comments cited `ADR-tmpstat1`, a temporary code that never
  named a document; the decision they meant is [ADR-085](record/decisions.d/ADR-085.md). The checker above
  found them on its first run.

  A record that spells out the temporary shape in prose — a decision that
  defines it, a README transcript, a CLI page — has illustrative codes that
  now resolve to nothing, and each wants an `unresolved-ok:` acknowledgement
  once. File them with the upgrade, not before: on the older version the
  directive excuses nothing and is reported stale.

### Fixed

- `LU-#193` linked to the *citing* project's issue 193, not the remote's. The
  prefix was inert prose and the number resolved through the local
  `issue_url`, producing a well-formed link to a different project's issue of
  the same number — which in a mature tracker exists and is about something
  else. No check could see it: the target resolved, so `broken-targets` was
  satisfied ([#194](https://github.com/dmarx/luria/issues/194)).

### Added

- `[luria.remotes.X] issue_url`, defaulting to the GitHub convention for a
  remote with a `repo`. A remote reached by a `url` template alone — an arXiv
  identifier, a ticket key — has no tracker, so its `X-#7` resolves to nothing
  and is left bare rather than pointed at the local one.

### Changed

- Every document code in the site's record line now carries the document's
  title. A code alone asks the reader to already know the record — `LIT-141`
  says nothing about what it is — and being followed by someone who does not
  yet know where it goes is the whole point of a backlink.
- A field with several values gets a bulleted list, one item per line, instead
  of values separated by center dots. With a title after each code the items
  are long enough that a line each is the only thing that reads. A single
  value stays plain: a one-item bullet is a bullet about nothing.

### Fixed

- A title containing markdown syntax is escaped where it is spliced. This
  project's own [ADR-025](record/decisions.d/ADR-025.md) is titled ``Wikilinks: `[[CODE]]` is a typed
  reference``, and two decisions cite it — unescaped, both their pages asked
  the resolver for a document called `CODE`. `|` is escaped too, which would
  otherwise end the table cell.

### Changed

- The site's record line is a two-column table instead of one line of
  `**Label** value` fragments separated by center dots. It read acceptably at
  three facts and badly at eleven — `LIT-140` ran to a paragraph of bolded
  fragments a reader had to parse before they could scan. The center dot keeps
  its job inside a cell, where it separates peers.

  The line is composed only when staging the site, so nothing about how the
  record reads in the repository changes.

### Added

- A `<!-- luria:site -->` README region, rewritten by `luria index` beside the
  badges and the citation block, carrying the URL `luria site` publishes to.
  Derived from `Site.base_url`, which needs no configuration for a GitHub
  project ([#197](https://github.com/dmarx/luria/issues/197)).
- `unlinked-site`, a lint finding for a record that publishes a site its README
  never names. Satisfied by the URL appearing anywhere in the README, prose
  link included — it is about the front page, not about the marker.
- `[luria.site] publish`, defaulting true. A record that lives only in its
  repository sets it false and the finding goes quiet.

### Changed

- The region machinery — markers, staleness-safe rewrite, README path — is one
  implementation in `readme.py`, read the same way by `badges`, `citation` and
  the new region. It had been copied three times and had already drifted in
  spelling.
- This project's README links its own site from that region instead of a
  hand-typed line, which had been sitting immediately below the region
  `luria index` rewrites.

### Fixed

- The site's record line named a document's status **twice** on every page of
  every scheme that declares a status vocabulary — which, since [#181](https://github.com/dmarx/luria/issues/181) requires
  the declaration, is every record. `record_line` had always rendered it
  through `statuses.display`; the generic vocabulary loop then rendered it
  again as an ordinary declared field. The dedicated path stays, because it is
  the only one that composes `Superseded — by X; note` out of the fields
  around the word.
- A relation with a declared `converse` rendered **twice** on the same line —
  once humanised from the field it holds, once as a backlink labelled with the
  raw field name (`**Extends** LIT-141 · … · Cited as `extended_by` by
  LIT-141`). Backlinks exist for the direction the site would otherwise lose,
  and storing the converse removes the loss. Suppressed by what the page
  actually holds rather than by the declaration alone, so a record with a
  one-sided relation still shows the edge it has while the lint reports it.

### Added

- `statuses.FIELD`, naming the frontmatter key a scheme may back with a
  vocabulary, so the two places reasoning about it as a declared field agree.

### Added

- **`luria upgrade`** — one-shot commands that carry a record across a
  version boundary. Each is temporary by construction and states what has to
  be true before it is deleted; `luria upgrade` with no argument lists them
  with those conditions. Nothing under it goes through config loading, since
  the config an upgrade repairs is the one the new version refuses to load.
- **`luria upgrade statuses`** writes the `status` declaration and the
  vocabulary file into a record that predates them.
- Lint class `spent-upgrades`: an upgrade this record no longer needs is
  dead code upstream, so the record says so rather than waiting for someone
  to remember.

### Changed

- **`status:` is a controlled vocabulary a scheme declares**, not a built-in
  axis. `[luria.schemes.X.fields.status] vocabulary = "statuses"` wires the
  field to `statuses.yaml`; the words are the project's, and every check,
  legend and page follows them.
- **A scheme that declares no `status` vocabulary is a lint violation**,
  naming `luria upgrade statuses`. An unchecked field looks exactly like a
  clean one, which is the failure the declaration exists to remove.
- The bespoke status check is gone: one bad word is one finding, raised
  where every other controlled field is checked.
- A `status:` still carrying its `— note` is read apart at the boundary
  where frontmatter is read for checking, so it is reported once — by the
  check whose finding names the repair.
- The record page lists each scheme's status words and cites the file they
  come from, instead of saying "nothing beyond the standard fields".

### Documentation

- `examples/README.md` and the shipped `luria.toml` explain that `active`
  picks the in-force word *from* the vocabulary rather than adding one.

### Added

- `luria lint` reports a prose field (`summary:`, `origin:`, `status_note:`)
  that still says what the scheme's `_template.md` says — the form's words,
  not the document's. Write it, or drop the key; an absent summary falls
  back to the title.

### Changed

- `luria new` no longer copies the form's placeholder into a prose field
  the caller did not fill (`summary:`, `origin:`, `status_note:`); the key
  is dropped and the comment above it stays as the instruction.

### Added

- A reference field may declare its `converse` — the field holding the same
  relation read backwards (`extends` / `extended_by`). `luria link --fix`
  makes the two sides agree, so a relation is stated once on whichever
  document the author was holding.
- A relation naming *itself* as its converse is what symmetry is, so
  `compared_against = { …, converse = "compared_against" }` gets the
  behaviour that used to be hard-wired to a chain's `sibling`.
- **Removing a relation propagates too.** `--fix` reads the last committed
  state to tell a write the other side has not caught up with from a
  deletion the other side is stale about, and writes or prunes accordingly.
  A relation withdrawn on one side and asserted on the other is reported and
  left alone.
- **`luria link --fix` never makes `luria lint` worse.** A repair that would
  move a document from satisfying its scheme to violating it — a
  back-reference added into a field group that permits one of two fields, a
  stale one removed out of a field the status requires — is not applied. The
  pair stays one-sided and the finding names both rules that disagree.
- Lint class `one-sided-relations`, naming for each finding whether the
  fixer will write the missing side or remove the stale one.

### Changed

- **A relation with no declared `converse` is now left entirely alone** —
  nothing completed, nothing reported. A project relying on the previous
  release's symmetric completion must add `converse` to the field's
  declaration to keep it; the change is otherwise silent.
- `broken-chains` keeps only the cycle. The one-sided finding moved to
  `one-sided-relations`, because a declared pair is one-sided or it is not,
  whether or not a chain walks it.
- A chain reads both its relations through the converse union, so a
  one-sided declaration renders correctly before the fixer runs.

### Documentation

- `docs/cli.md` covers `converse`, the add-versus-remove table, what `--fix`
  will not touch, and why an undeclared relation is left alone.

### Added

- `luria link --fix` now completes a chain's symmetric `sibling` relation:
  where one document declares a comparison and the other does not, the
  missing back-reference is written into the other document's frontmatter.
  You declare a comparison once, on the document that ran it. The directed
  `relation` is never mirrored.
- `luria link --links-only` restricts `--fix` to link rewriting — the
  behaviour it had before completion existed.

### Changed

- The `broken-chains` one-sided-comparison finding now names its remedy,
  the way `legacy-spellings` does.

### Documentation

- `docs/cli.md` covers the two repairs `luria link` performs and why
  `PATHS` narrows only the first of them.

### Added

- `[luria.chains.X] annotate = "field"` shows a second field beside each
  step's status on a chain page. A record can carry an axis the status cannot
  express — how far the *field* has converged, as against what the record
  itself asserts — and without this the page renders an agreed trunk and a
  disputed branch identically, which is the one distinction a line of work
  exists to show. Read through the contract, so a field with a `default`
  shows its default rather than a blank; a field the scheme does not declare
  is a config error ([#173](https://github.com/dmarx/luria/issues/173)).

### Added

- `required_when` is validated at load against what the scheme can actually
  say: an `on` the scheme cannot name is refused, and so is a value outside a
  closed set (the status vocabulary, or a vocabulary-backed field). A
  misspelled field and a miscased status used to be accepted and silently
  never hold — the outcome eager validation exists to remove ([#172](https://github.com/dmarx/luria/issues/172) review).

### Changed

- A condition is compared against a field's **effective** value, resolved
  through the compiled contract rather than read raw. A vocabulary field with
  a `default` is never absent ([ADR-076](record/decisions.d/ADR-076.md)), so a condition naming its default now
  holds for the documents that omit it; a list-valued field matches on any
  element. `RequiredWhen` is pure data again, so `config` no longer reaches
  into `statuses` ([#172](https://github.com/dmarx/luria/issues/172) review).
- [ADR-071](record/decisions.d/ADR-071.md)'s "a Superseded document names its successor" is a `required_when`
  on the built-in `superseded_by` field instead of a hand-written branch in
  `check_frontmatter`. One implementation, and the built-in gets the contract
  wording, provenance and record-page mention for nothing ([#172](https://github.com/dmarx/luria/issues/172) review).
- `docs/record.md` names the built-in conditional once, alongside the standard
  fields. `describe()` still lists only what a scheme declares *beyond* them.

### Changed

- A chain page renders the status *value*, not the composed
  `Superseded — by [X](…); note` display form. The successor is the next line
  on the page and the note is the argument this view leaves on the document —
  and composing it dragged a link authored in the source's frame onto a page
  that renders elsewhere, which is a thing to avoid rather than a thing to
  rebase. `status`, `superseded_by` and `status_note` being three fields is
  what makes the narrower reading available ([#171](https://github.com/dmarx/luria/issues/171)).

### Fixed

- A chain page's links pointed into the scheme's view directory, which for an
  index-rendered scheme holds a README and tag pages and never a page per
  document — so every rendered link resolved to nothing. Found by the first
  real corpus; the fixtures had checked the shape of a target and not its
  existence ([#171](https://github.com/dmarx/luria/issues/171)).
- A status note carrying a link is rebased on a chain page, as it already is
  on the index and tag pages ([#171](https://github.com/dmarx/luria/issues/171)).
- A chain page registers in `is_generated`: its job is to show a line
  including its retired steps, so scanning it reported every superseded
  document in every chain ([#171](https://github.com/dmarx/luria/issues/171)).
- A chain's relation fields are no longer read as citation sites. The step a
  document extends is superseded by construction, so `extends:` produced one
  "cites a retired document" finding per retired step, at the field whose
  whole job is to name it. Prose is unaffected ([#171](https://github.com/dmarx/luria/issues/171)).

### Added

- `[luria.chains]`: a declared relation is walked transitively and rendered
  as sequences on one page — the spine directed, optional symmetric
  cross-links alongside. Order, title and status only: the field carries the
  sequence, the prose keeps the argument ([#171](https://github.com/dmarx/luria/issues/171)).
- `broken-chains`: a succession that loops, and a comparison only one side
  declares. Both structural, neither acknowledgeable.

### Added

- `required_when`: a field can be required by another field's value —
  `required_when = { status = ["Proposed", "Deferred"] }` — so a record can
  say not only what it believes but what would change its mind. One field
  against a set of literal values, deliberately not an expression language
  ([#170](https://github.com/dmarx/luria/issues/170), [ADR-082](record/decisions.d/ADR-082.md)).
- The `fields` table accepts a declaration with no `vocabulary`: a rule about
  when a field applies needs no type, so a table declaring only
  `required_when` is a plain field.

### Added

- `template-drift`: a scheme's `_template.md` is now checked against the
  scheme's own contract — a `many` field scaffolded as one value, a scalar one
  scaffolded as a list, a required field the form never prompts for. Shape
  only; placeholder values stay placeholders. The template was the one file
  stating the schema that nothing compared to it, and it is the file every
  document is a copy of ([#169](https://github.com/dmarx/luria/issues/169)).
- `luria new` accepts a scheme's declared fields as flags — `--source
  LIT-134,LIT-140` — and writes each in the shape its contract declares. An
  undeclared flag is refused by name ([#169](https://github.com/dmarx/luria/issues/169)).

### Fixed

- `luria new` dropped a field the template did not already scaffold: the
  substitution matched nothing and the command reported success. It is
  appended to the frontmatter now ([#169](https://github.com/dmarx/luria/issues/169)).

### Fixed

- `source-mismatch` no longer reports a disagreement on HTML escaping.
  Metadata APIs serve XML and JSON, so a title arrives escaped — arXiv's Atom
  feed returns `Better &amp; Faster` — and comparing that against a title a
  person typed reported a mismatch on the ampersand. Entities are unescaped
  at the fetch rather than at the comparison, so the lockfile records what
  the title is rather than markup.

  Found by running the check on a real corpus of 186 notes, which is the only
  way it would have been found: the fixtures all had ASCII titles.

### Added

- `source-mismatch`: an identifier whose upstream title is not the one the
  document records. A citation can resolve perfectly and still name a
  different paper, and nothing looked — 53 of 139 arXiv identifiers in one
  record pointed at unrelated work and stayed green for two years.
- `source-unchecked`: an identifier nothing has verified. The case that
  matters most, since a citation is likeliest wrong in the minutes after it
  is typed, which is exactly when no lockfile has an answer for it.
- `[luria.lint] network` — `auto` (default) lets the lint ask about what the
  lockfile cannot answer, `never` is the hermetic build, `require` makes not
  being able to ask a finding, so a green CI run means the references were
  verified rather than remembered.
- `luria remotes --resolve` fetches the title behind every identifier and
  records it in the lockfile, which the lint then answers from — and adds to,
  so what it learns is committed and reviewable.
- `uris.title` and `title_re` on a remote say how to ask and how to read the
  answer. One line each for arXiv and Crossref, both in the CLI docs.
- `source-ok:` acknowledges a deliberate disagreement — a nickname the
  project prefers, a trimmed subtitle, a title that changed between versions.

### Changed

- The lockfile gains a `titles` section, preserved across `--refresh` and
  `--pin` like the others, and written by the lint as well as read.
- Fetch failures are distinguished by HTTP status: 404/410 is upstream saying
  the identifier names nothing — an answer, recorded and not retried — while
  429/503 is retried with backoff and, if it persists, reported as unchecked
  rather than written down as an absence.

### Added

- `uniform_share`, a per-scheme threshold for `inert-status`. The check
  reported only on unanimity; a scheme at 133/144 one status is a field a
  reader can predict without looking, and eleven exceptions were enough to
  silence it permanently. Defaults to `1.0` — the previous rule exactly — so
  no existing project's output changes.

### Changed

- An `inert-status` row shows the distribution behind the modal status:
  `SOTA: 133/144 at Active — 8 Proposed, 2 Superseded, 1 Deferred`. A finding
  about a proportion that prints only a proportion invites the reply that
  exceptions exist.
- `uniform_ok` acknowledges by the same rule, so what is acknowledged and
  what would have been reported cannot drift apart.

### Fixed

- A remote code in a reference field is read whole. `superseded_by:` naming
  a uid-remote document — `ARXIV-2110.08058`, `DOI:10.1145/3600006` — was
  truncated to a scheme-shaped prefix (or to nothing) before the contract
  check saw it, and failed as "names no scheme or remote" while the same
  code in prose resolved. The check always meant to admit a remote code;
  now its reader does.

### Added

- Directives in a record document's frontmatter. A reference field is a
  citation site, and the only comment the markdown scan read was an HTML
  one, so a `superseded_by:` naming a document that was itself later
  retired could be acknowledged only file-wide. A whole-line `#` comment
  inside the frontmatter is now a comment the directive parser reads, and
  its line scope reaches the whole YAML entry below it — key and list items
  or continuation lines — so `# inactive-ok: ADR-012 — …` directly above
  the field excuses the field.

### Fixed

- **`CONTRIBUTING.md` is scanned by the reference machinery.**
  `doc_refs.doc_files()` listed `README.md`, `CLAUDE.md` and `AGENTS.md` — the
  files an agent bootstraps from, which is a real category and the wrong one:
  what the reference rules care about is prose asserting the project's rules to
  a reader. `CONTRIBUTING.md` states [DP-008](record/principles.d/DP-008.md), [DP-006](record/principles.d/DP-006.md), [DP-003](record/principles.d/DP-003.md) and the
  [DP-001](record/principles.d/DP-001.md)/[DP-010](record/principles.d/DP-010.md) split almost verbatim while citing none of them, and
  nothing linked or checked its references. Those citations are now written and
  held by the lint. Second instance of this gap — the first was
  `examples/README.md`, where a hand-written link pointed at a path that does
  not exist.
- [ADR-077](record/decisions.d/ADR-077.md) records that [ADR-045](record/decisions.d/ADR-045.md)'s consequence — *"`examples/**` joins
  `template/**` in the site's exclusions"* — is no longer true, following
  [ADR-017](record/decisions.d/ADR-017.md)'s pattern: the old body stands as written and the newer decision
  is where a reader learns the state changed. [ADR-045](record/decisions.d/ADR-045.md) is not edited and not
  superseded; its decision is still in force, and only a sentence about its
  side effects aged out. The other half of that paragraph was already overtaken
  by [ADR-047](record/decisions.d/ADR-047.md).
- `CONTRIBUTING.md`'s description of `examples/` was left behind by
  [ADR-078](record/decisions.d/ADR-078.md): the views are committed and held by `luria index --check` now,
  and the temporary-tree build is about test isolation rather than about
  avoiding a committed view.

### Fixed

- **`examples/constitution`: `BOUNDARY-001` was grounded in a value that does
  not justify it.** `VALUE-003` governs the *manner* of a refusal — refuse in a
  sentence, then stop — and says nothing about which requests are refused. The
  edge was well-typed and false: `required = true` demanded a value and the
  nearest one to hand filled the slot, which is the failure mode a required
  reference is advertised to prevent, inverted. `VALUE-008` now says what the
  limit actually rests on — a cost landing on someone who was never in the
  conversation and cannot decline — and `VALUE-003` stays as the second
  ground, since it does govern the delivery.
- **`grounds` is `many = true`.** It was scalar, so a practice sitting on a
  seam between two values could name only one. `PRACTICE-006` was that case and
  carried the second as a **tag** — a tag standing in for a reference the
  schema could not express, which is [DP-016](record/principles.d/DP-016.md)'s reading. It now names both
  (`VALUE-006` for what a correction costs the reader, `VALUE-001` for the
  requirement that it happen), and the `honesty` tag is dropped rather than
  kept beside the edge.

### Added

- `test_every_section_of_the_source_says_what_accounts_for_it` — the reverse of
  the existing accountability test, and the direction that actually goes wrong.
  The forward test catches a document nobody derived; the likelier change is
  the source gaining a paragraph while nothing is written, and until now that
  left the suite green. Verified against exactly that: a planted `## Escalation`
  section with no document. A `nothing yet` block satisfies the check, which is
  the point rather than a loophole — three sections are accounted for by
  nothing deliberately, and an explicit "nothing, and nothing should" is a
  different statement from silence ([DP-015](record/principles.d/DP-015.md)).

### Changed

- **`luria index` regenerates nested records' views, and `--check` fails on a
  stale one** ([ADR-078](record/decisions.d/ADR-078.md)). `outputs()` and `view_dirs()` reach into each
  nested record under *its own* config; `run()` and `staleness()` inherit it
  unchanged. So the examples' views are **committed** now, `examples/.gitignore`
  is empty, and each example can be read here as a finished record.

  They were ignored on the argument that a committed view nobody regenerates is
  the stale projection the examples argue against — which conflated *committed*
  with *hand-maintained*. [DP-003](record/principles.d/DP-003.md)'s first rung is *derive it*, and a view CI
  regenerates on every push is derived; this project's own `docs/` are
  committed on exactly that basis. The examples being the one exception was
  [DP-016](record/principles.d/DP-016.md)'s same-shape-opposite-rules, and the gap was real rather than
  stylistic: nothing regenerated them, so committing them first would have made
  the original argument true.
- **`include_records` moves from `[luria.site]` to `[luria]`.** It says a
  project contains other projects, which generation needs as much as publishing
  — a key `luria index` had to reach into the site table to read is
  [DP-016](record/principles.d/DP-016.md)'s awkwardness. `Config.nested_records()` is the single answer all
  three callers use, because a record that is published but never regenerated
  is worse than either alone ([DP-004](record/principles.d/DP-004.md)).
- `luria site` stages a nested record from the record itself rather than
  copying it to a temporary directory and generating there. That copy existed
  only because the views were not committed.
- `luria index` names the nested records it wrote rather than folding them into
  the tally: *"…60 devlog entries, plus examples/collocated, …"*. "78 files from
  77 ADRs" is arithmetic nobody can check, and a record that silently rendered
  nothing would look exactly like one that rendered correctly ([DP-015](record/principles.d/DP-015.md)).

### Changed

- **[DP-012](record/principles.d/DP-012.md) to v2**, generalized from "one decision, one thing" to **one
  document, one thing**. Its test was always general; nothing in the wording
  said so, and a record of practices or claims would not have read itself as
  covered. Found in one that isn't: a record with no decisions in it at all.
- The principle gains a second test. The a-priori one — *could these have been
  decided differently?* — only fires when an author stops to ask. Typed edges
  ([ADR-060](record/decisions.d/ADR-060.md), [ADR-071](record/decisions.d/ADR-071.md)) supply one that arrives as friction: **an edge
  whose prose has to name which clause of its target it bears on is reporting
  that the target is two documents.** It also gains the reason not to fix such
  an edge with a qualifier — a `when:` beside a checked reference is prose in a
  data field, which is escalating emphasis one level up, and it is why
  [#141](https://github.com/dmarx/luria/issues/141) puts `when` expressions among its non-goals.
- `examples/constitution`: `PRACTICE-001` split, as the principle's worked
  case. It carried two claims that arrived in the same paragraph of the source
  — deliver the whole scope, and resolve ambiguity without escalating — and a
  boundary overriding it had to say in prose which of the two it argued with.
  The second is now `PRACTICE-010`, and `BOUNDARY-003` names it. The split
  exposed a second error: `BOUNDARY-003`'s edge to `PRACTICE-005` was dropped
  rather than repointed, because that practice licenses acting on what is
  *established* and explicitly not on what is assumed — it never permitted the
  inference, so there was nothing to override.

### Added

- **[DP-015](record/principles.d/DP-015.md)** — *an absence reads exactly like a success*. The premise
  underneath [DP-001](record/principles.d/DP-001.md), [DP-003](record/principles.d/DP-003.md)'s fail-stale rung, [DP-006](record/principles.d/DP-006.md) and
  [DP-010](record/principles.d/DP-010.md), each of which leans on the word *silent* at its load-bearing
  moment and none of which says why silence is the problem. Re-derived four
  times without being written down; a fifth time in another project
  ([SG-DP-022](https://github.com/dmarx/strata-g/blob/main/docs/design-principles.md#dp-22)). All four now cite it, so the unification is an edge rather
  than an assertion.
- An audit of the principle set for restatements, whose result is mostly
  negative and worth recording as such. [DP-002](record/principles.d/DP-002.md), [DP-003](record/principles.d/DP-003.md) and [DP-004](record/principles.d/DP-004.md)
  look like one principle and are not: [DP-003](record/principles.d/DP-003.md) is asymmetric (a source and a
  projection, so *derive it* is available), [DP-004](record/principles.d/DP-004.md) is symmetric (two peers,
  so the remedy is consolidation and "choose the failure polarity" is
  meaningless), and [DP-002](record/principles.d/DP-002.md)'s failure mode is contention, which occurs with
  no duplication at all. Every sampled citation of [DP-004](record/principles.d/DP-004.md) invokes
  divergence-between-implementations; none invokes [DP-003](record/principles.d/DP-003.md)'s remedy ladder.
  Merging them would make the advice a disjunction and cost ~130 citation sites
  their precision.

- **[DP-016](record/principles.d/DP-016.md)** — *an awkward structure is reporting a distinction the model
  has stopped expressing*. Extracted from [DP-009](record/principles.d/DP-009.md), where it was the third of
  three jobs and had **never been cited** — [DP-012](record/principles.d/DP-012.md)'s own symptom for a
  document carrying two things, firing on a principle. Promoted on its second
  substrate: [DP-009](record/principles.d/DP-009.md) found the reading in the file tree, and a typed
  `overrides` edge found it again in the citation graph, which is not a tree
  and which [DP-009](record/principles.d/DP-009.md) does not cover. [DP-009](record/principles.d/DP-009.md) goes to v2 and hands the
  clause over; [DP-012](record/principles.d/DP-012.md)'s edge test cites it as the general form.

### Added

- **`site.include_records`** ([ADR-077](record/decisions.d/ADR-077.md)) — mount a
  whole record inside another's site. Each match is staged by **its own
  config** into a temporary vault and only the finished `content/` is mounted,
  because the source-versus-view test (`link_base`) answers from the reading
  config's schemes: a parent publishing a child's files directly emits both a
  fragment and the view it renders into. One level deep, deliberately; a
  pattern matching no record is an error, a directory that is not a record is a
  quiet skip.
- `config.rooted()` — a bounded context manager that makes another project
  current and restores what it swapped, including restoring an absence.
  `load(root)` builds any config, but the modules underneath call `current()`
  for themselves, so switching projects means switching the global; this names
  and bounds it.
- A root `README.md` for each of the seven examples. Each is now self-contained
  — its own config, sources, README and generated views — and the README is
  what the published section uses as its landing page.

### Changed

- The examples are **published**, at `examples/<name>/` on this project's site,
  instead of being excluded from it. 103 pages to 208. Each keeps its own
  title, theme derivation and record lines, because each was staged by the
  config that knows about it.

### Added

- `examples/constitution/docs/constitution.md` — the source document the
  example's record decomposes. The record asserted things *about* a
  constitution that was not in the repository, so nothing could check the
  decomposition. It lives under `docs/` so `doc_files()` scans it and its
  references are held to the same rules as any other prose.
- Nine documents covering source passages the record did not account for:
  `VALUE-005` (an error that lands on a person is not symmetric with one that
  lands on the work), `VALUE-006` (every sentence the reader must process is a
  cost charged to them), `VALUE-007` (a refusal from the person you are working
  for is information, not an obstacle), `PRACTICE-005`–`PRACTICE-009`, and
  `BOUNDARY-003` (never infer a person's pronouns from their name).
  `BOUNDARY-003` overrides two practices that would have licensed the
  inference, which is the example's clearest demonstration of precedence as a
  checked edge.
- `test_every_active_document_accounts_for_something_in_the_source` — the
  schema checks `PRACTICE → VALUE`; nothing checked `document → the text it was
  drawn from`, and that is the direction a record drifts in. Retired documents
  are exempt.

### Changed

- `BOUNDARY-002` to v2. As written it said restatement *instead of*
  reproduction, which read as a rule against quoting a source at all. Narrowed:
  reproducing is fine, but a copy must not stand in for the analysis and a
  reproduction must stay one — which is why the source page's references sit in
  annotation blocks after each section rather than as links threaded into
  quoted prose.

### Added

- `examples/constitution/` — a worked record with no code in it: an AI
  assistant's operating instructions decomposed into `VALUE`, `PRACTICE` and
  `BOUNDARY` schemes, where precedence is a **checked reference**
  (`BOUNDARY.overrides → PRACTICE`) rather than escalating emphasis, `grounds`
  is a typed reference so no rule stands on its own authority, and a practice
  is retired by a boundary from a different scheme.
- `test_every_example_stages_its_own_site` — every example is staged as its own
  Quartz vault and asserted to publish pages with nothing unplaceable and
  nothing redirected out to the repository. The root `luria.toml` excludes
  `examples/**` from *this* site because a parent config cannot stage a child's
  record, not because the examples are unpublishable; the test says which.

### Fixed

- **`luria index` was not idempotent** for any record whose vocabulary pages
  cite a retired document. `Config.is_generated` covered a scheme's index and
  tag pages but not its **vocabulary** pages, while `adr_index.view_dirs()`
  did — so the reference machinery (`doc_refs.doc_files` →
  `ref_status.scanned_files`, both filtered on `is_generated`) read a generated
  page as prose. The reports render in the same parallel pass that writes those
  pages, so the report saw the *previous* run's copy and a second index produced
  a different report than the first. A citation inside one also could not be
  excused: an `inactive-ok:` written into a generated file is erased by the next
  build. Present since vocabularies shipped; only a *retired* vocabulary member
  makes it visible.
- `tests/test_examples.py::lint_errors` ran six of `lint.run`'s nine checks, so
  an example could pass these tests and fail the real command. It now runs all
  nine — `check_status_vocabulary`, `check_contracts` and
  `check_version_history` were the gap, and `check_contracts` is what makes a
  typed reference a finding rather than a sentence.

### Documentation

- `examples/README.md` records two things staging made visible that `luria
  lint` cannot see: a `render = "document"` scheme's sources are cited by their
  **anchor in the assembled view**, never by filename — the file exists and
  lints clean but is never published — and a document scheme's stub must
  contain `{principles}`, without which every member's body is dropped while
  index and lint both stay green.

### Changed

- The Pages workflow builds after the generation job has committed the
  views on the default branch (`workflow_run` on the CI workflow), instead
  of on the push — which had deployed the merge commit, one bot commit
  behind — and builds nothing on a pull request, where a branch carries no
  views of its own. The scaffold's `pages.yml` has the same shape.

### Changed

- `luria lint` reads sources only. Whether a committed view is current is
  `luria index --check`'s question, asked in the generation job on the
  default branch; the lint keeps the view-directory rule (a hand-written
  file inside one is a violation), computed without writing anything. A
  branch is linted as it is, in CI and locally — nobody regenerates a view
  to check a record.
- The generate action's pull-request shape is repairs only: `views: "false"`
  (was `commit-views`) pushes the repairs and writes no view; the lint
  follows in the same job. The scaffold's workflow uses it.

### Changed

- A temporary code cited from a workflow file is the `workflow-temp-codes`
  warning class, on the enforcement dial, rather than a lint error: the
  generation job cannot push the rewrite on the workflow's own token, and
  can on a token with workflow write. This repository and the scaffold
  name the class in `fail_on`.

### Added

- `luria lint` reports a temporary code cited in a workflow file: the
  generation job rewrites it when the decision is numbered, and the
  workflow token may not modify `.github/workflows/`, so the job's push is
  refused. Cite the number once the decision has one, or say it in prose.

### Added

- `luria repair` writes every mechanical source repair — bare codes linked,
  a journal entry's missing `created:` filled from its path, a retired
  configuration reference removed — each a state the lint reports with this
  command as its remedy. Idempotent.

### Changed

- `luria index` writes views only; the source repairs it used to make first
  are `luria repair`'s.
- Generated views are committed on the default branch only, and source
  repairs on the branch that authored them. A pull request pushes its
  repairs onto the branch, regenerates the views in the working tree, lints
  the result in the same job, and commits no view — so branches never
  conflict on the decision index or the devlog book, and the review reads
  repaired sources. The generate action takes `commit-views: "false"` for
  that shape and a `repair-message`; the scaffold's workflow uses it.

### Added

- `[luria.schemes.X.field_groups.NAME]`: several fields of which an entry
  must carry some — `fields = ["arxiv", "doi", "url"]` with `require =
  "at-least-one"` (or `exactly-one`, `at-most-one`). The finding names the
  need and every field that would have met it; the record page lists the
  group ([#141](https://github.com/dmarx/luria/issues/141)).

### Changed

- The knowledge-base example requires *a source* of a paper — arXiv, DOI
  or URL — rather than an arXiv identifier, and gains a technical report
  with only a URL.

### Changed

- The status note is its own field: `status: Superseded` with
  `status_note: …`, where one scalar carried both. `status_note` is prose
  — a code in it is a citation the fixer links. A note still riding in
  `status:` is a lint finding, and `luria repair` moves it ([#141](https://github.com/dmarx/luria/issues/141)).
- `superseded_by:` is a reference field on every scheme: the successor a
  superseded document names, one code or a list, checked and resolved,
  rendered as `Superseded — by X` and as a *Supersedes* backlink. A
  `Superseded` document that leaves it empty is a lint finding. `luria
  index` fills it from an old-form `by CODE` note.

### Fixed

- `luria new adr --tags record,mechanism` crashed: Fire hands a
  comma-separated flag to the scaffolder as a tuple, and it expected a
  string. Both spellings now work.

### Added

- A frontmatter field backed by a scheme-local controlled vocabulary
  ([#141](https://github.com/dmarx/luria/issues/141)): `[luria.schemes.X.fields.NAME]` with `vocabulary`, `many`, `required` and
  `default`, the values in `NAME.yaml` beside the records shaped like
  `tags.yaml`. Closed — a value the file does not name is a finding. A
  default is read as the field's value wherever it is absent and is never
  written into the source. `luria index` renders a page per value beside
  the tag pages, the scheme's index links them, the record page lists the
  field with what absence means, and the site's record line shows the
  written values. A `world-bible` worked example.

### Added

- `many = true` on a declared reference: the field holds a list of codes,
  every element is checked and resolved, and each becomes an edge ([#141](https://github.com/dmarx/luria/issues/141)).

### Fixed

- A reference field given a YAML list was stringified, its first code
  checked and the rest silently ignored. A list where one code was
  declared is now a finding that names `many = true` as the remedy.

### Changed

- A contract finding cites the key that declared the obligation — every
  key when a field is in both `requires` and `references`, and the
  vocabulary file a derived tag group reads its members from ([#141](https://github.com/dmarx/luria/issues/141)).
- `docs/record.md` gains *What an entry must carry*: each scheme's
  obligations with where each was declared, from the same renderer the
  findings cite. Says so truthfully when there are none.
- The knowledge-base example declares `source` a `LIT` reference rather
  than a bare `requires`, as [#141](https://github.com/dmarx/luria/issues/141)'s second dogfooding experiment asked.

### Added

- Typed edges, read from what the record already says (`luria/edges.py`,
  [#141](https://github.com/dmarx/luria/issues/141)): a `Superseded — by` note, an `influenced_by:` list and any declared
  reference field are edges named for the relation. `luria site` renders each
  document's edges both ways on its record line — *Supersedes*, *Influenced*,
  *Source*, *Cited as `source` by* — where the site previously showed only
  that a page was mentioned.

### Changed

- `requires`, `references` and `tag_groups` are checked in one pass over a
  contract compiled per scheme (`luria/contract.py`, [#141](https://github.com/dmarx/luria/issues/141)), where each was
  its own loop over the record. Findings are unchanged; a field named in
  both `requires` and `references` is now reported once rather than twice.

## 2026-08-31

### Changed

- `luria migrate` now carries pinned endorsements through a scheme rename
  ([#135](https://github.com/dmarx/luria/issues/135), [ADR-066](record/decisions.d/ADR-066.md) v2): for each remote claimed via `remotes = [...]`, a pin
  is re-keyed to the new spelling with both hashes intact — the endorsement
  is of content, which a rename does not change, and prune-and-re-endorse
  would have silently vouched for unreviewed upstream drift. The claimed
  remote's discovered filename map is dropped for re-discovery instead (its
  keys and values both spell the old world); `luria remotes --refresh`
  rebuilds it, and upstream's own rename later surfaces as ordinary
  `remote-drift` for review.

### Added

- `luria remotes --pin [CODE]` endorses remote content by hash ([#135](https://github.com/dmarx/luria/issues/135)): the
  hash of each pinned document's bytes is committed to `remotes.lock.json`,
  `--refresh` records what upstream serves now, and `luria lint` reports
  every pinned document that changed since its endorsement — the new
  `remote-drift` warning class, promotable via `fail_on`. Re-endorsing after
  review clears the finding; a bare `--pin` endorses everything cited and
  prunes pins nothing cites any more ([ADR-066](record/decisions.d/ADR-066.md)).
- A `pin_url` template on a remote (or remote scheme) declares where its
  *stable bytes* live, so content behind a rendered page becomes pinnable —
  `pin_url = "https://arxiv.org/e-print/{1}.{2}"` pins the paper an abstract
  page fronts. Declared rather than guessed: only the project can vouch that
  a URL is content-stable.
- Arbitrary URLs can be pinned too: flag one where it is cited
  (`<!-- pin: https://… — why it matters -->`) and run `luria remotes
  --pin`. The flag is the registration — deleting it retires the pin, so a
  pin that fires too often costs one removed comment.
- `pin = true` on a remote (or one of its schemes) registers a whole code
  family: every cited reference is pinned by a bare `luria remotes --pin`,
  and the lint reports any not yet endorsed. A bare `--pin` syncs the
  lockfile to what is registered — config declarations, `pin:` flags,
  existing pins — and never re-endorses drifted content: that always takes
  the explicit `--pin CODE`, so a scheduled sweep cannot quietly launder a
  drift finding. This repo registers its own cited `LU-ADR` references.

### Fixed

- `luria remotes --refresh` no longer writes an authoritative empty map for a
  remote it could not read: a private repository's failed discovery used to
  flip every one of that remote's references to "absent from the remote".
  Failure now leaves the remote off the lockfile — or keeps the map it
  already had — so it stays on the code-only convention.
- The migration sweep (`luria migrate`) skips `remotes.lock.json`: its JSON
  nests a remote's prefix away from its tails, so the composed-span mask
  could not tell a foreign pin key from a local code, and a scheme rename
  would have rewritten another project's namespace. Machine-derived state
  is re-derived after a migration, never re-spelled.

## 2026-08-25

### Added

- A design principle: **exempting a ledger from one matcher exempts it from
  none of the others.** A mechanism that rewrites instances of a pattern
  records what it rewrote, in the pattern's own spelling — so every matcher
  for that pattern also matches its own ledger, and the exemptions do not
  transfer between them.

### Added

- `uniform_ok` on a scheme: the acknowledgement `inert-status` never had.
  Every other judgment call in luria can be answered where it is raised, but
  that finding is about a *scheme* and a scheme has no line to comment on, so
  a project whose uniformity was deliberate had no move. Set it — a mandatory
  reason — and the scheme leaves `inert-status` for a new
  `acknowledged-uniformity` section that still reports the count and status
  and appends the reason. It lapses on its own when a second status appears,
  and it cannot be promoted to a failure.

### Changed

- [ADR-057](record/decisions.d/ADR-057.md) is `Active` at version 2, having absorbed the acknowledgement. The
  check and the reply to it are one decision restated, not two.

### Added

- A design principle: **meet the project where it is.** A project picks its
  language, platform, forge and shape for reasons that have nothing to do with
  keeping a record; the record arrives afterwards and should fit what it
  finds. Held by being explicit in what the tool writes and forgiving in what
  it assumes — and by asking what has been assumed and never written down,
  since coupling to an environment rarely arrives as a decision.

- A decision on how principles are worded: **write one as a value unless it
  is actually a rule.** The test is whether it can be partly met. If it can,
  the aspirational voice keeps the state a value spends most of its life in;
  if the only outcomes are satisfied and violated, it is a rule and should
  read like one. Two of the fourteen principles here are rules and keep their
  voice. The question is now in the principle template.

### Fixed

- Every file the package reads or writes now names UTF-8 explicitly. Nothing
  did before, so each one took the platform's preferred encoding — cp1252 on
  a default Windows install, where `luria index` crashed writing a check mark
  into a status report, and a tree written that way was then unreadable to
  the same tool under `PYTHONUTF8=1`. Reproducible without Windows under
  `LC_ALL=C`, which is how it is now tested.
- The CLI reconfigures its output streams with `errors="replace"`, so a
  terminal that cannot encode the arrow in `luria init → path` prints `?`
  rather than a traceback. The console keeps its own encoding; only files are
  unconditionally UTF-8.

### Changed

- The README leads with the mechanism firing. A page cites a decision, the
  decision is superseded, and `luria lint` names the page nobody edited —
  before any vocabulary is introduced. Install and the sixty-second
  walkthrough follow; the families and the "ADR is not in the code" reveal
  move after them.
- The quickstart ends by breaking something on purpose: supersede a decision,
  see the finding land, then close it by fixing the citation or acknowledging
  it. `concepts.md` had promised this and the quickstart had never delivered
  it — a self-checking system whose tutorial never catches anything.
- `luria init --dry-run` is in the first-run path, and `CLAUDE.md` gets a
  sentence saying what it is and that nothing depends on it.
- The live record at dmarx.github.io/luria is linked from the README and
  declared as `Documentation` in the package metadata.
- `adopting.md` opens with what makes a record worth keeping, what happens if
  statuses never move, what should stay ordinary prose, how much machinery
  adoption adds, what is GitHub-specific, and what is least settled.

- `CITATION.cff`, which GitHub reads for its "Cite this repository" button,
  and a BibTeX block at the bottom of the README **derived from it** by
  `luria index` — a new generated region alongside the badges, checked for
  staleness by `luria lint`. Two hand-written copies of a citation is the
  drift [DP-3](record/principles.d/DP-003.md) names, and a citation is a bad thing to have two versions of:
  the wrong one is the one that reaches somebody's bibliography.

  No version in either. The version comes from the release tag, and writing
  one into a file by hand is the copy [ADR-053](record/decisions.d/ADR-053.md) removed.

### Fixed

- The ontology said every entry has a name, a standing and declared rules.
  Journals and fragments have none of those — a journal entry is identified by
  when it was written and carries no status at all. `status` and citation
  semantics now belong to **referable documents**, and the other families are
  described as what they are.
- "What people read cannot drift from what people file" claimed more than the
  tool delivers. Hand-written prose drifts; what cannot is a generated view
  from its sources. Scoped accordingly.
- Two documents disagreed about how many worked configurations ship — one said
  four, one said five, and the fifth had been added a day earlier. Neither
  states a count now.
- The README enumerated four statuses of the five in the closed vocabulary.
- The prior-art section named Doyle, de Kleer, AGM and Dung without
  references; they have DOIs now.

### Fixed

- `tests/test_prose_frontmatter.py` writes an `ADR-007.md` into a temporary
  project as fixture data, and the number collides with this repository's own
  [ADR-007](record/decisions.d/ADR-007.md), which is `Superseded` — so the scanner read five lines of fixture
  data as citations of a retired decision. Acknowledged at file level with
  what they actually are.

  The reference-status report now reads clean in every section: nothing
  cited unacknowledged, every code resolving, no stale annotations.

### Added

- `luria config` writes the `luria.toml` that `luria init` would have
  written, and stops. The shorthand covers the two things projects usually
  vary; anything else — a directory name, a narrowed status vocabulary, a tag
  group — is an edit to the config, and making that edit *after* a scaffold
  means moving directories the first run already created. Writing the config
  first and scaffolding second avoids the migration. `--stdout` prints
  instead, and works where a config already exists.

### Documentation

- `render = "index"` versus `render = "document"` is explained rather than
  named. `modeling.md` gains the choice — one question about how the set is
  read, with the two checks worth testing an answer against — and
  `project-memory.md` gains a table of what each actually produces, including
  that `output` means a directory in one and a file in the other.

### Added

- `luria init` infers `issue_url` from the `origin` remote when one is not
  given, for hosts whose issue path is known (GitHub, GitLab), and reports
  what it used. The value cascades — `[luria.site]` derives its title, Pages
  URL and source base from it — so a repository with a remote scaffolds a
  correct record with no configuration at all.

### Added

- `luria init --schemes` and `--journals`, for a project that wants the
  shipped defaults plus a family or two:

  ```console
  $ luria init --schemes "RFC,SPEC:document" --journals "incidents:day"
  ```

  Each entry is `NAME` or `NAME:kind`, and the paths follow the prefix. The
  shorthand is an argument rather than a stored format — what lands in
  `luria.toml` is the ordinary commented table, so nothing reads it back and
  the config looks like every other project's.

### Added

- `docs/concepts.md`, between the quickstart and the modeling guide: the
  shortest complete account of the model — entries, citations, the status
  field everything hangs off, what a finding is and how one is answered, and
  the prior art the mechanism comes from. The page existed before the docs
  rewrite and was dropped; the rewrite left a gap between "do the loop" and
  "choose between the options", which this fills.

### Changed

- [ADR-058](record/decisions.d/ADR-058.md)'s rejection note no longer rests on the concepts page not existing,
  since it does. The reason that survives is the one that mattered: the README
  opens on what the record does rather than on what to call it.

### Fixed

- The README carried two badge blocks. The generator updates the first, so
  the second had frozen at numbers three weeks stale. It was left behind when
  the pitch rewrite inserted a new block above it.

### Changed

- The section introducing the four families is `## Kinds of record` rather
  than `## It is not only for decisions`, which argued against an impression
  the reader has no way to have formed.

### Added

- A scheme may name where its tag vocabulary lives — `tags = "record/topics.yaml"` —
  so two schemes can share one file instead of keeping a copy each.
- A tag may declare `primary_for: [LIT, SOTA]`, and a `tag_groups` entry that
  lists no tags derives its membership from those keys. One vocabulary file
  can now give two schemes different primaries without repeating the shared
  part.
- `[luria.schemes.X.references]` declares that a frontmatter field holds a
  code from a named scheme. Where `requires` checked only that a field was
  truthy, a declared reference checks that it is present, is a code, belongs
  to that scheme, and resolves.

### Changed

- A scheme's `_template.md` is no longer scanned for code references. It is a
  form the tool reads, not an entry in the record, so its example codes were
  reported as citations — a template with a realistic example produced a
  finding against itself. Link targets in templates are still checked.

### Fixed

- Nothing yet broken by this; all three additions are inert until declared.

### Changed

- Nine proposals adopted: [ADR-041](record/decisions.d/ADR-041.md), [ADR-052](record/decisions.d/ADR-052.md), [ADR-053](record/decisions.d/ADR-053.md), [ADR-054](record/decisions.d/ADR-054.md), [ADR-055](record/decisions.d/ADR-055.md),
  [ADR-056](record/decisions.d/ADR-056.md), [ADR-060](record/decisions.d/ADR-060.md), [ADR-061](record/decisions.d/ADR-061.md) and [DP-010](record/principles.d/DP-010.md). Each describes something the tree
  already does; leaving them `Proposed` said the question was open when it
  had been settled in code.
- [ADR-058](record/decisions.d/ADR-058.md), which asked the README to call luria a truth maintenance system,
  is `Rejected`. The README rewrite says what the record does in its own
  terms, and the concepts page the decision also named no longer exists.

### Documentation

- A decision recording why the skip-marker checker was dropped: it cannot
  fire when the marker is on a tip that stays the tip, which is the case that
  does harm, and does fire on commits that suppressed nothing. Required
  status checks in branch protection are the answer, and are not something
  this package can ship.

### Changed

- Test fixtures that model a principles scheme now use a `VP` prefix over
  `docs/values.md` rather than borrowing `DP`. A rename of the real scheme
  would have swept them: `luria migrate` walks tracked source files on the
  grounds that "a source file answers as truthfully as a document does", and
  a fixture's codes are not claims about this record. Six test files, and the
  `UP` remote's document-scheme fixtures with them.

### Fixed

- Five demonstration codes carried no acknowledgement, so they sat in the
  unresolved-codes report indistinguishable from typos: `DP-017` in
  `migrate.py`, `ADR-123` in `concretize.py` and again in [ADR-049](record/decisions.d/ADR-049.md)'s worked
  collision example, `DP-018` in [ADR-040](record/decisions.d/ADR-040.md), and the `[ADR-0` string literal in
  `test_concretize.py` that the scanner reads as a code. Each file now
  carries an `unresolved-ok-file:` directive next to the reason. The report
  reads "every code resolves" for the first time.

### Added

- `docs/modeling.md` — designing a record: what belongs in one, which family
  fits which material, the rule for when two kinds of entry are two schemes,
  what the schema can be made to refuse, and five worked shapes.
- `docs/importing.md` — turning material that already exists as data into a
  record, and what that transform surfaces.
- `examples/knowledge-base/` — a record of domain content rather than project
  meta-documentation: two schemes citing each other with separate statuses,
  required fields, and a one-primary-category rule. Built and linted by CI
  like the others.

### Changed

- The README leads with what a record *is* — entries with a name, a standing,
  declared rules and generated views — rather than with the furniture it
  ships with or the file format it happens to use. Markdown is demoted to an
  implementation note explaining why plain files are chosen (participation)
  and saying plainly that nothing in the model depends on them.
- The README names four shapes a record can take.
- `project-memory.md` gains a **Constraints** section. `requires`,
  `tag_groups`, `titles_generalize` and `inert-status` previously appeared in
  the prose docs only as names in the lint contract.
- A register pass over `modeling.md` and `project-memory.md`: headers now
  label their contents rather than stating verdicts or withholding them,
  padded triads are cut to the number of things there actually are, and a
  few staged constructions state their finding instead. Em-dash density is
  left alone — this project's own prose runs 2.5 to 3.5 per 150 words, and
  scrubbing that would make the docs less like the record they document.
- `adopting.md` documents two CI hazards: another workflow committing to the
  branch defeats the generate/lint handoff from outside, and a commit message
  containing the skip marker suppresses its own run.

### Changed

- The hand-written documentation — README, CLAUDE.md, CONTRIBUTING, and
  every prose page under `docs/` — was rewritten from scratch against a
  deliberately stripped checkout, reorganized around five pages:
  quickstart, project-memory, cli, directives, and adopting.

### Removed

- The docs pages `api.md`, `schemes.md`, and `in-practice.md`; their
  subject matter is folded into the rewritten set.

## 2026-08-24

### Added

- **`docs/record.md` — what *this* project's record is made of**, generated by
  `luria index` from the loaded `luria.toml`: the schemes it named and the
  shape of their codes, where journal entries are filed and where the books
  render, the fragment directories, the remotes it can cite, the `luria new`
  command for every kind, and the settings it moved off the defaults. The
  filing table comes from `new.kinds()` — the CLI's own dispatch mapping — so
  it cannot advertise a kind `luria new` would reject ([ADR-059](record/decisions.d/ADR-059.md)).

### Changed

- **`docs/configuration.md` now renders only in Luria's own tree.** The
  reference is generated so it cannot drift from `luria/config.py`, and that
  argument only holds where `config.py` is a file the reader can open.
  Downstream it was a vendored copy of Luria's schema, stamped *edit
  `luria/config.py`, not this file* at a reader with no such file, going stale
  on their next upgrade with nothing in their repository responsible for it.
  `record.md` is what an adopting project gets instead, and links the schema
  rather than restating it.

### Upgrading

- The first `luria index` after this release **deletes** an orphaned
  `docs/configuration.md` and says so, guarded on the generator's own marker —
  a page at that path that Luria did not write is left exactly where it is.
- `luria lint` will then ask for a `record.md` row in your `docs/README.md`.
  That is a judgement call (you describe your own page), which is why it is
  asked for rather than guessed at.
- Any prose that linked the old page needs repointing — at `record.md` for
  "how our record works", or at
  <https://github.com/dmarx/luria/blob/main/docs/configuration.md> for the
  schema.

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
  what [DP-5](record/principles.d/DP-005.md) predicts will drift; this is its
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
  [DP-1](record/principles.d/DP-001.md) inside the guard written to catch
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
  [DP-1](record/principles.d/DP-001.md) wearing a green hat: the tool refused
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

- **[DP-010](record/principles.d/DP-010.md), "One decision, one thing."** A decision with two unrelated halves
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
    ([DP-3](record/principles.d/DP-003.md)).
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
- [DP-9](record/principles.d/DP-009.md) — structure is read before text, so
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
  a GitHub project ([DP-3](record/principles.d/DP-003.md)). Only `exclude`
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
  fail-stale polarity [DP-3](record/principles.d/DP-003.md) rules out. Projects
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
  once ([DP-2](record/principles.d/DP-002.md)). The default `reports` path
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
  [DP-3](record/principles.d/DP-003.md), since rung 1 isn't available.
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
  [DP-3](record/principles.d/DP-003.md) predicts for hand-maintained
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
  ([DP-1](record/principles.d/DP-001.md)). Stdout is unchanged, so redirection still works.

### Documentation

- [`docs/adopting.md`](docs/adopting.md)'s CI section leads with the scaffolded workflow and the
  two actions, and keeps what stays in the caller's hands: the fork-safe
  checkout ref (a fork's head branch does not exist in the base repo — the
  checkout fails before any push guard can help), the `needs:` + `sha` handoff
  (a `GITHUB_TOKEN` push does not retrigger workflows), and the warning never
  to write GitHub's skip markers into a commit message you author.
