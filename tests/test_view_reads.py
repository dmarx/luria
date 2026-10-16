# tests/test_view_reads.py
"""What a view reads, and the findings that follow from it (ADR-tmpi08sj,
phase 3).

<!-- unresolved-ok-block: CLAIM-001 — fixture codes, not this record's -->
"""

from __future__ import annotations

import pytest

from _config import merged
from luria import config, doc_refs, lint, site_page, view_reads, views
from test_views import BASE, CLAIM_1, CLAIM_2, VIEW, write

RETIRING = """
schemes:
  CLAIM:
    retires_on: Superseded
"""

SUPERSEDED = CLAIM_2.replace("status: Proposed", "status: Superseded")


@pytest.fixture
def record(tmp_path, monkeypatch):
    write(tmp_path, "luria.yaml", merged(BASE, RETIRING, VIEW))
    write(tmp_path, "record/claims.d/CLAIM-001.md", CLAIM_1)
    write(tmp_path, "record/claims.d/CLAIM-002.md", SUPERSEDED)
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    yield tmp_path
    config.reset()


def template(root, text: str, rel: str = "record/views.d/BOOT.md.j2"):
    write(root, rel, text)


def reads(root) -> dict:
    view = config.current().views["boot"]
    return views.rendering(view).reads


# --- what is recorded ---------------------------------------------------

def test_a_read_names_its_template_line_and_kind(record):
    template(record, "Intro.\n{{ doc('CLAIM-001').title }}\n"
                     "{{ doc('CLAIM-002').body }}\n")
    found = reads(record)
    assert [(s.template, s.line, s.kind) for s in found["CLAIM-001"].sites] == [
        ("record/views.d/BOOT.md.j2", 2, "read")]
    assert [(s.template, s.line, s.kind) for s in found["CLAIM-002"].sites] == [
        ("record/views.d/BOOT.md.j2", 3, "transcluded")]


def test_part_and_summary_are_transclusions(record):
    template(record, "{{ doc('CLAIM-001').part('The inference') }}\n"
                     "{{ doc('CLAIM-002').summary }}\n")
    found = reads(record)
    assert {s.kind for s in found["CLAIM-001"].sites} == {"transcluded"}
    assert {s.kind for s in found["CLAIM-002"].sites} == {"transcluded"}


def test_printing_a_document_is_a_read(record):
    template(record, "See {{ doc('CLAIM-001') }}.\n")
    assert [s.kind for s in reads(record)["CLAIM-001"].sites] == ["read"]


def test_a_document_only_counted_is_not_read(record):
    template(record, "{{ docs('CLAIM') | length }}\n")
    assert reads(record) == {}


def test_a_read_in_an_included_file_is_sited_there(record):
    template(record, "{{ doc('CLAIM-002').body }}\n",
             rel="record/views.d/part.md.j2")
    template(record, "Top.\n{% include 'record/views.d/part.md.j2' %}")
    [site] = reads(record)["CLAIM-002"].sites
    assert (site.template, site.line) == ("record/views.d/part.md.j2", 1)


# --- the finding --------------------------------------------------------

def test_transcluding_a_retired_document_is_a_finding(record):
    template(record, "{{ doc('CLAIM-002').body }}\n")
    [row] = view_reads.retired_rows()
    assert "record/views.d/BOOT.md.j2:1" in row
    assert "CLAIM-002" in row and "Superseded" in row


def test_naming_a_retired_document_is_not(record):
    template(record, "{{ doc('CLAIM-002').title }} "
                     "({{ doc('CLAIM-002').status }})\n")
    assert view_reads.retired_rows() == []


def test_a_document_still_in_play_is_not_retired(record, monkeypatch):
    write(record, "record/claims.d/CLAIM-002.md", CLAIM_2)  # Proposed
    template(record, "{{ doc('CLAIM-002').body }}\n")
    assert view_reads.retired_rows() == []


@pytest.mark.parametrize("text", [
    "{# inactive-ok: CLAIM-002 — quoted as the view it replaced #}\n"
    "{{ doc('CLAIM-002').body }}\n",
    "{{ doc('CLAIM-002').body }} "
    "{# inactive-ok: CLAIM-002 — quoted as history #}\n",
])
def test_an_acknowledgement_at_the_site_excuses_it(record, text):
    template(record, text)
    assert view_reads.retired_rows() == []


def test_an_acknowledgement_for_another_code_does_not(record):
    template(record, "{# inactive-ok: CLAIM-001 — wrong one #}\n"
                     "{{ doc('CLAIM-002').body }}\n")
    assert len(view_reads.retired_rows()) == 1


def test_the_lint_reports_the_class(record):
    template(record, "{{ doc('CLAIM-002').body }}\n")
    assert "retired-transclusions" in lint.FAILABLE
    sections = {name: rows for name, _, rows in lint.status_sections()}
    assert len(sections["retired-transclusions"]) == 1


# --- the output is a view -----------------------------------------------

def test_a_view_output_is_generated(record):
    template(record, "Hello.\n")
    out = record / "BOOT.md"
    out.write_text("<!-- GENERATED -->\nCLAIM-002\n", encoding="utf-8")
    assert config.current().is_generated(out)
    assert out not in doc_refs.doc_files()


# --- each document names the views it renders into -----------------------

def test_rendered_into_inverts_the_reads(record):
    template(record, "{{ doc('CLAIM-001').title }}\n")
    assert view_reads.rendered_into() == {"CLAIM-001": ["BOOT.md"]}


def test_the_site_page_names_the_views(record):
    template(record, "{{ doc('CLAIM-001').title }}\n")
    path = record / "record/claims.d/CLAIM-001.md"
    props, _ = site_page.properties({"status": "Active"}, path, known={},
                                    rendered_into=["BOOT.md"])
    assert props["Rendered into"] == "BOOT.md"
