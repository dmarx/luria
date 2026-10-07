% luria/logic/invariants.lp
% facts: schema documents
% What a relation asserts, checked against what the fields say (#214).
% Needs relations.lp for held/4. See luria/invariants.py for the findings'
% meaning; this program decides which pairs and lines they are.

% ── a relation's own invariant: the pairs it joins ──────────────────────
rel_pair(S, F, X, Y) :- ref_invariant(S, F, _), held(S, F, X, Y), X <= Y.
rel_pair(S, F, Y, X) :- ref_invariant(S, F, _), held(S, F, X, Y), Y < X.
rel_shares(S, F, A, B) :- rel_pair(S, F, A, B), ref_invariant(S, F, I),
                          holds(A, I, V), holds(B, I, V).
unbound_relation(S, F, A, B) :- rel_pair(S, F, A, B), not rel_shares(S, F, A, B).

% ── a chain's invariant: every edge it walks, spine and sibling alike ───
walks(N, F) :- chain_relation(N, F, _).
walks(N, F) :- chain_sibling(N, F).
near(N, A, B) :- chain(N, S), chain_invariant(N, _), walks(N, F),
                 held(S, F, A, B), doc(A, S), doc(B, S).
near(N, A, B) :- near(N, B, A).

chain_pair(N, A, B) :- near(N, A, B), A <= B.
chain_shares(N, A, B) :- chain_pair(N, A, B), chain_invariant(N, I),
                         holds(A, I, V), holds(B, I, V).
unbound_edge(N, A, B) :- chain_pair(N, A, B), not chain_shares(N, A, B).

% ── and the line: a component holding no value common to every member ───
reach(N, A, A) :- near(N, A, _).
reach(N, A, C) :- reach(N, A, B), near(N, B, C).
member(N, R, A) :- reach(N, A, _), R = #min { B : reach(N, A, B) }.
common(N, R) :- member(N, R, R), chain_invariant(N, I), holds(R, I, V),
                #count { M : member(N, R, M), not holds(M, I, V) } = 0.
unbound_line(N, R) :- member(N, R, R), not common(N, R).

#show unbound_relation/4.
#show unbound_edge/3.
#show unbound_line/2.
#show member/3.
