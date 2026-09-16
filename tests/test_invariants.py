"""What a relation asserts, checked against what the fields say (#214).

A relation claims its two documents have something in common. If no field
names that something, the record made the claim and never said what it meant
— usually because the vocabulary was short a word, not because the relation
was wrong.
"""

from __future__ import annotations

from _config import merged

from pathlib import Path

from luria import config, invariants, reports


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


RELATIONS = """
schemes:
  LIT:
    axis: tags
    fields:
      # A chain may only assert an invariant on a field the scheme declares,
      # and since ADR-098 `tags` is one of those rather than an axis the
      # code assumes.
      tags:
        many: true
    references:
      extends:
        scheme: LIT
        required: false
        many: true
        converse: extended_by
      extended_by:
        scheme: LIT
        required: false
        many: true
        converse: extends
      compared_against:
        scheme: LIT
        required: false
        many: true
        converse: compared_against
"""

CHAIN = """
chains:
  lineage:
    scheme: LIT
    relation: extends
    sibling: compared_against
    output: docs/lineage.md
    invariant: tags
"""

# The same chain, declaring nothing about any field.
SILENT = CHAIN.replace("    invariant: tags\n", "")


def project(tmp_path, monkeypatch, extra: str = merged(RELATIONS, CHAIN)) -> Path:
    write(tmp_path, "luria.yaml", merged("""
                                  issue_url: https://example.test/issues/{n}
                                  schemes:
                                    LIT:
                                      dir: record/literature.d
                                      output: docs/literature
                                  """, extra))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def note(root: Path, number: int, tags: list[str], *, extends=(),
         compared_against=(), status: str = "Active") -> Path:
    front = ["---", f"status: {status}", f"title: 'Note {number}'", "tags:"]
    front += [f"- {t}" for t in tags]
    front.append("date: '2026-01-01'")
    for name, codes in (("extends", extends),
                        ("compared_against", compared_against)):
        if codes:
            front.append(f"{name}:")
            front += [f"- {c}" for c in codes]
    front += ["---", "", f"# LIT-{number:03d}: Note {number}", "", "Body."]
    return write(root, f"record/literature.d/LIT-{number:03d}.md",
                 "\n".join(front) + "\n")


def chain():
    return config.current().chains["lineage"]


# --- the edge finding -------------------------------------------------------

def test_a_relation_sharing_no_value_is_a_finding(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, ["optimizers"])
    note(root, 2, ["stability"], extends=["LIT-001"])
    hits = invariants.edges(chain())
    assert [h.codes for h in hits] == [("LIT-001", "LIT-002")]


def test_a_relation_sharing_a_value_is_not(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, ["optimizers", "schedules"])
    note(root, 2, ["optimizers"], extends=["LIT-001"])
    assert invariants.edges(chain()) == []


def test_the_shared_value_need_not_be_the_only_one(tmp_path, monkeypatch):
    """Overlapping membership is the feature. A document legitimately in two
    areas must not be a finding merely for being in two."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, ["optimizers", "vision"])
    note(root, 2, ["optimizers", "language"], extends=["LIT-001"])
    assert invariants.edges(chain()) == []


def test_a_document_in_no_relation_is_never_a_finding(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, ["optimizers"])
    note(root, 2, ["stability"])
    assert invariants.edges(chain()) == []
    assert invariants.paths(chain()) == []


def test_the_cross_link_is_walked_too(tmp_path, monkeypatch):
    """`compared_against` asserts two things are rivals for one job, which is
    as much a claim of commonality as succession is."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, ["optimizers"])
    note(root, 2, ["stability"], compared_against=["LIT-001"])
    assert [h.codes for h in invariants.edges(chain())] == [("LIT-001", "LIT-002")]


def test_a_one_sided_declaration_is_walked_before_the_fixer_runs(
        tmp_path, monkeypatch):
    """`extended_by` on one side, nothing written back yet — still an edge."""
    root = project(tmp_path, monkeypatch)
    write(root, "record/literature.d/LIT-001.md",
          "---\nstatus: Active\ntitle: 'Note 1'\ntags:\n- optimizers\n"
          "date: '2026-01-01'\nextended_by:\n- LIT-002\n---\n\n# LIT-001: Note 1\n")
    note(root, 2, ["stability"])
    assert [h.codes for h in invariants.edges(chain())] == [("LIT-001", "LIT-002")]


# --- the path finding -------------------------------------------------------

