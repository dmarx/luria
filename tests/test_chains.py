"""Sequences, walked transitively and rendered once (#171).

`edges.py` already reads a reference field as a typed relation and the site
already shows each page's neighbours. What no view answered is "what is the
sequence this document is a step in", which is the thing worth reading — and
the thing the consumer project's documents were each re-describing in their
own words, once per participant, until two of them went stale on the same
fact and were corrected in two places by luck.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import chains, config


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


CHAIN = """
[luria.chains.lineage]
scheme   = "LIT"
relation = "extends"
sibling  = "compared_against"
output   = "docs/lineage.md"
title    = "Lines of work"
"""

RELATIONS = """
[luria.schemes.LIT.references]
extends = { scheme = "LIT", required = false, many = true, converse = "extended_by" }
extended_by = { scheme = "LIT", required = false, many = true, converse = "extends" }
compared_against = { scheme = "LIT", required = false, many = true, converse = "compared_against" }
"""


def project(tmp_path, monkeypatch, extra: str = RELATIONS + CHAIN) -> Path:
    write(tmp_path, "luria.toml", f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"

[luria.schemes.LIT]
dir = "record/literature.d"
output = "docs/literature"
{extra}
""")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def note(root: Path, number: int, title: str, *, status: str = "Active",
         extends=(), compared_against=()) -> Path:
    front = ["---", f"status: {status}", f"title: {title!r}", "tags:",
             "- record", "date: '2026-01-01'"]
    for name, codes in (("extends", extends),
                        ("compared_against", compared_against)):
        if codes:
            front.append(f"{name}:")
            front += [f"- {c}" for c in codes]
    front += ["---", "", f"# LIT-{number:03d}: {title}", "", "Body."]
    return write(root, f"record/literature.d/LIT-{number:03d}.md",
                 "\n".join(front) + "\n")


# --- the walk ---------------------------------------------------------------

