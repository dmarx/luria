### Added

- **Wikilinks** ([ADR-025](record/decisions.d/ADR-025.md),
  [#9](https://github.com/dmarx/luria/issues/9)): `[[ADR-013]]`,
  `[[SG-DP-18]]`, `[[ARXIV-2403.05530|a label]]` — typed references the
  author asserts, resolved against everything the machinery can construct
  (local scheme codes including the bare `DP-3` spelling, document-scheme
  anchors, remote and uid-remote codes, issue numbers with no cue needed).
  `luria link --fix` consumes them into plain markdown links; an
  unresolvable wikilink is a lint violation with its causes named, because
  an explicit request deserves an explicit refusal.
