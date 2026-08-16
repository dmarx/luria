### Added

- An optional `statuses.yaml` in a scheme's directory, beside `tags.yaml` and
  shaped like it: which of [ADR-003](record/decisions.d/ADR-003.md)'s five statuses the scheme uses, and what
  each one means there. A record whose status the scheme does not declare fails
  the lint, and the meanings render above the index table they explain.
- `check_status_vocabulary`: a `statuses.yaml` key outside the closed five is
  an error. Narrowing the vocabulary per scheme is the point; extending it is
  what [ADR-003](record/decisions.d/ADR-003.md) bought and this does not sell it back.

### Documentation

- `docs/configuration.md` and `docs/adopting.md` describe the file, including
  the part that is easy to get backwards — the words stay closed, only their
  meanings and their per-scheme subset are yours.
