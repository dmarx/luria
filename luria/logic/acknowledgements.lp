% luria/logic/acknowledgements.lp
% facts: given by luria/ref_status.py, one scan at a time
% Which annotation excuses which citation, and which annotations no longer
% do anything. See luria/ref_status.py for what the three kinds claim; this
% program decides who answers for each site.
%
% Facts: site(I, P, L, C) — the I-th citation found, of code C on line L of
% file P; resolves(C) and active(C) for local documents; ann(A, P, K), the
% A-th annotation found, of kind K, in file P; ann_code(A, C); ann_line(A, L)
% for each line it governs, or ann_file(A) when it governs the whole file;
% ann_problem(A) when it is malformed.

covers(A, L) :- ann(A, P, _), ann_file(A), site(_, P, L, _).
covers(A, L) :- ann_line(A, L).
usable(A) :- ann(A, _, _), not ann_problem(A).

% Every annotation that could answer for a site: same file, names the code,
% governs the line, well formed.
can(I, A, K) :- site(I, P, L, C), ann(A, P, K), usable(A), ann_code(A, C),
                covers(A, L).

% What a site needs excusing for. A code naming nothing here wants an
% `unresolved-ok`; a retired document wants an `inactive-ok`; a document in
% force is no finding, so only a mention is recorded against it — which is
% what keeps that mention alive when its document goes Active (ADR-105).
dangling(I) :- site(I, _, _, C), not resolves(C).
retired(I) :- site(I, _, _, C), resolves(C), not active(C).
wants(I, "unresolved-ok") :- dangling(I).
wants(I, "inactive-ok") :- retired(I).

% The first annotation in the file that claims the site's state answers for
% it; failing one, the first `mention-ok`, which claims nothing and so
% answers either question.
claimed(I) :- can(I, _, K), wants(I, K).
excused(I, A) :- claimed(I), A = #min { B : can(I, B, K), wants(I, K) }.
excused(I, A) :- site(I, _, _, _), not claimed(I),
                 can(I, _, "mention-ok"),
                 A = #min { B : can(I, B, "mention-ok") }.
answered(I) :- excused(I, _).

% An annotation is doing its job while it answers for some site.
used(A) :- excused(_, A).
unused(A) :- usable(A), not used(A).

% What a malformed annotation cost: the sites in its reach, of a code it
% names, in the state its kind would have excused, that nothing answered.
reach(A, I) :- ann(A, P, K), ann_problem(A), site(I, P, L, C), ann_code(A, C),
               covers(A, L).
lost(A, C, I) :- reach(A, I), site(I, _, _, C), not answered(I),
                 ann(A, _, "mention-ok").
lost(A, C, I) :- reach(A, I), site(I, _, _, C), not answered(I),
                 ann(A, _, "unresolved-ok"), dangling(I).
lost(A, C, I) :- reach(A, I), site(I, _, _, C), not answered(I),
                 ann(A, _, "inactive-ok"), retired(I).

#show excused/2.
#show unused/1.
#show lost/3.
