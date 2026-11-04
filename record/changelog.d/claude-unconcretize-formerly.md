### Changed

- `luria unconcretize` now records the given-back code under the document's `formerly:` by default, so a citation the rewrite cannot reach still finds the document once it is numbered again. `--noformerly` records none, which is the choice for a branch whose number the trunk took. The rewrite also leaves other documents' `formerly:` blocks alone ([ADR-141](record/decisions.d/ADR-141.md), superseding [ADR-140](record/decisions.d/ADR-140.md)).
