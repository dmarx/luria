# tests/test_site_page.py
"""The staged page's frontmatter — what Quartz titles a page and what its
properties panel shows (ADR-121).

The bug this module exists for: Quartz 5 parses frontmatter only in its
`note-properties` plugin, and without it every page was untitled — blank
search results, graph nodes labelled with their paths — and the YAML
rendered as a paragraph above the page (dmarx/anthology-of-the-sota#271)."""
from pathlib import Path

import yaml

from luria import site, site_page
from luria.config import current

# unresolved-ok-file: ADR-919 — a fixture code, deliberately not real: the
# point of the test it appears in is that it resolves to nothing.


def _adr(n: int) -> Path:
    return current().schemes["ADR"].dir / f"ADR-{n:03d}.md"


def test_properties_carry_status_date_and_lineage():
    meta = {"status": "Active", "date": "2026-08-04", "issue": "#9",
            "influenced_by": ["ADR-005", "ADR-024"]}
    props, unresolved = site_page.properties(meta, _adr(25))
    assert unresolved == []
    assert props["Status"] == "Active"
    # The date is Quartz's to show, from its own key: not repeated here.
    assert "Filed" not in props
    # Resolved by the record's own resolver, then spelled from the vault
    # root — the form the plugin resolves without ambiguity.
    first, second = props["Influenced by"]
    assert first.startswith("[[record/decisions.d/ADR-005|ADR-005]] — ")
    assert second.startswith("[[record/decisions.d/ADR-024|ADR-024]] — ")
    assert props["Issue"] == "[#9](https://github.com/dmarx/luria/issues/9)"


def test_every_issue_in_the_field_is_read():
    """`issue: '#21, #23'` is a shape this record actually uses."""
    props, _ = site_page.properties({"issue": "#21, #23"}, current().index)
    assert [("issues/21" in v, "issues/23" in v) for v in props["Issue"]] == [
        (True, False), (False, True)]


def test_no_facts_no_properties():
    assert site_page.properties({}, current().index) == ({}, [])


def test_version_appears_only_when_it_is_not_one():
    assert "Version" not in site_page.properties({"version": 1}, _adr(1))[0]
    assert site_page.properties({"version": 2}, _adr(1))[0]["Version"] == "2"


def test_a_nested_record_links_through_its_mount_point():
    props, _ = site_page.properties({"influenced_by": ["ADR-005"]}, _adr(25),
                                    prefix="examples/child")
    assert props["Influenced by"].startswith(
        "[[examples/child/record/decisions.d/ADR-005|ADR-005]]")


def test_an_unresolvable_code_is_reported_not_linked():
    props, unresolved = site_page.properties(
        {"influenced_by": ["ADR-919"]}, _adr(25))
    assert props["Influenced by"] == "[[ADR-919]]"
    assert unresolved == ["[[ADR-919]]"]


def test_a_title_carries_its_code_once():
    assert site_page.title_of({"title": "A thing"}, "", "ADR-001") == (
        "ADR-001: A thing")
    assert site_page.title_of({"title": "ADR-001: A thing"}, "", "ADR-001") == (
        "ADR-001: A thing")


def test_a_page_with_no_frontmatter_is_titled_by_its_heading():
    body = "<!-- GENERATED -->\n\n# Curation log — `2026`\n\nText.\n"
    assert site_page.title_of({}, body, None) == "Curation log — 2026"


def test_a_heading_inside_code_is_not_a_title():
    body = "```sh\n# not a title\n```\n\n# The title\n"
    assert site_page.title_of({}, body, None) == "The title"


def test_the_heading_the_title_repeats_is_dropped_and_no_other():
    body = "# ADR-001: A thing\n\nText.\n\n# Another\n"
    assert site_page.without_title(body, "ADR-001: A thing") == (
        "Text.\n\n# Another\n")
    assert site_page.without_title(body, "Something else") == body


def test_a_title_that_looks_like_syntax_is_not_a_link():
    """This project's ADR-025 is titled ``Wikilinks: `[[CODE]]` is a typed
    reference``. As a title or a property value, a literal `[[` would be
    read as a link by the plugin and by luria's own resolver."""
    assert "[[" not in site_page.plain(site_page.titles()["ADR-025"])


def test_every_staged_page_is_titled(tmp_path):
    """The whole record, not a fixture: an untitled page is a blank search
    result, which is how this was reported."""
    site.stage(tmp_path)
    untitled = []
    for page in (tmp_path / "content").rglob("*.md"):
        text = page.read_text()
        front = (yaml.safe_load(text[4:text.index("\n---\n", 3)])
                 if text.startswith("---\n") else {})
        if not str((front or {}).get("title") or "").strip():
            untitled.append(page.relative_to(tmp_path).as_posix())
    assert untitled == []


def test_the_plugin_that_parses_frontmatter_is_configured(tmp_path):
    """The regression itself: Quartz 5 has no other frontmatter parser."""
    site.stage(tmp_path)
    config = yaml.safe_load((tmp_path / "quartz.config.yaml").read_text())
    plugin = next(p for p in config["plugins"]
                  if p["source"] == "@quartz-community/note-properties")
    assert plugin["enabled"] and plugin["order"] < 10
    assert plugin["options"]["includeAll"] is True
    assert "title" in plugin["options"]["excludedProperties"]
    assert plugin["layout"]["position"] == "beforeBody"
