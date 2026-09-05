# Worked configurations

Complete projects, each one a different shape of record. They exist
because the alternative was prose: a `luria.toml` block in a guide is a claim
nobody runs, and this repository's own founding observation is that every
surface governed by prose alone had drifted.

`tests/test_examples.py` builds each of these into a temporary directory,
runs the real `luria index` and `luria lint` against it, and asserts what
came out. So every configuration here is one CI proves, not one someone
believed at the time of writing.

Their generated views are **committed**, and `luria index` at the repository
root regenerates them along with everything else ([[ADR-078]]) — so each
example can be read here as a finished record, and `luria index --check` fails
if one goes stale. They were gitignored until that was true, on an argument
that turned out to conflate *committed* with *hand-maintained*.

| example | what it demonstrates |
|---|---|
| [`rfcs-and-specs/`](rfcs-and-specs/) | two document families beside each other, one browsed as an index and one read as a single document |
| [`collocated/`](collocated/) | no `output` anywhere — views render beside their sources, the shape a project has before it splits `docs/` from `record/` |
| [`many-journals/`](many-journals/) | three journals at three granularities: a devlog, an incident log, a meeting log |
| [`external-citations/`](external-citations/) | `uid` remotes — linted, linked citations to arXiv papers, Jira tickets and CVEs, none of which is a Luria record |
| [`knowledge-base/`](knowledge-base/) | a record of *domain* content rather than project meta-documentation: two schemes that cite each other and carry separate statuses, with required fields and a one-primary-category rule |
| [`world-bible/`](world-bible/) | a story bible: scenes that `follow` several scenes (a plural reference) and belong to world trajectories drawn from a closed vocabulary with a default — a field that is neither a reference, a tag nor a status |
| [`constitution/`](constitution/) | a record with no code in it at all: an AI assistant's operating instructions decomposed into values, practices and boundaries, where **precedence is a checked reference** (`BOUNDARY.overrides → PRACTICE`) rather than escalating emphasis, and a practice is retired by a boundary from another scheme |

To run one by hand:

```
cd examples/rfcs-and-specs
LURIA_ROOT=$PWD luria index
LURIA_ROOT=$PWD luria lint
```

## Each example is published, as a section of this site

Every example is a whole record — its own `luria.toml`, its own schemes, its
own README — and every one is **published**, at `examples/<name>/` on this
project's site. That is `site.include_records` ([ADR-077](../record/decisions.d/ADR-077.md)):

```toml
[luria.site]
include_records = ["examples/*"]
```

Each match is staged by **its own config** into a temporary vault, and only the
finished `content/` is mounted. That indirection is the whole design, and the
reason a plain merge does not work: `publishable()` tells a source from a view
with `link_base(path) != path.parent`, and `link_base` answers from the
*reading* config's schemes. Under the root config an example's `VALUE-001.md`
has no scheme to belong to, so it reads as ordinary prose —

```
examples/constitution/record/values.d/VALUE-001.md
    link_base=…/record/values.d  own_dir=…/record/values.d  PUBLISHED IN PLACE
```

— and the parent would publish the fragment *and* `docs/values.md`, the
document it renders into, with half the views coming from whatever a
contributor's working tree happened to hold, since none of them is committed.

Each example still stands alone, which is what makes the mount possible:

```
cd examples/constitution
LURIA_ROOT=$PWD luria index
LURIA_ROOT=$PWD luria site --out build/site
```

`tests/test_examples.py::test_every_example_stages_its_own_site` stages each
one and asserts the two counts that make a page readable: nothing unplaceable,
and nothing redirected out to the repository. The second is the sharp one.
`luria lint` checks that a relative target exists **on disk**; it has no
opinion about whether the file it names is ever *published*. `constitution/`
cited its values as `../values.d/VALUE-004.md` — present, lint-clean, and never
a page, because a `render = "document"` scheme renders its sources into one
assembled view. Staging was the only check that read those as links a reader
would try to follow. The spelling the fixer produces,
`../../docs/values.md#value-4`, is the anchor in the view. The same assertion
later caught these READMEs linking `luria.toml` and bare directories: real
files, no page, and in a standalone record the repository they redirect to is
the wrong one.

**A document scheme's stub must contain `{principles}`.** That is the
placeholder `render = "document"` substitutes every member's body into, and a
stub without it renders the prose and silently drops the documents —
`luria index` still reports "4 VALUEs" and `luria lint` still passes, because
the page it produced is a valid page. `constitution/docs/values.md` was eight
lines of preamble and no values until the site test made the page count worth
looking at.

`constitution/` also turned up a third, in `luria` itself rather than in the
example: a `Superseded` practice is still a member of its surface vocabulary,
and vocabulary pages were generated by one definition (`view_dirs`) and
hand-written by another (`Config.is_generated`), which the reference machinery
reads. The report scanned a page it should never have opened, found it only
after the run that wrote it, and `luria index` stopped converging. Fixed; the
example is what made it visible, about 26 hours after vocabularies shipped
(2026-09-03T23:29Z → 2026-09-05T01:19Z).

## The merge rule these examples demonstrate

A family table you declare — `schemes`, `fragments`, `journals`, `remotes` —
**replaces** the shipped default; one you never mention keeps it
([LU-ADR-047](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-047.md)).
`rfcs-and-specs/` declares two schemes and has exactly two: no phantom
decision index for an ADR scheme nobody asked for. `many-journals/` declares
only journals, so its scheme family is untouched and the default ADR scheme
survives. And `collocated/` omits `output` and gets a genuinely unset key —
the view renders beside its sources, because a declared family has no default
entry left to inherit from.

Two of these were *limits* when this directory was first written — the ADR
scheme could not be removed, and its `output` could not be unset by omission
— and the tests that pinned them fired the day the rule changed, which is
what pins are for.

## One limit these examples make visible

**`active` selects from a closed vocabulary — it does not define one.** The
five statuses (`Active`, `Proposed`, `Deferred`, `Superseded`, `Rejected`)
are fixed and enforced by the lint, deliberately
([LU-ADR-003](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-003.md)):
an audit across 121 files found thirty distinct spellings of "this one
counts". So `active = "Accepted"` does not make `Accepted` a legal status —
it names a state no document can hold, and every document in the scheme
fails the lint. What `active` *is* for is a scheme whose in-force state is
one of the five but not `Active`.
