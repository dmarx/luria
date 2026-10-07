% luria/logic/relations.lp
% facts: schema documents
% A declared relation, read from either side.
%
% `held(S, F, C, X)`: document C of scheme S stands in relation F to X —
% because C's own field F names X, or because X names C in F's declared
% converse. The union is why a one-sided declaration reads correctly before
% `luria link --fix` has written the other half: completion makes the two
% sides agree on disk, and this makes them agree in every reading meanwhile.

% The schemes a field's codes may land in. A field the scheme does not
% declare as a reference (the built-in successor, read without a
% declaration) lands in the scheme itself.
far(S, F, T) :- ref_target(S, F, T).
far(S, F, S) :- doc(C, S), ref_value(C, F, _), not ref(S, F).

% What one side declares, kept to codes that land on a document of a scheme
% the field may name. A code that resolves to nothing is the contract's
% finding, not an edge.
reads(S, F, C, X) :- doc(C, S), ref_value(C, F, X), far(S, F, T), doc(X, T).

held(S, F, C, X) :- reads(S, F, C, X).
held(S, F, C, X) :- ref_converse(S, F, B), far(S, F, T), reads(T, B, X, C),
                    doc(C, S).

#show held/4.
