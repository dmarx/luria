### Added

- **`[luria.site] graph_depth`** — how much of the configured graph each page
  shows, in hops from that page's own node. Default **1**: a page is a place,
  and the useful picture there is where you are, not the whole atlas. On this
  record that is a median of 6 nodes a page rather than 454, and 926 bytes
  gzipped rather than 40 KB. `0` restores the whole map on every page.

- **This record now shows a map of itself.** `[luria.site] graph` points at
  `docs/graphs/record-map.json` — 454 nodes and 827 edges, drawn in strata-g
  from the record itself, composed from **two layers**: the luria record
  (typed edges) and the repository's markdown as an Obsidian vault (markdown
  links), merged on filename and told apart by edge colour. Quartz's graph
  knows only the links; the lineage graph knows only the typed edges; this is
  both at once. Nothing filtered — a map that quietly dropped documents would
  be one you cannot trust, and density is what zoom, search and Fit are for.
  [`docs/graphs/README.md`](../../docs/graphs/README.md) has the recipe for
  redrawing it.
