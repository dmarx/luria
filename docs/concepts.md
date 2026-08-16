# Concepts

What luria is, what the pieces are, and why the status field is the one that
matters.

## The engine

Luria maintains a graph. The nodes are **records** — one file each, hand-written
prose with a little structured frontmatter. The edges are **citations** — one
record naming another by code, in its prose.

Every record has a `status`. One value per scheme is *in force*; the rest mean
the record is retired in some way.

That is the whole model, and everything else is machinery around one operation:

> **Change a record's status, and every citation of it becomes a finding.**

Nothing else in the system creates that effect, and nothing else is as easy to
get wrong — a project whose statuses never move has a graph that never
propagates, which is why `luria lint` reports a scheme where every record shares
one status.

## The prior art

This is a **truth maintenance system**. Doyle described one in 1979: a set of
beliefs plus the justifications linking them, where each node is IN or OUT, and
retracting a belief propagates to everything whose justification depended on it.
de Kleer's assumption-based variant followed in 1986.

Reading the literature is not required to use luria, but it is the fastest way
to understand it, and the vocabulary is worth having:

| For | Look at |
|---|---|
| the mechanism | truth maintenance / reason maintenance (Doyle 1979, de Kleer 1986) |
| the formal account of retraction | belief revision, AGM (Alchourrón, Gärdenfors & Makinson 1985) |
| the industrial cousin | requirements traceability, impact analysis (DOORS, Jama, DO-178C) |
| what argument-shaped schemes are | abstract argumentation (Dung 1995), argument mapping |

Three things here are not in that literature, and they are what make it work on
prose written by people:

**The nodes are documents.** A classical TMS runs over an inference engine's
output. Here the justifications are citations someone wrote, and the graph is a
side effect of citing premises by code rather than by paraphrase. You get it for
free by writing carefully; you lose it by writing "as we decided earlier".

**Propagation halts at a finding.** A TMS marks a node OUT automatically. Luria
does not, because *a bad argument for P is not a defeater for P*. An argument
whose premise you just retracted may still stand on other grounds, and only a
person can tell. So the retraction produces a list, and the list is worked.

**Acknowledgement is a move.** In a TMS a node is IN or OUT; "I know this is
retired and I am citing it deliberately" is not expressible. In luria it is a
comment:

```markdown
<!-- inactive-ok: ADR-012 — the decision this one replaces -->
```

That matters more than it sounds. In one downstream project's first propagation
wave, seventy findings appeared and forty-two of them were correct citations of
retired material — records that exist *to say* what was abandoned. Without a way
to say so, the only way to a green build would have been to un-retire things.

## Records

A record is a markdown file: YAML frontmatter, then prose.

```markdown
---
status: Active
title: Cache invalidation is time-based
version: 1
tags:
- performance
date: '2026-01-14'
---

# ADR-012: Cache invalidation is time-based

## Context
...
```

The **filename is the code and nothing else** — `ADR-012.md`. The title lives in
frontmatter, where fixing it costs an edit rather than a rename plus every
inbound link. `luria lint` checks that the frontmatter title and the body
heading agree, because two copies of one string drift.

Frontmatter is *data*; the body is *prose*. The generated index is built from
the frontmatter, so anything a reader should be able to browse by has to be a
field.

## Status

The vocabulary is closed to five words, checked by the lint:

`Active` · `Proposed` · `Deferred` · `Superseded` · `Rejected`

optionally followed by ` — a short note` (`Superseded — by ADR-030`).

It is closed because an audit of 121 records found an open one had entropied
into roughly thirty forms — not toward one wrong value, but toward *variety*,
which is worse, because a reader cannot learn what the field means.

**What each word means is yours, and it differs by scheme.** `Rejected` on a
decision means considered and declined. On a scheme recording someone else's
claims it can mean *they assert this and it is wrong*. On a scheme of terms it
can mean *this word picks nothing out*. Say which in a `statuses.yaml` beside
the records, and the meanings render above the index table they explain:

