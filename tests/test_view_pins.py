# tests/test_view_pins.py
"""A pinned view: an output that stops moving once it is published
(ADR-130, phase 4).

<!-- unresolved-ok-block: CLAIM-001 — fixture codes, not this record's -->
"""

from __future__ import annotations

import json

import pytest

from _config import merged
from luria import adr_index, config, lint, view_pins
from test_views import BASE, CLAIM_1, CLAIM_2, write

PINNED = """
views:
  paper:
    template: record/views.d/paper.md.j2
    output: docs/paper.md
    pin: true
"""

TEMPLATE = "{{ doc('CLAIM-001').part('The inference') }}\n"


@pytest.fixture
def record(tmp_path, monkeypatch):
    write(tmp_path, "luria.yaml", merged(BASE, PINNED))
    write(tmp_path, "record/claims.d/CLAIM-001.md", CLAIM_1)
    write(tmp_path, "record/claims.d/CLAIM-002.md", CLAIM_2)
    write(tmp_path, "record/views.d/paper.md.j2", TEMPLATE)
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    adr_index.forget_documents()
    yield tmp_path
    config.reset()


def output(root) -> str:
    return (root / "docs/paper.md").read_text(encoding="utf-8")


def edit(root, rel: str, old: str, new: str) -> None:
    path = root / rel
    path.write_text(path.read_text(encoding="utf-8").replace(old, new),
                    encoding="utf-8")
    adr_index.forget_documents()


def test_a_view_can_register_a_pin(record):
    assert config.current().views["paper"].pin is True


def test_pinning_writes_the_output_and_the_lock(record):
    view_pins.endorse("paper")
    assert "From the case to the rule." in output(record)
    lock = json.loads((record / "views.lock.json").read_text())
    entry = lock["paper"]
    assert set(entry["reads"]) == {"CLAIM-001"}
    assert entry["output"]


def test_a_pinned_view_is_not_rewritten_when_the_record_moves(record):
    view_pins.endorse("paper")
    edit(record, "record/claims.d/CLAIM-001.md",
         "From the case to the rule.", "From the rule to the case.")
    adr_index.run()
    assert "From the case to the rule." in output(record)
    assert record / "docs/paper.md" not in adr_index.staleness().stale


def test_drift_names_the_document_that_moved(record):
    view_pins.endorse("paper")
    edit(record, "record/claims.d/CLAIM-001.md",
         "From the case to the rule.", "From the rule to the case.")
    [row] = view_pins.drift_rows()
    assert "views.paper" in row and "CLAIM-001" in row
    assert "luria views --pin paper" in row


def test_a_change_the_view_never_read_is_not_drift(record):
    view_pins.endorse("paper")
    edit(record, "record/claims.d/CLAIM-001.md",
         "Not for the reader.", "Still not for the reader.")
    edit(record, "record/claims.d/CLAIM-002.md", "Body two.", "Body 2.")
    assert view_pins.drift_rows() == []


def test_a_template_change_is_drift_with_no_document_to_name(record):
    view_pins.endorse("paper")
    write(record, "record/views.d/paper.md.j2", "Preface.\n" + TEMPLATE)
    [row] = view_pins.drift_rows()
    assert "template" in row


def test_a_hand_edit_of_the_output_is_reported(record):
    view_pins.endorse("paper")
    (record / "docs/paper.md").write_text("Edited.\n", encoding="utf-8")
    [row] = view_pins.drift_rows()
    assert "docs/paper.md" in row and "pinned" in row


def test_a_registered_pin_nobody_endorsed_is_reported(record):
    [row] = view_pins.drift_rows()
    assert "luria views --pin paper" in row
    # …and the view renders as any other until it is endorsed.
    assert record / "docs/paper.md" in adr_index.outputs()


def test_re_pinning_endorses_the_new_state(record):
    view_pins.endorse("paper")
    edit(record, "record/claims.d/CLAIM-001.md",
         "From the case to the rule.", "From the rule to the case.")
    view_pins.endorse("paper")
    assert view_pins.drift_rows() == []
    assert "From the rule to the case." in output(record)


def test_pinning_an_unknown_view_says_so(record):
    with pytest.raises(SystemExit):
        view_pins.endorse("nonesuch")


def test_the_lint_reports_the_class(record):
    assert "view-drift" in lint.FAILABLE
    sections = {name: rows for name, _, rows in lint.status_sections()}
    assert len(sections["view-drift"]) == 1
