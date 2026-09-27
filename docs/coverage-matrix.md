# Documentation coverage matrix

This matrix is the documentation audit surface.

Legend:

- **P** — primary treatment
- **S** — secondary/brief treatment
- **—** — intentionally not covered there

| Feature / concept | README | Tutorial | Concepts | How-to | Reference |
|---|:---:|:---:|:---:|:---:|:---:|
| `luria.yaml` | S | P | S | — | P |
| `luria init` | S | P | — | — | P |
| `luria new` | S | P | — | — | P |
| schemes | S | P | P | S | P |
| journals | S | — | P | P | P |
| fragments | S | — | P | P | P |
| remotes | S | — | P | P | P |
| vocabularies | S | P | P | S | P |
| standing | P | P | P | S | P |
| references | P | P | P | P | P |
| converses | — | S | P | P | P |
| relation invariants | — | S | P | P | P |
| `luria relate` | — | S | — | P | P |
| chains | P | P | P | P | P |
| multiple spine relations | — | P | P | P | P |
| sibling relation | — | P | P | P | P |
| chain facets | S | P | P | P | P |
| chain invariant | S | P | P | P | P |
| `luria lint` | P | P | P | P | P |
| `luria repair` | S | S | P | P | P |
| `luria ack` | S | S | P | P | P |
| enforcement / `fail_on` | S | P | P | P | P |
| baselines | — | S | P | P | P |
| directives | — | S | P | P | P |
| generated views | P | P | P | P | P |
| `luria index` | P | P | P | P | P |
| reports | — | — | P | P | P |
| filing allocation | — | — | P | P | P |
| merge allocation | — | — | P | P | P |
| `concretize` | — | — | P | P | P |
| site publishing | S | P (chains) | P | P | P |
| SQLite export | — | — | P | P | P |
| journals | S | — | P | P | P |
| `collect` | — | — | P | P | P |
| external pinning | — | — | P | P | P |
| documentation dependencies | P | P | P | — | — |
| record theory/meta-record | S | P | P | — | — |
| adoption of existing corpus | — | P | S | — | — |

## Intentionally excluded from the stable public documentation plan

Developer convenience for carrying Luria itself across internal structural transitions (for example migration/upgrade machinery) is not treated as a core product concept here.

If one of those commands becomes an intended stable user workflow later, add it to the matrix deliberately rather than documenting it merely because the CLI exposes it.

## Audit rule

Every public product feature should have:

1. one conceptual home or explicit statement that it is purely operational,
2. one exact reference home,
3. a how-to page if users need to perform a nontrivial task with it,
4. tutorial coverage only when it teaches a distinct capability.

Anything with no home is a documentation gap.

Anything appearing as primary treatment everywhere is probably duplicated too much.
