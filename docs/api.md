# Python API

The supported surface is the CLI. The modules are importable, and this page
describes what is worth importing — for building a report, adding a check, or
querying a record from a script.

Two honest caveats before you start. The internals are not versioned
independently of the CLI, so pin the version if you depend on them. And if what
you want is a *check*, prefer extending the lint over reimplementing it —
`status_sections()` already computes every finding, and a second implementation
of the same rule is one that will disagree with the first.

## Loading a record

Everything starts from a `Config`. It is process-global and cached.

```python
from pathlib import Path
from luria import config

config.load(Path("/path/to/repo"))   # or load() to detect from cwd
cfg = config.current()

print(cfg.root, cfg.docs, cfg.reports)
print(list(cfg.schemes))             # ['ADR', 'DP', ...]
```

`config.reset()` clears the cache — needed in tests, or when walking several
repositories in one process. `config.find_root()` locates the repo root by
looking for `luria.toml`.

`load()` also takes `text=` to parse a config that is not on disk, which is how
the test suite builds fixtures.

## Schemes

A `Scheme` is the whole definition of a record family.

```python
adr = cfg.schemes["ADR"]

adr.prefix          # 'ADR'
adr.dir             # Path to record/decisions.d
adr.active          # 'Active' — the in-force status
adr.render          # 'index' | 'document'
adr.requires        # ('source', 'locus') — required frontmatter fields
adr.tag_groups      # declared tag constraints

adr.view            # where the index renders
adr.index_path      # …/README.md
adr.tag_dir         # …/tags/
adr.stub            # the hand-written prose the index is built around
adr.tags_yaml       # the tag vocabulary
adr.statuses_yaml   # the status vocabulary

adr.documents()      # {12: Path('record/decisions.d/ADR-012.md'), ...}
adr.temp_documents() # {'tmpk3n1p': Path(...)} — merge-allocated, not yet numbered
adr.code(12)         # 'ADR-012'
adr.number_of(path)  # 12, or None
```

`documents()` is keyed by number and sorted, which is usually what you want to
iterate.

## Reading records

`parse_frontmatter` splits a record into its metadata and its body. It is the
one place that knows the file shape, so use it rather than a YAML split of your
own.

```python
from luria import adr_index

meta, body = adr_index.parse_frontmatter(path.read_text())
meta["status"], meta["title"], meta.get("tags", [])
```

For a whole scheme, `load_scheme` gives `Adr` objects — numbered records with
their frontmatter parsed and their tags normalised:

```python
records = adr_index.load_scheme(cfg.schemes["ADR"])
for r in records:
    print(r.number, r.meta["status"], r.meta["title"], r.tags)
```

### Example: what is in force?

```python
from luria import adr_index, config

config.load()
cfg = config.current()

for prefix, scheme in cfg.schemes.items():
    records = adr_index.load_scheme(scheme)
    live = [r for r in records
            if str(r.meta.get("status", "")).split(" — ")[0] == scheme.active]
    print(f"{prefix}: {len(live)}/{len(records)} in force")
```

Note the `split(" — ")`. A status may carry a trailing note (`Superseded — by
ADR-030`), and the note qualifies the word rather than being part of it.
Comparing whole strings is the most common bug in code that touches this field
— it has been made twice inside luria itself.

## Statuses and tags

```python
from luria import statuses

statuses.declared(scheme)          # {'Active': {'label':…, 'blurb':…}, ...}, or {}
statuses.undeclared(scheme, "Deferred")  # True if the scheme declares a vocabulary without it
statuses.uniform(scheme)           # ('Active', 51) when every record shares one status
statuses.CLOSED                    # the five words; narrowed per scheme, never extended
```

An empty `declared()` means the scheme declares nothing, which leaves all five
available. Do not treat absent as empty — that inverts the default and rejects
every record in a project that has not adopted `statuses.yaml`.

## Findings

The whole warning surface, computed once:

```python
from luria import lint

for cls, headline, rows in lint.status_sections():
    print(cls, "—", headline)
    for row in rows:
        print("   ", row)
```

Each `cls` is a name from `lint.FAILABLE` — `retired-citations`,
`unresolved-codes`, `broken-targets`, `inert-status`, and the rest. This is what
both the report path and the `fail_on` path read, so they cannot disagree.

The violation checks each take an `errors` list and append to it:

```python
errors: list[str] = []
lint.check_frontmatter(errors)
lint.check_generated_index(errors)
```

## References and links

```python
from luria import doc_refs

doc_refs.doc_files()                 # every file the reference rules apply to
doc_refs.wikilinks(text, path)       # [[CODE]] occurrences, resolved where possible
doc_refs.rewritable_refs(text, path, adrs, anchors)   # what --fix would rewrite
```

`cfg.link_base(path)` is the one worth knowing: **the directory a link written
in `path` resolves against**, which is not always `path.parent`. A journal entry
renders into the journal's output directory; a fragment is assembled into its
target; a stub's prose lands in the index it introduces. If you are computing a
relative target, compute it against `link_base` or you will produce something
that looks right beside the source and points at nothing in the view.

## Directives

The acknowledgement comments, parsed:

```python
from luria import directives

found = directives.find(path, text, {"inactive-ok"})
for d in found:
    d.name, d.scope, d.args, d.reason, d.line
    d.covers(88)          # does it govern line 88?

directives.problems(d)    # 'names no argument', or None
```

Only real comments count — HTML comments in markdown, `COMMENT` tokens in
Python, text after a comment marker elsewhere. An example inside a fence is not
a comment and does not fire, which is deliberate and was learned four separate
times.

## Adding your own check

The pattern the built-in checks follow, and the one to copy:

```python
from luria import adr_index, config

def check_decisions_cite_an_issue() -> list[str]:
    """Every Active decision names the issue it came from."""
    cfg = config.current()
    scheme = cfg.schemes["ADR"]
    bad = []
    for record in adr_index.load_scheme(scheme):
        status = str(record.meta.get("status", "")).split(" — ")[0]
        if status == scheme.active and not record.meta.get("issue"):
            bad.append(f"{cfg.rel(record.path)}: no `issue:`")
    return bad
```

Run it in your own test suite against the committed record, not against a
fixture — a guard over a synthetic tree passes while the real record drifts.

Before writing one, check whether `requires` does it already: a scheme can
demand frontmatter fields in `luria.toml`, and a rule the tool owns is a rule
that does not have to be maintained.

## Stability

| Surface | Stability |
|---|---|
| the CLI | stable; commands and flags change with a decision behind them |
| `config.load` / `current` / `Scheme` | stable in practice, widely used |
| `adr_index.parse_frontmatter`, `load_scheme` | stable in practice |
| `lint.status_sections`, `lint.FAILABLE` | stable; the class names are a public vocabulary |
| everything else | internal — pin the version |
