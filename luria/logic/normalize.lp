% luria/logic/normalize.lp
% facts: schema documents
% A directed converse pair stores its primary side alone. What `luria repair`
% does about an entry written on the derived side, and what it refuses to
% touch. See luria/relations.py (`normalizations`) for the reasoning.
%
% A pair is P = (S, F, B, T): the primary field F on scheme S, whose converse
% B on scheme T is marked `derived`. An edge (A, X) runs from a document A of
% S to a document X of T, and is stored as A's F naming X.

pair(S, F, B, T) :- ref_converse(S, F, B), ref_target(S, F, T), scheme(T),
                    ref_derived(T, B), not ref_derived(S, F).

% The edge as the primary side stores it, and as the derived side files it:
% X's B naming A says A's F names X.
stored(S, F, B, T, A, X) :- pair(S, F, B, T), doc(A, S), ref_value(A, F, X),
                            doc(X, T).
filed(S, F, B, T, A, X) :- pair(S, F, B, T), doc(X, T), ref_value(X, B, A),
                           doc(A, S).

% What the primary side would hold once every filed entry moved. A directed
% relation within one scheme held both ways leaves neither document first,
% so a move that would complete such a pair is a contradiction, reported and
% never written — the same line ADR-084 drew for completion.
after(S, F, B, T, A, X) :- stored(S, F, B, T, A, X).
after(S, F, B, T, A, X) :- filed(S, F, B, T, A, X).
both_ways(S, F, B, S, A, X) :- after(S, F, B, S, A, X), after(S, F, B, S, X, A),
                               F != B.

% Filed where the primary already holds it: the derived entry is dropped.
drop(S, F, B, T, A, X) :- filed(S, F, B, T, A, X), stored(S, F, B, T, A, X).
% Filed on the derived side alone: moved to the primary side.
move(S, F, B, T, A, X) :- filed(S, F, B, T, A, X),
                          not stored(S, F, B, T, A, X),
                          not both_ways(S, F, B, T, A, X).
clash(S, F, B, T, A, X) :- filed(S, F, B, T, A, X),
                           not stored(S, F, B, T, A, X),
                           both_ways(S, F, B, T, A, X).

% A derived entry naming no document of any scheme the field may hold: there
% is no other side to write. The contract also reports an unresolvable code;
% this says what normalization did about it, which is nothing.
derived_side(T, B) :- pair(_, _, B, T).
lands(T, B, V) :- derived_side(T, B), ref_value(X, B, V), doc(X, T),
                  ref_target(T, B, S), doc(V, S).
dangling(T, B, X, V) :- derived_side(T, B), doc(X, T), ref_value(X, B, V),
                        not lands(T, B, V).

#show drop/6.
#show move/6.
#show clash/6.
#show dangling/4.
