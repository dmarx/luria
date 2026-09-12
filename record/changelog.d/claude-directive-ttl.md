### Added

- **A directive can carry a deadline — `until <YYYY-MM-DD>`**
  ([#58](https://github.com/dmarx/luria/issues/58)).

  ```
  <!-- inactive-ok: ADR-028 until 2026-10-01 — revisit when the API settles -->
  ```

  After that date `luria` behaves as if the directive were never written: the
  check it silenced starts reporting again. The date is inclusive — good on
  the 1st, gone on the 2nd.

  An acknowledgement is a promise about the future, and some of those promises
  have a horizon. Without one, "circle back to this" becomes "forever"
  silently, which is the failure directives exist to prevent, one level up.

  It works on **every** directive, not just `inactive-ok`: `until` is parsed by
  the same parser that reads the name and the scope suffix, so it is part of
  the shape rather than a feature of one word. See
  [ADR-tmpj2uc1](record/decisions.d/ADR-tmpj2uc1.md).

- **`luria lint` reports what expired**, as its own `expired-directives`
  finding — the file, the directive, the date and the author's own reason.
  Separate from "no longer apply", because they are different facts: a stale
  acknowledgement means the subject moved under it, an expired one ran out of
  the time its author gave it. Inert must not mean invisible.

- **A date `luria` cannot read is reported, and the directive stays live.**
  `until nextweek` is a typo; dropping a suppression over one would break a
  build for a reason the message would not explain. What must not happen is a
  typo quietly meaning "forever".
