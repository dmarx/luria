### Added

- **Published to PyPI** ([ADR-027](record/decisions.d/ADR-027.md),
  [#3](https://github.com/dmarx/luria/issues/3)): `pip install luria`.
  Publishing runs through GitHub trusted publishing — a `publish.yml`
  workflow whose `pypi` environment identity is the whole credential — on
  every GitHub release, gated by a cold-install smoke test that scaffolds a
  fresh project from the built wheel (`init → index → journal new → lint`).

### Fixed

- The scaffold ships inside the package (`luria/template/` in the wheel)
  instead of leaking a bare `template/` directory into `site-packages`,
  where it would have collided with any other package shipping one.
  `luria init` resolves the packaged location first and falls back to the
  repository top level in a checkout.
- A freshly scaffolded project now lints with zero warnings: the
  illustrative wikilinks in the template's CLAUDE.md no longer read as
  dangling codes.
