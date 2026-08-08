<!-- One fragment per contribution, named changelog.d/<branch-slug>.md. Keep
     only the headings that apply; delete the rest. Collected into CHANGELOG.md
     on a cadence, never on every merge (ADR-002). -->

### Added

- [ADR-042](record/decisions.d/ADR-042.md): the draft signal — a draft PR
  carrying a Proposed decision and a both-directions writeup asks for a
  verdict, not a review; merge flips the decision Active, close files it
  Rejected, and either way the reasoning is kept.
- [DP-011](record/principles.d/DP-011.md) (Proposed): the ledger looks like
  the prey — a mechanism that hunts a pattern must structurally exempt its
  own record of that pattern, because three subsystems independently ate
  the `formerly:` trail on the first migration's first day.
- Rung 1 of the migrations ladder ([ADR-040](record/decisions.d/ADR-040.md)): a migrated document's old
  spellings resolve through its `formerly:` frontmatter — the derived alias
  map, a `legacy-spellings` warning class on the `fail_on` ladder, a
  `luria link --fix` modernize pass that upgrades in-flight prose, and the
  scan keeps watching prefixes whose scheme has left the config. Schemes
  can demand extra frontmatter via `requires = [...]`, enforced by the
  lint.

### Changed

- [ADR-040](record/decisions.d/ADR-040.md), [ADR-041](record/decisions.d/ADR-041.md)
  and [DP-010](record/principles.d/DP-010.md) go Active: the doctrine
  batch's merge was the verdict. [ADR-040](record/decisions.d/ADR-040.md) also takes a version-2 correction:
  its Context's fixture examples are restated in fixture-doctrine-safe
  spellings.
- Test fixtures and docstring examples that borrowed real-sequence DP codes
  now use fixture spellings (`VP` schemes, OLD/NEW placeholders, composed
  remote forms) — the [ADR-032](record/decisions.d/ADR-032.md) hazard, cleared corpus-wide.
