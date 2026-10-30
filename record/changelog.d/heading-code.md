### Added

- **`luria lint` checks the code in a document's `# CODE: title` heading.**
  The title check compared only the words after the code, so a heading
  naming another code passed. A scheme document's heading must now carry
  the document's own code: its temporary code on a branch, its number after
  concretization. The error names the code the heading carries and the line
  to write.

### Fixed

- **`luria concretize` writes the code it assigns into the heading**,
  whatever code the heading carried. The rename used to rewrite only the
  document's own temporary code, so a heading written with any other code
  survived it. Nucleation's NOTE-1341 kept `NOTE-tmplu4ga` that way.
  Concretize prints a line when it corrects one.
- Four of this record's decisions, [ADR-053](record/decisions.d/ADR-053.md), [ADR-082](record/decisions.d/ADR-082.md), [ADR-083](record/decisions.d/ADR-083.md) and [ADR-086](record/decisions.d/ADR-086.md),
  still had the template's `ADR-NNN` in their headings. They now carry
  their own codes.
