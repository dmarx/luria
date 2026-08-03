### Added

- **Another project's decision is cited as `LU-ADR-013`** — a registered remote
  prefix composed with that project's own code
  ([ADR-016](docs/decisions/ADR-016.md)). One `[luria.remotes.LU]` entry makes
  it a **first-class reference**: `luria link --fix` writes the URL, `luria
  lint` fails on a bare one, and the citation scan no longer has to guess which
  project a code belonged to.
- **`luria remotes`** — what is configured and how each foreign reference
  resolves; `--refresh` discovers code→filename maps from a **public**
  repository into a committed `remotes.lock.json`; `--check` probes
  reachability. A remote that follows
  [ADR-013](docs/decisions/ADR-013.md) needs no lockfile: the code *is* the
  filename.
- **Two remotes are registered, and their difference is the point.** `SG` is
  the pilot this package was extracted from — private, filenames not yet
  converted, so `--check` reports it *unverifiable*. `LU` is Luria itself,
  which the `luria init` scaffold cites instead of pasting GitHub URLs into a
  new project's templates, and which `--check` verifies for real. The mechanism
  is exercised by the package, not only by its tests — which is how the
  `*.stub` hole below was found.
- **A citation may name a document before its URL resolves**
  ([ADR-017](docs/decisions/ADR-017.md)). `SG-ADR-032` 404s today and will land
  when strata-g's record is ported; naming the document is the durable half,
  and the whole set flips to `ok` in one `--check` run when it does.
- **`version:` is standard frontmatter for every scheme**, not just principles.
  Shown in the decision index only when it isn't 1, because a column of ones
  teaches nothing.

### Fixed

- **`*.stub` files are linted.** A stub is the hand-written prose of a
  generated view: the lint skipped it for not being markdown, and skipped the
  page it renders into for *being generated*, so a bare reference written there
  was invisible to both checks at once.
- **A code whose remote has been discovered is no longer guessed.** Once a
  lockfile has been read from a remote, its silence about a code is
  authoritative and the reference stays unlinked and reported.
- **`--check` no longer reports a private repository as a shelf of 404s.** It
  probes the repository once and says *unverifiable* — an anonymous 404 is not
  the claim "this document was deleted".

### Changed

- **Discovery reads public repositories over HTTPS only.** The local-clone
  option is gone: a resolution that depends on what happens to be on somebody's
  disk produces a committed lockfile nobody else can regenerate. A remote Luria
  can't read gets a `url` template, not a credential path
  ([ADR-016](docs/decisions/ADR-016.md) supersedes
  [ADR-015](docs/decisions/ADR-015.md)).
