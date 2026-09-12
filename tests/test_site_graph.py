"""The lineage graph `luria site` puts on a document's page.

Two halves, tested differently. `site_graph` is pure — codes, positions,
colours, a dict — so it is tested directly. The staging half is tested
through `site.stage` against this repo's own record, like the rest of
`test_site.py`: a graph that is right on a fixture and wrong on 110 real
documents has told you nothing.

What is NOT tested here is the viewer's own behaviour — that it draws, that a
click navigates, that a `javascript:` URL is refused. That is strata-g's
suite, running a real browser over the same payload this vendors; a browser
is not a dependency this package is willing to take on to re-check it. The
seam between the two IS tested: the payload's content hash is pinned, so the
vendored copy cannot drift from the one those tests cover.
"""
import json
from pathlib import Path

from luria import site, site_graph
from luria.config import current


class Edge:
    """The shape `edges.graph()` hands back — source, target, relation."""
    def __init__(self, source, target, relation):
        self.source, self.target, self.relation = source, target, relation


def resolver(**pages):
    return lambda code: pages.get(code)


def view(**over):
    kw = dict(
        code="ADR-001", title="First", url="https://x.test/ADR-001",
        outbound=[Edge("ADR-001", "ADR-002", "superseded_by")], inbound=[],
        resolve=resolver(**{"ADR-002": ("Second", "https://x.test/ADR-002")}),
        background="#1f2430", label_color="#e2e8f0")
    kw.update(over)
    return site_graph.lineage_view(**kw)


def test_the_vendored_viewer_matches_its_pin():
    """The one guard on a file this package does not author.

    A viewer edited in place — a quick fix, a merge — would ship a payload no
    test anywhere covers. The hash makes that a failure rather than a
    surprise, the same offline-drift rule ADR-016 applies to remote content.
    """
    assert site_graph.asset_sha256() == site_graph.LINEAGE_VIEWER_SHA256


def test_a_document_with_no_lineage_gets_no_graph():
    """Not an empty one. A box with nothing in it reads as a broken page."""
    assert view(outbound=[], inbound=[]) is None


def test_a_neighbour_the_site_does_not_publish_is_dropped():
    """A node that links nowhere is worse than an absent node."""
    assert view(resolve=resolver()) is None


def test_the_centre_sits_at_the_origin_and_neighbours_on_a_ring():
    v = view(outbound=[Edge("ADR-001", "ADR-002", "superseded_by"),
                       Edge("ADR-001", "ADR-003", "influenced_by")],
             resolve=resolver(**{"ADR-002": ("Second", "https://x.test/ADR-002"),
                                 "ADR-003": ("Third", "https://x.test/ADR-003")}))
    centre, *ring = v["nodes"]
    assert (centre["x"], centre["y"]) == (0.0, 0.0)
    assert centre["size"] > ring[0]["size"]
    radii = {round((n["x"] ** 2 + n["y"] ** 2) ** 0.5) for n in ring}
    assert radii == {round(site_graph.RING_RADIUS)}


def test_the_ring_starts_at_the_top():
    """A single neighbour reads as a vertical pair, which is the commonest
    shape in a record: a decision and the one that replaced it."""
    assert site_graph.ring_positions(1) == [(0.0, -site_graph.RING_RADIUS)]


def test_ring_positions_are_evenly_spaced_and_distinct():
    points = site_graph.ring_positions(6)
    assert len(set(points)) == 6
    assert all(abs((x ** 2 + y ** 2) ** 0.5 - site_graph.RING_RADIUS) < 0.01
               for x, y in points)


def test_edge_direction_follows_the_relation():
    out = view()["edges"][0]
    assert (out["source"], out["target"]) == ("ADR-001", "ADR-002")
    v = view(outbound=[], inbound=[Edge("ADR-002", "ADR-001", "superseded_by")])
    incoming = v["edges"][0]
    assert (incoming["source"], incoming["target"]) == ("ADR-002", "ADR-001")


def test_a_pair_stated_from_both_ends_is_one_edge():
    """The record states some relations as converses (ADR-071), so the same
    pair arrives twice. A doubled line would read as two different claims."""
    v = view(outbound=[Edge("ADR-001", "ADR-002", "superseded_by")],
             inbound=[Edge("ADR-002", "ADR-001", "influenced_by")])
    assert len(v["edges"]) == 1
    assert len(v["nodes"]) == 2


def test_a_self_reference_never_becomes_a_second_centre():
    v = view(outbound=[Edge("ADR-001", "ADR-001", "influenced_by"),
                       Edge("ADR-001", "ADR-002", "superseded_by")],
             resolve=resolver(**{"ADR-001": ("First", "https://x.test/ADR-001"),
                                 "ADR-002": ("Second", "https://x.test/ADR-002")}))
    assert [n["id"] for n in v["nodes"]] == ["ADR-001", "ADR-002"]


