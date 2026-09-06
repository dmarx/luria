"""A scheme's form, checked against the scheme's contract (#169).

`_template.md` is exempt from every document check, correctly: its codes are
placeholders and its status is a prompt, so linting it as a document reports
findings about a form nobody filed.

But that exemption made it the only file in the record that states the schema
and is never compared to it — and it is the file every document is a copy of.
A drift between `luria.toml` and the template does not produce one wrong
document; it produces every subsequent document, in the wrong shape, with the
lint reporting each of them as fine, because each of them is.

Shape only. Values stay placeholders.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import config, templates


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def project(tmp_path, monkeypatch, sota_extra: str = "") -> Path:
    write(tmp_path, "luria.toml", f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"

[luria.schemes.LIT]
dir = "record/literature.d"

[luria.schemes.SOTA]
dir = "record/practices.d"
{sota_extra}
""")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def template(root: Path, scheme_dir: str, *fields: str) -> Path:
    front = ["---", "status: Proposed", "title: The thing you should do",
             "tags:", "- record", "date: '2026-01-01'", *fields, "---", "",
             "# SOTA-NNN: The thing you should do", "", "Body."]
    return write(root, f"{scheme_dir}/_template.md", "\n".join(front) + "\n")


PLURAL = ('[luria.schemes.SOTA.references]\n'
          'source = { scheme = "LIT", required = true, many = true }')
SCALAR = ('[luria.schemes.SOTA.references]\n'
          'source = { scheme = "LIT", required = true }')


def test_a_scalar_scaffold_for_a_plural_field_is_a_finding(tmp_path, monkeypatch):
    """The anthology case: `many = true` was decided, the form kept saying
    one, and 140 of 144 practices were filed single-sourced."""
    root = project(tmp_path, monkeypatch, PLURAL)
    template(root, "record/practices.d", "source: LIT-000")
    rows = templates.rows()
    assert len(rows) == 1, rows
    assert "source" in rows[0] and "many" in rows[0]
    assert "_template.md" in rows[0]


def test_a_list_scaffold_for_a_plural_field_is_clean(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, PLURAL)
    template(root, "record/practices.d", "source:\n- LIT-000")
    assert templates.rows() == []


def test_a_scalar_scaffold_for_a_scalar_field_is_clean(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, SCALAR)
    template(root, "record/practices.d", "source: LIT-000")
    assert templates.rows() == []


def test_a_list_scaffold_for_a_scalar_field_is_a_finding(tmp_path, monkeypatch):
    """The mirror image, and the one #141 made a finding on documents: a list
    in a scalar field was stringified and half-read."""
    root = project(tmp_path, monkeypatch, SCALAR)
    template(root, "record/practices.d", "source:\n- LIT-000")
    rows = templates.rows()
    assert len(rows) == 1, rows
    assert "one value" in rows[0]


def test_a_required_field_missing_from_the_form_is_a_finding(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, PLURAL)
    template(root, "record/practices.d")
    rows = templates.rows()
    assert len(rows) == 1, rows
    assert "not scaffolded" in rows[0]


def test_an_optional_field_missing_from_the_form_is_clean(tmp_path, monkeypatch):
    """A form prompts for what is required; an optional field is the
    author's to add, and demanding it in the template would make every
    document carry an empty key."""
    root = project(tmp_path, monkeypatch,
                   '[luria.schemes.SOTA.references]\n'
                   'source = { scheme = "LIT", required = false, many = true }')
    template(root, "record/practices.d")
    assert templates.rows() == []


def test_an_optional_field_present_in_the_wrong_shape_is_still_a_finding(
        tmp_path, monkeypatch):
    """Absent is the author's choice; present-and-wrong is copied into every
    document."""
    root = project(tmp_path, monkeypatch,
                   '[luria.schemes.SOTA.references]\n'
                   'source = { scheme = "LIT", required = false, many = true }')
    template(root, "record/practices.d", "source: LIT-000")
    assert len(templates.rows()) == 1


