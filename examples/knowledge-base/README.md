# Knowledge base

A record of **domain content** rather than project meta-documentation: a
scheme of papers (`LIT`) and a scheme of the practices drawn from them
(`SOTA`).

Two things make it work that a single scheme could not do.

**The two carry separate statuses, and are allowed to disagree.** A paper and
the practice drawn from it are different claims — `Rejected` in the reading
list means the attic; `Deferred` in the practices means not adopted yet — and
one scheme means one status vocabulary, after which they cannot differ.

**A practice must cite a paper, as a typed reference.** Not `requires`, which
any truthy value satisfies: a typed reference says the field must name a `LIT`,
so a practice citing a decision, or a sentence, fails. The paper's own source
is a field *group* — `arxiv`, `doi` or `url`, any one of which will do —
because a report never posted to arXiv is a paper all the same.

The configuration is `luria.toml`, commented throughout; the sources are under
`record/`, each family with its own `statuses.yaml`. The generated views:
[literature](docs/literature/README.md), [practices](docs/practices/README.md),
and [the front door](docs/README.md).

```
LURIA_ROOT=$PWD luria index
LURIA_ROOT=$PWD luria lint
```
