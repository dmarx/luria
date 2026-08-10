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