def test_the_legend_names_each_relation_once_in_the_edges_colour():
    v = view(outbound=[Edge("ADR-001", "ADR-002", "superseded_by"),
                       Edge("ADR-001", "ADR-003", "superseded_by")],
             resolve=resolver(**{"ADR-002": ("Second", "https://x.test/ADR-002"),
                                 "ADR-003": ("Third", "https://x.test/ADR-003")}))
    assert v["legend"] == [{"label": "superseded by",
                            "color": site_graph.RELATION_COLORS["superseded_by"]}]
    assert {e["color"] for e in v["edges"]} == {
        site_graph.RELATION_COLORS["superseded_by"]}


def test_a_relation_luria_does_not_ship_still_gets_a_colour():
    """A project declaring its own reference field gets a working graph
    without editing this package's palette."""
    v = view(outbound=[Edge("ADR-001", "ADR-002", "overrides")])
    assert v["legend"] == [{"label": "overrides",
                            "color": site_graph.OTHER_RELATION_COLOR}]


def test_nodes_are_labelled_with_the_code_alone():
    """Measured, not preferred: at 300px the real titles ran off the canvas
    and overlapped. The title is still carried, as data."""
    centre = view()["nodes"][0]
    assert centre["label"] == "ADR-001"
    assert centre["attrs"]["title"] == "First"


def rendered(markdown: str) -> str:
    """`markdown` through a CommonMark parser.

    Quartz builds on remark/micromark. This is a different implementation of
    the same specification, which is the point: what is being checked is a
    CommonMark rule, not one renderer's habit.
    """
    from markdown_it import MarkdownIt
    return MarkdownIt("commonmark").render(markdown)


def test_the_block_survives_a_markdown_parser_intact():
    """The bug this exists for shipped, and looked fine until the site built.

    `<strata-g-graph …>` is a CommonMark "type 7" HTML-block opener, which
    requires the tag to be alone on its line. Written on one line with its
    data, the parser reads a PARAGRAPH containing inline HTML — and then the
    markup is text, so the typographer curls the quotes in it. The staged
    markdown looked correct; the built page carried JSON that cannot parse.
    """
    html = rendered("## Lineage\n" + site_graph.block(view(), "/viewer.js"))
    assert "<p><strata-g-graph" not in html, "the element was parsed as a paragraph"
    assert graph_data(html)[0]["nodes"][0]["id"] == "ADR-001"
    assert '<script src="/viewer.js">' in html


def test_the_one_line_form_is_what_a_parser_rejects():
    """A positive control (DP-22).

    The assertion above is only worth anything if the shape it rejects is the
    shape that actually breaks — otherwise "no paragraph wrapper" could be
    true of any markup at all and the test would pass on a fix that fixed
    nothing.
    """
    one_line = site_graph.block(view(), "/viewer.js").replace('">\n</strata-g-graph>',
                                                              '"></strata-g-graph>')
    html = rendered("## Lineage\n" + one_line)
    assert "<p><strata-g-graph" in html


def test_a_title_that_is_markup_stays_data():
    """A record can say anything, and these titles are record content.

    The value lands in an attribute inside a document other people open, so
    the claim is that it can neither close the attribute nor introduce a tag —
    and that it is still the SAME STRING once a parser has decoded it. Escaped
    bytes, not lost data.
    """
    nasty = '</strata-g-graph><img src=x onerror=alert(1)> "quoted" & ampersand'
    html = site_graph.block(view(title=nasty), "/viewer.js")
    assert "<img" not in html
    assert "</strata-g-graph><img" not in html
    parsed = graph_data(html)[0]
    assert parsed["nodes"][0]["attrs"]["title"] == nasty


# --- staged against this repo's own record -------------------------------

# The element, not the heading. `## Lineage` is a string prose can contain —
# the ADR describing this feature does — and keying off it counted that page as
# a graph, which is how the instrument check below caught its own instrument.
ELEMENT = "<strata-g-graph "


