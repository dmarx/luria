"""HTML comments and duplicate keys in YAML frontmatter (#164).

PyYAML's default loader accepts both; Quartz rejects them. The check has
to look at the raw fence, not the parsed dict.
"""
from luria import lint
from tests import _scheme


def errors_for(project) -> list[str]:
    found: list[str] = []
    lint.check_frontmatter(found)
    return found


def test_html_comment_in_frontmatter_is_reported(project):
    """PyYAML accepts `<!-- ... -->` as a mapping key; Quartz does not."""
    path = _scheme.decision(project, 1, "Active", title="A decision")
    text = path.read_text()
    path.write_text(text.replace(
        "title: 'A decision'\n",
        "title: 'A decision'\n<!-- inactive-ok: LIT-141 — predecessor -->\n"))
    errors = errors_for(project)
    assert any("HTML comment in YAML frontmatter" in e for e in errors), errors


def test_hash_comment_in_frontmatter_is_clean(project):
    """The intended spelling after #163: a YAML `#` comment is not a key."""
    path = _scheme.decision(project, 1, "Active", title="A decision")
    text = path.read_text()
    path.write_text(text.replace(
        "title: 'A decision'\n",
        "title: 'A decision'\n# inactive-ok: LIT-141 — predecessor\n"))
    assert errors_for(project) == []


def test_duplicate_frontmatter_key_is_reported(project):
    """PyYAML keeps the last value; a strict loader rejects the file."""
    path = _scheme.decision(project, 1, "Active", title="A decision")
    text = path.read_text()
    path.write_text(text.replace(
        "title: 'A decision'\n",
        "title: 'A decision'\nsource: LIT-141\nsource: LIT-142\n"))
    errors = errors_for(project)
    assert any("duplicate frontmatter key 'source'" in e for e in errors), errors


def test_indented_html_comment_in_folded_scalar_is_clean(project):
    """An indented `<!--` is content, not a mapping key."""
    path = _scheme.decision(project, 1, "Active", title="A decision")
    text = path.read_text()
    path.write_text(text.replace(
        "title: 'A decision'\n",
        "title: 'A decision'\n"
        "summary: >-\n"
        "  An entry explaining this bug may itself contain\n"
        "  <!-- a comment that is not a key -->\n"))
    assert errors_for(project) == []


# #240: the duplicate check asks the parser, not a line scan, so every
# spelling and depth PyYAML would silently collapse is reported.

def _with(project, extra: str):
    path = _scheme.decision(project, 1, "Active", title="A decision")
    path.write_text(path.read_text().replace(
        "title: 'A decision'\n", "title: 'A decision'\n" + extra))
    return errors_for(project)


def test_a_duplicate_spelled_with_quotes_is_reported(project):
    errors = _with(project, "\"title\": 'Another'\n")
    assert any("duplicate frontmatter key 'title'" in e for e in errors), errors


def test_a_nested_duplicate_is_reported(project):
    errors = _with(project, "meta:\n  name: a\n  name: b\n")
    assert any("duplicate frontmatter key 'name'" in e for e in errors), errors


def test_the_report_names_the_line(project):
    """The parser knows where the second key is; say so."""
    errors = _with(project, "source: a\nsource: b\n")
    path = project / "record/decisions.d/ADR-001.md"
    line = path.read_text().splitlines().index("source: b") + 1
    assert any(f"line {line}" in e for e in errors), errors


def test_repeated_keys_in_sibling_mappings_are_clean(project):
    """`- version:` under each history item is the false positive the line
    scan had to special-case; distinct mappings may share keys."""
    assert _with(project, "notes:\n- version: 1\n  why: a\n"
                          "- version: 2\n  why: b\n") == []


def test_a_merge_key_override_is_clean(project):
    """`<<` then an explicit key is how YAML spells an override."""
    assert _with(project, "base: &b {x: 1}\nmine:\n  <<: *b\n  x: 2\n") == []


def test_a_journal_entry_gets_the_same_check(project):
    """A devlog entry is rendered by the same strict parser downstream."""
    from tests.test_lint import entry, journal_errors, journal_project
    path = entry(journal_project(project), "2026/08/03/211926")
    text = path.read_text()
    path.write_text(text.replace("---\n\n", "title: 'Again'\n---\n\n", 1))
    errors = journal_errors(project)
    assert any("duplicate frontmatter key 'title'" in e for e in errors), errors


def test_a_journal_html_comment_is_reported(project):
    from tests.test_lint import entry, journal_errors, journal_project
    path = entry(journal_project(project), "2026/08/03/211926")
    text = path.read_text()
    path.write_text(text.replace("---\n\n", "<!-- inactive-ok: LIT-1 -->\n---\n\n", 1))
    errors = journal_errors(project)
    assert any("HTML comment" in e for e in errors), errors
