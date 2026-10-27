### Fixed

- The generate action's pull-request shape no longer lints a newer push's unrepaired commits. The action rebases its repair commit onto the branch before pushing, so a run that a newer push overtook pulled that push's commits into its tree, and the lint in the same job read their bare codes and failed. That run's red was stale, since the newer run repairs them, but it read as a failure. The action now repairs again when the rebase brought in commits, and pushes that repair with its own.

### Changed

- The template workflow `luria init` scaffolds, and this repository's own CI, cancel a pull request's run when a newer push overtakes it. The newer run repeats the older run's work, so the older run was wasted, and before the fix above it also went red. Runs outside a pull request each get a concurrency group of their own, so nothing on the default branch is cancelled or queued.
