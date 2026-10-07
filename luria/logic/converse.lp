% luria/logic/converse.lp
% A relation and its converse: what `luria link --fix` writes or removes to
% make the two sides of a declared pair agree, and what it refuses to touch.
% See luria/relations.py for the reasoning; this program decides it.
%
% A pair is P = (S, F, B, T): field F on scheme S, whose converse B lives on
% scheme T. An edge (A, X) runs from a document A of S to a document X of T.

pair(S, F, B, T) :- ref_converse(S, F, B), ref_target(S, F, T), scheme(T).

% The two sides as the working tree holds them, and as HEAD did.
now_f(S, F, B, T, A, X) :- pair(S, F, B, T), ref_value(A, F, X),
                           doc(A, S), doc(X, T).
now_b(S, F, B, T, A, X) :- pair(S, F, B, T), ref_value(X, B, A),
                           doc(X, T), doc(A, S).
was_f(S, F, B, T, A, X) :- pair(S, F, B, T), head_value(S, F, A, X),
                           doc(A, S), doc(X, T).
was_b(S, F, B, T, A, X) :- pair(S, F, B, T), head_value(T, B, X, A),
                           doc(X, T), doc(A, S).

now(S, F, B, T, A, X) :- now_f(S, F, B, T, A, X).
now(S, F, B, T, A, X) :- now_b(S, F, B, T, A, X).
seen(S, F, B, T, A, X) :- now(S, F, B, T, A, X).
seen(S, F, B, T, A, X) :- was_f(S, F, B, T, A, X).
seen(S, F, B, T, A, X) :- was_b(S, F, B, T, A, X).

% A directed relation within one scheme asserted both ways: neither document
% is earlier, so there is no side to complete. Reported once, from the lower
% code; a crossing relation cannot express it, since codes name one scheme.
both_ways(S, F, B, S, A, X) :- now(S, F, B, S, A, X), now(S, F, B, S, X, A),
                               F != B.
clash(S, F, B, T, A, X, mutual) :- both_ways(S, F, B, T, A, X), A < X.

% What changed since HEAD, on either side.
added(S, F, B, T, A, X) :- now_f(S, F, B, T, A, X), not was_f(S, F, B, T, A, X).
added(S, F, B, T, A, X) :- now_b(S, F, B, T, A, X), not was_b(S, F, B, T, A, X).
gone(S, F, B, T, A, X) :- was_f(S, F, B, T, A, X), not now_f(S, F, B, T, A, X).
gone(S, F, B, T, A, X) :- was_b(S, F, B, T, A, X), not now_b(S, F, B, T, A, X).

open(S, F, B, T, A, X) :- seen(S, F, B, T, A, X), not both_ways(S, F, B, T, A, X).

% Added on one side and withdrawn on the other: two deliberate edits that
% contradict. Withdrawn: taken from both. Anything else, untouched edges
% included, is written to both — what a corpus predating the fixer needs.
clash(S, F, B, T, A, X, withdrawn) :- open(S, F, B, T, A, X),
                                      added(S, F, B, T, A, X),
                                      gone(S, F, B, T, A, X).
remove(S, F, B, T, A, X) :- open(S, F, B, T, A, X), gone(S, F, B, T, A, X),
                            not added(S, F, B, T, A, X).
write(S, F, B, T, A, X) :- open(S, F, B, T, A, X), not gone(S, F, B, T, A, X).

% Each edit, by side: `near` edits A's field F to name X, `far` edits X's
% converse B to name A.
repair(S, F, B, T, A, X, near, remove) :- remove(S, F, B, T, A, X),
                                          now_f(S, F, B, T, A, X).
repair(S, F, B, T, A, X, far, remove) :- remove(S, F, B, T, A, X),
                                         now_b(S, F, B, T, A, X).
repair(S, F, B, T, A, X, near, add) :- write(S, F, B, T, A, X),
                                       not now_f(S, F, B, T, A, X).
repair(S, F, B, T, A, X, far, add) :- write(S, F, B, T, A, X),
                                      not now_b(S, F, B, T, A, X).

#show repair/8.
#show clash/7.
