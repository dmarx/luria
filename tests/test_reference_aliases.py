# tests/test_reference_aliases.py
"""A reference field accepts a scheme's derived alias, wherever it is read.

A scheme with `alias: "AREA-{slug}"` answers to `AREA-runtime` as well as
`AREA-001` (#219), and prose citations already resolved it. A reference
field did not: `area: AREA-runtime` was "not a code". That made the readable
spelling unusable in exactly the place it reads best — a document's own
classification — and is what would have forced a promoted vocabulary's
values (`runtime`) to become opaque numbers. These tests hold every reader of
a reference value to one resolution: the lint, the index's grouping, the
typed edges, a relation's walk, and the fixer, which leaves it alone.
"""

from __future__ import annotations

from pathlib import Path

from luria import adr_index as builder, config, edges, lint, link_refs
from luria import relations

CONFIG = """
issue_url: https://example.test/issues/{n}
vocabularies:
  statuses:
    Active: {}
schemes:
  AREA:
    dir: record/areas.d
    output: docs/areas
    active: Active
    render: index
    alias: "AREA-{slug}"
    fields:
      status: {vocabulary: statuses}
      slug: {unique: true}
    references:
      broader: {scheme: AREA, many: true, required: false}
  RFC:
    dir: record/rfcs.d
    output: docs/rfcs
    active: Active
    render: index
    fields:
      status: {vocabulary: statuses}
    references:
      area: {scheme: AREA, many: true, required: false, group: true}
"""


def _doc(path: Path, code: str, title: str, front: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nstatus: Active\ntitle: '{title}'\nversion: 1\n"
                    f"{front}date: '2026-01-01'\n---\n\n# {code}: {title}\n")


def project(tmp_path, monkeypatch, rfc_area: str = "- AREA-runtime\n"
            ) -> Path:
    (tmp_path / "luria.yaml").write_text(CONFIG)
    areas, rfcs = tmp_path / "record/areas.d", tmp_path / "record/rfcs.d"
    _doc(areas / "AREA-001.md", "AREA-001", "Runtime", "slug: runtime\n")
    _doc(areas / "AREA-002.md", "AREA-002", "Queues",
         "slug: queues\nbroader:\n- AREA-runtime\n")
    _doc(rfcs / "RFC-001.md", "RFC-001", "Durable jobs",
         f"area:\n{rfc_area}")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def _contract_errors() -> list[str]:
    errors: list[str] = []
    lint.check_contracts(errors)
    return errors


def test_an_alias_is_a_valid_reference(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    assert _contract_errors() == []


def test_an_alias_nothing_answers_to_is_not(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, rfc_area="- AREA-nonesuch\n")
    assert any("AREA-nonesuch" in e for e in _contract_errors())


def test_grouping_files_an_alias_under_its_document(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    page = builder.outputs()[root / "docs/rfcs/area/AREA-001.md"]
    assert "RFC-001" in page


def test_a_typed_edge_lands_on_the_code(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    inbound = edges.graph().inbound("AREA-001")
    assert {e.source for e in inbound} >= {"RFC-001", "AREA-002"}


def test_a_relation_walks_through_an_alias(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    assert relations.edges("AREA", "broader")["AREA-002"] == {"AREA-001"}


def test_the_fixer_leaves_the_alias_spelling_alone(tmp_path, monkeypatch):
    """Recovering an identifier a reader can interpret is the point of a
    derived alias; canonicalizing it on write would undo that (#219)."""
    root = project(tmp_path, monkeypatch)
    rfc = root / "record/rfcs.d/RFC-001.md"
    before = rfc.read_text()
    link_refs.run(fix=True)
    assert rfc.read_text() == before


def test_relate_takes_aliases_and_writes_the_spelling_given(
        tmp_path, monkeypatch):
    """`luria relate AREA-queues broader AREA-runtime` reads as it means; the
    readable spelling is what lands in the file, and a second spelling of a
    target already held is the same relation, not a new one."""
    from luria import relate
    root = project(tmp_path, monkeypatch)
    done = relate.relate("RFC-001", "area", "AREA-queues")
    assert done.outcome == "added"
    assert "- AREA-queues" in (root / "record/rfcs.d/RFC-001.md").read_text()
    assert relate.relate("RFC-001", "area", "AREA-001").outcome == "present"
    assert relate.relate("AREA-queues", "broader", "AREA-runtime").outcome \
        == "present"


def test_the_converse_is_written_in_the_readable_spelling(
        tmp_path, monkeypatch):
    """The fixer writes the side that is missing. Where the far scheme
    derives an alias, that is the spelling a person would have written."""
    root = project(tmp_path, monkeypatch)
    text = (root / "luria.yaml").read_text().replace(
        "      broader: {scheme: AREA, many: true, required: false}\n",
        "      broader: {scheme: AREA, many: true, required: false, "
        "converse: narrower}\n"
        "      narrower: {scheme: AREA, many: true, required: false, "
        "converse: broader}\n")
    (root / "luria.yaml").write_text(text)
    config.reset()
    relations.complete(fix=True)
    one = (root / "record/areas.d/AREA-001.md").read_text()
    assert "narrower:\n- AREA-queues\n" in one
    config.reset()
    assert relations.completions() == []
