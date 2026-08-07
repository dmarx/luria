### Added

- **A document can opt out of reference checking**
  ([ADR-033](record/decisions.d/ADR-033.md),
  [#37](https://github.com/dmarx/luria/issues/37)): `unlinted-file:` exempts
  a whole page from the bare-reference lint, wikilink handling and the
  reference-status scan — the blunt tool for a fixture-heavy or vendored
  document where a directive per code is maintenance without information.
  File-scoped only (backticks are already the narrow form; a bare
  `unlinted:` is reported as misuse), and the exemption is **counted**: the
  reference report lists every opted-out file and the lint prints the count,
  so the report stays a complete account of what nobody is checking
  ([ADR-007](record/decisions.d/ADR-007.md)).
- **Fixture codes get their own prefix**
  ([ADR-034](record/decisions.d/ADR-034.md),
  [#38](https://github.com/dmarx/luria/issues/38)): `FX` is registered as a
  remote whose every code resolves to the fixture-codes note in the
  directives doc, so an example like `FX-ADR-032` is a first-class reference
  that needs no `unresolved-ok` and can never collide with the real
  sequence. The template scaffold ships the same entry. Mechanizes what
  filing the real [ADR-032](record/decisions.d/ADR-032.md) taught the hard way, when five directives using
  that number as a specimen went stale at once.
