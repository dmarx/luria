import json
import sys
from pathlib import Path
from _scheme import decision
from luria import config, doc_refs, ref_status, remotes
REPO = Path(__file__).resolve().parents[1]
REMOTE_TOML = '[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.remotes.UP]\nname = "upstream"\nrepo = "o/r"\n'

def with_remote(project, extra: str='') -> Path:
    (project / 'luria.toml').write_text(REMOTE_TOML + extra)
    config.reset()
    return project

def lockfile(project, entries: dict[str, str]) -> None:
    (project / 'remotes.lock.json').write_text(json.dumps({'remotes': {'UP': entries}}))

def test_code_only_convention_is_the_default(project):
    with_remote(project)
    assert remotes.resolve('UP', 'ADR-32') == 'https://github.com/o/r/blob/main/record/decisions.d/ADR-032.md'

def test_a_discovered_filename_wins(project):
    with_remote(project)
    lockfile(project, {'ADR-032': 'adr-032-changelog-ci-collection.md'})
    assert remotes.resolve('UP', 'ADR-032').endswith('/adr-032-changelog-ci-collection.md')

def test_discovery_is_authoritative_once_done(project):
    with_remote(project)
    lockfile(project, {'ADR-032': 'adr-032-x.md'})
    assert remotes.resolve('UP', 'ADR-999') == ''

def test_no_lockfile_means_fall_back_rather_than_refuse(project):
    with_remote(project)
    assert remotes.resolve('UP', 'ADR-999').endswith('/ADR-999.md')

def test_an_explicit_template_overrides_everything(project):
    with_remote(project, 'url = "https://x.test/{code}"\n')
    lockfile(project, {'ADR-032': 'ignored.md'})
    assert remotes.resolve('UP', 'ADR-032') == 'https://x.test/ADR-032'

def test_an_unregistered_prefix_is_not_a_namespace(project):
    with_remote(project)
    assert remotes.resolve('MY', 'ADR-004') == ''

def test_the_finder_claims_the_whole_composed_span(project):
    with_remote(project)
    refs = doc_refs.find_refs('see UP-ADR-032 for that')
    assert [(r.kind, r.remote, r.code) for r in refs] == [('remote', 'UP', 'ADR-032')]

def test_a_local_code_still_reads_as_local(project):
    with_remote(project)
    refs = doc_refs.find_refs('see ADR-032 for that')
    assert [(r.kind, r.prefix) for r in refs] == [('scheme', 'ADR')]

def test_the_fixer_writes_a_url_not_a_relative_path(project):
    with_remote(project)
    lockfile(project, {'ADR-032': 'adr-032-x.md'})
    out, n = doc_refs.linkify('see UP-ADR-032', project / 'docs' / 'page.md')
    assert n == 1
    assert out == 'see [UP-ADR-032](https://github.com/o/r/blob/main/record/decisions.d/adr-032-x.md)'

def test_an_unresolvable_foreign_code_is_not_linked(project):
    with_remote(project)
    lockfile(project, {'ADR-032': 'adr-032-x.md'})
    _, n = doc_refs.linkify('see UP-ADR-999', project / 'docs' / 'page.md')
    assert n == 0

def test_the_citation_scan_does_not_read_a_local_code_out_of_it(project):
    decision(project, 12, 'Superseded', 'The replaced one')
    with_remote(project)
    (project / 'notes.md').write_text('per UP-ADR-012 upstream\n')
    docs = ref_status.load_docs()
    result = ref_status.scan([project / 'notes.md'], docs)
    assert result.cited == {}

def test_an_unresolvable_foreign_code_is_reported(project):
    decision(project, 1, 'Active')
    with_remote(project)
    lockfile(project, {'ADR-032': 'adr-032-x.md'})
    (project / 'notes.md').write_text('per UP-ADR-999 upstream\n')
    result = ref_status.scan([project / 'notes.md'], ref_status.load_docs())
    assert [c.line for c in result.dangling['UP-ADR-999']] == [1]

def test_the_annotation_validator_reads_the_composed_code(project):
    decision(project, 12, 'Active', 'A local decision')
    with_remote(project)
    lockfile(project, {'ADR-032': 'adr-032-x.md'})
    (project / 'notes.md').write_text('<!-- unresolved-ok: UP-ADR-999 — upstream, not here -->\nUP-ADR-999\n')
    docs = ref_status.load_docs()
    result = ref_status.scan([project / 'notes.md'], docs)
    assert ref_status.dangling(result, docs) == []
    assert ref_status.stale_annotations(result, docs) == []

