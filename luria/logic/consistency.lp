% luria/logic/consistency.lp
% Declarations in luria.yaml that cannot mean what they say, across schemes
% and chains. Each derived atom is one refusal; luria/consistency.py words it
% and raises the first in the order the loader has always checked them.
%
% Facts: scheme/1, remote/1, ref/2, ref_target/3, ref_converse/3,
% ref_many/2, ref_invariant/3, nameable/2 (every field a scheme can hold),
% role_successor/2, role_retires_on/2, role_influence/2, status_word/2, and
% per raw
% chain: chain_scheme/2 (one per listed scheme), chain_facet/2, chain_walks/3 (relation or sibling),
% chain_output/1, chain_invariant/2; and per pattern: pattern/1,
% pat_node/4 (pattern, path, position, label — path 0 is the match, 1.. each
% WHERE NOT), pat_hop/6 (pattern, path, hop, near position, far position,
% field), pat_closure/3, pat_prop/4, pat_ends/3 (first and last label),
% pat_hops/2.

% ── references ──────────────────────────────────────────────────────────
% A reference may only name a scheme or a remote that is declared.
unknown_target(S, F, T) :- ref_target(S, F, T), not scheme(T), not remote(T).

% A converse lives on the scheme the field's codes land in, points back,
% names this field as its own converse, and both sides take several codes.
pair(S, F, B, T) :- ref_converse(S, F, B), ref_target(S, F, T), scheme(T).
converse_missing(S, F, T) :- pair(S, F, B, T), not ref(T, B).
converse_elsewhere(S, F, T) :- pair(S, F, B, T), ref(T, B),
                               not ref_target(T, B, S).
converse_unrequited(S, F, T) :- pair(S, F, B, T), ref(T, B),
                                not ref_converse(T, B, F).
converse_single(S, F, T, S, F) :- pair(S, F, B, T), ref(T, B),
                                  not ref_many(S, F).
converse_single(S, F, T, T, B) :- pair(S, F, B, T), ref(T, B),
                                  not ref_many(T, B).

% A relation's invariant has to be a field both of its ends can hold.
invariant_unheld(S, F, S) :- ref_invariant(S, F, I), not nameable(S, I).
invariant_unheld(S, F, T) :- ref_invariant(S, F, I), ref_target(S, F, T),
                             T != S, scheme(T), not nameable(T, I).

% ── roles ───────────────────────────────────────────────────────────────
% A role points at something declared; it never declares it. The successor
% role names a reference the scheme declares; the retiring role names a word
% its status vocabulary holds.
successor_undeclared(S, F) :- role_successor(S, F), not ref(S, F).
retires_unknown(S, W) :- role_retires_on(S, W), not status_word(S, W).
influence_undeclared(S, F) :- role_influence(S, F), not ref(S, F).

% ── chains ──────────────────────────────────────────────────────────────
% A chain lists one scheme or several, and any listed scheme's documents may
% be a step. A field it walks may be declared on any of them and land on any
% of them; a pattern may start and end on any of them.
chain_unknown(N, S) :- chain_scheme(N, S), not scheme(S).
chain_known(N) :- chain_scheme(N, _), #count { S : chain_scheme(N, S),
                                               not scheme(S) } = 0.
facet_held(N, X) :- chain_facet(N, X), chain_scheme(N, S), nameable(S, X).
facet_unheld(N, X) :- chain_facet(N, X), chain_known(N), not facet_held(N, X).
walk_declared(N, F) :- chain_walks(N, _, F), chain_scheme(N, S), ref(S, F).
walk_undeclared(N, K, F) :- chain_walks(N, K, F), chain_known(N),
                            not walk_declared(N, F), not pattern(F).
walk_leaves(N, K, F, T) :- chain_walks(N, K, F), chain_scheme(N, S),
                           ref_target(S, F, T), not chain_scheme(N, T).
walk_pattern_ends(N, K, P, L) :- chain_walks(N, K, P), pattern(P),
                                 chain_known(N), pat_ends(P, L, _),
                                 not chain_scheme(N, L).
walk_pattern_ends(N, K, P, L) :- chain_walks(N, K, P), pattern(P),
                                 chain_known(N), pat_ends(P, _, L),
                                 not chain_scheme(N, L).
walk_pattern_still(N, K, P) :- chain_walks(N, K, P), pat_hops(P, 0).
output_missing(N) :- chain_known(N), not chain_output(N).
% Every listed scheme holds an invariant, since every step is checked.
chain_invariant_unheld(N, I, S) :- chain_invariant(N, I), chain_known(N),
                                   chain_scheme(N, S), not nameable(S, I).

% ── patterns ────────────────────────────────────────────────────────────
% Every label a scheme; every hop a reference declared on the node the arrow
% leaves, able to land on the node it reaches; a closure within one scheme;
% every property a field the node's scheme can hold; and no pattern named
% like a reference, so a name a chain walks means one thing.
pattern_label_unknown(P, W, I) :- pat_node(P, W, I, L), not scheme(L).
pattern_hop_undeclared(P, W, H) :- pat_hop(P, W, H, Near, _, F),
                                   pat_node(P, W, Near, S), scheme(S),
                                   not ref(S, F).
pattern_hop_misses(P, W, H) :- pat_hop(P, W, H, Near, Far, F),
                               pat_node(P, W, Near, S), ref(S, F),
                               pat_node(P, W, Far, T), scheme(T),
                               not ref_target(S, F, T),
                               not ref_target(S, F, "*").
pattern_closure_leaves(P, W, H) :- pat_closure(P, W, H),
                                   pat_hop(P, W, H, Near, Far, _),
                                   pat_node(P, W, Near, S),
                                   pat_node(P, W, Far, T), S != T.
pattern_prop_unheld(P, W, I, F) :- pat_prop(P, W, I, F), pat_node(P, W, I, S),
                                   scheme(S), not nameable(S, F).
pattern_shadows(P, S) :- pattern(P), ref(S, P).

#show unknown_target/3.
#show converse_missing/3.
#show converse_elsewhere/3.
#show converse_unrequited/3.
#show converse_single/5.
#show invariant_unheld/3.
#show successor_undeclared/2.
#show retires_unknown/2.
#show influence_undeclared/2.
#show chain_unknown/2.
#show facet_unheld/2.
#show walk_undeclared/3.
#show walk_leaves/4.
#show walk_pattern_ends/4.
#show walk_pattern_still/3.
#show output_missing/1.
#show pattern_label_unknown/3.
#show pattern_hop_undeclared/3.
#show pattern_hop_misses/3.
#show pattern_closure_leaves/3.
#show pattern_prop_unheld/4.
#show pattern_shadows/2.
#show chain_invariant_unheld/3.
