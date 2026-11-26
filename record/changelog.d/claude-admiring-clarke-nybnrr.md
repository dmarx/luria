### Added

- `actions/site` takes a `timings` input. On, it runs `luria site` with
  `LURIA_TIMINGS=1`, runs `quartz build --verbose` with every line stamped by
  the new `luria.site_perf`, and uploads a `site-perf` artifact — step
  durations, Quartz's phase totals, a per-emitter timeline, the slowest
  markdown files, and the built output's files and bytes by kind (per-page
  social cards counted apart, `contentIndex.json` named) — also written to the
  job summary. Off by default.
- luria's own Pages workflow, and the template's, run that timed build weekly
  (Wednesdays 04:23 UTC) and on demand via the `timings` dispatch input, so the
  cost of publishing is a series rather than an anecdote.

### Documentation

- Three proposed decisions for replacing the Quartz publisher, with
  requirements drawn from CI history: a bespoke shell that renders the record
  in the browser ([ADR-tmpj6kwd](record/decisions.d/ADR-tmpj6kwd.md)), a LadybugDB export ([ADR-tmpc1dme](record/decisions.d/ADR-tmpc1dme.md)), and views
  computed in the browser instead of committed as markdown ([ADR-tmpnqetk](record/decisions.d/ADR-tmpnqetk.md)).