def test_discovery_reads_both_filename_conventions(tmp_path):
    found = remotes._from_names(['adr-032-changelog-ci.md', 'ADR-004.md', 'README.md', 'tags.yaml'])
    assert found == {'ADR-032': 'adr-032-changelog-ci.md', 'ADR-004': 'ADR-004.md'}

def test_the_remotes_own_config_says_where_its_documents_live():
    assert remotes._upstream_dir('[luria.schemes.ADR]\ndir = "records"\n', 'docs/decisions') == 'records'

def test_an_unparseable_upstream_config_leaves_the_default_standing():
    assert remotes._upstream_dir('!! not toml', 'docs/decisions') == 'docs/decisions'
    assert remotes._upstream_dir('', 'docs/decisions') == 'docs/decisions'

def test_discovery_says_why_it_found_nothing(project):
    (project / 'luria.toml').write_text('[luria]\nissue_url = ""\n[luria.remotes.UP]\nname = "upstream"\n')
    config.reset()
    found, how = remotes.discover(config.current().remotes['UP'])
    assert found == {} and 'no `repo` configured' in how

def hand(project, body: str, name: str='notes.md'):
    page = project / name
    page.write_text(body)
    return remotes.hand_links([page])

def test_hand_written_url_is_reported(project):
    with_remote(project)
    flagged, stale = hand(project, '[UP-ADR-032](https://example.test/elsewhere.md)\n')
    assert len(flagged) == 1
    assert 'UP-ADR-032' in flagged[0] and 'hand-written' in flagged[0]
    assert 'record/decisions.d/ADR-032.md' in flagged[0]
    assert stale == []

def test_constructed_url_is_not_reported(project):
    with_remote(project)
    flagged, _ = hand(project, '[UP-ADR-032](https://github.com/o/r/blob/main/record/decisions.d/ADR-032.md)\n')
    assert flagged == []

def test_url_ok_acknowledges_the_link(project):
    with_remote(project)
    flagged, stale = hand(project, '<!-- url-ok-block: UP-ADR-032 — their principles are one document -->\n\n[UP-ADR-032](https://example.test/elsewhere.md#anchor)\n')
    assert flagged == [] and stale == []

def test_url_ok_matches_unpadded_codes(project):
    with_remote(project)
    flagged, stale = hand(project, '[UP-ADR-32](https://example.test/x.md) <!-- url-ok: UP-ADR-032 — deliberate -->\n')
    assert flagged == [] and stale == []

def test_unused_url_ok_is_stale(project):
    with_remote(project)
    _, stale = hand(project, '<!-- url-ok: UP-ADR-032 — nothing here -->\n')
    assert len(stale) == 1 and 'acknowledges no hand-written link' in stale[0]

def test_url_ok_on_a_constructed_link_is_stale(project):
    with_remote(project)
    _, stale = hand(project, '<!-- url-ok: UP-ADR-032 — was hand-written once -->\n[UP-ADR-032](https://github.com/o/r/blob/main/record/decisions.d/ADR-032.md)\n')
    assert len(stale) == 1

def test_a_quoted_hand_link_is_a_specimen_not_a_citation(project):
    with_remote(project)
    flagged, _ = hand(project, 'quoting `[UP-ADR-032](https://x.test/y.md)` here\n')
    assert flagged == []
SCHEMED = '[luria.remotes.UP.schemes.DP]\ndocument = "docs/design-principles.md"\n[luria.remotes.UP.schemes.RFC]\ndir = "docs/rfcs"\n'

def test_document_scheme_constructs_a_file_anchor(project):
    with_remote(project, SCHEMED)
    assert remotes.resolve('UP', 'DP-18') == 'https://github.com/o/r/blob/main/docs/design-principles.md#dp-18'

def test_anchor_defaults_to_the_stable_anchor_shape(project):
    with_remote(project, SCHEMED)
    assert remotes.resolve('UP', 'DP-9').endswith('#dp-9')

def test_anchor_template_is_configurable(project):
    with_remote(project, '[luria.remotes.UP.schemes.DP]\ndocument = "PRINCIPLES.md"\nanchor = "principle-{number}"\n')
    assert remotes.resolve('UP', 'DP-4').endswith('PRINCIPLES.md#principle-4')

