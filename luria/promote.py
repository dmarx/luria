# luria/promote.py
"""`promote_vocabulary`: a migration operation that turns a vocabulary into
the scheme it was abbreviating.

    operations:
    - op: promote_vocabulary
      vocabulary: area          # the vocabulary to promote
      to: AREA                  # the new scheme's prefix
      dir: record/areas.d       # optional: defaults from the prefix
      output: docs/areas        # optional: defaults from the prefix
      status_vocabulary: statuses   # optional: defaults to `statuses`
      active: Active            # optional: the word that means in force

A vocabulary is a shorthand for a tiny constrained scheme: named values with
a label and a blurb, and nothing else. A record that needs a value to carry
more — standing, history, relations of its own, a place in a hierarchy — is
showing a type error, and the repair is the long form, not a richer
shorthand. Promotion writes it:

- **One document per value**, numbered in the vocabulary's order, then any
  value in use that the vocabulary never declared (an open field's), sorted.
  The value's `label` becomes the title, its `blurb` the summary, and its old
  spelling is kept as `slug:` — a unique field, because it was an identity.
  The scheme derives an alias from it (`alias: "AREA-{slug}"`, #219), so the
  documents go on citing `AREA-runtime` rather than an opaque `AREA-001`.
- **Every field that drew from the vocabulary becomes a reference** to the
  new scheme, `group: true`, so the views it had — a page per value, the
  scheme's `axis` — survive as a page per target. `required` is written out:
  a reference is required unless it says otherwise, a vocabulary field was
  optional unless it said so.
- **Documents now hold the term's alias**, `AREA-runtime` for `runtime`: a
  typed reference that still reads as the value did. Only the frontmatter
  field is rewritten;
  prose is never swept for a value's spelling, because a word in a sentence
  is not a citation of it.
- **The vocabulary is removed**, and its own `label`/`blurb`, if it had
  them, become the new scheme's `title`/`blurb`.

What a reference cannot carry is refused, not dropped: a `default`, value
`groups`, a derivation, an `alert`. A migration that silently loses a
constraint reports success over a record that now checks less (DP-1). So is
a vocabulary behind a `status` field — standing is read off those words, and
they are not documents.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from . import yaml_edit
from .config import current, reset
from . import writes

# What a vocabulary field may say that a reference can say too. `closed` is
# dropped on purpose: a reference is closed by construction, which is the
# promotion's point.
CARRIED = {"vocabulary", "many", "required", "required_when",
           "forbidden_when", "label", "blurb", "closed"}


@dataclass(frozen=True)
class Promotion:
    vocabulary: str
    prefix: str
    dir: str
    output: str
    status_vocabulary: str
    active: str
    # (value as written, its alias-safe slug, {label, blurb}), in document
    # order. The slug is the value unless the value holds a character an
    # alias cannot (a space, an underscore), in which case it is slugged.
    values: tuple[tuple[str, str, dict], ...]
    # (scheme prefix, field name) for every field drawing from the vocabulary.
    fields: tuple[tuple[str, str], ...]
    # The vocabulary's own description, for the scheme's title and blurb.
    about: tuple[tuple[str, str], ...] = ()

    @property
    def mapping(self) -> dict[str, str]:
        """Slug → code, in the order the documents are filed."""
        return {value: f"{self.prefix}-{n:03d}"
                for n, (value, _, _) in enumerate(self.values, start=1)}

    @property
    def spellings(self) -> dict[str, str]:
        """Value → the alias documents cite it by, `AREA-runtime`."""
        return {value: f"{self.prefix}-{slug}"
                for value, slug, _ in self.values}


def _raw() -> dict:
    return yaml.safe_load((current().root / "luria.yaml")
                          .read_text(encoding="utf-8")) or {}


def alias_slug(value: str) -> str:
    """The value as an alias tail can spell it: unchanged when it already
    can (letters, digits, dots, hyphens), otherwise lower-cased with every
    other run of characters collapsed to one hyphen."""
    import re
    from .aliases import ALIAS_RE
    if ALIAS_RE.match(f"X-{value}"):
        return value
    return re.sub(r"[^a-z0-9.]+", "-", value.lower()).strip("-.")


def _slug(prefix: str) -> str:
    """The directory name a prefix implies — the convention `luria init`
    uses, so a promoted scheme lands where a declared one would."""
    from .init import _slug as init_slug
    return init_slug(prefix)


def _in_use(prefix: str, field: str) -> list[str]:
    """Every value documents of `prefix` hold in `field`, as written."""
    from .adr_index import load_scheme
    found = []
    for doc in load_scheme(current().schemes[prefix]):
        raw = doc.meta.get(field)
        for value in raw if isinstance(raw, list) else [raw]:
            if value not in (None, ""):
                found.append(str(value))
    return found


def plan(op: dict) -> Promotion:
    """Validate the operation against the config and the tree, and say what
    it will do. Refuses before anything is written."""
    cfg, raw = current(), _raw()
    name = str(op.get("vocabulary", ""))
    prefix = str(op.get("to", "")).upper()
    where = f"luria migrate: promote_vocabulary {name!r}"
    vocabularies = raw.get("vocabularies") or {}
    if name not in vocabularies:
        raise SystemExit(f"{where}: no vocabulary named {name!r} "
                         f"(declared: {', '.join(sorted(vocabularies))})")
    if not prefix:
        raise SystemExit(f"{where}: `to` names the new scheme's prefix")
    if prefix in (raw.get("schemes") or {}):
        raise SystemExit(f"{where}: scheme {prefix!r} already exists — "
                         f"promotion writes a new one")

    fields: list[tuple[str, str]] = []
    for scheme_prefix, spec in (raw.get("schemes") or {}).items():
        for field, fspec in ((spec or {}).get("fields") or {}).items():
            if not isinstance(fspec, dict) or fspec.get("vocabulary") != name:
                continue
            if field == "status":
                raise SystemExit(
                    f"{where}: {scheme_prefix}.status draws from it, and "
                    f"standing is read off a status vocabulary's words — they "
                    f"are not documents")
            extra = sorted(set(fspec) - CARRIED)
            if extra:
                raise SystemExit(
                    f"{where}: {scheme_prefix}.{field} declares "
                    f"{', '.join(chr(96) + k + chr(96) for k in extra)}, which "
                    f"a reference cannot carry — remove it first, so the "
                    f"record does not silently check less")
            fields.append((str(scheme_prefix), str(field)))

    declared = cfg.vocabularies.get(name) or {}
    for value, meta in declared.items():
        if isinstance(meta, dict) and meta.get("primary_for"):
            raise SystemExit(
                f"{where}: value {value!r} declares `primary_for`, which "
                f"derives tag groups a reference cannot carry — remove it "
                f"first")
    ordered = [(str(v), dict(m or {})) for v, m in declared.items()]
    seen = {v for v, _ in ordered}
    loose = sorted({v for p, f in fields for v in _in_use(p, f)} - seen)
    ordered += [(v, {}) for v in loose]

    status_vocabulary = str(op.get("status_vocabulary")
                            or ("statuses" if "statuses" in vocabularies
                                else ""))
    active = str(op.get("active", "Active"))
    if status_vocabulary:
        words = cfg.vocabularies.get(status_vocabulary)
        if words is None:
            raise SystemExit(f"{where}: no vocabulary named "
                             f"{status_vocabulary!r} for the new scheme's "
                             f"status")
        if active not in words:
            raise SystemExit(
                f"{where}: {active!r} is not a word of {status_vocabulary!r} "
                f"— name the in-force word with `active:`")

    from .aliases import ALIAS_RE, canon
    slugged: dict[str, str] = {}
    for value, _ in ordered:
        tail = alias_slug(value)
        if not tail or not ALIAS_RE.match(f"{prefix}-{tail}"):
            raise SystemExit(f"{where}: value {value!r} has no spelling an "
                             f"alias can carry")
        if canon(f"{prefix}-{tail}") is not None:
            raise SystemExit(
                f"{where}: value {value!r} reads as a code ({prefix}-{tail}), "
                f"and a code outranks an alias — it would cite whatever "
                f"document holds that number; rename the value first")
        if tail in slugged:
            raise SystemExit(
                f"{where}: values {slugged[tail]!r} and {value!r} both spell "
                f"the alias {prefix}-{tail} — rename one first")
        slugged[tail] = value
    triples = [(value, alias_slug(value), meta) for value, meta in ordered]

    slug = _slug(prefix)
    about = cfg.vocabulary_meta.get(name) or {}
    return Promotion(
        vocabulary=name, prefix=prefix,
        dir=str(op.get("dir") or f"record/{slug}.d"),
        output=str(op.get("output") or f"docs/{slug}"),
        status_vocabulary=status_vocabulary, active=active,
        values=tuple(triples), fields=tuple(fields),
        about=tuple((k, str(v)) for k, v in about.items()
                    if k in ("label", "blurb") and v))


def describe(p: Promotion) -> list[str]:
    lines = [f"  promote vocabulary {p.vocabulary} -> {p.prefix} "
             f"({p.dir}, {p.output})"]
    lines += [f"  {value} -> {code} (cited as {p.spellings[value]})"
              for value, code in p.mapping.items()]
    lines += [f"  {scheme}.{field}: vocabulary -> grouped reference to "
              f"{p.prefix}" for scheme, field in p.fields]
    return lines


def _config_edit(p: Promotion) -> None:
    path = current().root / "luria.yaml"
    data = yaml_edit.load(path.read_text(encoding="utf-8"))
    entry: dict = {"dir": p.dir, "output": p.output, "render": "index",
                   "alias": f"{p.prefix}-{{slug}}"}
    about = dict(p.about)
    if about.get("label"):
        entry["title"] = about["label"]
    if about.get("blurb"):
        entry["blurb"] = about["blurb"]
    if p.active != "Active":
        entry["active"] = p.active
    fields: dict = {}
    if p.status_vocabulary:
        fields["status"] = {"vocabulary": p.status_vocabulary}
    fields["slug"] = {"unique": True}
    entry["fields"] = fields
    yaml_edit.ensure(data, ("schemes",))[p.prefix] = entry

    for scheme, field in p.fields:
        spec = data["schemes"][scheme]
        old = spec["fields"][field]
        ref = {"scheme": p.prefix, "many": bool(old.get("many", False)),
               "required": bool(old.get("required", False)), "group": True}
        for key in ("required_when", "forbidden_when", "label", "blurb"):
            if key in old:
                ref[key] = old[key]
        del spec["fields"][field]
        if not spec["fields"]:
            del spec["fields"]
        yaml_edit.ensure(spec, ("references",))[field] = ref

    del data["vocabularies"][p.vocabulary]
    if not data["vocabularies"]:
        del data["vocabularies"]
    writes.write_text(path, yaml_edit.dump(data))


def _scaffold(p: Promotion) -> None:
    """The new scheme's directory starts as a declared one's would — a
    `_template.md` and a `README.stub` from `luria init`'s own shapes — so
    the next term is filed with `luria new` like any other entry."""
    from .init import _scheme_files
    for path, text in _scheme_files(current().schemes[p.prefix]).items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            writes.write_text(path, text)


def _file_documents(p: Promotion) -> None:
    """One document per value, through `luria new`'s own filing. The body is
    the value's blurb, or a line saying where the term came from: the
    template's placeholder prose is for a person starting from nothing, and
    these documents start from something."""
    from .new import _drop_field, new_scheme_doc
    for value, slug, meta in p.values:
        reset()  # the next number is read off the directory
        blurb = str(meta.get("blurb") or "").strip()
        values = {"title": str(meta.get("label") or slug), "slug": slug,
                  "status": p.active,
                  "body": blurb or (f"Promoted from the `{p.vocabulary}` "
                                    f"vocabulary, where it was `{value}`.")}
        if blurb:
            values["summary"] = blurb
        scheme = current().schemes[p.prefix]
        path = new_scheme_doc(scheme, values)
        # The shared template seeds `tags:`; a promoted scheme declares none.
        if "tags" not in scheme.grouped_fields:
            text = path.read_text(encoding="utf-8")
            writes.write_text(path, _drop_field(text, "tags"))


def _rewrite(path: Path, field: str, many: bool,
             mapping: dict[str, str]) -> bool:
    """Swap one frontmatter field's values for their aliases. Text surgery on
    the frontmatter alone, so the body and every other field are untouched."""
    from .new import _sub_line
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[3:]:
        return False
    end = text.index("\n---\n", 3)
    head, rest = text[:end + 1], text[end + 1:]
    meta = yaml.safe_load(head[4:]) or {}
    raw = meta.get(field)
    if raw in (None, "", []):
        return False
    values = raw if isinstance(raw, list) else [raw]
    codes = [mapping.get(str(v), str(v)) for v in values]
    head = _sub_line(head, field, codes if many else codes[0], many=many)
    writes.write_text(path, head + rest)
    return True


def apply(p: Promotion) -> int:
    """Execute the promotion. Returns the number of documents rewritten."""
    _config_edit(p)
    reset()
    _scaffold(p)
    _file_documents(p)
    reset()
    cfg, mapping, rewritten = current(), p.spellings, 0
    for scheme_prefix, field in p.fields:
        scheme = cfg.schemes[scheme_prefix]
        ref = next(r for r in scheme.references if r.field == field)
        paths = list(scheme.documents().values()) + \
            list(scheme.temp_documents().values())
        for path in paths:
            rewritten += _rewrite(path, field, ref.many, mapping)
    reset()
    return rewritten
