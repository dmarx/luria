"""What a status *means* in one scheme, declared beside the records.

[ADR-003](../record/decisions.d/ADR-003.md) closed the status vocabulary to
five words and put a lint behind it, on the strength of an audit finding that
every surface guarded by an executable check had held and every surface
governed by prose convention alone had drifted.

The five words held. What that decision did not cover is the layer above them:
**a status means something different in every scheme**, and that meaning has
only ever lived in prose — a template comment and, if a project is diligent, a
decision record. Which is precisely the surface ADR-003 measured as the one
that drifts.

It drifted. A downstream project adopting luria wrote three decisions to say
what its statuses mean, and twice found the record doing something else: a
scheme where fifty-one of fifty-one records sat at the in-force status because
extraction defaulted there and nothing said otherwise, and a sibling scheme
whose template said status carried a judgment that a tag was actually carrying.
Both were caught by a person re-reading, which is what ADR-003 says not to rely
on.

So this is that decision applied one level up, and deliberately not further:

- **The five words stay closed.** Nothing here adds a status. A `statuses.yaml`
  key outside the closed set is an error, not a new word.
- **A scheme may declare which of the five it uses**, and a record whose status
  is not declared fails the lint. That narrows the vocabulary per scheme without
  reopening it.
- **A scheme may say what each one means**, and the meaning renders into the
  generated index — next to the column it explains, where a reader is, rather
  than in a template only the author of a new record ever opens.

Shaped after `tags.yaml`, which does the same job for the other browsing axis:
the vocabulary lives in YAML beside the records, and any *rule* about combining
them lives in `luria.toml`. Declaring nothing keeps today's behaviour exactly —
all five words, no legend.
"""

from __future__ import annotations

import yaml

# ADR-003's vocabulary. This module narrows it and never extends it.
CLOSED = ("Active", "Proposed", "Deferred", "Superseded", "Rejected")


def declared(scheme) -> dict[str, dict]:
    """`{status: {label, blurb}}` as the scheme declares it, or `{}`.

    An empty mapping means "declares nothing", which is the default and leaves
    every check below inert — an unconfigured project must not be told it has a
    problem, and must not be told it is clean either.
    """
    path = scheme.statuses_yaml
    if not path.exists():
        return {}
    loaded = yaml.safe_load(path.read_text()) or {}
    return {k: (v or {}) for k, v in loaded.items()}


def problems(scheme) -> list[str]:
    """Keys a scheme declares that are not statuses.

    The one place this module can catch a project trying to invent a word. It
    is worth catching loudly: a `statuses.yaml` naming `Accepted` would render a
    legend and silence nothing, so the file would look like it was working.
    """
    from .config import current
    bad = [k for k in declared(scheme) if k not in CLOSED]
    if not bad:
        return []
    rel = current().rel(scheme.statuses_yaml)
    return [f"{rel}: {k!r} is not a status (want one of: "
            f"{', '.join(CLOSED)}) — the vocabulary is closed (ADR-003)"
            for k in bad]


def undeclared(scheme, status: str) -> bool:
    """True when the scheme declares a vocabulary and this status is not in it.

    `status` is the bare word: ADR-003 allows a trailing ` — note`, and the
    note is a qualifier on the word rather than part of it.
    """
    vocab = declared(scheme)
    return bool(vocab) and status.split(" — ")[0].strip() not in vocab


def legend(scheme) -> str:
    """The declared statuses as a markdown table, or `''` when none are.

    Rendered above the index table rather than behind a stub placeholder, so
    that adopting the file is enough to make the meaning visible. A legend
    nobody added a placeholder for is a legend nobody reads, which is the
    failure this exists to fix.
    """
    vocab = declared(scheme)
    if not vocab:
        return ""
    rows = []
    for status, meta in vocab.items():
        label = meta.get("label", "")
        blurb = meta.get("blurb", "")
        # Sentence-case the first letter only; `str.capitalize()` lowercases
        # everything after it and mangles anything capitalised in the blurb.
        text = f"{blurb[:1].upper()}{blurb[1:]}" if blurb else ""
        rows.append(f"| `{status}` | {label} | {text} |")
    return ("What the status column means in this scheme — the words are "
            "luria's, the meanings are this project's.\n\n"
            "| Status | | Means |\n|---|---|---|\n" + "\n".join(rows) + "\n")
