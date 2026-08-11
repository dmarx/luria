---
status: Active
title: 'Why we pinned the tokenizer'
tags:
- security
date: '2026-04-01'
summary: >-
  The upgrade path is blocked on a fix tracked in [JIRA:PLAT-88](https://acme.atlassian.net/browse/PLAT-88). Rejected:
  vendoring the tokenizer, which trades a tracked dependency for an untracked
  fork.
---

# NOTE-001: Why we pinned the tokenizer

The method is the one from [ARXIV-2301.07041](https://arxiv.org/abs/2301.07041), and the version bump is held by
[CVE-2024-3094](https://nvd.nist.gov/vuln/detail/CVE-2024-3094). Ticket: [JIRA:PLAT-88](https://acme.atlassian.net/browse/PLAT-88).
