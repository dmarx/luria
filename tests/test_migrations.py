import subprocess
from pathlib import Path
from luria import aliases, concretize, config, doc_refs, lint, migrate, ref_status

def _record_project(tmp_path, monkeypatch):
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.paths]\ndesign_principles = "docs/guiding-principles.md"\n[luria.schemes.GP]\ndir = "record/principles.d"\nrender = "document"\noutput = "docs/guiding-principles.md"\n[luria.remotes.SG]\nrepo = "example/strata-g"\n')
    gp_dir = tmp_path / 'record' / 'principles.d'
    gp_dir.mkdir(parents=True)
    (gp_dir / 'GP-004.md').write_text("---\nstatus: Active\ntitle: 'A principle'\ntags:\n- record\ndate: '2026-01-01'\nformerly:\n- DP-4\n---\n\n# GP-004: A principle\n\nBody.\n")
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    config.reset()
    aliases.reset()
    return tmp_path

def test_the_alias_map_derives_from_formerly(tmp_path, monkeypatch):
    _record_project(tmp_path, monkeypatch)
    assert aliases.alias_map() == {'DP-004': 'GP-004'}

def _git(root, *args):
    subprocess.run(['git', *args], cwd=root, capture_output=True, check=True)

def _premigration_project(tmp_path, monkeypatch):
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.paths]\ndesign_principles = "docs/design-principles.md"\n[luria.schemes.DP]\ndir = "record/principles.d"\nrender = "document"\noutput = "docs/design-principles.md"\n[luria.remotes.SG]\nrepo = "example/strata-g"\n[luria.remotes.SG.schemes.DP]\ndocument = "docs/design-principles.md"\n[luria.remotes.LU]\nrepo = "example/this-project"\n[luria.remotes.LU.schemes.DP]\ndocument = "docs/design-principles.md"\n')
    (tmp_path / 'docs' / 'design-principles.md').write_text('<!-- GENERATED -->\n\n# Principles\n\n<a name="dp-4"></a>\n\n## 4. Fourth value\n')
    dp_dir = tmp_path / 'record' / 'principles.d'
    dp_dir.mkdir(parents=True)
    for n, title in ((1, 'First value'), (4, 'Fourth value')):
        (dp_dir / f'DP-{n:03d}.md').write_text(f"---\nstatus: Active\ntitle: '{title}'\ntags:\n- record\ndate: '2026-01-01'\n---\n\n# DP-{n:03d}: {title}\n\nBody citing DP-1 sometimes.\n")
    (tmp_path / 'docs' / 'notes.md').write_text("# Notes\n\nBare DP-4 and a link [DP-4](design-principles.md#dp-4).\nFixture DP-018 is nobody's document.\nForeign SG-DP-4 belongs to strata-g.\nMirrored LU-DP-004 follows this project.\n[theirs](https://example.test/sg/docs/design-principles.md#x)\n")
    entry_dir = tmp_path / 'record' / 'devlog.d' / '2026' / '08' / '01'
    entry_dir.mkdir(parents=True)
    (entry_dir / '120000.md').write_text("---\ntitle: 'An entry'\ncreated: '2026-08-01T12:00:00'\ntags: []\n---\n\nBook-frame link: [DP-4](../../record/../docs/design-principles.md#dp-4).\n")
    mig_dir = tmp_path / 'record' / 'migrations.d'
    mig_dir.mkdir(parents=True)
    (mig_dir / '0001-dp-to-gp.toml').write_text('title = "DP becomes GP"\nissue = "#29"\n\n[[operations]]\nop = "rename_scheme"\nfrom = "DP"\nto = "GP"\noutput = "docs/guiding-principles.md"\nremotes = ["LU"]\n')
    _git(tmp_path, 'init', '-q')
    _git(tmp_path, 'add', '-A')
    _git(tmp_path, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'before')
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    config.reset()
    aliases.reset()
    return tmp_path

def test_dry_run_prints_the_plan_and_changes_nothing(tmp_path, monkeypatch, capsys):
    root = _premigration_project(tmp_path, monkeypatch)
    before = {p: p.read_text() for p in root.rglob('*.md')}
    migrate.run('0001', dry_run=True)
    out = capsys.readouterr().out
    assert 'DP-001 -> GP-001' in out and 'DP-004 -> GP-004' in out
    assert 'LU-DP-004 -> LU-GP-004' in out
    assert 'design-principles.md -> guiding-principles.md' in out
    assert {p: p.read_text() for p in root.rglob('*.md')} == before

