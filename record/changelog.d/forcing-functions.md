### Added

- A pattern declared `report: true` is a warning class named after the pattern. Each match is a row naming its first node's document; `lint.fail_on`, `lint.baseline` and `lint.mute` take the class like a built-in one, and a `pattern-ok: <name>` directive in that document acknowledges its rows. A reported pattern may not take a built-in class's name. [ADR-131](record/decisions.d/ADR-131.md).
- A top-level `reliance:` list names the reference fields that carry dependence. When set, the pending-documents table (console, `luria reports` and the committed report) gains a column of each undecided document's transitive dependents and ranks by it, age breaking ties. Unset, the report is unchanged.
- `load_bearing: N` adds the `load-bearing` warning class: every undecided document with at least N transitive dependents.
- `unbounded-acknowledgements`, with `reliance` set: an `inactive-ok` directive that excuses a retired document its own document depends on through a reliance field, and carries no `until <date>`.

### Documentation

- `docs/directives.md` lists `pattern-ok:`. The configuration reference describes `report`, `reliance` and `load_bearing`, and quotes a `match:` that holds a property map, since `: ` is not allowed in a plain YAML scalar.
