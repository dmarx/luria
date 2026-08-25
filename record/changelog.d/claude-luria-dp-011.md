### Added

- A design principle: **exempting a ledger from one matcher exempts it from
  none of the others.** A mechanism that rewrites instances of a pattern
  records what it rewrote, in the pattern's own spelling — so every matcher
  for that pattern also matches its own ledger, and the exemptions do not
  transfer between them.
