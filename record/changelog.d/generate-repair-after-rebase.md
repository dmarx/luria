### Fixed

- The generate action's pull-request shape no longer lints a newer push's unrepaired commits. The action rebases its repair commit onto the branch before pushing, so a run that a newer push overtook pulled that push's commits into its tree, and the lint in the same job read their bare codes and failed. That run's red was stale, since the newer run repairs them, but it read as a failure. The action now repairs again when the rebase brought in commits, and pushes that repair with its own.
