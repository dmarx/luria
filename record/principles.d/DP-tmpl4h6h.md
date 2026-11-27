---
status: Active
title: 'Configuration says what the record is; CI says when the work runs'
version: 1
tags:
- process
date: '2026-11-26'
influenced_by:
- ADR-tmpbyqjw
origin: >-
  Asked to make journal consumption run on its own cadence, the first design
  put a `cadence:` key in `luria.yaml` and a daily `luria collect --due` to read
  it. The owner pointed out that a schedule is CI configuration, not record
  configuration. The same line had been drawn without saying so when the
  site build's timing switch became an action input and an environment
  variable rather than a `luria.yaml` key.
summary: >-
  `luria.yaml` holds what is true of the record and what a command produces
  from a given tree: schemes, fields, vocabularies, rules, what consuming a
  journal means. The workflows hold when, where and by whose trigger a command
  runs: schedules, runners, events, how much to log. Test: would the setting
  differ between running the command by hand and running it in CI? If it
  would, it belongs to CI.
---

# DP-tmpl4h6h: Configuration says what the record is; CI says when the work runs

`luria.yaml` describes the record: its shape, its rules, and what each
command produces from a given tree. The workflows describe the running of
it: when a command runs, on what machine, on what trigger, with how much
logging. **The test: would the setting change if you ran the same command by
hand?** If yes, it is CI's. If no, it is the record's.

Why it matters: a schedule in `luria.yaml` is a second scheduler, a field
that a cron has to read and a `--due` flag has to evaluate. It is also
invisible to anyone who looks for schedules where schedules live, in the
workflow files. A rule in a workflow is the opposite mistake: the record
behaves differently when run by hand, so a contributor's local lint passes
what CI fails.

Applied here:

- **Collection cadence is a cron per directory** in the docs workflow
  (`luria collect --dir …`). What collecting a journal *means* (closed
  periods only, the retro hold) is `luria.yaml`'s ([ADR-tmpbyqjw](../record/decisions.d/ADR-tmpbyqjw.md)).
- **The site build's timing** is the `timings` input of `actions/site` and
  the `LURIA_TIMINGS` environment variable, not a config key. It changes how
  much a run reports, not what it produces.
- **`lint.fail_on` is configuration**, because it changes what a correct
  record is: a local run and a CI run must agree on it.

The corollary that costs something: a CI setting is per repository, so every
adopter restates it. That cost is paid in the template workflows luria ships,
not by moving the setting into `luria.yaml`. The template is where a project
starts from, and its own copy is where it changes the cron.
