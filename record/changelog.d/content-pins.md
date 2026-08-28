### Added

- `luria remotes --pin [CODE]` endorses remote content by hash ([#135](https://github.com/dmarx/luria/issues/135)): the
  hash of each pinned document's bytes is committed to `remotes.lock.json`,
  `--refresh` records what upstream serves now, and `luria lint` reports
  every pinned document that changed since its endorsement — the new
  `remote-drift` warning class, promotable via `fail_on`. Re-endorsing after
  review clears the finding; a bare `--pin` endorses everything cited and
  prunes pins nothing cites any more ([ADR-066](record/decisions.d/ADR-066.md)).
- A `pin_url` template on a remote (or remote scheme) declares where its
  *stable bytes* live, so content behind a rendered page becomes pinnable —
  `pin_url = "https://arxiv.org/e-print/{1}.{2}"` pins the paper an abstract
  page fronts. Declared rather than guessed: only the project can vouch that
  a URL is content-stable.
- Arbitrary URLs can be pinned too: flag one where it is cited
  (`<!-- pin: https://… — why it matters -->`) and run `luria remotes
  --pin`. The flag is the registration — deleting it retires the pin, so a
  pin that fires too often costs one removed comment.
- `pin = true` on a remote (or one of its schemes) registers a whole code
  family: every cited reference is pinned by a bare `luria remotes --pin`,
  and the lint reports any not yet endorsed. A bare `--pin` syncs the
  lockfile to what is registered — config declarations, `pin:` flags,
  existing pins — and never re-endorses drifted content: that always takes
  the explicit `--pin CODE`, so a scheduled sweep cannot quietly launder a
  drift finding. This repo registers its own cited `LU-ADR` references.

### Fixed

- `luria remotes --refresh` no longer writes an authoritative empty map for a
  remote it could not read: a private repository's failed discovery used to
  flip every one of that remote's references to "absent from the remote".
  Failure now leaves the remote off the lockfile — or keeps the map it
  already had — so it stays on the code-only convention.
- The migration sweep (`luria migrate`) skips `remotes.lock.json`: its JSON
  nests a remote's prefix away from its tails, so the composed-span mask
  could not tell a foreign pin key from a local code, and a scheme rename
  would have rewritten another project's namespace. Machine-derived state
  is re-derived after a migration, never re-spelled.
