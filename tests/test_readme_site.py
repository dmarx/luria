"""The README's link to the published site (#197).

`luria site` knows where the record will live — `Site.base_url` derives from
`issue_url` with no configuration — and until now nothing wrote it anywhere a
reader of the repository front page could see it. Luria's own README carried a
hand-typed link on the line *after* the region `luria index` rewrites, which
is the projection DP-3 is about.
"""
from pathlib import Path

from luria import config, lint, readme, site
from luria.config import current

BASE = ('[luria]\nissue_url = "https://github.com/dmarx/demo/issues/{n}"\n'
        '[luria.schemes.ADR]\ndir = "docs/decisions"\n')
PUBLISHES = BASE + '[luria.site]\nexclude = []\n'
UNPUBLISHED = BASE + '[luria.site]\npublish = false\n'


def at(project, toml: str) -> Path:
    (project / "luria.toml").write_text(toml)
    config.reset()
    return project


# ── the region ───────────────────────────────────────────────────────────

def test_the_region_carries_the_derived_url(project):
    at(project, PUBLISHES)
    body = site.readme_region()
    assert "dmarx.github.io/demo" in body
    assert "https://dmarx.github.io/demo/" in body


def test_a_project_that_derives_no_url_renders_nothing(project):
    """A non-GitHub issue URL derives no base_url, and inventing one would be
    a link to a page that does not exist."""
    at(project, '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
                '[luria.schemes.ADR]\ndir = "docs/decisions"\n'
                '[luria.site]\nexclude = []\n')
    assert site.readme_region() == ""


def test_rewrite_replaces_only_the_named_region(project):
    at(project, PUBLISHES)
    o, c = readme.markers("site")
    text = f"# Title\n\n{o}\nstale\n{c}\n\nProse.\n"
    out = readme.rewrite(text, "site", site.readme_region())
    assert out.startswith("# Title") and out.endswith("Prose.\n")
    assert "stale" not in out and "dmarx.github.io/demo" in out


def test_a_readme_without_the_region_is_left_alone(project):
    at(project, PUBLISHES)
    text = "# Title\n\nNo region here.\n"
    assert readme.rewrite(text, "site", site.readme_region()) == text


def test_rewriting_twice_changes_nothing(project):
    at(project, PUBLISHES)
    o, c = readme.markers("site")
    once = readme.rewrite(f"{o}\n{c}\n", "site", site.readme_region())
    assert readme.rewrite(once, "site", site.readme_region()) == once


def test_the_two_regions_do_not_collide(project):
    """`luria:badges` and `luria:site` are separate markers so a project can
    take one without the other, and so neither region's meaning has to widen
    to hold the other's content."""
    at(project, PUBLISHES)
    assert readme.markers("site") != readme.markers("badges")
    bo, bc = readme.markers("badges")
    so, sc = readme.markers("site")
    text = f"{bo}\nBADGES\n{bc}\n\n{so}\nSITE\n{sc}\n"
    out = readme.rewrite(text, "site", site.readme_region())
    assert "BADGES" in out and "SITE" not in out


# ── the finding ──────────────────────────────────────────────────────────

def test_a_record_that_publishes_and_does_not_link_is_reported(project):
    at(project, PUBLISHES)
    (project / "README.md").write_text("# Demo\n\nNothing about the site.\n")
    found = lint.unlinked_site()
    assert found and "dmarx.github.io/demo" in found[0]


def test_a_hand_written_link_satisfies_it(project):
    """The finding is 'your README does not point at the site you publish',
    not 'you must use our marker'. A project that wrote the link in its own
    prose has already done the thing."""
    at(project, PUBLISHES)
    (project / "README.md").write_text(
        "# Demo\n\nRead it at https://dmarx.github.io/demo/ if you like.\n")
    assert lint.unlinked_site() == []


def test_a_record_that_does_not_publish_is_not_reported(project):
    """`base_url` derives for every GitHub project whether or not anyone
    deploys, so it cannot scope this on its own. A record that lives only in
    its repository says so, and the guard goes quiet — a guard opts out
    rather than being argued with (DP-10)."""
    at(project, UNPUBLISHED)
    (project / "README.md").write_text("# Demo\n\nNothing.\n")
    assert lint.unlinked_site() == []


def test_a_record_with_no_readme_is_not_reported(project):
    at(project, PUBLISHES)
    (project / "README.md").unlink(missing_ok=True)
    assert lint.unlinked_site() == []


def test_lurias_own_readme_links_its_site():
    """Fired on the real corpus, not only a fixture: the repository this
    ships from publishes a site and must say so on its front page."""
    text = (Path(__file__).resolve().parents[1] / "README.md").read_text()
    assert "dmarx.github.io/luria" in text
