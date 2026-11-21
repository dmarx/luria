---
status: Proposed
title: 'A hands-free regime for an assistant working on a record: the owner switches it on and off, and while it is on the assistant files what the work develops as it goes, reports each filing, merges into an integration branch when its checks pass, and reverts when the owner interjects; the owner''s review moves to the one merge that reaches the default branch'
version: 1
tags:
- process
date: '2026-11-21'
summary: >-
  Upstreamed at the owner's request from the Nucleation record, where it
  was decided and first run on 2026-11-21 (its decisions on the dialectic regime
  and on merging into staging, in dmarx/nucleation pull requests 570 and
  573). A record kept with
  an assistant spends much of the owner's attention on permission: offer to
  file, wait, file; open a pull request, wait, merge. Once work lands on an
  integration branch that only a promotion carries to the default branch,
  the owner's review can sit at that promotion, and the assistant can file
  as it goes and be reverted when wrong. Luria documents the regime as an
  opt-in working agreement; the template carries it commented out. Rejected:
  asking each time, always on, and a regime with no integration branch.
---

# ADR-tmpwcl6h: A hands-free regime for an assistant working on a record: the owner switches it on and off, and while it is on the assistant files what the work develops as it goes, reports each filing, merges into an integration branch when its checks pass, and reverts when the owner interjects; the owner's review moves to the one merge that reaches the default branch

## Context

A project that keeps its record with an assistant runs on handoffs. The
assistant works something out, offers to file it and waits; the owner says
"file it"; the assistant files, opens a pull request and waits; the owner
merges. In Nucleation's session of 2026-11-20 and 21 the first handoff came
round about a dozen times, and at one point six pull requests stood green
and unmerged while the conversation went on. Each round spends an owner's
turn on permission rather than on the work, and keeps the record a step
behind what it records.

Asking first was prudent when every merge reached the default branch. It is
less so once two things hold:

- **an integration branch** that work merges into and that only a promotion,
  by the owner or a workflow, carries to the default branch (Nucleation's
  `staging`, from its pull request 565); temporary codes stay temporary there and are
  concretized at the promotion ([ADR-049](ADR-049.md)'s merge allocation);
- **history kept,** so any filing is a commit a revert can name.

Then the risk left is that the assistant files something the owner would
not have, and it is cheaper to revert that once than to prevent it by
asking every time: sometimes it is better to ask forgiveness once than
permission a thousand times.

## Decision

Luria documents a **hands-free regime** as an opt-in working agreement,
for projects that have an integration branch.

- **A switch.** The owner switches it on and off in words the project
  names. It is on until switched off, and not tied to a topic, a pull
  request or a stretch of work. A new session cannot see an earlier
  session's switch and starts off.
- **What the assistant does without asking, while it is on:**
  - files what the work develops in the schemes the project names for it
    (for Nucleation, the schemes of its own argument), as it goes, under
    the project's ordinary rules for filing;
  - when a turn admits several readings that would be filed differently,
    files each, marked as alternatives, for the owner to choose;
  - one commit per turn, so a revert names one turn; reverts are reverts,
    never rewrites of history;
  - reports, after answering, what was filed and where;
  - merges a pull request into the integration branch when its checks pass
    and it merges cleanly, with a merge commit, and reports the merge.
- **What still waits for the owner:** a change of status on a held entry,
  new decisions and principles (so the regime cannot amend itself),
  configuration, CI, spending that the project gates, anything sent outside,
  and the promotion to the default branch.
- **Interjection.** "Revert that" or "don't file that" is acted on in the
  next turn. A go-ahead covers everything the message it answers proposed.
- **Exits.** The assistant may suggest switching off when continuing would
  be awkward, for instance before work the regime excludes.

The template's `CLAUDE.md` carries the regime as a commented-out working
agreement, so a project turns it on by deciding to, not by default
([DP-010](../principles.d/DP-010.md): disclosures opt in).

## Alternatives considered

- **Ask each time.** The default, and right without an integration branch.
  Its cost is the owner's turns and a record that lags.
- **Always on.** Filing during tooling work, where a commit can break CI, is
  where a revert is not cheap. The switch keeps the regime to the work it
  suits.
- **Hands-free with no integration branch.** Every merge would reach the
  default branch and concretize codes as it went; the owner's review would
  come after the fact. The regime presumes the branch.
- **A config key that switches it.** A regime is a working agreement
  between an owner and an assistant, not something the CLI enforces;
  nothing in `luria` reads it.

## Consequences

- A project that adopts it moves the owner's review to the promotion, and
  the record keeps pace with the work.
- More commits and revisions per pull request; the per-turn commit and the
  report keep them legible.
- The integration branch can hold combinations no pull-request check has
  seen; the promotion's lint is the check on them, as Nucleation's Promote
  workflow lints before it pushes.
- Nothing in `luria` changes. The decision is documentation and a template
  section; a project's own decision adopts it.

## First application

Nucleation ran it from 2026-11-21: filings under its regime decision in its
pull request 572, and merges into `staging` of its pull requests 567 to 570
under its decision on merging. Here, the template's commented-out section.
