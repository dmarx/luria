### Changed

- **The README's two record badges are counts now, not adjectives**
  ([ADR-018](meta/decisions/ADR-018.md)). "generated index" and "versioned"
  were assertions that could never be false; they are replaced by **needs
  decision** (`Proposed` + `Deferred`) and **cited but retired** (retired
  documents still cited without an acknowledgement). Zero is green, non-zero is
  amber — neither number is a failure.
- **`luria pending` covers every scheme**, not just decisions. A `Proposed`
  principle is an open question in exactly the same way, and its rows are keyed
  by code (`ADR-012`, `DP-004`) rather than by ADR number.

### Added

- **`luria badges`**, and `luria index` regenerates the counts into a
  `<!-- luria:badges -->` region. The numbers are baked into static shields
  URLs — no endpoint to configure and no committed JSON — and `luria lint`
  fails when the region disagrees with the record. Baked in rather than served
  means the count is correct *per commit*, so a pull request shows its own
  numbers rather than the default branch's.
