from dataclasses import make_dataclass
import pytest
from luria import config_doc
from luria.config import Fragment, Journal, Remote, RemoteScheme, Scheme, Site, current
ALL_SECTIONS = [Scheme, Fragment, Journal, Remote, RemoteScheme, Site]

def test_renders_a_page_with_every_section():
    text = config_doc.render()
    assert text.startswith('# Configuration')
    for _, cls, _ in config_doc.SECTIONS:
        assert cls in ALL_SECTIONS

@pytest.mark.parametrize('cls', ALL_SECTIONS)
def test_every_public_field_of_every_config_dataclass_has_a_row(cls):
    text = config_doc.render()
    for name, _, _ in config_doc.rows(cls):
        assert f'| `{name}` |' in text, f'{cls.__name__}.{name} missing'

def test_a_new_field_appears_without_touching_the_renderer():
    Invented = make_dataclass('Invented', [('prefix', str), ('novel_key', str, 'x')])
    names = [name for name, _, _ in config_doc.rows(Invented)]
    assert names == ['prefix', 'novel_key']
    assert '| `novel_key` |' in config_doc.table(Invented)

def test_private_fields_are_not_documented():
    assert '_raw' not in config_doc.render()
    assert '_root' not in config_doc.render()

def test_union_types_do_not_break_the_table():
    row = [r for r in config_doc.rows(Scheme) if r[0] == 'output'][0]
    assert '|' in row[1], "precondition: output's type is a union"
    assert 'Path \\| None' in config_doc.table(Scheme)

def test_keys_luria_fills_itself_are_not_labelled_required():
    scheme = dict(((name, default) for name, _, default in config_doc.rows(Scheme)))
    assert scheme['prefix'] == "*the table's own name*"
    assert scheme['dir'] == '*required*'
    site = dict(((name, default) for name, _, default in config_doc.rows(Site)))
    assert site['title'] == '*derived from `issue_url`*'

def test_defaults_are_the_schema_not_this_repos_config():
    scheme = dict(((name, default) for name, _, default in config_doc.rows(Scheme)))
    assert scheme['output'] == '*unset*'
    assert current().schemes['ADR'].output is not None, 'precondition'

def test_indented_examples_become_fenced_blocks():
    assert config_doc.fence('Prose.\n\n    [luria]\n    a = 1\n') == 'Prose.\n\n```toml\n[luria]\na = 1\n```\n'

def test_page_is_registered_as_generated():
    cfg = current()
    assert cfg.is_generated(cfg.config_doc)
    assert cfg.config_doc not in __import__('luria.doc_refs', fromlist=['doc_files']).doc_files()

def test_renders_into_the_index_alongside_every_other_view():
    from luria import adr_index
    assert current().config_doc in adr_index.outputs()

def test_outputs_can_be_redirected(tmp_path):
    path, = config_doc.outputs(tmp_path)
    assert path == tmp_path / 'configuration.md'

def test_render_is_deterministic():
    assert config_doc.render() == config_doc.render()

def test_states_what_is_not_configurable():
    text = config_doc.render()
    assert '## What is not configurable' in text
    assert 'LURIA_JOBS' in text and 'LURIA_ROOT' in text

def test_this_repo_owns_the_schema():
    assert current().owns_schema

def test_an_adopting_project_does_not_own_the_schema(project):
    assert not current().owns_schema

def test_the_reference_is_not_a_view_in_an_adopting_project(project):
    from luria import adr_index
    assert current().config_doc not in adr_index.outputs()

def test_the_record_description_is_a_view_in_both(project):
    from luria import adr_index
    assert current().record_doc in adr_index.outputs()

def test_retire_removes_a_reference_luria_wrote(project):
    stale = current().config_doc
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text(config_doc.render())
    assert config_doc.retire() == [stale]
    assert not stale.exists()

def test_retire_leaves_a_page_the_project_wrote_itself(project):
    theirs = current().config_doc
    theirs.parent.mkdir(parents=True, exist_ok=True)
    theirs.write_text('# Configuration\n\nHow *we* configure our deployment.\n')
    assert config_doc.retire() == []
    assert theirs.exists()

def test_retire_never_touches_the_reference_where_it_belongs():
    assert config_doc.retire() == []
    assert current().config_doc.exists()
