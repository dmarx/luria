# tests/test_unique_fields.py
"""A field the project declares unique, checked across the scheme (#165).

Two documents can name one source and every existing check passes: each
pointer resolves, each identifier is well formed, and nothing asks the
converse question — whether two documents resolve to the same place.

The fixtures use the reserved local fixture prefix `FXL` (ADR-093), so a
specimen code here cannot read as a citation of any real document.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from _config import merged

from luria import config, lint


def project(tmp_path, monkeypatch, fields: dict | None = None,
            field_groups: dict | None = None) -> Path:
    fxl: dict = {"dir": "record/fixtures.d", "output": "docs/fixtures"}
    if fields:
        fxl["fields"] = fields
    if field_groups:
        fxl["field_groups"] = field_groups
    (tmp_path / "luria.yaml").write_text(merged(
        {"issue_url": "https://example.test/issues/{n}",
         "schemes": {"FXL": fxl}}))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def note(root: Path, number: int, superseded_by=(), status="Active",
         **frontmatter) -> Path:
    path = root / "record/fixtures.d" / f"FXL-{number:03d}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    front = [f"status: {status}", f"title: 'A note {number}'",
             "tags:", "- record", "date: '2026-01-01'"]
    if superseded_by:
        front.append("superseded_by:")
        front += [f"- {c}" for c in superseded_by]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            front.append(f"{key}:")
            front += [f"- {v!r}" for v in value]
        else:
            front.append(f"{key}: {value!r}")
    path.write_text("---\n" + "\n".join(front) + "\n---\n\n"
                    f"# FXL-{number:03d}: A note {number}\n\nBody.\n")
    return path


UNIQUE_ARXIV = {"arxiv": {"unique": True}}


# --- the finding -------------------------------------------------------------

def test_two_documents_on_one_value_is_a_violation(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, fields=UNIQUE_ARXIV)
    note(root, 41, arxiv="2302.06675")
    note(root, 42, arxiv="2302.06675")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert len(errors) == 1, errors
    assert "FXL-041, FXL-042" in errors[0]
    assert "2302.06675" in errors[0]
    assert "arxiv" in errors[0]


def test_distinct_values_pass(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, fields=UNIQUE_ARXIV)
    note(root, 41, arxiv="2302.06675")
    note(root, 42, arxiv="1608.03983")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert errors == []


def test_nothing_is_checked_unless_the_project_declares_it(tmp_path, monkeypatch):
    """Opt-in, like `invariant`. A record that has not said its identifiers
    are unique has not said they are."""
    root = project(tmp_path, monkeypatch,
                   fields={"arxiv": {"many": False, "required": False,
                                     "required_when": {"status": ["Active"]}}})
    note(root, 41, arxiv="2302.06675")
    note(root, 42, arxiv="2302.06675")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert errors == []


def test_a_missing_value_is_not_a_collision(tmp_path, monkeypatch):
    """Absence is not a shared value — otherwise every document lacking an
    optional field would collide with every other."""
    root = project(tmp_path, monkeypatch, fields=UNIQUE_ARXIV)
    note(root, 41)
    note(root, 42)
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert errors == []


def test_three_documents_report_once_naming_all_three(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, fields=UNIQUE_ARXIV)
    for n in (41, 42, 43):
        note(root, n, arxiv="2302.06675")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert len(errors) == 1, errors
    assert "FXL-041, FXL-042, FXL-043" in errors[0]


# --- the retirement is the resolution ----------------------------------------

def test_a_duplicate_retired_into_its_survivor_is_not_a_collision(tmp_path, monkeypatch):
    """The shape the anthology already holds three times: the losing note is
    retired naming the winner, and the pair is the record's answer rather
    than its defect (DP-3 keeps the body)."""
    root = project(tmp_path, monkeypatch, fields=UNIQUE_ARXIV)
    note(root, 41, arxiv="2302.06675", status="Rejected",
         superseded_by=["FXL-042"])
    note(root, 42, arxiv="2302.06675")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert errors == []


def test_both_retired_still_resolves_when_one_names_the_other(tmp_path, monkeypatch):
    """LIT-090/LIT-105: the survivor is itself Rejected, for its own
    unrelated reason. What resolves the pair is the pointer, not a status."""
    root = project(tmp_path, monkeypatch, fields=UNIQUE_ARXIV)
    note(root, 41, arxiv="2302.06675", status="Rejected",
         superseded_by=["FXL-042"])
    note(root, 42, arxiv="2302.06675", status="Rejected")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert errors == []


def test_retired_pointing_somewhere_else_is_still_a_collision(tmp_path, monkeypatch):
    """The negative that gives the rule its shape. Being retired does not
    excuse a collision; naming *the document you collide with* does."""
    root = project(tmp_path, monkeypatch, fields=UNIQUE_ARXIV)
    note(root, 41, arxiv="2302.06675", status="Rejected",
         superseded_by=["FXL-099"])
    note(root, 42, arxiv="2302.06675")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert len(errors) == 1, errors
    assert "FXL-041, FXL-042" in errors[0]


def test_one_of_three_yielding_leaves_the_other_two(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, fields=UNIQUE_ARXIV)
    note(root, 41, arxiv="2302.06675", status="Rejected",
         superseded_by=["FXL-042"])
    note(root, 42, arxiv="2302.06675")
    note(root, 43, arxiv="2302.06675")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert len(errors) == 1, errors
    assert "FXL-042, FXL-043" in errors[0]
    assert "FXL-041" not in errors[0]


# --- what counts as the same value -------------------------------------------

def test_case_and_surrounding_space_do_not_make_two_identifiers(tmp_path, monkeypatch):
    """A DOI is case-insensitive by specification, and a trailing space is
    nobody's intent."""
    root = project(tmp_path, monkeypatch, fields={"doi": {"unique": True}})
    note(root, 41, doi="10.1234/ABC")
    note(root, 42, doi=" 10.1234/abc ")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert len(errors) == 1, errors


