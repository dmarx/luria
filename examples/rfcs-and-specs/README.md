# RFCs and specs

Two document families beside each other, browsed differently. `RFC` renders as
an **index** plus per-tag pages — proposals are read one at a time — and `SPEC`
renders as a single **document**, because an interface is read whole.

The two schemes are the whole configuration. Declaring them replaces the
shipped `ADR` table rather than adding to it, so this record has exactly the
families it named and no phantom decision index.

Naming a table also creates its references: `RFC-7` and `SPEC-3` become
first-class the moment the table exists, so `luria link --fix` writes their
links, `luria lint` demands them, and `luria new --kind rfc` scaffolds the next
free number.

The configuration is `luria.toml`, commented throughout; the sources are under
`record/`. The generated views: [the record's front door](docs/README.md),
[the RFC index](docs/rfcs/README.md), [the interfaces document](docs/interfaces.md).

```
LURIA_ROOT=$PWD luria index
LURIA_ROOT=$PWD luria lint
```
