# Luria documentation

Luria keeps a project's memory — decisions, principles, changelog, devlog —
as small plain-markdown sources, rendered into linked views and held
together by a lint. This page is the map. (`luria lint` checks that every
page in `docs/` is listed here, so the map cannot silently rot.)

## Using Luria

- [Quickstart](quickstart.md) — install, scaffold, file, lint: the whole
  loop in ten minutes.
- [Project memory](project-memory.md) — sources and views; the four families (schemes,
  journals, fragments, remotes); statuses; how references are found,
  linked, and kept honest.
- [CLI reference](cli.md) — every command, flag by flag.
- [Comment directives](directives.md) — acknowledging a lint finding where
  it happens, with the reason attached; also the fixture-code convention.
- [Adopting Luria](adopting.md) — bringing the record to an existing
  project, the CI wiring, and the published site.

## Generated references

Built by `luria index` — read them, don't edit them.

- [Configuration](configuration.md) — the full `luria.toml` schema,
  generated from the dataclasses that parse it: every key, type, and
  default.
- [The record](record.md) — the shape *this* project gave the machinery,
  generated from its `luria.toml`: what families exist, where entries are
  filed, and what to type to add one.

## This project's record

Luria's own memory, kept with the tool it ships:

- [Decisions](decisions/README.md) — every architectural choice, with
  status, tags, and alternatives.
- [Design principles](design-principles.md) — the standing values, one
  page, anchored for citation.
- [Development log](devlog/README.md) — the narrative: root causes, failed
  approaches, and the traps the next person would otherwise rediscover.
- Status reports — [pending decisions](reports/pending-decisions.md) and
  [reference status](reports/reference-status.md): what awaits a human eye.