def test_scheme_dir_scopes_the_file_convention(project):
    with_remote(project, SCHEMED + '\n')
    assert remotes.resolve('UP', 'RFC-7') == 'https://github.com/o/r/blob/main/docs/rfcs/RFC-007.md'
    assert 'record/decisions.d/ADR-001.md' in remotes.resolve('UP', 'ADR-1')

def test_scheme_url_template_wins(project):
    with_remote(project, '[luria.remotes.UP.schemes.DP]\nurl = "https://up.example/values/{number}"\n')
    assert remotes.resolve('UP', 'DP-3') == 'https://up.example/values/3'

def test_lockfile_authority_does_not_cover_document_schemes(project):
    with_remote(project, SCHEMED)
    lockfile(project, {'ADR-032': 'adr-032-changelog-ci-collection.md'})
    assert remotes.resolve('UP', 'DP-18').endswith('#dp-18')
    assert remotes.resolve('UP', 'ADR-999') == ''

def test_url_ok_retires_when_the_construction_catches_up(project):
    with_remote(project, SCHEMED)
    flagged, stale = hand(project, '<!-- url-ok: UP-DP-18 — was unconstructible before ADR-023 -->\n[UP-DP-18](https://github.com/o/r/blob/main/docs/design-principles.md#dp-18)\n')
    assert flagged == []
    assert len(stale) == 1
ARXIV = '[luria.remotes.ARXIV]\nuid = "(\\\\d{4})[.:](\\\\d{4,5})"\nurl = "https://arxiv.org/abs/{1}.{2}"\n'

def test_uid_remote_constructs_through_the_template(project):
    with_remote(project, ARXIV)
    assert remotes.resolve('ARXIV', '2403.05530') == 'https://arxiv.org/abs/2403.05530'

def test_uid_capture_groups_index_the_template_by_position(project):
    with_remote(project, ARXIV)
    assert remotes.resolve('ARXIV', '1234:5678') == 'https://arxiv.org/abs/1234.5678'

def test_uid_is_exact_never_normalised(project):
    with_remote(project, ARXIV)
    remote = config.current().remotes['ARXIV']
    assert remote.canon('2403.05530') == '2403.05530'

def test_the_delimiter_is_configurable(project):
    with_remote(project, '[luria.remotes.JIRA]\ndelim = ":"\nuid = "[A-Z]+-\\\\d+"\nurl = "https://example.atlassian.net/browse/{uid}"\n')
    text = 'tracked as JIRA:PROJ-42 upstream'
    refs = remotes.references(text)
    assert [r.composed for r in refs] == ['JIRA:PROJ-42']
    assert remotes.link(refs[0].remote, refs[0].tail).endswith('/browse/PROJ-42')

def test_unconfigured_prefixes_do_not_match(project):
    with_remote(project, ARXIV)
    assert remotes.references('see FAKE-1234.5678 here') == []

def test_uid_remote_without_a_template_constructs_nothing(project):
    with_remote(project, '[luria.remotes.ARXIV]\nuid = "\\\\d{4}[.]\\\\d{4,5}"\n')
    assert remotes.resolve('ARXIV', '2403.05530') == ''

def test_lockfile_never_vetoes_a_uid_remote(project):
    with_remote(project, ARXIV)
    lockfile(project, {'ADR-032': 'x.md'})
    assert remotes.resolve('ARXIV', '2403.05530').endswith('/abs/2403.05530')

def test_scheme_shaped_references_still_scan_beside_uid_remotes(project):
    with_remote(project, ARXIV)
    text = 'per UP-ADR-032 and ARXIV-2403.05530'
    assert [r.composed for r in remotes.references(text)] == ['UP-ADR-032', 'ARXIV-2403.05530']

def test_url_ok_covers_uid_remotes_too(project):
    with_remote(project, ARXIV)
    flagged, stale = hand(project, '[ARXIV-2403.05530](https://arxiv.org/pdf/2403.05530v2)\n')
    assert len(flagged) == 1 and 'ARXIV-2403.05530' in flagged[0]
    flagged, stale = hand(project, '<!-- url-ok: ARXIV-2403.05530 — the v2 PDF specifically -->\n[ARXIV-2403.05530](https://arxiv.org/pdf/2403.05530v2)\n')
    assert flagged == [] and stale == []

def test_fixture_prefix_resolves_to_the_convention_note():
    url = remotes.resolve('FX', 'ADR-032')
    assert url.endswith('docs/directives.md#fixture-codes')
    assert remotes.resolve('FX', 'DP-9').endswith('#fixture-codes')
