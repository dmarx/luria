"""References to retired documents, and the annotations that excuse them
([ADR-007](../meta/decisions/ADR-007.md)).

The report is a warning, so nothing fails when it is wrong — which is exactly
why its scoping and its acknowledgement syntax need tests. Every rule here
exists to keep the signal actionable; a regression would drown it rather than
break a build.
"""
import sys
from pathlib import Path

from _scheme import decision

from luria import ref_status
from luria.config import current

# unresolved-ok-file: ADR-920 ADR-777 — fixture codes, deliberately not real
REPO = Path(__file__).resolve().parents[1]


def scan(project, body, name="notes.md", retired=12, active=1):
    """A project with one retired and one Active decision, plus `body`."""
    decision(project, retired, "Superseded", "The replaced one")
    decision(project, active, "Active", "The live one")
    (project / name).write_text(body)
    docs = ref_status.load_docs()
    return docs, ref_status.scan([project / name], docs)


def codes(docs):
    retired = next(d for d in docs.values() if not d.active)
    live = next(d for d in docs.values() if d.active)
    return retired, live


# ── Finding references ───────────────────────────────────────────────────


def test_finds_citations_with_line_numbers(project):
    docs, result = scan(project, "intro\nper ADR-012 it works\n")
    assert [c.line for c in result.cited["ADR-012"]] == [2]


def test_repeated_reference_on_one_line_is_one_site(project):
    """Two mentions in a sentence are one place to go look."""
    docs, result = scan(project, "`[ADR-012]` with an `[ADR-012]: x` definition\n")
    assert len(result.cited["ADR-012"]) == 1


def test_a_document_does_not_cite_itself(project):
    """Every decision's own title names it; that is not a reference to follow."""
    path = decision(project, 12, "Superseded")
    docs = ref_status.load_docs()
    assert "ADR-012" not in ref_status.scan([path], docs).cited


def test_only_retired_documents_are_flagged(project):
    docs, result = scan(project, "see ADR-001 and ADR-012\n")
    assert set(result.cited) == {"ADR-001", "ADR-012"}
    assert [d.code for d, _, _ in ref_status.flagged(result, docs)] == ["ADR-012"]


def test_historical_records_are_out_of_scope():
    """A dated record is true about the day it was written, forever. Scanning
    it produces permanent, unactionable rows."""
    scanned = set(ref_status.scanned_files())
    assert REPO / "CHANGELOG.md" not in scanned
    assert REPO / "docs" / "project-memory.md" in scanned
    assert REPO / "README.md" in scanned


def test_journals_are_out_of_scope_entries_and_books_alike():
    """A journal is a dated record too (ADR-020), and its entries are *nested*
    — which is why the check is `is_historical` rather than a membership test
    on `path.parent`."""
    cfg = current()
    scanned = set(ref_status.scanned_files())
    for journal in cfg.journals.values():
        entries = [p for p in journal.dir.rglob("*.md") if p.name != "_template.md"]
        assert entries, "fixture-free test needs a filed entry to be meaningful"
        assert not (scanned & set(entries))
        assert not (scanned & set(journal.output.glob("*.md")))


def test_configured_code_globs_are_in_scope():
    scanned = set(ref_status.scanned_files())
    assert REPO / "luria" / "doc_refs.py" in scanned


# ── Acknowledgements ─────────────────────────────────────────────────────


def test_line_annotation_excuses_its_own_line(project):
    docs, result = scan(
        project, "per ADR-012 <!-- inactive-ok: ADR-012 — deliberate -->\n")
    assert result.cited["ADR-012"][0].excused_by is not None
    assert ref_status.flagged(result, docs) == []


def test_line_annotation_excuses_the_line_below(project):
    """So it can be written above the sentence it excuses."""
    docs, result = scan(
        project, "<!-- inactive-ok: ADR-012 — history -->\nper ADR-012\n")
    assert ref_status.flagged(result, docs) == []


def test_a_bare_annotation_does_not_reach_across_a_blank_line(project):
    """The suffix is the only thing that decides scope
    ([ADR-008](../meta/decisions/ADR-008.md))."""
    docs, result = scan(
        project, "<!-- inactive-ok: ADR-012 -->\n\nper ADR-012\n")
    assert [c.line for _, sites, _ in ref_status.flagged(result, docs)
            for c in sites] == [3]


