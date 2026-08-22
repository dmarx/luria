import re
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
from luria import adr_index as builder
from luria import doc_refs
from luria.config import Scheme
rebase = builder.rebase_links

def test_relative_targets_are_rebased():
    assert rebase('see [ADR-404](adr-404-x.md)', '../') == 'see [ADR-404](../adr-404-x.md)'
    assert rebase('see [dp](../design-principles.md#13-a)', '../') == 'see [dp](../../design-principles.md#13-a)'

def test_absolute_and_anchor_targets_are_left_alone():
    for target in ('https://github.com/dmarx/strata-g/issues/551', 'mailto:x@y.z', '/docs/x.md', '#a-heading'):
        text = f'see [x]({target})'
        assert rebase(text, '../') == text

def test_no_prefix_is_a_no_op():
    text = 'see [ADR-404](adr-404-x.md) and [#1](https://example.com/1)'
    assert rebase(text, '') == text

def test_row_rebases_summary_and_status_together(tmp_path, monkeypatch):
    from luria import config
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    config.reset()
    adr_dir = config.current().schemes['ADR'].dir
    adr_dir.mkdir(parents=True)
    (adr_dir / 'ADR-001.md').write_text("---\nstatus: 'Superseded — by [ADR-002](ADR-002.md)'\ntags:\n- record\nsummary: 'refines [ADR-002](ADR-002.md)'\n---\n\n# ADR-001: Old\n")
    adr = builder.load_adrs()[0]
    assert '](ADR-002.md)' in adr.row()
    row = adr.row('../')
    assert '](../ADR-002.md)' in row
    assert row.count('](ADR-002.md)') == 0
    config.reset()

def test_every_generated_relative_link_resolves():
    broken = []
    for path, text in builder.outputs().items():
        quoted = doc_refs.code_spans(text)
        for m in builder.RELATIVE_LINK_RE.finditer(text):
            if doc_refs.in_html_block(m.start(), quoted):
                continue
            file = m.group(1).split('#')[0]
            if file and (not (path.parent / file).resolve().exists()):
                broken.append(f'{path.name} -> {m.group(1)}')
    assert broken == []

def principle(root: Path, number: int, title: str, body: str='Body.', **front) -> Path:
    path = root / 'docs' / 'principles' / f'DP-{number:03d}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ['status: Active', f'title: {title!r}', 'tags:', '- record']
    lines += [f'{k}: {v}' for k, v in front.items()]
    path.write_text('---\n' + '\n'.join(lines) + f'\n---\n\n# DP-{number:03d}: {title}\n\n{body}\n')
    return path
DP_SCHEME_ARGS = dict(active='Active', render='document')

def dp_scheme(root: Path) -> Scheme:
    return Scheme('DP', root / 'docs' / 'principles', output=root / 'docs' / 'design-principles.md', **DP_SCHEME_ARGS)

def render(root: Path) -> str:
    scheme = dp_scheme(root)
    return builder.render_document(scheme, builder.load_scheme(scheme))

def test_document_demotes_the_heading_and_renumbers(project):
    principle(project, 3, 'Fire before trusting')
    out = render(project)
    assert '## 3. Fire before trusting' in out
    assert '# DP-003' not in out

def test_document_emits_a_stable_anchor(project):
    principle(project, 3, 'Fire before trusting')
    assert '<a name="dp-3"></a>' in render(project)

def test_document_strips_the_frontmatter(project):
    principle(project, 1, 'A value', **{'version': 2})
    out = render(project)
    assert 'status: Active' not in out and 'tags:' not in out

def test_metadata_line_carries_version_and_origin(project):
    principle(project, 1, 'A value', **{'version': 2, 'origin': "'An incident.'"})
    assert '*v2 · origin: An incident*' in render(project)

def test_a_retired_principle_says_so(project):
    path = principle(project, 1, 'A value')
    path.write_text(path.read_text().replace('status: Active', 'status: Rejected'))
    assert '**Rejected**' in render(project)

def test_influenced_by_renders_as_a_followable_backlink(project):
    import os
    from luria.config import current
    from tests import _scheme
    _scheme.decision(project, 4, 'Active')
    principle(project, 1, 'A value', influenced_by='[ADR-004]')
    target = os.path.relpath(current().schemes['ADR'].dir / 'ADR-004.md', current().design_principles.parent)
    assert f'[ADR-004]({target})' in render(project)

