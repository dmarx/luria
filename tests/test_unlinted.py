"""The whole-document opt-out: `unlinted-file:` (#37).

Every other directive excuses one code; this one excuses a document. The
tests pin the three exits it covers (bare-reference lint, wikilinks, the
reference-status scan), the visibility bargain (counted, never hidden), and
the one misuse it reports (a narrower scope, which governs nothing).
"""
from pathlib import Path

from _scheme import decision

from luria import doc_refs, ref_status, reports

REPO = Path(__file__).resolve().parents[1]

DIRECTIVE = "<!-- unlinted-file: — a fixture-heavy page, checked by hand -->\n"


def page(project: Path, body: str, opted_out: bool = True) -> Path:
    path = project / "docs" / "notes.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((DIRECTIVE if opted_out else "") + body)
    return path


def test_unlinted_file_yields_no_rewritable_refs(project):
    decision(project, 1, "Active")
    body = "This page cites ADR-001 bare, on purpose.\n"
    path = page(project, body)
    adrs, anchors = doc_refs.adr_paths(), doc_refs.dp_anchors()

    assert doc_refs.rewritable_refs(path.read_text(), path, adrs, anchors) == []

    control = page(project, body, opted_out=False)
    assert doc_refs.rewritable_refs(control.read_text(), control,
                                    adrs, anchors), \
        "without the directive the same page has work for the fixer"


def test_unlinted_file_keeps_wikilinks_quiet(project):
    decision(project, 1, "Active")
    path = page(project, "An asserted reference: [[ADR-001]].\n")
    assert doc_refs.wikilinks(path.read_text(), path) == []


def test_unlinted_file_is_skipped_by_the_scan_and_counted(project):
    """The visibility bargain: the file's citations vanish from the scan, and
    the file itself appears in the count — an exemption nobody sees is how a
    report stops being a complete account (ADR-007)."""
    decision(project, 12, "Superseded")
    path = page(project, "Still leaning on ADR-012 here.\n")

    docs = ref_status.load_docs()
    result = ref_status.scan(docs=docs)
    assert result.unlinted == [path]
    assert all(c.path != path
               for sites in result.cited.values() for c in sites)
    assert ref_status.flagged(result, docs) == []


def test_report_lists_the_opted_out_files(project):
    from luria.config import current
    page(project, "Nothing to see.\n")
    text = reports.reference_status()
    assert "## Files that opt out of reference checking" in text
    assert "docs/notes.md" in text


def test_narrow_unlinted_governs_nothing_and_says_so(project):
    path = project / "docs" / "notes.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("<!-- unlinted: — too narrow to mean anything -->\n"
                    "Prose.\n")
    problems = doc_refs.directive_problems(path, path.read_text())
    assert any("file-scoped" in p and "unlinted-file" in p for p in problems)
    assert not doc_refs.unlinted(path, path.read_text())
