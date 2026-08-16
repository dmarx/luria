### Changed

- **The published version is derived from the release tag** rather than a
  hand-written `pyproject.toml` field, completing the fix [#93](https://github.com/dmarx/luria/issues/93) began: `hatch-vcs`
  reads `git describe`, and the publish checkout fetches tags so there is
  something to describe against. [#93](https://github.com/dmarx/luria/issues/93)'s assertion that the built version matches
  the tag stays — deriving prevents the drift, the guard makes a recurrence loud.
