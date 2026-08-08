<!-- One fragment per contribution, named changelog.d/<branch-slug>.md. Keep
     only the headings that apply; delete the rest. Collected into CHANGELOG.md
     on a cadence, never on every merge (ADR-002). -->

### Added

- [ADR-042](record/decisions.d/ADR-042.md): the draft signal — a draft PR
  carrying a Proposed decision and a both-directions writeup asks for a
  verdict, not a review; merge flips the decision Active, close files it
  Rejected, and either way the reasoning is kept.
- Rung 1 of the migrations ladder ([ADR-040](record/decisions.d/ADR-040.md)): a migrated document's old
  spellings resolve through its `formerly:` frontmatter — the derived alias
  map, a `legacy-spellings` warning class on the `fail_on` ladder, a
  `luria link --fix` modernize pass that upgrades in-flight prose, and the
  scan keeps watching prefixes whose scheme has left the config. Schemes
  can demand extra frontmatter via `requires = [...]`, enforced by the
  lint. The modernize pass and the scan both structurally exempt
  `formerly:` stamps — the ledger is not the prey.

### Changed

- [ADR-040](record/decisions.d/ADR-040.md), [ADR-041](record/decisions.d/ADR-041.md)
  and [DP-010](record/principles.d/DP-010.md) go Active: the doctrine
  batch's merge was the verdict.
