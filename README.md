<p align="center">
  <img src="assets/branding/luria-brainslug/luria_project_memory_lockup_horizontal.svg"
       alt="Luria — project memory" width="480">
</p>

<!-- luria:badges -->
[![needs decision: 4](https://img.shields.io/badge/needs%20decision-4-orange)](docs/reports/pending-decisions.md)
[![cited, not in force: 1](https://img.shields.io/badge/cited,%20not%20in%20force-1-orange)](docs/reports/reference-status.md)
<!-- /luria:badges -->

<!-- luria:site -->
📖 **[dmarx.github.io/luria](https://dmarx.github.io/luria/)** — this record, published by `luria site`.
<!-- /luria:site -->

---

# Luria

**Give a body of knowledge an explicit internal logic.**

Luria is a framework for building **governed knowledge records**.

A record might describe:

- the architecture of a software system,
- the state of a scientific literature,
- a collection of standards,
- an investigation,
- institutional policy,
- an operational environment,
- a historical corpus,
- a set of design principles,
- or any other body of knowledge that needs to remain meaningful as it changes.

Luria lets you make explicit:

- what kinds of claims the record contains,
- how those claims relate,
- what gives them standing,
- which distinctions matter,
- what counts as evidence,
- which states and transitions are valid,
- which artifacts are authoritative,
- which views are derived,
- and what should happen when the record's own conceptual scheme needs to change.

The result is more than structured documentation.

It is a body of knowledge with a theory of itself.

---

## The problem

Most knowledge systems are good at storing assertions.

They are much worse at preserving their meaning under change.

Suppose a document says:

```text
Writes are retried because ADR-012 requires at-least-once delivery.
```

Later, [ADR-012](record/decisions.d/ADR-012.md) is superseded.

Nothing happened to the sentence.

The file still exists.  
The Markdown still renders.  
The reference still looks plausible.

But the epistemic state of the system changed.

The sentence depended on something that no longer has the same standing.

Luria is built around making changes like that visible.

But stale references are only one instance of the more general problem.

A research recommendation may remain in an anthology after its supporting literature has been reinterpreted.

A policy may continue to cite a rule that has been withdrawn.

A taxonomy may force new observations into categories that no longer fit.

A generated summary may drift from the sources from which it was supposedly derived.

A procedure may survive long after the constraint that justified it disappeared.

A body of knowledge can remain perfectly readable while becoming internally incoherent.

Luria exists to make that coherence inspectable.

---

# A record is a knowledge system

The simplest mental model is:

\[
\mathcal K = (O, M, R, E)
\]

where:

- \(O\) is the **ontology** of the record,
- \(M\) is its **record theory**,
- \(R\) is its **knowledge state**,
- \(E\) is the **machinery** that checks and derives consequences from the first three.

You do not need to think in this notation to use Luria.

But it captures the architecture.

---

## \(R\): the knowledge record

\(R\) is what the record says about its subject.

Examples:

```text
Use PostgreSQL for durable application state.
```

```text
Paper X provides evidence for technique Y.
```

```text
This incident began at 14:32 UTC.
```

```text
The committee adopted policy Z in 2024.
```

```text
This practice is currently recommended.
```

These are ordinary claims about some domain.

Luria stores them in small, human-readable source files with stable identities and explicit structure.

---

## \(O\): the ontology

The ontology specifies the kinds of things the record knows how to distinguish.

For one record, that might be:

```text
Decision
Principle
Incident
Runbook
```

For another:

```text
Paper
Recommendation
Theory
Reading note
```

For another:

```text
Policy
Proposal
Interpretation
Case
```

The ontology also includes distinctions *within* those kinds.

A research anthology, for example, may need to distinguish:

```text
Is this paper worth retaining?
```

from:

```text
Is the recommendation supported by this paper still current?
```

from:

```text
Do we believe this explanatory theory?
```

from:

```text
Does the wider field agree?
```

Those are different predicates over different objects.

Luria lets a record preserve those distinctions instead of flattening them into a generic `status` field whose meaning changes silently from one context to another.

---

## \(M\): the record theory

Some knowledge is not about the record's subject.

It is about **how the record itself should behave**.

For example:

```text
A changed decision must supersede the previous decision rather than rewrite it.
```

```text
A recommendation requires supporting evidence.
```

```text
An inactive authority may only be cited from an explicitly historical context.
```

```text
Generated views are derivative and must not become competing sources of truth.
```

```text
If a real observation does not fit the taxonomy, revise the taxonomy rather than misclassifying the observation.
```

```text
A normative prohibition should identify an actual enforcement mechanism.
```

These are not ordinary metadata.

They are rules over the knowledge system.

Call the collection of such rules \(M\), the **record theory**.

Then a useful way to describe Luria is:

\[
M \vdash R
\]

> Under this record theory, this knowledge state is admissible.

For a transition:

\[
M \vdash R_t \xrightarrow{\Delta} R_{t+1}
\]

> Under this record theory, this change is admissible.

This distinction is fundamental.

A record does not merely have structure.

It has **laws of change**.

---

## \(E\): executable semantics

Not every principle in a record theory can or should become code.

Some can.

Luria makes part of \(M\) executable.

For example:

```text
Every SOTA recommendation must cite at least one literature record.
```

can become a lint rule.

A rule like:

```text
When a new phenomenon does not fit the existing taxonomy,
prefer revising the taxonomy to distorting the observation.
```

may remain discursive.

So in practice:

\[
M =
M_{\text{executable}}
+
M_{\text{discursive}}
\]

This is intentional.

A knowledge system needs both:

- machine-checkable invariants,
- and reasoned principles whose interpretation still requires judgment.

Luria lets those coexist in the same governed record.

---

# The important unit is not the file

Luria uses plain files.

That is an implementation choice, not the abstraction.

The abstraction is the **record**.

A record contains identifiable objects with semantics.

A typical object may have:

- an identity,
- a kind,
- a status,
- structured fields,
- categories,
- references,
- provenance,
- relationships,
- and a body of prose.

For example:

```yaml
---
id: SOTA-017
status: Active
topic: inference
sources:
  - LIT-042
  - LIT-071
---

Prefer technique X when ...
```

The important thing is not that this happens to be Markdown with YAML front matter.

The important thing is that the record knows what `SOTA-017` *is*, what `Active` means for this kind of object, what relationship `sources` expresses, and what conditions make that object valid.

---

# Different kinds of knowledge should remain different

A recurring failure mode in knowledge systems is to collapse distinct epistemic questions into one axis.

Luria encourages the opposite.

Suppose a record contains a scientific paper and a recommendation derived from it.

The paper can remain historically important:

\[
\mathrm{status}_{LIT}(p)=\mathrm{Active}
\]

while a recommendation based on it becomes obsolete:

\[
\mathrm{status}_{SOTA}(r)=\mathrm{Superseded}.
\]

Those statements are perfectly compatible.

Likewise:

\[
\mathrm{status}(x)=\mathrm{Active}
\]

may coexist with:

\[
\mathrm{consensus}(x)=\mathrm{Contested}.
\]

A theory can be rejected while the phenomenon it attempted to explain remains real.

A policy can remain historically significant after it ceases to govern.

A decision can remain part of the record after the project stops endorsing it.

These distinctions are easy to describe in prose and surprisingly easy to lose in practice.

A governed record makes them structural.

---

# Identity is not standing

Luria distinguishes:

> Does this object exist?

from:

> What standing does it currently have?

Those are different questions.

A decision may be:

```text
ADR-012
```

for its entire lifetime.

Its standing may evolve:

```text
Proposed
    ↓
Active
    ↓
Superseded
```

Retiring the decision does not erase it.

Its history remains available.

This allows a record to preserve both:

1. what was once believed or adopted,
2. what is endorsed now.

Without that distinction, systems tend toward one of two pathologies:

- delete obsolete knowledge and lose history,
- retain obsolete knowledge and make current authority ambiguous.

Luria keeps history without pretending history is current truth.

---

# References are claims

In Luria, a reference is more than a string that happens to resolve.

It is a dependency.

Suppose:

```text
We do X because ADR-012 requires Y.
```

This implies something like:

\[
\mathrm{claim}
\xrightarrow{\mathrm{depends\ on}}
\mathrm{ADR\text{-}012}
\]

and frequently something stronger:

\[
\mathrm{claim}
\xrightarrow{\mathrm{depends\ on\ ADR\text{-}012\ being\ active}}
\mathrm{ADR\text{-}012}.
\]

If [ADR-012](record/decisions.d/ADR-012.md) changes standing, the referencing text may need reconsideration even though nobody touched it.

That is the point.

A knowledge system should be able to tell the difference between:

```text
this reference still resolves
```

and:

```text
this reference still justifies the claim being made.
```

---

# Invalidity should propagate

A powerful property of formal systems is that changing a premise can invalidate its dependents.

Luria brings a lightweight version of that property to human-readable knowledge.

At time \(t\):

\[
M;R_t \vdash c
\]

A claim \(c\) is acceptable under the current record.

Then some premise changes.

At time \(t+1\):

\[
M;R_{t+1} \nvdash c.
\]

The text of \(c\) may be identical.

Its context changed.

Luria surfaces that.

This is one of the central ideas behind `luria lint`.

---

# Linting is knowledge checking

Run:

```bash
luria lint
```

The interesting question is not:

> Is the Markdown pretty?

It is:

> Does this record still satisfy the rules it says matter?

Depending on the record, lint can ask things like:

- Does this identifier resolve?
- Is this referenced object still active?
- Is this status legal for this scheme?
- Is a required relation missing?
- Does every recommendation have evidence?
- Does this object have exactly one primary category?
- Has a generated view drifted from its sources?
- Does this constraint claim enforcement that does not actually exist?
- Has an exception been explicitly justified?

The general shape is:

\[
M;R \vdash x\ \mathrm{valid}
\]

or:

\[
M;R \nvdash x\ \mathrm{valid}.
\]

Luria is not a theorem prover.

But this is closer in spirit to type checking than to ordinary documentation linting.

---

# Change has semantics

Version control tells you that a file changed.

It does not tell you what kind of epistemic change occurred.

Consider these two operations.

### Revision

```text
The choice is unchanged.
The record of its rationale was inaccurate.
```

### Supersession

```text
The system has made a different choice.
```

Both can appear in Git as edits to Markdown.

They mean radically different things.

A governed record can distinguish:

\[
\operatorname{revise}(x)
\]

from:

\[
\operatorname{supersede}(x).
\]

Likewise:

- correcting provenance,
- withdrawing a recommendation,
- changing a taxonomy,
- replacing a policy,
- generating an index,
- resolving a temporary identity,
- adding an exception,
- adopting a proposal,

are different transformations.

Luria's model gives those transformations somewhere to acquire explicit semantics.

---

# A record can govern itself

Once a record contains rules about how the record itself should evolve, the system becomes reflective.

Suppose \(M\) contains:

```text
Process decisions must themselves be superseded rather than silently rewritten.
```

That rule governs changes to the same class of knowledge to which it belongs.

Conceptually:

\[
M \vdash M.
\]

Not in the unrestricted logical sense.

In the practical sense that a knowledge system may contain **rules for amending its own rules**.

This matters because otherwise governance tends to escape the system it governs.

The real rules end up scattered across:

- maintainer memory,
- CI configuration,
- contribution guides,
- scripts,
- review habits,
- old discussions,
- conventions,
- and undocumented precedent.

A self-governing record brings those rules into the same historical and inspectable system as everything else.

---

# The ontology can change too

Luria does not require the conceptual scheme to be treated as infallible.

Suppose a record uses a closed vocabulary:

```text
training
inference
evaluation
systems
```

and a legitimate new object does not fit.

There are two possible responses.

The bad response:

```text
force it into the nearest category
```

The better response may be:

```text
the ontology no longer describes the domain adequately
```

and therefore:

\[
O_t \rightarrow O_{t+1}.
\]

This gives a useful feedback loop:

\[
O_t,M_t \vdash R_t
\]

but anomalies in \(R_t\) can motivate changes to \(O\) or \(M\):

\[
(O_t,M_t,R_t)
\rightarrow
(O_{t+1},M_{t+1},R_{t+1}).
\]

The record and the conceptual scheme used to understand it can coevolve.

That is often what serious knowledge work actually requires.

---

# Sources and views

A maintained knowledge system needs a direction of authority.

Luria distinguishes **sources** from **derived views**.

Conceptually:

\[
R
\xrightarrow{\operatorname{derive}}
V.
\]

For example:

```text
record/decisions.d/*.md
        ↓
docs/decisions/index.md
```

or:

```text
individual changelog fragments
        ↓
CHANGELOG.md
```

or:

```text
source records
        ↓
published site
```

The direction matters.

A derived artifact should not quietly become an independent second source of truth.

So Luria follows the rule:

> edit sources; regenerate views.

This gives the system one authoritative direction and prevents semantic fork.

Run:

```bash
luria index
```

to rebuild generated views.

---

# Exceptions are evidence

Rules that cannot admit exceptions are usually too rigid for real knowledge work.

But exceptions that merely disable checking destroy information.

Luria prefers local, explicit acknowledgements.

For example:

```html
<!-- inactive-ok: ADR-012 — this section describes the historical design -->
```

This says more than:

```text
ignore the warning
```

It records:

1. that the exceptional condition is known,
2. where it applies,
3. why it is intentional.

Conceptually:

\[
\frac{
x : \mathrm{NormallyInvalid}
\qquad
j : \mathrm{Justification}(x)
}{
x : \mathrm{Accepted}
}
\]

An exception should carry evidence.

---

# Plain text is a feature

Luria records live in ordinary repositories.

Sources are intentionally:

- readable,
- diffable,
- searchable,
- version-controlled,
- editable with normal tools,
- reviewable in ordinary pull requests,
- and accessible to both humans and agents.

There is no database you must trust with the only copy of the record.

There is no proprietary editor required to understand it.

There is no export step between the knowledge system and the repository that contains the work.

The files are yours.

Markdown is the primary representation today, but the model is not fundamentally about Markdown.

It is about identity, semantics, relations, standing, and governed change.

---

# Records can describe almost anything

The same machinery can support very different knowledge systems.

## Software architecture

```text
ADR       architectural decisions
PRINCIPLE design constraints
RFC       proposals
INCIDENT  operational history
RUNBOOK   active operational knowledge
```

Rules might include:

```text
Superseded decisions cannot silently justify current implementation.

Every normative principle must name its enforcement mechanism.

Runbooks citing retired infrastructure decisions require review.
```

---

## Research anthology

```text
LIT       papers and other evidence
SOTA      current recommendations
THEORY    explanatory accounts
NOTE      reading and synthesis notes
```

Rules might include:

```text
Every SOTA recommendation requires evidence.

The standing of evidence is independent of the standing of a recommendation.

Field consensus is distinct from editorial endorsement.

Reading depth is distinct from evidentiary relevance.
```

A foundational paper may remain important while a recommendation derived from it becomes obsolete.

The ontology can express that without contradiction.

---

## Standards registry

```text
PROPOSAL
STANDARD
INTERPRETATION
IMPLEMENTATION
```

Rules might include:

```text
An implementation declares which standard revision it conforms to.

A superseded standard remains citable from historical material.

Interpretations must identify the text they interpret.
```

---

## Policy corpus

```text
POLICY
AUTHORITY
INTERPRETATION
EXCEPTION
CASE
```

The relevant question may not merely be whether a document exists.

It may be whether it remains authoritative for a particular use.

---

## Investigation

```text
CLAIM
EVIDENCE
SOURCE
HYPOTHESIS
FINDING
```

Different status axes can separate:

```text
credibility of a source
```

from:

```text
confidence in a claim
```

from:

```text
current status of a hypothesis.
```

Those distinctions can evolve independently.

---

## Historical corpus

```text
EVENT
SOURCE
PERSON
CLAIM
INTERPRETATION
```

A record can distinguish:

```text
this source asserted X
```

from:

```text
the record endorses X.
```

Preserving that distinction is often the whole point.

---

# Define the record in `luria.yaml`

A Luria deployment begins with a configuration describing the families that make up the record.

For example, schematically:

```yaml
schemes:
  lit:
    prefix: LIT
    path: record/literature.d

  sota:
    prefix: SOTA
    path: record/sota.d

  theory:
    prefix: THEORY
    path: record/theories.d
```

Each scheme can give its objects their own:

- identities,
- statuses,
- fields,
- vocabularies,
- constraints,
- generated views,
- and relations.

The point is not to discover the one correct universal schema.

The point is to make **this record's distinctions explicit**.

`ADR` is not the essence of Luria.

Neither is `SOTA`, `RFC`, `POLICY`, or `LIT`.

They are inhabitants of record theories you define.

---

# The meta-record

For simple deployments, the rules governing a record can live alongside the subject-level knowledge.

For larger ones, it can be useful to think explicitly in terms of two records:

```text
meta/
subject/
```

where:

\[
R = \text{knowledge about the subject}
\]

and:

\[
M = \text{knowledge governing how }R\text{ is represented and changed}.
\]

This separation does not have to be physical.

It is first a semantic distinction.

But making it explicit can reveal useful questions:

- May subject-level facts justify changes to record-level rules?
- Which rules are allowed to depend on which other rules?
- What happens when a governing rule changes?
- Which parts of the record must be reconsidered?
- How are amendments to the meta-record itself governed?
- Which rules are executable, and which remain interpretive?

A mature Luria system often develops some form of this second level whether or not it is initially named.

---

# Installation

Luria requires Python 3.11 or later.

```bash
pip install luria
```

---

# Sixty seconds

From a repository:

```bash
luria init --dry-run
```

See what Luria would add.

Then:

```bash
luria init
```

Build the generated views:

```bash
luria index
```

Create an entry in the default journal:

```bash
luria new --title "Observed a new constraint"
```

Create a decision:

```bash
luria new adr --title "Consumers must be idempotent"
```

Then check the record:

```bash
luria index
luria lint
```

A healthy record reports clean.

As the record changes, the same checks become more interesting.

Supersede a decision.

Change a controlled vocabulary.

Remove required evidence.

Retire something that current prose still relies on.

Luria makes the consequences visible.

---

# Typical layout

A software-oriented record might look like:

```text
luria.yaml

record/
  decisions.d/
    ADR-001.md
    ADR-002.md

  principles.d/
    DP-001.md

  devlog.d/
    2026/
      09/
        27/
          013200.md

  changelog.d/
    fix-api-timeout.md

docs/
  decisions/
    index.md          # generated
    tags/             # generated

  design-principles.md # generated

  devlog/              # generated

  reports/             # generated

CHANGELOG.md            # assembled
```

A research record might instead look like:

```text
luria.yaml

record/
  literature.d/
    LIT-001.md
    LIT-002.md

  sota.d/
    SOTA-001.md

  theories.d/
    THEORY-001.md

  notes.d/
    NOTE-001.md

docs/
  literature/          # generated
  sota/                # generated
  theories/            # generated
```

The engine is the same.

The knowledge system is different.

---

# Record families

Luria provides several general families of source material.

## Schemes

Schemes are referable objects with stable identities.

Examples:

```text
ADR-012
LIT-042
RFC-7
POLICY-19
```

They can have standing, fields, constraints, categories, and relations.

Use them for knowledge whose identity matters across time.

---

## Journals

Journals represent dated observations.

A journal entry is usually true *of the moment in which it was recorded*.

Unlike a decision, an old journal entry need not become “inactive.”

It says:

> this happened, or this was observed, then.

That is a different epistemic type from:

> this is currently endorsed.

Luria keeps the distinction explicit.

---

## Fragment directories

Some documents are best authored distributively and assembled later.

A changelog is the canonical example.

Instead of many branches editing one shared file:

```text
CHANGELOG.md
```

they contribute fragments:

```text
changelog.d/
  added-x.md
  fixed-y.md
  deprecated-z.md
```

Luria can collect them into a derived artifact.

---

## Remotes

Not every identity belongs to the local record.

A record may cite:

- another Luria record,
- arXiv identifiers,
- issue keys,
- external standards,
- or some other namespace.

Remotes bring those identities into the citation graph without pretending the local repository owns them.

---

# Generated views

Source files optimize for authorship.

Readers often want different structures:

- indexes,
- tag pages,
- status reports,
- concatenated documents,
- backlinks,
- graphs,
- sites,
- summaries.

Luria generates those from the source record.

```bash
luria index
```

The generated views are disposable.

The sources are authoritative.

That asymmetry is deliberate.

---

# The citation graph

Stable identities allow knowledge to form a graph.

A record may contain edges like:

\[
\mathrm{SOTA\text{-}17}
\rightarrow
\mathrm{LIT\text{-}42}
\]

\[
\mathrm{ADR\text{-}31}
\rightarrow
\mathrm{DP\text{-}4}
\]

\[
\mathrm{POLICY\text{-}8}
\rightarrow
\mathrm{AUTHORITY\text{-}2}.
\]

These relations are useful for more than navigation.

They let the system ask:

> What rests on this?

That becomes especially important when the target changes.

A knowledge graph becomes much more valuable when edges have consequences.

---

# Reports

Run:

```bash
luria reports
```

to inspect findings surfaced from the record.

Reports turn implicit inconsistencies into explicit work.

That work may be:

```text
update this claim
```

or:

```text
acknowledge that the historical reference is intentional
```

or:

```text
supply missing evidence
```

or:

```text
amend the ontology
```

or:

```text
change the rule because the rule is wrong
```

The checker is not the final authority.

The record is allowed to learn.

---

# Human judgment remains part of the system

Luria does not try to formalize away interpretation.

That would be both unrealistic and undesirable for most knowledge systems.

Instead, it tries to separate:

```text
things the machine can check
```

from:

```text
things humans still need to reason about
```

without pretending the second category does not exist.

A useful record theory often says:

> this condition should trigger review

rather than:

> this condition mathematically determines the correct answer.

Luria is machinery for maintaining epistemic discipline, not replacing epistemic judgment.

---

# Why this matters for AI agents

Generative models make producing artifacts cheap.

Maintaining coherent knowledge is still expensive.

An agent can generate:

- documentation,
- analysis,
- policies,
- code,
- summaries,
- recommendations,
- literature syntheses,
- plans,

very quickly.

But generation is not the same as maintaining standing.

An agent working from a directory full of text still has to infer:

- which sources are authoritative,
- which claims are current,
- which conclusions were superseded,
- which distinctions are intentional,
- what evidence supports what,
- what rules govern changes,
- which generated artifacts are merely projections.

Luria makes more of that environment explicit.

Instead of giving an agent only documents to search, a Luria record can give it:

- typed identities,
- explicit relations,
- current standing,
- provenance,
- controlled vocabularies,
- validity constraints,
- and a recorded theory of how the knowledge is meant to evolve.

The difference is between:

> retrieve relevant text

and:

> reason inside a maintained epistemic context.

---

# Luria is not

## A wiki

A wiki stores and links pages.

Luria cares about what the links mean when the objects they refer to change.

## A database

A database can store every field Luria stores.

That does not by itself give those fields a repository-native history, human-readable rationale, laws of transition, or semantics of standing.

## A knowledge graph

Luria can produce a graph.

The graph is not the point.

The point is that nodes and edges participate in a governed record.

## A documentation generator

Luria generates documentation views.

Those are projections of the record, not the record itself.

## An ADR tool

ADRs are one useful instance of a scheme.

Luria has no commitment to software architecture as its domain.

## A theorem prover

Luria can make some knowledge rules executable.

It does not require the whole record to become a formal logic.

## A memory system

A Luria record remembers things, but retention is only one property.

The more interesting property is that remembered knowledge has **standing, relations, and laws of change**.

---

# Design principles

## Preserve identity through change

Changing standing should not require destroying history.

## Keep epistemic axes separate

Evidence, endorsement, consensus, confidence, relevance, and recency are not interchangeable.

## Make dependencies visible

When a premise changes, the things relying on it should become inspectable.

## Prefer explicit laws to folklore

If a convention matters repeatedly, give the record a way to represent it.

## Make enforceable rules executable

When a rule can be checked mechanically, let the machine carry that burden.

## Keep judgment where judgment belongs

Not every important principle should be reduced to a boolean validator.

## Make exceptions informative

An exception should explain why it is legitimate, not merely silence a check.

## Preserve the distinction between source and projection

Generated convenience should not become accidental authority.

## Let the ontology evolve

If reality stops fitting the model, changing the model must remain a legitimate operation.

## Record the process that governs the record

A knowledge system should be able to explain how its own rules came to be.

## Keep the substrate ordinary

The record should remain inspectable with a text editor, Git, grep, and standard repository tooling.

---

# A deeper interpretation

Luria can be thought of as a lightweight two-level system.

At one level:

\[
R
\]

contains claims about some subject.

At another:

\[
M
\]

contains claims about how claims in \(R\) should be formed, interpreted, related, and transformed.

So judgments take the shape:

\[
M;R \vdash x.
\]

This resembles ideas from type systems, modal logic, truth-maintenance systems, configuration languages, knowledge representation, and formal methods.

But Luria deliberately remains much less formal than any of them.

The analogy is useful because it highlights a central idea:

> correctness is contextual.

A statement can remain textually identical while becoming invalid because its premises, authority, or surrounding theory changed.

Luria gives ordinary knowledge records a way to notice.

---

# Where to begin

Do not begin by designing the perfect ontology.

Start with knowledge that already matters.

Maybe that is:

```text
decisions
```

or:

```text
papers
```

or:

```text
policies
```

Give the important objects stable identities.

Give them explicit standing.

Make their important relationships referable.

Add one invariant that you currently enforce by memory.

Then run:

```bash
luria lint
```

Eventually, patterns emerge.

You discover that some facts are observations while others are commitments.

You discover that one `status` field was secretly answering three different questions.

You discover that certain references imply stronger dependencies than hyperlinks capture.

You discover rules for how the record changes.

Write those down too.

At that point you are no longer merely collecting information.

You are constructing a governed knowledge system.

---

# The end state

Imagine a corpus in which:

- claims have stable identity,
- different epistemic roles remain distinct,
- evidence relationships are explicit,
- current standing is distinguishable from historical existence,
- references can become invalid when their premises change,
- changes have semantics beyond file diffs,
- generated views cannot silently acquire authority,
- exceptions preserve reasons,
- the ontology can evolve when it stops fitting the subject,
- rules about maintaining the record are themselves part of the record,
- and machines can check the parts of that theory that are executable.

At that point, the repository is doing something more interesting than storing documents.

It is maintaining an evolving model of what it knows, why it knows it, what it currently endorses, and how those judgments are allowed to change.

That is Luria.

---

## Documentation

- **Quickstart** — build and lint a record from an empty repository.
- **Concepts** — identities, standing, references, sources, and views.
- **Designing a record** — choose schemes, epistemic axes, relations, and constraints.
- **Configuration reference** — the complete `luria.yaml` schema.
- **CLI reference** — commands and flags.
- **Comment directives** — acknowledge intentional exceptions locally.
- **Adopting Luria** — introduce a record into an existing repository.
- **Importing an existing corpus** — turn existing structured material into a governed record.

---

## Citing Luria

```bibtex
@software{marx_luria,
  author  = {Marx, David},
  title   = {Luria},
  url     = {https://github.com/dmarx/luria},
  license = {MIT},
}
```

---

## License

MIT.

---

**Luria — governed knowledge, kept coherent under change.**

---

## Documentation

- [Quickstart](docs/quickstart.md) — from empty repository to linted record.
- [Concepts](docs/concepts.md) — entries, citations, and the one operation
  everything else is machinery around.
- [Designing a record](docs/modeling.md) — what belongs in one, which family
  fits, when two kinds of entry are two schemes, and what the schema can be
  made to refuse.
- [Project memory](docs/project-memory.md) — sources and views, schemes, journals,
  fragments, remotes, statuses, constraints, and how references work.
- [CLI reference](docs/cli.md) — every command and flag.
- [Comment directives](docs/directives.md) — acknowledging a finding where
  it happens instead of silencing the check.
- [Adopting Luria](docs/adopting.md) — scaffolding an existing project,
  wiring up CI, publishing the site.
- [Importing an existing corpus](docs/importing.md) — when the material
  already exists as data, and what the transform will surface.
- [Configuration reference](docs/configuration.md) — generated from the
  schema, every key with its default.

And the record itself, dogfooded: [decisions](docs/decisions/README.md) ·
[design principles](docs/design-principles.md) ·
[development log](docs/devlog/README.md) ·
[status reports](docs/reports/pending-decisions.md).

## Citing Luria

<!-- luria:citation -->
```bibtex
@software{marx_luria,
  author  = {Marx, David},
  title   = {Luria: project memory, kept honest by lint},
  url     = {https://github.com/dmarx/luria},
  license = {MIT},
}
```
<!-- /luria:citation -->

Derived from [`CITATION.cff`](CITATION.cff) by `luria index`, which is also
what GitHub reads for its *Cite this repository* button — so the two cannot
disagree. Add `version = {...}` for the release you used; `pip show luria`
prints it. Nothing pins one here, because a version written into a file by
hand is a copy of the release tag, which is the drift [DP-3](record/principles.d/DP-003.md) names and [ADR-053](record/decisions.d/ADR-053.md)
removed.

## License

[MIT](LICENSE).
