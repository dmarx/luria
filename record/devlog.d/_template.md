<!-- The shape of a journal entry. Don't copy this file by hand — run

         luria journal new "What you did"

     which files it at devlog.d/yyyy/mm/dd/hhmmss.md, the path derived from the
     timestamp so nothing has a number to assign and nothing has a name to
     collide on. `luria lint` checks the path and the `created:` field agree —
     and when the field is empty in an entry filed by hand, `luria index`
     populates it from the path, since the path already says it (#33).

     Entries persist. A journal entry is a dated observation — true when it was
     written, and still true — so unlike a changelog fragment it is never
     consumed. `docs/devlog/` is generated from these and can be rebuilt from
     scratch (ADR-020).

     The devlog is narrative, not a changelog: what problem was solved, what the
     fix was, and what was found along the way — root-cause archaeology, failed
     approaches, verification details, the traps the next person would otherwise
     rediscover. **Record the wrong theories and why they were wrong.** They are
     the expensive part and the part that never appears in a commit message.

     `title:` is what the book's contents list shows, so make it say what
     happened rather than which files moved. The rendered heading is the title,
     so the body starts at prose.

     No entry is required — the devlog covers significant work, not every
     contribution. -->

---
title: 'A sentence-shaped title'
created: '2026-01-01T00:00:00'
tags: []
---

**Short lead naming the work (#issue).** What was reported, what it actually
turned out to be, how it was verified, and what surprised you.
