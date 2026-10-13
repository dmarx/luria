# Argument map

An argument kept as a record, and the shape that needed path patterns.

**Three kinds of document.** A *claim* states something. An *inference*
draws one claim from others: its `premises` name the claims it starts from,
and `concludes` names the claim it reaches. An *objection* `challenges` a
claim or an inference.

**No field says which claim follows from which.** That fact takes two
fields on two documents: `premise_of` on the premise and `concludes` on the
inference. A chain over either field alone stops at the inference. So the
line is declared as a named path pattern, and the chain walks that:

```yaml
patterns:
  follows_from: (b:CLAIM)<-[:concludes]-(i:INF)<-[:premise_of]-(a:CLAIM)
```

It reads like the field it stands in for: the first node is the step and
the last is the claim it builds on, so a conclusion nests under its
premises. `i` is named, so each step on the page says which inference it
went through.

**Two views of one argument.** [Lines of argument](docs/argument.md) walks
every step. [Uncontested lines](docs/uncontested.md) walks `stands_on`, the
same pattern with `WHERE NOT (i)<-[:challenges]-(:OBJ)`. It drops the step
from the 2025 inspection to "the repair can wait", because [OBJ-001](record/objections.d/OBJ-001.md)
challenges it.

**An unfinished step draws nothing.** [INF-004](record/inferences.d/INF-004.md) has a premise and no
conclusion yet, so it is not a step on either page. What counts as
unfinished depends on what this record requires, so luria does not guess.
The record can say it as a pattern of its own:

```yaml
unfinished: (i:INF)<-[:premise_of]-(:CLAIM) WHERE NOT (i)-[:concludes]->(:CLAIM)
```

Rendering such a pattern as a list of its matches is luria's
[issue 373](https://github.com/dmarx/luria/issues/373).

```
LURIA_ROOT=$PWD luria index
LURIA_ROOT=$PWD luria lint
```
