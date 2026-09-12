### Added

- **A document-rendered scheme's sources are published as pages.**
  `record/principles.d/DP-004.md` is served at `/record/principles.d/DP-004`,
  alias `/DP-004`, exactly like a decision. `publishable()` excluded them by a
  derived rule — "are this file's links spelled for somewhere else?" — which a
  design principle answered yes to for the same reason a changelog fragment
  does. It is nothing like one: numbered, titled, statused, versioned, cited by
  code. The rule now says what it meant — a **fragment** is not published, a
  **document** rendered as a section of one is — and the assembled view is
  still published alongside. On this record, 281 → **307** staged pages.

  Their links are re-spelled on the way out, not in the repository: a
  principle's source writes `../record/decisions.d/ADR-006.md`, correct from
  `docs/` and wrong from its own page, so staging re-points each target as it
  writes.

- **`[luria.schemes.X] cite`** — where a citation of one of this scheme's codes
  points. `"page"` for the cited document's own file, `"view"` for an anchor in
  the assembled view. **Unset means what the scheme already does**, so nothing
  changes until a project sets it. An unknown value, or an explicit `"view"` on
  a scheme that assembles no view, is refused by name.

- **`luria repair` moves links a record already wrote**, not only bare
  references. Changing `cite` governs every citation written from then on and
  nothing already on disk — those are plain markdown links, which the linkifier
  has no reason to touch. The link text is left exactly as written, a link with
  no fragment is left alone, and an anchor naming no document is left alone
  rather than swapped for a dead file.

### Fixed

- **A citation of a principle now goes somewhere.** Every one resolved to
  `docs/design-principles.md#dp-N`, and those anchors are `<a name="dp-3"></a>`
  — raw HTML that Quartz's markdown pipeline drops, slugifying each heading's
  own text instead. Measured on a real v4.5.2 build: **330 links across 81
  pages, none of which resolved**, while the same links worked in the
  repository, which is why no lint had ever mentioned them.

  This record now sets `cite = "page"`; `luria repair` rewrote 98 files.
  Re-measured on the same build: **330 broken → 0**, and links to a principle's
  page **85 → 404, all resolving**. See
  [ADR-094](record/decisions.d/ADR-094.md).
