import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
from _scheme import decision
from luria import config, doc_refs, lint

def project_with(project, extra: str=''):
    (project / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n' + extra)
    config.reset()
    return project

def expand(project, text, name='notes.md'):
    return doc_refs.linkify(text, project / 'docs' / name)

def test_local_code_expands(project):
    project_with(project)
    decision(project, 4, 'Active')
    out, n = expand(project, 'see [[ADR-004]] for why')
    assert n == 1
    assert '[ADR-004](' in out and 'ADR-004.md)' in out and ('[[' not in out)

def test_label_becomes_the_link_text(project):
    project_with(project)
    decision(project, 4, 'Active')
    out, _ = expand(project, 'see [[ADR-004|the index decision]]')
    assert '[the index decision](' in out and '[[' not in out

def test_document_scheme_code_expands_to_an_anchor(project):
    project_with(project, '[luria.schemes.DP]\ndir = "docs/principles"\nrender = "document"\noutput = "docs/design-principles.md"\n[luria.schemes.ADR]\ndir = "docs/decisions"\n')
    out, n = expand(project, 'per [[DP-3]] this holds')
    assert n == 1
    assert '[DP-3](design-principles.md#dp-3)' in out

def test_remote_code_expands_to_a_url(project):
    project_with(project, '[luria.remotes.UP]\nrepo = "o/r"\n')
    out, n = expand(project, 'compare [[UP-ADR-032]]')
    assert n == 1
    assert '[UP-ADR-032](https://github.com/o/r/blob/main/' in out

def test_uid_remote_expands_through_its_template(project):
    project_with(project, '[luria.remotes.ARXIV]\nuid = "\\\\d{4}[.]\\\\d{4,5}"\nurl = "https://arxiv.org/abs/{uid}"\n')
    out, n = expand(project, 'the model card ([[ARXIV-2403.05530]])')
    assert n == 1
    assert '[ARXIV-2403.05530](https://arxiv.org/abs/2403.05530)' in out

def test_a_low_issue_number_needs_no_cue_inside_brackets(project):
    project_with(project)
    out, n = expand(project, 'fixed by [[#10]]')
    assert n == 1
    assert '[#10](https://example.test/issues/10)' in out

def test_quoted_wikilinks_are_specimens(project):
    project_with(project)
    decision(project, 4, 'Active')
    out, n = expand(project, 'type `[[ADR-004]]` to force a link')
    assert n == 0 and '`[[ADR-004]]`' in out

def test_unresolvable_wikilinks_stay_put(project):
    project_with(project)
    out, n = expand(project, 'see [[FAKE-001]]')
    assert n == 0 and '[[FAKE-001]]' in out

def test_expansion_is_idempotent(project):
    project_with(project)
    decision(project, 4, 'Active')
    once, _ = expand(project, 'see [[ADR-004]].')
    twice, n = expand(project, once)
    assert twice == once and n == 0

def test_the_inner_code_is_not_also_a_bare_reference(project):
    project_with(project)
    decision(project, 4, 'Active')
    refs = doc_refs.find_refs('see [[ADR-004]]', project / 'docs' / 'n.md')
    assert refs == []

def wikilink_errors(project) -> list[str]:
    found: list[str] = []
    lint.check_wikilinks(found)
    return found

def test_a_resolvable_wikilink_names_the_fixer(project):
    project_with(project)
    decision(project, 4, 'Active')
    (project / 'docs' / 'notes.md').write_text('see [[ADR-004]]\n')
    errors = wikilink_errors(project)
    assert len(errors) == 1 and 'luria link --fix' in errors[0]

def test_an_unresolvable_wikilink_is_its_own_error(project):
    project_with(project)
    (project / 'docs' / 'notes.md').write_text('see [[FAKE-001]]\n')
    errors = wikilink_errors(project)
    assert len(errors) == 1
    assert 'resolves to nothing' in errors[0] and 'FAKE-001' in errors[0]
