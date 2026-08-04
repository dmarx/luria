### Changed

- **`ADR-018` is at `v2`.** Its rejection of the endpoint-badge alternative
  cited [ADR-002](meta/decisions/ADR-002.md)'s per-merge bot commit, which
  over-applied it — that hazard depends on a file being appended to at a marker
  and carrying assigned numbers, and a derived badge file has neither. The
  decision is unchanged; the reason it gives is now the real one (a baked-in
  URL is correct per commit, so a reviewer sees the count move in the diff).
- **Contributions to this repository go through a pull request.** A decision
  record is an interpretation of somebody's intent, and it should be read
  before it becomes what the project believes.

### Added

- **[ADR-019](meta/decisions/ADR-019.md): a wrong *reason* is corrected in
  place and versioned; a changed *choice* is superseded.** Superseding over a
  bad argument retires a decision still in force and points every citation at
  an identical claim. "Never rewrite a body" objects to *silent* revision — a
  `version` bump with a `history:` note saying what the old version got wrong
  is the opposite of silent.

### Documentation

- **The docs no longer read as "these documents are frozen."**
  [Project memory](docs/project-memory.md) gains a section on what is and isn't
  revisable, with a table of the four shapes — choice changed, reason wrong,
  value reworded, consequence falsified — and **a live example of each from this
  repository**, because a rule a project has never applied to itself is a rule
  nobody has tested.
- **[ADR-001](meta/decisions/ADR-001.md) is at `v2`.** Its traffic rule said a
  decision is "superseded but never rewritten", which reads as immutability and
  leaves no way to fix a wrong argument short of retiring a decision still in
  force. Narrowed to the case it governs — supersede when the *choice* changes —
  with `history:` recording the over-broad version. The rule about which layer
  holds what is unchanged.
- The decision templates, both index stubs, `CLAUDE.md` and the adoption guide
  now say the same thing, and the scaffold points a new project at Luria's
  worked examples by remote code rather than a pasted URL.
