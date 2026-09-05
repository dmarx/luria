"""What `luria site` publishes, and what it refuses to.

The load-bearing property is the second one: a source whose prose renders
into a view somewhere else must not be staged in place, because its links are
spelled for the view's directory. That rule is derived from `link_base`, so
these tests assert the *invariant* over the real corpus rather than a list of
directories that would drift the day one moved (DP-3).
"""
import re
from pathlib import Path

import pytest

from luria import adr_index, config, site
from luria.config import current, load, rooted

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


def test_the_action_copies_everything_the_staging_writes(tmp_path):
    """The pair that has to move together. `stage` gained a second generated
    file and the action did not copy it — a whole layout silently reverting
    to Quartz's default is exactly the drift DP-3 says to guard as a
    property, not as a list somebody remembers to extend.

    It matches `cp` commands rather than mentions. The first version of this
    test asked whether the name appeared anywhere in the action, which a
    directory called `static` satisfies from any of the three other lines
    that say `quartz/static/` — a guard that passes for a reason unrelated to
    what it checks is not a guard."""
    site.stage(tmp_path)
    staged = {p.name for p in tmp_path.iterdir() if p.name != "content"}
    action = (current().root / "actions" / "site" / "action.yml").read_text()
    copied = set(re.findall(r"^\s*cp\b[^\n]*luria-site/([\w.-]+)", action,
                            re.MULTILINE))
    assert staged, "nothing staged beside content/ — the guard would be vacuous"
    assert staged <= copied, f"actions/site never copies {staged - copied}"


def test_the_palette_merges_over_the_generators_defaults():
    """A project names the colours it cares about; the rest stay Quartz's."""
    block = site.colors(current().site)
    assert 'light: "#f4f1e8"' in block          # this project's paper
    assert 'fontOrigin' not in block            # only the colour block
    for mode in ("lightMode", "darkMode"):
        assert f"{mode}: {{" in block
    for name in site.THEME_DEFAULTS["light"]:
        assert f"{name}: " in block, f"{name} dropped from the palette"


def test_an_unknown_colour_name_is_refused_by_name():
    """Silently dropping a key is a project wondering why its brand didn't
    take (DP-1)."""
    from luria.config import Site
    broken = Site(title="t", base_url="", source_url="",
                  theme={"light": {"lightt": "#fff"}})
    with pytest.raises(SystemExit) as caught:
        site.colors(broken)
    assert "lightt" in str(caught.value)


def test_the_icon_is_staged_as_the_vector_master(tmp_path):
    """Not rasterized here and not committed anywhere: `actions/site` renders
    it with the generator's own `sharp`, so nothing derived from the artwork
    exists in the repository to drift (DP-3)."""
    site.stage(tmp_path)
    assert (tmp_path / "static" / "icon.svg").exists()


def test_the_logo_is_baked_once_per_theme(tmp_path):
    site.stage(tmp_path)
    light = (tmp_path / "static" / "logo-light.svg").read_text()
    dark = (tmp_path / "static" / "logo-dark.svg").read_text()
    assert f"{site.INK_VAR}:#111111" in light
    assert f"{site.INK_VAR}:#f4f1e8" in dark
    scss = (tmp_path / "custom.scss").read_text()
    assert 'url("static/logo-light.svg")' in scss
    assert '[saved-theme="dark"]' in scss
    # The aspect comes from the artwork, so a different lockup still fits.
    assert "aspect-ratio: 1177.0 / 340.0" in scss


def test_artwork_that_cannot_be_re_inked_is_left_alone():
    plain = '<svg viewBox="0 0 10 5"><path fill="#000" d="M0 0"/></svg>'
    assert site._reinked(plain, "#ffffff") == plain


def test_missing_artwork_is_named_not_skipped(project):
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.site]\nicon = "nope/icon.svg"\nlogo = "nope/logo.svg"\n')
    from luria import config as config_module
    config_module.reset()
    report = site.stage(project / "build" / "site")
    assert any("icon" in line and "no such file" in line
               for line in report.unplaced)
    assert any("logo" in line for line in report.unplaced)


