### Fixed

- **The published version and the git tag can no longer disagree.** 0.4.0 was
  tagged and released against a tree whose `pyproject.toml` still said
  `0.3.0`, so `python -m build` produced a *0.3.0* wheel and PyPI rejected it
  as a duplicate — after the GitHub release was already published, and with
  `twine check` and the cold-install smoke test both passing, because neither
  validates identity. `pyproject.toml` is bumped to 0.4.0, and the build job
  now asserts the built wheel's version equals the release tag (`v` prefix
  tolerated) before the publish job ever runs. The version was a
  hand-maintained projection of a source of truth kept in two places, which is
  what [DP-5](docs/design-principles.md#dp-5) predicts will drift; this is its
  rung-2 remedy — guard the property. Rung 1, deriving the version from the
  tag with `hatch-vcs`, is the better fix and needs `fetch-depth: 0` on the
  publish checkout, so it is left as a follow-up rather than bundled into a
  release-unblocking change.
