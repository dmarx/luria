### Added

- **`[luria.schemes.X] cite`** — where a citation of one of this scheme's codes
  points. Only a `render = "document"` scheme has the choice, because only its
  sources have two addresses: their own files, and an anchor in the page they
  assemble into. `"page"` picks the file, `"view"` picks the anchor.

  **Unset means what the scheme already does** — `"view"` for a document
  scheme, `"page"` for an index scheme, which has no second address — so this
  changes nothing until a project sets it. An unknown value, or an explicit
  `"view"` on a scheme that assembles no view, is refused by name.

  The reason to want the choice: the anchors this generator emits are
  `<a name="dp-3"></a>`, raw HTML that a publisher is free to drop. Quartz
  does, so a link written against an anchor the source genuinely contains
  lands on a page with no such id — working in the repository and broken on
  the site, where nothing this project checks was looking. See
  [ADR-tmp6pv64](record/decisions.d/ADR-tmp6pv64.md).

- **`luria repair` moves links a record already wrote**, not only bare
  references. Changing `cite` governs every citation written from then on and
  nothing already on disk — those are plain markdown links, which the
  linkifier has no reason to touch. The link text is left exactly as written,
  a link with no fragment is left alone, and an anchor naming no document is
  left alone rather than swapped for a dead file.
