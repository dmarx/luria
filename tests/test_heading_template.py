# tests/test_heading_template.py
"""A scheme can say how its documents' H1 is written (#405, part 2).

`heading:` is a template over `{code}` and `{title}`, defaulting to
`{code}: {title}`, today's form. `luria new` derives the H1 from it, so a
record that drops the code from its headings scaffolds `# Title`, which the
lint accepts since part 1. Anything else that rewrites the H1 (a title given
on the command line, a body handed over whole) finds it in either form."""
from _config import merged

import pytest

from luria import config
from luria import new as new_mod
from luria.config import current

TEMPLATE = ("---\nstatus: Proposed\ntitle: 'A placeholder'\ntags:\n- record\n"
            "date: '2026-01-01'\n---\n\n# ADR-NNN: A placeholder\n\nBody.\n")


def _heading(project, template: str | None) -> None:
    path = project / "luria.yaml"
    if template is not None:
        path.write_text(merged(path.read_text(),
                               {"schemes": {"ADR": {"heading": template}}}))
    config.reset()
    scheme = current().schemes["ADR"]
    scheme.dir.mkdir(parents=True, exist_ok=True)
    (scheme.dir / "_template.md").write_text(TEMPLATE)


def test_the_default_heading_keeps_the_code(project):
    _heading(project, None)
    assert current().schemes["ADR"].heading == "{code}: {title}"
    text = new_mod.new_entry("adr", {"title": "A thing"}, None).read_text()
    assert "\n# ADR-001: A thing\n" in text


def test_a_bare_heading_template_scaffolds_the_title_alone(project):
    _heading(project, "{title}")
    text = new_mod.new_entry("adr", {"title": "A thing"}, None).read_text()
    assert "\n# A thing\n" in text
    assert "# ADR-001" not in text


def test_the_heading_follows_the_template_without_a_title_flag(project):
    _heading(project, "{title}")
    text = new_mod.new_entry("adr", {}, None).read_text()
    assert "\n# A placeholder\n" in text
    assert "ADR-NNN" not in text


def test_a_body_replaces_the_prose_under_a_bare_heading(project):
    _heading(project, "{title}")
    text = new_mod.new_entry("adr", {"title": "A thing", "body": "New prose."},
                             None).read_text()
    assert "\n# A thing\n\nNew prose.\n" in text
    assert "Body." not in text


@pytest.mark.parametrize("bad", ["{code}", "Untitled", "{title} {name}"])
def test_a_heading_template_without_the_title_or_with_strangers_is_refused(
        project, bad):
    path = project / "luria.yaml"
    path.write_text(merged(path.read_text(),
                           {"schemes": {"ADR": {"heading": bad}}}))
    config.reset()
    with pytest.raises(ValueError, match="heading"):
        current()


def test_a_bare_scaffold_passes_the_title_check(project):
    """Parts 1 and 2 together: what `luria new` scaffolds under a bare
    heading template is what the lint accepts."""
    from luria import adr_index, lint
    _heading(project, "{title}")
    path = new_mod.new_entry("adr", {"title": "GPT-4: a thing"}, None)
    meta, body = adr_index.parse_frontmatter(path.read_text())
    errors: list[str] = []
    lint.check_title(errors, str(path), meta, body)
    assert errors == []
