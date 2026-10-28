# tests/test_views.py
"""A view may be a Jinja template over the record (ADR-130).

<!-- unresolved-ok-block: CLAIM-001 — fixture codes, not this record's -->
The fixture record is two claims and a vocabulary; each test writes the
template it needs and renders it the way `luria index` does.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from _config import merged
from luria import adr_index, config, doc_refs, views


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


BASE = """
issue_url: https://example.test/issues/{n}
vocabularies:
  topics:
    label: Topics
    terms:
      alpha: {label: Alpha, blurb: the first}
      beta: {label: Beta, blurb: the second}
  voices:
    terms:
      thesis: {blurb: the record's own}
      objection: {blurb: against it}
schemes:
  CLAIM:
    dir: record/claims.d
    output: docs/claims
    axis: tags
    fields:
      tags:
        vocabulary: topics
        many: true
      role:
        vocabulary: voices
        default: thesis
      warrant:
        required_when: {status: [Active]}
    references:
      rests_on:
        scheme: CLAIM
        many: true
        required: false
"""

VIEW = """
views:
  boot:
    template: record/views.d/BOOT.md.j2
    output: BOOT.md
"""

CLAIM_1 = """---
status: Active
title: 'Constraints bind conduct'
version: 1
tags:
- alpha
date: '2026-01-01'
warrant: interpretive
rests_on:
- CLAIM-002
summary: Rests on [CLAIM-002](CLAIM-002.md).
---

# CLAIM-001: Constraints bind conduct

Intro paragraph, citing [CLAIM-002](CLAIM-002.md).

## The inference

From the case to the rule.

### A detail

Still part of the inference.

## Critical questions

Not for the reader.
"""

CLAIM_2 = """---
status: Proposed
status_note: pending a second case
title: 'Authority is separate'
version: 2
tags:
- beta
- alpha
date: '2026-01-02'
role: objection
---

# CLAIM-002: Authority is separate

Body two.
"""


@pytest.fixture
def record(tmp_path, monkeypatch):
    write(tmp_path, "luria.yaml", merged(BASE, VIEW))
    write(tmp_path, "record/claims.d/CLAIM-001.md", CLAIM_1)
    write(tmp_path, "record/claims.d/CLAIM-002.md", CLAIM_2)
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    adr_index.forget_documents()
    yield tmp_path
    config.reset()


def render(root: Path, template: str, output: str = "BOOT.md") -> str:
    write(root, "record/views.d/BOOT.md.j2", template)
    out = views.outputs()
    return out[root / output]


def body_of(text: str) -> str:
    """The rendered text without the generated stamp."""
    return text.split("\n", 2)[2] if text.startswith("<!--") else text


# --- config ---------------------------------------------------------------

def test_a_declared_view_is_loaded(record):
    view = config.current().views["boot"]
    assert view.template == record / "record/views.d/BOOT.md.j2"
    assert view.output == record / "BOOT.md"


@pytest.mark.parametrize("spec, missing", [
    ("views:\n  boot:\n    output: BOOT.md\n", "template"),
    ("views:\n  boot:\n    template: record/views.d/BOOT.md.j2\n", "output"),
])
def test_a_view_must_name_its_template_and_output(tmp_path, monkeypatch,
                                                  spec, missing):
    write(tmp_path, "luria.yaml", merged(BASE, spec))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    with pytest.raises(ValueError, match=f"views.boot.*{missing}"):
        config.current()


def test_a_view_cannot_render_over_its_own_template(tmp_path, monkeypatch):
    write(tmp_path, "luria.yaml", merged(BASE, """
views:
  boot:
    template: BOOT.md
    output: BOOT.md
"""))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    with pytest.raises(ValueError, match="views.boot"):
        config.current()


# --- the context ------------------------------------------------------------

def test_any_frontmatter_field_is_an_attribute(record):
    text = render(record, "{% set c = doc('CLAIM-002') %}"
                          "{{ c.code }}|{{ c.title }}|{{ c.version }}|"
                          "{{ c.date }}|{{ c.tags | join(',') }}\n")
    assert body_of(text) == "[CLAIM-002](record/claims.d/CLAIM-002.md)|" \
        "Authority is separate|2|2026-01-02|beta,alpha\n"


def test_a_field_is_read_as_the_contract_reads_it(record):
    # A status carrying a note is that status; a vocabulary field left
    # unwritten is its default.
    text = render(record, "{{ doc('CLAIM-002').status }}|"
                          "{{ doc('CLAIM-002').role }}|"
                          "{{ doc('CLAIM-001').role }}\n")
    assert body_of(text) == "Proposed|objection|thesis\n"


def test_a_declared_field_left_unwritten_is_empty(record):
    text = render(record, "[{{ doc('CLAIM-002').warrant }}]"
                          "[{{ doc('CLAIM-002').rests_on | length }}]\n")
    assert body_of(text) == "[None][0]\n"


def test_a_reference_field_holds_documents(record):
    text = render(record, "{% set c = doc('CLAIM-001') %}"
                          "{{ c.rests_on[0].title }} — "
                          "{{ c.rests_on | join(', ') }}\n")
    assert body_of(text) == ("Authority is separate — "
                             "[CLAIM-002](record/claims.d/CLAIM-002.md)\n")


def test_a_field_the_scheme_does_not_have_is_undefined(record):
    with pytest.raises(views.ViewError,
                       match=r"CLAIM-002 has no field 'nonesuch'.*warrant"):
        render(record, "{{ doc('CLAIM-002').nonesuch }}\n")


def test_an_undefined_field_still_takes_a_default(record):
    text = render(record, "{{ doc('CLAIM-002').nonesuch | default('-') }}|"
                          "{{ doc('CLAIM-002').nonesuch is defined }}\n")
    assert body_of(text) == "-|False\n"


def test_item_access_reads_the_same_fields(record):
    text = render(record, "{{ doc('CLAIM-002')['role'] }}\n")
    assert body_of(text) == "objection\n"


def test_prose_fields_are_rebased(record):
    text = body_of(render(record, "{{ doc('CLAIM-002').status_note }}|"
                                  "{{ doc('CLAIM-001').summary }}\n"))
    assert text == ("pending a second case|Rests on "
                    "[CLAIM-002](record/claims.d/CLAIM-002.md).\n")


def test_body_drops_the_title_heading(record):
    text = body_of(render(record, "{{ doc('CLAIM-002').body }}\n"))
    assert "# CLAIM-002" not in text
    assert text.strip() == "Body two."


def test_part_is_one_section_with_its_subsections(record):
    text = body_of(render(record,
                          "{{ doc('CLAIM-001').part('The inference') }}\n"))
    assert "From the case to the rule." in text
    assert "### A detail" in text
    assert "Still part of the inference." in text
    assert "Critical questions" not in text
    assert "## The inference" not in text


def test_a_missing_part_is_a_render_error(record):
    with pytest.raises(views.ViewError, match="No such part"):
        render(record, "{{ doc('CLAIM-001').part('Nope') }}\n")


def test_docs_filters_on_frontmatter_in_code_order(record):
    titles = "| map(attribute='title') | join(';') }}"
    text = render(record, "{{ docs('CLAIM') " + titles + "\n"
                          "{{ docs('CLAIM', status='Active') " + titles + "\n"
                          "{{ docs('CLAIM', tags='alpha') " + titles + "\n")
    assert body_of(text).splitlines() == [
        "Constraints bind conduct;Authority is separate",
        "Constraints bind conduct",
        "Constraints bind conduct;Authority is separate",
    ]


def test_docs_filters_as_the_contract_reads(record):
    titles = "| map(attribute='code') | join(';') }}"
    text = render(record, "{{ docs('CLAIM', status='Proposed') " + titles
                          + "|{{ docs('CLAIM', role='thesis') " + titles
                          + "|{{ docs('CLAIM', rests_on='CLAIM-002') "
                          + titles + "\n")
    assert body_of(text) == ("[CLAIM-002](record/claims.d/CLAIM-002.md)|"
                             "[CLAIM-001](record/claims.d/CLAIM-001.md)|"
                             "[CLAIM-001](record/claims.d/CLAIM-001.md)\n")


def test_docs_in_force_reads_the_schemes_own_word(record):
    codes = "| map(attribute='code') | join(';') }}"
    text = render(record, "{{ docs('CLAIM', in_force=true) " + codes + "|"
                          "{{ docs('CLAIM', in_force=false) " + codes + "\n")
    assert body_of(text) == ("[CLAIM-001](record/claims.d/CLAIM-001.md)|"
                             "[CLAIM-002](record/claims.d/CLAIM-002.md)\n")


def test_in_force_follows_a_scheme_that_names_another_word(tmp_path,
                                                           monkeypatch):
    write(tmp_path, "luria.yaml", merged(BASE, VIEW, """
schemes:
  CLAIM:
    active: Proposed
"""))
    write(tmp_path, "record/claims.d/CLAIM-001.md", CLAIM_1)
    write(tmp_path, "record/claims.d/CLAIM-002.md", CLAIM_2)
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    text = render(tmp_path, "{{ docs('CLAIM', in_force=true) "
                            "| map(attribute='title') | join(';') }}\n")
    assert body_of(text) == "Authority is separate\n"


def test_in_force_combines_with_field_filters(record):
    text = render(record, "{{ docs('CLAIM', in_force=true, tags='beta') "
                          "| length }}\n")
    assert body_of(text) == "0\n"


def test_docs_refuses_an_unknown_scheme(record):
    with pytest.raises(views.ViewError, match="NOPE"):
        render(record, "{{ docs('NOPE') }}\n")


def test_vocabulary_keeps_declared_order_label_and_blurb(record):
    text = render(record, "{% for t in vocabulary('topics') %}"
                          "{{ t.value }}={{ t.label }}: {{ t.blurb }}\n"
                          "{% endfor %}")
    assert body_of(text) == "alpha=Alpha: the first\nbeta=Beta: the second\n"


def test_an_unknown_vocabulary_is_a_render_error(record):
    with pytest.raises(views.ViewError, match="nope"):
        render(record, "{{ vocabulary('nope') }}\n")


def test_schemes_name_where_each_scheme_is_filed(record):
    text = render(record, "{% for s in schemes() %}"
                          "{{ s.prefix }} in `{{ s.dir }}` to "
                          "`{{ s.output }}`\n{% endfor %}")
    assert body_of(text) == "CLAIM in `record/claims.d` to `docs/claims`\n"


def test_journals_name_where_each_journal_is_filed(tmp_path, monkeypatch):
    write(tmp_path, "luria.yaml", merged(BASE, VIEW, """
journals:
  workbench:
    dir: record/workbench.d
    output: docs/workbench
    title: Workbench
"""))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    text = render(tmp_path, "{% for j in journals() %}{{ j.title }} in "
                            "`{{ j.dir }}`\n{% endfor %}")
    assert body_of(text) == "Workbench in `record/workbench.d`\n"


# --- links ------------------------------------------------------------------

def test_a_bare_code_in_the_template_is_linked_from_the_output(record):
    text = render(record, "See CLAIM-002.\n")
    assert body_of(text) == "See [CLAIM-002](record/claims.d/CLAIM-002.md).\n"


def test_transcluded_links_are_rebased_to_the_outputs_frame(record):
    text = body_of(render(record, "{{ doc('CLAIM-001').body }}\n"
                                  "{{ doc('CLAIM-001').summary }}\n"))
    assert "[CLAIM-002](record/claims.d/CLAIM-002.md)" in text
    assert "](CLAIM-002.md)" not in text


def test_links_follow_an_output_in_another_directory(tmp_path, monkeypatch):
    write(tmp_path, "luria.yaml", merged(BASE, """
views:
  guide:
    template: record/views.d/BOOT.md.j2
    output: docs/guide/claims.md
"""))
    write(tmp_path, "record/claims.d/CLAIM-001.md", CLAIM_1)
    write(tmp_path, "record/claims.d/CLAIM-002.md", CLAIM_2)
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    text = body_of(render(tmp_path, "CLAIM-002 and {{ doc('CLAIM-001').body }}",
                          output="docs/guide/claims.md"))
    assert text.startswith(
        "[CLAIM-002](../../record/claims.d/CLAIM-002.md) and")
    assert "Intro paragraph, citing " \
        "[CLAIM-002](../../record/claims.d/CLAIM-002.md)." in text


# --- the environment --------------------------------------------------------

def test_templates_compose_with_include(record):
    write(record, "record/views.d/prose.md", "Hand-written prose.\n")
    text = render(record, "{% include 'record/views.d/prose.md' %}"
                          "Then CLAIM-001.\n")
    assert body_of(text) == ("Hand-written prose.\n"
                             "Then [CLAIM-001](record/claims.d/CLAIM-001.md).\n")


def test_an_undefined_name_is_an_error_naming_the_template_line(record):
    with pytest.raises(views.ViewError,
                       match=r"record/views\.d/BOOT\.md\.j2:2"):
        render(record, "fine\n{{ doc('CLAIM-001').nonesuch }}\n")


def test_an_unknown_code_is_a_render_error(record):
    with pytest.raises(views.ViewError, match="CLAIM-009"):
        render(record, "{{ doc('CLAIM-009').title }}\n")


def test_a_syntax_error_names_the_template(record):
    with pytest.raises(views.ViewError, match=r"BOOT\.md\.j2:1"):
        render(record, "{% for %}\n")


def test_the_sandbox_refuses_reaching_python_internals(record):
    with pytest.raises(views.ViewError):
        render(record, "{{ ''.__class__.__mro__ }}\n")


def test_no_clock_is_reachable(record):
    with pytest.raises(views.ViewError):
        render(record, "{{ now() }}\n")


# --- the output -------------------------------------------------------------

def test_a_markdown_output_is_stamped_with_its_template(record):
    text = render(record, "Hello.\n")
    first = text.splitlines()[0]
    assert "GENERATED" in first and "luria index" in first
    assert "record/views.d/BOOT.md.j2" in first


def test_a_non_markdown_output_is_not_stamped(tmp_path, monkeypatch):
    write(tmp_path, "luria.yaml", merged(BASE, """
views:
  plain:
    template: record/views.d/BOOT.md.j2
    output: out.txt
"""))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    assert render(tmp_path, "Hello.\n", output="out.txt") == "Hello.\n"


def test_views_render_with_every_other_view(record):
    write(record, "record/views.d/BOOT.md.j2", "Hello.\n")
    assert record / "BOOT.md" in adr_index.outputs()


def test_index_check_reports_a_stale_view(record):
    write(record, "record/views.d/BOOT.md.j2", "Hello.\n")
    adr_index.run()
    assert "Hello." in (record / "BOOT.md").read_text(encoding="utf-8")
    assert record / "BOOT.md" not in adr_index.staleness().stale
    write(record, "record/views.d/BOOT.md.j2", "Changed.\n")
    assert record / "BOOT.md" in adr_index.staleness().stale


def test_the_lint_renders_a_working_view_once(record, monkeypatch):
    write(record, "record/views.d/BOOT.md.j2", "Hello.\n")
    rendered = views.outputs()
    monkeypatch.setattr(views, "render",
                        lambda view: pytest.fail("rendered again"))
    assert views.errors(rendered) == []


def test_errors_collects_every_broken_view(record):
    write(record, "record/views.d/BOOT.md.j2", "{{ doc('CLAIM-009') }}\n")
    found = views.errors()
    assert len(found) == 1 and "CLAIM-009" in found[0]
    # …and the rest of the views still render, so the lint can go on.
    assert record / "BOOT.md" not in views.outputs(skip_broken=True)


def test_the_fixer_never_scans_a_template(record):
    write(record, "record/views.d/BOOT.md.j2", "{{ doc('CLAIM-001') }}\n")
    assert record / "record/views.d/BOOT.md.j2" not in doc_refs.doc_files()
