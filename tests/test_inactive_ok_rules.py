# tests/test_inactive_ok_rules.py
"""`lint.inactive_ok`: the config-level form of the `inactive-ok` directive.

An entry is a one-hop path pattern over the reserved `cites` edge and a
mandatory reason:

    lint:
      inactive_ok:
        - match: "(:QN {status: 'Open'})-[:cites]->(:QN {status: 'Answered'})"
          reason: a split parent cites the answered child split off it

A citation of a retired document is then sanctioned when the document it
sits in matches the citing node and the cited document matches the other.
The case it was built for is a question record: the open parent cites the
answered child split off it, which is the record working; every OTHER
citation of an answered question still warns.

`QN` and `CM` rather than live prefixes, per the fixture-code rule.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from _config import merged

from luria import ack, config, ref_status

RULE = {"match": "(:QN {status: 'Open'})-[:cites]->(:QN {status: 'Answered'})",
        "reason": "a split parent cites the answered child split off it"}

BASE = {
    "issue_url": "https://example.test/issues/{n}",
    "vocabularies": {
        "qstatuses": {"Open": {"blurb": "being asked"},
                      "Answered": {"blurb": "settled"},
                      "Deferred": {"blurb": "parked"}},
        "cstatuses": {"Active": {"blurb": "held"},
                      "Retracted": {"blurb": "withdrawn"}},
    },
    "schemes": {
        "QN": {"dir": "record/questions.d", "output": "docs/questions",
               "active": "Open",
               "fields": {"status": {"vocabulary": "qstatuses"},
                          "kind": {"many": True}}},
        "CM": {"dir": "record/claims.d", "output": "docs/claims",
               "active": "Active",
               "fields": {"status": {"vocabulary": "cstatuses"}}},
    },
}


def project(root: Path, monkeypatch, rules=(RULE,)) -> Path:
    (root / "luria.yaml").write_text(
        merged(BASE, {"lint": {"inactive_ok": list(rules)}}))
    for d in ("record/questions.d", "record/claims.d", "docs"):
        (root / d).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LURIA_ROOT", str(root))
    config.reset()
    return root


def doc(root: Path, code: str, status: str, body: str = "",
        kind: str = "") -> Path:
    folder = "questions.d" if code.startswith("QN") else "claims.d"
    path = root / "record" / folder / f"{code}.md"
    extra = f"kind: {kind}\n" if kind else ""
    path.write_text(f"---\nstatus: {status}\n{extra}title: 'Entry {code}'\n"
                    f"date: '2026-01-01'\n---\n\n# {code}: Entry\n\n{body}\n")
    return path


def corpus(root: Path, parent_body: str = "Split off: QN-001.") -> list[Path]:
    """An answered question, the open parent citing it, and every other kind
    of citer: a question at another status, another scheme, a plain file."""
    return [
        doc(root, "QN-001", "Answered", "The answered child."),
        doc(root, "QN-002", "Open", parent_body),
        doc(root, "QN-003", "Deferred", "Waits on QN-001."),
        doc(root, "CM-001", "Active", "Settles QN-001."),
        _write(root / "notes.md", "Still asking QN-001.\n"),
    ]


def _write(path: Path, text: str) -> Path:
    path.write_text(text)
    return path


def _scan(files):
    docs = ref_status.load_docs()
    return docs, ref_status.scan(files, docs)


def _loud_files(result, docs, root):
    rows = {d.code: loud for d, loud, _ in ref_status.flagged(result, docs)}
    return sorted(c.path.relative_to(root).as_posix()
                  for c in rows.get("QN-001", []))


# ── the sanctioned citation ──────────────────────────────────────────────

def test_the_matched_citer_needs_no_acknowledgement(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    docs, result = _scan(corpus(root))
    parent = [c for c in result.cited["QN-001"]
              if c.path.name == "QN-002.md"]
    assert len(parent) == 1 and parent[0].sanctioned
    assert not parent[0].loud
    assert "record/questions.d/QN-002.md" not in _loud_files(result, docs, root)


@pytest.mark.parametrize("citer", [
    "record/questions.d/QN-003.md",     # the right scheme, another status
    "record/claims.d/CM-001.md",        # another scheme
    "notes.md",                          # not a record document at all
])
def test_every_other_citer_still_warns(tmp_path, monkeypatch, citer):
    root = project(tmp_path, monkeypatch)
    docs, result = _scan(corpus(root))
    assert citer in _loud_files(result, docs, root)


def test_the_arrow_may_point_either_way(tmp_path, monkeypatch):
    """`<-[:cites]-` reverses the roles: the node it leaves is the citer."""
    root = project(tmp_path, monkeypatch, rules=[{
        "match": "(:QN {status: 'Answered'})<-[:cites]-(:QN {status: 'Open'})",
        "reason": RULE["reason"]}])
    docs, result = _scan(corpus(root))
    assert "record/questions.d/QN-002.md" not in _loud_files(result, docs, root)
    assert "record/questions.d/QN-003.md" in _loud_files(result, docs, root)


def test_a_property_may_name_any_field(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, rules=[{
        "match": "(:QN {kind: 'parent'})-[:cites]->(:QN {status: 'Answered'})",
        "reason": RULE["reason"]}])
    files = corpus(root)
    doc(root, "QN-003", "Deferred", "Waits on QN-001.", kind="parent")
    docs, result = _scan(files)
    loud = _loud_files(result, docs, root)
    assert "record/questions.d/QN-003.md" not in loud
    assert "record/questions.d/QN-002.md" in loud


def test_no_rule_judges_exactly_as_before(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, rules=())
    docs, result = _scan(corpus(root))
    assert "record/questions.d/QN-002.md" in _loud_files(result, docs, root)


def test_an_acknowledgement_over_a_sanctioned_site_goes_stale(tmp_path,
                                                             monkeypatch):
    """The migration signal: an `inactive-ok` written before the rule existed
    now answers for nothing, and says which rule took over."""
    root = project(tmp_path, monkeypatch)
    files = corpus(root, parent_body=(
        "<!-- inactive-ok: QN-001 — the answered child -->\n"
        "Split off: QN-001."))
    docs, result = _scan(files)
    stale = ref_status.stale_annotations(result, docs)
    assert any("QN-002.md" in s and "no longer applies" in s
               and "QN-001 is cited here where `lint.inactive_ok[0]` "
                   "allows it" in s
               for s in stale), stale


def test_a_rule_that_sanctions_nothing_is_reported(tmp_path, monkeypatch):
    """A dead rule reads exactly like a working one unless something says so
    (DP-015); the row carries the rule's reason."""
    root = project(tmp_path, monkeypatch, rules=[RULE, {
        "match": "(:CM {status: 'Retracted'})-[:cites]->(:QN)",
        "reason": "a retraction names the question it gave up on"}])
    docs, result = _scan(corpus(root))
    stale = ref_status.stale_annotations(result, docs)
    dead = [s for s in stale if "lint.inactive_ok" in s]
    assert len(dead) == 1, stale
    assert "lint.inactive_ok[1]" in dead[0]
    assert "a retraction names the question it gave up on" in dead[0]


