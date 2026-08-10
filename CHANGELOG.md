# Changelog

Assembled from `changelog.d/` fragments on a cadence — never hand-edited
([ADR-002](record/decisions.d/ADR-002.md)).

<!-- luria-insert-here -->

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
