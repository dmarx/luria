### Added

- An `undescribed-schemes` lint class names each scheme that declares neither `title` nor `blurb`, so that `docs/record.md` cannot say what its family is for. It is warn-first like every class, so `lint.mute` silences it and `lint.fail_on` makes it a gate. The default ADR scheme, the scaffolded ADR and DP schemes, and luria's own schemes now describe themselves, so a fresh `luria init` still prints no findings.

### Fixed

- `docs/record.md` leaves out a section that has nothing to show, heading and all. "What each family is" used to render its heading and introduction over nothing when no scheme described itself. That something is missing is reported by the lint, not written into the document.

### Changed

- `docs/record.md` is rendered from a template luria ships, `luria:record.md.j2`, in the sandbox views use ([ADR-tmp1m1lj](record/decisions.d/ADR-tmp1m1lj.md)). Its prose and layout are in the template, and `record_doc.context` supplies only facts from the config. The output is unchanged: it was byte-identical on luria's record, nucleation's, a fresh init and three fixtures.
