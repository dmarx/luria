# Site graphs

A graph in here is a **picture somebody drew**, not one this project generates.
[`record-map.json`](record-map.json) is what `[luria.site] graph` points at, and
it replaces Quartz's local graph on every page of the published site.

## What this one shows

The whole record, as **two kinds of edge at once** — 456 nodes, 922 edges — of
which each page shows the neighbourhood around **its own** node:

| Edge | Count | Where it comes from |
|---|---|---|
| markdown link | 313 | one page links to another |
| `cites` | 548 | prose names a code |
| `influenced_by` | 58 | frontmatter |
| `superseded_by` | 3 | frontmatter |

That combination is the point. Quartz's graph knows only the first; the lineage
graph at the foot of each page knows only the rest. Here they are the same
picture, told apart by colour, so "this page mentions that one" and "this
decision replaced that one" do not look like the same claim.

Nothing is filtered out of the FILE. A map that quietly dropped documents would
be one you cannot trust: a reader who looks for `ADR-070`, does not find it, and
concludes it does not exist has been misled by the picture.

What each page shows is a different question, and the answer is
`[luria.site] graph_depth` — hops from that page's own node, **1** by default.
A page is a place, and the useful picture there is where you are, not the whole
atlas. Measured on this record: median **7 nodes** a page rather than 456, and
**1,062 bytes** gzipped rather than 39 KB. `graph_depth = 0` restores the whole
map on every page for a project that wants one poster.

A document with a code links to its page. A file with no code — a guide, a
generated view — has no `/<code>` address, so its node does not navigate.

## Redrawing it

Two layers in [strata-g](https://github.com/dmarx/strata-g).

> **They do not fully merge, and that is measured, not assumed.** strata-g folds
> nodes together when their on-screen LABELS match — not when their filenames
> do. The record layer titles a decision `ADR-001: Four layers of record…` and
> the vault layer reads the bare heading `Four layers of record…`, so 112
> documents stay as two nodes. 122 others do merge, where the two labels happen
> to coincide (a changelog fragment's title *is* its timestamp). A computed
> column stripping the `CODE: ` prefix would fix it, except a virtual column
> cannot be a label — see [strata-g#787](https://github.com/dmarx/strata-g/issues/787).

> **Load the record FIRST.** The order matters: with the vault layer loaded
> first, `kind` never reaches the edge Color-by catalog, even after the record
> layer is added. That is a strata-g bug, not a step you can work around by
> setting something else.

1. Add a **Luria record** source for `dmarx/luria`. Its record backend reads
   `luria.toml`, mounts every document as a node carrying `code`, `scheme`,
   `status`, `citations` and the rest, and every typed reference as an edge.
2. Add a second layer for the repository's markdown as an **Obsidian vault**.
   Its edges are the markdown links, and its nodes are titled from each file's
   own heading.
3. Add one **computed column** (`+ Column`), which is how a node gets a URL,
   since neither backend has one:

   | Column | Expression |
   |---|---|
   | `url` | `code ? "https://dmarx.github.io/luria/" & code : ""` |

   One line, because every scheme document has a page and answers at `/<code>`
   ([ADR-094](../../record/decisions.d/ADR-094.md)). A file with no code yields `""`, which the viewer
   declines to make a link of.
4. On **🌐 Global defaults**, set edge **Color by** → `kind`.
5. Bind node **Color by** `scheme` and **Link by** `url`. Leave **Label by**
   on `title`, its default.
6. Set **Size by** `_uniform` and **Size scale** to about **32**, which exports
   a node size near 9. That number is not taste: the viewer draws a node at
   `max(1.5, size × min(1, cap/maxSize) × zoom)` and only labels one whose
   radius clears **6** — and `min(1, …)` means it will only ever SHRINK a node,
   never grow one, so the exported size has to carry it. Sizing by `citations`
   pins the floor at 2, which renders at ~2.5px: the low-cited nodes lose their
   labels and the high-cited ones grow big enough to cover the edges underneath.
   Uniform costs the citation encoding and buys a legible map.
7. Fit to view.
8. **Export → `Canvas — graph data (JSON)`** over `record-map.json`.

**Why `title` and not `code`.** A map labelled `ADR-001`, `DP-004`, `ADR-093`
is a map you cannot read without opening every node: the code is an address,
not a name. Titles are long and the canvas cuts them at 60 characters, which is
the cost — and it is the cheaper one. (The obvious repair, a computed column
that truncates with an ellipsis, does not work: binding **Label by** to a
virtual column is accepted by the select and ignored by the canvas,
[strata-g#787](https://github.com/dmarx/strata-g/issues/787).)

`citations` is the document's in-degree — how many others reference it, counting
typed relations and prose citations, deduped where both join the same pair.

## What the build checks

`luria site` validates the file and says which way it is wrong if it is — not
JSON, not a graph, a node with no position. A node whose URL is not `http(s)`
is **reported** rather than rejected: the viewer only follows those, so such a
node would look clickable and silently not be. `navigateOnClick` and the panel
title default on here, because these nodes are pages of this site.

The cost is a neighbourhood inlined per page: **926 bytes gzipped** at the
median, 0.17 MB across the site. A nested record gets no configured graph at
all — its pages are not nodes of this map, and this map is about a different
record.

## It is a snapshot

The picture is taken at a moment; the record moves. Re-export when the shape has
changed enough to matter — and in particular after a batch of new documents
lands, since a code that was temporary when the map was drawn
(`luria concretize` numbers those where merges serialize) will have been
renumbered since.
