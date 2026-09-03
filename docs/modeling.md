# Designing a record

Luria ships with decisions, principles, a changelog and a devlog. That is a
**default, not the product**. The product is four families of table and a set
of constraints, and nothing in the code spells `ADR` — it is simply the scheme
the package ships with. This page is how to decide what *your* record is made
of.

## Identity, standing, relation

Not all documentation is record material. Three properties separate the two,
and material with all three is what this machinery is for:

**Identity.** Something will refer to this entry later, by name. Not "see the
architecture guide" but "per RFC-7" — a reference precise enough that a
checker can follow it and tell you when it breaks.

**Standing.** The entry can stop being in force without becoming untrue *that
it was once believed*. A decision gets superseded; a tutorial just gets
edited. Standing is what lets a record hold its own history instead of
overwriting it.

**Relation.** Entries cite each other, supersede each other, derive from each
other — and the relationships matter enough that you would want to be told
when one dangles.

A getting-started guide has none of these. Nothing cites paragraph four of
it, and it has no status worth tracking. Leave it as prose in `docs/`; the
lint will still check that your index links it.

## Which family

| If the entry… | it is a |
|---|---|
| will be cited by name, and can be in force or not | **scheme** — it gets a code |
| is true about a moment and never revised | **journal** — it gets a timestamp |
| is written now to be absorbed into a shared document later | **fragment directory** |
| lives in someone else's namespace | **remote** — it gets a prefix |

The distinguishing question for a scheme is *citation*, not importance. A
numbered code exists so other things can point at it; material nothing will
ever point at does not need one, and numbering it anyway produces a scheme
whose `status:` column nobody maintains.

The distinguishing question for a journal is *revision*. A journal entry is a
dated observation — true when written, still true, never updated. That is why
its entries persist while a fragment's are consumed: the fragment exists to
become part of something else, the journal entry exists as itself.

## Index or document

Every scheme declares a `render`, and the two words name the output rather
than the question you are answering. The question is **how the set is read**.

> Would somebody sit down and read all of these, in order, in one go?

If yes, that is `render = "document"`. The entries concatenate into one page
and each gets a stable anchor, so a citation points at a *section*. Design
principles work this way: there are nine of them, they argue with each other,
and reading the fourth without the third is worse than not reading either.

If no — people arrive at one entry by following a link, and never read the
set — that is `render = "index"`. The entries stay separate files and the view
is a table of them plus a page per tag. Decisions work this way: there are
sixty, nobody reads them end to end, and you get to one because something
cited it.

Two things follow from the reading, and both are worth checking your answer
against:

- **Count.** A set that grows past twenty or so stops being readable whole,
  whatever its author intended. If you expect it to keep growing, it is an
  index, and choosing `document` now means a migration later.
- **How a citation should land.** `DP-3` taking a reader to a section of a
  page they can then keep reading is the point of a document render. `ADR-012`
  taking them to a file with its own context is the point of an index.

