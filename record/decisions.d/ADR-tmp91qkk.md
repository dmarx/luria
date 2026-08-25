---
status: Active
title: Files are UTF-8; the console is the platform's
version: 1
tags:
- mechanism
date: '2026-08-25'
issue: '#112'
summary: >-
  Nothing in the package named an encoding, so every read and write took the
  platform's — cp1252 on a default Windows install. A scaffold crashed writing
  a check mark, and a tree written that way was then unreadable to the same
  tool under UTF-8. Files are now UTF-8 unconditionally, because a record that
  only opens on the machine that wrote it is not a record. The console keeps
  its own encoding and stops raising. Rejected: UTF-8 output at a cp1252
  console, which trades a crash for mojibake.
---

# ADR-tmp91qkk: Files are UTF-8; the console is the platform's

## Context

The package named no encoding anywhere. `Path.read_text()` and
`Path.write_text()` with no argument use whatever the platform prefers, which
is UTF-8 on Linux and macOS and **cp1252 on a default Windows install**.

Reported from Windows: `luria index` died on a repository `luria init` had
created a minute earlier, encoding a `✅` bound for a status report. Setting
`PYTHONUTF8=1` on the same tree then failed the other way, because the em
dashes the earlier run had written as cp1252 were no longer valid UTF-8. The
two halves of one bug disagreed with each other, and the only workaround was
to set the variable before the first command rather than after.

Reproduced here without Windows: `LC_ALL=C` gives an ASCII preferred encoding
and the same failure, which is what made this testable in CI.

## Decision

**Every file this package reads or writes is UTF-8, explicitly.** A record is
plain files in a repository that other people clone; one that only opens on
the machine that wrote it is not serving its purpose. There is no case where
the platform's guess is the right answer for a file, so the argument is
present at every call site rather than configurable.

**The console keeps the platform's encoding, and only stops raising.** At the
CLI entry point both streams are reconfigured with `errors="replace"`, so a
character the terminal cannot show becomes `?` and the line still arrives.

The asymmetry is the decision. A file has a reader somewhere else and has to
be portable; console output has exactly one reader, at that terminal, and
should look like what that terminal can show.

## Alternatives considered

- **Reconfigure the console to UTF-8 as well.** Full fidelity where the
  terminal supports it, mojibake where it does not — and a user who cannot
  read the output has no more idea what happened than one who got a
  traceback. `PYTHONUTF8=1` remains available for anyone who wants it.
- **Strip non-ASCII from printed strings.** The arrows, dashes and check marks
  carry meaning in reports that are read as tables. Removing them to satisfy
  the worst available terminal would degrade every other terminal.
- **Set the encoding once, in a wrapper around `Path`.** One place to change,
  and it hides the fact at every call site — a reader of `write_text` in this
  package would have to know a local convention to know what it does.
- **Document `PYTHONUTF8=1` as a requirement.** What the reporter had already
  found. It is a prerequisite nobody discovers before the first crash, and it
  does not repair a tree already written the other way.

## Consequences

A tree written by an older version under cp1252 still holds bytes this
version will refuse to read. Nothing here repairs one, and the failure is at
least loud. The population is small — a Windows user on a pre-fix release —
and the remedy is `git checkout` of the generated views, which are derived
anyway.

The structural half is guarded by a test that walks the package's syntax tree
and fails on any `read_text` or `write_text` without an explicit encoding. It
earned its place immediately: a first mechanical pass missed five nested
calls, where an inner `read_text(encoding=...)` made the outer `write_text`
look already covered, and the test named all five.