def test_ack_offers_only_the_loud_sites(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    docs, result = _scan(corpus(root))
    _, sites, refusal = ack.plan("QN-001", docs, result)
    assert refusal == ""
    assert "QN-002.md" not in {c.path.name for c in sites}
    assert len(sites) == 3


# ── the declaration ──────────────────────────────────────────────────────

def test_the_rule_is_parsed(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    (rule,) = config.current().inactive_ok
    assert rule.reason == RULE["reason"]
    assert (rule.citer.label, rule.cited.label) == ("QN", "QN")
    assert rule.citer.props == (("status", "Open"),)
    assert rule.cited.props == (("status", "Answered"),)


@pytest.mark.parametrize("rules, message", [
    ("(:QN)-[:cites]->(:QN)",
     r"lint\.inactive_ok: has to be a list"),
    (["(:QN)-[:cites]->(:QN)"],
     r"lint\.inactive_ok\[0\]: has to be a mapping"),
    ([{"match": "(:QN)-[:cites]->(:QN)"}],
     r"lint\.inactive_ok\[0\]: needs a `reason`"),
    ([{"match": "(:QN)-[:cites]->(:QN)", "reason": "  "}],
     r"lint\.inactive_ok\[0\]: needs a `reason`"),
    ([{"match": "(:QN)-[:cites]->(:QN)", "reason": "r", "blurb": "b"}],
     r"lint\.inactive_ok\[0\]: blurb is not a key"),
    ([{"match": "(:QN)", "reason": "r"}],
     r"lint\.inactive_ok\[0\]: .*exactly one hop"),
    ([{"match": "(:QN)-[:cites]->(:QN)-[:cites]->(:QN)", "reason": "r"}],
     r"lint\.inactive_ok\[0\]: .*exactly one hop"),
    ([{"match": "(:QN)-[:refines]->(:QN)", "reason": "r"}],
     r"lint\.inactive_ok\[0\]: .*the hop is `\[:cites\]` and only that"),
    ([{"match": "(:QN)-[:cites|refines]->(:QN)", "reason": "r"}],
     r"lint\.inactive_ok\[0\]: .*the hop is `\[:cites\]` and only that"),
    ([{"match": "(:QN)-[:cites*]->(:QN)", "reason": "r"}],
     r"lint\.inactive_ok\[0\]: .*variable-length"),
    ([{"match": "(a:QN)-[:cites]->(b:QN) WHERE NOT (b)-[:cites]->(a)",
       "reason": "r"}],
     r"lint\.inactive_ok\[0\]: .*`WHERE NOT`"),
    ([{"match": "(:XX)-[:cites]->(:QN)", "reason": "r"}],
     r"lint\.inactive_ok\[0\]: `\(:XX\)`: XX is not a declared scheme"),
    ([{"match": "(:CM {kind: 'x'})-[:cites]->(:QN)", "reason": "r"}],
     r"lint\.inactive_ok\[0\]: `\(:CM\)`: `kind` is not a field CM declares"),
    ([{"match": "()-[:cites]->(:QN)", "reason": "r"}],
     r"lint\.inactive_ok\[0\]: `\(\)` needs a label"),
    ([{"match": "MATCH (:QN)-[:cites]->(:QN)", "reason": "r"}],
     r"lint\.inactive_ok\[0\]: write the pattern without `MATCH`"),
    ([RULE, {"match": "(:QN)-[:cites]->(:QN)"}],
     r"lint\.inactive_ok\[1\]: needs a `reason`"),
])
def test_a_rule_that_cannot_mean_what_it_says_is_refused(
        tmp_path, monkeypatch, rules, message):
    (tmp_path / "luria.yaml").write_text(
        merged(BASE, {"lint": {"inactive_ok": rules}}))
    for d in ("record/questions.d", "record/claims.d", "docs"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    with pytest.raises(ValueError, match=message):
        config.current()
