# Worked configurations

Four complete projects, each one a different shape of record. They exist
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

To run one by hand:

```
cd examples/rfcs-and-specs
LURIA_ROOT=$PWD luria index
LURIA_ROOT=$PWD luria lint
```

## Three limits these examples make visible

Worth knowing before you design a record around them, and both are the kind
of thing that only shows up when someone actually runs the configuration.

**The shipped `ADR` scheme cannot be removed.** Configuration merges over
Luria's defaults, and those defaults include `[luria.schemes.ADR]`. A project
that wants RFCs and no decisions still gets an ADR scheme pointing at
`record/decisions.d`, and still renders an empty decision index. Leaving it
empty is harmless and is what these examples do; deleting it is not currently
possible.

**Omitting `output` does not collocate the `ADR` scheme** — set it equal to
`dir` instead. This is the same merge, and it is the one that bites hardest,
because it hits the documented adoption path. `output` is *unset* for a scheme
you invent, so omitting it renders the view beside the sources as described.
But the shipped ADR entry carries `output = "docs/decisions"`, so a project
that points `dir` at its existing decisions and omits `output` — expecting to
keep its layout — silently gets its index relocated to `docs/decisions/`.
`examples/collocated/` writes `output = "decisions"` for exactly this reason.

**`active` selects from a closed vocabulary — it does not define one.** The
five statuses (`Active`, `Proposed`, `Deferred`, `Superseded`, `Rejected`)
are fixed and enforced by the lint, deliberately
([LU-ADR-003](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-003.md)):
an audit across 121 files found thirty distinct spellings of "this one
counts". So `active = "Accepted"` does not make `Accepted` a legal status —
it names a state no document can hold, and every document in the scheme
fails the lint. What `active` *is* for is a scheme whose in-force state is
one of the five but not `Active`.
