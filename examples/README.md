# Worked configurations

Complete projects, each one a different shape of record. They exist
because the alternative was prose: a `luria.toml` block in a guide is a claim
nobody runs, and this repository's own founding observation is that every
surface governed by prose alone had drifted.

`tests/test_examples.py` builds each of these into a temporary directory,
runs the real `luria index` and `luria lint` against it, and asserts what
came out. So every configuration here is one CI proves, not one someone
believed at the time of writing.

| example | what it demonstrates |
|---|---|
| [`rfcs-and-specs/`](rfcs-and-specs/) | two document families beside each other, one browsed as an index and one read as a single document |
| [`collocated/`](collocated/) | no `output` anywhere — views render beside their sources, the shape a project has before it splits `docs/` from `record/` |
| [`many-journals/`](many-journals/) | three journals at three granularities: a devlog, an incident log, a meeting log |
| [`external-citations/`](external-citations/) | `uid` remotes — linted, linked citations to arXiv papers, Jira tickets and CVEs, none of which is a Luria record |
| [`knowledge-base/`](knowledge-base/) | a record of *domain* content rather than project meta-documentation: two schemes that cite each other and carry separate statuses, with required fields and a one-primary-category rule |
| [`world-bible/`](world-bible/) | a story bible: scenes that `follow` several scenes (a plural reference) and belong to world trajectories drawn from a closed vocabulary with a default — a field that is neither a reference, a tag nor a status |

To run one by hand:

```
cd examples/rfcs-and-specs
LURIA_ROOT=$PWD luria index
LURIA_ROOT=$PWD luria lint
```

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
