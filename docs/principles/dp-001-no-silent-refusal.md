---
status: Active
version: 1
tags:
- craft
date: '2026-08-03'
influenced_by: []
origin: >-
  The strata-g design-language review, where tools silently no-opped on inputs
  that didn't meet their preconditions.
summary: >-
  A tool that explains its refusal teaches its own model. If a precondition
  isn't met, say so — never quietly no-op, because a no-op with no feedback
  reads as "broken", which reads as "useless", when the real answer is "not
  here, and here's why".
---

# DP-001: No silent refusal

A tool that explains its refusal teaches its own model. If a precondition isn't
met, the tool *says so* — it never quietly no-ops. A no-op with no feedback
reads as "broken", which reads as "useless", when the real answer is "not here,
and here's why".

Applied here: the fragment collector raises when its insert marker is missing
rather than guessing where entries belong; `luria` prints the command list when
given a name it doesn't know; a directive that names an unknown region is
reported, with the known vocabulary named, rather than ignored.

The corollary that costs the most to follow: **a suppression must not become a
silence.** An acknowledgement that hides a warning is counted in the report, and
one that has stopped applying is reported in its own right — otherwise the
mechanism for saying "this is fine" becomes the mechanism for never hearing
about it again.
