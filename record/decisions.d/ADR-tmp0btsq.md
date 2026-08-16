---
status: Proposed
title: Luria is a truth maintenance system, and should say so
version: 1
tags:
- record
- process
date: '2026-08-16'
summary: >-
  Nobody could name the category, so every description reached for a new
  metaphor and none of them stuck. The category exists and is from 1979:
  a truth maintenance system maintains beliefs plus the justifications
  linking them, and retracting one propagates to everything that rested on
  it. That is the engine, exactly. What is ours is narrow and worth stating
  narrowly — the nodes are human prose, propagation halts at a finding
  instead of resolving itself, and acknowledgement is a first-class move.
  Rejected: claiming a new category, which costs us the prior art.
---

# ADR-tmp0btsq: Luria is a truth maintenance system, and should say so

## Context

This project has never been able to say what it is in one sentence. The
README's banner carries four attempts — a project memory framework, a
priorities accumulator, a reference linter, an evidence accumulator — and each
is true of some part. The repository description takes three clauses. Asked
directly, the answers reached for fresh metaphors: an epistemic linter, a
compiler for culture, a build system for beliefs.

Four descriptions and no name is not a communication problem. It is what
happens when a category is assumed to be new.

**It is not new.** The mechanism has a name, a literature and a fifty-year
history, and using it costs nothing and buys the reader everything.

## Decision

**Luria is a truth maintenance system.** Say so, in those words, in the README
and in the concepts documentation.

A TMS — Doyle, 1979; de Kleer's assumption-based variant, 1986 — maintains a
set of beliefs together with the **justifications** that link them. Each node
is IN or OUT. Retract a belief and the system propagates the retraction to
every node whose justification depended on it. The propagation step is called
dependency-directed backtracking.

That is a description of this package, not an analogy to it. In a downstream
adoption, a scheme's fifty-one records all sat at the in-force status; setting
twenty-three of them to `Rejected` produced twenty-seven findings naming every
argument that had cited one, across files nobody had touched. Same data
structure — justifications with antecedents — and the same operation.

The neighbouring vocabulary is worth naming too, because each is the right
reference for a different reader:

| Read for | Prior art |
|---|---|
| the mechanism | truth maintenance (Doyle 1979; de Kleer 1986) |
| the formal account of retraction | belief revision, AGM (Alchourrón, Gärdenfors & Makinson 1985) — `Rejected` is contraction |
| the industrial cousin | requirements traceability and impact analysis (DOORS, Jama, DO-178C) |
| what the argument schemes are | abstract argumentation (Dung 1995), argument mapping |

**What is ours is narrow, and stating it narrowly is the point.** Three things,
none of which is the mechanism:

1. **The nodes are human-authored documents.** A classical TMS runs over an
   inference engine's output; here the justifications are citations a person
   wrote, in prose, and the graph is a side effect of writing carefully.
2. **Propagation halts at a finding rather than resolving itself.** A TMS marks
   a node OUT automatically. This one fails the build and waits, because
   whether a withdrawn premise kills an argument is a judgment — a bad argument
   for P is not a defeater for P, and the downstream record has live cases in
   both directions.
3. **Acknowledgement is a first-class move.** `inactive-ok: CLM-050 — the claim
   this argument repairs` has no counterpart in a TMS, where a node is IN or
   OUT and "I know, and I am citing it deliberately" is not expressible. This
   is borrowed from linter suppressions rather than invented, and it is what
   makes the propagation survivable: of seventy findings in that first
   downstream wave, forty-two were legitimate deliberate citations.

So the accurate claim is **not** a new category. It is truth maintenance plus
suppression semantics, applied to prose, enforced in CI — a recombination of
three existing things, and useful precisely because nobody had combined them.

## Alternatives considered

- **Claim a new category and name it.** Tempting, and it is what four rounds of
  fresh metaphor were implicitly doing. It costs the prior art: a reader who
  knows what a TMS is understands this package in one sentence, and inventing a
  word denies them that while asking them to take the novelty on faith. It also
  invites the wrong questions — anyone who *does* know the literature will spend
  their first hour working out whether we know it too.
- **"Epistemic linter."** The closest of the coinages and the most misleading
  half. `linter` is right about the surface — a check that fails a build — and
  wrong about the operation: a linter checks a file against rules that do not
  change, and never propagates anything. What happened downstream was not that
  a file broke a rule; it was that one field changed and consequences appeared
  in files nobody had opened.
- **Lead with "project memory framework."** True, and it describes the
  packaging rather than the engine. Scaffolding and view generation are means —
  a cookiecutter and a static-site generator also do them — and leading with
  them is why the current description needs three clauses to arrive.
- **Say nothing and let the tool speak.** What we have been doing. The cost is
  measurable in this record: four descriptions, none load-bearing, and a
  recurring inability to answer the first question anyone asks.

## Consequences

The documentation leads with the mechanism — *retract a premise, and the build
names everything that rested on it* — and gives TMS as the second sentence, so
the reader who knows the literature is oriented immediately and the reader who
does not is not blocked by jargon.

We inherit a literature we should now be answerable to. An ATMS maintains
multiple simultaneous contexts, which this package cannot; AGM's postulates
describe properties of contraction that our `Rejected` does not obviously
satisfy. Both are now legitimate questions to be asked, and being asked them is
better than being unplaceable.

The status field is revealed as the load-bearing part rather than one field
among several. Without a status that moves, the justification graph is inert
and the package degenerates into a documentation generator — which is exactly
what the `inert-status` report detects, and this decision is why that check
matters more than its size suggests.
