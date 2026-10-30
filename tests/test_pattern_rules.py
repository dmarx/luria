# tests/test_pattern_rules.py
"""Lowering a path pattern to clingo, checked against hand-written facts.

The facts are the ones `facts.py` emits (`doc/2`, `status/2`, `value/4`,
`ref_value/3`, `ref_target/3`, `ref_converse/3`), and `relations.lp` reads
them into `held/4` exactly as every chain does — so a pattern's hop means
what a chain's field means, converse side included.
"""
from __future__ import annotations

from luria import logic
from luria.facts import Fact
from luria.pattern_rules import program
from luria.patterns import parse


def F(pred, *args):
    return Fact(pred, args)


SCHEMA = [
    F("ref_target", "CLAIM", "premise_of", "INF"),
    F("ref_converse", "CLAIM", "premise_of", "premises"),
    F("ref_target", "INF", "premises", "CLAIM"),
    F("ref_converse", "INF", "premises", "premise_of"),
    F("ref_target", "INF", "concludes", "CLAIM"),
    F("ref_target", "OBJ", "challenges", "CLAIM"),
    F("ref_target", "LIT", "extends", "LIT"),
]

FOLLOWS = "(b:CLAIM)<-[:concludes]-(i:INF)<-[:premise_of]-(a:CLAIM)"


def solve(patterns: dict[str, str], facts: list[Fact]):
    parsed = {n: parse(n, s) for n, s in patterns.items()}
    return logic.solve([logic.rules("relations"), program(parsed)],
                       SCHEMA + facts)


def docs(scheme, *codes):
    return [F("doc", c, scheme) for c in codes]


def test_a_two_hop_pattern_joins_through_the_intermediate():
    facts = (docs("CLAIM", "C1", "C2") + docs("INF", "I1")
             + [F("ref_value", "C1", "premise_of", "I1"),
                F("ref_value", "I1", "concludes", "C2")])
    got = solve({"follows_from": FOLLOWS}, facts)
    assert got["pattern_edge"] == {("follows_from", "C2", "C1")}
    assert got["pattern_via"] == {("follows_from", "C2", "C1", "i", "I1")}


def test_a_hop_stated_only_on_the_converse_side_counts():
    facts = (docs("CLAIM", "C1", "C2") + docs("INF", "I1")
             + [F("ref_value", "I1", "premises", "C1"),
                F("ref_value", "I1", "concludes", "C2")])
    got = solve({"follows_from": FOLLOWS}, facts)
    assert got["pattern_edge"] == {("follows_from", "C2", "C1")}


def test_the_label_filters_where_a_code_lands():
    # C1's premise_of names a CLAIM, not an INF: not a match, and not an
    # error here either — the contract owns codes in the wrong scheme.
    facts = (docs("CLAIM", "C1", "C2", "C3")
             + [F("ref_value", "C1", "premise_of", "C3")])
    assert "pattern_edge" not in solve({"f": FOLLOWS}, facts)


def test_unfinished_is_a_pattern_the_record_writes():
    """What counts as an unfinished step depends on what the schema
    requires, so luria derives no partial matches of its own (#373): a
    record states it, and only the step it names is reported."""
    facts = (docs("CLAIM", "C1", "C2", "C3") + docs("INF", "I1", "I2", "I3")
             + [F("ref_value", "C1", "premise_of", "I1"),   # complete
                F("ref_value", "I1", "concludes", "C2"),
                F("ref_value", "C1", "premise_of", "I2"),   # premise, no conclusion
                F("ref_value", "I3", "concludes", "C3")])   # conclusion, no premise
    got = solve({"unfinished": "(i:INF)<-[:premise_of]-(a:CLAIM) "
                               "WHERE NOT (i)-[:concludes]->(:CLAIM)"}, facts)
    assert got["pattern_edge"] == {("unfinished", "I2", "C1")}
    assert "pattern_open" not in solve({"f": FOLLOWS}, facts)


