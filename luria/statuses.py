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


# Below the floor a uniform status is not evidence of anything: three records
# that all happen to be in force is a young scheme, not an unused field.
FLOOR = 10


def uniform(scheme) -> tuple[str, int] | None:
    """`(status, count)` when every record in the scheme shares one status.

    A status field where every record agrees is indistinguishable from no
    status field, and the difference matters because other machinery reads it:
    `active` decides what counts as retired, and `retired-citations` fires off
    that. A scheme in this state has an enforcement mechanism that cannot fire,
    and the build is green *because* nothing is being judged (#104).

    `None` below the floor, for a scheme rendered as one document (a
    design-principles page where everything is in force is the expected state,
    not a smell), when the scheme declares a vocabulary of exactly one status,
    which is a project saying so on purpose, and when the scheme sets
    `uniform_ok` — the acknowledgement this finding lacked. See
    `acknowledged_rows` for where that reason surfaces instead.
    """
    from . import adr_index
    if scheme.render == "document" or scheme.uniform_ok:
        return None
    vocab = declared(scheme)
    if len(vocab) == 1:
        return None
    found: list[str] = []
    for path in [*scheme.documents().values(), *scheme.temp_documents().values()]:
        meta, _ = adr_index.parse_frontmatter(path.read_text())
        status = str((meta or {}).get("status", "")).strip()
        if status:
            found.append(status.split(" — ")[0].strip())
    if len(found) < FLOOR or len(set(found)) != 1:
        return None
    return found[0], len(found)


def uniform_rows() -> list[str]:
    """One line per scheme whose status field carries no information."""
    from .config import current
    rows = []
    for prefix, scheme in current().schemes.items():
        if hit := uniform(scheme):
            status, count = hit
            rows.append(f"{prefix}: {count}/{count} at `{status}`")
    return rows


def acknowledged_rows() -> list[str]:
    """One line per scheme whose uniformity a human has vouched for.

    The counterpart to `uniform_rows`. An acknowledged scheme is still
    uniform — nothing there is being judged, and the citation checks still
    cannot fire — so the fact does not stop being true when someone explains
    it. It stops being a *finding* and becomes a note, which is the same
    bargain `inactive-ok:` strikes at a citation site: the reason is
    mandatory, and it renders where the finding would have.
    """
    from .config import current
    from . import adr_index
    rows = []
    for prefix, scheme in current().schemes.items():
        if not scheme.uniform_ok:
            continue
        found = []
        for path in [*scheme.documents().values(),
                     *scheme.temp_documents().values()]:
            meta, _ = adr_index.parse_frontmatter(path.read_text())
            status = str((meta or {}).get("status", "")).strip()
            if status:
                found.append(status.split(" — ")[0].strip())
        if len(found) >= FLOOR and len(set(found)) == 1:
            rows.append(f"{prefix}: {len(found)}/{len(found)} at "
                        f"`{found[0]}` — {scheme.uniform_ok}")
    return rows