def test_rename_scheme_end_to_end(tmp_path, monkeypatch, capsys):
    root = _premigration_project(tmp_path, monkeypatch)
    migrate.run('0001')
    dp_dir = root / 'record' / 'principles.d'
    assert not (dp_dir / 'DP-004.md').exists()
    moved = (dp_dir / 'GP-004.md').read_text()
    assert 'formerly:\n- DP-4\n' in moved, 'identity stamped'
    assert '# GP-004: Fourth value' in moved, 'own heading swept'
    assert 'citing GP-1 sometimes' in moved, 'cross-citations swept'
    config_text = (root / 'luria.toml').read_text()
    assert '[luria.schemes.GP]' in config_text
    assert '[luria.schemes.DP]' not in config_text
    assert 'design_principles = "docs/guiding-principles.md"' in config_text
    assert 'output = "docs/guiding-principles.md"' in config_text
    assert '[luria.remotes.LU.schemes.GP]' in config_text, 'mirror follows'
    assert config_text.count('document = "docs/guiding-principles.md"') == 1
    assert '[luria.remotes.SG.schemes.DP]' in config_text, 'theirs stays'
    assert 'document = "docs/design-principles.md"' in config_text, "SG's own path untouched by the section-aware pass"
    assert not (root / 'docs' / 'design-principles.md').exists(), 'a generated view is removed, not renamed — the next index rebuilds it'
    notes = (root / 'docs' / 'notes.md').read_text()
    assert 'Bare GP-4 and a link [GP-4](guiding-principles.md#gp-4).' in notes
    assert "Fixture DP-018 is nobody's document." in notes, 'not in the mapping'
    assert 'Foreign SG-DP-4 belongs to strata-g.' in notes, 'their namespace'
    assert 'Mirrored LU-GP-004 follows this project.' in notes
    assert 'https://example.test/sg/docs/design-principles.md#x' in notes, 'a foreign URL never follows a local path pair'
    entry = next((root / 'record' / 'devlog.d').rglob('1*.md')).read_text()
    assert '[GP-4](../../record/../docs/guiding-principles.md#gp-4)' in entry, "history swept, and the link's frame untouched (#57)"
    spec = (root / 'record' / 'migrations.d' / '0001-dp-to-gp.toml').read_text()
    assert 'from = "DP"' in spec, 'the spec remembers the old spelling'
    config.reset()
    aliases.reset()
    assert aliases.alias_map() == {'DP-001': 'GP-001', 'DP-004': 'GP-004'}

def test_a_rename_mirrors_each_citation_s_padding(tmp_path, monkeypatch):
    root = _premigration_project(tmp_path, monkeypatch)
    page = root / 'docs' / 'padding.md'
    page.write_text('Padded DP-004, bare DP-4, anchor [x](design-principles.md#dp-4).\n')
    _git(root, 'add', '-A')
    _git(root, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'padding')
    migrate.run('0001')
    out = page.read_text()
    assert 'Padded GP-004' in out, out
    assert 'bare GP-4,' in out, out
    assert '#gp-4)' in out, out

def test_move_doc_lands_provisional_then_concretizes(tmp_path, monkeypatch):
    root = _premigration_project(tmp_path, monkeypatch)
    (root / 'luria.toml').write_text((root / 'luria.toml').read_text() + '[luria.schemes.VAL]\ndir = "record/values.d"\n')
    (root / 'record' / 'values.d').mkdir(parents=True)
    config.reset()
    aliases.reset()
    mig = root / 'record' / 'migrations.d' / '0002-promote.toml'
    mig.write_text('title = "DP-4 becomes a value"\n\n[[operations]]\nop = "move_doc"\ndoc = "DP-4"\nto = "VAL"\n')
    migrate.run('0002')
    landed = list((root / 'record' / 'values.d').glob('VAL-tmp*.md'))
    assert len(landed) == 1, 'the move lands provisional, never numbered'
    assert 'formerly:\n- DP-4\n' in landed[0].read_text()
    assert not (root / 'record' / 'principles.d' / 'DP-004.md').exists()
    notes = (root / 'docs' / 'notes.md').read_text()
    assert '(../record/values.d/VAL-tmp' in notes, notes
    assert 'design-principles.md#val' not in notes, 'no link to the old view'
    _git(root, 'add', '-A')
    _git(root, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'migrated')
    config.reset()
    aliases.reset()
    concretize.run()
    final = (root / 'record' / 'values.d' / 'VAL-001.md').read_text()
    assert '- DP-4' in final and '- VAL-tmp' in final, 'both the migrated-from code and the provisional one stay resolvable'
    notes = (root / 'docs' / 'notes.md').read_text()
    assert '[VAL-001](../record/values.d/VAL-001.md)' in notes, notes
    assert 'val-tmp' not in notes, 'no provisional spelling survives the sweep'
    assert 'Fixture DP-018' in notes, 'a fixture number is not in the mapping'

