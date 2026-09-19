### Added

- **`[luria.site] graph` — show a graph you designed instead of Quartz's.**
  Point it at a strata-g `Canvas — graph data (JSON)` export and that one
  curated picture replaces Quartz's own graph plugin on every page, where its
  local graph used to be. `graph_height` tunes the element (default `320px`).
  Unset, nothing changes. See [ADR-tmp0hx52](record/decisions.d/ADR-tmp0hx52.md).

  ```yaml
  site:
    graph: docs/graphs/record-map.json
  ```

  The file is validated at build time and the error says which way it is wrong
  — missing, not JSON, not a graph, a node with no position. A node whose URL
  the viewer will not follow (it writes only http(s) hrefs) is **reported**
  rather than rejected, as is `graph` set without a `base_url` to serve the
  viewer from.
