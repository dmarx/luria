### Fixed

- **Two acknowledgements stopped applying when the sequence reached [ADR-053](record/decisions.d/ADR-053.md).**
  The specimen lists in `ADR-014` and `tests/test_adr_index.py` borrowed a code
  from the real sequence, and a real fifty-third decision made it resolve. This
  is the second time — `ADR-032` went the same way — so `ADR-014` now records
  that trimming the list is the symptom fix and the `FX-` prefix is the cause
  fix.
