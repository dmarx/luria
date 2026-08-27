### Added

- `luria remotes --pin [CODE]` endorses remote content by hash ([#135](https://github.com/dmarx/luria/issues/135)): the
  hash of each pinned document's bytes is committed to `remotes.lock.json`,
  `--refresh` records what upstream serves now, and `luria lint` reports
  every pinned document that changed since its endorsement — the new
  `remote-drift` warning class, promotable via `fail_on`. Re-endorsing after
  review clears the finding; a bare `--pin` endorses everything cited and
  prunes pins nothing cites any more ([ADR-tmptuwov](record/decisions.d/ADR-tmptuwov.md)).
- A `pin_url` template on a remote (or remote scheme) declares where its
  *stable bytes* live, so content behind a rendered page becomes pinnable —
  `pin_url = "https://arxiv.org/e-print/{1}.{2}"` pins the paper an abstract
  page fronts. Declared rather than guessed: only the project can vouch that
  a URL is content-stable.
- Arbitrary URLs can be pinned too: flag one where it is cited
  (`<!-- pin: https://… — why it matters -->`) and run `luria remotes
  --pin`. The flag is the registration — deleting it retires the pin, so a
  pin that fires too often costs one removed comment.

### Fixed

- `luria remotes --refresh` no longer writes an authoritative empty map for a
  remote it could not read: a private repository's failed discovery used to
  flip every one of that remote's references to "absent from the remote".
  Failure now leaves the remote off the lockfile — or keeps the map it
  already had — so it stays on the code-only convention.
