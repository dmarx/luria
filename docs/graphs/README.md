# Site graphs

A graph in here is a **picture somebody drew**, not one this project generates.
[`record-map.json`](record-map.json) is what `[luria.site] graph` points at, and
it replaces Quartz's local graph on every page of the published site.

## What this one shows

The whole record — every document luria knows about, 248 nodes and 482 typed
edges — coloured by scheme, sized by how many other documents cite it, labelled
by code.

Nothing is filtered out. A map that quietly dropped two thirds of the decisions
would be a map you cannot trust: a reader who looks for `ADR-070`, does not find
it, and concludes it does not exist has been misled by the picture. Density is
what the viewer's zoom, pan, search and **Fit** are for.

A document with a code links to its page. A journal entry or a changelog
fragment has no code and no page of its own, so its node does not navigate —
which is the truth about it, and better than inventing an address.

## Redrawing it

The file is strata-g's `Canvas — graph data (JSON)` export, so changing the
picture means drawing a new one rather than editing JSON:

1. In [strata-g](https://github.com/dmarx/strata-g), add a **Luria record**
   source for `dmarx/luria`. Its record backend reads `luria.toml`, mounts every
   document as a node carrying `code`, `scheme`, `status`, `citations` and the
   rest, and every typed reference as an edge.
2. Add one **computed column** (`+ Column`) — this is how a node gets a URL,
   since the backend has no URL column of its own:

   | Column | Expression |
   |---|---|
   | `url` | `code ? "https://dmarx.github.io/luria/" & code : ""` |

   One line, because every scheme document has a page and answers at `/<code>`
   ([ADR-tmp40zph](../../record/decisions.d/ADR-tmp40zph.md)). A document with no code yields `""`, which the viewer
   declines to make a link of.
3. Bind **Color by** `scheme`, **Size by** `citations`, **Label by** `code`,
   **Link by** `url`. Fit to view.
4. **Export → `Canvas — graph data (JSON)`** over `record-map.json`.

`citations` is the document's in-degree: how many others reference it, counting
typed relations from frontmatter and prose citations, deduped where both join
the same pair.

## What the build checks

`luria site` validates the file and says which way it is wrong if it is — not
JSON, not a graph, a node with no position. A node whose URL is not `http(s)`
is **reported** rather than rejected: the viewer only follows those, so such a
node would look clickable and silently not be. `navigateOnClick` and the panel
title default on here, because these nodes are pages of this site.

The cost is the map inlined once per page: **24 KB gzipped**, on every page.

## It is a snapshot

The picture is taken at a moment; the record moves. Re-export when the shape has
changed enough to matter — and in particular after a batch of new documents
lands, since a code that was temporary when the map was drawn
(`luria concretize` numbers those where merges serialize) will have been
renumbered since.
