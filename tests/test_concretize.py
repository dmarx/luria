import re
import subprocess
from pathlib import Path
import pytest
from luria import adr_index, concretize, config, doc_refs, lint, new
TOML = '[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.schemes.ADR]\ndir = "record/decisions.d"\noutput = "docs/decisions"\nallocate = "merge"\n'

@pytest.fixture
def merge_project(tmp_path, monkeypatch):
    (tmp_path / 'luria.toml').write_text(TOML)
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'docs' / 'README.md').write_text('# Docs\n\n- [Decisions](decisions/README.md)\n')
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    config.reset()
    first = new.new_entry('adr', {'title': 'First decision'}, None)
    second = new.new_entry('adr', {'title': 'Second decision'}, None)
    a, b = (first.stem, second.stem)
    first.write_text(first.read_text() + f'\nPaired with [[{b}]].\n')
    second.write_text(second.read_text() + f'\nBuilds on {a}.\n')
    subprocess.run(['git', 'init', '-q', '.'], cwd=tmp_path, check=True)
    subprocess.run(['git', '-c', 'user.email=t@t', '-c', 'user.name=t', 'add', '-A'], cwd=tmp_path, check=True)
    subprocess.run(['git', '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'seed'], cwd=tmp_path, check=True)
    return (tmp_path, first, second)

def lint_errors() -> list[str]:
    errors: list[str] = []
    lint.check_frontmatter(errors)
    lint.check_bare_refs(errors)
    lint.check_wikilinks(errors)
    return errors

def test_prose_that_merely_resembles_a_code_is_not_a_reference(merge_project):
    _, first, _ = merge_project
    assert doc_refs.find_refs('the ADR-review process', first) == []
    assert doc_refs.find_refs('see ADR-tmpab123 here', first), '…while a real sentinel-shaped code is found'

def test_a_minted_code_can_never_be_read_as_a_number(merge_project):
    _, first, second = merge_project
    scheme = config.current().schemes['ADR']
    for path in (first, second):
        tail = scheme.temp_of(path)
        assert re.fullmatch('tmp[a-z0-9]{5}', tail), 'the sentinel is spelled out — provisional at a glance (ADR-049)'
        assert scheme.number_of(path) is None, 'the patterns are disjoint'

def test_temp_documents_are_first_class_on_the_branch(merge_project):
    root, first, second = merge_project
    adr_index.run()
    index = (root / 'docs' / 'decisions' / 'README.md').read_text()
    assert first.stem in index and second.stem in index
    errors = lint_errors()
    assert any((f'{first.stem} is not a link' in e for e in errors)), 'a bare temp reference is demanded like any other'
    linked, count = doc_refs.linkify(second.read_text(), second)
    assert count == 1
    assert f'[{first.stem}]({first.name})' in linked

def test_concretize_assigns_renames_rewrites_and_aliases(merge_project):
    root, first, second = merge_project
    a, b = (first.stem, second.stem)
    doc_refs_fixed = doc_refs.linkify(second.read_text(), second)[0]
    second.write_text(doc_refs_fixed)
    adr_index.run()
    concretize.run()
    scheme = config.current().schemes['ADR']
    docs = scheme.documents()
    assert sorted(docs) == [1, 2], 'sequential numbers, no temp files left'
    assert scheme.temp_documents() == {}
    texts = {n: p.read_text() for n, p in docs.items()}
    by_title = {'First' if 'First' in t else 'Second': (n, t) for n, t in texts.items()}
    n_first, t_first = by_title['First']
    n_second, t_second = by_title['Second']
    assert f'[ADR-{n_first:03d}](ADR-{n_first:03d}.md)' in t_second
    assert a not in t_second, 'no temporary code survives outside formerly:'
    assert re.search(f'^formerly:\\n- {a}$', t_first, flags=re.MULTILINE)
    index = (root / 'docs' / 'decisions' / 'README.md').read_text()
    assert 'ADR-001' in index and a not in index

def test_an_aliased_code_resolves_forever(merge_project):
    root, first, _ = merge_project
    a = first.stem
    concretize.run()
    elsewhere = root / 'docs' / 'README.md'
    linked, count = doc_refs.linkify(f'As {a} said.', elsewhere)
    assert count == 1 and 'record/decisions.d/ADR-' in linked
    wiki, count = doc_refs.linkify(f'And [[{a}]] too.', elsewhere)
    assert count == 1 and 'record/decisions.d/ADR-' in wiki

def test_check_guards_the_trunk(merge_project):
    with pytest.raises(SystemExit):
        concretize.run(check=True)
    concretize.run()
    concretize.run(check=True)

def test_concretize_rewrites_history_too(merge_project):
    root, first, _ = merge_project
    a = first.stem
    (root / 'luria.toml').write_text(TOML + '[luria.journals.devlog]\ndir = "record/devlog.d"\noutput = "docs/devlog"\n')
    config.reset()
    entry = root / 'record' / 'devlog.d' / '2026' / '01' / '02' / '030405.md'
    entry.parent.mkdir(parents=True)
    entry.write_text(f"---\ntitle: 'A day'\ncreated: '2026-01-02T03:04:05'\n---\n\nToday we filed {a}.\n")
    concretize.run()
    text = entry.read_text()
    assert a not in text, 'history is swept to the canonical spelling'
    assert 'Today we filed ADR-' in text

def test_filing_allocation_is_untouched(project):
    (project / 'record' / 'decisions.d').mkdir(parents=True)
    path = new.new_entry('adr', {'title': 'Numbered on the spot'}, None)
    assert path.name == 'ADR-001.md'

def test_a_legacy_spelling_is_reported_and_upgraded(merge_project):
    root, first, _ = merge_project
    a = first.stem
    concretize.run()
    straggler = root / 'docs' / 'straggler.md'
    straggler.write_text(f'# Late branch\n\nPer {a}, we chose this.\n')
    rows = doc_refs.legacy_spellings()
    assert len(rows) == 1 and a in rows[0] and ('→ ADR-' in rows[0])
    linked, count = doc_refs.linkify(straggler.read_text(), straggler)
    assert count == 1
    assert a not in linked, 'the spelling is upgraded, not preserved'
    assert '[ADR-0' in linked
    straggler.write_text(linked)
    assert doc_refs.legacy_spellings() == [], 'fixed means gone'

def test_a_live_temp_code_is_not_a_legacy_spelling(merge_project):
    assert doc_refs.legacy_spellings() == []

def test_the_warning_is_promotable(merge_project, monkeypatch):
    root, first, _ = merge_project
    concretize.run()
    (root / 'docs' / 'straggler.md').write_text(f'# Late\n\nPer {first.stem}.\n')
    assert any((cls == 'legacy-spellings' for cls, _, _ in lint.status_sections()))
