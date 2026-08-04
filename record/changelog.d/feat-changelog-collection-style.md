### Added

- Fragment directories can declare a collection style
  ([ADR-028](record/decisions.d/ADR-028.md)): `append` (unchanged default —
  narrative order, marker at the end) or `changelog` — one `## <date>` batch
  per collection inserted right after the marker, newest batch first,
  fragments newest-first within it, and a stub-only batch emits nothing
  rather than an empty date heading. Luria's own changelog now collects in
  the changelog style.
