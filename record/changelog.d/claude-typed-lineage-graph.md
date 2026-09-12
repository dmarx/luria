### Added

- **`luria site` draws each document's typed lineage on its page.** Under a
  `## Lineage` heading at the foot of the page, the document's `superseded_by:`
  / `influenced_by:` / declared-relation edges are rendered as an interactive
  graph — coloured by relation, with a legend, and every node a link to that
  document's published page. It appears only where lineage exists (58 of 280
  staged pages on this record) and sits **beside** Quartz's own graph rather
  than replacing it: measured, the typed-edge graph reaches 47% of scheme
  documents and none of the journal entries, so a swap would have left most
  pages with an empty box. See [ADR-tmpronup](record/decisions.d/ADR-tmpronup.md).
- Codes belonging to a scheme rendered into one assembled document (design
  principles) resolve to their anchor in that document, through the same
  `wikilink_target` resolver the rest of the record links by. On this record
  that is 50 of 122 typed-edge endpoints, so a graph without them would have
  drawn less than half the lineage.
- The viewer is vendored from strata-g ([SG-ADR-237](https://github.com/dmarx/strata-g/blob/main/docs/decisions/ADR-237.md), [SG-ADR-238](https://github.com/dmarx/strata-g/blob/main/docs/decisions/ADR-238.md)) with a
  content-hash pin, served once from the site root, and written only when a
  page references it.

### Changed

- `luria site`'s report now says how many pages got a lineage graph.
