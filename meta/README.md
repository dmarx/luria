# Luria's own project memory

This is the record Luria keeps of *itself* — the choices, the standing values,
and the narrative of how the package got to be the way it is. It is here rather
than in `docs/` because it is evidence, not documentation
([ADR-021](decisions/ADR-021.md)).

- [Decisions](decisions/README.md) — the choices, with their alternatives.
- [Design principles](design-principles.md) — the standing values, numbered and
  citable.
- [Development log](devlog/README.md) — the narrative: failed approaches, root
  causes, and the traps worth not rediscovering. One book per month, generated
  from the dated entries in `devlog.d/`.

**Two audiences, and this directory serves the second one.** Someone adopting
Luria wants [`docs/`](../docs/README.md) and the scaffold in `template/`;
nothing here ships to them, and `luria init` never copies it. Someone
*contributing* to Luria wants exactly this: why a thing is the way it is,
what was tried and rejected, and which values the code keeps re-deriving.

It stays in the repository rather than moving to one of its own because
[ADR-009](decisions/ADR-009.md) is a claim that has to keep being true — Luria
runs its own machinery on its own record, and several tests are deliberately
corpus-dependent against *this* corpus. Segregating the record is not the same
as exiling it.
