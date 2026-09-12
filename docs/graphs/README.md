# Site graphs

A graph in here is a **picture somebody drew**, not one this project generates.
[`record-map.json`](record-map.json) is what `[luria.site] graph` points at, and
it replaces Quartz's local graph on every page of the published site.

## What this one shows

The whole record, as **two kinds of edge at once** — 454 nodes, 827 edges:

| Edge | Count | Where it comes from |
|---|---|---|
| markdown link | 345 | one page links to another |
| `cites` | 421 | prose names a code |
| `influenced_by` | 58 | frontmatter |
| `superseded_by` | 3 | frontmatter |

That combination is the point. Quartz's graph knows only the first; the lineage
graph at the foot of each page knows only the rest. Here they are the same
picture, told apart by colour, so "this page mentions that one" and "this
decision replaced that one" do not look like the same claim.

Nothing is filtered out. A map that quietly dropped documents would be one you
cannot trust: a reader who looks for `ADR-070`, does not find it, and concludes
it does not exist has been misled by the picture. Density is what the viewer's
zoom, pan, search and **Fit** are for.

A document with a code links to its page. A file with no code — a guide, a
generated view — has no `/<code>` address, so its node does not navigate.

## Redrawing it

Two layers in [strata-g](https://github.com/dmarx/strata-g), merged on filename.

> **Load the record FIRST.** The order matters: with the vault layer loaded
> first, `kind` never reaches the edge Color-by catalog, even after the record
> layer is added. That is a strata-g bug, not a step you can work around by
> setting something else.

1. Add a **Luria record** source for `dmarx/luria`. Its record backend reads
   `luria.toml`, mounts every document as a node carrying `code`, `scheme`,
   `status`, `citations` and the rest, and every typed reference as an edge.
2. Add a second layer for the repository's markdown as an **Obsidian vault**.
   Its edges are the markdown links. Nodes merge with the first layer's on
   filename automatically — the vault labels by filename stem and the record's
   `code` is that same string.
3. Add one **computed column** (`+ Column`), which is how a node gets a URL,
   since neither backend has one:

   | Column | Expression |
   |---|---|
   | `url` | `code ? "https://dmarx.github.io/luria/" & code : ""` |

   One line, because every scheme document has a page and answers at `/<code>`
   ([ADR-tmp40zph](../../record/decisions.d/ADR-tmp40zph.md)). A file with no code yields `""`, which the viewer
   declines to make a link of.
4. On **🌐 Global defaults**, set edge **Color by** → `kind`.
5. Bind node **Color by** `scheme`, **Size by** `citations`, **Label by**
   `code`, **Link by** `url`. Fit to view.
6. **Export → `Canvas — graph data (JSON)`** over `record-map.json`.

`Label by code` matters: merged containers otherwise inherit the vault node's
long title and the labels collide into a paragraph.

`citations` is the document's in-degree — how many others reference it, counting
typed relations and prose citations, deduped where both join the same pair.

## What the build checks

`luria site` validates the file and says which way it is wrong if it is — not
JSON, not a graph, a node with no position. A node whose URL is not `http(s)`
is **reported** rather than rejected: the viewer only follows those, so such a
node would look clickable and silently not be. `navigateOnClick` and the panel
title default on here, because these nodes are pages of this site.

The cost is the map inlined once per page: **40 KB gzipped**, on every page.

## It is a snapshot

The picture is taken at a moment; the record moves. Re-export when the shape has
changed enough to matter — and in particular after a batch of new documents
lands, since a code that was temporary when the map was drawn
(`luria concretize` numbers those where merges serialize) will have been
renumbered since.
