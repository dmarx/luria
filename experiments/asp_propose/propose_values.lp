% experiments/asp_propose/propose_values.lp
% Which values should a document with an empty vocabulary field take? A
% proposal, not a view: choice, constraints and optimisation, read back as
% cautious and brave consequences so the answer is still a function of the
% sources. Needs relations.lp for held/4, and the `values` facts.
%
% Parameters (clingo -c): scheme, field, e.g. -c scheme='"CASE"' -c field='"line"'.

#const scheme = "CASE".
#const field  = "line".

valued(C)  :- value(C, field, _, _).
empty(C)   :- doc(C, scheme), not valued(C).

% Two documents are adjacent when any declared relation joins them, either way.
adj(C, X) :- held(_, _, C, X), C != X.
adj(C, X) :- held(_, _, X, C), C != X.

% What an empty document may take: a value of a valued neighbour, or,
% transitively, anything an empty neighbour may take. Plain recursion,
% computed before any guess, so the guess ranges over a fixed set.
may(C, V) :- empty(C), adj(C, X), value(X, field, _, V).
may(C, V) :- empty(C), adj(C, D), empty(D), may(D, V).

% Guess: each empty document with candidates takes some of them.
{ take(C, V) : may(C, V) } :- empty(C).
:- empty(C), may(C, _), not take(C, _).

% Every neighbour that has (or is given) a value must share one with it.
has(X, V) :- value(X, field, _, V).
has(X, V) :- take(X, V).
shares(C, X) :- empty(C), adj(C, X), take(C, V), has(X, V).
:- empty(C), adj(C, X), has(X, _), not shares(C, X).

% Fewest values in all.
#minimize { 1, C, V : take(C, V) }.

% The silent case gets a signal (DP-015): an empty document with nothing
% to go on is reported, not left out of the answer.
no_evidence(C) :- empty(C), not may(C, _).

#show take/2.
#show no_evidence/1.
