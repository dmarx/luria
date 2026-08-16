### Fixed

- **A generated view the project gitignores is no longer reported stale.** A
  project can point `[luria.paths] reports` at a build directory and publish
  the result as a CI artifact instead of committing it. A fresh clone then
  never has the file, so *missing* read as *stale* — and the remedy the
  failure printed, "regenerate and commit the result", is the one thing
  `.gitignore` forbids. Downstream that meant a docs job red on every commit
  for a day, on a check nothing could satisfy, which is
  [DP-1](docs/design-principles.md#dp-1) wearing a green hat: the tool refused
  and its explanation was impossible to act on. `--check` now excludes
  gitignored outputs from all three staleness kinds. Writing is unchanged —
  `luria index` still renders an ignored view, because *not committed* is not
  *not wanted*; that report is exactly what the artifact upload publishes.
- **`luria lint` and `luria index --check` share one staleness rule set.** They
  each had their own copy of the same three rules — stale view, orphan in a
  view directory, drifted README badges — and the fix above landed in one of
  them, so `lint` went on rejecting the identical tree the generator had just
  called current. That is the fixer/linter split this package exists to
  prevent, reproduced inside the package. `adr_index.staleness()` is now the
  single answer both consume; only the wording stayed with the linter, because
  a build log and a `--check` want different sentences. A test pins the
  invariant from outside: whatever one command says about a tree, the other
  says too.
