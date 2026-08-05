### Added

- `luria/ci.py`: luria now notices when it is being read in a build, and says
  different things there ([ADR-029](record/decisions.d/ADR-029.md)). Detection is crude on purpose
  (`CI` plus the vendor variables) and only ever changes what is *said* — no
  write and no exit code depends on it.

### Fixed

- **The staleness remedy no longer names the one action that must not be taken
  in CI.** `stale — run luria index` is correct in a working copy and disables
  the check inside a checking job, where a generator ahead of `luria lint`
  makes it compare the generator's output against itself. Under CI the message
  now says to regenerate locally, commit the result, and not to add the
  generator to that job ([#21](https://github.com/dmarx/luria/issues/21)).
- `luria index` and `luria badges --write` warn when they write inside CI,
  where the result is usually discarded at job end — previously a wasted write
  was indistinguishable from one that landed.
- Bare `luria badges` says on **stderr** that it only printed. As a `- run:`
  step it looked exactly like a write and exited 0 having done nothing
  ([DP-1](docs/design-principles.md#dp-1)). Stdout is unchanged, so redirection still works.

### Documentation

- [`docs/adopting.md`](docs/adopting.md): the badges section says who runs the generator and that
  its output is committed; the CI section states *a checking job runs nothing
  that writes* as a rule, with the reason — the failure it produces is a green
  check.
