---
status: Proposed
title: 'The ledger looks like the prey: exempt it structurally, not incidentally'
version: 1
tags:
- mechanism
- craft
date: '2026-08-08'
influenced_by:
- ADR-040
origin: >-
  The DP→GP migration's first live day: three subsystems — the migration
  sweep, the fixer's modernize pass, and the reference scan — each
  independently attacked the `formerly:` stamps the migration had just
  written, because the record of an old spelling is spelled exactly like
  the stale reference each of them hunts.
summary: >-
  Any mechanism that hunts a pattern will eventually hunt its own record of
  that pattern, because the ledger is written in the prey's spelling — an
  alias table names the old codes, a redirect map names the dead URLs, a
  suppression file names the warnings. The exemption must be structural (a
  mask the hunter applies by rule, with a test that fires it) and never
  incidental (an ordering that happens to protect it, a format the pattern
  happens to miss), because incidental protection is silently lost by the
  next refactor. Three subsystems ate the same ledger in one day; each was
  a separate discovery precisely because each hunter had its own mouth.
---

# DP-tmpqu8fy: The ledger looks like the prey: exempt it structurally, not incidentally

A mechanism that rewrites, flags, or retires instances of a pattern usually
keeps a record of what it did — and that record is written in the pattern's
own spelling. A migration's `formerly:` field names the old codes. A
redirect map names the dead URLs. A suppression list names the warnings it
suppresses. To every hunter of that pattern, the ledger is
indistinguishable from prey.

The failure is not hypothetical and not singular. On the day the record's
first migration ran, three subsystems attacked the stamps it had just
written, independently, each through its own mouth:

- the **sweep** rewrote the `formerly:` values into the new spelling —
  erasing the map at its source, in the same operation that created it;
- the **fixer**'s modernize pass did the same from the other side, turning
  every alias into a self-reference on the live corpus;
- the **scan** counted each stamp as a citation of the old code — every
  migrated document warning about its own former name, forever.

Three mouths, three separate discoveries, one cause. That multiplicity is
the point: exempting the ledger in one place does not exempt it anywhere
else, because each consumer of the pattern matches it independently.

So the exemption must be **structural**: a mask the hunter applies by rule
(this span is the ledger, never touch it), stated where the hunting
happens, with a test that fires it — a guard is trusted only once it has
been seen to catch ([DP-6](design-principles.md#dp-6)). What does not count is **incidental**
protection: an execution order that happens to write the ledger after the
sweep, a file the glob happens to miss, a format the regex happens not to
match. Incidental protection is real protection today and gone after the
next refactor, and it fails silently — the ledger doesn't complain when
eaten; it just stops being true, and everything derived from it (an alias
map, a resolution table) degrades into self-reference.

The test, when building anything that hunts a pattern: *does this system
keep a record of the thing being hunted, and does that record spell the
pattern?* If yes, the mask is part of the hunter's definition — written,
tested, and named in the same breath as the hunt itself.
