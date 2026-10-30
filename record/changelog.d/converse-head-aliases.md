### Fixed

- The converse fixer now reads the HEAD baseline through derived aliases, as it already read the working tree. An edge HEAD spelled by alias (`LIT-Jia-2015-1146`) named no document, so withdrawing it read as "nothing changed" and `luria link --fix` wrote it back instead of removing its converse. It now prunes the stale side, as [ADR-084](record/decisions.d/ADR-084.md) says a withdrawal should.
