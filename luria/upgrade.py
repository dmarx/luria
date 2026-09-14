#!/usr/bin/env python3
"""`luria upgrade` — carry a record across a version boundary (#181).

    luria upgrade                     # list them, with what each waits on
    luria upgrade yaml                # luria.toml -> luria.yaml
    luria upgrade yaml --dry-run      # print what it would write

**Every command in here is temporary by construction.** An upgrade exists to
move records that predate a change onto it, and once they have moved it is
dead code that still has to be read, tested and explained. `SUNSET` below
says, for each one, what has to be true before it is deleted — and `luria
lint` reports an upgrade this record no longer needs, so the question comes
up on its own rather than waiting to be remembered. That is the same posture
`stale-directives` takes: a guard that no longer guards anything is worse
than no guard, because it reads like one.

Nothing here goes through `config.load()`. The config an upgrade repairs is
the config the new version refuses to load, so a command that needed it
would be unrunnable in exactly the situation it exists for.
"""

# inactive-ok-file: ADR-098 — Proposed. Every mention names it as the decision
# this module implements; the citation is to the reasoning, not a claim the
# decision is settled.

from __future__ import annotations

import tomllib

import yaml
from dataclasses import dataclass
from pathlib import Path

from . import yaml_edit
from .config import CONFIG_NAME, find_root
from .statuses import DEFAULT_STATUSES

_BLURBS = {
    "Active": "in force — the current answer, and what a citation should "
              "normally point at",
    "Proposed": "not in force yet — an open question, so citing it as settled "
                "is what the reference report catches",
    "Deferred": "not in force and not being worked on; the question is real "
                "and the answer waits on something",
    "Superseded": "no longer in force because something replaced it; the "
                  "successor is named in the field, not in the prose",
    "Rejected": "no longer in force and nothing replaced it — kept because a "
                "rejection is worth being able to point at",
}


@dataclass(frozen=True)
class Upgrade:
    """One version boundary, and what has to be true before it is deleted."""
    summary: str
    sunset: str


SUNSET = {
    "yaml": Upgrade(
        summary="convert `luria.toml` and the per-scheme vocabulary files "
                "into one `luria.yaml`",
        sunset="1.0.0, or when no record on TOML remains. This is the only "
               "way across the boundary ADR-098 drew — the new version "
               "does not read TOML at all — so it has to outlive every "
               "record that has not crossed it.",
    ),
    "statuses": Upgrade(
        summary="declare `status:` as the controlled vocabulary it is",
        sunset="1.0.0. Both records that predated #181 have run it "
               "already, but more are coming onto luria before the first "
               "stable release, and each of them predates #181 too. The "
               "pin is the version rather than a list of projects because "
               "a list is never finished at the moment you read it.",
    ),
}


def _statuses_yaml() -> str:
    lines = [
        "# The words this scheme's documents may use, and what each means.",
        "#",
        "# `status:` is a controlled vocabulary like any other, and this is",
        "# the vocabulary: `schemes.X.fields.status` in luria.yaml is",
        "# the wiring. Rename these, drop what you do not want, add your own.",
        "# The one rule is that the scheme's `active` word has to appear here",
        "# — it is how everything decides what is in force.",
        "",
    ]
    for word in DEFAULT_STATUSES:
        lines += [f"{word}:", f"  blurb: {_BLURBS[word]}"]
    return "\n".join(lines) + "\n"


def _schemes(raw: dict) -> dict[str, dict]:
    return (raw.get("luria", raw) or {}).get("schemes", {}) or {}


def _plan(root: Path) -> tuple[list[tuple[Path, str]], list[str], list[str]]:
    """(files to write, config lines to append, notes) — nothing written."""
    config = root / CONFIG_NAME
    if not config.exists():
        return [], [], [f"no {CONFIG_NAME} at {root} — nothing to upgrade"]
    raw = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
    schemes = _schemes(raw.get("luria", raw))
    if not schemes:
        return [], [], [
            f"{CONFIG_NAME} declares no schemes, so this record runs on the "
            f"shipped default — `luria init --config` writes it out first"]
    writes: list[tuple[Path, str]] = []
    lines: list[str] = []
    notes: list[str] = []
    for prefix, spec in schemes.items():
        if "status" in (spec.get("fields") or {}):
            notes.append(f"{prefix}: already declares `status` — left alone")
            continue
        # The vocabulary lives in the config under a name every scheme can
        # point at, rather than a statuses.yaml beside each one (ADR-098).
        lines.append(prefix)
    return writes, lines, notes


