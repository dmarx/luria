<!-- One fragment per contribution, named changelog.d/<branch-slug>.md. Keep
     only the headings that apply; delete the rest. Collected into CHANGELOG.md
     on a cadence, never on every merge (ADR-002).

     No user-facing changes? Replace everything with a single HTML comment
     saying why. A stub collects to nothing, which keeps "every contribution
     files a fragment" enforceable without inventing an entry. -->

### Added

- [ADR-040](../decisions.d/ADR-040.md): the migrations doctrine — how schemes
  get renamed and documents move between them (mapping-driven sweeps,
  `formerly:` as identity, full rewrite including history, a rung ladder from
  prose relabel to `luria migrate`). Doctrine only; the machinery lands per
  the ladder, starting with rung 1.
