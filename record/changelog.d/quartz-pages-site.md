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