def _declared(text: str, prefixes: list[str], values: dict) -> str:
    """`text` with `status` wired up for each scheme, and the vocabulary it
    names declared once.

    Written into the document rather than onto the end of it. YAML nests by
    indentation, so an appended `schemes.VP.statuses: x` is a key literally
    called "schemes.VP.statuses", and an appended indented block joins
    whichever top-level key happens to be last — both of them silent. The
    round trip is ruamel's, so the comments a project wrote in its own
    config come through it (ADR-098)."""
    data = yaml_edit.load(text)
    base = ("luria",) if isinstance(data.get("luria"), dict) else ()
    for prefix in prefixes:
        yaml_edit.merge_into(
            data, {"fields": {"status": {"vocabulary": "statuses"}}},
            base + ("schemes", prefix))
    vocabularies = yaml_edit.at(data, base + ("vocabularies",))
    if vocabularies is None:
        # First in the file, because a reader asking what a status *means*
        # should not have to scroll past every scheme to find out.
        into = yaml_edit.ensure(data, base) if base else data
        into.insert(0, "vocabularies", {})
        vocabularies = into["vocabularies"]
    words = vocabularies.setdefault("statuses", {})
    for word, blurb in values.items():
        words.setdefault(word, {"blurb": blurb})
    return yaml_edit.dump(data)


TOML_NAME = "luria.toml"


def convert_config(root: Path) -> tuple[str, list[str], list[Path]]:
    """One `luria.yaml` from a TOML config and the vocabulary files beside
    each scheme's records: (the YAML, what it folded, what nothing reads now).

    **Parsed with `tomllib` and written with `yaml`, never moved as bytes.**
    `uid = "(\\d{4})[.:](\\d{4,5})"` does not survive a copy — the two
    formats escape differently — so every value is re-encoded by a writer that
    knows its own rules. That is the only version of this that is safe, and
    the reason a regex in a `uid` is the thing to check afterwards.

    A vocabulary two schemes hold identical copies of becomes ONE entry they
    both name, which is the whole point of the boundary (ADR-098)."""
    cfg = tomllib.loads((root / TOML_NAME).read_text(encoding="utf-8"))
    cfg = cfg.get("luria", cfg)
    vocabs: dict[str, dict] = {}
    by_text: dict[str, str] = {}
    notes: list[str] = []
    orphans: list[Path] = []
    for prefix, spec in (cfg.get("schemes") or {}).items():
        for kind in ("tags", "statuses"):
            f = root / str(spec.get("dir", "")) / f"{kind}.yaml"
            if not f.exists():
                continue
            text = f.read_text(encoding="utf-8")
            orphans.append(f)
            if text in by_text:
                spec[kind] = by_text[text]
                notes.append(f"{prefix}.{kind} -> {by_text[text]} "
                             f"(the same words {by_text[text]} already holds)")
                continue
            name = f"{prefix.lower()}-{kind}"
            vocabs[name] = yaml.safe_load(text) or {}
            by_text[text] = name
            spec[kind] = name
            notes.append(f"{prefix}.{kind} -> {name}")
    # A field's `vocabulary` named a file stem beside the records.
    for prefix, spec in (cfg.get("schemes") or {}).items():
        for fspec in (spec.get("fields") or {}).values():
            named = fspec.get("vocabulary")
            if named in ("tags", "statuses") and spec.get(named):
                fspec["vocabulary"] = spec[named]
            elif named and named not in vocabs:
                f = root / str(spec.get("dir", "")) / f"{named}.yaml"
                if f.exists():
                    vocabs[named] = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
                    orphans.append(f)
                    notes.append(f"{prefix}.fields vocabulary {named} -> {named}")
        # `status` and `tags` are fields, so their vocabularies are named in
        # `fields:` and nowhere else. A record that never declared either
        # still had the `.yaml` beside its records, which the old code read
        # by position; wiring them up here is what carries the vocabularies
        # across, and `schemes.X.statuses`/`.tags` do not exist on the far
        # side of the boundary.
        fields = spec.setdefault("fields", {})
        if folded := spec.pop("statuses", ""):
            if not (fields.get("status") or {}).get("vocabulary"):
                fields.setdefault("status", {})["vocabulary"] = folded
                notes.append(f"{prefix}.status -> vocabulary {folded}")
        folded = spec.pop("tags", "")
        # `tag_groups` constrained a subset of the tag vocabulary; it is
        # declared with the field it constrains now.
        moved = spec.pop("tag_groups", None)
        if folded or moved or "tags" in fields:
            entry = fields.setdefault("tags", {})
            if folded and not entry.get("vocabulary"):
                entry["vocabulary"] = folded
            # What `tags:` always was and nothing could say: many, expected
            # on every entry, and OPEN — a new tag is an edit to a document.
            entry.setdefault("many", True)
            entry.setdefault("required", True)
            entry.setdefault("closed", False)
            if moved is not None:
                entry["groups"] = moved
                notes.append(f"{prefix}.tag_groups -> fields.tags.groups")
            # Which field heads the index. Every record crossing this
            # boundary has exactly one, because the old code only had one.
            spec["axis"] = "tags"
            notes.append(f"{prefix}.tags -> field, axis"
                         + (f", vocabulary {folded}" if folded else ""))
    out = {"vocabularies": vocabs, **cfg} if vocabs else cfg
    # Emitted by the module that also *edits* configs, so a freshly converted
    # file is already in the shape every later `luria init`/`migrate` writes.
    # Two emitters would mean the first one-key edit reflowed the whole file.
    return yaml_edit.dump(out), notes, orphans


