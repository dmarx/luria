# External citations

Linked, linted citations to things that are not Luria records at all: arXiv
papers, Jira tickets, CVEs.

A remote normally points at another project's record and composes that
project's own codes. Give it a **`uid` pattern** instead and the tail is an
opaque identifier — matched exactly, never normalised, and turned into a URL
through the template. So `arXiv-2103.00020` and `CVE-2021-44228` are references
the linter checks and the fixer writes, without either source being a record.

The prefix is the table's name, which means the namespace is always visible at
the citation site: a reader can tell what kind of thing is being cited without
following the link.

The configuration is `luria.toml`, commented throughout; the sources are under
`record/notes.d/`. The generated views: [the note index](docs/notes/README.md)
and [the front door](docs/README.md).

```
LURIA_ROOT=$PWD luria index
LURIA_ROOT=$PWD luria lint
```
