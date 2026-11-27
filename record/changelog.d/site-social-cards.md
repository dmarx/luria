### Added

- `site.social_cards` (default `true`): set it `false` to drop Quartz's
  per-page social-card images. Each page's preview then uses one site-wide
  image. On luria's own site the cards were 54 s of a 74 s Quartz build, and
  540 of its 1,642 files, so luria's record turns them off.

### Changed

- luria's Pages workflow deploys only from `main`. A run dispatched from
  another branch, for instance to time a site change before it merges, builds
  and uploads its `site-perf` report without publishing.
