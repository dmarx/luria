### Added

- `luria/ci.py`: luria now notices when it is being read in a build, and says
  different things there ([ADR-029](record/decisions.d/ADR-029.md)). Detection is crude on purpose
  (`CI` plus the vendor variables) and only ever changes what is *said* — no
  write and no exit code depends on it.

### Fixed

- **The staleness remedy now names the half that matters: the output has to be
  committed.** `stale — run luria index` is complete advice in a working copy
  and half an answer in a build. Under CI the message names both legitimate
  routes — regenerate locally, or give CI a generation job that runs the
  generator and pushes what it wrote — and warns against the specific broken
  shape instead: the generator dropped into a checking job with nothing
  committing its output, which discards the result *and* leaves a following
  `luria lint` comparing the generator against itself
  ([#21](https://github.com/dmarx/luria/issues/21), [#23](https://github.com/dmarx/luria/issues/23)).
- `luria index` and `luria badges --write` warn when they write inside CI,
  saying what is lost if nothing commits — while allowing that a generation job
  writing there is exactly right. A discarded write was previously
  indistinguishable from one that landed.
- Bare `luria badges` says on **stderr** that it only printed. As a `- run:`
  step it looked exactly like a write and exited 0 having done nothing
  ([DP-1](docs/design-principles.md#dp-1)). Stdout is unchanged, so redirection still works.

### Documentation

- [`docs/adopting.md`](docs/adopting.md) gains a *Who regenerates?* section covering both
  arrangements, and full wiring for the generation job — the `needs:` + `sha`
  handoff (a `GITHUB_TOKEN` push does not retrigger workflows, so generation in
  a separate workflow strands the lint on a red it can never clear), the fork
  read-only-token guard, and a warning never to write GitHub's skip markers
  into a commit message you author, since a message documenting this workflow
  suppresses its own run.
