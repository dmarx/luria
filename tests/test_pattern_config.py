# tests/test_pattern_config.py
"""`patterns:` in luria.yaml, and the refusals that keep a pattern meaning
what it says (#371).

A pattern over a label nothing declares, or a hop nothing types, matches
nothing — and a chain walking it renders an empty page, which reads exactly
like a record with nothing to say (DP-15). So each is refused at load, in
the words of the key to change.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from _config import merged
from luria import config

SCHEMES = """
vocabularies:
  kinds: {x: an x}
schemes:
  CLAIM:
    dir: record/claims.d
    output: docs/claims
    fields:
      kind: {vocabulary: kinds}
    references:
      premise_of: {scheme: INF, many: true, required: false, converse: premises}
  INF:
    dir: record/inferences.d
    output: docs/inferences
    references:
      premises: {scheme: CLAIM, many: true, required: false, converse: premise_of}
      concludes: {scheme: CLAIM, required: false}
  OBJ:
    dir: record/objections.d
    output: docs/objections
    references:
      challenges: {scheme: [CLAIM, INF], required: false}
  LIT:
    dir: record/literature.d
    output: docs/literature
    references:
      extends: {scheme: LIT, many: true, required: false}
      cites: {scheme: CLAIM, many: true, required: false}
"""

FOLLOWS = "(b:CLAIM)<-[:concludes]-(i:INF)<-[:premise_of]-(a:CLAIM)"


def load(tmp_path: Path, monkeypatch, *parts: str | dict) -> config.Config:
    (tmp_path / "luria.yaml").write_text(merged(SCHEMES, *parts))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return config.load(tmp_path)


def refused(tmp_path, monkeypatch, *parts) -> str:
    with pytest.raises(ValueError) as caught:
        load(tmp_path, monkeypatch, *parts)
    return str(caught.value)


def test_a_pattern_loads_as_a_string_or_a_table(tmp_path, monkeypatch):
    cfg = load(tmp_path, monkeypatch, {"patterns": {
        "follows_from": FOLLOWS,
        "lineage": {"match": "(a:LIT)-[:extends*]->(b:LIT)",
                    "blurb": "Every ancestor."}}})
    assert cfg.patterns["follows_from"].match == FOLLOWS
    assert cfg.patterns["lineage"].blurb == "Every ancestor."
    assert cfg.patterns["lineage"].parsed.path.hops[0].high is None


def test_no_patterns_is_the_default(tmp_path, monkeypatch):
    assert load(tmp_path, monkeypatch).patterns == {}


def test_an_unknown_key_is_refused(tmp_path, monkeypatch):
    msg = refused(tmp_path, monkeypatch,
                  {"patterns": {"p": {"match": FOLLOWS, "returns": "a"}}})
    assert "patterns.p: returns is not a key" in msg


def test_a_syntax_error_is_a_config_error(tmp_path, monkeypatch):
    msg = refused(tmp_path, monkeypatch,
                  {"patterns": {"p": "MATCH (a:LIT) RETURN a"}})
    assert msg.startswith("luria.yaml: patterns.p: write the pattern without")


@pytest.mark.parametrize("pattern, says", [
    ("(a:THEORY)-[:extends]->(b:LIT)",
     "`(a:THEORY)`: THEORY is not a declared scheme"),
    ("(a:LIT)-[:supersedes]->(b:LIT)",
     "`-[:supersedes]->` is not a reference LIT declares"),
    ("(a:LIT)<-[:extends]-(b:CLAIM)",
     "`<-[:extends]-` is not a reference CLAIM declares"),
    ("(a:LIT)-[:cites]->(b:INF)",
     "`-[:cites]->` holds CLAIM codes, so it never lands on `(b:INF)`"),
    ("(a:LIT)-[:extends|cites]->(b:LIT)",
     "`-[:extends|cites]->`: `cites` holds CLAIM codes"),
    ("(o:OBJ)-[:challenges*]->(c:CLAIM)",
     "a variable-length hop stays within one scheme"),
    ("(c:CLAIM {colour: 'red'})-[:premise_of]->(i:INF)",
     "`colour` is not a field CLAIM declares"),
    ("(c:CLAIM WHERE c.colour <> 'red')-[:premise_of]->(i:INF)",
     "`colour` is not a field CLAIM declares"),
    ("(c:CLAIM) WHERE NOT (c)<-[:challenges]-(:THEORY)",
     "THEORY is not a declared scheme"),
])
def test_a_pattern_is_checked_against_the_schemes(tmp_path, monkeypatch,
                                                 pattern, says):
    msg = refused(tmp_path, monkeypatch, {"patterns": {"p": pattern}})
    assert msg.startswith("luria.yaml: patterns.p: ")
    assert says in msg


def test_a_hop_into_a_union_is_valid_when_the_label_is_a_target(
        tmp_path, monkeypatch):
    cfg = load(tmp_path, monkeypatch,
               {"patterns": {"p": "(o:OBJ)-[:challenges]->(i:INF)"}})
    assert "p" in cfg.patterns


def test_a_property_may_be_status_undeclared(tmp_path, monkeypatch):
    load(tmp_path, monkeypatch,
         {"patterns": {"p": "(c:CLAIM {status: 'Active', kind: 'x'})"}})


def test_a_pattern_may_not_share_a_name_with_a_reference(tmp_path, monkeypatch):
    msg = refused(tmp_path, monkeypatch, {"patterns": {"extends": FOLLOWS}})
    assert "patterns.extends: is also a reference LIT declares" in msg


CHAIN = {"chains": {"argument": {"scheme": "CLAIM", "relation": "follows_from",
                                 "output": "docs/arguments.md"}}}


def test_a_chain_may_walk_a_pattern(tmp_path, monkeypatch):
    cfg = load(tmp_path, monkeypatch,
               {"patterns": {"follows_from": FOLLOWS}}, CHAIN)
    assert cfg.chains["argument"].relation == ("follows_from",)


def test_a_chain_pattern_must_start_and_end_on_the_chain_scheme(
        tmp_path, monkeypatch):
    msg = refused(tmp_path, monkeypatch, {"patterns": {
        "follows_from": "(i:INF)<-[:premise_of]-(a:CLAIM)"}}, CHAIN)
    assert msg.startswith("luria.yaml: chains.argument: `relation` names "
                          "pattern 'follows_from', which runs from INF to CLAIM")


def test_a_chain_pattern_needs_a_hop(tmp_path, monkeypatch):
    msg = refused(tmp_path, monkeypatch,
                  {"patterns": {"follows_from": "(c:CLAIM)"}}, CHAIN)
    assert "pattern 'follows_from', which has no hop" in msg


def test_a_chain_naming_neither_says_patterns_count(tmp_path, monkeypatch):
    msg = refused(tmp_path, monkeypatch, {"patterns": {"other": FOLLOWS}},
                  CHAIN)
    assert "'follows_from', which is neither a reference CLAIM declares " \
           "nor a declared pattern" in msg
