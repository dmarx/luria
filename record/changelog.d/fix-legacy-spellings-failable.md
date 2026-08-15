### Fixed

- Every warning class `status_sections` can emit is now nameable in
  `[luria.lint] fail_on`, and a test asserts it over the whole vocabulary
  rather than one class. `legacy-spellings` had been emitted since rung one
  landed but was missing from `FAILABLE`, so a project asking to enforce it was
  told *"which is no warning class"* — the dial rejecting a notch it was
  already printing on, which is
  [DP-1](docs/design-principles.md#dp-1) inside the guard written to catch
  exactly that. The tuple entry itself rode in unremarked with the
  `narrow-titles` work; this is the test that would have caught the omission,
  and the changelog line it never got.
