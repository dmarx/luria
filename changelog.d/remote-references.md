### Added

- **Another project's decision is cited as `SG-ADR-032`** — a registered remote
  prefix composed with that project's own code
  ([ADR-015](docs/decisions/ADR-015.md)). One `[luria.remotes.SG]` entry makes
  it a **first-class reference**: `luria link --fix` writes the URL, `luria
  lint` fails on a bare one, and the citation scan no longer has to guess which
  project a code belonged to.
- **`luria remotes`** — what is configured and how each foreign reference
  resolves; `--refresh` discovers code→filename maps into a committed
  `remotes.lock.json`; `--check` probes reachability.
- **Discovery reads the remote's own `luria.toml`**, so where its documents
  live comes from the authority rather than a guess. It works from a local
  clone (`path = "../strata-g"`) — the only way a *private* remote resolves —
  or the GitHub contents API for a public one.

### Changed

- **Eight pasted GitHub URLs in [ADR-009](docs/decisions/ADR-009.md) became
  eight bare codes** that the fixer linked automatically, and several
  `unresolved-ok` acknowledgements turned back into real references. An
  acknowledgement is a suppression; the best thing that can happen to one is
  that it stops being needed.
- **`luria ref-status` reports a foreign code that names no document** in its
  remote, alongside the local ones. Blanking the composed span so the local
  scanner can't misread it must not also make it invisible.

### Fixed

- **A code whose remote has been discovered is no longer guessed.** Rung 3 (the
  code-only filename convention) built a confident URL for a document that has
  never existed; once a lockfile has been read *from* the remote, its silence
  about a code is authoritative and the reference stays unlinked and reported.
- **`--check` no longer reports a private repository as a shelf of 404s.** It
  probes the repository once and says *unverifiable* — an anonymous 404 is not
  the claim "this document was deleted".
