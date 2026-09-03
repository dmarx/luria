"""Typed edges, derived from what the record already says (#141).

The citation graph has one kind of edge: A mentions B. Three facts in the
record are stronger than a mention and were already written down — a
`superseded_by:` field, an `influenced_by:` list, and any field a scheme
declares a reference (ADR-060) — and nothing read them as edges. Now
something does.
"""

from __future__ import annotations

from pathlib import Path

from luria import config, edges, site
from luria.adr_index import Adr
from luria.config import current

from _scheme import decision

# inactive-ok-file: ADR-007, ADR-010, ADR-015 — the superseded decisions whose
# successions these tests read; retired is the point.


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def doc(root: Path, rel: str, *, code: str, status: str = "Active",
        extra: str = "") -> Path:
    front = ["---", f"status: {status!r}", f"title: 'Entry {code}'",
             "tags:", "- record", "date: '2026-01-01'"]
    if extra:
        front.append(extra)
    front += ["---", "", f"# {code}: Entry {code}", "", "Body."]
    return write(root, rel, "\n".join(front) + "\n")


def adr(path: Path) -> Adr:
    return Adr(path, current().schemes["ADR"])


# --- supersession, read out of the note it already lives in --------------

def test_the_superseded_by_field_is_an_edge(project):
    decision(project, 1, "Active")
    path = decision(project, 2, "Superseded", superseded_by=["ADR-001"])
    edge, = edges.outbound(adr(path))
    assert (edge.source, edge.relation, edge.target) == \
        ("ADR-002", "superseded_by", "ADR-001")
    assert "superseded_by" in edge.because


def test_the_field_may_name_several_successors(project):
    decision(project, 1, "Active")
    decision(project, 2, "Active")
    path = decision(project, 3, "Superseded", superseded_by=["ADR-001", "ADR-002"])
    assert [e.target for e in edges.outbound(adr(path))] == ["ADR-001", "ADR-002"]


def test_a_note_alone_is_not_an_edge(project):
    """Two drafts inferred the successor from a `by CODE` note and were
    corrected on review: the field is structure, checked and resolved; a
    sentence the tool happens to recognise is not. The old shape is read
    once more by `luria index`, as the repair that fills the field."""
    decision(project, 1, "Active")
    path = decision(project, 2, "Superseded — by ADR-001")
    assert edges.outbound(adr(path)) == []


def test_a_note_beside_the_field_is_prose_not_a_second_edge(project):
    decision(project, 1, "Active")
    decision(project, 2, "Active")
    path = decision(project, 3, "Superseded — folds in ADR-002",
                    superseded_by=["ADR-001"])
    assert [(e.relation, e.target) for e in edges.outbound(adr(path))] == \
        [("superseded_by", "ADR-001")]


def test_a_code_in_any_other_status_note_is_not_an_edge(project):
    """A Rejected note may cite what defeated it, a Deferred one what parked
    it. The note is prose: those are citations the scanner finds, not
    relations the graph invents."""
    decision(project, 1, "Active")
    rejected = decision(project, 2, "Rejected — [ADR-001](ADR-001.md) covers it")
    deferred = decision(project, 3, "Deferred — parked by ADR-001")
    for path in (rejected, deferred):
        assert edges.outbound(adr(path)) == []


def test_a_foreign_successor_is_not_an_edge(project):
    """A remote's namespace is theirs (ADR-016); the graph has no node for
    it, so there is nothing for the edge to land on."""
    (project / "luria.toml").write_text(
        (project / "luria.toml").read_text()
        + '[luria.remotes.LU]\nname = "luria"\nrepo = "dmarx/luria"\n'
          'dir = "record/decisions.d"\n')
    config.reset()
    path = decision(project, 1, "Superseded", superseded_by=["LU-ADR-013"])
    assert edges.outbound(adr(path)) == []


# --- lineage and declared references ------------------------------------

def test_influenced_by_is_an_edge(project):
    decision(project, 1, "Active")
    path = decision(project, 2, "Active")
    path.write_text(path.read_text().replace(
        "date: '2026-01-01'", "date: '2026-01-01'\ninfluenced_by:\n- ADR-001"))
    edge, = edges.outbound(adr(path))
    assert (edge.relation, edge.target) == ("influenced_by", "ADR-001")


