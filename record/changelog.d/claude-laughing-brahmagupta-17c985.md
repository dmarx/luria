### Added

- `lint.inactive_ok`, the config-level form of the `inactive-ok` directive:
  a list of entries, each a one-hop path pattern over the reserved `cites`
  edge and a mandatory reason.
  `match: "(:QUESTION {status: 'Open'})-[:cites]->(:QUESTION {status: 'Answered'})"`
  lets an open question cite an answered one without warning. A citation
  from any other scheme, any other status, or a file outside the record
  still warns. Properties are literal equality on any frontmatter field, as
  in `patterns.X`. An `inactive-ok` made redundant by a rule is reported
  stale, naming the rule, and so is a rule that sanctions no citation. The
  loader refuses, by `lint.inactive_ok[N]`, anything but one `cites` hop,
  variable length, `WHERE NOT`, an unknown scheme or field, and a missing
  reason ([ADR-tmpfu1s6](record/decisions.d/ADR-tmpfu1s6.md)).
