### Added

- **[ADR-058](record/decisions.d/ADR-058.md): luria is a truth maintenance system, and should say so.**
  Nobody could name the category, so every description reached for a new
  metaphor. The category exists and is from 1979. The documentation now leads
  with the mechanism — retract a premise, and the build names what rested on it
  — and gives TMS as the second sentence.
- `docs/concepts.md` — the model and its prior art.
- `docs/quickstart.md` — fifteen minutes ending in a real finding.
- `docs/schemes.md` — designing record families beyond decisions.
- `docs/cli.md` — every command, and the CI wiring including the version-split
  trap.
- `docs/api.md` — the Python surface, with stability marked.
- `docs/in-practice.md` — the three existing records compared: luria itself,
  strata-g, and a corpus project. What varied, what drove each choice, and
  the short list of things all three do the same way.
- `CONTRIBUTING.md`.

### Changed

- Every hand-written page rewritten from scratch: `README.md`,
  `docs/README.md`, `docs/adopting.md`, `docs/directives.md`,
  `docs/project-memory.md`. The README's four competing self-descriptions are
  replaced by one lead and one placement.