def test_a_standalone_block_annotation_governs_what_it_introduces(project):
    docs, result = scan(
        project,
        "<!-- inactive-ok-block: ADR-012 -->\n\nper ADR-012\nagain ADR-012\n"
        "\nbut not here, ADR-012\n")
    assert [c.line for _, sites, _ in ref_status.flagged(result, docs)
            for c in sites] == [6]


def test_block_annotation_covers_its_paragraph(project):
    docs, result = scan(
        project,
        "first ADR-012 <!-- inactive-ok-block: ADR-012 -->\nsecond ADR-012\n"
        "\nnext paragraph ADR-012\n")
    assert [c.line for _, sites, _ in ref_status.flagged(result, docs)
            for c in sites] == [4]


def test_file_annotation_covers_the_whole_document(project):
    docs, result = scan(
        project,
        "<!-- inactive-ok-file: ADR-012 — supersession history -->\n"
        "\nfirst ADR-012\n\n\nmuch later ADR-012\n")
    assert ref_status.flagged(result, docs) == []
    assert ref_status.acknowledged_count(result, docs) == 2


def test_annotation_works_in_a_code_comment(project):
    docs, result = scan(
        project, "// shaped by ADR-012  // inactive-ok: ADR-012 — shipped\n",
        name="thing.ts")
    assert ref_status.flagged(result, docs) == []


def test_annotation_only_excuses_the_codes_it_names(project):
    decision(project, 920, "Rejected", "Another retired one")
    docs, result = scan(
        project, "<!-- inactive-ok: ADR-012 -->\nADR-012 and ADR-920\n")
    assert [d.code for d, _, _ in ref_status.flagged(result, docs)] == ["ADR-920"]


def test_bare_numbers_are_rejected(project):
    """The vocabulary has to survive a second reference scheme, so a code
    carries its prefix ([ADR-006](../meta/decisions/ADR-006.md))."""
    docs, result = scan(project, "<!-- inactive-ok: 012 -->\nper ADR-012\n")
    assert ref_status.flagged(result, docs)                      # not excused
    assert any("no document code" in s
               for s in ref_status.stale_annotations(result, docs))


def test_mixed_bare_number_is_rejected(project):
    docs, result = scan(project, "<!-- inactive-ok: ADR-012, 20 -->\n")
    assert any("bare number" in s
               for s in ref_status.stale_annotations(result, docs))


def test_unknown_code_is_reported(project):
    docs, result = scan(project, "<!-- inactive-ok: ADR-999 -->\n")
    assert any("unknown document" in s
               for s in ref_status.stale_annotations(result, docs))


# ── Stale acknowledgements ───────────────────────────────────────────────


def test_annotation_for_an_active_document_is_stale(project):
    docs, result = scan(project, "<!-- inactive-ok: ADR-001 -->\nper ADR-001\n")
    assert any("Active now" in s
               for s in ref_status.stale_annotations(result, docs))


def test_annotation_with_no_matching_reference_is_stale(project):
    docs, result = scan(project, "<!-- inactive-ok: ADR-012 -->\n")
    assert any("no longer applies" in s
               for s in ref_status.stale_annotations(result, docs))


# ── Report shape ─────────────────────────────────────────────────────────


def test_summary_names_the_acknowledged_count(project):
    """Suppression is never silent — the line says how many it hid."""
    docs, result = scan(
        project,
        "<!-- inactive-ok: ADR-012 -->\nADR-012\n\nunexcused ADR-012\n")
    assert "1 acknowledged" in ref_status.summary_lines(result, docs)[0]


def test_summary_counts_every_site_even_when_they_are_not_listed(project):
    """The console caps at five sites per document; the count never caps, so
    the report can't read as "covered everything" when it elided most of it."""
    body = "\n".join(f"line {n} cites ADR-012" for n in range(1, 9))
    docs, result = scan(project, body + "\n")
    assert "cited 8×" in ref_status.summary_lines(result, docs)[0]
    assert "… and 6 more" in "\n".join(ref_status.warnings(2, result, docs))


def test_spread_prefers_distinct_files(tmp_path):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    sites = [ref_status.Citation(a, 1, "ADR-001"),
             ref_status.Citation(a, 2, "ADR-001"),
             ref_status.Citation(b, 9, "ADR-001")]
    assert [c.line for c in ref_status._spread(sites, 2)] == [1, 9]


