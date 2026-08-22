import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
from luria import lint
from tests import _scheme

def errors_for(project) -> list[str]:
    found: list[str] = []
    lint.check_frontmatter(found)
    return found

def test_agreeing_title_and_heading_pass(project):
    _scheme.decision(project, 1, 'Active', title='A decision')
    assert errors_for(project) == []

def test_a_drifted_heading_is_reported(project):
    path = _scheme.decision(project, 1, 'Active', title='The corrected title')
    path.write_text(path.read_text().replace('# ADR-001: The corrected title', '# ADR-001: The old title'))
    errors = errors_for(project)
    assert len(errors) == 1
    assert 'disagree' in errors[0]
    assert 'The corrected title' in errors[0] and 'The old title' in errors[0]

def test_a_missing_title_is_reported(project):
    path = _scheme.decision(project, 1, 'Active', title='A decision')
    path.write_text(path.read_text().replace("title: 'A decision'\n", ''))
    assert any(('no `title:`' in e for e in errors_for(project)))

def test_a_body_with_no_heading_is_not_a_disagreement(project):
    path = _scheme.decision(project, 1, 'Active', title='A decision')
    path.write_text(path.read_text().replace('# ADR-001: A decision\n', ''))
    assert errors_for(project) == []

def test_the_check_covers_every_scheme(project):
    (project / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.schemes.ADR]\ndir = "docs/decisions"\n[luria.schemes.DP]\ndir = "docs/principles"\nrender = "document"\noutput = "docs/design-principles.md"\n')
    from luria import config
    config.reset()
    path = project / 'docs' / 'principles' / 'DP-001.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\nstatus: Active\ntitle: 'A value'\ntags:\n- record\n---\n\n# DP-001: A different value\n\nBody.\n")
    errors = errors_for(project)
    assert len(errors) == 1 and 'DP-001.md' in errors[0]

def journal_project(project) -> Path:
    (project / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.journals.devlog]\ndir = "devlog.d"\noutput = "docs/devlog"\n')
    from luria import config
    config.reset()
    return project / 'devlog.d'

def entry(root: Path, at: str, created: str | None='same', title: str='An entry') -> Path:
    path = root / f'{at}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = at.replace('/', '')
    iso = f'{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[8:10]}:{stamp[10:12]}:{stamp[12:14]}' if created == 'same' else created
    front = [f'title: {title!r}'] if title else []
    if iso is not None:
        front.append(f"created: '{iso}'")
    path.write_text('---\n' + '\n'.join(front) + '\n---\n\nBody.\n')
    return path

def journal_errors(project) -> list[str]:
    found: list[str] = []
    lint.check_journals(found)
    return found

def test_an_entry_at_its_own_timestamp_passes(project):
    entry(journal_project(project), '2026/08/03/211926')
    assert journal_errors(project) == []

def test_a_moved_entry_is_reported(project):
    root = journal_project(project)
    entry(root, '2026/08/03/211926', created='2026-08-04T03:27:11')
    errors = journal_errors(project)
    assert len(errors) == 1
    assert 'devlog.d/2026/08/04/032711.md' in errors[0]

def test_an_entry_with_no_created_is_reported(project):
    entry(journal_project(project), '2026/08/03/211926', created=None)
    errors = journal_errors(project)
    assert any(('no `created:`' in e for e in errors))
    assert any(('`luria index` populates it from the path' in e for e in errors))

def test_an_entry_no_witness_can_date_is_reported_as_such(project):
    root = journal_project(project)
    path = root / 'notes.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\ntitle: 'Loose notes'\n---\n\nBody.\n")
    errors = journal_errors(project)
    assert any(("the path doesn't imply one" in e for e in errors))

def test_an_untitled_entry_is_reported(project):
    entry(journal_project(project), '2026/08/03/211926', title='')
    assert any(('no `title:`' in e for e in journal_errors(project)))

def test_the_template_is_exempt(project):
    root = journal_project(project)
    root.mkdir(parents=True, exist_ok=True)
    (root / '_template.md').write_text("---\ntitle: 'Shape'\n---\n\nShape.\n")
    assert journal_errors(project) == []

