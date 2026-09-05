# Collocated views

No `output` anywhere. Every view renders **beside its sources**, which is what
adoption looks like when you would rather not move files first: point luria at
the directory the decisions already live in and let the index appear next to
them.

The mechanism is worth knowing because it is not a default value. A declared
family replaces the shipped one, so `output` here is a genuinely *unset* key —
there is no default entry left to inherit from — and an unset `output` means
"render in place". That was a limit once: `output` could not be unset by
omission, and the test pinning the limit fired the day the rule changed.

The configuration is `luria.toml`, commented throughout. Sources and their
index share a directory — `decisions/`, where [the generated
index](decisions/README.md) sits beside the decisions it lists. There is also
[a front door](docs/README.md).

```
LURIA_ROOT=$PWD luria index
LURIA_ROOT=$PWD luria lint
```
