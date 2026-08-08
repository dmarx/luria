<!-- One fragment per contribution, named changelog.d/<branch-slug>.md. Keep
     only the headings that apply; delete the rest. Collected into CHANGELOG.md
     on a cadence, never on every merge (ADR-002). -->

### Added

- [ADR-042](record/decisions.d/ADR-042.md): the draft signal — a draft PR
  carrying a Proposed decision and a both-directions writeup asks for a
  verdict, not a review; merge flips the decision Active, close files it
  Rejected, and either way the reasoning is kept.
- `luria migrate` executes migration specs from `record/migrations.d/`
  (`luria new migration` scaffolds one): `rename_scheme` and `move_doc`,
  each with an explicit `strategy = "supersede"` mode, `--dry-run`, and
  `--commit` with automatic `.git-blame-ignore-revs` bookkeeping ([ADR-040](record/decisions.d/ADR-040.md)).
- A migrated document's old spellings resolve through its `formerly:`
  frontmatter: the derived alias map, a `legacy-spellings` warning class on
  the `fail_on` ladder, and a `luria link --fix` modernize pass that
  upgrades in-flight prose. Schemes can demand extra frontmatter via
  `requires = [...]`, enforced by the lint.

### Changed

- **The design principles are the guiding principles now**: `DP-N` became
  `GP-N` tree-wide (`formerly:` remembers), the view moved to
  `docs/guiding-principles.md`, and the default `design_principles` path a
  bare config inherits points at the new address — an adopting project
  that relied on the old default should set `[luria.paths]
  design_principles` explicitly. Executed by the machinery from
  `record/migrations.d/0001-design-principles-become-guiding-principles.toml`.

- [ADR-040](record/decisions.d/ADR-040.md), [ADR-041](record/decisions.d/ADR-041.md)
  and [GP-010](record/principles.d/GP-010.md) go Active: the doctrine
  batch's merge was the verdict.
