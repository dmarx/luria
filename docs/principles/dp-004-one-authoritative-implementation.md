---
status: Active
version: 1
tags:
- craft
date: '2026-08-03'
influenced_by:
- ADR-005
- ADR-006
origin: >-
  A tool-icon migration whose bug was precisely a fallback that only one render
  site preferred, so every other site leaked the legacy value.
summary: >-
  Load-bearing logic lives in exactly one tested place and every consumer reads
  it identically. A second copy — or a fallback each consumer must remember to
  prefer — is a latent bug. The sharpest instance here: the linter and the fixer
  share one scanner, so the linter can never demand a rewrite the fixer wouldn't
  make.
---

# DP-004: One authoritative implementation, read the same way everywhere

The load-bearing logic of a thing lives in exactly one tested place, and every
consumer reads it identically. A second copy — or a fallback each consumer must
*remember* to prefer — is a latent bug: sooner or later one consumer diverges
and silently ships stale behavior.

The sharpest instance here: **the linter and the fixer share one scanner**, so
the linter can never demand a rewrite the fixer wouldn't make. Two
implementations of "what counts as a bare reference" would drift within a month,
and the failure mode is the worst kind — a CI failure whose suggested remedy
doesn't work.

The same reasoning rejected threading configuration through every entry point
([ADR-006](decisions/adr-006-reference-schemes-are-configured.md)): the
second caller forgets an argument, and the two checks quietly cover different
files.

"The new thing overrides the old at one site" is the smell; "the new thing
*replaces* the old everywhere" is the fix.