def test_a_project_with_no_artwork_still_gets_a_stylesheet(project):
    site.stage(project / "build" / "site")
    scss = (project / "build" / "site" / "custom.scss").read_text()
    assert scss.startswith("// GENERATED")
    assert '@use "./base.scss";' in scss
    assert ".page-title" not in scss


# --- nested records (ADR-077) -------------------------------------------

def parent(tmp_path, monkeypatch, include='include_records = ["sub/*"]') -> Path:
    """A minimal record that publishes whatever `include` names.

    `include_records` sits in `[luria]`, not `[luria.site]`: it says this
    project contains other projects, which `luria index` needs as much as the
    site does (ADR-078)."""
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        f"{include}\n")
    (tmp_path / "README.md").write_text("# Parent\n\nThe outer record.\n")
    (tmp_path / "docs" / "README.md").write_text("# Docs\n\nNothing here.\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def child(root: Path, name: str) -> Path:
    """A complete little record inside `root`, carrying a scheme the parent
    has never heard of — which is the condition the mount exists for."""
    place = root / "sub" / name
    (place / "record" / "notes.d").mkdir(parents=True)
    (place / "luria.toml").write_text(f"""
[luria]
issue_url = "https://example.test/{name}/issues/{{n}}"
[luria.site]
title = "{name}"
[luria.schemes.NOTE]
dir = "record/notes.d"
output = "docs/notes.md"
render = "document"
""")
    (place / "record" / "notes.d" / "NOTE-001.md").write_text(
        "---\nstatus: Active\ntitle: 'One'\nversion: 1\ntags: [x]\n"
        "date: '2026-01-01'\n---\n\n# NOTE-001: One\n\nBody.\n")
    (place / "README.md").write_text(f"# {name}\n\nA nested record.\n")
    # A nested record's views are committed and regenerated with the parent's
    # (ADR-078), so staging reads them rather than building them. Generating
    # here is what a `luria index` at the root would have done.
    with rooted(place):
        adr_index.run()
    config.reset()
    return place


def test_a_nested_record_is_staged_by_its_own_config(tmp_path, monkeypatch):
    """The whole point, and the reason a merge would not do.

    `publishable()` tells a source from a view with
    `link_base(path) != path.parent`, and `link_base` answers from the
    *reading* config's schemes. The parent has no NOTE scheme, so under the
    parent's config `NOTE-001.md` reads as ordinary prose and would be
    published beside `docs/notes.md`, the document it renders into. Staged by
    the child's own config, only the view appears."""
    root = parent(tmp_path, monkeypatch)
    child(root, "alpha")
    report = site.stage(tmp_path / "vault")
    content = tmp_path / "vault" / "content"

    assert (content / "sub" / "alpha" / "docs" / "notes.md").exists()
    assert not (content / "sub" / "alpha" / "record" / "notes.d" / "NOTE-001.md").exists(), (
        "the child's document-scheme source was published beside its assembled "
        "view, which is what happens when the parent's config does the staging"
    )
    assert report.nested.get("sub/alpha", 0) > 0
    assert report.pages > report.nested["sub/alpha"], (
        "the parent's own pages are missing from the total"
    )


def test_a_nested_record_gets_its_own_landing_page(tmp_path, monkeypatch):
    """The child's README becomes the section's index, titled from the child's
    own `site.title`. Without it a link to the section lands on nothing — the
    examples had no root README and mounted as a directory with no front
    page."""
    root = parent(tmp_path, monkeypatch)
    child(root, "alpha")
    site.stage(tmp_path / "vault")
    index = tmp_path / "vault" / "content" / "sub" / "alpha" / "index.md"
    assert index.exists(), "the nested section has no landing page"
    text = index.read_text()
    assert 'title: "alpha"' in text, "titled from the parent's config, not its own"
    assert '"README"' in text, "the section's old address must keep answering"


def test_include_records_implies_exclusion_from_the_parent_pass(tmp_path, monkeypatch):
    """Without this the merge reintroduces what the mount solves.

    Asserted against the parent's file list rather than the staged vault,
    because from the vault the two failures are indistinguishable: a child file
    published by the parent and one mounted by the child both land under
    `sub/alpha/`."""
    root = parent(tmp_path, monkeypatch)
    place = child(root, "alpha")
    published = site.publishable(current())
    assert published, "the parent published nothing; the assertion below is vacuous"
    assert not [p for p in published if place in p.parents], (
        "the parent's own pass picked up files inside a nested record"
    )


def test_a_pattern_matching_no_record_is_an_error(tmp_path, monkeypatch):
    """A silently empty include is a section of the site that does not exist,
    and nothing else would report it (DP-1). A directory that is not a record
    is a different case and stays a quiet skip — `sub/*` is the natural way to
    write "every one of these", and a stray directory beside them should not
    break a publish."""
    root = parent(tmp_path, monkeypatch)
    (root / "sub" / "not-a-record").mkdir(parents=True)
    with pytest.raises(ValueError, match="matched no record"):
        site.stage(tmp_path / "vault")

    child(root, "alpha")
    config.reset()
    report = site.stage(tmp_path / "vault")
    assert set(report.nested) == {"sub/alpha"}, (
        "the non-record directory beside it should have been skipped quietly"
    )


def test_staging_a_child_leaves_the_parent_config_current(tmp_path, monkeypatch):
    """`rooted()` restores what it swapped. A leaked `LURIA_ROOT` would make
    every later call in the process read the child's record instead."""
    root = parent(tmp_path, monkeypatch)
    child(root, "alpha")
    before = current().root
    site.stage(tmp_path / "vault")
    assert current().root == before
    assert "NOTE" not in current().schemes


def test_a_nested_record_is_regenerated_by_the_parents_index(tmp_path, monkeypatch):
    """`luria index` at the root writes a nested record's views too (ADR-078).

    This is the half that makes committing them safe. A committed view is only
    as good as the thing that regenerates it, and before this the parent's
    index did not know the child existed — so the views were gitignored, and
    the examples were the one place in this repository where a view could not
    be browsed at all.
    """
    root = parent(tmp_path, monkeypatch)
    place = child(root, "alpha")
    view = place / "docs" / "notes.md"
    assert view.exists(), "the fixture did not generate; the rest proves nothing"

    view.write_text("stale\n")
    config.reset()
    assert adr_index.staleness().stale, (
        "a stale view inside a nested record is invisible to the parent's "
        "staleness check, so nothing would ever notice it drifting"
    )

    adr_index.run()
    assert not adr_index.staleness().stale
    # The child's document, rendered by the child's config. `render_document`
    # demotes the fragment's H1 and renumbers it, so the code does not survive
    # literally — the stable anchor does, which is the point of having one.
    text = view.read_text()
    assert '<a name="note-1">' in text and "Body." in text, (
        "the parent's index wrote the file but rendered none of the child's "
        "documents into it — which is what happens when the PARENT's config "
        "does the rendering, since it has no NOTE scheme"
    )


def test_an_orphan_in_a_nested_view_directory_is_an_orphan(tmp_path, monkeypatch):
    """`view_dirs` reaches into nested records for the same reason `outputs`
    does: a stale page left in a child's view directory reads as generated,
    and the parent is the only thing running the check.

    An index-render scheme, because only those own a view *directory* — a
    document scheme owns one file, and a stray beside it is somebody's prose,
    not an orphan."""
    root = parent(tmp_path, monkeypatch)
    place = root / "sub" / "beta"
    (place / "record" / "memos.d").mkdir(parents=True)
    (place / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/beta/issues/{n}"\n'
        '[luria.schemes.MEMO]\ndir = "record/memos.d"\n'
        'output = "docs/memos"\nrender = "index"\n')
    (place / "record" / "memos.d" / "MEMO-001.md").write_text(
        "---\nstatus: Active\ntitle: 'One'\nversion: 1\ntags: [x]\n"
        "date: '2026-01-01'\n---\n\n# MEMO-001: One\n\nBody.\n")
    (place / "README.md").write_text("# beta\n\nA nested record.\n")
    with rooted(place):
        adr_index.run()
    config.reset()

    assert not adr_index.staleness().orphaned, (
        "already orphaned before the stray was planted; the assertion below "
        "would pass for the wrong reason"
    )
    stray = place / "docs" / "memos" / "ZZZ.md"
    stray.write_text("# stray\n")
    config.reset()
    assert any(p.name == "ZZZ.md" for p in adr_index.staleness().orphaned), (
        "an unrendered file in a nested record's view directory went unreported"
    )
