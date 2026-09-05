# A constitution as a record

A record with no code in it at all: an assistant's operating instructions
decomposed into a typed ontology, beside the document it decomposes.

| scheme | render | what it holds |
|---|---|---|
| `VALUE` | document | claims that would still mean something to an assistant with none of this one's tools. Read whole, in order. |
| `PRACTICE` | index | situated rules, one per document, each grounded in a value and tagged with the surface it applies to |
| `BOUNDARY` | index | constraints that override, each naming what it overrides |

**Precedence is a checked reference, not a font size.** A constitution written
as prose signals precedence by escalation — *IMPORTANT*, *ALWAYS*, *you MUST* —
which is unfalsifiable: nothing verifies that the emphatic rule wins, and
nothing notices when the rule it was meant to beat is deleted. Declaring
`overrides` as a typed reference makes it an edge the lint resolves and the
site draws. `grounds` does the same job downward, so no rule stands on its own
authority: a practice with no value behind it is a habit.

**The source is here too**, and the record is checked against it. A test
asserts that every document in force accounts for some part of it — the schema
checks `PRACTICE → VALUE`, but nothing else would check `document → the text it
was drawn from`, which is the direction a record like this drifts in.

The configuration is `luria.toml`, commented throughout; the documents are
under `record/`. Start with [the source
constitution](docs/constitution.md), annotated section by section with what
accounts for it, then [the values](docs/values.md),
[the practices](docs/practices/README.md),
[the boundaries](docs/boundaries/README.md), and
[the session log](docs/sessions/README.md).

```
LURIA_ROOT=$PWD luria index
LURIA_ROOT=$PWD luria lint
```
