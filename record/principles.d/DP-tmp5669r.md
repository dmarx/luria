---
status: Active
title: A record must not constrain the project it records
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
  A record holds claims *about* a project, so the project is the variable and
  the recorder is not entitled to an opinion about it — not its language, its
  operating system, its forge, or the format the record itself is stored in.
  The discipline that keeps this true is to be explicit in what the tool
  writes and forgiving in what it assumes, because coupling to an environment
  almost never arrives as a decision. It arrives as something nobody wrote
  down, and surfaces on somebody else's machine.
---

# DP-tmp5669r: A record must not constrain the project it records

A record exists to hold claims about a project: what was decided, what is
still believed, what it stopped believing. That makes the project the
variable. A tool that required the project to be written in a particular
language, or built on a particular operating system, or stored in a
particular format, would be deciding which projects are permitted to have a
memory. It has no standing to decide that.

What the agnosticism actually looks like, in four places it has already been
tested:

- **Language.** Source files are scanned for references as text, with no
  parser and no list of languages. A code in a Rust comment is a claim about
  why that code is the way it is, and so is one in a Makefile; the scanner
  does not need to know which it is holding. Adding a language means adding a
  glob.
- **Operating system and terminal.** Files are UTF-8 unconditionally, because
  a record is cloned by people on other machines. The console is left at the
  platform's own encoding and merely stopped from raising.
- **Forge.** An issue URL is inferred from the origin remote for the hosts
  whose issue paths are known, and inferred *not at all* for the rest. The
  shipped CI is a convenience over plain Git rather than a requirement.
- **Storage.** Markdown is what a record looks like today and is nowhere in
  the model. Identity, standing, declared rules and generated views are claims
  about a record, and none of them says anything about a file format.

The discipline underneath is a pair, and both halves are needed:

> **Be explicit in what you write, and forgiving in what you assume.**

Files get an encoding named at every call site, because a file has a reader
on another machine and has to open there. The console gets
`errors="replace"`, because it has exactly one reader and guessing wrong
should cost a `?` rather than the command. An unrecognised forge yields
nothing rather than a plausible URL, because a wrong guess would put a broken
link on every entry that carries an issue.

**The failure mode is that coupling arrives unstated.** Nobody decided this
package required a UTF-8-capable console. It simply never said what it
needed, and a hundred call sites inherited whatever the platform preferred —
which is fine on the machine where the code was written and a stack trace on
somebody's first run. So the test is not *did we choose to support this
environment*; it is *did we assume anything we never wrote down*. The first
question gets asked during design. The second one only gets asked by a bug
report from a stranger, unless something in the process asks it earlier.

The corollary is the expensive half. Refusing to depend on the environment
means refusing capabilities that depend on it: no per-language parsers, so a
comment marker inside a string literal is matched anyway; no format-specific
model, so nothing can exploit what markdown makes cheap; no guessing at an
unknown forge, so a self-hosted instance gets no inference at all. Each of
those is real precision given up. It is bought back in reach, and reach is
what a tool for holding a project's memory is for — the projects that most
need one are rarely the ones that look like yours.
