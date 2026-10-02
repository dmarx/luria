### Fixed

- `source-mismatch` no longer fires when the recorded and upstream titles differ only in spelling: TeX math and symbol commands (`$O(n^2)$`, `$\mu$P`), TeX or Unicode accents, Unicode superscripts, or Greek letters against their names. A nickname or a trimmed subtitle is still a mismatch ([#340](https://github.com/dmarx/luria/issues/340)).
- A `source-ok:` that only excused such a spelling difference is now reported as excusing nothing, and can be removed ([#340](https://github.com/dmarx/luria/issues/340)).