def test_a_line_can_be_unbound_while_every_step_is_bound(tmp_path, monkeypatch):
    """The case that makes this a second finding rather than the first one
    with a knob: A∩B = {x}, B∩C = {y}, A∩B∩C = empty."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, ["x"])
    note(root, 2, ["x", "y"], extends=["LIT-001"])
    note(root, 3, ["y"], extends=["LIT-002"])
    assert invariants.edges(chain()) == []
    assert [h.codes for h in invariants.paths(chain())] == [
        ("LIT-001", "LIT-002", "LIT-003")]


def test_a_line_sharing_one_value_throughout_is_not_a_finding(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, ["x"])
    note(root, 2, ["x", "y"], extends=["LIT-001"])
    note(root, 3, ["x", "z"], extends=["LIT-002"])
    assert invariants.paths(chain()) == []


def test_every_edge_finding_sits_inside_a_path_finding(tmp_path, monkeypatch):
    """The containment that justifies reporting both: edges are a strict
    subset, so the sharp case is never lost among the diffuse ones."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, ["x"])
    note(root, 2, ["y"], extends=["LIT-001"])
    note(root, 3, ["p"])
    note(root, 4, ["q"], extends=["LIT-003"])
    edge_codes = {h.codes for h in invariants.edges(chain())}
    path_members = [set(h.codes) for h in invariants.paths(chain())]
    assert edge_codes
    for pair in edge_codes:
        assert any(set(pair) <= group for group in path_members)


# --- cardinality ------------------------------------------------------------

def test_a_single_valued_field_is_compared_by_equality(tmp_path, monkeypatch):
    """Equality and intersection are the same test once a scalar reads as a
    set of one, which is why the config needs no operator."""
    root = project(tmp_path, monkeypatch,
                   merged(RELATIONS, CHAIN).replace("invariant: tags",
                                                     "invariant: status"))
    note(root, 1, ["x"], status="Active")
    note(root, 2, ["x"], extends=["LIT-001"], status="Proposed")
    assert [h.codes for h in invariants.edges(chain())] == [("LIT-001", "LIT-002")]

    root = project(tmp_path, monkeypatch,
                   merged(RELATIONS, CHAIN).replace("invariant: tags",
                                                     "invariant: status"))
    note(root, 1, ["x"], status="Active")
    note(root, 2, ["x"], extends=["LIT-001"], status="Active")
    assert invariants.edges(chain()) == []