def test_report_never_fails_the_build():
    """It is a warning. `luria lint` must not start failing on a citation that
    may be correct."""
    sys.argv = ["luria ref-status"]
    assert ref_status.main() == 0


# ── Genericity ───────────────────────────────────────────────────────────


def test_a_second_scheme_needs_no_code_change(project):
    """A prefix and a directory, per
    [ADR-006](../meta/decisions/ADR-006.md)."""
    from luria import config
    (project / "docs" / "rfcs").mkdir(parents=True)
    (project / "docs" / "rfcs" / "rfc-007-example.md").write_text(
        "---\nstatus: Rejected\ntags:\n- record\n---\n\n# RFC-007: A thing\n")
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n'
        '[luria.schemes.ADR]\ndir = "docs/decisions"\n'
        '[luria.schemes.RFC]\ndir = "docs/rfcs"\n')
    config.reset()
    docs = ref_status.load_docs()
    assert "RFC-007" in docs and not docs["RFC-007"].active

    (project / "notes.md").write_text("as RFC-007 decided\n")
    result = ref_status.scan([project / "notes.md"], docs)
    assert [d.code for d, _, _ in ref_status.flagged(result, docs)] == ["RFC-007"]


def test_the_vocabulary_is_scheme_agnostic():
    """`inactive-ok`, not `adr-ok` — the annotation names a prefixed code, so a
    second scheme is config rather than a fork."""
    for module in ("ref_status.py", "directives.py", "doc_refs.py"):
        assert "adr-ok:" not in (REPO / "luria" / module).read_text()


# ── Codes that resolve to nothing (ADR-014) ──────────────────────────────


def test_a_code_naming_no_document_is_reported(project):
    """It used to be dropped: the fixer can't link it, so the lint said
    nothing — and that silence hid ten stale numbers from another project."""
    docs, result = scan(project, "ported from elsewhere: ADR-777\n")
    assert [c.line for c in result.dangling["ADR-777"]] == [1]
    assert [code for code, _, _ in ref_status.dangling(result, docs)] == ["ADR-777"]


def test_a_resolvable_code_is_not_dangling(project):
    docs, result = scan(project, "per ADR-001 it works\n")
    assert result.dangling == {}


def test_unresolved_ok_retires_one(project):
    docs, result = scan(
        project, "<!-- unresolved-ok: ADR-777 — another project's -->\nADR-777\n")
    assert ref_status.dangling(result, docs) == []
    assert ref_status.stale_annotations(result, docs) == []


def test_unresolved_ok_is_scoped_like_every_other_directive(project):
    """No per-directive defaults: the suffix decides, and a blank line between
    the annotation and what it governs needs `-block`."""
    body = "<!-- unresolved-ok{}: ADR-777 — deliberate -->\n\nADR-777\n"
    _, loose = scan(project, body.format(""))
    assert [c.line for c in loose.dangling["ADR-777"] if c.excused_by is None]
    _, block = scan(project, body.format("-block"), name="b.md")
    assert ref_status.dangling(block) == []


def test_unresolved_ok_naming_a_real_document_is_malformed(project):
    """The inverted check. `inactive-ok` is wrong when it names a code that
    doesn't resolve; this one is wrong when it names a code that does — so an
    annotation that stops applying is reported either way."""
    docs, result = scan(
        project, "<!-- unresolved-ok: ADR-001 — deliberate -->\nADR-001\n")
    stale = ref_status.stale_annotations(result, docs)
    assert stale and "does resolve here" in stale[0]


def test_a_code_inside_a_url_is_not_a_citation(project):
    """Linking out to another project's decision is the *correct* way to name
    a foreign document, and the URL contains its code. Counting that as a local
    reference would report every such link as dangling — which is exactly what
    broke the `luria init` template's own scaffolded lint."""
    docs, result = scan(
        project,
        "see [their ADR](https://github.com/o/r/blob/main/docs/ADR-777.md)\n")
    assert result.dangling == {}


def test_a_directive_naming_a_code_is_not_citing_it(project):
    """True of a live annotation and of an example of one alike — otherwise
    documenting the syntax inflates the report, and an annotation excuses
    itself and can never go stale."""
    docs, result = scan(project, "<!-- unresolved-ok: ADR-777 — why -->\n")
    assert result.dangling == {}
