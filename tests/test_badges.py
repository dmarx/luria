import sys
from pathlib import Path
from _scheme import decision
from luria import badges, config
REPO = Path(__file__).resolve().parents[1]
TWO_SCHEMES = '[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.schemes.ADR]\ndir = "docs/decisions"\n[luria.schemes.DP]\ndir = "docs/principles"\nrender = "document"\noutput = "docs/design-principles.md"\n'

def principle(root: Path, number: int, status: str, title: str='A value') -> Path:
    path = root / 'docs' / 'principles' / f'DP-{number:03d}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nstatus: {status}\ntitle: {title!r}\ntags:\n- record\ndate: '2026-01-01'\n---\n\n# DP-{number:03d}: {title}\n")
    return path

def with_schemes(project) -> None:
    (project / 'luria.toml').write_text(TWO_SCHEMES)
    config.reset()

def test_a_settled_record_counts_zero(project):
    with_schemes(project)
    decision(project, 1, 'Active')
    assert badges.counts() == (0, 0)

def test_proposed_and_deferred_both_need_a_decision(project):
    with_schemes(project)
    decision(project, 1, 'Proposed')
    decision(project, 2, 'Deferred')
    decision(project, 3, 'Active')
    assert badges.counts()[0] == 2

def test_every_scheme_is_counted(project):
    with_schemes(project)
    decision(project, 1, 'Proposed')
    principle(project, 2, 'Deferred')
    assert badges.counts()[0] == 2

def test_a_retired_document_counts_only_while_cited(project):
    with_schemes(project)
    decision(project, 1, 'Superseded')
    decision(project, 2, 'Active')
    assert badges.counts()[1] == 0
    (project / 'docs' / 'notes.md').write_text('per ADR-001 we do this\n')
    assert badges.counts()[1] == 1

def test_an_acknowledged_citation_does_not_count(project):
    with_schemes(project)
    decision(project, 1, 'Superseded')
    (project / 'docs' / 'notes.md').write_text('<!-- inactive-ok: ADR-001 — deliberate -->\nper ADR-001 we do this\n')
    assert badges.counts()[1] == 0

def test_zero_is_green_and_nonzero_is_amber(project):
    assert badges.GOOD in badges.badge('needs decision', 0, 'x.md')
    assert badges.ATTENTION in badges.badge('needs decision', 3, 'x.md')

def test_rewrite_replaces_only_the_region(project):
    with_schemes(project)
    decision(project, 1, 'Active')
    text = f'# Title\n\n{badges.OPEN}\nstale junk\n{badges.CLOSE}\n\nProse.\n'
    out = badges.rewrite(text)
    assert out.startswith('# Title') and out.endswith('Prose.\n')
    assert 'stale junk' not in out and 'needs%20decision-0' in out

def test_a_project_without_a_region_is_left_alone(project):
    with_schemes(project)
    decision(project, 1, 'Active')
    assert badges.rewrite('# Title\n\nNo region here.\n') == '# Title\n\nNo region here.\n'

def test_rewriting_twice_changes_nothing(project):
    with_schemes(project)
    decision(project, 1, 'Proposed')
    once = badges.rewrite(f'{badges.OPEN}\n{badges.CLOSE}\n')
    assert badges.rewrite(once) == once
