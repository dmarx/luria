% luria/logic/consistency.lp
% Declarations in luria.yaml that cannot mean what they say, across schemes
% and chains. Each derived atom is one refusal; luria/consistency.py words it
% and raises the first in the order the loader has always checked them.
%
% Facts: scheme/1, ref/2, ref_target/3, ref_converse/3, ref_many/2,
% ref_invariant/3, nameable/2 (every field a scheme can hold), and per raw
% chain: chain_scheme/2, chain_facet/2, chain_walks/3 (relation or sibling),
% chain_output/1, chain_invariant/2.

% ── references ──────────────────────────────────────────────────────────
% A reference may only name a scheme that is declared.
unknown_target(S, F, T) :- ref_target(S, F, T), not scheme(T).

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

% ── chains ──────────────────────────────────────────────────────────────
chain_unknown(N) :- chain_scheme(N, S), not scheme(S).
facet_unheld(N, X) :- chain_facet(N, X), chain_scheme(N, S), scheme(S),
                      not nameable(S, X).
% A chain walks references, and only within its own scheme.
walk_undeclared(N, K, F) :- chain_walks(N, K, F), chain_scheme(N, S),
                            scheme(S), not ref(S, F).
walk_leaves(N, K, F) :- chain_walks(N, K, F), chain_scheme(N, S),
                        ref_target(S, F, T), T != S.
output_missing(N) :- chain_scheme(N, S), scheme(S), not chain_output(N).
chain_invariant_unheld(N, I) :- chain_invariant(N, I), chain_scheme(N, S),
                                scheme(S), not nameable(S, I).

#show unknown_target/3.
#show converse_missing/3.
#show converse_elsewhere/3.
#show converse_unrequited/3.
#show converse_single/5.
#show invariant_unheld/3.
#show chain_unknown/1.
#show facet_unheld/2.
#show walk_undeclared/3.
#show walk_leaves/3.
#show output_missing/1.
#show chain_invariant_unheld/2.