def two_schemes(tmp_path, monkeypatch) -> Path:
    write(tmp_path, "luria.toml", """
[luria]
issue_url = "https://example.test/issues/{n}"
[luria.schemes.LIT]
dir = "record/literature.d"
[luria.schemes.SOTA]
dir = "record/practices.d"
[luria.schemes.SOTA.references]
source = { scheme = "LIT" }
""")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def test_a_declared_reference_field_is_an_edge_named_for_the_field(
        tmp_path, monkeypatch):
    root = two_schemes(tmp_path, monkeypatch)
    doc(root, "record/literature.d/LIT-001.md", code="LIT-001")
    path = doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
               extra="source: LIT-001")
    edge, = edges.outbound(Adr(path, current().schemes["SOTA"]))
    assert (edge.source, edge.relation, edge.target) == \
        ("SOTA-001", "source", "LIT-001")
    assert "source" in edge.because


def test_a_linked_reference_field_still_reads(tmp_path, monkeypatch):
    root = two_schemes(tmp_path, monkeypatch)
    path = doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
               extra="source: '[LIT-001](../literature.d/LIT-001.md)'")
    edge, = edges.outbound(Adr(path, current().schemes["SOTA"]))
    assert edge.target == "LIT-001"


def test_a_reference_that_is_not_a_code_is_no_edge(tmp_path, monkeypatch):
    """The lint reports it (ADR-060); the graph does not invent a node."""
    root = two_schemes(tmp_path, monkeypatch)
    path = doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
               extra="source: 'a paper I read once'")
    assert edges.outbound(Adr(path, current().schemes["SOTA"])) == []


# --- the graph, both directions -------------------------------------------

def test_inbound_edges_are_the_backlinks(project):
    decision(project, 1, "Active")
    decision(project, 2, "Superseded", superseded_by=["ADR-001"])
    graph = edges.graph()
    edge, = graph.inbound("ADR-001")
    assert edge.source == "ADR-002" and edge.relation == "superseded_by"
    assert graph.inbound("ADR-002") == []
    assert [e.target for e in graph.outbound("ADR-002")] == ["ADR-001"]


def test_the_shipped_record_has_its_three_successions():
    """Fired on a real case: the three superseded decisions in this record
    each name a successor, and the graph reads every one."""
    graph = edges.graph()
    succession = {(e.source, e.target) for e in graph.edges
                  if e.relation == "superseded_by"}
    assert {("ADR-007", "ADR-035"), ("ADR-010", "ADR-011")} <= succession
    assert any(s == "ADR-015" and t == "ADR-016" for s, t in succession)


# --- rendered where a reader is -------------------------------------------

def test_the_record_line_names_what_a_decision_supersedes():
    where = current().schemes["ADR"].dir / "ADR-011.md"
    inbound = [edges.Edge("ADR-010", "superseded_by", "ADR-011", "status")]
    line = site.record_line({"status": "Active"}, where, inbound=inbound)
    assert "**Supersedes** [ADR-010](ADR-010.md)" in line


def test_the_record_line_names_what_a_decision_influenced():
    where = current().schemes["ADR"].dir / "ADR-035.md"
    inbound = [edges.Edge("DP-010", "influenced_by", "ADR-035", "frontmatter")]
    line = site.record_line({"status": "Active"}, where, inbound=inbound)
    assert "**Influenced** [DP-010](../../docs/design-principles.md#dp-10)" in line


def test_the_record_line_carries_a_declared_reference_both_ways(
        tmp_path, monkeypatch):
    root = two_schemes(tmp_path, monkeypatch)
    lit = doc(root, "record/literature.d/LIT-001.md", code="LIT-001")
    sota = doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
               extra="source: LIT-001")
    out = [edges.Edge("SOTA-001", "source", "LIT-001", "frontmatter `source:`")]
    assert "**Source** [LIT-001](../literature.d/LIT-001.md)" in \
        site.record_line({"status": "Active"}, sota, outbound=out)
    assert "**Cited as `source` by** [SOTA-001](../practices.d/SOTA-001.md)" in \
        site.record_line({"status": "Active"}, lit, inbound=out)


def test_a_staged_page_carries_its_inbound_edges(project):
    decision(project, 1, "Active")
    decision(project, 2, "Superseded", superseded_by=["ADR-001"])
    out = project / "build" / "site"
    site.stage(out)
    staged = (out / "content" / "record" / "decisions.d" / "ADR-001.md").read_text()
    assert "**Supersedes** [ADR-002](ADR-002.md)" in staged
