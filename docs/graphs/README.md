# Site graphs

A graph in here is a **picture somebody drew**, not one this project generates.
[`record-map.json`](record-map.json) is what `[luria.site] graph` points at, and
it replaces Quartz's local graph on every page of the published site.

## What this one shows

The documents this record **leans on**: every decision and design principle
cited five or more times — 37 of them, 104 typed edges — coloured by scheme,
sized by citation count, labelled by code, each node linking to its own page.

The threshold is the legibility budget, measured rather than picked. All 110
decisions and principles render as an unreadable ball at this height; at five
citations and up the map is a shape you can read, and 4.4 KB gzipped per page
instead of 11.8. Journal entries and changelog fragments are out entirely —
they are the record's narrative, not its shape.

## Redrawing it

The file is strata-g's `Canvas — graph data (JSON)` export, so changing the
picture means drawing a new one rather than editing JSON:

1. In [strata-g](https://github.com/dmarx/strata-g), add a **Luria record**
   source for `dmarx/luria`. Its record backend reads `luria.toml`, mounts every
   document as a node carrying `code`, `scheme`, `status`, `citations` and the
   rest, and every typed reference as an edge.
2. Add two **computed columns** (`+ Column`), which is how a node gets a URL —
   the backend has no URL column of its own:

   | Column | Expression |
   |---|---|
   | `url` | `code ? "https://dmarx.github.io/luria/" & code : ""` |
   | `keep` | `scheme in ["ADR", "DP"] and $not($contains(code, "tmp")) and citations >= 5 ? 1 : 0` |

   The `url` rule is one line because every scheme document has a page and
   answers at `/<code>`. The `keep` rule drops **temporary** codes: `luria
   concretize` numbers those where merges serialize, so a node for one would
   link to a page that does not exist yet and then move when it does.
3. Add a **Filter** on `keep`, bounds `1` to `1`.
4. Bind **Color by** `scheme`, **Size by** `citations`, **Label by** `code`,
   and **Link by** `url`. Fit to view.
5. **Export → `Canvas — graph data (JSON)`** over `record-map.json`.

## What the build checks

`luria site` validates the file and says which way it is wrong if it is — not
JSON, not a graph, a node with no position. A node whose URL is not `http(s)`
is **reported** rather than rejected: the viewer only follows those, so such a
node would look clickable and silently not be. `navigateOnClick` defaults on
here, because these nodes are pages of this site.

## It is a snapshot

The picture is taken at a moment; the record moves. Re-export when the shape
has changed enough to matter. Nothing breaks in the meantime — a node for a
document that has since been renamed simply links to where it was.
