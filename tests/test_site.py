import re
from pathlib import Path
import pytest
from luria import site
from luria.config import current, load
from _scheme import decision

def test_publishes_the_decisions_and_the_generated_views():
    published = {current().rel(p) for p in site.publishable()}
    assert 'record/decisions.d/ADR-025.md' in published
    assert 'docs/decisions/README.md' in published
    assert 'docs/design-principles.md' in published
    assert 'README.md' in published

def test_never_publishes_a_source_that_renders_somewhere_else():
    cfg = current()
    published = {cfg.rel(p) for p in site.publishable()}
    assert not [p for p in published if p.startswith('record/changelog.d/')]
    assert not [p for p in published if p.startswith('record/devlog.d/')]
    assert not [p for p in published if p.startswith('record/principles.d/')]

def test_publishable_is_exactly_the_files_whose_links_resolve_in_place():
    cfg = current()
    for path in site.publishable():
        assert cfg.link_base(path) == path.parent, cfg.rel(path)

def test_excludes_are_honoured():
    cfg = current()
    assert 'template/**' in cfg.site.exclude
    published = {cfg.rel(p) for p in site.publishable()}
    assert not [p for p in published if p.startswith('template/')]
    assert not [p for p in published if p.endswith('_template.md')]

def test_readme_becomes_the_landing_page():
    cfg = current()
    assert site.destination(cfg.root / 'README.md', cfg) == Path('index.md')
    assert site.destination(cfg.root / 'docs' / 'README.md', cfg) == Path('docs/README.md')

def test_site_defaults_derive_from_the_issue_url():
    s = current().site
    assert s.title == 'luria'
    assert s.base_url == 'dmarx.github.io/luria'
    assert s.source_url == 'https://github.com/dmarx/luria/blob/HEAD'

def test_site_defaults_stay_empty_without_a_github_issue_url(project):
    s = load(project).site
    assert s.base_url == ''
    assert s.source_url == ''
    assert s.title == project.name

def test_record_line_carries_status_date_and_lineage():
    meta = {'status': 'Active', 'date': '2026-08-04', 'issue': '#9', 'influenced_by': ['ADR-005', 'ADR-024']}
    line = site.record_line(meta, current().schemes['ADR'].dir / 'ADR-025.md')
    assert line.startswith('> ')
    assert '**Status** Active' in line
    assert '**Filed** 2026-08-04' in line
    assert '[ADR-005](ADR-005.md)' in line
    assert '[ADR-024](ADR-024.md)' in line
    assert '[#9](https://github.com/dmarx/luria/issues/9)' in line

def test_record_line_reads_every_issue_in_the_field():
    line = site.record_line({'issue': '#21, #23'}, current().index)
    assert 'issues/21' in line and 'issues/23' in line

def test_record_line_is_empty_without_frontmatter_facts():
    assert site.record_line({}, current().index) == ''

def test_version_appears_only_when_it_is_not_one():
    where = current().schemes['ADR'].dir / 'ADR-001.md'
    assert '**Version**' not in site.record_line({'version': 1}, where)
    assert '**Version** 2' in site.record_line({'version': 2}, where)

def test_staged_decision_gets_its_code_as_an_alias(tmp_path):
    site.stage(tmp_path)
    staged = (tmp_path / 'content' / 'record' / 'decisions.d' / 'ADR-025.md').read_text()
    assert '\naliases:\n- "ADR-025"\n' in staged
    assert 'status: Active' in staged
    assert '> **Status** Active' in staged

def test_staging_is_idempotent_and_drops_removed_pages(tmp_path):
    site.stage(tmp_path)
    stray = tmp_path / 'content' / 'docs' / 'gone.md'
    stray.write_text('# Gone\n')
    site.stage(tmp_path)
    assert not stray.exists()

def test_a_staging_directory_inside_the_project_is_not_republished(project):
    decision(project, 1, 'Active')
    out = project / 'build' / 'site'
    first = site.stage(out)
    second = site.stage(out)
    assert first.pages == second.pages
    assert not (out / 'content' / 'build').exists()

def test_config_is_written_with_the_project_title(tmp_path):
    site.stage(tmp_path)
    config = (tmp_path / 'quartz.config.ts').read_text()
    assert 'pageTitle: "luria"' in config
    assert 'baseUrl: "dmarx.github.io/luria"' in config
    assert 'markdownLinkResolution: "relative"' in config
    assert '"frontmatter", "filesystem"' in config

def test_links_out_of_the_site_go_to_the_repository(tmp_path):
    report = site.stage(tmp_path)
    index = (tmp_path / 'content' / 'index.md').read_text()
    assert 'https://github.com/dmarx/luria/blob/HEAD/LICENSE' in index
    assert report.to_source > 0
    assert report.unplaced == []

def test_a_quoted_path_is_never_retargeted(tmp_path):
    site.stage(tmp_path)
    text = (tmp_path / 'content' / 'docs' / 'adopting.md').read_text()
    assert '```' in text
    for fence_body in text.split('```')[1::2]:
        assert 'blob/HEAD' not in fence_body

def test_pages_land_at_their_repository_paths(tmp_path):
    site.stage(tmp_path)
    content = tmp_path / 'content'
    assert (content / 'record' / 'decisions.d' / 'ADR-001.md').exists()
    assert (content / 'docs' / 'decisions' / 'README.md').exists()
    assert (content / 'docs' / 'devlog' / '2026-08.md').exists()
    assert not (content / 'README.md').exists()