def test_the_report_quotes_every_spelling_that_matched(tmp_path, monkeypatch):
    """A reader seeing one quoted value and two documents would go looking
    for a difference the comparison had already folded away."""
    root = project(tmp_path, monkeypatch, fields={"doi": {"unique": True}})
    note(root, 41, doi="10.1234/ABC")
    note(root, 42, doi="10.1234/abc")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert "`10.1234/ABC` / `10.1234/abc`" in errors[0]


def test_the_report_quotes_the_value_as_written(tmp_path, monkeypatch):
    """Never the folded form: a spelling nobody wrote is one nobody can
    grep for."""
    root = project(tmp_path, monkeypatch, fields={"doi": {"unique": True}})
    note(root, 41, doi="10.1234/ABC")
    note(root, 42, doi="10.1234/ABC")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert "`10.1234/ABC`" in errors[0]
    assert "10.1234/abc" not in errors[0]


def test_a_list_valued_field_is_unique_element_by_element(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   fields={"implements": {"many": True, "unique": True}})
    note(root, 41, implements=["Lion", "Adam"])
    note(root, 42, implements=["Adam"])
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert len(errors) == 1, errors
    assert "Adam" in errors[0]
    assert "Lion" not in errors[0]


# --- a group declares it once ------------------------------------------------

def test_a_field_group_declares_uniqueness_for_every_field_in_it(tmp_path, monkeypatch):
    """`source` on LIT is `arxiv`/`doi`/`url`, and saying `unique` once on
    the group is saying it of each."""
    root = project(tmp_path, monkeypatch,
                   field_groups={"source": {"fields": ["arxiv", "doi", "url"],
                                            "unique": True}})
    note(root, 41, doi="10.1234/abc")
    note(root, 42, doi="10.1234/abc")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert len(errors) == 1, errors
    assert "source" in errors[0]


def test_a_group_does_not_join_values_across_its_fields(tmp_path, monkeypatch):
    """An arXiv identifier and a DOI are different namespaces, and a string
    equal in both is a coincidence rather than a duplicate. Recognising one
    paper under two KINDS of identifier is normalisation, which this is
    deliberately not (#165)."""
    root = project(tmp_path, monkeypatch,
                   field_groups={"source": {"fields": ["arxiv", "doi"],
                                            "unique": True}})
    note(root, 41, arxiv="2302.06675")
    note(root, 42, doi="2302.06675")
    errors: list[str] = []
    lint.check_unique_fields(errors)
    assert errors == []


# --- refused at load ---------------------------------------------------------

def test_unique_alone_types_a_field(tmp_path, monkeypatch):
    """`fields.<f>: {unique: true}` constrains something, so the
    "declares no type" refusal must not fire on it."""
    project(tmp_path, monkeypatch, fields=UNIQUE_ARXIV)
    assert config.current().schemes["FXL"].plain_fields[0].unique is True


def test_unique_on_a_vocabulary_field_is_refused(tmp_path, monkeypatch):
    """A closed vocabulary exists to be shared. Declaring its values unique
    caps the scheme at one document per term, which nobody means."""
    (tmp_path / "luria.yaml").write_text(merged(
        {"issue_url": "https://example.test/issues/{n}",
         "vocabularies": {"colours": {"red": {}, "blue": {}}},
         "schemes": {"FXL": {"dir": "record/fixtures.d",
                             "output": "docs/fixtures",
                             "fields": {"colour": {"vocabulary": "colours",
                                                   "unique": True}}}}}))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    with pytest.raises(ValueError, match="unique"):
        config.current()
