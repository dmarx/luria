# tests/test_inherited_families.py
"""A family the config never declared is labelled, and never consumed (#136).

ADR-047 stands: a family left out of `luria.yaml` keeps the shipped default.
Two harms followed from that silently. `record.md`, whose promise is that it
cannot drift from the config, listed a `record/changelog.d` fragment
directory the author never wrote, in every example record. And `luria
collect`, which deletes what it reads, would consume a `record/changelog.d`
that happened to exist for some other reason. The default stays; the page
says where it came from, and the destructive step needs a declaration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import collect, config, record_doc

JOURNAL_ONLY = """\
journals:
  changelog:
    dir: changelog.d
    output: docs/changelog
"""

DECLARED = JOURNAL_ONLY + """\
fragments:
  record/changelog.d: CHANGELOG.md
"""


def record(tmp_path: Path, monkeypatch, text: str) -> Path:
    (tmp_path / "luria.yaml").write_text(text)
    (tmp_path / "CHANGELOG.md").write_text(
        f"# Changelog\n\n{collect.MARKER}\n")
    frag = tmp_path / "record/changelog.d"
    frag.mkdir(parents=True)
    (frag / "one.md").write_text("### Added\n\n- An entry.\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def test_the_config_knows_which_families_it_inherited(tmp_path, monkeypatch):
    record(tmp_path, monkeypatch, JOURNAL_ONLY)
    cfg = config.current()
    assert "fragments" in cfg.inherited and "schemes" in cfg.inherited
    assert "journals" not in cfg.inherited


def test_collect_refuses_a_directory_nobody_declared(tmp_path, monkeypatch):
    root = record(tmp_path, monkeypatch, JOURNAL_ONLY)
    with pytest.raises(SystemExit) as stop:
        collect.run()
    said = str(stop.value)
    assert "record/changelog.d" in said and "luria.yaml" in said
    assert "fragments:" in said, said
    assert (root / "record/changelog.d/one.md").exists()
    assert "An entry" not in (root / "CHANGELOG.md").read_text()


def test_collect_consumes_a_declared_directory(tmp_path, monkeypatch):
    root = record(tmp_path, monkeypatch, DECLARED)
    collect.run()
    assert "An entry" in (root / "CHANGELOG.md").read_text()
    assert not (root / "record/changelog.d/one.md").exists()


def test_an_empty_inherited_directory_is_still_quiet(tmp_path, monkeypatch,
                                                     capsys):
    """Nothing to consume, nothing at risk: no reason to fail a CI run."""
    root = record(tmp_path, monkeypatch, JOURNAL_ONLY)
    (root / "record/changelog.d/one.md").unlink()
    collect.run()
    assert "No fragments to collect" in capsys.readouterr().out


def _section(page: str, heading: str) -> str:
    return page.split(f"## {heading}")[1].split("\n## ")[0]


def test_the_record_page_labels_an_inherited_fragment_directory(
        tmp_path, monkeypatch):
    record(tmp_path, monkeypatch, JOURNAL_ONLY)
    section = _section(record_doc.render(), "Fragment directories")
    assert "record/changelog.d" in section
    assert "shipped default" in section and "luria.yaml" in section


def test_the_record_page_labels_inherited_schemes_and_journals(
        tmp_path, monkeypatch):
    record(tmp_path, monkeypatch, DECLARED.replace(JOURNAL_ONLY, ""))
    page = record_doc.render()
    assert "shipped default" in _section(page, "Referable documents")
    assert "shipped default" in _section(page, "Journals")


def test_a_declared_family_is_not_labelled(tmp_path, monkeypatch):
    record(tmp_path, monkeypatch, DECLARED)
    page = record_doc.render()
    assert "shipped default" not in _section(page, "Fragment directories")
    assert "shipped default" not in _section(page, "Journals")
