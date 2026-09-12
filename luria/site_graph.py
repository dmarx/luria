"""A document's lineage, as an interactive graph on its page.

`luria site` already states a document's typed edges as prose — the record
line under the title (ADR-042): what it supersedes, what influenced it, what
names it. This renders the same facts as a picture, on the pages that have
them, using strata-g's exported graph viewer ([[SG-ADR-237]], [[SG-ADR-238]]).

**Why this ADDS to Quartz's graph rather than replacing it**, which was the
first plan: Quartz draws the page-link graph, and on this record that is dense
because the generated indexes link every document they list. The typed-edge
graph is not dense. Measured on this record at the time of writing: 61 typed
edges over 110 scheme documents, so 52 of them (47%) have any lineage at all,
degrees 1-6 — and journal entries, reports and the README have none by
construction. Swapping one for the other would leave most pages with an empty
box where a neighbourhood used to be. So the lineage graph appears exactly
where lineage exists, and Quartz's graph stays.

What it shows that Quartz cannot: the edges are TYPED and coloured by relation,
with a legend. Quartz's graph and backlinks say only that a page was mentioned.

The layout is computed here rather than simulated in the browser: a depth-1
neighbourhood is a star, so the centre goes at the origin and its neighbours on
a ring. That is exact for the shape, needs no physics, and means the picture is
identical on every load — a graph that settles differently each time is harder
to recognise on a page you revisit.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

ASSET = Path(__file__).parent / "assets" / "strata_graph_viewer.js"

# The vendored viewer's content hash. A test compares the file to this, so the
# two cannot drift silently — the same offline-drift discipline ADR-016 applies
# to remote document content, applied to a vendored asset.
LINEAGE_VIEWER_SHA256 = "f2627b6c1d37e1e6e70bab743ff5950aeea829a3fe0546962e01f9b561f89aca"

# The filename the viewer is served under, at the site root.
ASSET_NAME = "strata-graph-viewer.js"

# Relation → edge colour. Keys are luria's built-in typed relations; any other
# declared reference field falls back to the neutral colour, so a project that
# declares its own relations gets a working graph without touching this map.
RELATION_COLORS = {
    "superseded_by": "#e15759",
    "influenced_by": "#4e79a7",
}
OTHER_RELATION_COLOR = "#8d8d8d"

# The graph's own palette, fixed rather than themed. The viewer paints its
# canvas labels with these as literal 2D-context colours, so a `var(--light)`
# would be dropped by the canvas and only half the widget would follow the
# page. A single dark figure that reads on both of Quartz's themes is the
# honest version of what this can currently do; making it follow the theme
# toggle needs a re-theme hook in the viewer upstream, not a change here.
GRAPH_BACKGROUND = "#1f2430"
GRAPH_LABEL_COLOR = "#e2e8f0"

CENTRE_COLOR = "#f28e2b"
NEIGHBOUR_COLOR = "#59a14f"

# Nodes are labelled with the CODE alone, not "code — title". Measured rather
# than guessed: at 300px with real titles ("Collection styles are configuration;
# the change…") the labels ran off the canvas and overlapped each other, and a
# figure you cannot read is worse than a short one. The titles are two lines up
# on the same page — the record line states every one of these edges in prose —
# so the graph carries the shape and the prose carries the words. Titles stay in
# each node's `attrs` for anything scripting the page.
CENTRE_SIZE = 13.0
NEIGHBOUR_SIZE = 9.0
# Graph-space radius of the neighbour ring. Arbitrary units — the viewer fits
# whatever it is given — chosen so labels have room at the ring's top and bottom.
RING_RADIUS = 120.0


@dataclass(frozen=True)
class LineageNode:
    code: str
    title: str
    url: str


def relation_color(relation: str) -> str:
    return RELATION_COLORS.get(relation, OTHER_RELATION_COLOR)


def ring_positions(count: int, radius: float = RING_RADIUS) -> list[tuple[float, float]]:
    """`count` points evenly spaced on a circle, starting at the top.

    Starting at the top (rather than at 0 radians, the right) puts the first
    neighbour where a reader looks first, and makes a two-node lineage read as
    a vertical pair rather than a horizontal one — which matters because the
    commonest shape here is a document and its single successor.
    """
    if count <= 0:
        return []
    return [
        (
            round(radius * math.sin(2 * math.pi * i / count), 3),
            round(-radius * math.cos(2 * math.pi * i / count), 3),
        )
        for i in range(count)
    ]


def lineage_view(
    code: str,
    title: str,
    url: str,
    outbound,
    inbound,
    resolve,
    background: str,
    label_color: str,
) -> dict | None:
    """The strata-g GraphExportView for one document's lineage, or None.

    `resolve(code)` answers (title, url) for a neighbour, or None for a code
    this site does not publish — a remote reference, or a document withheld
    from the site. Those are dropped rather than drawn as a node that links
    nowhere.

    Returns None when nothing survives: a page with no lineage gets no graph,
    not an empty one.
    """
    neighbours: dict[str, LineageNode] = {}
    edges: list[dict] = []
    relations: dict[str, str] = {}

    def add(other: str, relation: str, outgoing: bool) -> None:
        # A relation already drawn between this pair stays one edge: the record
        # states some facts from both ends (ADR-071's converses), so the same
        # pair arrives twice and a doubled line would read as two claims. A
        # self-reference is dropped outright — it would add the centre a second
        # time under its own id.
        if other == code or other in neighbours:
            return
        resolved = resolve(other)
        if resolved is None:
            return
        neighbours[other] = LineageNode(other, resolved[0], resolved[1])
        relations[relation] = relation_color(relation)
        edges.append({
            "source": code if outgoing else other,
            "target": other if outgoing else code,
            "color": relation_color(relation),
            "size": 2,
            "curvature": 0,
            "directed": True,
        })

    for edge in outbound:
        add(edge.target, edge.relation, outgoing=True)
    for edge in inbound:
        add(edge.source, edge.relation, outgoing=False)

    if not neighbours:
        return None

    positions = ring_positions(len(neighbours))
    nodes = [{
        "id": code,
        "x": 0.0,
        "y": 0.0,
        "size": CENTRE_SIZE,
        "color": CENTRE_COLOR,
        "label": code,
        "attrs": {"code": code, "title": title},
        "url": url,
    }]
    for (name, node), (x, y) in zip(neighbours.items(), positions):
        nodes.append({
            "id": name,
            "x": x,
            "y": y,
            "size": NEIGHBOUR_SIZE,
            "color": NEIGHBOUR_COLOR,
            "label": name,
            "attrs": {"code": name, "title": node.title},
            "url": node.url,
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "background": background,
        "labelColor": label_color,
        "title": f"{code} lineage",
        # The nodes ARE pages, so a click follows the link; the inspector is
        # the detour here, not the destination ([[SG-ADR-238]]).
        "navigateOnClick": True,
        "legend": [
            {"label": relation.replace("_", " "), "color": color}
            for relation, color in sorted(relations.items())
        ],
    }


def block(view: dict, asset_url: str, height: str = "300px") -> str:
    """The HTML to drop into a page's markdown.

    One `<script src>` for the viewer — shared by every page, unlike the
    self-contained snippet strata-g exports, because this is a site and a
    cached script beats a copy per page — plus the element carrying its data.

    **The data rides in an attribute, not in a `<script>` island**, and that
    is the whole reason this function has a docstring. Two things a markdown
    pipeline does to an island, both measured against a real Quartz v4.5.2
    build rather than reasoned about:

    *A tag sharing its line with content is a PARAGRAPH.* CommonMark only
    opens a "type 7" HTML block when the tag is alone on its line. Written on
    one line, the whole element was parsed as inline HTML inside a paragraph,
    the typographer curled every quote in the island and the `</script>` was
    relocated. Hence the newlines below, which a test pins with a parser.

    *Even as a clean HTML block, element CONTENT is re-serialized.* Quartz
    goes remark → hast → preact, and a script element's text children come out
    entity-escaped. Script content is raw text, so the browser never decodes
    them back: `JSON.parse` throws on a page whose source was perfectly
    correct, and no amount of escaping on this side helps.

    An attribute value is the one place HTML escaping round-trips by
    construction — whatever a serializer escapes, the parser decodes — so the
    JSON goes in `data-graph` and arrives intact. strata-g's viewer reads
    either carrier; the island remains right for a self-contained file, which
    passes through no pipeline at all.

    The value is escaped for an attribute context. `<` is written as its JSON
    escape as well, belt and braces, because these titles are record content
    and a record can say anything.
    """
    data = json.dumps(view, ensure_ascii=False).replace("<", "\\u003c")
    attr = (data.replace("&", "&amp;").replace('"', "&quot;")
                .replace("<", "&lt;").replace(">", "&gt;"))
    return (
        f'\n<strata-g-graph style="height: {height}" data-graph="{attr}">\n'
        f"</strata-g-graph>\n"
        f'<script src="{asset_url}"></script>\n'
    )


def load_view(path: Path) -> dict:
    """A `Canvas — graph data (JSON)` export, checked enough to fail usefully.

    The file is somebody's export pointed at by a config key, so every way of
    getting it wrong — a path typo, the wrong JSON, a graph with nothing in it
    — should say which, at build time. A site that builds and then shows an
    empty box has told the author nothing.

    Structural, not a schema: a `nodes` list whose entries carry an id and a
    position is what the viewer needs and what distinguishes this file from any
    other JSON. The rest is the exporter's business, and a check that enumerated
    every optional field would reject next month's export for adding one.
    """
    if not path.exists():
        raise SystemExit(
            f"luria site: [luria.site] graph = {path} does not exist. Export it "
            f"from strata-g with `Canvas — graph data (JSON)`.")
    try:
        view = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"luria site: {path} is not valid JSON — {exc}") from None
    nodes = view.get("nodes") if isinstance(view, dict) else None
    if not isinstance(nodes, list) or not nodes:
        raise SystemExit(
            f"luria site: {path} carries no nodes. Expected a strata-g graph "
            f"export — an object with a non-empty `nodes` list.")
    for node in nodes:
        if not isinstance(node, dict) or "id" not in node or "x" not in node:
            raise SystemExit(
                f"luria site: {path} has a node with no id or no position "
                f"({node!r:.60}). Expected a strata-g graph export.")
    view.setdefault("edges", [])
    view.setdefault("background", GRAPH_BACKGROUND)
    view.setdefault("labelColor", GRAPH_LABEL_COLOR)
    return view


def unfollowable(view: dict) -> list[str]:
    """Node labels whose URL the viewer will refuse to follow.

    Reported rather than rejected: a graph whose nodes are not links is a
    perfectly good picture, and so is one where only some are. What is not
    good is a node that LOOKS clickable and silently is not, which is what a
    relative or `javascript:` URL becomes — the viewer only ever writes an
    href it recognises as http(s)."""
    out = []
    for node in view.get("nodes", []):
        url = node.get("url")
        if url is None:
            continue
        if not str(url).lower().startswith(("http://", "https://")):
            out.append(str(node.get("label") or node.get("id")))
    return out


def asset_sha256() -> str:
    return hashlib.sha256(ASSET.read_bytes()).hexdigest()