def test_alternation_is_a_union_of_fields():
    schema = [F("ref_target", "REPLY", "rebuts", "OBJ"),
              F("ref_target", "REPLY", "concedes", "OBJ")]
    facts = (schema + docs("OBJ", "O1", "O2") + docs("REPLY", "R1", "R2")
             + [F("ref_value", "R1", "rebuts", "O1"),
                F("ref_value", "R2", "concedes", "O2")])
    got = solve({"met": "(o:OBJ)<-[:rebuts|concedes]-(r:REPLY)"}, facts)
    assert got["pattern_edge"] == {("met", "O1", "R1"), ("met", "O2", "R2")}


def test_variable_length_is_the_closure_within_bounds():
    facts = (docs("LIT", "L1", "L2", "L3", "L4")
             + [F("ref_value", "L2", "extends", "L1"),
                F("ref_value", "L3", "extends", "L2"),
                F("ref_value", "L4", "extends", "L3")])
    def edges(text):
        return {(a, b) for _, a, b in
                solve({"x": text}, facts).get("pattern_edge", ())}
    assert edges("(a:LIT)-[:extends*]->(b:LIT)") == {
        ("L2", "L1"), ("L3", "L2"), ("L4", "L3"),
        ("L3", "L1"), ("L4", "L2"), ("L4", "L1")}
    assert edges("(a:LIT)-[:extends*2]->(b:LIT)") == {("L3", "L1"), ("L4", "L2")}
    assert edges("(a:LIT)-[:extends*2..]->(b:LIT)") == {
        ("L3", "L1"), ("L4", "L2"), ("L4", "L1")}
    assert edges("(a:LIT)<-[:extends*..2]-(b:LIT)") == {
        ("L1", "L2"), ("L2", "L3"), ("L3", "L4"), ("L1", "L3"), ("L2", "L4")}


def test_variable_length_terminates_on_a_cycle():
    facts = (docs("LIT", "L1", "L2")
             + [F("ref_value", "L1", "extends", "L2"),
                F("ref_value", "L2", "extends", "L1")])
    got = solve({"x": "(a:LIT)-[:extends*]->(b:LIT)"}, facts)
    assert len(got["pattern_edge"]) == 4


def test_a_property_map_filters_on_status_and_on_any_field():
    facts = (docs("CLAIM", "C1", "C2") + docs("INF", "I1", "I2")
             + [F("status", "C1", "Active"), F("status", "C2", "Withdrawn"),
                F("value", "I1", "kind", 0, "deductive"),
                F("value", "I2", "kind", 0, "abductive")]
             + [F("ref_value", "C1", "premise_of", "I1"),
                F("ref_value", "I1", "concludes", "C2"),
                F("ref_value", "C2", "premise_of", "I2"),
                F("ref_value", "I2", "concludes", "C1")])
    def edges(text):
        return {(a, b) for _, a, b in
                solve({"x": text}, facts).get("pattern_edge", ())}
    assert edges("(b:CLAIM {status: 'Active'})<-[:concludes]-(i:INF)"
                 "<-[:premise_of]-(a:CLAIM)") == {("C1", "C2")}
    assert edges("(b:CLAIM)<-[:concludes]-(i:INF {kind: 'deductive'})"
                 "<-[:premise_of]-(a:CLAIM)") == {("C2", "C1")}


def matched(text: str, facts: list[Fact]) -> set[str]:
    """The first node of every match, read through `pattern_node` as the
    lint reads a reported pattern, so a one-node pattern is a row too."""
    parsed = {"x": parse("x", text)}
    got = logic.solve([logic.rules("relations"), program(parsed, nodes=True)],
                      SCHEMA + facts)
    return {code for _, _, i, code in got.get("pattern_node", ()) if i == 0}


def test_a_node_test_is_inequality_or_membership_on_status_or_any_field():
    facts = (docs("CLAIM", "C1", "C2", "C3", "C4")
             + [F("status", "C1", "Active"), F("status", "C2", "Proposed"),
                F("status", "C3", "Rejected"),
                F("value", "C1", "tags", 0, "a"),
                F("value", "C2", "tags", 0, "a"),
                F("value", "C2", "tags", 1, "b"),
                F("value", "C3", "tags", 0, "c")])
    # C4 has neither field, and matches none of them, as Cypher's null.
    assert matched("(c:CLAIM WHERE c.status <> 'Active')", facts) == {
        "C2", "C3"}
    assert matched("(c:CLAIM WHERE c.status IN ['Active', 'Rejected'])",
                   facts) == {"C1", "C3"}
    assert matched("(c:CLAIM WHERE NOT c.status IN ['Active', 'Rejected'])",
                   facts) == {"C2"}
    # A list field: membership is any value, inequality is no value.
    assert matched("(c:CLAIM WHERE c.tags <> 'a')", facts) == {"C3"}
    assert matched("(c:CLAIM WHERE c.tags IN ['b', 'c'])", facts) == {
        "C2", "C3"}
    assert matched("(c:CLAIM WHERE NOT c.tags IN ['b', 'c'])", facts) == {
        "C1"}