@pytest.mark.parametrize('target,expected', [('../../record/decisions.d/../../docs/design-principles.md#dp-2', '../../docs/design-principles.md#dp-2'), ('ADR-024.md', 'ADR-024.md'), ('#anchor-only', '#anchor-only')])
def test_index_normalizes_rebased_targets(target, expected):
    from luria.adr_index import _normalize
    assert _normalize(target) == expected

def test_an_unresolvable_influence_is_counted_not_swallowed(project):
    path = decision(project, 1, 'Active')
    path.write_text(path.read_text().replace("date: '2026-01-01'", "date: '2026-01-01'\ninfluenced_by:\n- ADR-919"))
    report = site.stage(project / 'build' / 'site')
    assert any(('ADR-919' in line for line in report.unplaced))

def test_a_superseded_decision_says_so_on_its_page(project):
    decision(project, 1, 'Active')
    decision(project, 2, 'Superseded — by [ADR-001](ADR-001.md)')
    out = project / 'build' / 'site'
    site.stage(out)
    staged = (out / 'content' / 'record' / 'decisions.d' / 'ADR-002.md').read_text()
    assert '> **Status** Superseded — by [ADR-001](ADR-001.md)' in staged

def test_an_html_image_is_staged_beside_its_page(tmp_path):
    report = site.stage(tmp_path)
    banner = tmp_path / 'content' / 'assets' / 'branding' / 'luria-brainslug' / 'luria_project_memory_lockup_horizontal.svg'
    assert banner.exists()
    assert report.assets >= 1

def test_the_landing_page_is_named_and_still_answers_to_README(tmp_path):
    site.stage(tmp_path)
    index = (tmp_path / 'content' / 'index.md').read_text()
    assert index.startswith('---\ntitle: "luria"\n')
    assert 'aliases:\n- "README"' in index

def test_the_graph_sits_above_the_article_not_in_the_sidebar(tmp_path):
    site.stage(tmp_path)
    layout = (tmp_path / 'quartz.layout.ts').read_text()
    before, _, right = layout.partition('right: [')
    assert 'Component.Graph(' in before.split('left: [')[0]
    assert 'Component.Graph(' not in right

def test_the_action_copies_everything_the_staging_writes(tmp_path):
    site.stage(tmp_path)
    staged = {p.name for p in tmp_path.iterdir() if p.name != 'content'}
    action = (current().root / 'actions' / 'site' / 'action.yml').read_text()
    copied = set(re.findall('^\\s*cp\\b[^\\n]*luria-site/([\\w.-]+)', action, re.MULTILINE))
    assert staged, 'nothing staged beside content/ — the guard would be vacuous'
    assert staged <= copied, f'actions/site never copies {staged - copied}'

def test_the_palette_merges_over_the_generators_defaults():
    block = site.colors(current().site)
    assert 'light: "#f4f1e8"' in block
    assert 'fontOrigin' not in block
    for mode in ('lightMode', 'darkMode'):
        assert f'{mode}: {{' in block
    for name in site.THEME_DEFAULTS['light']:
        assert f'{name}: ' in block, f'{name} dropped from the palette'

def test_an_unknown_colour_name_is_refused_by_name():
    from luria.config import Site
    broken = Site(title='t', base_url='', source_url='', theme={'light': {'lightt': '#fff'}})
    with pytest.raises(SystemExit) as caught:
        site.colors(broken)
    assert 'lightt' in str(caught.value)

def test_the_icon_is_staged_as_the_vector_master(tmp_path):
    site.stage(tmp_path)
    assert (tmp_path / 'static' / 'icon.svg').exists()

def test_the_logo_is_baked_once_per_theme(tmp_path):
    site.stage(tmp_path)
    light = (tmp_path / 'static' / 'logo-light.svg').read_text()
    dark = (tmp_path / 'static' / 'logo-dark.svg').read_text()
    assert f'{site.INK_VAR}:#111111' in light
    assert f'{site.INK_VAR}:#f4f1e8' in dark
    scss = (tmp_path / 'custom.scss').read_text()
    assert 'url("static/logo-light.svg")' in scss
    assert '[saved-theme="dark"]' in scss
    assert 'aspect-ratio: 1177.0 / 340.0' in scss

def test_artwork_that_cannot_be_re_inked_is_left_alone():
    plain = '<svg viewBox="0 0 10 5"><path fill="#000" d="M0 0"/></svg>'
    assert site._reinked(plain, '#ffffff') == plain

def test_missing_artwork_is_named_not_skipped(project):
    (project / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.site]\nicon = "nope/icon.svg"\nlogo = "nope/logo.svg"\n')
    from luria import config as config_module
    config_module.reset()
    report = site.stage(project / 'build' / 'site')
    assert any(('icon' in line and 'no such file' in line for line in report.unplaced))
    assert any(('logo' in line for line in report.unplaced))

def test_a_project_with_no_artwork_still_gets_a_stylesheet(project):
    site.stage(project / 'build' / 'site')
    scss = (project / 'build' / 'site' / 'custom.scss').read_text()
    assert scss.startswith('// GENERATED')
    assert '@use "./base.scss";' in scss
    assert '.page-title' not in scss
