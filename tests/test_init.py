from pathlib import Path
from luria import init

def test_existing_files_are_kept_verbatim(tmp_path, capsys):
    (tmp_path / 'CLAUDE.md').write_text('mine, hands off\n')
    written, skipped, kept = init.write(tmp_path)
    assert (tmp_path / 'CLAUDE.md').read_text() == 'mine, hands off\n'
    assert any((p.name == 'CLAUDE.md' for p in kept))
    assert skipped >= 1 and written >= 1

def test_a_kept_claude_md_gets_the_map_pointer(tmp_path, capsys):
    (tmp_path / 'CLAUDE.md').write_text('mine, hands off\n')
    assert init.run(into=str(tmp_path), dry_run=True) is None
    out = capsys.readouterr().out
    assert 'left alone' in out and 'luria --help' in out
    assert (tmp_path / 'CLAUDE.md').read_text() == 'mine, hands off\n'
CUSTOM = '[luria]\nissue_url = "https://github.com/acme/team/issues/{n}"\n[luria.schemes.RFC]\ndir = "record/rfcs.d"\noutput = "docs/rfcs"\n[luria.journals.incidents]\ndir = "record/incidents.d"\noutput = "docs/incidents"\ngranularity = "year"\ntitle = "Incident log"\n'

def repoint(tmp_path, monkeypatch):
    from luria import config
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    config.reset()

def test_a_fresh_default_init_lints_clean(tmp_path, monkeypatch, capsys):
    from luria import adr_index, lint
    init.run(into=str(tmp_path))
    repoint(tmp_path, monkeypatch)
    adr_index.run()
    lint.run()

def test_init_config_scaffolds_the_declared_shape(tmp_path, monkeypatch):
    from luria import adr_index, lint, new
    src = tmp_path / 'team.toml'
    src.write_text(CUSTOM)
    into = tmp_path / 'proj'
    into.mkdir()
    init.run(into=str(into), config=str(src))
    assert (into / 'luria.toml').read_text() == CUSTOM
    assert (into / 'record' / 'rfcs.d' / '_template.md').exists()
    assert (into / 'record' / 'rfcs.d' / 'README.stub').exists()
    assert (into / 'record' / 'incidents.d' / '_template.md').exists()
    assert not (into / 'record' / 'decisions.d').exists()
    assert not (into / 'record' / 'principles.d').exists()
    views = (into / 'docs' / 'README.md').read_text()
    assert 'rfcs/README.md' in views and 'incidents/README.md' in views
    repoint(into, monkeypatch)
    path = new.new_entry('rfc', {'title': 'Widgets speak JSON'}, None)
    assert path.name == 'RFC-001.md'
    adr_index.run()
    lint.run()

def test_init_config_refuses_a_project_that_already_has_one(tmp_path):
    import pytest
    (tmp_path / 'luria.toml').write_text('[luria]\nissue_url = ""\n')
    src = tmp_path / 'other.toml'
    src.write_text(CUSTOM)
    with pytest.raises(SystemExit):
        init.run(into=str(tmp_path), config=str(src))

def test_init_scaffolds_from_the_projects_own_config(tmp_path):
    (tmp_path / 'luria.toml').write_text(CUSTOM)
    init.run(into=str(tmp_path))
    assert (tmp_path / 'record' / 'rfcs.d' / '_template.md').exists()
    assert not (tmp_path / 'record' / 'decisions.d').exists()

def test_generic_template_matches_new_entrys_contract(tmp_path, monkeypatch):
    from luria import new
    (tmp_path / 'luria.toml').write_text(CUSTOM)
    init.run(into=str(tmp_path))
    repoint(tmp_path, monkeypatch)
    text = new.new_entry('rfc', {}, None).read_text()
    assert 'RFC-NNN' not in text
    assert '# RFC-001:' in text

def test_generated_stub_placeholders_are_single_braced(tmp_path):
    (tmp_path / 'luria.toml').write_text(CUSTOM)
    init.run(into=str(tmp_path))
    stub = (tmp_path / 'record' / 'rfcs.d' / 'README.stub').read_text()
    assert '{categories}' in stub and '{table}' in stub
    assert '{{' not in stub and '}}' not in stub
