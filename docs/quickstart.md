# Quickstart

Fifteen minutes, ending with luria telling you something you did not already
know. Do it in a scratch repo first — everything here is reversible, but the
last step deliberately breaks the build.

## 1. Install and scaffold

```console
$ pip install luria
$ mkdir /tmp/memory-demo && cd /tmp/memory-demo && git init
$ luria init
  write  luria.toml
  write  record/decisions.d/_template.md
  write  record/decisions.d/README.stub
  ...
wrote 18 file(s), skipped 0 existing.

Next: `luria index` to build the generated views, then `luria lint`.
```

`init` never overwrites, so it is safe to run in a repo that already has files.
Add `--issue-url https://github.com/you/repo/issues/{n}` and bare `#42` in prose
becomes a link too.

```console
$ luria index && luria lint
luria: docs lint clean
```

A green build on an empty record. Now make it mean something.

## 2. Write a decision

```console
$ luria new adr
record/decisions.d/ADR-001.md
```

Open it. The template is mostly commentary explaining each field — read it once,
then delete the parts you have internalised. Fill in:

```yaml
status: Active
title: Sessions are stored in Redis, not in the database
tags:
- infrastructure
```

and give the body a real **Context**, **Decision**, **Alternatives considered**
and **Consequences**. The alternatives section is the one that pays: it is what
stops the decision being re-litigated, and what tells a future reader whether
their new idea is actually new.

Two rules the lint will enforce, so you may as well know them now:

- The body's `# ADR-001:` heading must match the frontmatter `title:`.
- `status:` must be one of the five words.

Now a second one that depends on the first:

```console
$ luria new adr
record/decisions.d/ADR-002.md
```

```yaml
title: Session tokens are opaque, with no embedded claims
```

In its **Context**, write the dependency in prose, citing the code bare:

```markdown
Sessions already live in Redis (ADR-001), so a lookup is one round trip and
there is no reason to smuggle state into the token itself.
```

## 3. Link and generate

```console
$ luria link --fix
record/decisions.d/ADR-002.md: 1 reference(s)
linked 1 reference(s) in 6 file(s)
```

That bare `ADR-001` is now a markdown link with a target you did not have to
compute. **This is the habit to build.** Write bare codes; let the fixer spell
them. A hand-written target that looks right beside the source is wrong in the
view the prose renders into.

```console
$ luria index
Wrote 4 file(s) from 2 ADRs, 6 DPs.
```

Open `docs/decisions/README.md` — an index table built from your frontmatter,
with tag pages beside it. Do not edit it. Edit the record and regenerate; a
stale view is a lint failure.

```console
$ luria lint
luria: docs lint clean
```

## 4. Change your mind

This is the part that is not like other documentation tools.

Redis turned out to be the wrong call. Open `ADR-001.md` and change one line:

```yaml
status: Rejected — sessions moved to signed cookies; Redis was a single point of failure
```

Leave the body alone. Rejection is a *status*, not a deletion — the reasoning
that turned out wrong is the most valuable thing in the file.

```console
$ luria index && luria lint
luria: 1 warning(s) — retired documents cited unacknowledged from current docs/code
  ADR-001 is Rejected, cited 1× in 1 file(s) — Sessions are stored in Redis, not in the database
luria: docs lint clean
```

There it is. Nothing about `ADR-002` changed, and luria knows its context now
argues from something you abandoned. In a real repository that list is dozens of
lines long and spans files you had forgotten existed.

## 5. Resolve the finding

Every finding gets one of three answers, and picking is the work.

**Repair it.** `ADR-002`'s reasoning genuinely depended on Redis, so the decision
needs revisiting. Supersede it:

```yaml
# ADR-002
status: Superseded — by ADR-003, which re-decides this on signed cookies
```

**Acknowledge it.** Sometimes the citation is *correct* — the whole point of the
new record is to say what the old one got wrong:

```markdown
<!-- inactive-ok: ADR-001 — the decision this one replaces; cited as target, not support -->

Sessions used to live in Redis ([ADR-001](ADR-001.md)), which made the cache a
single point of failure for authentication.
```

The annotation carries a reason, and it reports itself the day it stops
applying — acknowledge a citation, then delete the citation, and the lint tells
you the annotation is stale.

**Leave it listed.** A warning is not a failure. If you have not decided yet,
the finding stays in `docs/reports/reference-status.md` and in the badge count,
which is where an undecided thing belongs.

## 6. Turn it up

Once the record is clean, promote the class you care about:

```toml
# luria.toml
[luria.lint]
fail_on = ["retired-citations"]
```

Now a retired citation fails CI rather than printing. Acknowledged ones never
fail, so the escape hatch survives enforcement.

## 7. Wire it into CI

```yaml
- uses: dmarx/luria/actions/generate@main
  with:
    concretize: ${{ github.event_name != 'pull_request' }}
- uses: dmarx/luria/actions/lint@main
```

The generate action regenerates the views and commits them, so a contributor who
forgets `luria index` does not fail the build for it. Pin `pip-spec` to a
release once you depend on this.

## What you just built

A justification graph. Two records, one citation, and a retraction that
propagated. Scale that to a hundred decisions and the property that matters is
this: **you can change your mind and find out what it costs**, instead of
discovering three years later that half your architecture rests on a premise
somebody quietly abandoned.

## Next

- [Concepts](concepts.md) — the model, and the prior art it comes from.
- [Schemes](schemes.md) — record families beyond decisions. This is where it
  gets interesting.
- [Adopting](adopting.md) — doing this to a repo that already has ten years of
  history.