def test_an_unresolvable_backlink_stays_a_bare_code(project):
    principle(project, 1, 'A value', influenced_by='[ADR-404]')
    out = render(project)
    assert 'shaped by ADR-404' in out and '](' not in out.split('shaped by')[1]

def test_outputs_covers_every_scheme(project, monkeypatch):
    from tests import _scheme
    _scheme.decision(project, 1, 'Active')
    principle(project, 1, 'A value')
    (project / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.schemes.ADR]\ndir = "docs/decisions"\n[luria.schemes.DP]\ndir = "docs/principles"\nrender = "document"\noutput = "docs/design-principles.md"\n')
    from luria import config
    config.reset()
    out = builder.outputs()
    assert project / 'docs' / 'design-principles.md' in out
    assert project / 'docs' / 'decisions' / 'README.md' in out

def test_filename_is_the_code(project):
    scheme = builder.current().schemes['ADR']
    assert scheme.filename(13) == 'ADR-013.md'
    assert scheme.filename('4') == 'ADR-004.md'

def test_a_legacy_slug_filename_is_still_read(project):
    from tests import _scheme
    path = _scheme.decision(project, 10, 'Active')
    path.rename(path.parent / 'adr-010-some-old-title.md')
    assert set(builder.current().schemes['ADR'].documents()) == {10}

def test_a_readme_is_not_a_document(project):
    from tests import _scheme
    _scheme.decision(project, 1, 'Active')
    decisions = project / 'docs' / 'decisions'
    (decisions / 'README.md').write_text('# Index\n')
    (decisions / '_template.md').write_text('---\nstatus: Proposed\n---\n')
    assert set(builder.current().schemes['ADR'].documents()) == {1}

def test_title_frontmatter_wins_over_the_heading(project):
    from tests import _scheme
    path = _scheme.decision(project, 1, 'Active', title='The real title')
    path.write_text(path.read_text().replace('# ADR-001: The real title', '# ADR-001: A stale heading'))
    assert builder.load_adrs()[0].title == 'The real title'

def test_the_heading_is_the_fallback(project):
    from tests import _scheme
    path = _scheme.decision(project, 1, 'Active', title='From the heading')
    path.write_text(path.read_text().replace("title: 'From the heading'\n", ''))
    assert builder.load_adrs()[0].title == 'From the heading'

def test_prefix_for_collocated_scheme_is_empty():
    s = Scheme('ADR', REPO / 'x')
    assert builder.prefix_for(s, s.view) == ''

def test_split_scheme_rows_link_into_the_source_tree(project, monkeypatch):
    from luria import config
    (project / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.schemes.ADR]\ndir = "record/decisions.d"\noutput = "docs/decisions"\n')
    config.reset()
    from tests import _scheme
    _scheme.decision(project, 1, 'Active', summary='see [ADR-002](ADR-002.md)')
    _scheme.decision(project, 2, 'Active')
    rendered = builder.outputs()
    index = rendered[project / 'docs' / 'decisions' / 'README.md']
    assert '[ADR-001](../../record/decisions.d/ADR-001.md)' in index
    assert 'see [ADR-002](../../record/decisions.d/ADR-002.md)' in index
    tag = rendered[project / 'docs' / 'decisions' / 'tags' / 'record.md']
    assert '[ADR-001](../../../record/decisions.d/ADR-001.md)' in tag

def test_stub_lives_with_the_sources_and_renders_in_the_view(project):
    from luria import config
    (project / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.schemes.ADR]\ndir = "record/decisions.d"\noutput = "docs/decisions"\n')
    config.reset()
    from tests import _scheme
    _scheme.decision(project, 1, 'Active')
    stub = project / 'record' / 'decisions.d' / 'README.stub'
    stub.write_text('# Mine\n\nProse.\n\n{categories}\n\n{table}\n')
    index = builder.outputs()[project / 'docs' / 'decisions' / 'README.md']
    assert index.startswith('# Mine')

def test_orphans_reports_strays_in_every_view_dir(project):
    from luria import config
    (project / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.schemes.ADR]\ndir = "record/decisions.d"\noutput = "docs/decisions"\n[luria.journals.devlog]\ndir = "record/devlog.d"\noutput = "docs/devlog"\n')
    config.reset()
    from tests import _scheme
    _scheme.decision(project, 1, 'Active')
    rendered = builder.outputs()
    for path, text in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    assert builder.orphans(rendered) == []
    stray = project / 'docs' / 'decisions' / 'notes.md'
    stray.write_text('# Handwritten\n')
    assert builder.orphans(rendered) == [stray]

