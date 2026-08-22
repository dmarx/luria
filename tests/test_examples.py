import shutil
from pathlib import Path
import pytest
from luria import adr_index, config, doc_refs, lint
EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'
NAMES = ['rfcs-and-specs', 'collocated', 'many-journals', 'external-citations']

@pytest.fixture
def example(tmp_path, monkeypatch):

    def build(name: str) -> Path:
        root = tmp_path / name
        shutil.copytree(EXAMPLES / name, root)
        monkeypatch.setenv('LURIA_ROOT', str(root))
        config.reset()
        adr_index.run()
        return root
    return build

def lint_errors() -> list[str]:
    errors: list[str] = []
    lint.check_docs_index(errors)
    lint.check_frontmatter(errors)
    lint.check_generated_index(errors)
    lint.check_journals(errors)
    lint.check_bare_refs(errors)
    lint.check_wikilinks(errors)
    return errors

@pytest.mark.parametrize('name', NAMES)
def test_every_example_lints_clean(example, name):
    example(name)
    assert lint_errors() == []

@pytest.mark.parametrize('name', NAMES)
def test_every_example_render_is_stable(example, name):
    example(name)
    first = adr_index.outputs()
    assert all((p.read_text() == text for p, text in first.items()))

def test_two_schemes_render_in_their_two_shapes(example):
    root = example('rfcs-and-specs')
    index = (root / 'docs' / 'rfcs' / 'README.md').read_text()
    assert 'RFC-001' in index
    assert (root / 'docs' / 'rfcs' / 'tags' / 'protocol.md').exists()
    document = (root / 'docs' / 'interfaces.md').read_text()
    assert 'id, a kind and a payload' in document, 'the body, not just a link'
    assert '<a name="spec-1"></a>' in document
    assert document.startswith('# SPEC documents'), "a scheme with no README.stub is titled after itself, not after this package's principles"
    cfg = config.current()
    assert set(cfg.schemes) >= {'RFC', 'SPEC'}
    assert cfg.schemes['SPEC'].render == 'document'

def test_a_view_can_render_beside_its_sources(example):
    root = example('collocated')
    assert (root / 'decisions' / 'README.md').exists()
    assert (root / 'decisions' / 'tags' / 'record.md').exists()
    assert not (root / 'docs' / 'decisions').exists()

def test_three_journals_at_three_granularities(example):
    root = example('many-journals')
    assert {j for j in config.current().journals} >= {'devlog', 'incidents', 'meetings'}
    assert (root / 'docs' / 'devlog' / '2026-03.md').exists()
    assert (root / 'docs' / 'incidents' / '2026.md').exists()
    assert (root / 'docs' / 'meetings' / '2026-03-12.md').exists()

def test_uid_remotes_link_things_that_are_not_records(example):
    root = example('external-citations')
    source = root / 'record' / 'notes.d' / 'NOTE-001.md'
    linked, count = doc_refs.linkify('Method: ARXIV-2301.07041, ticket JIRA:PLAT-88, hold CVE-2024-3094.', source)
    assert count == 3
    assert 'https://arxiv.org/abs/2301.07041' in linked
    assert 'https://acme.atlassian.net/browse/PLAT-88' in linked
    assert 'https://nvd.nist.gov/vuln/detail/CVE-2024-3094' in linked

def test_a_uid_remote_can_move_its_delimiter(example):
    example('external-citations')
    assert config.current().remotes['JIRA'].delim == ':'

def test_active_selects_a_status_it_does_not_define(example):
    root = example('rfcs-and-specs')
    rfc = root / 'record' / 'rfcs.d' / 'RFC-001.md'
    rfc.write_text(rfc.read_text().replace('status: Active', 'status: Accepted'))
    errors: list[str] = []
    lint.check_frontmatter(errors)
    assert any(('nonstandard status' in e for e in errors))

def test_a_declared_family_replaces_the_defaults(example):
    root = example('rfcs-and-specs')
    assert set(config.current().schemes) == {'RFC', 'SPEC'}
    assert not (root / 'docs' / 'decisions').exists(), 'no phantom decision index for a scheme nobody declared'

def test_an_undeclared_family_keeps_the_defaults(example):
    example('many-journals')
    assert 'ADR' in config.current().schemes
    assert set(config.current().journals) == {'devlog', 'incidents', 'meetings'}

def test_omitting_output_collocates_a_declared_scheme(example):
    example('collocated')
    adr = config.current().schemes['ADR']
    assert adr.output is None
    assert adr.view == adr.dir

def test_a_configured_scheme_is_linted_like_any_other(example):
    root = example('rfcs-and-specs')
    source = root / 'record' / 'specs.d' / 'SPEC-001.md'
    refs = doc_refs.find_refs('see RFC-001 and SPEC-001', source)
    assert [(r.kind, r.prefix, r.num) for r in refs] == [('scheme', 'RFC', 1), ('scheme', 'SPEC', 1)]

def test_cross_scheme_references_resolve_to_each_shape(example):
    root = example('rfcs-and-specs')
    from_rfc, _ = doc_refs.linkify('See SPEC-001.', root / 'record' / 'rfcs.d' / 'RFC-001.md')
    assert 'interfaces.md#spec-1' in from_rfc
    from_spec, _ = doc_refs.linkify('Motivated by RFC-001.', root / 'record' / 'specs.d' / 'SPEC-001.md')
    assert 'rfcs.d/RFC-001.md' in from_spec

def test_the_dp_code_spelling_is_found_not_only_the_prose_one(example):
    root = example('rfcs-and-specs')
    source = root / 'record' / 'specs.d' / 'SPEC-001.md'
    assert doc_refs.find_refs('per SPEC-1 exactly', source)
    assert doc_refs.find_refs('per SPEC 1 exactly', source)

def test_a_document_never_links_to_itself(example):
    root = example('rfcs-and-specs')
    spec = root / 'record' / 'specs.d' / 'SPEC-001.md'
    linked, count = doc_refs.linkify(spec.read_text(), spec)
    assert count == 0
    assert linked.count('# SPEC-001:') == 1