def graph_data(markup: str) -> list[dict]:
    """Every lineage view in `markup`, read the way a BROWSER reads it.

    Through an HTML parser rather than by slicing the string, because the
    claim being made is precisely that the value survives a serialize/parse
    round-trip: the attribute is written entity-escaped and has to come back
    as the same bytes. Slicing the raw text would skip the half that matters.
    """
    from html.parser import HTMLParser

    found: list[dict] = []

    class Reader(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag != "strata-g-graph":
                return
            value = dict(attrs).get("data-graph")
            assert value is not None, "the element carries no data-graph"
            found.append(json.loads(value.replace("\\u003c", "<")))

    Reader(convert_charrefs=True).feed(markup)
    return found


def graphed(content):
    """Every staged page carrying a lineage graph, as (path, view)."""
    out = []
    for path in sorted(content.rglob("*.md")):
        text = path.read_text()
        if ELEMENT not in text:
            continue
        for view in graph_data(text):
            out.append((path, view))
    return out


def test_page_url_is_absolute_and_spells_quartzs_slug():
    cfg = current()
    adr = cfg.root / "record" / "decisions.d" / "ADR-001.md"
    assert site.page_url(adr, cfg) == (
        "https://dmarx.github.io/luria/record/decisions.d/ADR-001")
    assert site.page_url(cfg.root / "README.md", cfg) == "https://dmarx.github.io/luria/"


def test_no_base_url_means_no_urls_and_therefore_no_graphs(project):
    """A record luria cannot name a domain for gets no lineage graph, because
    the viewer only follows an `http(s)` href and a relative one would be
    refused. Better no picture than nodes that navigate nowhere."""
    from luria.config import load
    cfg = load(project)
    assert cfg.site.base_url == ""
    assert site.page_url(project / "docs" / "design-principles.md", cfg) is None


def test_every_scheme_document_resolves_to_its_own_page():
    """Principles used to resolve to an anchor in the assembled document,
    because they had no page. ADR-094 gave them one, which collapsed two
    resolution rules into one. Dropping them would not be a rounding error:
    on this record they are 50 of 122 typed-edge endpoints."""
    cfg = current()
    index = site.lineage_index(site.publishable(cfg), cfg, site.titles())
    assert index["ADR-001"][1].endswith("/record/decisions.d/ADR-001")
    title, url = index["DP-002"]
    assert url.endswith("/record/principles.d/DP-002"), url
    assert "#" not in url, "a principle is a page now, not an anchor"
    assert title


def test_staging_puts_a_graph_on_the_pages_that_have_lineage(tmp_path):
    report = site.stage(tmp_path)
    # The instrument check: a count of zero would pass every assertion below
    # about what the graphs contain, because there would be nothing to check.
    assert report.graphs > 0
    assert len(graphed(tmp_path / "content")) == report.graphs
    # And not on every page — a graph everywhere would mean the "no lineage,
    # no graph" rule never fired, which is the other way this reads as a pass.
    assert report.graphs < report.pages


def test_a_staged_graph_carries_absolute_urls_for_every_node(tmp_path):
    site.stage(tmp_path)
    seen = 0
    for path, view in graphed(tmp_path / "content"):
        for node in view["nodes"]:
            assert node["url"].startswith("https://dmarx.github.io/luria/"), (path, node)
            seen += 1
    assert seen > 0


def test_the_viewer_is_staged_once_at_the_site_root(tmp_path):
    site.stage(tmp_path)
    content = tmp_path / "content"
    copies = list(content.rglob(site_graph.ASSET_NAME))
    assert [p.relative_to(content) for p in copies] == [Path(site_graph.ASSET_NAME)]
    assert copies[0].read_bytes() == site_graph.ASSET.read_bytes()


def test_a_nested_records_nodes_link_through_its_mount_point(tmp_path):
    """A child is staged by its own config, which has never heard of the path
    the parent mounts it at. A URL spelled from the child's own `base_url`
    would be missing that prefix and every node would link to a 404."""
    site.stage(tmp_path)
    content = tmp_path / "content"
    nested = [(p, v) for p, v in graphed(content)
              if p.relative_to(content).parts[0] == "examples"]
    assert nested, "no nested record staged a lineage graph"
    for path, view in nested:
        mount = path.relative_to(content).parts[:2]      # examples/<record>
        for node in view["nodes"]:
            assert f"/{mount[0]}/{mount[1]}/" in node["url"], node["url"]
        # …and it points at the single root copy of the viewer, not its own.
        assert (f'src="https://dmarx.github.io/luria/{site_graph.ASSET_NAME}"'
                in path.read_text())


def test_the_graph_goes_below_the_prose_the_record_line_states(tmp_path):
    """The record line is the authoritative statement and belongs above the
    fold; the graph is where to go next. 300px between a decision's title and
    its first paragraph is a toll on every reader who came to read it."""
    site.stage(tmp_path)
    text = (tmp_path / "content" / "record" / "decisions.d" / "ADR-002.md").read_text()
    assert text.index("| **Status**") < text.index(ELEMENT)
    assert "## Lineage" in text
    assert text.rstrip().endswith("</script>")
