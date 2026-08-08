### Added

- **Design principles are fragments, and `docs/guiding-principles.md` is
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
  fail-stale polarity [GP-3](docs/guiding-principles.md#gp-3) rules out. Projects
  whose principles are still one hand-written file keep the heading-slug
  fallback.

### Fixed

- **Tag pages no longer credit a script that doesn't exist here** — the
  generated header named `scripts/ci/build_adr_index.py`, a leftover from the
  corpus Luria was extracted from.
