import pytest
from luria import adr_index, config, record_doc
from luria.config import current

@pytest.fixture
def unusual(tmp_path, monkeypatch):
    (tmp_path / 'spec.d').mkdir()
    (tmp_path / 'notes.d').mkdir()
    (tmp_path / 'incidents.d').mkdir()
    (tmp_path / 'news.d').mkdir()
    (tmp_path / 'luria.toml').write_text('\n[luria]\nissue_url = "https://example.test/issues/{n}"\nstale_days = 14\n\n[luria.paths]\ndocs = "documentation"\n\n[luria.schemes.RFC]\ndir = "spec.d"\noutput = "documentation/specs"\nactive = "Ratified"\n\n[luria.fragments."news.d"]\nfile = "NEWS.md"\n\n[luria.journals.notes]\ndir = "notes.d"\noutput = "documentation/notes"\ngranularity = "year"\ntitle = "Field notes"\n\n[luria.journals.incidents]\ndir = "incidents.d"\noutput = "documentation/incidents"\ntitle = "Incidents"\n\n[luria.remotes.LU]\nname = "luria"\nrepo = "dmarx/luria"\ndir = "record/decisions.d"\n')
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    config.reset()
    yield tmp_path
    config.reset()

def test_names_every_scheme_the_project_declared(unusual):
    section = record_doc.render().split('## Referable')[1].split('\n## ')[0]
    assert '`RFC-001`' in section and '`spec.d/`' in section
    assert '`Ratified`' in section
    assert 'ADR-001' not in section

def test_names_every_journal_including_the_second(unusual):
    text = record_doc.render()
    for name, title, grain in [('notes', 'Field notes', 'year'), ('incidents', 'Incidents', 'month')]:
        assert f'`{name}`' in text and title in text
        assert grain in text

def test_names_the_fragment_directory_and_its_target(unusual):
    text = record_doc.render()
    assert '`news.d/`' in text and '`NEWS.md`' in text
    assert 'changelog.d' not in text

def test_names_each_remote_by_the_prefix_a_citation_carries(unusual):
    text = record_doc.render()
    assert '`LU-' in text and 'dmarx/luria' in text

def test_filing_table_offers_exactly_what_the_cli_dispatches_on(unusual):
    from luria.new import kinds
    text = record_doc.render()
    for kind in kinds():
        assert f'--kind {kind} ' in text, f'{kind} missing from the table'
    assert '--kind adr ' not in text

def test_a_new_family_appears_without_touching_the_renderer(unusual):
    before = record_doc.render()
    assert 'POLICY-001' not in before
    (unusual / 'policy.d').mkdir()
    (unusual / 'luria.toml').write_text((unusual / 'luria.toml').read_text() + '\n[luria.schemes.POLICY]\ndir = "policy.d"\n')
    config.reset()
    assert '`POLICY-001`' in record_doc.render()

def test_settings_table_shows_what_changed_and_not_what_did_not(unusual):
    text = record_doc.render().split('## Settings')[1]
    assert '`stale_days`' in text and '`14`' in text and ('`90`' in text)
    assert 'fail_on' not in text

def test_a_nested_table_is_one_row_not_one_row_per_colour(project):
    (project / 'luria.toml').write_text((project / 'luria.toml').read_text() + '\n[luria.site.theme.light]\n' + ''.join((f'c{i} = "#00000{i}"\n' for i in range(9))))
    config.reset()
    text = record_doc.render()
    assert '`site.theme`' in text
    assert 'c0' not in text and '#000000' not in text

def test_family_tables_stay_out_of_the_settings_diff(unusual):
    text = record_doc.render().split('## Settings')[1]
    for family in record_doc.FAMILIES:
        assert f'`{family}' not in text

def test_the_page_is_the_same_after_the_generator_has_run(unusual):
    first = record_doc.render()
    adr_index.run()
    assert record_doc.render() == first
    assert (unusual / 'documentation' / 'record.md').read_text() == first

def test_the_page_lands_where_the_docs_surface_is(unusual):
    assert current().record_doc == unusual / 'documentation' / 'record.md'

def test_the_fixer_leaves_it_alone(unusual):
    assert current().is_generated(current().record_doc)
