### Added

- **Drop-in CI for the record** ([ADR-029](record/decisions.d/ADR-029.md)): `actions/generate` regenerates the
  views, commits and pushes them as the bot, and outputs the SHA a checking
  job must read (fork PRs get a warning and an un-regenerated SHA instead of a
  403); `actions/lint` runs `luria lint` and uploads the status reports. The
  `luria init` template workflow is now the full recommended shape built from
  those actions — it previously scaffolded a verify-only lint, handing every
  new adopter a gate with nothing keeping it satisfied — and luria's own
  `ci.yml` runs the same two actions by local path, so the scaffolded workflow
  is the one this repository lives on ([ADR-009](record/decisions.d/ADR-009.md)).
- `luria/ci.py`: luria notices when it is being read in a build. Detection is
  crude on purpose (`CI` plus the vendor variables) and only ever changes what
  is *said* — no write and no exit code depends on it.

### Fixed

- **The staleness remedy now names the half that matters: the output has to be
  committed.** `stale — run luria index` is complete advice in a working copy
  and half an answer in a build. Under CI the message names both legitimate
  routes — regenerate locally, or give CI a generation job — and warns against
  the specific broken shape: the generator dropped into a checking job with
  nothing committing its output, which discards the result *and* leaves a
  following `luria lint` comparing the generator against itself
  ([#21](https://github.com/dmarx/luria/issues/21), [#23](https://github.com/dmarx/luria/issues/23)).
- Bare `luria badges` says on **stderr** that it only printed. As a `- run:`
  step it looked exactly like a write and exited 0 having done nothing
  ([DP-1](docs/design-principles.md#dp-1)). Stdout is unchanged, so redirection still works.

### Documentation

- [`docs/adopting.md`](docs/adopting.md)'s CI section leads with the scaffolded workflow and the
  two actions, and keeps what stays in the caller's hands: the fork-safe
  checkout ref (a fork's head branch does not exist in the base repo — the
  checkout fails before any push guard can help), the `needs:` + `sha` handoff
  (a `GITHUB_TOKEN` push does not retrigger workflows), and the warning never
  to write GitHub's skip markers into a commit message you author.