def test_two_moves_into_one_scheme_do_not_collide(tmp_path, monkeypatch):
    root = _premigration_project(tmp_path, monkeypatch)
    (root / 'luria.toml').write_text((root / 'luria.toml').read_text() + '[luria.schemes.VAL]\ndir = "record/values.d"\n')
    (root / 'record' / 'values.d').mkdir(parents=True)
    config.reset()
    aliases.reset()
    mig = root / 'record' / 'migrations.d' / '0002-promote-both.toml'
    mig.write_text('title = "Both principles become values"\n\n[[operations]]\nop = "move_doc"\ndoc = "DP-1"\nto = "VAL"\n\n[[operations]]\nop = "move_doc"\ndoc = "DP-4"\nto = "VAL"\n')
    migrate.run('0002')
    landed = sorted((root / 'record' / 'values.d').glob('VAL-tmp*.md'))
    assert len(landed) == 2, [p.name for p in landed]
    assert not list((root / 'record' / 'principles.d').glob('DP-*.md'))
    _git(root, 'add', '-A')
    _git(root, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'migrated')
    config.reset()
    aliases.reset()
    concretize.run()
    numbered = sorted((p.name for p in (root / 'record' / 'values.d').glob('VAL-0*.md')))
    assert numbered == ['VAL-001.md', 'VAL-002.md'], numbered

def test_move_doc_supersede_copies_and_tombstones(tmp_path, monkeypatch):
    root = _premigration_project(tmp_path, monkeypatch)
    (root / 'luria.toml').write_text((root / 'luria.toml').read_text() + '[luria.schemes.VAL]\ndir = "record/values.d"\n')
    (root / 'record' / 'values.d').mkdir(parents=True)
    config.reset()
    aliases.reset()
    mig = root / 'record' / 'migrations.d' / '0002-supersede.toml'
    mig.write_text('title = "DP-4 superseded by a value"\n\n[[operations]]\nop = "move_doc"\ndoc = "DP-4"\nto = "VAL"\nstrategy = "supersede"\n')
    migrate.run('0002')
    old = (root / 'record' / 'principles.d' / 'DP-004.md').read_text()
    assert 'status: Superseded — by VAL-tmp' in old
    assert len(list((root / 'record' / 'values.d').glob('VAL-tmp*.md'))) == 1
    assert 'Bare DP-4' in (root / 'docs' / 'notes.md').read_text(), 'supersede mode rewrites nothing'
    _git(root, 'add', '-A')
    _git(root, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'superseded')
    config.reset()
    aliases.reset()
    concretize.run()
    old = (root / 'record' / 'principles.d' / 'DP-004.md').read_text()
    assert 'status: Superseded — by VAL-001' in old
    assert 'Bare DP-4' in (root / 'docs' / 'notes.md').read_text()

def test_new_migration_scaffolds_a_numbered_spec(tmp_path, monkeypatch):
    _premigration_project(tmp_path, monkeypatch)
    from luria import new
    path = new.new_entry('migration', {'title': 'A second move'}, None)
    assert path.name == '0002-a-second-move.toml'
    assert 'title = "A second move"' in path.read_text()

def test_the_sweep_honors_unlinted_file(tmp_path, monkeypatch, capsys):
    root = _premigration_project(tmp_path, monkeypatch)
    specimen = root / 'docs' / 'specimens.md'
    specimen.write_text('<!-- unlinted-file: — every code here is a specimen -->\n\n# Specimens\n\nThe old spelling DP-4 preserved verbatim.\n')
    _git(root, 'add', '-A')
    migrate.run('0001')
    assert 'The old spelling DP-4 preserved verbatim.' in specimen.read_text()

def test_provisional_is_decided_in_one_place(tmp_path, monkeypatch):
    from luria.config import is_temp_tail
    assert is_temp_tail('tmp47fje') and (not is_temp_tail('004'))
    assert not is_temp_tail('nonsense'), 'not-a-number is not the same test'
    assert migrate.Pair('DP-004', 'VAL-tmp47fje').new_is_provisional
    assert not migrate.Pair('DP-004', 'VAL-007').new_is_provisional
    assert not migrate.Pair('DP-004', 'VAL-nonsense').new_is_provisional

