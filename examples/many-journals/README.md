# Many journals

Three journals at three granularities in one record: a **devlog** collected by
month, an **incident log** by day, a **meeting log** by day. Journals are a
table like any other, so a project has as many as it names.

Only journals are declared here, so the scheme family is untouched and the
default `ADR` table survives — the merge rule from the other direction.

The test that decides journal-versus-fragment: **do the sources survive?** A
journal's entries are dated observations that stay true after the thing they
describe changes, so they persist and the book is regenerated from them. A
changelog fragment is consumed into a release and is gone. Same directory
shape, opposite lifecycle.

The configuration is `luria.toml`, commented throughout; the entries are under
`record/`, one per journal. The generated books: [devlog](docs/devlog/README.md),
[incidents](docs/incidents/README.md), [meetings](docs/meetings/README.md), and
[the front door](docs/README.md).

```
LURIA_ROOT=$PWD luria index
LURIA_ROOT=$PWD luria lint
```
