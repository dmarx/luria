# Schemes

A scheme is a family of numbered records. `ADR` is the one luria ships; it is
not the product.

## What a scheme is

Six things:

| | |
|---|---|
| a **prefix** | `ADR`, `CLM`, `RFC` — the code a citation uses |
| a **directory** | where the records live, conventionally `record/<name>.d/` |
| a **template** | `_template.md`, what `luria new <kind>` copies |
| a **tag vocabulary** | `tags.yaml` — what each browsing tag means |
| a **status vocabulary** | `statuses.yaml` — what each status means *here* |
| a **rendering** | an index of many records, or one collected document |

Declared in `luria.toml`:

```toml
[luria.schemes.RFC]
dir = "record/proposals.d"
output = "docs/proposals"
active = "Active"
render = "index"
```

**Declaring any scheme replaces the shipped family.** A project that wants
decisions *plus* proposals declares both — otherwise `ADR` vanishes and every
citation of it dangles.

## Why you would want more than one

Because the propagation is only as useful as the graph is real, and one
undifferentiated pile of "documents" has no edges worth checking.

The question to ask is not "what kinds of document do we have?" but **"what
would I want to retire on its own?"** If two things always die together they are
one scheme, probably one record. If either could be withdrawn while the other
survives, they are two — and the citation between them is now load-bearing.

## A worked example

One project reads a corpus of philosophical arguments — eight book drafts and a
few hundred conversation transcripts — and runs six schemes:

| Scheme | Holds | Status means |
|---|---|---|
| `CLM` | one proposition the corpus asserts | does the record still assert it |
| `ARG` | premises → conclusion, written as CLM citations | is this still our reading of the argument |
| `CON` | a term of art | does the term pick something out |
| `POS` | what *this* record commits to | endorsement |
| `ADR` | how the corpus is read | in force |
| `DP` | standing values the decisions cite | in force |

The load-bearing edge is `ARG` → `CLM`: an argument states its premises **as
citations**, never as prose. So when a claim is refuted and set to `Rejected`,
every argument resting on it becomes a finding. In that project's first
retraction wave, twenty-three claims moved and twenty-seven arguments surfaced —
across files nobody had opened.

Note what makes that work. It is not that the schemes exist; it is the rule that
*premises are citations*. A scheme whose records describe their dependencies in
prose contributes nothing to the graph.

## Designing one

**Start from the retirement.** Write down the sentence you would want to see in
a finding list: *"CLM-018 is Rejected, cited 4× in 3 files."* If that sentence
would be useful, the scheme is real. If you cannot imagine retiring one, you
want tags on an existing scheme, not a new one.

**Give it a status vocabulary immediately.** The five words are fixed; their
meanings are not, and they will differ from your other schemes. Writing
`statuses.yaml` on day one is the cheapest way to avoid the most common failure
in this system, which is a scheme where everything sits at `Active` forever
because nobody said what else would mean.

```yaml
# record/proposals.d/statuses.yaml
Active:
  label: Open
  blurb: proposed and still under consideration
Rejected:
  label: Declined
  blurb: considered and turned down; the reasoning is the point
```

**Decide the rendering.** `render = "index"` gives a table with tag pages —
right when records are browsed and arrived at by link. `render = "document"`
collects every record into one page in number order — right when they are read
front to back, like a set of principles.

**Consider `requires`.** A scheme can demand frontmatter fields beyond the
standard set:

```toml
[luria.schemes.CLM]
requires = ["source", "locus"]
```

Now a claim that cannot say where it came from fails the lint. This is what
makes moving a record between schemes safe to automate — the moved file fails
until a person supplies what the target scheme's template would have prompted
for.

**Consider tag groups**, if your tags are an axis rather than a pile:

```toml
[luria.schemes.ARG.tag_groups.strength]
tags = ["sound", "overreach", "invalid"]
require = "exactly-one"

[luria.schemes.ARG.tag_groups.failure]
tags = ["equivocation", "gap", "analogy", "circular"]
excluded_by = ["sound"]
```

Exactly one strength tag, and a `sound` argument may not also name a failure
mode. Most vocabularies are piles and want none of this; some are axes, and an
axis nobody enforces drifts on the fourth record.

## Numbering, and parallel work

By default a scheme takes the next free number when you run `luria new`. That is
fine when one person files at a time and a nuisance when three branches do —
they all mint `ADR-042`.

```toml
allocate = "merge"
```

mints a temporary code instead (`ADR-tmpk3n1p`), which `luria concretize`
numbers where merges serialize — on the default branch, in CI, never on a pull
request. A temp code on the trunk means the concretizer did not run, and
`luria concretize --check` is the guard for that.

The tradeoff is real: temporary codes are ugly in review, and numbering carries
information — it is the order things were decided. Use `merge` when collisions
actually happen.

## Citing across schemes, and across repositories

Within a repo, any code cites any other. Across repos, declare a **remote**:

```toml
[luria.remotes.LU]
name = "luria"
repo = "dmarx/luria"
ref  = "main"
dir  = "record/decisions.d"
```

Now `LU-ADR-013` in prose resolves to a URL. This is how sibling records cite
each other — one repo per corpus, per thinker, per subsystem — without vendoring
anything.

A foreign code is *not* status-checked: luria cannot know whether another
repository has retired something. What it does check is that you did not
hand-write the URL when construction would have produced it, since a
hand-written one is frozen at writing time.

## What not to make a scheme

**A place to put notes.** That is a journal — dated, historical, never
retroactively wrong.

**Anything assembled from pieces.** That is a fragment directory — a changelog
or digest, collected on a cadence.

**A taxonomy.** If you want to slice existing records, that is `tags`, and tags
are open by design. A new scheme costs a directory, a template, two
vocabularies, and a prefix in everyone's head.

**A distinction the five statuses already carry.** Two schemes that differ only
in whether the thing is agreed on are one scheme with a status.