def test_a_collocated_view_dir_is_not_policed(project):
    from luria import config
    (project / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.schemes.ADR]\ndir = "docs/decisions"\n')
    config.reset()
    from tests import _scheme
    _scheme.decision(project, 1, 'Active')
    rendered = builder.outputs()
    for path, text in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    assert builder.orphans(rendered) == []

def test_a_pipe_in_a_summary_stays_one_cell(tmp_path, monkeypatch):
    from luria import config
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    config.reset()
    adr_dir = config.current().schemes['ADR'].dir
    adr_dir.mkdir(parents=True)
    (adr_dir / 'ADR-001.md').write_text("---\nstatus: Active\ntags:\n- record\nsummary: 'a closed vocabulary (Active | Proposed | Rejected)'\n---\n\n# ADR-001: Vocab\n")
    row = builder.load_adrs()[0].row()
    assert re.findall('(?<!\\\\)\\|', row) == ['|'] * 5
    assert '(Active \\| Proposed \\| Rejected)' in row
    config.reset()

def test_a_hand_escaped_pipe_is_not_double_escaped(tmp_path, monkeypatch):
    from luria import config
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    config.reset()
    adr_dir = config.current().schemes['ADR'].dir
    adr_dir.mkdir(parents=True)
    (adr_dir / 'ADR-001.md').write_text("---\nstatus: Active\ntags:\n- record\nsummary: 'data is {subject: node\\|selection}'\n---\n\n# ADR-001: Macro\n")
    row = builder.load_adrs()[0].row()
    assert 'node\\|selection' in row
    assert '\\\\|' not in row
    config.reset()

def test_title_and_summary_are_separate_columns(tmp_path, monkeypatch):
    from luria import config
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    config.reset()
    adr_dir = config.current().schemes['ADR'].dir
    adr_dir.mkdir(parents=True)
    (adr_dir / 'ADR-001.md').write_text("---\nstatus: Active\ntags:\n- record\ntitle: 'The choice'\nsummary: 'Why, and what lost.'\n---\n\n# ADR-001: The choice\n")
    (adr_dir / 'ADR-002.md').write_text("---\nstatus: Active\ntags:\n- record\ntitle: 'Terse one'\n---\n\n# ADR-002: Terse one\n")
    with_summary, without = (a.row() for a in builder.load_adrs())
    assert '| The choice | Why, and what lost. |' in with_summary
    assert '| Terse one |  |' in without, 'no summary → an empty cell, not the title twice'
    assert builder.TABLE_HEAD.startswith('| # | Title | Summary | Status |')
    config.reset()

def _rfc_project(tmp_path, monkeypatch):
    from luria import config
    (tmp_path / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/{n}"\n[luria.schemes.RFC]\ndir = "record/rfcs.d"\noutput = "docs/rfcs"\nactive = "Active"\nrender = "index"\n')
    d = tmp_path / 'record' / 'rfcs.d'
    d.mkdir(parents=True)
    (d / 'RFC-001.md').write_text("---\nstatus: Active\ntitle: 'A proposal'\nversion: 1\ntags:\n- network\ndate: '2026-01-01'\n---\n\n# RFC-001: A proposal\n")
    (d / 'tags.yaml').write_text('network:\n  label: Network\n  blurb: routing and transport. HTTP and gRPC both live here\n')
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    config.reset()
    return config.current().schemes['RFC']

def test_tag_page_names_its_own_scheme_not_decisions(tmp_path, monkeypatch):
    scheme = _rfc_project(tmp_path, monkeypatch)
    docs = builder.load_scheme(scheme)
    page = builder.render_tag_page('network', {'label': 'Network'}, docs, scheme)
    assert '# RFCs tagged `network`' in page
    assert 'ADRs tagged' not in page
    assert '1 of 1 RFC documents.' in page
    assert 'decisions.' not in page

def test_tag_page_blurb_keeps_its_casing(tmp_path, monkeypatch):
    scheme = _rfc_project(tmp_path, monkeypatch)
    docs = builder.load_scheme(scheme)
    meta = {'label': 'Network', 'blurb': 'routing and transport. HTTP and gRPC both live here'}
    page = builder.render_tag_page('network', meta, docs, scheme)
    assert 'Routing and transport. HTTP and gRPC both live here.' in page
    assert 'http and grpc' not in page
