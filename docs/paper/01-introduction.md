<!-- docs/paper/01-introduction.md -->

# Introduction

Solomon Shereshevsky could not forget. A. R. Luria, who studied him for
roughly three decades, reports a man for whom every experience persisted in
full detail and who, for that reason, could not summarize, abstract, or tell
which of his memories still mattered (Luria 1968). Borges gave the same
predicament to Funes, and put the diagnosis in a sentence: "Pensar es olvidar
diferencias, es generalizar, abstraer" (Borges 1944), which I render as: to
think is to forget differences, to generalize, to abstract. A memory that
keeps everything and distinguishes nothing is not a better memory. It is a
different kind of failure.

Most of what we write down is kept the way Funes kept the world. Decisions,
policies, papers read, claims made, and the reasons for them accumulate in
repositories and wikis that retain every word and judge none of them. The
common complaint is that such collections go stale. That description is
imprecise in a way that matters. Staleness is not something that happens to
a document over time. It is something that happens to a document when
something *else* changes, and a collection that tracks only its own edits
cannot see it.

I distinguish three ways a corpus can fail to be alive.

- **The archive** keeps everything and assigns nothing a standing. Every
  document is equally present and no document is more authoritative than
  another, which is Funes's condition. It can answer *what was written* and
  cannot answer *what do we now hold*.
- **The canon** assigns standing and cannot revoke it. It answers *what do we
  hold* with great confidence, and the answer is whatever was true when the
  canon closed.
- **The palimpsest** revises freely and keeps no account. A wiki page is
  rewritten, a decision is quietly edited, and the corpus is always
  current-looking and never accountable: nothing in it says what it used to
  believe, what replaced it, or who reconsidered what as a result.

A *living* corpus avoids all three. It keeps a record of what it has held, a
current answer to what it holds, and an account of how the second came from the
first. The question for this paper is what has to be true of the *structure*
of a corpus, not of the diligence of its authors, for that to be possible.

## Contribution and scope

The paper makes four claims.

1. **A criterion.** A corpus is living in the relevant sense when it satisfies
   three conditions on standing, dependence, and accountability, stated in the
   section *What it is for a corpus to live*. The criterion is deliberately
   behavioural. It asks what happens when a premise is withdrawn.
2. **A diagnosis.** The conditions can be met only by adding what Hart called
   *secondary rules* to what is otherwise a pile of first-order assertions.
   The section *Secondary rules for knowledge* develops the analogy and marks
   where it fails.
3. **An architecture.** Six distinctions, each of which a living corpus must
   draw and which a conventional collection typically blurs: identity,
   standing and history; dependence and testimony; authority and display;
   finding and judgment; subject-matter and governing knowledge; and the
   different rates at which different parts forget.
4. **A worked example.** Luria, a framework that implements these
   distinctions as plain files and a command-line lint, is introduced early as
   a motivating case and returns throughout as the instance against which the
   distinctions are tested. Its record of its own development is examined as a
   case study.

The paper is conceptual. It does not report a controlled comparison, a user
study, or a measurement of whether corpora maintained this way are more
accurate or cheaper to keep than corpora maintained otherwise. Luria is the
author's project, and its record is evidence that the distinctions can be
implemented and survive use by their implementer, which is weaker than
evidence that they help anyone else. The section on objections returns to this.

The argument is also scoped to corpora made of discrete, citable entries whose
meaning depends on one another. It says nothing about, for instance,
unstructured archives of images or the continuous revision of a single
manuscript.

## Plan

The next section presents Luria through one small scenario in which a sentence
becomes false without being edited. The remaining sections generalize from
that scenario: the criterion, the Hartian diagnosis, the architecture, the
question of forgetting, the evidence from Luria's own record, objections, and
related work.
