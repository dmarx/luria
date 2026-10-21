### Added

- `schemes.X.citable_from` lets a scheme name the citers that may cite one of
  its retired statuses with no acknowledgement, as `PREFIX:Status` lists
  keyed by status: `Answered: [QUESTION:Open]` lets an open question cite an
  answered one without warning. A citation from any other scheme, any other
  status, or a file outside the record still warns. An `inactive-ok` that
  covered only such a site is now reported stale, with the reason. The
  loader refuses an entry naming an unknown status, the scheme's own
  `active` word, an undeclared citer scheme, or a status the citer's
  vocabulary lacks ([ADR-tmpfu1s6](record/decisions.d/ADR-tmpfu1s6.md)).
