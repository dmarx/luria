# luria/vocabularies.py
"""A frontmatter field backed by a controlled vocabulary — and the one
renderer for every field a view groups by.

    vocabularies:
      worlds:
        A: {label: The unbroken line, blurb: where the treaty holds}
        B: {label: The main line}

    schemes:
      SCENE:
        axis: tags                   # the field that heads the index
        fields:
          worlds: {vocabulary: worlds, many: true, default: [B]}
          tags:   {vocabulary: topics, many: true, closed: false}

A scheme directory used to hold two of these as hand-built special cases —
`statuses.yaml` behind `status:` (closed, one value) and `tags.yaml` behind
`tags:` (open, many). A downstream record's `worlds: [A, C]` on 37 of 75
entries, from a closed six-value set, was the third and showed the pattern
(ADR-076). `status` came in under it at #181; `tags` came in last
(ADR-098), once a vocabulary could be OPEN and a group could name the
field it constrains.

The vocabulary is the values; the `fields` table is the wiring, and the
wiring is explicit. Closed is the default: a value the vocabulary does not
declare is a finding. Open is what `tags` needed — the declaration supplies
order, label and blurb for the values a project has an opinion about, and
reaching for a new one stays an edit to a document. A default is an
*effective* value — every consumer reads an absent field as it — and never
a rewrite of the source.

**This module renders every grouped field, the axis included.** There were
two renderers, and the axis's was the older: a categories block listing the
documents, and a tag page whose heading said "tagged" and whose blurb was
sentence-cased by hand. They had drifted in three places — the label
fallback, the blurb, and whether a value the vocabulary does not declare
appears at all. What is left of the difference is one shape choice the
scheme itself makes: the axis lists its documents because it is the
browsing surface; every other field is a row of chips, because the value's
own page already holds the table.

The contract compiles the field (`contract.for_scheme`) and the lint checks
it; the config validates the declaration at load, eagerly, like a group.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def declared(values: dict | None) -> dict[str, dict]:
    """`{value: {label, blurb}}` in declaration order, or `{}` when a scheme
    names no vocabulary.

    Takes the values rather than a path since ADR-098: a vocabulary is
    declared once under `vocabularies:` and referenced by name, so there is no
    longer a file per scheme to read — which is what let two schemes sharing
    one vocabulary drift apart in ten of thirteen entries."""
    if not isinstance(values, dict):
        return {}
    return {str(k): (v or {}) for k, v in values.items()}


def label_of(meta: dict | None, value: str) -> str:
    """What a view calls this value: its `label`, else the value itself.

    One fallback, because there were three — `tag.title()` in the tag pages,
    `""` in the status legend, and the raw value here — so a scheme declaring
    no `label` rendered an empty legend column but a title-cased tag heading
    (ADR-098)."""
    return str((meta or {}).get("label") or value)


def _label(meta: dict, value: str) -> str:
    return label_of(meta, value)


def _fields(scheme):
    """Every field whose values a view groups by: the scheme's declared
    vocabularies, and its axis even when the axis declares no vocabulary.

    `Scheme.grouped_fields` is the one answer — the same one the generator
    uses to decide which directories it owns (ADR-098)."""
    from .contract import for_scheme
    compiled = {f.name: f for f in for_scheme(scheme).fields}
    named = {v.field: v for v in scheme.vocabularies}
    return [(f, named.get(f), compiled[f])
            for f in scheme.grouped_fields if f in compiled]


def _listing(scheme, docs) -> list[tuple[str, object, object, dict[str, list]]]:
    """Per grouped field: (name, declaration or None, compiled field,
    {value: [docs]}) — the documents under each value by their *effective*
    values, so an entry with the field absent sits under the default.

    The values come in one order for every field: declared ones as the
    vocabulary declares them, then — for an OPEN field only — any value a
    document actually uses, alphabetically. Using a new value must never
    require a config change, which is the whole of what `tags` being open
    always meant; a closed field's unknown value is a finding instead, and
    giving it a page would be publishing the mistake.

    A field naming no vocabulary is open the same way, and for a plainer
    reason: there is no closed set for a value to fall outside of."""
    from .contract import effective_values
    out = []
    for name, vocab, field in _fields(scheme):
        loose_ok = field.vocabulary is None or not field.closed
        under: dict[str, list] = {v: [] for v in field.values}
        loose: dict[str, list] = {}
        for doc in docs:
            for value in effective_values(field, doc.meta.get(name)) or []:
                value = str(value)
                if value in under:
                    under[value].append(doc)
                elif loose_ok:
                    loose.setdefault(value, []).append(doc)
        under.update({v: loose[v] for v in sorted(loose)})
        out.append((name, vocab, field, under))
    return out


def _noun(scheme) -> str:
    return "decisions" if scheme.prefix == "ADR" else f"{scheme.prefix} documents"


def _meta_of(vocab) -> dict[str, dict]:
    return declared(vocab.values_by_name) if vocab is not None else {}


def index_blocks(scheme, docs) -> str:
    """The `{categories}` block on a scheme's index: one block per grouped
    field, the axis first.

    Two shapes, and the scheme's own `axis:` chooses between them rather
    than the code knowing which field is special. The axis is the browsing
    surface, so its values list the documents under them; every other field
    is a row of chips with counts, because the value's own page already
    holds the table (ADR-098). One walk, one label rule, one blurb
    rule, one ordering rule — where there were two of each, and they had
    drifted."""
    from .adr_index import prefix_for
    prefix = prefix_for(scheme, scheme.view)
    blocks = []
    for name, vocab, field, under in _listing(scheme, docs):
        meta = _meta_of(vocab)
        if name == (getattr(scheme, "axis", "") or ""):
            for value, listed in under.items():
                info = meta.get(value, {})
                blurb = f" — {info['blurb']}" if info.get("blurb") else ""
                # A temporary document (ADR-049) has no number to abbreviate
                # to, so its chip is the tail — still short, still a link.
                links = " · ".join(
                    f"[{d.number:03d}]({prefix}{d.path.name})"
                    if d.number is not None
                    else f"[{d.tail}]({prefix}{d.path.name})" for d in listed)
                # A declared value nobody uses still gets its row and its
                # page — the vocabulary says the value exists, and `(0)` is
                # the useful thing to know about it — but not a colon
                # introducing a list of nothing.
                head = f"**[{_label(info, value)}]({name}/{value}.md)** " \
                       f"({len(listed)}){blurb}"
                blocks.append(f"{head}:\n{links}" if listed else f"{head}.")
            continue
        chips = []
        for value, listed in under.items():
            note = (", the default" if field.default
                    and value in field.default else "")
            chips.append(f"[{_label(meta.get(value, {}), value)}]"
                         f"({name}/{value}.md) ({len(listed)}{note})")
        if chips:
            blocks.append(f"**By {name.replace('_', ' ')}:** " + " · ".join(chips))
    return "\n\n".join(blocks)


def pages(scheme, docs) -> dict[Path, str]:
    """A page per value, at `<view>/<field>/<value>.md` — the axis's pages
    among them, on the same template.

    They were two templates: the axis's said "ADRs tagged `x`" and
    sentence-cased the blurb, every other field's named the field and
    rendered `**Label** — blurb`. Same directory, same table, same footer,
    two spellings of the heading and two of the blurb (ADR-098)."""
    from .adr_index import TABLE_HEAD, prefix_for
    out: dict[Path, str] = {}
    noun = _noun(scheme)
    for name, vocab, field, under in _listing(scheme, docs):
        meta = _meta_of(vocab)
        where = scheme.vocab_dir(name)
        prefix = prefix_for(scheme, where)
        for value, listed in under.items():
            info = meta.get(value, {})
            label = _label(info, value)
            raw = str(info.get("blurb") or "")
            blurb = f"**{label}**" + (f" — {raw}" if raw else "") + ".\n\n"
            default = (f" — the default when `{name}:` is absent"
                       if field.default and value in field.default else "")
            # The vocabulary's own account of itself, above the value's
            # (#279). A reader landing on one value's page has the set's
            # purpose in front of them rather than having to infer the axis
            # from the one member they happened to arrive at.
            about = ""
            if vocab is not None and getattr(vocab, "blurb", ""):
                called = getattr(vocab, "label", "") or f"`{vocab.name}`"
                about = f"*{called} — {vocab.blurb}*\n\n"
            out[where / f"{value}.md"] = (
                f"<!-- GENERATED by `luria index` — do not edit. -->\n\n"
                f"# {scheme.prefix}s with `{name}` `{value}`\n\n"
                f"{about}"
                f"{blurb}"
                f"{len(listed)} of {len(docs)} {noun}{default}. "
                f"Back to the [full index](../README.md).\n\n"
                + TABLE_HEAD
                + "\n".join(d.row(prefix=prefix) for d in listed)
                + "\n")
    return out
