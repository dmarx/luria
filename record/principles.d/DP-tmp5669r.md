---
status: Active
title: Meet the project where it is
version: 1
tags:
- craft
- mechanism
date: '2026-08-25'
influenced_by:
- ADR-tmp91qkk
origin: >-
  A Windows user ran `luria init` and then `luria index`, and got a stack
  trace writing a check mark into a status report. Nothing about their project
  was unusual. The tool had required a UTF-8-capable platform without ever
  saying so.
summary: >-
  A project picks its language, its platform, its forge and its shape for
  reasons that have nothing to do with keeping a record; the record arrives
  afterwards and should fit what it finds. The way to hold that is to be
  explicit in what the tool writes and forgiving in what it assumes — and to
  keep asking what has been assumed and never written down, because coupling
  to an environment rarely arrives as a decision.
---

# DP-tmp5669r: Meet the project where it is

Aim to be usable by whatever project has something worth remembering. It
picked its language, its operating system, its forge and its file layout for
reasons that had nothing to do with keeping a record, and it made those
choices long before this tool showed up. The record is the guest.

That is an aspiration rather than a rule, because it is never finished — but
it is a testable one, and here is where it has been tested so far:

- **Language.** Source files are scanned for references as text, with no
  parser and no list of languages. A code in a Rust comment is a claim about
  why that code is the way it is, and so is one in a Makefile; the scanner
  does not need to know which it is holding. Reaching a new language means
  adding a glob.
- **Operating system and terminal.** Files are UTF-8 everywhere, because a
  record gets cloned onto whatever machine the next reader has. The console is left at
  whatever encoding the platform gave it, and taught to degrade instead of
  raise.
- **Forge.** An issue URL is inferred from the origin remote for the hosts
  whose issue paths are known, and left empty for the rest, so a self-hosted
  instance gets a record that works and one field to fill in. The shipped CI
  is a convenience over plain Git.
- **Storage.** Markdown is what a record looks like today. Identity, standing,
  declared rules and generated views are the model, and none of them says
  anything about a file format.

The discipline that keeps this true is a pair:

> **Be explicit in what you write, and forgiving in what you assume.**

Files get an encoding named at every call site, because a file has a reader on
another machine and has to open there. The console gets `errors="replace"`,
because it has one reader and guessing wrong should cost a `?` rather than the
command. An unrecognised forge yields nothing rather than a plausible URL,
because a wrong guess would put a broken link on every entry that carries an
issue.

**The aspiration is easy to hold and easy to lose, because coupling rarely
arrives as a decision.** Nobody chose to require a UTF-8-capable console. The
package simply never said what it needed, and a hundred call sites inherited
whatever the platform preferred — which is invisible on the machine where the
code was written and a stack trace on somebody's first run. So the question
worth asking is not *which environments do we support*, which gets asked
during design and answered generously. It is *what have we assumed and never
written down*, which otherwise gets asked for the first time by a stranger.

What it costs is worth saying plainly, because the bill comes in capability.
No per-language parsers, so a comment marker inside a string literal is
matched anyway. No format-specific model, so nothing exploits what markdown
makes cheap. No guessing at an unknown forge, so a self-hosted instance gets
no inference at all. Each of those is precision given up in exchange for
reach — and reach is the point, because the projects that most need a memory
are rarely the ones that look like yours.
