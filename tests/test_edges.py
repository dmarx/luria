"""Typed edges, derived from what the record already says (#141).

The citation graph has one kind of edge: A mentions B. Three facts in the
record are stronger than a mention and were already written down — a
`Superseded — by` note, an `influenced_by:` list, and any field a scheme
declares a reference (ADR-060) — and nothing read them as edges. Now
something does. No new frontmatter field: a `superseded_by:` beside the note
would be the second copy of one fact that DP-3 says will drift.
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

def test_a_superseded_note_with_a_link_is_an_edge(project):
    decision(project, 1, "Active")
    path = decision(project, 2, "Superseded — by [ADR-001](ADR-001.md)")
    edge, = edges.outbound(adr(path))
    assert (edge.source, edge.relation, edge.target) == \
        ("ADR-002", "superseded_by", "ADR-001")
    assert "status" in edge.because


def test_a_bare_code_in_the_note_is_the_same_edge(project):
    decision(project, 1, "Active")
    path = decision(project, 2, "Superseded — by ADR-001")
    edge, = edges.outbound(adr(path))
    assert edge.target == "ADR-001"


def test_a_note_that_runs_on_yields_only_the_successor(project):
    """ADR-015's note runs on past its successor and names a second code.
    The canonical `by CODE` opening is the succession; the second code is a
    mention — the citation scanner's business, not an edge."""
    decision(project, 1, "Active")
    decision(project, 2, "Active")
    path = decision(project, 3, "Superseded — by ADR-001, which folds in ADR-002")
    found = {(e.relation, e.target) for e in edges.outbound(adr(path))}
    assert found == {("superseded_by", "ADR-001")}


def test_a_superseded_note_off_the_canonical_form_derives_nothing(project):
    """`Superseded` is scheme-relative (ADR-056) and the note is prose. Only
    the shape the migration machinery writes — `by CODE` first — is read as
    the succession; a code anywhere else is not promoted to one."""
    decision(project, 1, "Active")
    path = decision(project, 2, "Superseded — folded into ADR-001 wholesale")
    assert edges.outbound(adr(path)) == []


def test_a_superseded_note_with_no_code_is_no_edge(project):
    path = decision(project, 1, "Superseded — by the new runbook")
    assert edges.outbound(adr(path)) == []


def test_a_code_in_any_other_status_note_is_not_an_edge(project):
    """A Rejected note may cite what defeated it, a Deferred one what parked
    it. Reading either as a relation — a succession, or a `status_note`
    relation an earlier draft invented — dresses a location up as a
    meaning. Where the code was found is provenance; the fact is a mention,
    and mentions belong to the citation scanner once the note is read as
    prose (a separate decision)."""
    decision(project, 1, "Active")
    rejected = decision(project, 2, "Rejected — [ADR-001](ADR-001.md) covers it")
    deferred = decision(project, 3, "Deferred — parked by ADR-001")
    for path in (rejected, deferred):
        assert edges.outbound(adr(path)) == []


def test_a_foreign_code_in_the_note_is_not_an_edge(project):
    """A remote's namespace is theirs (ADR-016); the graph has no node for
    it, so there is nothing for the edge to land on."""
    (project / "luria.toml").write_text(
        (project / "luria.toml").read_text()
        + '[luria.remotes.LU]\nname = "luria"\nrepo = "dmarx/luria"\n'
          'dir = "record/decisions.d"\n')
    config.reset()
    path = decision(project, 1, "Superseded — by LU-ADR-013")
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
    decision(project, 2, "Superseded — by [ADR-001](ADR-001.md)")
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
    decision(project, 2, "Superseded — by [ADR-001](ADR-001.md)")
    out = project / "build" / "site"
    site.stage(out)
    staged = (out / "content" / "record" / "decisions.d" / "ADR-001.md").read_text()
    assert "**Supersedes** [ADR-002](ADR-002.md)" in staged


# --- one edge per code in a plural reference ------------------------------

def scenes(tmp_path, monkeypatch, many: bool = True) -> Path:
    write(tmp_path, "luria.toml", f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"
[luria.schemes.SCENE]
dir = "record/scenes.d"
[luria.schemes.SCENE.references]
follows = {{ scheme = "SCENE", many = {str(many).lower()} }}
""")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    for n in (1, 2):
        doc(tmp_path, f"record/scenes.d/SCENE-00{n}.md", code=f"SCENE-00{n}")
    return tmp_path


def test_a_plural_reference_is_one_edge_per_code(tmp_path, monkeypatch):
    """The reported defect's other half: the edge derivation stringified
    the list too, and emitted one edge for two codes."""
    root = scenes(tmp_path, monkeypatch)
    path = doc(root, "record/scenes.d/SCENE-003.md", code="SCENE-003",
               extra="follows:\n- SCENE-001\n- SCENE-002")
    found = edges.outbound(Adr(path, current().schemes["SCENE"]))
    assert [(e.relation, e.target) for e in found] == \
        [("follows", "SCENE-001"), ("follows", "SCENE-002")]


def test_a_list_in_a_scalar_reference_yields_no_edge(tmp_path, monkeypatch):
    """The lint reports the shape; the graph does not guess which element
    was meant."""
    root = scenes(tmp_path, monkeypatch, many=False)
    path = doc(root, "record/scenes.d/SCENE-003.md", code="SCENE-003",
               extra="follows:\n- SCENE-001\n- SCENE-002")
    assert edges.outbound(Adr(path, current().schemes["SCENE"])) == []