def test_a_field_absent_on_one_end_shares_nothing(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    write(root, "record/literature.d/LIT-001.md",
          "---\nstatus: Active\ntitle: 'Note 1'\ndate: '2026-01-01'\n"
          "---\n\n# LIT-001: Note 1\n")
    note(root, 2, ["x"], extends=["LIT-001"])
    assert [h.codes for h in invariants.edges(chain())] == [("LIT-001", "LIT-002")]


# --- opt-in -----------------------------------------------------------------

def test_a_chain_declaring_no_invariant_reports_nothing(tmp_path, monkeypatch):
    """The default that keeps the check from firing on relations which never
    asserted a shared field — the reason it is opt-in at all."""
    root = project(tmp_path, monkeypatch, merged(RELATIONS, SILENT))
    note(root, 1, ["optimizers"])
    note(root, 2, ["stability"], extends=["LIT-001"])
    assert invariants.findings() == ([], [])


def test_an_invariant_naming_an_undeclared_field_is_refused(
        tmp_path, monkeypatch):
    """Eagerly, like every other declaration: a field nothing holds would
    report every line and mean nothing."""
    import pytest
    project(tmp_path, monkeypatch,
            merged(RELATIONS, CHAIN).replace("invariant: tags",
                                             "invariant: nonexistent"))
    # The config is parsed lazily, so the refusal lands on first read rather
    # than on write — which is still before any document is walked.
    with pytest.raises(ValueError, match="invariant"):
        config.current()


# --- the report -------------------------------------------------------------

def test_the_report_names_both_findings(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, ["x"])
    note(root, 2, ["y"], extends=["LIT-001"])
    text = reports.unbound_lineage(root)
    assert "1 unbound relation" in text
    assert "1 unbound line" in text
    assert "LIT-001" in text and "LIT-002" in text


def test_the_report_says_so_when_nothing_is_declared(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, merged(RELATIONS, SILENT))
    note(root, 1, ["x"])
    note(root, 2, ["y"], extends=["LIT-001"])
    assert "Nothing declares an `invariant`" in reports.unbound_lineage(root)


def test_the_report_is_a_configured_output(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    assert any(p.name == "unbound-lineage.md" for p in reports.outputs())


# --- declared on the relation itself (#272) ---------------------------------

# The same two references, with the assertion on the relation rather than on a
# chain — so it holds with no chain declared at all.
ON_RELATION = RELATIONS.replace("""      extends:
        scheme: LIT
        required: false
        many: true
        converse: extended_by
""", """      extends:
        scheme: LIT
        required: false
        many: true
        converse: extended_by
        invariant: tags
""")

# A second scheme whose `source` points at the first — the shape a chain
# cannot walk, and the reason the key exists.
CROSS = ON_RELATION + """
  SOTA:
    dir: record/practices.d
    output: docs/practices
    axis: tags
    fields:
      tags:
        many: true
    references:
      source:
        scheme: LIT
        required: false
        many: true
        invariant: tags
"""


def practice(root: Path, number: int, tags: list[str], *, source=()) -> Path:
    front = ["---", "status: Active", f"title: 'Practice {number}'", "tags:"]
    front += [f"- {t}" for t in tags]
    front.append("date: '2026-01-01'")
    if source:
        front.append("source:")
        front += [f"- {c}" for c in source]
    front += ["---", "", f"# SOTA-{number:03d}: Practice {number}", "", "Body."]
    return write(root, f"record/practices.d/SOTA-{number:03d}.md",
                 "\n".join(front) + "\n")


def test_a_relation_can_assert_an_invariant_with_no_chain(tmp_path, monkeypatch):
    """The point of the key: the assertion belongs to the relation, so it
    holds without a sequence to walk or a page to render."""
    root = project(tmp_path, monkeypatch, ON_RELATION)
    note(root, 1, ["optimizers"])
    note(root, 2, ["stability"], extends=["LIT-001"])
    assert config.current().chains == {}
    edge_hits, path_hits = invariants.findings()
    assert [h.codes for h in edge_hits] == [("LIT-001", "LIT-002")]
    assert [h.declared_by for h in edge_hits] == ["LIT.extends"]


def test_a_relation_that_shares_a_value_is_not_a_finding(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, ON_RELATION)
    note(root, 1, ["optimizers", "stability"])
    note(root, 2, ["stability"], extends=["LIT-001"])
    assert invariants.findings() == ([], [])


def test_a_relation_asserts_the_edge_and_not_the_line(tmp_path, monkeypatch):
    """A relation says something about the pair it joins and nothing about
    what else either end is joined to. The transitive reading is the chain's,
    so the case that is a path finding under a chain is no finding here."""
    root = project(tmp_path, monkeypatch, ON_RELATION)
    note(root, 1, ["x"])
    note(root, 2, ["x", "y"], extends=["LIT-001"])
    note(root, 3, ["y"], extends=["LIT-002"])
    assert invariants.findings() == ([], [])


def test_the_relation_may_cross_schemes(tmp_path, monkeypatch):
    """What a chain cannot do. `source` joins a practice to its paper; the two
    sit in no sequence together, and the assertion still means something."""
    root = project(tmp_path, monkeypatch, CROSS)
    note(root, 1, ["optimizers"])
    note(root, 2, ["stability"])
    practice(root, 1, ["stability"], source=["LIT-001"])
    practice(root, 2, ["stability"], source=["LIT-002"])
    edge_hits, _ = invariants.findings()
    assert [(h.declared_by, h.codes) for h in edge_hits] == [
        ("SOTA.source", ("LIT-001", "SOTA-001"))]


def test_a_cross_scheme_chain_is_refused_and_says_where_to_put_it(
        tmp_path, monkeypatch):
    """It used to raise `KeyError` mid-render, because the walker loaded one
    scheme and the relation left it (#272)."""
    import pytest
    project(tmp_path, monkeypatch, CROSS + """
chains:
  evidence:
    scheme: SOTA
    relation: source
    output: docs/evidence.md
""")
    with pytest.raises(ValueError, match="points at LIT rather than SOTA"):
        config.current()


def test_an_invariant_the_far_scheme_cannot_hold_is_refused(
        tmp_path, monkeypatch):
    """Both ends, because the assertion is symmetric: a far scheme with no
    such field makes every edge a finding, which is the same as none.

    `stage` is declared on SOTA and not on LIT, so the near end alone would
    have accepted it."""
    import pytest
    project(tmp_path, monkeypatch, RELATIONS + """
  SOTA:
    dir: record/practices.d
    output: docs/practices
    axis: tags
    fields:
      tags:
        many: true
      stage:
        many: true
    references:
      source:
        scheme: LIT
        required: false
        many: true
        invariant: stage
""")
    with pytest.raises(ValueError, match="which LIT does not declare"):
        config.current()


def test_one_assertion_declared_twice_reports_once(tmp_path, monkeypatch):
    """A chain and the relation it walks, both naming `tags`. That is one
    claim about the record and a redundancy in the config; a second row would
    report the config."""
    root = project(tmp_path, monkeypatch, merged(ON_RELATION, CHAIN))
    note(root, 1, ["optimizers"])
    note(root, 2, ["stability"], extends=["LIT-001"])
    edge_hits, path_hits = invariants.findings()
    assert [(h.declared_by, h.codes) for h in edge_hits] == [
        ("LIT.extends", ("LIT-001", "LIT-002"))]
    # The chain still makes the finding only it can make.
    assert [h.codes for h in path_hits] == [("LIT-001", "LIT-002")]


def test_the_report_names_the_relation_that_declared_it(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, CROSS)
    note(root, 1, ["optimizers"])
    practice(root, 1, ["stability"], source=["LIT-001"])
    text = reports.unbound_lineage(root)
    assert "`SOTA.source` on `tags`" in text
    assert "| Declared by |" in text
    assert "SOTA.source" in text and "1 unbound relation" in text