The mechanical consequences — what gets generated, what `output` means, which
checks apply — are in
[project memory](project-memory.md#what-each-render-produces).

## When is it two schemes?

The question that takes the most thought, and it has a usable rule:

> **If one field would have to mean different things depending on the entry,
> you have two schemes.**

A worked case. An anthology of ML training practice kept papers and
recommendations in one structure, where each paper carried `attic` and
`experimental` flags alongside a list of the recommendations drawn from it.
Those flags are judgements about a *paper*; the recommendations are judgements
about *practice*. One structure meant one status field, so the two claims could
never disagree.

They needed to. A foundational paper stays worth reading while one of the
recommendations drawn from it goes stale — that is the normal life of a
citation. And a paper retired as uninteresting can still be the source of
something everybody does. Under one scheme, retiring the paper retired the
practice, so neither could be said.

Split into two schemes, each got its own status field, and the relationship
between them became a citation the lint can follow — a live practice sourced
from a retired paper is now a reported finding rather than something nobody
could have noticed.

So the corollary: **split when two kinds of claim must be able to disagree.**
If they always agree, you have one scheme and a tag.

The split pays for itself through the cross-reference. Make it mandatory:

```toml
[luria.schemes.SOTA]
dir      = "record/practices.d"
requires = ["source"]     # a practice with no paper behind it is an opinion
```

## Statuses in two schemes

The five words are fixed — `Active`, `Proposed`, `Deferred`, `Superseded`,
`Rejected` ([ADR-003](../record/decisions.d/ADR-003.md)). What they *mean* is per scheme, declared in a
`statuses.yaml` beside the sources and rendered as a legend above the index.

In the anthology, `Rejected` means two different things in two schemes, and
saying so is the point. On a paper it means the attic: retired from the
reading list, with the reason kept. On a practice it means no longer believed.
One word, two claims; the index legend says which is meant.

**If you cannot say what each status means for this scheme, you may not need
a status here.** Luria will eventually tell you. A scheme where every document
shares one status is reported as `inert-status`, on the grounds that a field
every record agrees on tells you nothing and is indistinguishable from no
field at all.

The anthology arrived with 119 recommendations at one status, a schema
advertising three, and two code branches that could provably never execute on
the data. Nothing had failed; nothing could.

## Rules the config can enforce

This is the part most easily missed, and it is where a record stops being a
folder of markdown.

> **A convention nobody can break is a comment.**

Everything you would otherwise write in a CONTRIBUTING file — *every X cites a
Y*, *pick exactly one category*, *these two tags are contradictory* — ask
whether the config can state it instead:

| The rule you would write in prose | The table that enforces it | What fires |
|---|---|---|
| every entry carries a field | `requires = ["published"]` | a violation |
| every entry has a source, and any of several fields is one | `field_groups` with `fields = ["arxiv", "doi", "url"]` | a violation naming all three |
| every entry names its source paper — a real one | `references` with `source = { scheme = "LIT" }` | a violation |
| an entry names several of its own kind | `references` with `follows = { scheme = "SCENE", many = true }` | a violation per element |
| an entry belongs to one or more of a closed set of values, absent meaning one of them | `fields` with `vocabulary = "worlds"`, `many = true`, `default = ["B"]`; values in `worlds.yaml` | a violation per unknown value |
| exactly one primary category | `tag_groups` with `require = "exactly-one"` | a violation |
| at most one of these, they are an axis | `require = "at-most-one"` | a violation |
| saying it failed contradicts saying it holds | `excluded_by` | a violation |
| this scheme only uses three of the five statuses | `statuses.yaml` | a violation |
| a principle should not name one subsystem | `titles_generalize` + `narrow_terms` | `narrow-titles` |
| citing something not in force should be deliberate | (always on) | `retired-citations` |

```toml
[luria.schemes.SOTA.tag_groups.primary_topic]
require = "exactly-one"
tags = ["training-optimization", "systems-optimization", "model-stability",
        "distributed-optimization", "data-pipeline", "attention-techniques",
        "model-architecture"]
```

Those eight lines replaced a specification that had sat in a template for two
years, complete with scope definitions and a stated rule — *each entry is
tagged with exactly one primary topic* — that had never once been applied. The
vocabulary had drifted to 172 distinct strings across 118 entries. Nothing was
wrong with the specification; nothing was checking it.

Constraints are opt-in and independent. A scheme that declares none behaves
exactly as it did before they existed, so adding one later is a local change.

## Shapes

Five shapes, all of them the same engine with different tables.

**Project memory.** The default, and what the scaffold writes.

```toml
[luria.schemes.ADR]   # decisions, browsed as an index
[luria.schemes.DP]    # principles, read as one document
[luria.journals.devlog]
[luria.fragments."record/changelog.d"]
```

**A research anthology.** Domain content, not project meta-documentation. Two
content schemes that cite each other, and an external identifier namespace
made citable.

```toml
[luria.schemes.LIT]    # one note per paper; Rejected means "the attic"
[luria.schemes.SOTA]   # one document per recommendation; requires = ["source"]
[luria.remotes.ARXIV]
uid = "(\\d{4})[.:](\\d{4,5})(v\\d+)?"
url = "https://arxiv.org/abs/{1}.{2}"
```

Now `ARXIV-1412.6980` written anywhere in the record is a resolvable,
checkable citation rather than a string in a field, and the reading list and
the practice list can disagree about the same paper.

**A standards or interface registry** — proposals browsed one at a time, the
interfaces they define read as one page.

```toml
[luria.schemes.RFC]    # render = "index"
[luria.schemes.SPEC]   # render = "document"
```

**An operations record** — incidents are dated and never revised; runbooks are
cited by name and go stale.

```toml
[luria.journals.incidents]   # granularity = "day"
[luria.schemes.RUN]          # requires = ["owner"]
[luria.remotes.JIRA]         # uid, so ticket keys link and are checked
```

**A compliance record** — controls are claims with standing; evidence is dated
observation. The relationship between them is the audit.

```toml
[luria.schemes.CTRL]         # requires = ["evidence"]
[luria.journals.evidence]
```

None of these needed a plugin, and none of them is a special case in the code.
A family is a table; the entries are yours to name.

## Four smells

Four smells, each with a reading:

- **Every entry has the same status.** The field is decoration. Either narrow
  the vocabulary in `statuses.yaml` to the one word you mean, or work out what
  distinction you were trying to draw. `inert-status` reports this.
- **You keep wanting a second status field.** That is the two-schemes signal,
  arriving as a schema request.
- **Nothing ever cites these entries.** They may be a journal rather than a
  scheme. A journal entry is a dated observation; nothing points at it by
  name.
- **A tag is on 80% of entries.** It is not a browsing axis, it is the name of
  the scheme.

And the general one, which applies to the machinery as much as the content: a
guard that keeps catching you is a bug report about the workflow. One catch is
the net working; the same catch twice means the hazard is upstream.

## Next

- [Project memory](project-memory.md) — the mechanics of each family, and how
  references are found and checked.
- [Importing an existing corpus](importing.md) — when the material already
  exists in some other form.
- [Configuration reference](configuration.md) — every key, generated from the
  schema.
- [`examples/`](https://github.com/dmarx/luria/tree/main/examples) — worked
  configurations, each one built and linted by CI.