def test_a_node_test_inside_where_not_finds_what_is_ready_for_a_ruling():
    facts = (docs("CLAIM", "C1", "C2", "C3", "C4", "P1", "P2")
             + docs("OBJ", "O1", "O2")
             + [F("status", c, s) for c, s in [
                 ("C1", "Proposed"), ("C2", "Proposed"), ("C3", "Proposed"),
                 ("C4", "Active"), ("P1", "Active"), ("P2", "Proposed"),
                 ("O1", "Rejected"), ("O2", "Proposed")]]
             + [F("ref_target", "CLAIM", "rests_on", "CLAIM"),
                F("ref_value", "C1", "rests_on", "P1"),
                F("ref_value", "C2", "rests_on", "P2"),
                F("ref_value", "O1", "challenges", "C1"),
                F("ref_value", "O2", "challenges", "C3")])
    ready = ("(c:CLAIM {status: 'Proposed'})"
             " WHERE NOT (c)-[:rests_on]->(p:CLAIM WHERE p.status <> 'Active')"
             " WHERE NOT (c)<-[:challenges]-(o:OBJ"
             " WHERE o.status IN ['Proposed', 'Active'])")
    # C2 rests on a Proposed premise and C3 has a live objection; C1's
    # premise is Active and its objection Rejected; P2 rests on nothing.
    assert matched(ready, facts) == {"C1", "P2"}


def test_a_node_test_on_a_field_other_than_status_needs_values():
    from luria.pattern_rules import needs_values
    assert not needs_values({"x": parse("x", "(c:CLAIM WHERE c.status <> 'A')")})
    assert needs_values({"x": parse("x", "(c:CLAIM WHERE c.kind <> 'A')")})


def test_where_not_removes_matches_with_the_negated_path():
    facts = (docs("CLAIM", "C1", "C2", "C3") + docs("INF", "I1", "I2")
             + docs("OBJ", "O1")
             + [F("ref_value", "C1", "premise_of", "I1"),
                F("ref_value", "I1", "concludes", "C2"),
                F("ref_value", "C1", "premise_of", "I2"),
                F("ref_value", "I2", "concludes", "C3"),
                F("ref_value", "O1", "challenges", "C3")])
    got = solve({"x": FOLLOWS + " WHERE NOT (b)<-[:challenges]-(:OBJ)"},
                facts)
    assert got["pattern_edge"] == {("x", "C2", "C1")}


def test_a_bare_reference_closes_a_cycle():
    facts = (docs("LIT", "L1", "L2", "L3")
             + [F("ref_value", "L1", "extends", "L2"),
                F("ref_value", "L2", "extends", "L1"),
                F("ref_value", "L3", "extends", "L1")])
    got = solve({"loop": "(a:LIT)-[:extends]->(b:LIT)-[:extends]->(a)"},
                facts)
    assert got["pattern_edge"] == {("loop", "L1", "L1"), ("loop", "L2", "L2")}


def test_two_patterns_lower_side_by_side():
    facts = (docs("CLAIM", "C1", "C2") + docs("INF", "I1")
             + [F("ref_value", "C1", "premise_of", "I1"),
                F("ref_value", "I1", "concludes", "C2")])
    got = solve({"f": FOLLOWS,
                 "g": "(a:CLAIM)-[:premise_of]->(i:INF)-[:concludes]->(b:CLAIM)"},
                facts)
    assert got["pattern_edge"] == {("f", "C2", "C1"), ("g", "C1", "C2")}


def test_a_name_is_quoted_not_interpolated_into_the_program():
    text = program({'we"ird': parse('we"ird', FOLLOWS)})
    assert '"we\\"ird"' in text
