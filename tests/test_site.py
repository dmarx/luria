"""What `luria site` publishes, and what it refuses to.

The load-bearing property is the second one: a source whose prose renders
into a view somewhere else must not be staged in place, because its links are
spelled for the view's directory. That rule is derived from `link_base`, so
these tests assert the *invariant* over the real corpus rather than a list of
directories that would drift the day one moved (DP-3).
"""
from pathlib import Path

import pytest

from luria import site
from luria.config import current, load

from _scheme import decision

# unresolved-ok-file: ADR-919 — a fixture code, deliberately not real: the
# point of the test it appears in is that it resolves to nothing.


def test_publishes_the_decisions_and_the_generated_views():
    published = {current().rel(p) for p in site.publishable()}
    assert "record/decisions.d/ADR-025.md" in published
    assert "docs/decisions/README.md" in published
    assert "docs/design-principles.md" in published
    assert "README.md" in published


def test_never_publishes_a_source_that_renders_somewhere_else():
    """Fragments, journal entries and a document-scheme's sources all write
    links for the page they land in — staging them in place would break every
    one, and duplicate the view besides."""
    cfg = current()
    published = {cfg.rel(p) for p in site.publishable()}
    assert not [p for p in published if p.startswith("record/changelog.d/")]
    assert not [p for p in published if p.startswith("record/devlog.d/")]
    assert not [p for p in published if p.startswith("record/principles.d/")]


def test_publishable_is_exactly_the_files_whose_links_resolve_in_place():
    """The invariant, not the list: whatever the layout becomes, a published
    page is one a reader can follow the links of from where it sits."""
    cfg = current()
    for path in site.publishable():
        assert cfg.link_base(path) == path.parent, cfg.rel(path)


def test_excludes_are_honoured():
    cfg = current()
    assert "template/**" in cfg.site.exclude
    published = {cfg.rel(p) for p in site.publishable()}
    assert not [p for p in published if p.startswith("template/")]
    assert not [p for p in published if p.endswith("_template.md")]


def test_readme_becomes_the_landing_page():
    cfg = current()
    assert site.destination(cfg.root / "README.md", cfg) == Path("index.md")
    assert (site.destination(cfg.root / "docs" / "README.md", cfg)
            == Path("docs/README.md"))


def test_site_defaults_derive_from_the_issue_url():
    s = current().site
    assert s.title == "luria"
    assert s.base_url == "dmarx.github.io/luria"
    assert s.source_url == "https://github.com/dmarx/luria/blob/HEAD"


def test_site_defaults_stay_empty_without_a_github_issue_url(project):
    """No guessing: a project Luria cannot identify gets empty URLs, which
    `luria site` reports rather than inventing a domain for (DP-1)."""
    s = load(project).site
    assert s.base_url == ""
    assert s.source_url == ""
    assert s.title == project.name


def test_record_line_carries_status_date_and_lineage():
    meta = {"status": "Active", "date": "2026-08-04", "issue": "#9",
            "influenced_by": ["ADR-005", "ADR-024"]}
    line = site.record_line(meta, current().schemes["ADR"].dir / "ADR-025.md")
    assert line.startswith("> ")
    assert "**Status** Active" in line
    assert "**Filed** 2026-08-04" in line
    # Wikilinks in, resolved links out — the fixer owns every target (DP-4).
    assert "[ADR-005](ADR-005.md)" in line
    assert "[ADR-024](ADR-024.md)" in line
    assert "[#9](https://github.com/dmarx/luria/issues/9)" in line


def test_record_line_reads_every_issue_in_the_field():
    """`issue: '#21, #23'` is a shape this record actually uses, so the
    separator is read out of the field rather than assumed."""
    line = site.record_line({"issue": "#21, #23"}, current().index)
    assert "issues/21" in line and "issues/23" in line


def test_record_line_is_empty_without_frontmatter_facts():
    assert site.record_line({}, current().index) == ""


def test_version_appears_only_when_it_is_not_one():
    where = current().schemes["ADR"].dir / "ADR-001.md"
    assert "**Version**" not in site.record_line({"version": 1}, where)
    assert "**Version** 2" in site.record_line({"version": 2}, where)


def test_staged_decision_gets_its_code_as_an_alias(tmp_path):
    site.stage(tmp_path)
    staged = (tmp_path / "content" / "record" / "decisions.d"
              / "ADR-025.md").read_text()
    assert '\naliases:\n- "ADR-025"\n' in staged
    # The frontmatter that was already there is carried over verbatim.
    assert "status: Active" in staged
    assert "> **Status** Active" in staged


def test_staging_is_idempotent_and_drops_removed_pages(tmp_path):
    site.stage(tmp_path)
    stray = tmp_path / "content" / "docs" / "gone.md"
    stray.write_text("# Gone\n")
    site.stage(tmp_path)
    assert not stray.exists()


def test_a_staging_directory_inside_the_project_is_not_republished(project):
    """The default `--out build/site` sits in the tree Luria scans. Without
    the skip, the second run publishes the first run's output."""
    decision(project, 1, "Active")
    out = project / "build" / "site"
    first = site.stage(out)
    second = site.stage(out)
    assert first.pages == second.pages
    assert not (out / "content" / "build").exists()


