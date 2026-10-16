### Added

- More of the configuration reaches a view template: each scheme's
  `render` kind on `schemes()`, `chains()` and `views()` with their
  outputs, and `paths()` for the status reports, the record description
  and the configuration reference. This repository's `CLAUDE.md` uses
  them to derive its "never edit a generated file" list in the template.
  A test holds that every file `luria index` writes falls under a path
  the bootloader names.
