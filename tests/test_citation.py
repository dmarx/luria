"""The README's BibTeX block, derived from `CITATION.cff`.

Two places want the same facts — GitHub reads the `.cff` for its "Cite this
repository" button, and a README reader wants a block to paste. Writing both
by hand is the drift DP-3 names, and a citation is a bad thing to have two
versions of: the wrong one is the one that reaches somebody's bibliography.
"""

import pytest

from luria import adr_index, citation, config

CFF = """\
cff-version: 1.2.0
title: "Luria: project memory"
type: software
authors:
  - family-names: Marx
    given-names: David
repository-code: https://github.com/dmarx/luria
license: MIT
"""


@pytest.fixture
def cited(project):
    def build(cff=CFF, readme=None):
        if cff is not None:
            (project / "CITATION.cff").write_text(cff)
        if readme is not None:
            (project / "README.md").write_text(readme)
        config.reset()
        return project
    return build


# --- rendering -----------------------------------------------------------

def test_a_person_renders_family_then_given(cited):
    cited()
    assert "author  = {Marx, David}" in citation.entry()


def test_an_entity_author_is_braced(cited):
    """BibTeX splits an unbraced name on the last space, which turns a lab
    into a surname."""
    cited(CFF.replace("  - family-names: Marx\n    given-names: David\n",
                      "  - name: The Luria Project\n"))
    assert "author  = {{The Luria Project}}" in citation.entry()


def test_several_authors_join_with_and(cited):
    cited(CFF.replace("    given-names: David\n",
                      "    given-names: David\n  - family-names: Doe\n"
                      "    given-names: Jane\n"))
    assert "{Marx, David and Doe, Jane}" in citation.entry()


def test_the_key_is_the_surname_and_the_first_title_word(cited):
    """A slice of the title produced `luriaprojectmemoryk`, which is a key
    nobody would type twice."""
    cited()
    assert citation.entry().startswith("@software{marx_luria,")


def test_the_key_does_not_move_with_the_version(cited):
    """A key that changed per release would break every bibliography that had
    already used it."""
    cited()
    before = citation.entry().splitlines()[0]
    cited(CFF + "version: 9.9.9\n")
    after = citation.entry()
    assert after.splitlines()[0] == before
    assert "version = {9.9.9}" in after, "the version still reaches the entry" 


def test_a_release_date_becomes_the_year(cited):
    cited(CFF + "date-released: '2026-08-25'\n")
    assert "year    = {2026}" in citation.entry()


def test_the_repository_wins_over_a_docs_url(cited):
    """One `url` in BibTeX, and for software it is where the source is."""
    cited(CFF + "url: https://dmarx.github.io/luria/\n")
    assert "url     = {https://github.com/dmarx/luria}" in citation.entry()


# --- absence, and refusing to guess --------------------------------------

def test_no_cff_renders_nothing(project):
    config.reset()
    assert citation.entry() == ""


def test_unreadable_yaml_renders_nothing_rather_than_half(cited):
    cited("title: [unclosed\n")
    assert citation.entry() == ""


def test_the_region_says_so_when_there_is_no_source(project):
    config.reset()
    assert "No readable `CITATION.cff`" in citation.region()


# --- the projection ------------------------------------------------------

def test_rewrite_fills_the_region(cited):
    root = cited(readme=f"# P\n\n{citation.OPEN}\n{citation.CLOSE}\n")
    out = citation.rewrite((root / "README.md").read_text())
    assert "@software{marx_luria," in out


def test_a_readme_without_a_region_is_left_alone(cited):
    """A project that has not opted in is not nagged — the same bargain the
    badge region makes."""
    root = cited(readme="# P\n\nNo region here.\n")
    text = (root / "README.md").read_text()
    assert citation.rewrite(text) == text


def test_a_stale_region_is_reported(cited):
    root = cited(readme=f"# P\n\n{citation.OPEN}\nstale\n{citation.CLOSE}\n")
    assert adr_index.staleness().readme == root / "README.md"


def test_a_fresh_region_is_not(cited):
    root = cited(readme=f"# P\n\n{citation.OPEN}\n{citation.CLOSE}\n")
    (root / "README.md").write_text(
        citation.rewrite((root / "README.md").read_text()))
    assert adr_index.staleness().readme is None
