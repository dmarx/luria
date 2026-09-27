# How to run Luria in CI

CI should enforce only guarantees the record has intentionally adopted.

## What ships

`luria init` scaffolds two workflows, built on three composite actions published from the Luria repository:

- `.github/workflows/docs.yml` — on push to the default branch, `dmarx/luria/actions/generate` (with `concretize: "true"`) then `dmarx/luria/actions/lint` on the SHA it produced; on a pull request, one job running generate with `views: "false"` and then lint; and a weekly or manually dispatched `luria collect --commit`.
- `.github/workflows/pages.yml` — `dmarx/luria/actions/site` builds the site after the Docs workflow completes on the default branch, and deploys it to GitHub Pages (see [publishing](publishing.md)).

The actions' inputs:

| action | inputs |
|---|---|
| `generate` | `concretize`, `resolve`, `views` (default `"true"`), `pip-spec`, `commit-message`, `repair-message`; outputs `sha` |
| `lint` | `reports-artifact` (default `doc-reports`), `reports-path` (default `docs/reports`), `pip-spec` |
| `site` | `quartz-repo`, `quartz-ref`, `node-version`, `pip-spec`; outputs `path` |

[Adopting](../adopting.md#ci) walks through both workflows step by step, including which token the jobs push with and the hazards of other commits on the same branch.

## Core check

```console
$ luria lint
```

Lint is the check every run makes, on pull requests and on the default branch. It is not the only command that exits 1: `luria index --check` and `luria concretize --check` do too, and the generate action runs both where they apply.

## Generated views

Views — the decision index, tag pages, devlog books, reports, the README badges — are written and committed on the default branch only. A branch carries no views of its own and is not checked for them: it carries stale views by design, and `luria lint` reads sources ([ADR-068](../../record/decisions.d/ADR-068.md)).

So do not run `luria index --check` on pull requests. It runs once, in the generation job on the default branch, right after `luria index`: stale immediately after regenerating means the generator itself is broken. The generate action does exactly that when `views` is `"true"`.

[DP-2](../../record/principles.d/DP-002.md)'s rule is important here: generated shared artifacts should be written where merges serialize, not independently by every branch.

## Merge-allocated identities

Where merges serialize — the push-to-default-branch job — run the concretizer and then its guard:

```console
$ luria concretize
$ luria concretize --check
```

The first assigns permanent numbers to temporary codes; the second fails if any survived ([ADR-049](../../record/decisions.d/ADR-049.md)). The guard alone, without the concretizer before it, simply fails on every temporary code a merge brought in. The generate action with `concretize: "true"` runs the pair in that order. Never pass it on a pull request: concretizing on a branch is the premature number claim the temporary codes exist to avoid.

## Reports

`luria reports` writes the status reports (pending decisions, reference status); `--out DIR` sends them somewhere other than the configured directory, such as an artifact staging directory. The lint action runs it after the lint whether or not the lint passed, and uploads the result as the `reports-artifact`.

## Fragment collection

`luria collect --commit` assembles fragments into their targets, deletes the fragments, and commits the result. Collection is deliberately not per-merge: a bot commit on every merge races in-flight rebases, so the scaffold runs it weekly and on manual dispatch ([ADR-002](../../record/decisions.d/ADR-002.md)). See [journals and fragments](journals-fragments.md).

## Remote verification

Choose the configured network policy deliberately, with `lint.network` in `luria.yaml`:

- `auto` (the default) asks about identifiers the lockfile has no answer for, and reports them as unchecked when the network is not there,
- `never` answers only from the lockfile — the hermetic build,
- `require` makes an unverifiable identifier a failure.

A hermetic CI run and a network-required CI run make different guarantees.

The lint never writes `remotes.lock.json`; it only reads it. The lockfile's resolved titles are written by `luria remotes --resolve` where merges serialize — the generate action's `resolve: "true"` input, on the default-branch job only — so no branch conflicts with another over it ([ADR-112](../../record/decisions.d/ADR-112.md)). See [remotes](remotes.md).

## Enforcement policy

Do not make every new warning fatal by default.

Luria's [ADR-035](../../record/decisions.d/ADR-035.md) model supports:

- reported classes,
- `fail_on`,
- baselines,
- acknowledgements.

Promote a class when the project is ready to treat it as a guarantee; [findings](findings.md) shows the configuration. The scaffold starts with one: `workflow-temp-codes` is in `fail_on`, because the default token cannot push a concretized code into `.github/workflows/`.