```yaml
Active:
  label: Asserted
  blurb: the record asserts this proposition
Rejected:
  label: Defeated
  blurb: the corpus contains it and it is wrong
```

A record whose status the scheme does not declare fails the lint, so declaring
is also narrowing.

**One status per scheme is *in force*** — `active` in `luria.toml`, `Active` by
default. Everything else counts as retired, which is what makes citations of it
findings.

## Citations

A citation is a code in prose. Write it bare and let the fixer link it:

```console
$ luria link --fix
docs/scaling.md: 3 reference(s)
```

**Never hand-write a link target.** Record prose is rendered into views in other
directories, so a target has to resolve from where the text *lands*, not where
it lives. A journal entry five directories deep renders into `docs/journal/`;
the depth that looks right beside the source points at nothing in the view. Only
the fixer knows that frame, and a check catches targets it did not write.

Want prose as the label? `[[ADR-012|the caching decision]]` — still the fixer's
job.

## What a finding looks like

Four classes matter most:

**`retired-citations`** — a record cites something not in force, unacknowledged.
The core finding. Either repair the citation or acknowledge it.

**`unresolved-codes`** — `ADR-047` names no document. A reference the reader
cannot follow and the fixer cannot link.

**`broken-targets`** — a relative link resolves to nothing from where the prose
renders.

**`inert-status`** — a whole scheme where every record shares one status. Not
about any record; about the *field*, which is carrying no information. Since
`active` is what `retired-citations` reads, a scheme in this state has an
enforcement mechanism that cannot fire, and its green build says only that
nobody has looked.

By default these are reported. Naming one in `[luria.lint] fail_on` promotes it
to a build failure. The dial is per-class, so a project can enforce the one it
cares about while it cleans up the rest — and acknowledged findings never fail,
so the escape hatch survives enforcement.

## Schemes

A **scheme** is a family of records: a prefix, a directory, a template, a tag
vocabulary, a status vocabulary, and a rendering.

`ADR` is the one luria ships. It is not the product. Declaring any scheme
replaces the shipped family, so a project that wants decisions *plus* something
else declares both.

Schemes cite each other. That is the whole point: when arguments cite claims as
premises, retiring a claim surfaces every argument built on it. See
[schemes](schemes.md).

## The two surfaces

```
record/     WRITE — hand-edited, one file per record, plus templates and vocabularies
docs/       READ  — indexes, tag pages, collected documents, status reports
```

Everything under `docs/` that luria owns is **generated**, and a stale view is a
lint failure rather than a quiet divergence. Do not hand-edit an index; edit the
frontmatter and run `luria index`.

The one hand-written part of a generated view is its **stub** — `README.stub`
beside the records — which holds the prose that introduces the index. It lives
on the write surface because it is written, and renders into the read surface
with everything else.

## Journals and fragments

Two kinds of record are not numbered.

A **journal** is a dated log — one entry per pass at something, collected into
books by day or month. Entries are historical: true about the day they were
written, and never retroactively wrong. This is where the failed approaches go,
and it is the layer that survives contact with the future best.

A **fragment directory** is a set of files assembled into one document — a
changelog, a digest. One fragment per contribution, collected on a cadence
rather than on every merge, so the assembled file is not a lock every branch
must touch.

## What luria is not

**Not a documentation generator.** It generates documentation, but so does
everything; the generation is a means. Without a status that moves, luria
degenerates into exactly that, which is the failure `inert-status` detects.

**Not a linter**, in the usual sense. A linter checks a file against rules that
do not change. Nothing about the prose changes when a status does — one field
moves and consequences appear in files nobody opened.

**Not a wiki.** A wiki's links break silently. That is the difference.

## Where to go next

- [Quickstart](quickstart.md) — do the above, with a real finding at the end.
- [Schemes](schemes.md) — design a record family for your own material.
- [Directives](directives.md) — the acknowledgement vocabulary in full.
- [Project memory](project-memory.md) — the doctrine: what belongs in which layer.
