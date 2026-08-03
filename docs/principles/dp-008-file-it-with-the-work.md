---
status: Active
version: 1
tags:
- record
date: '2026-08-03'
influenced_by:
- ADR-002
origin: >-
  The reason the fragment convention exists at all — the changelog was being
  reconstructed retroactively from git log, badly.
summary: >-
  "Later" is a euphemism for never. A fact filed while its context is loaded
  costs a paragraph; re-derived cold it costs a session — the rediscovery tax,
  paid per collaborator, forever. Which is why the paperwork loop has to be
  cheap: any friction here is repaid in re-derivation at a much worse rate.
---

# DP-008: File it in the same contribution as the work

"Later" is a euphemism for never. A fact filed while its context is loaded costs
a paragraph; re-derived cold, it costs a session — the **rediscovery tax**, paid
per collaborator, forever.

This is why the paperwork loop has to be cheap: a fragment is one new file, the
index is generated, and the lint tells you exactly what is missing. Any friction
here is paid back in re-derivation, at a much worse rate.

The corollary that people skip: **record the wrong theories.** The approach that
failed on Tuesday leaves no commit, appears in no diff, and is the single most
expensive thing for the next person to rediscover.
