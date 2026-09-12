"""`[luria.site] graph` — a graph the project designed, in place of Quartz's.

The lineage graph (`test_site_graph.py`) is GENERATED from typed edges, one
per page. This is the other direction: one picture the project laid out itself
in strata-g, exported as `Canvas — graph data (JSON)`, shown on every page
where Quartz's local graph used to be.

The contract with strata-g is a file format, so one test here reads a file
that really came out of that app rather than one written to match this
module's idea of it.
"""
import json
from pathlib import Path

import pytest

from luria import site, site_graph
from luria.config import current, load

FIXTURE = Path(__file__).parent / "fixtures" / "strata_g_export.json"


def write_graph(root: Path, **over) -> Path:
    view = {
        "nodes": [
            {"id": "a", "x": 0.0, "y": 0.0, "size": 12.0, "color": "#f28e2b",
             "label": "A", "attrs": {}, "url": "https://example.test/a"},
            {"id": "b", "x": 80.0, "y": 40.0, "size": 8.0, "color": "#4e79a7",
             "label": "B", "attrs": {}, "url": "https://example.test/b"},
        ],
        "edges": [{"source": "a", "target": "b", "color": "#888", "size": 2,
                   "curvature": 0, "directed": True}],
        "background": "#1f2430", "labelColor": "#e2e8f0",
    }
    view.update(over)
    path = root / "docs" / "graphs" / "map.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(view))
    return path


def configure(root: Path, value: str, base_url: str = "example.test/rec") -> None:
    """Point the fixture project's [luria.site] at a graph.

    A `base_url` comes with it because the viewer is served from the site
    root, and the fixture's `issue_url` is not a GitHub one so nothing derives
    it. `test_a_graph_without_a_base_url_is_reported` is where its absence is
    the subject.
    """
    toml = root / "luria.toml"
    site = f'\n[luria.site]\ngraph = "{value}"\n'
    if base_url:
        site += f'base_url = "{base_url}"\n'
    toml.write_text(toml.read_text() + site)
    from luria import config as cfg_mod
    cfg_mod.reset()


# --- the file the config points at ---------------------------------------

def test_a_real_strata_g_export_is_accepted():
    """The contract between the two projects is this file format.

    Written by strata-g's `Canvas — graph data (JSON)` exporter through its
    real UI, not by hand here — a fixture that only matches what this module
    expects would pass forever while the two drifted apart.
    """
    view = site_graph.load_view(FIXTURE)
    assert view["nodes"] and all("id" in n and "x" in n for n in view["nodes"])
    assert "labelColor" in view and "background" in view


def test_a_missing_file_says_where_to_get_one(tmp_path):
    with pytest.raises(SystemExit, match="does not exist"):
        site_graph.load_view(tmp_path / "nope.json")


def test_json_that_is_not_a_graph_is_refused(tmp_path):
    (tmp_path / "x.json").write_text('{"rows": [1, 2]}')
    with pytest.raises(SystemExit, match="carries no nodes"):
        site_graph.load_view(tmp_path / "x.json")


def test_a_node_without_a_position_is_refused(tmp_path):
    (tmp_path / "x.json").write_text('{"nodes": [{"id": "a"}]}')
    with pytest.raises(SystemExit, match="no id or no position"):
        site_graph.load_view(tmp_path / "x.json")


def test_broken_json_names_the_file(tmp_path):
    (tmp_path / "x.json").write_text("{oh no")
    with pytest.raises(SystemExit, match="not valid JSON"):
        site_graph.load_view(tmp_path / "x.json")


def test_a_url_the_viewer_will_not_follow_is_reported_not_rejected(tmp_path):
    """A graph whose nodes are not links is a fine picture. A node that LOOKS
    clickable and silently is not, is not."""
    path = write_graph(tmp_path)
    view = json.loads(path.read_text())
    view["nodes"][1]["url"] = "../relative/page"
    path.write_text(json.dumps(view))
    loaded = site_graph.load_view(path)
    assert site_graph.unfollowable(loaded) == ["B"]
    # …and a graph whose links are all http(s) reports nothing, so the check
    # is not simply returning every node it is given.
    assert site_graph.unfollowable(json.loads(write_graph(tmp_path).read_text())) == []


# --- what staging does with it -------------------------------------------

def test_without_the_key_quartzs_graph_is_what_the_layout_keeps(project):
    """The default, and the control for every assertion below: unset means the
    site is exactly what it was."""
    out = project / "build" / "site"
    site.stage(out)
    assert "Component.Graph({" in (out / "quartz.layout.ts").read_text()
    for page in (out / "content").rglob("*.md"):
        assert "<strata-g-graph" not in page.read_text(), page


def test_a_graph_without_a_base_url_is_reported_rather_than_skipped(project):
    """The project asked for a graph and is not getting one; the reason is a
    different key, and only the build can say so (DP-1)."""
    write_graph(project)
    configure(project, "docs/graphs/map.json", base_url="")
    report = site.stage(project / "build" / "site")
    assert any("no base_url" in u for u in report.unplaced), report.unplaced


def test_the_configured_graph_replaces_it_on_every_page(project):
    write_graph(project)
    configure(project, "docs/graphs/map.json")
    out = project / "build" / "site"
    report = site.stage(out)

    layout = (out / "quartz.layout.ts").read_text()
    assert "Component.Graph({" not in layout, "both graphs would stack on every page"

    pages = list((out / "content").rglob("*.md"))
    assert pages, "the fixture project staged nothing"
    for page in pages:
        assert "<strata-g-graph " in page.read_text(), page
    assert report.unplaced == []


def test_the_graph_sits_where_quartzs_did_above_the_heading(project):
    """The swap is positional as well as functional: a reader who knew where
    to look for the graph still finds it there."""
    write_graph(project)
    configure(project, "docs/graphs/map.json")
    out = project / "build" / "site"
    site.stage(out)
    page = next(p for p in (out / "content").rglob("*.md")
                if "# " in p.read_text())
    text = page.read_text()
    body = text.split("---\n", 2)[-1] if text.startswith("---") else text
    assert body.index("<strata-g-graph ") < body.index("# ")


def test_the_viewer_is_staged_even_when_no_page_has_lineage(project):
    """The configured graph is a reference to the viewer like any other, and
    a project with no typed edges at all still needs the file served."""
    write_graph(project)
    configure(project, "docs/graphs/map.json")
    out = project / "build" / "site"
    report = site.stage(out)
    assert report.graphs == 0, "this fixture has no lineage — that is the point"
    assert (out / "content" / site_graph.ASSET_NAME).exists()
