### Changed

- **A document's filename is its code and nothing else** — `ADR-013.md`, not
  `adr-013-a-documents-filename-is-its-code.md`
  ([ADR-013](record/decisions.d/ADR-013.md)). A slug in the filename is a third copy
  of the title that no tool reads and that a rename plus every inbound link is
  needed to correct, so it never gets corrected.
- **The title moves into a `title:` frontmatter field**, which the generated
  index and principles document prefer over the body's `#` heading. The heading
  falls back in — a project mid-adoption, or one that never adds the field,
  still renders a title rather than a blank cell.
- **Filename decoding lives on `Scheme`** (`filename()`, `number_of()`,
  `documents()`). Five separate places had grown their own regex for it.
  `number_of()` reads legacy `adr-010-a-slug.md` names too, so adopting Luria
  is not a rename-everything-first proposition.

### Added

- **`luria lint` reports a `title:` that disagrees with its body heading**, and
  a missing `title:`. The heading has to stay — someone opening the file alone
  needs one — so the two copies get a guard rather than a merge: rung 2 of
  [DP-3](docs/design-principles.md#dp-3), since rung 1 isn't available.
- **`tests/test_lint.py`**, covering the new check in both directions and
  across both schemes.