def test_a_field_the_contract_does_not_know_is_clean(tmp_path, monkeypatch):
    """Templates carry optional fields and comments, and should."""
    root = project(tmp_path, monkeypatch, PLURAL)
    template(root, "record/practices.d", "source:\n- LIT-000",
             "implementations: []")
    assert templates.rows() == []


def test_placeholder_values_are_never_checked(tmp_path, monkeypatch):
    """`LIT-000` resolves to nothing and that is the point of a form."""
    root = project(tmp_path, monkeypatch, PLURAL)
    template(root, "record/practices.d", "source:\n- LIT-999999")
    assert templates.rows() == []


def test_a_scheme_with_no_template_is_clean(tmp_path, monkeypatch):
    """Every scheme predating templates, and every scheme that wants none."""
    project(tmp_path, monkeypatch, PLURAL)
    assert templates.rows() == []


def test_a_template_with_no_frontmatter_is_clean(tmp_path, monkeypatch):
    """Reported by the docs checks already; not this check's finding to
    duplicate."""
    root = project(tmp_path, monkeypatch, PLURAL)
    write(root, "record/practices.d/_template.md", "# A form\n\nBody.\n")
    assert templates.rows() == []


def test_the_finding_cites_the_declaration(tmp_path, monkeypatch):
    """DP-4: a finding says where the obligation was declared, so the reader
    is sent to the key and not just told the rule."""
    root = project(tmp_path, monkeypatch, PLURAL)
    template(root, "record/practices.d", "source: LIT-000")
    assert "schemes.SOTA.references.source" in templates.rows()[0]


def test_a_commented_out_field_does_not_count_as_scaffolded(
        tmp_path, monkeypatch):
    """A form that explains a field in a comment has not prompted for it."""
    root = project(tmp_path, monkeypatch, PLURAL)
    template(root, "record/practices.d", "# source: LIT-000")
    rows = templates.rows()
    assert len(rows) == 1 and "not scaffolded" in rows[0]


def test_this_repos_own_templates_agree_with_its_contracts():
    """Fired on the real record, which is the only place it can be wrong in
    a way a fixture cannot show."""
    assert templates.rows() == []


def test_the_class_is_promotable_and_wired(tmp_path, monkeypatch):
    """A class reported by `status_sections` but absent from FAILABLE tells a
    project asking to enforce it that the class does not exist (test_lint's
    `legacy-spellings` regression, kept from recurring)."""
    from luria import lint
    assert "template-drift" in lint.FAILABLE
    root = project(tmp_path, monkeypatch, PLURAL)
    template(root, "record/practices.d", "source: LIT-000")
    assert "template-drift" in {n for n, _, _ in lint.status_sections()}


def test_a_form_that_agrees_reports_nothing(tmp_path, monkeypatch):
    from luria import lint
    root = project(tmp_path, monkeypatch, PLURAL)
    template(root, "record/practices.d", "source:\n- LIT-000")
    assert "template-drift" not in {n for n, _, _ in lint.status_sections()}


def test_a_conditionally_required_field_is_demanded_at_the_forms_own_status(
        tmp_path, monkeypatch):
    """The form scaffolds `status: Proposed`, and a proposed entry in this
    scheme must say what would settle it — so the form has to prompt for it
    (#170 meeting #169)."""
    root = project(tmp_path, monkeypatch,
                   '[luria.schemes.SOTA.fields.promote_when]\n'
                   'required_when = { status = ["Proposed"] }\n')
    template(root, "record/practices.d")
    rows = templates.rows()
    assert len(rows) == 1 and "promote_when" in rows[0]


def test_it_is_not_demanded_when_the_form_starts_elsewhere(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   '[luria.schemes.SOTA.fields.promote_when]\n'
                   'required_when = { status = ["Deferred"] }\n')
    template(root, "record/practices.d")
    assert templates.rows() == []
