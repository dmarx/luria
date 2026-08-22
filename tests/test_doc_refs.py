import os
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
from luria import doc_refs
DOCS = REPO / 'docs'
ANY_MD = DOCS / 'project-memory.md'
ISSUE_551 = doc_refs.current().issue_url.format(n=551)
DECISIONS = os.path.relpath(doc_refs.current().schemes['ADR'].dir, DOCS)
ROOT_DECISIONS = os.path.relpath(doc_refs.current().schemes['ADR'].dir, REPO)

def kinds(text):
    return [(r.prefix.lower() if r.kind == 'scheme' else r.kind, r.num) for r in doc_refs.find_refs(text)]

def test_finds_each_kind():
    text = 'See ADR-004, design-principles #13 and issue #551.'
    assert kinds(text) == [('adr', 4), ('dp', 13), ('issue', 551)]

def test_design_principle_wins_over_issue():
    assert kinds('per design-principles #13') == [('dp', 13)]
    assert kinds('per design principle #13') == [('dp', 13)]
    assert kinds('per design-principles **#13**') == [('dp', 13)]

def test_bare_principle_is_a_principle():
    assert kinds('the key-check shape principle #4 forbids') == [('dp', 4)]

def test_principle_run_carries_the_label():
    assert kinds('**Design principles #17 and #18**: both hosts') == [('dp', 17), ('dp', 18)]

def test_bold_marker_is_not_stolen_from_the_run():
    out, _ = doc_refs.linkify('**Design principles #17 and #18**: both', ANY_MD)
    assert out.endswith('**: both') and '#18**]' not in out

def test_spaced_adr_and_bold():
    assert kinds('see ADR 004') == [('adr', 4)]
    assert kinds('**ADR-004** landed') == [('adr', 4)]

def test_hex_colour_is_not_an_issue():
    assert kinds('the swatch is #1a2b3c') == []
    assert kinds('the swatch is #123456') == []

def test_heading_hash_is_not_an_issue():
    assert kinds('# Title\n\n## 2. Another') == []

def test_low_numbers_need_a_cue_to_be_issues():
    resolved = lambda t: [r for r in doc_refs.find_refs(t) if doc_refs.resolve(r, ANY_MD, {}, doc_refs.dp_anchors(), t)]
    assert [r.num for r in resolved('Saved layer query presets (issue #10)')] == [10]
    assert [r.num for r in resolved('resolves #120, #6 and #7')] == [120, 6, 7]
    assert resolved('cover story #1 fully') == []
    assert resolved('ADR-163 open question #3') == []
    assert [r.num for r in resolved('the #445 rewrite')] == [445]

def test_code_is_ignored():
    assert kinds('`ADR-004` and `#551`') == []
    assert kinds('```\nADR-004 #551\n```\n') == []
    assert kinds('~~~py\nADR-004\n~~~\n') == []

def test_stray_backtick_does_not_poison_the_rest_of_the_file():
    text = '```\nan ` unbalanced tick inside a fence\n```\n\nA stray ` in this paragraph.\n\nThen `#123` stays code and ADR-004 is a live reference.\n'
    assert kinds(text) == [('adr', 4)]

def test_unexempt_puts_a_code_block_back_under_the_lint(tmp_path):
    text = 'prose ADR-004\n\n<!-- unexempt: codeblock -->\n```python\n# implements ADR-004\ndef f(): ...\n```\n\n```python\n# but ADR-004 here stays exempt\n```\n'
    lines = [r.line for r in doc_refs.find_refs(text, ANY_MD)]
    assert lines == [1, 5]

def test_unexempt_needs_block_scope_across_a_blank_line():
    body = '<!-- unexempt{}: codeblock -->\n\n```python\n# ADR-004\n```\n'
    assert doc_refs.find_refs(body.format(''), ANY_MD) == []
    assert [r.line for r in doc_refs.find_refs(body.format('-block'), ANY_MD)] == [4]

def test_unexempt_is_off_by_default(tmp_path):
    text = '```python\n# implements ADR-004\n```\n'
    assert doc_refs.find_refs(text, ANY_MD) == []

def test_unexempt_reports_an_unknown_region():
    text = '<!-- unexempt: sidebar -->\n\n```\nADR-004\n```\n'
    problems = doc_refs.directive_problems(ANY_MD, text)
    assert problems and 'unknown argument' in problems[0]
    assert 'codeblock' in problems[0]

def test_existing_links_are_ignored():
    assert kinds('[ADR-004](decisions/ADR-004.md)') == []
    assert kinds('[#551](https://github.com/dmarx/strata-g/issues/551)') == []
    assert kinds('see [the index ADR](ADR-004.md)') == []

def test_defined_shortcut_reference_is_already_a_link():
    text = 'the registry ([ADR-919]) turned it around.\n\n[ADR-919]: ADR-919.md\n'
    assert kinds(text) == []

def test_undefined_shortcut_reference_is_bare():
    assert kinds('the registry ([ADR-919]) turned it around.') == [('adr', 919)]

def test_frontmatter_data_is_exempt_but_the_summary_is_not():
    text = "---\nstatus: Superseded — by ADR-001\nissue: '#551'\nsummary: 'refines ADR-001 (issue #551)'\n---\n\nBody.\n"
    assert kinds(text) == [('adr', 1), ('issue', 551)]
    start = text.index('summary:')
    assert all((r.start > start for r in doc_refs.find_refs(text)))

