### Added

- **The published site can wear your brand**
  ([ADR-043](record/decisions.d/ADR-043.md),
  [#13](https://github.com/dmarx/luria/issues/13)): four optional
  `[luria.site]` keys — `icon`, `logo`, `logo_dark`, and a `theme` table that
  merges over the generator's palette by name. An unknown colour name is
  refused with the known ones listed rather than dropped, and a project that
  sets none of them gets exactly the site it had before.
  - **The favicon is rasterized during the build**, from whatever `icon`
    points at, using the `sharp` Quartz already depends on. Point it at the
    vector master: no derived PNG is committed, so none can drift
    ([DP-3](docs/design-principles.md#dp-3)).
  - **The logo replaces the site title** in the sidebar, baked once per
    theme. Artwork exposing a `--luria-ink` custom property is re-inked to
    each theme automatically; anything else needs `logo_dark` or is used as
    it stands.
- **Luria's own record wears the brainslug kit**: paper and ink from the
  kit's two colours, the horizontal lockup in the sidebar, and a new
  `luria_project_memory_icon.svg` — the mark on a paper badge, contours
  thickened so the line art still reads at 16px — as the favicon.

### Fixed

- **`actions/site` no longer fails the build for a project with no favicon**
  ([#73](https://github.com/dmarx/luria/issues/73)): the icon lookup used
  `ls … 2>/dev/null | head -1`, and under the step's own `set -euo pipefail`
  an unmatched glob ends the step before Quartz ever runs. Silencing a
  command's stderr reads as handling its failure and isn't. It could not
  bite this repository, which always configures an icon; it would have bitten
  the first adopter who didn't.
