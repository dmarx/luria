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
LINEAGE_VIEWER_SHA256 = "46a62fba29676c29c6f302d962bd7fe671972c28503c44b95b502fc92fe54895"

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
    cached script beats a copy per page — plus the element and its data.

    The JSON goes through the same escaping strata-g uses: `<` is written as
    its JSON escape so no value can close the script element, which matters
    because these titles are record content and a record can say anything.
    """
    data = json.dumps(view, ensure_ascii=False).replace("<", "\\u003c")
    return (
        f'\n<strata-g-graph style="height: {height}">'
        f'<script type="application/json">{data}</script>'
        f"</strata-g-graph>\n"
        f'<script src="{asset_url}"></script>\n'
    )


def asset_sha256() -> str:
    return hashlib.sha256(ASSET.read_bytes()).hexdigest()
