---
status: Active
title: Init takes shorthand and writes ordinary tables
version: 1
tags:
- mechanism
date: '2026-08-25'
summary: >-
  A project that wants the defaults plus one scheme had to write the whole
  config, and three of a scheme table's four lines follow from its prefix.
  `--schemes`/`--journals` accept `NAME:kind` and expand into the ordinary
  commented tables. Rejected: a compact form stored in luria.toml, which
  would be a second grammar every reader has to learn.
---

# ADR-tmpio6tr: Init takes shorthand and writes ordinary tables

## Context

`luria init` scaffolds whatever a config declares ([ADR-048](ADR-048.md)), and that is the
right shape — but it left a project with only two ways to start. Take the
shipped template exactly, or write a `luria.toml` and pass `--config`.

There is a large middle. Most new records want the defaults and one more
thing: an RFC family, an incident log, a specs page. Reaching that meant
copying the template, finding the scheme tables, and writing four more lines
of which three follow from the prefix — `record/rfcs.d`, `docs/rfcs`, an
index render. That is the first thing a new project types, and it is the part
with no decision in it.

## Decision

`luria init --schemes "RFC,SPEC:document" --journals "incidents:day"`.

Each entry is `NAME` or `NAME:kind`: `index` or `document` for a scheme,
`year`, `month` or `day` for a journal. Paths follow the prefix.

**The shorthand is an argument, never a stored format.** What lands in
`luria.toml` is the ordinary table, commented like the rest of the template.
Nothing reads the shorthand back; there is no second parser, no precedence
question between a compact form and an explicit one, and a reader of the
generated config sees exactly what every other project's config looks like.
The saving is in what somebody types once.

**Additive, and the additivity is load-bearing.** A declared family replaces
the shipped one whole ([ADR-047](ADR-047.md)), so "the defaults plus an RFC scheme" only
works because the template's own ADR and DP tables stay in the file. That
makes the rule visible at the moment it matters. Removing a default is
deleting its table — an edit to a file the user can now see, rather than a
flag that would have to express absence.

**Refused where a config already exists**, and alongside `--config`. The
shorthand extends the shipped template; where a project has a config the
shape is its own decision, and a flag should not append to a file the project
owns.

## Alternatives considered

- **A compact form stored in `luria.toml`** — `schemes = ["RFC", "SPEC:document"]`
  parsed at load. Shorter on disk, and it costs a second grammar in the one
  file every contributor and every agent reads, plus a precedence rule for
  what happens when both forms appear. The config is the interface; keeping
  it one shape is worth more than the lines.
- **A wizard.** Interactive prompts fit a scaffold run once, and they do not
  fit CI, an agent, or a README that wants to show the command that produced
  a project.
- **More flags, one per key** — `--rfc-dir`, `--rfc-render`. Scales with the
  schema rather than with what people actually vary, and the two things
  people vary are which families exist and how each renders.
- **Shipping more example configs to copy.** `examples/` already does this
  and is the right home for a whole shape. It does not help the case here,
  which is one line's worth of difference from the default.
- **Status quo.** Defensible — the config is small and well commented. It
  keeps the first five minutes of a new record spent editing TOML rather than
  filing an entry, which is the wrong first impression for a tool whose
  argument is that filing should be cheap.

## Consequences

Two things now describe a scheme table: the shorthand expander and the
template's own tables. They can drift — a change to the conventional layout
would have to touch both — and the tests pin the expansion's output against a
loaded `Config` rather than against a string, so a drift shows up as a
scheme that does not resolve rather than as a diff nobody reads.

The prefix-to-directory rule (`RFC` → `rfcs.d`) is mechanical, and the
shipped schemes deliberately break it: `decisions.d`, not `adrs.d`. A
generated table therefore looks slightly unlike the ones above it in the same
file. The comment on each generated table says the paths follow the prefix
and invites the rename, which is the honest version of a convention that
cannot guess what an RFC is.
