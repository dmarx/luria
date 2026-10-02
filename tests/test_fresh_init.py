# tests/test_fresh_init.py
"""A fresh record is quiet: `init`, `index`, `lint` prints nothing to act on.

`test_a_fresh_default_init_lints_clean` holds the loop to *violations*; this
holds it to every finding, because a record that starts with warnings
teaches its owner to skim past them on day one (#331). Three had been
printing on every new record:

- `CLAUDE.md` linked `docs/design-principles.md` whether or not the config
  declared a principles scheme, so a record without one carried a link to a
  page it would never generate;
- `spent-upgrades` told every record born on the current format that it no
  longer needed upgrades it never needed — a finding whose only remedy
  ("remove it at 1.0.0") belongs to luria's maintainers;
- `luria collect` crashed on the changelog fragment directory `init` had
  just scaffolded, because nothing wrote the file it collects into.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import adr_index, collect, config, init, lint, new


def _repoint(root: Path, monkeypatch) -> None:
    monkeypatch.setenv("LURIA_ROOT", str(root))
    config.reset()


def _findings(capsys) -> str:
    """Everything `luria lint` printed except its all-clear line."""
    capsys.readouterr()
    lint.run()
    out = capsys.readouterr()
    said = (out.out + out.err).splitlines()
    return "\n".join(line for line in said if "lint clean" not in line)


CUSTOM = """\
vocabularies:
  rfc-status:
    Proposed: {}
    Accepted: {}
schemes:
  RFC:
    dir: record/rfcs.d
    output: docs/rfcs
    active: Accepted
    fields:
      status:
        vocabulary: rfc-status
"""


def test_a_fresh_default_record_prints_no_findings(tmp_path, monkeypatch,
                                                   capsys):
    init.run(into=str(tmp_path))
    _repoint(tmp_path, monkeypatch)
    adr_index.run()
    assert _findings(capsys) == ""


def test_a_record_without_principles_is_not_sent_to_read_them(
        tmp_path, monkeypatch, capsys):
    (tmp_path / "luria.yaml").write_text(CUSTOM)
    init.run(into=str(tmp_path))
    claude = (tmp_path / "CLAUDE.md").read_text()
    assert "design-principles" not in claude
    _repoint(tmp_path, monkeypatch)
    adr_index.run()
    assert _findings(capsys) == ""


def test_a_record_with_principles_is_sent_to_where_they_render(tmp_path):
    """The link follows the config: a principles page somewhere else is
    linked where it actually is."""
    init.run(into=str(tmp_path))
    assert "(docs/design-principles.md)" in (tmp_path / "CLAUDE.md").read_text()
    moved = tmp_path / "moved"
    moved.mkdir()
    text = (tmp_path / "luria.yaml").read_text().replace(
        "docs/design-principles.md", "docs/values.md")
    (moved / "luria.yaml").write_text(text)
    init.run(into=str(moved))
    claude = (moved / "CLAUDE.md").read_text()
    assert "(docs/values.md)" in claude
    assert "design-principles" not in claude


def test_the_fragment_target_is_scaffolded_with_its_marker(
        tmp_path, monkeypatch):
    init.run(into=str(tmp_path))
    changelog = (tmp_path / "CHANGELOG.md").read_text()
    assert collect.find_marker(changelog) is not None
    _repoint(tmp_path, monkeypatch)
    fragment = new.new_entry("changelog", {}, None)
    fragment.write_text("### Added\n\n- A first entry.\n")
    collect.run()
    assert "- A first entry." in (tmp_path / "CHANGELOG.md").read_text()
    assert not fragment.exists()


def test_a_missing_target_is_a_message_not_a_traceback(tmp_path, monkeypatch,
                                                       capsys):
    """A fragment directory declared after `init` ran has no target yet.
    Say which file, and what writes it (DP-1)."""
    init.run(into=str(tmp_path))
    (tmp_path / "CHANGELOG.md").unlink()
    _repoint(tmp_path, monkeypatch)
    fragment = new.new_entry("changelog", {}, None)
    fragment.write_text("### Added\n\n- An entry.\n")
    with pytest.raises(SystemExit) as stop:
        collect.run()
    said = str(stop.value) + capsys.readouterr().err
    assert "CHANGELOG.md" in said and "luria init" in said


def test_spent_upgrades_speak_only_to_the_record_that_ships_them(
        tmp_path, monkeypatch):
    """The remedy — delete the upgrade — is luria's maintainers' to take, so
    the finding belongs in luria's own record and nowhere else."""
    assert lint.spent_upgrades(), "luria's own record should still be told"
    init.run(into=str(tmp_path))
    _repoint(tmp_path, monkeypatch)
    assert lint.spent_upgrades() == []


def test_a_target_without_a_marker_is_a_message_not_a_traceback(
        tmp_path, monkeypatch):
    """An adopted project's own CHANGELOG.md survives `init` (it never
    overwrites) and has no marker. Name the file and the line to add."""
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\nOld entries.\n")
    init.run(into=str(tmp_path))
    _repoint(tmp_path, monkeypatch)
    fragment = new.new_entry("changelog", {}, None)
    fragment.write_text("### Added\n\n- An entry.\n")
    with pytest.raises(SystemExit, match="CHANGELOG.md.*luria-insert-here"):
        collect.run()
    assert fragment.exists()