def test_summary_rewrite_is_verified_against_the_yaml():
    text = "---\nstatus: Active\nsummary: 'refines ADR-001'\n---\n\nBody.\n"
    out, n = doc_refs.linkify(text, doc_refs.adr_paths()[4])
    assert n == 1
    meta, _ = doc_refs.parse_frontmatter(out)
    assert meta['status'] == 'Active'
    assert meta['summary'] == 'refines [ADR-001](ADR-001.md)'

def test_unsurvivable_summary_rewrite_is_dropped_by_both_sides():
    text = "---\nstatus: Active\nsummary: 'refines ADR-001'\n---\n\nBody.\n"
    adrs, anchors = (doc_refs.adr_paths(), doc_refs.dp_anchors())
    original = doc_refs._frontmatter_survives
    doc_refs._frontmatter_survives = lambda old, new: False
    try:
        assert doc_refs.rewritable_refs(text, adrs[4], adrs, anchors) == []
        assert doc_refs.linkify(text, adrs[4])[1] == 0
    finally:
        doc_refs._frontmatter_survives = original

def test_html_attributes_and_anchors_are_ignored():
    assert kinds('<img alt="fixes #551" src="x.png">') == []
    assert kinds('<a href="x.md">ADR-004</a>') == []

def test_urls_and_comments_are_ignored():
    assert kinds(ISSUE_551 + '#issuecomment-1') == []
    assert kinds('<!-- ADR-004, #551 -->') == []

def test_linkify_uses_repo_conventions():
    out, n = doc_refs.linkify('See ADR-004 and #551.', ANY_MD)
    assert n == 2
    assert f'[ADR-004]({DECISIONS}/ADR-004.md)' in out
    assert f'[#551]({ISSUE_551})' in out

def test_linkify_is_idempotent():
    once, _ = doc_refs.linkify('See ADR-004 and #551.', ANY_MD)
    twice, n = doc_refs.linkify(once, ANY_MD)
    assert n == 0 and twice == once

def test_html_block_gets_an_html_anchor():
    text = '<table>\n<tr><td>Fields editor (#551)</td></tr>\n</table>\n'
    out, n = doc_refs.linkify(text, REPO / 'README.md')
    assert n == 1
    assert f'<a href="{ISSUE_551}">#551</a>' in out
    assert '[#551]' not in out

def test_undefined_shortcut_brackets_are_absorbed():
    out, _ = doc_refs.linkify('as in [ADR-004] above', ANY_MD)
    assert out == f'as in [ADR-004]({DECISIONS}/ADR-004.md) above'

def test_self_reference_is_not_linked():
    adr = doc_refs.adr_paths()[4]
    _, n = doc_refs.linkify('# ADR-004: the index is generated', adr)
    assert n == 0

def test_fragment_links_resolve_from_the_collected_file():
    fragment_dir = next(iter(doc_refs.current().fragments))
    out, _ = doc_refs.linkify('See ADR-004.', REPO / fragment_dir / 'x.md')
    assert f'({ROOT_DECISIONS}/ADR-004.md)' in out

def test_journal_entry_links_resolve_from_its_book():
    journal = next(iter(doc_refs.current().journals.values()))
    entry = journal.dir / '2026' / '08' / '03' / '211926.md'
    out, _ = doc_refs.linkify('See ADR-004.', entry)
    want = os.path.relpath(doc_refs.current().schemes['ADR'].dir, journal.output)
    assert f'({want}/ADR-004.md)' in out

def test_design_principle_links_to_its_anchor():
    out, _ = doc_refs.linkify('per design-principles #1', ANY_MD)
    assert '(design-principles.md#dp-1)' in out

def test_design_principles_page_links_to_its_own_anchor():
    out, _ = doc_refs.linkify('per design-principles #1', doc_refs.current().design_principles)
    assert '[design-principles #1](#dp-1)' in out

def test_explicit_anchor_beats_the_heading_slug(project):
    (project / 'docs' / 'design-principles.md').write_text('<a name="dp-4"></a>\n\n## 4. Fire before trusting\n')
    assert doc_refs.dp_anchors() == {4: 'dp-4'}

def test_heading_slug_is_the_fallback(project):
    (project / 'docs' / 'design-principles.md').write_text('## 4. Fire before trusting\n')
    assert doc_refs.dp_anchors() == {4: '4-fire-before-trusting'}

def test_repo_docs_have_no_bare_references():
    adrs, anchors = (doc_refs.adr_paths(), doc_refs.dp_anchors())
    bare = []
    for path in doc_refs.doc_files():
        text = path.read_text()
        bare += [f'{path.relative_to(REPO)}:{r.line}: {r.describe()}' for r in doc_refs.rewritable_refs(text, path, adrs, anchors)]
    assert bare == []

def test_fixer_links_a_uid_remote_reference(tmp_path, monkeypatch):
    from luria import config
    (tmp_path / 'docs').mkdir(parents=True)
    (tmp_path / 'luria.toml').write_text('[luria]\nissue_url = ""\n[luria.remotes.ARXIV]\nuid = "\\\\d{4}[.]\\\\d{4,5}"\nurl = "https://arxiv.org/abs/{uid}"\n')
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    config.reset()
    out, n = doc_refs.linkify('see ARXIV-2403.05530 for the details', tmp_path / 'docs' / 'notes.md')
    assert n == 1
    assert '[ARXIV-2403.05530](https://arxiv.org/abs/2403.05530)' in out
    config.reset()