def _run_yaml(where: Path, dry_run: bool) -> None:
    """The boundary crossing. Leaves the TOML on disk: deleting what you just
    converted, before anyone has read the result, is not a migration anybody
    should trust."""
    if not (where / TOML_NAME).exists():
        print(f"yaml: no {TOML_NAME} at {where} — this record is already "
              f"across, and `luria upgrade yaml` can be deleted once every "
              f"other one is")
        return
    text, notes, orphans = convert_config(where)
    for note in notes:
        print(f"  {note}")
    if dry_run:
        print(f"  would write {CONFIG_NAME}")
        for f in orphans:
            print(f"  would leave {f.relative_to(where)} unread")
        return
    (where / CONFIG_NAME).write_text(text, encoding="utf-8")
    print(f"  wrote {CONFIG_NAME}")
    if orphans:
        print(f"\n  nothing reads these now — check the result first, then:")
        print("    git rm " + " ".join(str(f.relative_to(where)) for f in orphans)
              + f" {TOML_NAME}")
    print("\n  check a regex survived the format change before you trust it:"
          "\n    luria lint")


def run(name: str = "", *, dry_run: bool = False, root: str = "") -> None:
    """Write what a new version requires into a record that predates it.

    NAME is the upgrade to run; with none, the available ones are listed
    with what each is waiting on before it can be deleted."""
    where = Path(root).resolve() if root else find_root()
    if not name:
        print("temporary — each is deleted once every record has run it:\n")
        for key, up in SUNSET.items():
            print(f"  luria upgrade {key}\n      {up.summary}"
                  f"\n      remove when: {up.sunset}\n")
        return
    if name not in SUNSET:
        raise SystemExit(f"luria upgrade: no upgrade named {name!r} "
                         f"(have: {', '.join(SUNSET) or 'none'})")
    if name == "yaml":
        return _run_yaml(where, dry_run)
    if (where / TOML_NAME).exists() and not (where / CONFIG_NAME).exists():
        raise SystemExit(
            f"luria upgrade {name}: this record still has a {TOML_NAME}, "
            f"which nothing reads — run `luria upgrade yaml` first")
    writes, lines, notes = _plan(where)
    for note in notes:
        print(f"  {note}")
    if not writes and not lines:
        print(f"{name}: nothing to do — this record is already upgraded, and "
              f"`luria upgrade {name}` can be deleted once every other one is")
        return
    if dry_run:
        for path, _ in writes:
            print(f"  would write {path.relative_to(where)}")
        if lines:
            print(f"  would declare `status` for {len(lines)} scheme(s) in "
                  f"{CONFIG_NAME}")
        return
    for path, text in writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(where)}")
    if lines:
        config = where / CONFIG_NAME
        config.write_text(
            _declared(config.read_text(encoding="utf-8"), lines,
                      {w: _BLURBS[w] for w in DEFAULT_STATUSES}),
            encoding="utf-8")
        print(f"  declared `status` for {len(lines)} scheme(s) "
              f"in {CONFIG_NAME}")


if __name__ == "__main__":
    import fire
    fire.Fire(run)