def test_a_same_render_move_keeps_its_links_untouched(tmp_path, monkeypatch):
    root = _premigration_project(tmp_path, monkeypatch)
    (root / 'luria.toml').write_text((root / 'luria.toml').read_text() + '[luria.schemes.SRC]\ndir = "record/src.d"\n[luria.schemes.DST]\ndir = "record/dst.d"\n')
    (root / 'record' / 'src.d').mkdir(parents=True)
    (root / 'record' / 'dst.d').mkdir(parents=True)
    (root / 'record' / 'src.d' / 'SRC-001.md').write_text("---\nstatus: Active\ntitle: 'A thing'\ntags:\n- record\ndate: '2026-01-01'\n---\n\n# SRC-001: A thing\n\nBody.\n")
    page = root / 'docs' / 'shapes.md'
    page.write_text('See [SRC-001](../record/src.d/SRC-001.md).\n')
    config.reset()
    aliases.reset()
    _git(root, 'add', '-A')
    _git(root, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'shapes')
    mig = root / 'record' / 'migrations.d' / '0002-same-shape.toml'
    mig.write_text('title = "SRC-1 becomes a DST"\n\n[[operations]]\nop = "move_doc"\ndoc = "SRC-1"\nto = "DST"\n')
    migrate.run('0002')
    out = page.read_text()
    assert '(../record/dst.d/DST-tmp' in out, out
    assert 'src.d' not in out, 'the path follows the move'

def test_a_worded_citation_of_a_moved_document_is_rebuilt(tmp_path, monkeypatch):
    root = _premigration_project(tmp_path, monkeypatch)
    (root / 'luria.toml').write_text((root / 'luria.toml').read_text() + '[luria.schemes.VAL]\ndir = "record/values.d"\n')
    (root / 'record' / 'values.d').mkdir(parents=True)
    page = root / 'docs' / 'worded.md'
    page.write_text('The fix ([design-principles #4](design-principles.md#dp-4)) held.\n')
    config.reset()
    aliases.reset()
    _git(root, 'add', '-A')
    _git(root, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'worded')
    mig = root / 'record' / 'migrations.d' / '0002-worded.toml'
    mig.write_text('title = "DP-4 becomes a value"\n\n[[operations]]\nop = "move_doc"\ndoc = "DP-4"\nto = "VAL"\n')
    migrate.run('0002')
    out = page.read_text()
    assert 'design-principles.md#dp-4' not in out, out
    assert '#dp-4' not in out, 'the vacated anchor must not survive anywhere'
    assert 'VAL-tmp' in out, out

def _worded_move_project(tmp_path, monkeypatch):
    root = _premigration_project(tmp_path, monkeypatch)
    (root / 'luria.toml').write_text((root / 'luria.toml').read_text() + '[luria.code]\nglobs = ["src/*.py"]\n[luria.schemes.VAL]\ndir = "record/values.d"\n')
    (root / 'record' / 'values.d').mkdir(parents=True)
    (root / 'src').mkdir()
    (root / 'src' / 'engine.py').write_text('# Selection rides undo by decision (design-principles #4), not by\n# accident. DP-4 is the claim; DP-1 is a different one.\nSELECTION_RIDES_UNDO = True\n')
    config.reset()
    aliases.reset()
    _git(root, 'add', '-A')
    _git(root, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'src')
    (root / 'record' / 'migrations.d' / '0002-worded-code.toml').write_text('title = "DP-4 becomes a value"\n\n[[operations]]\nop = "move_doc"\ndoc = "DP-4"\nto = "VAL"\n')
    return root

def test_the_relink_pass_stops_where_the_hyperlink_lint_stops(tmp_path, monkeypatch):
    root = _worded_move_project(tmp_path, monkeypatch)
    migrate.run('0002')
    src = (root / 'src' / 'engine.py').read_text()
    assert '](' not in src, f'no markdown links in a source file:\n{src}'
    assert 'DP-1 is a different one' in src, src

def test_a_worded_citation_in_code_follows_the_move(tmp_path, monkeypatch):
    root = _worded_move_project(tmp_path, monkeypatch)
    migrate.run('0002')
    src = (root / 'src' / 'engine.py').read_text()
    assert 'design-principles #4' not in src, src
    assert '#4' not in src, 'the vacated anchor number must not survive'
    assert src.count('VAL-tmp') == 2, f'both spellings respelled:\n{src}'
    assert 'DP-1 is a different one' in src, 'an unmoved code is left alone'

def test_a_formerly_stamp_is_not_a_dangling_citation(tmp_path, monkeypatch):
    root = _worded_move_project(tmp_path, monkeypatch)
    migrate.run('0002')
    config.reset()
    aliases.reset()
    moved = next((root / 'record' / 'values.d').glob('VAL-*.md'))
    assert 'formerly:' in moved.read_text(), moved.read_text()
    assert 'DP-004' not in ref_status.scan().dangling, 'the stamp is a declaration, not a citation'
