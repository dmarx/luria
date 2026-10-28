% luria/logic/reliance.lp
% facts: schema documents
% Needs relations.lp for held/4.
% What rests on a document, along the fields `luria.yaml` names in
% `reliance:` (given as `reliance(F)` facts beside this program).
%
% `relies(A, B, F)`: A holds B in the dependence field F — read through `held/4`,
% so a relation stated only on its converse side counts, exactly as a chain
% or a pattern reads it. `depends(A, B)`: A reaches B along such steps.
% `dependents(B, N)`: N distinct documents depend on B, B itself excluded,
% so a cycle does not count a document as its own dependent.

relies(A, B, F) :- held(_, F, A, B), reliance(F), A != B.

depends(A, B) :- relies(A, B, _).
depends(A, C) :- depends(A, B), relies(B, C, _), A != C.

dependents(B, N) :- doc(B, _), N = #count { A : depends(A, B) }, N > 0.

#show dependents/2.
#show relies/3.
