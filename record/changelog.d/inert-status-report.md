### Added

- `inert-status`: a scheme where every record shares one status is reported.
  `active` is what `retired-citations` reads, so nothing is ever retired there
  and the citation checks cannot fire — the build is green because nothing is
  being judged rather than because nothing is wrong. A warning by default,
  nameable in `fail_on`. Exempt below ten records, for a `render = "document"`
  scheme, and for a scheme that declares exactly one status on purpose.