def test_a_line_is_ordered_oldest_first(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    note(root, 3, "The replacement's replacement", extends=["LIT-002"])
    lines = chains.walk()
    assert len(lines) == 1
    assert [d.code for d in lines[0].spine] == ["LIT-001", "LIT-002", "LIT-003"]


def test_a_document_in_no_relation_is_in_no_chain(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "Alone")
    assert chains.walk() == []


def test_two_lines_are_two_chains(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "One root")
    note(root, 2, "Its successor", extends=["LIT-001"])
    note(root, 3, "Another root")
    note(root, 4, "Its successor", extends=["LIT-003"])
    assert len(chains.walk()) == 2


def test_a_branch_keeps_both_successors(tmp_path, monkeypatch):
    """A line is a DAG, not a list: two papers can replace the same one."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "One replacement", extends=["LIT-001"])
    note(root, 3, "Another replacement", extends=["LIT-001"])
    line, = chains.walk()
    assert {d.code for d in line.spine} == {"LIT-001", "LIT-002", "LIT-003"}
    assert line.depth["LIT-002"] == line.depth["LIT-003"] == 1


def test_a_sibling_joins_the_chain_without_joining_the_spine(
        tmp_path, monkeypatch):
    """A rival that extends nothing is still part of the story."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    note(root, 3, "The rival", compared_against=["LIT-002"])
    line, = chains.walk()
    assert [d.code for d in line.spine] == ["LIT-001", "LIT-002"]
    assert [d.code for d in line.alongside] == ["LIT-003"]


def test_a_chain_of_siblings_alone_still_renders(tmp_path, monkeypatch):
    """Two papers that only compare themselves to each other are a
    comparison, which is the fact the field exists to record."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "One design", compared_against=["LIT-002"])
    note(root, 2, "The other", compared_against=["LIT-001"])
    line, = chains.walk()
    assert not line.spine
    assert {d.code for d in line.alongside} == {"LIT-001", "LIT-002"}


# --- the findings -----------------------------------------------------------

def test_a_cycle_is_a_finding(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "A", extends=["LIT-002"])
    note(root, 2, "B", extends=["LIT-001"])
    rows = chains.rows()
    assert len(rows) == 1 and "cycle" in rows[0]
    assert "LIT-001" in rows[0] and "LIT-002" in rows[0]


def test_a_cycle_does_not_crash_the_walk(tmp_path, monkeypatch):
    """A finding is not an excuse to render nothing (DP-15)."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "A", extends=["LIT-002"])
    note(root, 2, "B", extends=["LIT-001"])
    line, = chains.walk()
    assert {d.code for d in line.spine} == {"LIT-001", "LIT-002"}


def test_a_one_sided_relation_is_not_this_check_s_business(
        tmp_path, monkeypatch):
    """It moved to `relations.py` (#178). A declared pair is one-sided or it
    is not, whether or not a chain walks it — so the finding belongs to the
    relation, and `broken-chains` keeps only what is about the sequence."""
    from luria import relations
    root = project(tmp_path, monkeypatch)
    note(root, 1, "One design")
    note(root, 2, "The other", compared_against=["LIT-001"])
    assert chains.rows() == []
    assert len(relations.rows()) == 1


def test_a_two_sided_comparison_is_clean(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "One design", compared_against=["LIT-002"])
    note(root, 2, "The other", compared_against=["LIT-001"])
    assert chains.rows() == []


def test_succession_is_not_expected_to_be_symmetric(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    assert chains.rows() == []


def test_no_sibling_relation_declared_means_no_symmetry_finding(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, RELATIONS + """
[luria.chains.lineage]
scheme   = "LIT"
relation = "extends"
output   = "docs/lineage.md"
""")
    note(root, 1, "One design")
    note(root, 2, "The other", compared_against=["LIT-001"])
    assert chains.rows() == []


# --- the view ---------------------------------------------------------------

def test_the_page_is_generated_and_stamped(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    page = chains.outputs()[root / "docs/lineage.md"]
    assert page.startswith("<!-- GENERATED")
    assert "Lines of work" in page
    assert "The original" in page and "The replacement" in page


def test_the_page_shows_status_so_a_retired_step_reads_as_one(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original", status="Superseded")
    note(root, 2, "The replacement", extends=["LIT-001"])
    page = chains.outputs()[root / "docs/lineage.md"]
    assert "Superseded" in page


def test_every_rendered_target_resolves(tmp_path, monkeypatch):
    """The first version linked into the scheme's *view* directory, which for
    an index-rendered scheme holds a README and tag pages and never a page
    per document — so every link on the page resolved to nothing, and no
    fixture noticed until a real corpus did."""
    import re
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    page = chains.outputs()[root / "docs/lineage.md"]
    targets = re.findall(r"\]\(([^)]+)\)", page)
    assert targets
    for target in targets:
        assert (root / "docs" / target).resolve().exists(), target


def test_a_project_declaring_no_chains_renders_nothing(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, RELATIONS)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    assert chains.outputs() == {}
    assert chains.rows() == []


def test_an_undeclared_relation_is_a_config_error(tmp_path, monkeypatch):
    """A chain over a field the scheme does not declare a reference would
    render nothing, and nothing is indistinguishable from current (DP-15)."""
    with pytest.raises(ValueError, match="extends"):
        project(tmp_path, monkeypatch, """
[luria.chains.lineage]
scheme   = "LIT"
relation = "extends"
output   = "docs/lineage.md"
""")
        config.current()


def test_a_chain_over_an_undeclared_scheme_is_a_config_error(
        tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="NOPE"):
        project(tmp_path, monkeypatch, RELATIONS + """
[luria.chains.lineage]
scheme   = "NOPE"
relation = "extends"
output   = "docs/lineage.md"
""")
        config.current()


def test_the_class_is_promotable_and_wired(tmp_path, monkeypatch):
    from luria import lint
    assert "broken-chains" in lint.FAILABLE
    root = project(tmp_path, monkeypatch)
    note(root, 1, "A", extends=["LIT-002"])
    note(root, 2, "B", extends=["LIT-001"])
    assert "broken-chains" in {n for n, _, _ in lint.status_sections()}


def test_the_page_is_part_of_the_generated_views(tmp_path, monkeypatch):
    """`luria index --check` has to compare it, or a stale chain page ships
    looking current."""
    from luria import adr_index
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    assert root / "docs/lineage.md" in adr_index.outputs()


def test_only_the_status_value_is_rendered(tmp_path, monkeypatch):
    """`status`, `superseded_by` and `status_note` are three fields, and the
    composed display form is one reading of them. This page wants the value:
    the successor is the next line, and the note is the argument this view
    leaves on the document. Rendering the composed form also dragged a link
    authored in the source's frame onto a page that renders elsewhere."""
    import re
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    write(root, "record/literature.d/LIT-002.md",
          "---\nstatus: 'Superseded'\nsuperseded_by:\n- LIT-001\n"
          "status_note: 'The original was replaced; [LIT-001](LIT-001.md) says why'\n"
          "title: 'The replacement'\ntags:\n- record\ndate: '2026-01-01'\n"
          "extends:\n- LIT-001\n---\n\n# LIT-002: The replacement\n\nBody.\n")
    page = chains.outputs()[root / "docs/lineage.md"]
    assert "*(Superseded)*" in page
    assert "The original was replaced" not in page, "the note is not this view's"
    for target in re.findall(r"\]\(([^)]+)\)", page):
        assert (root / "docs" / target).resolve().exists(), target


def test_the_page_is_not_a_citing_site(tmp_path, monkeypatch):
    """A chain's job is to show the line *including* its retired steps, so
    scanning it would report every superseded document in every chain — at a
    site the reader must not edit, in a file the next build overwrites."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    assert config.current().is_generated(root / "docs/lineage.md")


def test_a_relation_naming_a_retired_step_is_not_a_citation(
        tmp_path, monkeypatch):
    """A successor's predecessor is superseded by construction. Reading
    `extends:` as a citation hands back one finding per retired step in every
    chain, at the field whose whole job is to name it."""
    from luria import ref_status
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original", status="Superseded")
    note(root, 2, "The replacement", extends=["LIT-001"])
    result = ref_status.scan()
    sites = [c.path.name for c in result.cited.get("LIT-001", [])]
    assert "LIT-002.md" not in sites, sites


def test_prose_naming_a_retired_step_is_still_a_citation(
        tmp_path, monkeypatch):
    """Only the field is exempt. A paragraph pointing at a retired document
    is the finding this record adopted the check to get."""
    from luria import ref_status
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original", status="Superseded")
    path = note(root, 2, "The replacement", extends=["LIT-001"])
    path.write_text(path.read_text() + "\nThis replaces LIT-001.\n")
    result = ref_status.scan()
    sites = [c.path.name for c in result.cited.get("LIT-001", [])]
    assert "LIT-002.md" in sites, sites
