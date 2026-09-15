# tests/test_cite_targets.py
"""`cite = "page"` in a record whose pages are not published.

The two halves of ADR-094 have to travel together. `cite = "page"` sends a
citation of DP-003 to that principle's own page rather than to an anchor in
the assembled view, which is the durable address — a path does not move when
somebody rewords a heading. It is also only an address if the page exists:
a site that excludes the scheme's sources does the one thing it can and
sends the reader to the repository. ADR-094 measured that when
`publishable()` still withheld them, and links leaving the site went from 10
to 195.

`publishable()` no longer withholds them by derivation, so this is reachable
only on purpose now — which is exactly when it needs saying (ADR-100).
"""

from __future__ import annotations

from pathlib import Path

from _config import merged

from luria import config, lint


def _document_record(root: Path, extra: dict | None = None) -> Path:
    path = root / "luria.yaml"
    path.write_text(merged(path.read_text(), merged({
        "schemes": {"DP": {"dir": "record/principles.d",
                           "output": "docs/design-principles.md",
                           "render": "document", "cite": "page"}},
        "site": {"publish": True,
                 "base_url": "example.github.io/r"}}, extra or {})))
    d = root / "record" / "principles.d"
    d.mkdir(parents=True, exist_ok=True)
    (d / "DP-001.md").write_text(
        "---\nstatus: Active\ntitle: 'A principle'\nversion: 1\n"
        "date: '2026-01-01'\n---\n\n# DP-001: A principle\n\nBody.\n")
    config.reset()
    return root


def test_a_published_record_is_silent(project):
    _document_record(project)
    assert lint.cite_target_lines() == []


def test_excluding_the_sources_is_a_finding(project):
    """The config asks for durable citations and the publishing rules
    withhold the thing they resolve to."""
    _document_record(project, {"site": {"exclude": ["record/principles.d/**"]}})
    lines = lint.cite_target_lines()
    assert len(lines) == 1, lines
    assert "DP" in lines[0] and "not published" in lines[0]
    assert "DP-001" in lines[0], "names one, so the reader can go look"


def test_citing_the_view_instead_is_silent(project):
    """`cite = "view"` resolves to an anchor luria emits into the assembled
    page, which is published whether or not the sources are."""
    _document_record(project, {"schemes": {"DP": {"cite": "view"}},
                               "site": {"exclude": ["record/principles.d/**"]}})
    assert lint.cite_target_lines() == []


def test_a_record_that_publishes_nothing_is_silent(project):
    """Nothing resolves anywhere, so the two settings do not disagree —
    there is only one of them."""
    _document_record(project, {"site": {"publish": False,
                                        "exclude": ["record/principles.d/**"]}})
    assert lint.cite_target_lines() == []


def test_the_class_can_be_enforced(project):
    """A warning by default: a record may publish a subset deliberately and
    this cannot tell. Naming it in `fail_on` makes it fatal (ADR-035)."""
    assert "unresolved-citations" in lint.FAILABLE
