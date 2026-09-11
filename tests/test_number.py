"""Identity in the document rather than in the filename (#219).

Schemes now work the way journals always have: the frontmatter carries the
truth, the path is a projection of it, and the lint guards the agreement.

The fixtures use the reserved local fixture prefix `FXL` (ADR-093), so a
specimen filename here cannot read as a citation of this repository's own
decisions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import adr_index, config, lint, new, repair


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def project(tmp_path, monkeypatch, allocate: str = "filing") -> Path:
    write(tmp_path, "luria.toml", f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"

[luria.schemes.FXL]
dir = "record/fixtures.d"
output = "docs/fixtures"
allocate = "{allocate}"
""")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def doc(root: Path, name: str, *, number: int | None = None,
        title: str = "A decision") -> Path:
    front = ["---", "status: Active", f"title: '{title}'"]
    if number is not None:
        front.insert(1, f"number: {number}")
    front += ["date: '2026-01-01'", "---", "", f"# {name}: {title}", "", "Body."]
    return write(root, f"record/fixtures.d/{name}.md", "\n".join(front) + "\n")


def scheme():
    return config.current().schemes["FXL"]


# --- the field is the identity ----------------------------------------------

def test_the_field_wins_over_the_filename(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    path = doc(root, "FXL-007", number=42)
    assert scheme().number_of(path) == 42
    assert scheme().documents() == {42: path}
    assert adr_index.Adr(path, scheme()).code == "FXL-042"


def test_the_filename_answers_when_the_field_is_absent(tmp_path, monkeypatch):
    """A record written before `number:` existed still reads — which is what
    makes the field introducible without a migration anyone has to run."""
    root = project(tmp_path, monkeypatch)
    path = doc(root, "FXL-007")
    assert scheme().number_of(path) == 7
    assert scheme().documents() == {7: path}


def test_a_number_in_the_body_is_prose_not_a_claim(tmp_path, monkeypatch):
    """Not hypothetical: a line wrap in a real note put `number:` at column
    zero mid-sentence ("...here mainly for the 10%\nnumber: the record's
    optimizer practices..."). The frontmatter boundary is what keeps prose
    from claiming an identity."""
    root = project(tmp_path, monkeypatch)
    path = write(root, "record/fixtures.d/FXL-007.md",
                 "---\nstatus: Active\ntitle: 'A decision'\ndate: '2026-01-01'\n"
                 "---\n\n# FXL-007: A decision\n\nhere mainly for the 10%\n"
                 "number: the record's optimizer practices trade convergence\n")
    assert scheme().number_of(path) == 7


def test_a_temporary_document_has_no_number_yet(tmp_path, monkeypatch):
    """By design: a merge-allocated document holds no claim on the sequence
    until `luria concretize` assigns one (ADR-049)."""
    root = project(tmp_path, monkeypatch, allocate="merge")
    doc(root, "FXL-tmpabcde")
    assert scheme().documents() == {}
    assert scheme().temp_documents().keys() == {"tmpabcde"}


def test_the_cache_expires_when_the_file_changes(tmp_path, monkeypatch):
    """Keyed on the stat rather than reset by hand, so a writer that forgets
    to invalidate cannot serve a stale identity."""
    root = project(tmp_path, monkeypatch)
    path = doc(root, "FXL-007", number=42)
    assert scheme().number_of(path) == 42
    import os
    path.write_text(path.read_text().replace("number: 42", "number: 43"))
    os.utime(path, (0, 0))
    assert scheme().number_of(path) == 43


# --- the agreement check ----------------------------------------------------

def test_a_disagreement_is_a_finding(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "FXL-007", number=42)
    errors: list[str] = []
    lint.check_numbers(errors)
    assert len(errors) == 1
    assert "`number: 42` but the filename says 7" in errors[0]


def test_agreement_is_silent(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "FXL-007", number=7)
    errors: list[str] = []
    lint.check_numbers(errors)
    assert errors == []


def test_an_absent_field_is_not_a_disagreement(tmp_path, monkeypatch):
    """It is the repairable case, and reporting it here would name a finding
    whose remedy is a different command."""
    root = project(tmp_path, monkeypatch)
    doc(root, "FXL-007")
    errors: list[str] = []
    lint.check_numbers(errors)
    assert errors == []


# --- the migration ----------------------------------------------------------

def test_repair_populates_the_field_from_the_path(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    path = doc(root, "FXL-007")
    assert repair.populate_numbers(scheme()) == [path]
    assert "number: 7\n" in path.read_text()
    assert path.read_text().startswith("---\nnumber: 7\n")


def test_repair_is_idempotent(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "FXL-007")
    repair.populate_numbers(scheme())
    assert repair.populate_numbers(scheme()) == []


def test_repair_leaves_a_temporary_document_alone(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, allocate="merge")
    path = doc(root, "FXL-tmpabcde")
    before = path.read_text()
    assert repair.populate_numbers(scheme()) == []
    assert path.read_text() == before


def test_repair_never_invents_a_number(tmp_path, monkeypatch):
    """A file whose name carries no number has no witness to repair from."""
    root = project(tmp_path, monkeypatch)
    doc(root, "notes")
    assert repair.populate_numbers(scheme()) == []


# --- the writers ------------------------------------------------------------

def test_new_writes_the_field(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    path = new.new_entry("fxl", {"title": "First"}, None)
    assert path.read_text().startswith("---\nnumber: 1\n")
    assert scheme().number_of(path) == 1


def test_new_leaves_it_out_for_a_merge_allocated_scheme(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, allocate="merge")
    path = new.new_entry("fxl", {"title": "First"}, None)
    assert "number:" not in path.read_text()


def test_write_number_replaces_rather_than_duplicates(tmp_path, monkeypatch):
    text = "---\nnumber: 3\nstatus: Active\n---\n\n# FXL-003\n"
    out = new.write_number(text, 9)
    assert out.count("number:") == 1
    assert "number: 9" in out


def test_write_number_leaves_a_document_with_no_frontmatter_alone(tmp_path):
    assert new.write_number("# Heading\n", 4) == "# Heading\n"


def test_concretize_writes_the_field_when_it_assigns_the_number(
        tmp_path, monkeypatch):
    """The one moment a merge-allocated document acquires a number at all."""
    from luria import concretize
    root = project(tmp_path, monkeypatch, allocate="merge")
    doc(root, "FXL-001", number=1)
    doc(root, "FXL-tmpabcde", title="Landed from a branch")
    concretize.run()
    landed = root / "record/fixtures.d/FXL-002.md"
    assert landed.exists()
    assert "number: 2\n" in landed.read_text()
    assert scheme().number_of(landed) == 2


def test_unterminated_frontmatter_declares_nothing(tmp_path, monkeypatch):
    """`parse_frontmatter` treats an unclosed block as no frontmatter; reading
    identity has to agree, or the two disagree about what a document says."""
    root = project(tmp_path, monkeypatch)
    path = write(root, "record/fixtures.d/FXL-007.md",
                 "---\nstatus: Active\nnumber: 42\n\n# FXL-007\n")
    assert config._declared_number(path) is None
    assert scheme().number_of(path) == 7


def test_an_indented_number_is_inside_another_field(tmp_path, monkeypatch):
    """A block scalar's continuation lines are indented, so the column-zero
    anchor is what keeps prose out of the identity."""
    root = project(tmp_path, monkeypatch)
    path = write(root, "record/fixtures.d/FXL-007.md",
                 "---\nstatus: Active\nsummary: >-\n  we rejected\n"
                 "  number: 42\ndate: '2026-01-01'\n---\n\n# FXL-007\n")
    assert config._declared_number(path) is None
    assert scheme().number_of(path) == 7
