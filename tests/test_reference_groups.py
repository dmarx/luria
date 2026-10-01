# tests/test_reference_groups.py
"""A reference field can head an index, or be grouped, like a vocabulary.

A vocabulary is a shorthand for a tiny constrained scheme: its values are
entries with a name, a label and a blurb, and nothing else. Once a record
needs more than that — a term with standing, history, relations of its own,
or a place in a hierarchy — the vocabulary is promoted to a scheme and the
field that drew from it becomes a reference. These tests are for the half of
that which keeps the views: a reference to a scheme groups its documents
exactly as a vocabulary field did, one page per target, titled and described
by the target document itself.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import adr_index as builder, config, lint

CONFIG = """
issue_url: https://example.test/issues/{n}
vocabularies:
  statuses:
    Active: {}
    Superseded: {}
schemes:
  AREA:
    dir: record/areas.d
    output: docs/areas
    active: Active
    render: index
    fields:
      status: {vocabulary: statuses}
  RFC:
    dir: record/rfcs.d
    output: docs/rfcs
    active: Active
    render: index
%s
    fields:
      status: {vocabulary: statuses}
    references:
      area:
        scheme: AREA
        many: true
        required: false
%s
"""


def _doc(path: Path, code: str, title: str, front: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nstatus: Active\ntitle: '{title}'\nversion: 1\n"
                    f"{front}date: '2026-01-01'\n---\n\n# {code}: {title}\n")


def project(tmp_path, monkeypatch, *, axis: bool = False,
            group: bool = False) -> Path:
    (tmp_path / "luria.yaml").write_text(CONFIG % (
        "    axis: area" if axis else "",
        "        group: true" if group else ""))
    areas, rfcs = tmp_path / "record/areas.d", tmp_path / "record/rfcs.d"
    _doc(areas / "AREA-001.md", "AREA-001", "Runtime",
         "summary: 'the execution engine'\n")
    _doc(areas / "AREA-002.md", "AREA-002", "Storage")
    _doc(areas / "AREA-003.md", "AREA-003", "Nobody uses this")
    _doc(rfcs / "RFC-001.md", "RFC-001", "Durable jobs",
         "area:\n- AREA-001\n- AREA-002\n")
    _doc(rfcs / "RFC-002.md", "RFC-002", "Faster boot", "area: AREA-001\n")
    _doc(rfcs / "RFC-003.md", "RFC-003", "Unfiled")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def test_an_axis_may_name_a_reference_field(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, axis=True)
    scheme = config.current().schemes["RFC"]
    assert scheme.axis == "area"
    assert scheme.grouped_fields[0] == "area"


def test_a_reference_is_not_grouped_unless_it_says_so(tmp_path, monkeypatch):
    """Most relations are not taxonomies — `extends`, `superseded_by` — and
    a page per target for every one of them would be noise."""
    root = project(tmp_path, monkeypatch)
    assert "area" not in config.current().schemes["RFC"].grouped_fields
    assert not any(p.parent == root / "docs/rfcs/area"
                   for p in builder.outputs())


def test_a_grouped_reference_gets_a_page_per_target(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, group=True)
    out = builder.outputs()
    page = out[root / "docs/rfcs/area/AREA-001.md"]
    # Titled and described by the target document, the way a vocabulary
    # value is by its label and blurb — and linked to it, since the target
    # is a document a reader can open.
    assert "Runtime" in page
    assert "the execution engine" in page
    assert "../../../record/areas.d/AREA-001.md" in page
    assert "RFC-001" in page and "RFC-002" in page
    assert "RFC-003" not in page
    assert "RFC-001" in out[root / "docs/rfcs/area/AREA-002.md"]


def test_a_target_nobody_references_still_has_a_page(tmp_path, monkeypatch):
    """As a declared vocabulary value nobody uses does: the target exists,
    and `(0)` is the useful thing to know about it."""
    root = project(tmp_path, monkeypatch, group=True)
    out = builder.outputs()
    assert root / "docs/rfcs/area/AREA-003.md" in out
    assert "Nobody uses this" in out[root / "docs/rfcs/README.md"]


def test_the_axis_lists_documents_under_each_target(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, axis=True)
    index = builder.outputs()[root / "docs/rfcs/README.md"]
    assert "**[Runtime](area/AREA-001.md)** (2) — the execution engine" \
        in index


def test_a_code_that_resolves_to_nothing_gets_no_page(tmp_path, monkeypatch):
    """The lint already reports it; a page would publish the mistake, which
    is what a closed vocabulary's unknown value gets too."""
    root = project(tmp_path, monkeypatch, group=True)
    _doc(root / "record/rfcs.d/RFC-004.md", "RFC-004", "Typo",
         "area: AREA-099\n")
    config.reset()
    assert root / "docs/rfcs/area/AREA-099.md" not in builder.outputs()


def test_grouped_reference_pages_are_owned_views(tmp_path, monkeypatch):
    """Same ownership as a vocabulary's pages: the generator owns the
    directory, so a stale page in it is an orphan and the docs index does
    not ask for it to be listed."""
    root = project(tmp_path, monkeypatch, group=True)
    assert root / "docs/rfcs/area" in builder.view_dirs()
    builder.run()
    errors: list[str] = []
    lint.check_docs_index(errors)
    assert not [e for e in errors if "area" in e], errors


def test_group_is_refused_on_a_reference_to_a_remote(tmp_path, monkeypatch):
    """A page per target needs the targets: a scheme this record holds."""
    (tmp_path / "luria.yaml").write_text((CONFIG % (
        "", "        group: true")).replace("scheme: AREA", "scheme: NOPE"))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    with pytest.raises((ValueError, SystemExit)):
        config.current()