def test_config_is_written_with_the_project_title(tmp_path):
    site.stage(tmp_path)
    config = (tmp_path / "quartz.config.ts").read_text()
    assert 'pageTitle: "luria"' in config
    assert 'baseUrl: "dmarx.github.io/luria"' in config
    # The two settings the record depends on, guarded because a Quartz upgrade
    # is exactly where a default would quietly come back (DP-3).
    assert 'markdownLinkResolution: "relative"' in config
    assert '"frontmatter", "filesystem"' in config


def test_links_out_of_the_site_go_to_the_repository(tmp_path):
    report = site.stage(tmp_path)
    index = (tmp_path / "content" / "index.md").read_text()
    assert "https://github.com/dmarx/luria/blob/HEAD/LICENSE" in index
    assert report.to_source > 0
    assert report.unplaced == []


def test_a_quoted_path_is_never_retargeted(tmp_path):
    """Code is a specimen, not a claim (ADR-008). Rewriting a path inside a
    fence would edit the example the prose is teaching."""
    site.stage(tmp_path)
    text = (tmp_path / "content" / "docs" / "adopting.md").read_text()
    assert "```" in text
    for fence_body in text.split("```")[1::2]:
        assert "blob/HEAD" not in fence_body


def test_pages_land_at_their_repository_paths(tmp_path):
    """Preserved paths are what let the record's own relative links keep
    resolving — the whole reason no second link resolver exists here."""
    site.stage(tmp_path)
    content = tmp_path / "content"
    assert (content / "record" / "decisions.d" / "ADR-001.md").exists()
    assert (content / "docs" / "decisions" / "README.md").exists()
    assert (content / "docs" / "devlog" / "2026-08.md").exists()
    assert not (content / "README.md").exists()


@pytest.mark.parametrize("target,expected", [
    ("../../record/decisions.d/../../docs/design-principles.md#dp-2",
     "../../docs/design-principles.md#dp-2"),
    ("ADR-024.md", "ADR-024.md"),
    ("#anchor-only", "#anchor-only"),
])
def test_index_normalizes_rebased_targets(target, expected):
    """The bug the site build found (#13): concatenation alone leaves
    `a/../b`, which GitHub forgives and a static site generator does not."""
    from luria.adr_index import _normalize
    assert _normalize(target) == expected


def test_an_unresolvable_influence_is_counted_not_swallowed(project):
    """`influenced_by` is frontmatter — data, which the prose scanner never
    reads — so an unexpandable code there has no other place to be seen."""
    path = decision(project, 1, "Active")
    path.write_text(path.read_text().replace(
        "date: '2026-01-01'", "date: '2026-01-01'\ninfluenced_by:\n- ADR-919"))
    report = site.stage(project / "build" / "site")
    assert any("ADR-919" in line for line in report.unplaced)


def test_a_superseded_decision_says_so_on_its_page(project):
    """Status lives in frontmatter, which renders as nothing — so on a site a
    retired decision reads as current unless the staging says otherwise."""
    decision(project, 1, "Active")
    decision(project, 2, "Superseded — by [ADR-001](ADR-001.md)")
    out = project / "build" / "site"
    site.stage(out)
    staged = (out / "content" / "record" / "decisions.d"
              / "ADR-002.md").read_text()
    assert "> **Status** Superseded — by [ADR-001](ADR-001.md)" in staged


def test_an_html_image_is_staged_beside_its_page(tmp_path):
    """`<img src>` is how a README centres a banner — markdown isn't parsed
    inside an HTML block — and an unrecognised shape is worse than a wrong
    one: it is neither staged, nor redirected, nor counted (#70)."""
    report = site.stage(tmp_path)
    banner = (tmp_path / "content" / "assets" / "branding"
              / "luria-brainslug"
              / "luria_project_memory_lockup_horizontal.svg")
    assert banner.exists()
    assert report.assets >= 1


def test_the_landing_page_is_named_and_still_answers_to_README(tmp_path):
    site.stage(tmp_path)
    index = (tmp_path / "content" / "index.md").read_text()
    assert index.startswith('---\ntitle: "luria"\n')
    assert 'aliases:\n- "README"' in index


def test_the_graph_sits_above_the_article_not_in_the_sidebar(tmp_path):
    """Quartz's sidebars stack below the content under 1200px, so a graph in
    the right rail is at the bottom of the page on most windows (#71)."""
    site.stage(tmp_path)
    layout = (tmp_path / "quartz.layout.ts").read_text()
    before, _, right = layout.partition("right: [")
    assert "Component.Graph(" in before.split("left: [")[0]
    assert "Component.Graph(" not in right


def test_the_action_copies_every_file_the_staging_writes(tmp_path):
    """The pair that has to move together. `stage` gained a second generated
    file and the action did not copy it — a whole layout silently reverting
    to Quartz's default is exactly the drift DP-3 says to guard as a
    property, not as a list somebody remembers to extend."""
    site.stage(tmp_path)
    written = {p.name for p in tmp_path.iterdir() if p.is_file()}
    action = (current().root / "actions" / "site" / "action.yml").read_text()
    for name in written:
        assert name in action, f"actions/site never copies {name}"
