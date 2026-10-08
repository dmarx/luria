<!-- docs/paper/02-motivating-example.md -->
<!-- inactive-ok-file: ADR-010 — the paper's example of a naming decision that was superseded, cited as history -->

# A motivating example: a sentence that became false overnight

## The scenario

A project's documentation contains one sentence: *we retry writes because
`ADR-001` requires at-least-once delivery*. The sentence is correct, carefully
written, and cites its reason. Some weeks later the team decides the opposite:
consumers are not idempotent, so writes will be sent once. A second decision,
`ADR-002`, records the new choice, and the first is marked as replaced.

Nobody touches the documentation. The sentence is now wrong, and in the
ordinary arrangement of files nothing indicates it. Its text is unchanged, its
modification date is unchanged, the link it contains still resolves, and the
document it cites still exists, intact, with every argument it ever made. What
changed is a fact about a *different* file.

This is the scenario [Luria](../project-memory.md) is built around. I ran it in
a scratch project, with the two decisions declared in the framework's
frontmatter. The only edit made after the documentation was written is the one
that moves the first decision's status:

```yaml
# record/decisions.d/ADR-001.md   (before)         (after)
status: Active                  →  status: Superseded
                                   superseded_by: ADR-002
```

The documentation file was not touched. The tool's report, verbatim:

```console
$ luria lint
luria: 1 warning(s) — retired documents cited unacknowledged from current docs/code
  ADR-001 is Superseded, cited 1× in 1 file(s) — Writes are retried; delivery is at-least-once
    docs/api.md:3
```

One field moved, and a page nobody opened became a finding. That is the
whole mechanism, and the rest of this paper is an attempt to say why it is
the right mechanism to have and what has to surround it for it to work.

## What the tool is

Luria is a command-line program that maintains a repository's memory as plain
markdown files. A project declares, in one configuration file, the *kinds* of
entry it keeps: decisions, principles, papers, policies, claims, whatever its
subject matter calls for. Each kind is a *scheme* whose entries have codes
(`ADR-001`, `LIT-042`), a *status* drawn from a vocabulary the project
declares, and typed relations to other entries. Dated entries (a development
log) and small contributions waiting to be assembled (a changelog) are kept in
separate families. The pages a reader browses (indexes, tag pages, one-page
renderings of the principles, reports) are not written by anyone. They are
generated from the entries, and a lint fails the build when one is stale.
The mechanism by which a citation in prose becomes a checked reference is the
subject of the section on dependence; here it suffices that a code written
in a sentence is treated as a *claim* that the cited entry is why the
sentence is true.

The framework is named for A. R. Luria and his case study of a man who could
not forget. The record of the naming is itself instructive. The project was
first called *chester*, after Chesterton's Fence, and that decision ([ADR-010](../../record/decisions.d/ADR-010.md))
was superseded the same day by [ADR-011](../../record/decisions.d/ADR-011.md), for reasons the successor records: the
allusion named one failure the record prevents rather than the faculty it
supplies, and it framed the record as an argument against change when its
purpose is to make change cheap. [ADR-011](../../record/decisions.d/ADR-011.md) adopts the new name partly because
Shereshevsky's case carries its own warning. A record that never forgets and
never abstracts becomes unusable, and "that tension is the design brief, not a
flaw in the allusion."

## What the scenario shows

Three features of the scenario carry the argument.

1. **The wrongness is relational.** The documentation sentence did not change,
   and neither did anything inside it. Whatever made it false is located
   elsewhere. A system that watches files for change, which is what version
   control and most document tooling do, cannot see this.
2. **The old decision is not deleted.** It keeps its body and its reasoning,
   and gains a status and a pointer to its successor. The corpus can still say
   what it used to believe and why.
3. **The tool reports and waits.** It does not rewrite the sentence, and it
   does not mark the sentence invalid. There are two legitimate ways to close
   the finding. If the citation is wrong, the sentence is rewritten to cite
   the successor. If the citation is deliberate (the sentence is about the
   history, or the rejection is what is being pointed at), the author says so
   at the site, with a reason:

   ```markdown
   <!-- inactive-ok: ADR-001 — the decision this section explains replacing -->
   ```

   The reason is mandatory and lives where the finding would have appeared.
   What the tool will not allow is the third option, which is nothing,
   silently.

The same three-way shape (something is retired, its dependents are surfaced,
a person decides) is what the next sections try to explain. The scenario
is small but it already contains the criterion for being alive. Before
the status moved, the corpus held a belief and a sentence resting on it. After
it, the corpus held a *question*: does this sentence still stand? That is a
state a pile of notes cannot be in.
