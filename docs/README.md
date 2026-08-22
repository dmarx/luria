# Luria documentation

Luria is a **truth maintenance system for a repository's prose**. Records hold
what you decided; citations link them; and retracting one propagates to
everything that rested on it, as findings you can act on.

If you are here to use it, go in this order.

## Start

| | |
|---|---|
| [Quickstart](quickstart.md) | fifteen minutes, ending in a real finding |
| [Concepts](concepts.md) | the model — records, status, citations, propagation — and the prior art |
| [Adopting](adopting.md) | bringing luria to a repository that already has history |
| [In practice](in-practice.md) | three real records compared — what varied, and what drove it |

## Reference

| | |
|---|---|
| [CLI](cli.md) | every command, what it is for, and the CI wiring |
| [Configuration](configuration.md) | every `luria.toml` key, generated from the schema |
| [The record](record.md) | what *this* project configured — the families it named, where entries are filed, what to type to add one |
| [Directives](directives.md) | the acknowledgement vocabulary, and how to choose |
| [Schemes](schemes.md) | designing record families beyond decisions |
| [Python API](api.md) | using luria as a library, and adding your own checks |

## Doctrine

| | |
|---|---|
| [Project memory](project-memory.md) | the four layers, and what belongs in each |
| [Design principles](design-principles.md) | the standing values, cited by number |

## This project's own record

Luria is maintained with luria, so these are both documentation and worked
examples.

| | |
|---|---|
| [Decisions](decisions/README.md) | every choice, its alternatives, its status |
| [Devlog](devlog/README.md) | what went wrong, and the theories that failed |
| [Pending decisions](reports/pending-decisions.md) | what is undecided, and since when |
| [Reference status](reports/reference-status.md) | what cites something not in force |

The reports are sometimes non-empty on purpose. A project whose own findings
always read clean is one whose findings are not wired to anything.
