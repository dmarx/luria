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
  in the browser ([ADR-148](record/decisions.d/ADR-148.md)), a LadybugDB export ([ADR-146](record/decisions.d/ADR-146.md)), and views
  computed in the browser instead of committed as markdown ([ADR-149](record/decisions.d/ADR-149.md)).
- Two more proposed decisions and a principle for the publishing overhaul:
  every generated view becomes a template luria ships ([ADR-147](record/decisions.d/ADR-147.md)); a
  journal may be consumed into its period books on the project's schedule,
  holding back entries a review hasn't read ([ADR-145](record/decisions.d/ADR-145.md)); and
  configuration says what the record is while CI says when the work runs
  ([DP-019](record/principles.d/DP-019.md)).
