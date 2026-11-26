# tests/test_bare_heading.py
"""A document's H1 may be the title alone, `# Title`, as well as
`# CODE: Title` (#405).

The lint guards one property: the heading and `title:` agree. The code prefix
was never part of that property, but the comparison stripped only a
`# CODE:` prefix, so a bare `# Title` kept its `#` and always disagreed.
Everything else that reads the H1 has to accept the bare form too, or the
lint would pass a heading the rest of luria mishandles."""

from luria import adr_index, lint, site_page


def _errors(title: str, body: str) -> list[str]:
    errors: list[str] = []
    lint.check_title(errors, "record/x.d/ADR-001.md", {"title": title}, body)
    return errors


def test_a_heading_with_the_code_still_agrees():
    assert _errors("A thing", "# ADR-001: A thing\n\nText.\n") == []


def test_a_bare_heading_agrees_with_its_title():
    assert _errors("A thing", "# A thing\n\nText.\n") == []


def test_a_title_that_starts_like_a_code_is_not_stripped():
    # GPT-4 has the shape of a code; a bare heading must still match.
    assert _errors("GPT-4: what it can do", "# GPT-4: what it can do\n") == []


def test_a_bare_heading_that_disagrees_is_still_reported():
    errors = _errors("A thing", "# Another thing\n")
    assert len(errors) == 1 and "disagree" in errors[0]


def test_a_coded_heading_that_disagrees_is_still_reported():
    errors = _errors("A thing", "# ADR-001: Another thing\n")
    assert len(errors) == 1 and "disagree" in errors[0]


def test_the_heading_title_is_read_from_either_form():
    assert adr_index.heading_title("# ADR-001: A thing") == "A thing"
    assert adr_index.heading_title("# A thing") == "A thing"
    assert adr_index.heading_title("") == ""


def test_an_assembled_document_demotes_a_bare_heading_too():
    assert adr_index.demote_heading("# A thing\n\nText.", 3) == (
        "## 3. A thing\n\nText.")
    assert adr_index.demote_heading("# DP-003: A thing\n\nText.", 3) == (
        "## 3. A thing\n\nText.")


def test_the_site_drops_a_bare_heading_the_title_repeats():
    body = "# A thing\n\nText.\n"
    assert site_page.without_title(body, "ADR-001: A thing") == "Text.\n"
    assert site_page.without_title("# Other\n\nText.\n", "ADR-001: A thing") == (
        "# Other\n\nText.\n")