def version_errors(project) -> list[str]:
    found: list[str] = []
    lint.check_version_history(found)
    return found

def versioned(project, version: int, history: str='') -> Path:
    path = _scheme.decision(project, 1, 'Active', title='A decision')
    path.write_text(path.read_text().replace('status: Active\n', f'status: Active\nversion: {version}\n{history}'))
    return path

def test_version_one_needs_no_history(project):
    versioned(project, 1)
    assert version_errors(project) == []

def test_a_bumped_version_with_no_history_is_reported(project):
    versioned(project, 2)
    assert any(('no `history:`' in e for e in version_errors(project)))

def test_history_that_agrees_passes(project):
    versioned(project, 2, "history:\n- version: 2\n  changed: 'Reworded.'\n")
    assert version_errors(project) == []

def test_history_that_lags_the_version_is_reported(project):
    versioned(project, 3, "history:\n- version: 2\n  changed: 'Reworded.'\n")
    errors = version_errors(project)
    assert len(errors) == 1 and 'ends at version 2' in errors[0]

def generated_errors(project) -> list[str]:
    found: list[str] = []
    lint.check_generated_index(found)
    return found

def test_a_hand_written_file_in_a_view_dir_is_a_violation(project):
    from luria import config
    (project / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.schemes.ADR]\ndir = "record/decisions.d"\noutput = "docs/decisions"\n')
    config.reset()
    from tests import _scheme
    _scheme.decision(project, 1, 'Active')
    from luria import adr_index as builder
    for path, text in builder.outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    assert generated_errors(project) == []
    (project / 'docs' / 'decisions' / 'notes.md').write_text('# Stray\n')
    errors = generated_errors(project)
    assert len(errors) == 1
    assert 'notes.md' in errors[0] and 'generator' in errors[0]

def dial_project(project, fail_on: str='') -> None:
    _scheme.decision(project, 12, 'Superseded')
    page = project / 'docs' / 'notes.md'
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text('Still leaning on ADR-012 here.\n')
    (project / 'luria.toml').write_text(f'[luria]\nissue_url = "https://example.test/issues/{{n}}"\n[luria.lint]\nfail_on = [{fail_on}]\n')
    from luria import config
    config.reset()

def dial_errors(capsys) -> tuple[list[str], str]:
    found: list[str] = []
    lint.report_warnings(found)
    return (found, capsys.readouterr().err)

def test_the_default_posture_is_warn_only(project, capsys):
    dial_project(project)
    errors, err = dial_errors(capsys)
    assert errors == []
    assert 'retired documents cited unacknowledged' in err

def test_a_promoted_class_fails_instead_of_printing(project, capsys):
    dial_project(project, '"retired-citations"')
    errors, err = dial_errors(capsys)
    assert any(('failing: `fail_on`' in e for e in errors))
    assert any(('ADR-012' in e for e in errors)), 'the detail rows come along'
    assert 'retired documents cited unacknowledged' not in err, 'promoted, not duplicated'

def test_every_emitted_class_is_nameable_in_the_dial(project, capsys):
    dial_project(project, '"legacy-spellings"')
    errors, _ = dial_errors(capsys)
    assert not any(('is no warning class' in e for e in errors)), errors

def test_an_acknowledged_row_never_fails(project, capsys):
    dial_project(project, '"retired-citations"')
    page = project / 'docs' / 'notes.md'
    page.write_text('<!-- inactive-ok: ADR-012 — quoted deliberately -->\nStill leaning on ADR-012 here.\n')
    errors, _ = dial_errors(capsys)
    assert errors == []

def test_a_wrong_notch_is_an_error(project, capsys):
    dial_project(project, '"retired-refs"')
    errors, _ = dial_errors(capsys)
    assert any(('no warning class' in e and 'retired-citations' in e for e in errors))

def test_pending_documents_can_be_promoted(project, capsys):
    _scheme.decision(project, 2, 'Proposed')
    (project / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.lint]\nfail_on = ["pending-documents"]\n')
    from luria import config
    config.reset()
    errors, _ = dial_errors(capsys)
    assert any(('undecided document(s)' in e and 'failing' in e for e in errors))
