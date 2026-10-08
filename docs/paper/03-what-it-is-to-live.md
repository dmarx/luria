<!-- docs/paper/03-what-it-is-to-live.md -->
<!-- inactive-ok-file: ADR-058 — Rejected as a README headline; the downstream-adoption figures it records are cited as evidence -->

# What it is for a corpus to live

## Not growth, and not editing

The obvious candidate for liveness is change. Lehman's laws of software
evolution say that a program used in the real world must be continually
adapted or become progressively less satisfactory (Lehman 1980), and a corpus
that people rely on is under the same pressure: its subject moves, so it must.
But change alone cannot be the criterion. A wiki that is edited daily and a
document store that only grows both change constantly, and both can be dead in
the sense that matters, because neither can say what it currently holds or how
it came to hold it. The palimpsest of the introduction is the most frequently
edited kind of corpus and the least accountable.

The criterion has to be about what the corpus does *when something changes*,
not about how often it does.

## Staleness is a Cambridge change

Peter Geach distinguished real change from what he called "mere Cambridge
change": Socrates becomes shorter than Theaetetus when Theaetetus grows,
without Socrates having altered at all (Geach 1969). A relational predicate
begins to apply to a thing because something else moved.

Staleness is a Cambridge change. When the decision a sentence rests on is
retired, the sentence acquires a new property, *resting on something no longer
held*, and acquires it without any change in the sentence. This is why the
standard instruments of document hygiene fail here. Modification times, diffs,
and blame all measure change in the *intrinsic* state of a file. The change
that matters occurred in a different file, and the file it affects is the one
those instruments report as quiet.

Two consequences follow. First, the unit of change that a corpus must track is
not the document but the *relation* between documents. A corpus that does not
represent relations cannot, even in principle, notice its most important
changes. Second, the new property is a *question*, not a verdict. Whether a
sentence that cites a retired premise is now false depends on the sentence,
and a bad argument for a conclusion is not a refutation of the conclusion. The
record of one downstream adoption makes the point quantitatively: of seventy
findings in its first wave, forty-two were deliberate citations that were
entirely correct ([ADR-058](../../record/decisions.d/ADR-058.md)). I return to this in
the discussion of judgment, because it is why the tool cannot simply fix what
it finds.

## Why standing matters: the notebook that is believed

Clark and Chalmers argue that Otto's notebook is part of his memory, and that
what he writes in it is among his beliefs, because it is reliably available,
easily accessed, and, crucially, information from it is "automatically
endorsed" when consulted (Clark and Chalmers 1998). The criterion transfers to
a corpus. A project's decision records, runbooks, and reading notes are
consulted in exactly this way, and by collaborators for whom no other memory
exists. A collaborator who arrives with no prior context, as is now routinely
true of software agents and often true of new colleagues, can only know what
the repository says, and the project's own record states this as the premise
of its design: the repository is the next collaborator's mind, reconstituted
from disk ([ADR-001](../../record/decisions.d/ADR-001.md)).

If entries are automatically endorsed, stale entries are not inert. They are
beliefs the project holds without knowing that it holds them. The remedy
cannot be to withdraw the endorsement, since that would defeat the purpose
of the memory. It has to be to make the endorsement *conditional and
visible*: a signal on each entry that says whether it is, at present, the kind
of thing that deserves automatic endorsement, and a mechanism that keeps that
signal honest. That signal is what I call standing.

## Three conditions

I propose that a corpus is *living*, for the purposes of this paper, when it
satisfies three conditions.

**L1. Standing.** Each entry has, in addition to its existence, a current
answer to *is this in force?*, drawn from a declared vocabulary, and the
answer can change without destroying the entry.

**L2. Dependence.** Relations among entries are represented in a form that
lets a change of standing in one entry determine a set of other entries whose
standing is thereby in question.

**L3. Accountability.** Every settlement of such a question leaves a trace at
the place the question arose, with a reason, and a question cannot be left open
silently. A settlement is either a revision of the dependent entry or a
recorded decision that it stands.

Each of the three failures in the introduction fails exactly one or two of
these. The archive has no L1: it keeps everything and gives nothing a
standing. The canon has L1 in a degenerate form, since standing is assigned
once and the answer cannot change, so L2 never has anything to propagate. The
palimpsest has neither L2 nor L3: it revises in place, represents no
dependence, and leaves no trace of what it replaced.

The three conditions jointly yield one operation, which the framework's
documentation states as its engine:

> Change an entry's status, and every citation of it becomes a finding.

This is not a rule about documents. It is what it looks like for a body of
claims to be answerable to its own changes.

## On the word "living"

"Living" invites a comparison with autopoiesis, the property of a system that
produces the components that produce it (Maturana and Varela 1980). A corpus
does not meet that standard. It produces neither its authors nor its readers,
and everything that keeps it coherent is done by people or by tools people
run. I use "living" as a term of art for L1 to L3, and I think the biological
word earns two things beyond a label while costing one.

It earns *homeostasis*: a living corpus holds itself in a declared state of
coherence under perturbation, and a perturbation (a retirement) produces a
corrective response rather than a drift. It earns *metabolism*: different parts
of the corpus turn over at different rates, and the architecture has to
provide for that, which is the subject of the section on forgetting.

What it costs is the suggestion of spontaneity. Nothing here is automatic. The
tool surfaces questions and people answer them, and a living corpus in this
sense is one whose maintenance is *cheap enough to actually be done*, not one
that maintains itself.
