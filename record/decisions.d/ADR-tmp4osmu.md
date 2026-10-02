---
status: 'Active'
title: 'An amendment that keeps its summary word for word is a warning, read against HEAD'
version: 1
tags:
- mechanism
date: '2026-10-02'
issue: '#326'
summary: >-
  The `unrevisited-summaries` warning class reports a document whose working
  tree has a newer `version:` than HEAD while its `summary:` reads the same.
  `summary:` is what the index shows, and it is the field an amendment
  forgets. A `summary-ok: vN` directive acknowledges one amendment, not every
  later one. The previous revision comes from `git show HEAD`, so the check
  speaks while the amendment is uncommitted and is silent after. Rejected: a
  fingerprint field written by `luria repair`, walking file history for the
  revision before the bump, and making it a violation.
influenced_by:
- ADR-019
- ADR-035
---

# ADR-tmp4osmu: An amendment that keeps its summary word for word is a warning, read against HEAD

## Context

[ADR-019](ADR-019.md) lets a document be corrected in place, provided the correction is
visible: a `version:` bump and a `history:` entry. Nothing looks at the
fields that restate the body. In anthology-of-the-sota, twelve documents
were amended in one day, and one `summary:` was left saying "the evidence is
image classifiers only" five versions after the body began arguing the
verdict reverses on text ([#326](https://github.com/dmarx/luria/issues/326)). `summary:` is what `luria index` renders
into the browse tables, so the stale line was the one readers met first.

The other eleven summaries were right to survive their amendments. So this
is a judgement call, and a judgement call is a warning with an
acknowledgement ([ADR-035](ADR-035.md)), not a violation.

## Decision

- **The finding.** A document whose working-tree `version:` is greater than
  HEAD's, while its parsed `summary:` equals HEAD's, is an
  `unrevisited-summaries` row at the `summary:` line. The values are
  compared parsed, not as bytes, so re-wrapping a folded summary does not
  count as revisiting it. Failable through `lint.fail_on` like any class.
- **The acknowledgement names the version:** `# summary-ok: v7 — reason`
  above `summary:`. It answers one amendment; the next bump is a new
  question, and an acknowledgement naming another version is reported stale.
- **HEAD is the only revision asked.** One `git diff --name-only HEAD` picks
  the changed documents, and `git show HEAD:<path>` reads each one's previous
  frontmatter. No repository, no HEAD, or an untracked file means no
  finding. After the commit, HEAD is the amendment and there is nothing to
  compare, so the check is silent and no acknowledgement is called stale.

## Alternatives considered

- **A `summary_rev:` fingerprint recorded with each `history:` entry.** The
  check would work on any checkout, CI included. Rejected: it adds schema to
  every amended document for a warning, and the fingerprint is another
  hand-kept copy unless `luria repair` writes it on every bump.
- **Walk the file's history for the revision before the bump.** The check
  would also speak after the commit. Rejected: CI and the checkouts this
  project runs in are shallow, so the answer would depend on clone depth,
  the same reason `spent-upgrades` does not read history.
- **A violation.** Eleven of the twelve measured summaries were right to
  stay. A rule that is wrong that often is a report.

## Consequences

- The check speaks to whoever runs `luria lint` before committing, which is
  the moment the summary can still be fixed cheaply. A CI run on a pushed
  branch does not see it.
- An acknowledgement stays in the file after its amendment is committed,
  doing nothing until the next bump. It is reported stale only when a newer
  bump is pending and it names an older version.
- Only `summary:`. `consensus_note:`-style fields from the same measurement
  are record-specific. Extending the check to a configured list is a
  follow-up if another record asks.
