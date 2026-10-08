# tests/test_explicit_relations.py
"""Configuration is the only source of relation semantics (the ADR on
explicit relations): no relation is synthesized by the code, roles point at
declarations instead of creating them, every reference value the logic core
sees has a declared type, and `luria upgrade explicit-relations` writes down
what older versions supplied."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from _config import merged, successor

from luria import config, contract, edges, explicit_relations, facts, lint, logic
from luria.adr_index import Adr

PACKAGE = Path(__file__).resolve().parent.parent / "luria"

BASE = {"issue_url": "https://example.test/issues/{n}",
        "schemes": {"LIT": {"dir": "record/literature.d",
                            "output": "docs/literature"},
                    "SOTA": {"dir": "record/practices.d",
                             "output": "docs/practices"}}}

REMOTES = {"remotes": {"ARXIV": {"uid": r"(\d{4})[.:](\d{4,5})",
                                 "url": "https://arxiv.org/abs/{1}.{2}"}}}


def project(root: Path, monkeypatch, *extra) -> Path:
    (root / "luria.yaml").write_text(merged(BASE, *extra))
    for d in ("record/literature.d", "record/practices.d", "docs"):
        (root / d).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LURIA_ROOT", str(root))
    config.reset()
    return root


def doc(root: Path, code: str, status: str = "Active", **fields) -> Path:
    folder = "literature.d" if code.startswith("LIT") else "practices.d"
    front = [f"status: {status}", f"title: 'Entry {code}'", "tags:",
             "- record", "date: '2026-01-01'"]
    for name, values in fields.items():
        front.append(f"{name}:")
        front += [f"- {v}" for v in values]
    path = root / "record" / folder / f"{code}.md"
    path.write_text("---\n" + "\n".join(front) + f"\n---\n\n# {code}: Entry\n\nBody.\n")
    return path


# ── nothing is supplied ──────────────────────────────────────────────────

def test_an_undeclared_successor_is_just_frontmatter(tmp_path, monkeypatch):
    """No contract field, no edge, no fact: the field name alone means
    nothing."""
    root = project(tmp_path, monkeypatch)
    doc(root, "LIT-002")
    one = doc(root, "LIT-001", "Superseded", superseded_by=["LIT-002"])
    lit = config.current().schemes["LIT"]
    assert contract.for_scheme(lit).fields == ()
    assert edges.outbound(Adr(one, lit)) == []
    assert not [f for f in facts.facts() if f.predicate == "ref_value"]
    errors: list[str] = []
    lint.check_contracts(errors)
    assert errors == []


def test_no_module_synthesizes_a_relation():
    """The names the old built-ins used appear in no code path that could
    supply them: no `ANY_SCHEME`, no `built_in`, no `INFLUENCED_BY`."""
    found = []
    for path in sorted(PACKAGE.rglob("*.py")):
        if path.name == "explicit_relations.py":
            continue            # the migration names what it writes down
        text = path.read_text(encoding="utf-8")
        for name in ("ANY_SCHEME", "def built_in", "INFLUENCED_BY",
                     "builtin=True"):
            if name in text:
                found.append(f"{path.name}: {name}")
    assert found == []


def test_relations_lp_never_reads_a_type_off_an_absence():
    text = (PACKAGE / "logic" / "relations.lp").read_text(encoding="utf-8")
    assert "not ref(" not in text


# ── roles point, they do not declare ─────────────────────────────────────

@pytest.mark.parametrize("roles, message", [
    ({"successor": "superseded_by"}, "LIT.successor: names 'superseded_by'"),
    ({"influence": "influenced_by"}, "LIT.influence: names 'influenced_by'"),
    ({"retires_on": "Gone"}, "LIT.retires_on: names 'Gone'"),
])
def test_a_role_naming_nothing_declared_is_refused(tmp_path, monkeypatch,
                                                   roles, message):
    project(tmp_path, monkeypatch, {"schemes": {"LIT": roles}})
    with pytest.raises(ValueError, match=message):
        config.current()


def test_a_declared_successor_carries_its_conditions(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, {"schemes": {"LIT": successor("LIT")}})
    doc(root, "LIT-001", "Superseded")
    errors: list[str] = []
    lint.check_contracts(errors)
    assert any("no `superseded_by:` in frontmatter" in e for e in errors), errors


# ── the facts are a complete interface ───────────────────────────────────

def test_every_reference_value_has_a_declared_type(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, REMOTES, {"schemes": {
        "LIT": successor("LIT", targets=["LIT", "ARXIV"]),
        "SOTA": {"references": {"source": {"scheme": "LIT", "many": True}}}}})
    doc(root, "LIT-002")
    doc(root, "LIT-001", "Superseded", superseded_by=["LIT-002", "ARXIV-2110.08058"])
    doc(root, "SOTA-001", source=["LIT-001"])
    found = facts.facts()
    typed = {x.args[:2] for x in found if x.predicate == "ref_target"}
    docs = {c: s for c, s in (x.args for x in found if x.predicate == "doc")}
    values = [x.args for x in found if x.predicate == "ref_value"]
    assert values
    for code, field, _ in values:
        assert (docs[code], field) in typed, (code, field)
    assert ("LIT", "superseded_by", "ARXIV") in {
        x.args for x in found if x.predicate == "ref_target"}
    # A remote target is a citation, never an edge between documents.
    held = logic.derive("relations")["held"]
    assert ("LIT", "superseded_by", "LIT-001", "LIT-002") in held
    assert not any(x == "ARXIV-2110.08058" for *_, x in held)


def test_a_remote_target_must_be_a_declared_remote(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, {"schemes": {
        "LIT": successor("LIT", targets=["LIT", "ARXIV"])}})
    with pytest.raises(ValueError, match="names scheme 'ARXIV'"):
        config.current()


# ── the migration ────────────────────────────────────────────────────────

def old_record(tmp_path, monkeypatch, *extra) -> Path:
    """A record as an older luria left it: roles implied, nothing declared."""
    root = project(tmp_path, monkeypatch, REMOTES, *extra)
    doc(root, "LIT-002")
    doc(root, "LIT-003")
    doc(root, "LIT-001", "Superseded", superseded_by=["LIT-002", "ARXIV-2110.08058"],
        influenced_by=["LIT-003"])
    doc(root, "SOTA-001", "Superseded", superseded_by=["LIT-002"])
    return root


def upgraded(root: Path) -> dict:
    explicit_relations.run(root, dry_run=False)
    config.reset()
    return yaml.safe_load((root / "luria.yaml").read_text())["schemes"]


def test_the_upgrade_writes_down_what_was_supplied(tmp_path, monkeypatch):
    root = old_record(tmp_path, monkeypatch)
    schemes = upgraded(root)
    lit = schemes["LIT"]
    assert (lit["active"], lit["retires_on"], lit["successor"],
            lit["influence"]) == ("Active", "Superseded", "superseded_by",
                                  "influenced_by")
    assert lit["references"]["superseded_by"] == {
        "scheme": ["LIT", "ARXIV"], "many": True, "required": False,
        "required_when": {"status": ["Superseded"]},
        "forbidden_when": {"status": ["Active"]}}
    assert lit["references"]["influenced_by"] == {
        "scheme": "LIT", "many": True, "required": False}
    # SOTA retires into LIT and cites nothing: narrowest targets, and no
    # `influenced_by` where no document uses it.
    assert schemes["SOTA"]["references"]["superseded_by"]["scheme"] == "LIT"
    assert "influenced_by" not in schemes["SOTA"]["references"]
    assert "influence" not in schemes["SOTA"]
    # And it loads, lints clean, and draws the edges it always drew.
    errors: list[str] = []
    lint.check_contracts(errors)
    assert errors == []
    one = Adr(root / "record/literature.d/LIT-001.md",
              config.current().schemes["LIT"])
    assert {(e.relation, e.target) for e in edges.outbound(one)} == {
        ("superseded_by", "LIT-002"), ("influenced_by", "LIT-003")}


def test_a_second_run_has_nothing_to_do(tmp_path, monkeypatch, capsys):
    root = old_record(tmp_path, monkeypatch)
    upgraded(root)
    before = (root / "luria.yaml").read_text()
    explicit_relations.run(root, dry_run=False)
    assert (root / "luria.yaml").read_text() == before
    assert "nothing to do" in capsys.readouterr().out
    assert not explicit_relations.pending(root)


def test_a_declaration_already_written_is_kept(tmp_path, monkeypatch):
    mine = {"scheme": "LIT", "many": True, "required": False,
            "label": "Replaced by"}
    root = old_record(tmp_path, monkeypatch,
                      {"schemes": {"LIT": {"references": {"superseded_by": mine}}}})
    assert upgraded(root)["LIT"]["references"]["superseded_by"] == mine


def test_a_value_naming_nothing_declared_is_refused(tmp_path, monkeypatch):
    root = old_record(tmp_path, monkeypatch)
    doc(root, "LIT-004", "Superseded", superseded_by=["NOPE-001"])
    before = (root / "luria.yaml").read_text()
    with pytest.raises(SystemExit, match=r"LIT-004.md: `superseded_by: NOPE-001`"):
        explicit_relations.run(root, dry_run=False)
    assert (root / "luria.yaml").read_text() == before


def test_a_scheme_that_never_retires_gets_no_successor(tmp_path, monkeypatch):
    """No document names one, and the vocabulary has no retiring word: the
    old built-in could never have fired, so nothing is written."""
    root = project(tmp_path, monkeypatch, {
        "vocabularies": {"standing": {"Active": {}, "Draft": {}}},
        "schemes": {"LIT": {"fields": {"status": {"vocabulary": "standing"}}}}})
    doc(root, "LIT-001")
    lit = upgraded(root)["LIT"]
    assert "successor" not in lit and "references" not in lit


def test_the_upgrade_only_adds_lines(tmp_path, monkeypatch):
    """A migration that only adds keys adds lines: a long string the person
    wrapped stays wrapped, a quote stays a quote, a comment stays put —
    re-emitting the document would have rewritten all three."""
    root = old_record(tmp_path, monkeypatch, {"schemes": {"SOTA": {
        "references": {"source": {"scheme": "LIT", "many": True,
                                  "required": False}}}}})
    text = (root / "luria.yaml").read_text()
    text = text.replace(
        "issue_url:",
        "# The record's own words, wrapped by hand.\n"
        "blurb: 'A long description that somebody wrapped by hand, across\n"
        "  two lines, which an emitter would unwrap'\n"
        "issue_url:", 1)
    (root / "luria.yaml").write_text(text)
    config.reset()
    explicit_relations.run(root, dry_run=False)
    after = (root / "luria.yaml").read_text().splitlines()
    before = text.splitlines()
    # Every original line is still there, in order.
    it = iter(after)
    assert all(line in it for line in before)
    assert len(after) > len(before)
