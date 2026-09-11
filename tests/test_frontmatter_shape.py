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
