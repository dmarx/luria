# tests/test_page_title.py
"""How the published site names a page is a template (#405, part 3).

`site.page_title` is a template over `{code}` and `{title}`, defaulting to
`{code}: {title}`, today's form, so a graph node or search card still matches
the code a reader followed. A record that labels by title alone sets
`"{title}"`. Either way, a body heading that repeats the page title, with or
without the code, is dropped so the page does not print it twice."""
from _config import merged

import pytest

from luria import config, site_page
from luria.config import current


def test_the_default_page_title_carries_the_code():
    assert site_page.title_of({"title": "A thing"}, "", "ADR-001") == (
        "ADR-001: A thing")


def test_a_bare_template_titles_the_page_by_its_title_alone():
    assert site_page.title_of({"title": "A thing"}, "", "ADR-001",
                              "{title}") == "A thing"


def test_a_title_already_carrying_its_code_is_not_doubled():
    assert site_page.title_of({"title": "ADR-001: A thing"}, "", "ADR-001",
                              "{title}") == "A thing"
    assert site_page.title_of({"title": "ADR-001: A thing"}, "", "ADR-001") == (
        "ADR-001: A thing")


def test_a_page_without_a_code_is_titled_as_before():
    assert site_page.title_of({"title": "Curation"}, "", None, "{title}") == (
        "Curation")


def test_a_coded_heading_is_dropped_under_a_bare_page_title():
    body = "# ADR-001: A thing\n\nText.\n"
    assert site_page.without_title(body, "A thing", "ADR-001") == "Text.\n"


def test_an_unrelated_heading_is_kept_under_either_template():
    body = "# Something else\n\nText.\n"
    assert site_page.without_title(body, "A thing", "ADR-001") == body
    assert site_page.without_title(body, "ADR-001: A thing", "ADR-001") == body


def test_the_site_reads_its_page_title_template(project):
    path = project / "luria.yaml"
    path.write_text(merged(path.read_text(), {"site": {"page_title": "{title}"}}))
    config.reset()
    assert current().site.page_title == "{title}"


def test_the_page_title_defaults_to_the_coded_form(project):
    config.reset()
    assert current().site.page_title == "{code}: {title}"


@pytest.mark.parametrize("bad", ["{code}", "{title} {name}"])
def test_a_page_title_template_without_the_title_or_with_strangers_is_refused(
        project, bad):
    path = project / "luria.yaml"
    path.write_text(merged(path.read_text(), {"site": {"page_title": bad}}))
    config.reset()
    with pytest.raises(ValueError, match="page_title"):
        current()


def test_a_staged_page_follows_the_template_and_drops_its_heading(
        project, tmp_path_factory):
    """End to end: luria.yaml → `luria site`'s staging → the page Quartz
    reads."""
    import yaml
    from luria import site
    from tests._scheme import decision
    path = project / "luria.yaml"
    path.write_text(merged(path.read_text(), {"site": {"page_title": "{title}"}}))
    config.reset()
    decision(project, 1, "Active")
    doc = current().schemes["ADR"].documents()[1]
    title = yaml.safe_load(doc.read_text().split("---\n")[1])["title"]
    out = tmp_path_factory.mktemp("site")
    site.stage(out)
    page = next(p for p in (out / "content").rglob("*.md")
                if "ADR-001" in p.name or "adr-001" in p.as_posix().lower())
    text = page.read_text()
    front = yaml.safe_load(text[4:text.index("\n---\n", 3)])
    assert front["title"] == title
    assert f"# ADR-001: {title}" not in text and f"\n# {title}\n" not in text
