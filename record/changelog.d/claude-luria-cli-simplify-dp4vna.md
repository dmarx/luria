<!-- One fragment per contribution, named changelog.d/<branch-slug>.md. Keep
     only the headings that apply; delete the rest. Collected into CHANGELOG.md
     on a cadence, never on every merge (ADR-002).

     No user-facing changes? Replace everything with a single HTML comment
     saying why. A stub collects to nothing, which keeps "every contribution
     files a fragment" enforceable without inventing an entry. -->

### Added

- [ADR-040](record/decisions.d/ADR-040.md): the migrations doctrine — how schemes
  get renamed and documents move between them (mapping-driven sweeps,
  `formerly:` as identity, full rewrite including history, a rung ladder from
  prose relabel to `luria migrate`). Doctrine only; the machinery lands per
  the ladder, starting with rung 1.
- [ADR-041](record/decisions.d/ADR-041.md): the bug protocol — a defect enters
  the record as an issue carrying a minimal working example before any fix,
  the response is classified on the [ADR-035](record/decisions.d/ADR-035.md) ladder, and the fix PR turns the
  MWE into a regression test. First live run: the journal link-frame bug.
- [GP-010](record/principles.d/GP-010.md): defaults follow the failure mode
  — guards ship on and are opted out of visibly at the site; disclosures
  ship off and are opted into by a config line; either deviation is written
  down where it applies.

### Documentation

- Both CLAUDE.mds (this repo's and the template's) rewrite the hyperlink
  ground rule as "never hand-write a link target" — bare codes and
  `[[CODE|label]]` wikilinks, with the fixer owning every target because
  only it knows which render frame a target must resolve in — and add a
  fourth ground rule: a guard that keeps catching the same mistake is a
  bug report about the workflow, and the fix belongs upstream of the guard.
  Prompted by four wrong-frame links in one day, all hand-written, all
  wanting a prose label the (previously undocumented) labeled-wikilink
  syntax already provides.
- Both CLAUDE.mds now open with a read-this-first directive: load the full
  design-principles document into context before anything else — the
  principles are the one part of the record the map assumes rather than
  links.
