"""`luria init` never overwrites, and says something useful when it skips
the one file an agent reads first (ADR-037)."""
from pathlib import Path

from luria import init


def test_existing_files_are_kept_verbatim(tmp_path, capsys):
    (tmp_path / "CLAUDE.md").write_text("mine, hands off\n")
    written, skipped, kept = init.write(tmp_path)
    assert (tmp_path / "CLAUDE.md").read_text() == "mine, hands off\n"
    assert any(p.name == "CLAUDE.md" for p in kept)
    assert skipped >= 1 and written >= 1


def test_a_kept_claude_md_gets_the_map_pointer(tmp_path, capsys):
    """The file isn't touched — the recommendation goes to stdout, where
    permission isn't needed."""
    (tmp_path / "CLAUDE.md").write_text("mine, hands off\n")
    assert init.run(into=str(tmp_path), dry_run=True) is None
    out = capsys.readouterr().out
    assert "left alone" in out and "luria --help" in out
    assert (tmp_path / "CLAUDE.md").read_text() == "mine, hands off\n"


# --- the scaffold is planned from configuration (ADR-048) ----------------

CUSTOM = """\
[luria]
issue_url = "https://github.com/acme/team/issues/{n}"
[luria.schemes.RFC]
dir = "record/rfcs.d"
output = "docs/rfcs"
[luria.journals.incidents]
dir = "record/incidents.d"
output = "docs/incidents"
granularity = "year"
title = "Incident log"
"""


def repoint(tmp_path, monkeypatch):
    from luria import config
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()


def test_a_fresh_default_init_lints_clean(tmp_path, monkeypatch, capsys):
    """The three documented commands, run as documented. This exact loop
    caught two template defects the day it was first automated — a bare
    LU-ADR-048 and a bare DP-1, both invisible until scheme-driven reference
    detection existed — so it stays as the guard for that whole class."""
    from luria import adr_index, lint
    init.run(into=str(tmp_path))
    repoint(tmp_path, monkeypatch)
    adr_index.run()
    lint.run()                            # raises SystemExit on any violation


def test_init_config_scaffolds_the_declared_shape(tmp_path, monkeypatch):
    """`--config` installs the file and scaffolds what it declares — and
    nothing else: no decision directory for a project that declared no
    decision scheme."""
    from luria import adr_index, lint, new
    src = tmp_path / "team.toml"
    src.write_text(CUSTOM)
    into = tmp_path / "proj"
    into.mkdir()
    init.run(into=str(into), config=str(src))

    assert (into / "luria.toml").read_text() == CUSTOM
    assert (into / "record" / "rfcs.d" / "_template.md").exists()
    assert (into / "record" / "rfcs.d" / "README.stub").exists()
    assert (into / "record" / "incidents.d" / "_template.md").exists()
    assert not (into / "record" / "decisions.d").exists()
    assert not (into / "record" / "principles.d").exists()

    views = (into / "docs" / "README.md").read_text()
    assert "rfcs/README.md" in views and "incidents/README.md" in views

    # And the scaffold is drivable: file an RFC from the generic template,
    # render, lint — the loop an adopter runs in their first five minutes.
    repoint(into, monkeypatch)
    path = new.new_entry("rfc", {"title": "Widgets speak JSON"}, None)
    assert path.name == "RFC-001.md"
    adr_index.run()
    lint.run()


def test_init_config_refuses_a_project_that_already_has_one(tmp_path):
    """Scaffolding one config's shape while a different config governs the
    record would build directories the project's own machinery doesn't know
    about — an error, not a skip."""
    import pytest
    (tmp_path / "luria.toml").write_text('[luria]\nissue_url = ""\n')
    src = tmp_path / "other.toml"
    src.write_text(CUSTOM)
    with pytest.raises(SystemExit):
        init.run(into=str(tmp_path), config=str(src))


def test_init_scaffolds_from_the_projects_own_config(tmp_path):
    """A project that already has a `luria.toml` gets that config's shape,
    not the template's. This was the old wart: init used to copy the fixed
    tree regardless, scaffolding decision directories for a record whose
    config declared none."""
    (tmp_path / "luria.toml").write_text(CUSTOM)
    init.run(into=str(tmp_path))
    assert (tmp_path / "record" / "rfcs.d" / "_template.md").exists()
    assert not (tmp_path / "record" / "decisions.d").exists()


def test_generic_template_matches_new_entrys_contract(tmp_path, monkeypatch):
    """The `{PREFIX}-NNN` placeholder is `luria new`'s substitution target
    (ADR-036); a scaffolded template that misspelled it would copy the
    placeholder into every real document."""
    from luria import new
    (tmp_path / "luria.toml").write_text(CUSTOM)
    init.run(into=str(tmp_path))
    repoint(tmp_path, monkeypatch)
    text = new.new_entry("rfc", {}, None).read_text()
    assert "RFC-NNN" not in text
    assert "# RFC-001:" in text
