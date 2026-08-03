### Changed

- **`ADR-018` is at `v2`.** Its rejection of the endpoint-badge alternative
  cited [ADR-002](docs/decisions/ADR-002.md)'s per-merge bot commit, which
  over-applied it — that hazard depends on a file being appended to at a marker
  and carrying assigned numbers, and a derived badge file has neither. The
  decision is unchanged; the reason it gives is now the real one (a baked-in
  URL is correct per commit, so a reviewer sees the count move in the diff).
- **Contributions to this repository go through a pull request.** A decision
  record is an interpretation of somebody's intent, and it should be read
  before it becomes what the project believes.

### Added

- **[ADR-019](docs/decisions/ADR-019.md): a wrong *reason* is corrected in
  place and versioned; a changed *choice* is superseded.** Superseding over a
  bad argument retires a decision still in force and points every citation at
  an identical claim. "Never rewrite a body" objects to *silent* revision — a
  `version` bump with a `history:` note saying what the old version got wrong
  is the opposite of silent.
