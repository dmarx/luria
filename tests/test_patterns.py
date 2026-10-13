# tests/test_patterns.py
"""Path patterns: the subset a named pattern may be written in (ADR on
chains walking a named path pattern, #371).

The grammar is the subset's definition, so these tests are the subset's
specification: what parses here is what a record may declare, and every
construct a Cypher user will reach for that is outside it is refused by name
rather than by column number.
"""
from __future__ import annotations

import pytest

from luria.patterns import Hop, Node, PatternError, parse


def test_a_fixed_path_reads_nodes_and_hops_in_order():
    p = parse("leads_to",
              "(b:CLAIM)<-[:concludes]-(i:INF)<-[:premise_of]-(a:CLAIM)")
    assert [(n.var, n.label) for n in p.path.nodes] == [
        ("b", "CLAIM"), ("i", "INF"), ("a", "CLAIM")]
    assert p.path.hops == (Hop(("concludes",), right=False),
                           Hop(("premise_of",), right=False))
    assert p.negations == ()


def test_alternation_is_a_set_of_fields_on_one_hop():
    p = parse("met", "(o:OBJ)<-[:rebuts|concedes]-(r:REPLY)")
    assert p.path.hops[0].fields == ("rebuts", "concedes")


def test_variable_length_defaults_follow_cypher():
    def bounds(text):
        return [(h.low, h.high) for h in parse("x", text).path.hops]
    assert bounds("(a:LIT)-[:extends*]->(b:LIT)") == [(1, None)]
    assert bounds("(a:LIT)-[:extends*2]->(b:LIT)") == [(2, 2)]
    assert bounds("(a:LIT)-[:extends*2..]->(b:LIT)") == [(2, None)]
    assert bounds("(a:LIT)-[:extends*..3]->(b:LIT)") == [(1, 3)]
    assert bounds("(a:LIT)-[:extends*1..3]->(b:LIT)") == [(1, 3)]
    assert bounds("(a:LIT)-[:extends]->(b:LIT)") == [(1, 1)]


def test_a_property_map_is_literal_equality():
    p = parse("x", "(c:CLAIM {status: 'Active', number: 3})-[:answers]->(q:Q)")
    assert p.path.nodes[0].props == (("status", "Active"), ("number", "3"))


def test_where_not_takes_a_pattern_over_bound_nodes():
    p = parse("unchallenged", "(c:CLAIM) WHERE NOT (c)<-[:challenges]-(:OBJ)")
    (neg,) = p.negations
    assert neg.nodes[0] == Node("c", "CLAIM", (), bound=True)
    assert neg.nodes[1] == Node("", "OBJ", ())


def test_a_bare_reference_inherits_its_label():
    p = parse("loop", "(a:LIT)-[:extends]->(b:LIT)-[:extends]->(a)")
    assert p.path.nodes[2] == Node("a", "LIT", (), bound=True)


def test_keywords_are_case_insensitive_and_whitespace_is_free():
    p = parse("x", " ( c:CLAIM )\n  where   not ( c ) <-[ :challenges ]- ( :OBJ ) ")
    assert len(p.negations) == 1


@pytest.mark.parametrize("text, says", [
    ("MATCH (a:LIT) RETURN a", "without `MATCH`"),
    ("(a:LIT)-[:x]->(b:LIT) RETURN a", "`RETURN`"),
    ("(a:LIT) OPTIONAL MATCH (a)-[:x]->(b:LIT)", "`OPTIONAL MATCH`"),
    ("(a:LIT)-[:extends]-(b:LIT)", "undirected"),
    ("(a:LIT)<-[:extends]->(b:LIT)", "undirected"),
    ("(a:LIT)-->(b:LIT)", "needs a type"),
    ("(a:LIT)-[]->(b:LIT)", "needs a type"),
    ("(a:LIT:SOTA)", "one label"),
    ("(a:LIT|SOTA)", "one label"),
    ("(a:LIT)-[e:extends]->(b:LIT)", "named edge"),
    ("(a:LIT)-[:extends*0..]->(b:LIT)", "at least 1"),
    ("(a:LIT)-[:extends*3..2]->(b:LIT)", "3..2"),
    ("(a:LIT) WHERE a.status = 'Active'", "`WHERE NOT`"),
    ("(a:LIT) WHERE NOT (a)-[:extends*]->(:LIT)", "variable-length"),
    ("(a:LIT)-[:extends]->(b)", "not bound"),
    ("(a:LIT)-[:extends]->(a:SOTA)", "already bound"),
    ("(a)", "label"),
    ("shortestPath((a:LIT)-[:extends*]->(b:LIT))", "shortestPath"),
    ("(a:LIT) SET a.x = 1", "`SET`"),
    ("", "empty"),
])
def test_out_of_subset_is_refused_by_name(text, says):
    with pytest.raises(PatternError) as caught:
        parse("p", text)
    message = str(caught.value)
    assert message.startswith("luria.yaml: patterns.p: ")
    assert says in message


def test_any_other_mistake_says_where():
    with pytest.raises(PatternError, match=r"column \d+"):
        parse("p", "(a:LIT)-[:extends->(b:LIT)")
