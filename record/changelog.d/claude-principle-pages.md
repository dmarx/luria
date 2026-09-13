### Added

- **This record now shows a map of itself.** `[luria.site] graph` points at
  `docs/graphs/record-map.json` — 456 nodes and 922 edges, drawn in strata-g
  from the record itself, composed from **two layers**: the luria record
  (typed edges) and the repository's markdown as an Obsidian vault (markdown
  links), told apart by edge colour. Quartz's graph knows only the links; the
  lineage graph knows only the typed edges; this is both at once. Nothing
  filtered — a map that quietly dropped documents would be one you cannot
  trust, and density is what zoom, search and Fit are for.
  [`docs/graphs/README.md`](docs/graphs/README.md) has the recipe for
  redrawing it.

- **`[luria.site] graph_depth`** — how much of the configured graph each page
  shows, in hops from that page's own node. Default **1**: a page is a place,
  and the useful picture there is where you are, not the whole atlas. On this
  record that is a median of 7 nodes a page rather than 456, and 1,062 bytes
  gzipped rather than 39 KB. `0` restores the whole map on every page.

### Changed

- **The map's nodes are labelled with document titles**, not bare codes. A map
  reading `ADR-001`, `DP-004`, `ADR-093` is one you cannot navigate without
  opening every node — the code is an address, not a name. Titles are cut at
  the canvas's 60 characters, which is the cost and is the cheaper one.

- **The vendored strata-g viewer is re-pinned** to the build that re-renders on
  new data (`strata-g#786`). Quartz routes in-page navigation client-side and
  *morphs* the existing DOM rather than replacing it, so arriving at a page by
  clicking a link left the previous page's graph on screen — only the node you
  clicked *inside the graph* looked right, because that was a full page load.
  Measured on a real build: navigating [ADR-042](record/decisions.d/ADR-042.md) → [ADR-005](record/decisions.d/ADR-005.md) by an ordinary prose
  link drew 13 nodes where a reload of the same URL drew 26, and leaked a graph
  instance on every hop. Both graphs now match the reload exactly.
