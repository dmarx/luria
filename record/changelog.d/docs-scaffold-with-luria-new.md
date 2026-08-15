### Documentation

- Templates and the decisions stub now point at **`luria new <kind>`** instead
  of telling the reader to copy `_template.md` by hand. The copy instruction
  predates the command and had outlived it: `new`'s kinds are derived from
  config, so `luria new <kind>` works for a scheme the moment it is declared,
  and it assigns the identity — which hand-copying does not, and which is how
  two branches end up claiming one number. Which identity depends on the
  scheme's `allocate` mode, so the comment names the mechanism rather than one
  of its two outcomes: `filing` takes the next free number on the spot, `merge`
  mints a temporary code that `luria concretize` numbers where merges
  serialize. Fixed in both the shipped
  `template/` scaffold and this project's own record, so an adopter and a
  maintainer read the same instruction.
