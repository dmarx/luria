### Changed

- **The CLI is driven by Fire** ([ADR-039](record/decisions.d/ADR-039.md),
  proposed — this ships as a draft PR): every command is a plain typed
  function (`<module>.run`), flags and help derive from signatures and
  docstrings, and the hand-rolled dispatcher plus every module's argparse
  layer are deleted (~150 lines). Failure is signalled by `SystemExit`
  only — Fire prints return values, and a CI gate's exit code is not
  output. Every existing invocation spelling (`--fix`, `--check`,
  `--commit`, `new adr --title …`) parses identically; help output becomes
  Fire's house format. `fire>=0.7` joins PyYAML as a runtime dependency.
