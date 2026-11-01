<!-- inactive-ok-file: ADR-084 — the decision this change supersedes -->

### Added

- **A converse pair can mark its derived side** with `derived: true` on that
  side's reference ([ADR-tmpwpas9](record/decisions.d/ADR-tmpwpas9.md)). Only the primary side is stored, and every
  reader gets the derived side from the converse, as `relations.edges()`
  already did. `luria repair` moves an entry written on the derived side to
  the primary side of the other document, or drops it where that side
  already holds it. CI therefore applies it on every pull request. A move
  that would make a relation run both ways, break a document's contract, or
  name no document is left as filed and reported. A pair marking both sides,
  `derived` on a field with no `converse`, and `derived` on a self-converse
  relation are refused when the configuration loads.
- **Lint class `derived-relations`**: an entry filed on a derived side, naming
  `luria repair` as the remedy, or saying why repair leaves it.
- **Lint class `undirected-relations`**: a converse pair that marks neither
  side, once per pair. Such a pair keeps working as before.

### Changed

- **`one-sided-relations` covers only symmetric relations and pairs that
  declare no direction.** A directed pair is never one-sided, because its
  derived side is computed. These two kinds keep [ADR-084](record/decisions.d/ADR-084.md)'s completion in
  `luria link --fix`. [ADR-084](record/decisions.d/ADR-084.md) is superseded for directed pairs.
- **`luria relate` says where the other side of a relation lives**: derived
  and never stored, moved by `luria repair`, or completed by
  `luria link --fix`. It used to claim `luria repair` wrote the converse,
  which it never did.

### Documentation

- **[ADR-tmpu2wwj](record/decisions.d/ADR-tmpu2wwj.md) states what belongs in `luria repair` and what in
  `luria link --fix`.** A write whose answer is a function of the committed
  sources goes in `repair`. Only a write that reads the author's change
  against HEAD stays in `link --fix` alone.
