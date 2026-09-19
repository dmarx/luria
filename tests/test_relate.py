# tests/test_relate.py
"""`luria relate SOURCE FIELD TARGET` writes one relation into an existing
document's frontmatter (#304) — the hand-over for a relation drawn between
two filed documents on a canvas, the way `luria new --draft` is the
hand-over for a drafted entry."""

import json

import pytest
from _config import merged

from luria import relate as relate_mod
from luria.config import current


def _decisions(project, *statuses):
    from tests._scheme import decision
    return [decision(project, i, s) for i, s in enumerate(statuses, 1)]


def _declared_project(project):
    """SOTA extends SOTA (a declared converse pair) and is sourced to LIT (a
    scalar reference to another scheme)."""
    (project / "luria.yaml").write_text(merged("""
issue_url: https://example.test/issues/{n}
schemes:
  LIT:
    dir: record/literature.d
  SOTA:
    dir: record/practices.d
""", {"schemes": {"SOTA": {"references": {
        "source": {"scheme": "LIT", "many": False},
        "extends": {"scheme": "SOTA", "many": True, "converse": "extended_by"},
        "extended_by": {"scheme": "SOTA", "many": True, "converse": "extends"},
    }}}}))
    from luria import config
    config.reset()
    for code, title in (("SOTA-105", "Batch"), ("SOTA-113", "Continuous batching"),
                        ("LIT-224", "Orca")):
        prefix, num = code.split("-")
        d = current().schemes[prefix].dir
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{code}.md").write_text(
            f"---\nstatus: Active\ntitle: '{title}'\ntags:\n- record\n"
            f"date: '2026-01-01'\n---\n\n# {code}: {title}\n\nBody.\n")


def test_influenced_by_is_written_as_a_list_and_the_form_is_otherwise_untouched(project):
    a, b = _decisions(project, "Active", "Active")
    before = b.read_text()
    done = relate_mod.relate("ADR-002", "influenced_by", "ADR-001")
    assert done.outcome == "added" and done.path == b
    after = b.read_text()
    assert "influenced_by:\n- ADR-001\n" in after, after
    # One field appeared; every other line is as it was.
    assert after.replace("influenced_by:\n- ADR-001\n", "") == before


def test_a_second_run_reports_the_relation_instead_of_duplicating_it(project):
    _decisions(project, "Active", "Active")
    relate_mod.relate("ADR-002", "influenced_by", "ADR-001")
    done = relate_mod.relate("ADR-002", "influenced_by", "ADR-001")
    assert done.outcome == "present"
    assert current().schemes["ADR"].documents()[2].read_text().count("- ADR-001") == 1


def test_a_second_influence_joins_the_list(project):
    _decisions(project, "Active", "Active", "Active")
    relate_mod.relate("ADR-003", "influenced_by", "ADR-001")
    relate_mod.relate("ADR-003", "influenced_by", "ADR-002")
    text = current().schemes["ADR"].documents()[3].read_text()
    assert "influenced_by:\n- ADR-001\n- ADR-002\n" in text, text


def test_a_field_the_scheme_does_not_relate_through_is_refused_by_name(project):
    _decisions(project, "Active", "Active")
    with pytest.raises(SystemExit) as caught:
        relate_mod.relate("ADR-002", "cites", "ADR-001")
    assert "'cites'" in str(caught.value) and "influenced_by" in str(caught.value)


def test_a_target_that_resolves_to_nothing_is_refused_not_written(project):
    [a] = _decisions(project, "Active")
    before = a.read_text()
    with pytest.raises(SystemExit) as caught:
        relate_mod.relate("ADR-001", "influenced_by", "ADR-040")
    assert "ADR-040" in str(caught.value)
    assert a.read_text() == before


def test_an_unknown_source_is_refused(project):
    _decisions(project, "Active")
    with pytest.raises(SystemExit) as caught:
        relate_mod.relate("ADR-009", "influenced_by", "ADR-001")
    assert "ADR-009" in str(caught.value)


def test_a_document_cannot_relate_to_itself(project):
    _decisions(project, "Active")
    with pytest.raises(SystemExit):
        relate_mod.relate("ADR-001", "influenced_by", "ADR-001")


def test_the_successor_field_on_a_document_still_in_force_says_so(project):
    _decisions(project, "Active", "Active")
    done = relate_mod.relate("ADR-001", "superseded_by", "ADR-002")
    assert done.outcome == "added"
    assert any("Superseded" in n and "status" in n for n in done.notes), done.notes
    assert "superseded_by:\n- ADR-002\n" in current().schemes["ADR"].documents()[1].read_text()


def test_a_declared_relation_is_written_and_its_converse_is_left_to_repair(project):
    _declared_project(project)
    done = relate_mod.relate("SOTA-113", "extends", "SOTA-105")
    assert done.outcome == "added"
    assert "extends:\n- SOTA-105\n" in done.path.read_text()
    assert any("extended_by" in n and "repair" in n for n in done.notes), done.notes
    # The other side is not written here; `luria repair` owns that.
    other = current().schemes["SOTA"].documents()[105].read_text()
    assert "extended_by" not in other


def test_a_declared_scalar_reference_is_set_once(project):
    _declared_project(project)
    done = relate_mod.relate("SOTA-113", "source", "LIT-224")
    assert done.outcome == "added"
    assert "source: 'LIT-224'" in done.path.read_text()
    # Set to something else already: refused rather than silently replaced.
    (current().schemes["LIT"].dir / "LIT-112.md").write_text(
        "---\nstatus: Active\ntitle: 'vLLM'\ntags:\n- record\ndate: '2026-01-01'\n---\n\n# LIT-112: vLLM\n")
    with pytest.raises(SystemExit) as caught:
        relate_mod.relate("SOTA-113", "source", "LIT-112")
    assert "LIT-224" in str(caught.value)


def test_a_typed_field_refuses_a_document_of_another_scheme(project):
    _declared_project(project)
    with pytest.raises(SystemExit) as caught:
        relate_mod.relate("SOTA-113", "source", "SOTA-105")
    assert "LIT" in str(caught.value)


def test_a_drafts_file_relations_list_files_every_entry(project, capsys):
    _decisions(project, "Active", "Active", "Active")
    path = project / "drafts.json"
    path.write_text(json.dumps({
        "format": "luria-drafts", "version": 1, "drafts": [],
        "relations": [
            {"source": "ADR-003", "field": "influenced_by", "target": "ADR-001"},
            {"source": "ADR-003", "field": "influenced_by", "target": "ADR-002"},
        ],
    }))
    relate_mod.run(draft=str(path))
    out = capsys.readouterr().out
    assert out.count("+= ADR-00") == 2, out
    text = current().schemes["ADR"].documents()[3].read_text()
    assert "influenced_by:\n- ADR-001\n- ADR-002\n" in text


def test_run_prints_one_line_per_relation(project, capsys):
    _decisions(project, "Active", "Active")
    relate_mod.run("ADR-002", "influenced_by", "ADR-001")
    assert capsys.readouterr().out.strip() == "record/decisions.d/ADR-002.md: influenced_by += ADR-001"
