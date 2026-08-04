# Luria docs

- [Project memory: how a repo thinks](project-memory.md) — the doctrine. Start
  here; this is what an agent file should point at.
- [Design principles](design-principles.md) — the standing values, numbered and
  citable.
- [Decisions](decisions/README.md) — the choices, with their alternatives.
- [Comment directives](directives.md) — the `inactive-ok` / `unexempt`
  vocabulary and its scope rules.
- [Development log](devlog/README.md) — the narrative: failed approaches, root
  causes, and the traps worth not rediscovering. One book per month, generated
  from the dated entries in `record/devlog.d/`.
- [Adopting Luria](adopting.md) — putting the record into a project that hasn't
  got one.

Everything in this directory is for *reading* — the prose pages are authored,
and the decisions index, principles document and devlog books are generated.
Filing happens in [`record/`](../record/), whose `.d`-suffixed containers hold
the sources ([ADR-021](../record/decisions.d/ADR-021.md)).
