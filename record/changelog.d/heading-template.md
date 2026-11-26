### Added

- A scheme can set how its documents write their H1, with `heading:`, a
  template over `{code}` and `{title}` ([#405](https://github.com/dmarx/luria/issues/405)). The default, `{code}: {title}`,
  is today's form. `luria new` derives the H1 from it once the title is final,
  and finds the H1 in either form when replacing a body; `heading: "{title}"`
  scaffolds `# Title`. A template that does not place `{title}`, or names
  anything else, is refused at load. Decided in [ADR-144](record/decisions.d/ADR-144.md).
