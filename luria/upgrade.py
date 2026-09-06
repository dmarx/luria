#!/usr/bin/env python3
"""`luria upgrade` — carry a record across a version boundary (#181).

    luria upgrade statuses            # write what the new version requires
    luria upgrade statuses --dry-run  # print what it would write

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

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

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
    "statuses": Upgrade(
        summary="declare `status:` as the controlled vocabulary it is",
        sunset="every record that predates #181 has run it. Luria has one "
               "user today, so: once luria's own record and the anthology "
               "are both on the release that carries this.",
    ),
}


def _statuses_yaml() -> str:
    lines = [
        "# The words this scheme's documents may use, and what each means.",
        "#",
        "# `status:` is a controlled vocabulary like any other, and this is",
        "# the vocabulary: `[luria.schemes.X.fields.status]` in luria.toml is",
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
    raw = tomllib.loads(config.read_text(encoding="utf-8"))
    schemes = _schemes(raw)
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
        lines += [f"[luria.schemes.{prefix}.fields.status]",
                  'vocabulary = "statuses"', ""]
        values = root / str(spec.get("dir", "")) / "statuses.yaml"
        if not values.exists():
            writes.append((values, _statuses_yaml()))
    return writes, lines, notes


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
            print(f"  would append {len(lines) // 3} declaration(s) to "
                  f"{CONFIG_NAME}")
        return
    for path, text in writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(where)}")
    if lines:
        config = where / CONFIG_NAME
        body = config.read_text(encoding="utf-8").rstrip("\n")
        config.write_text(
            body + "\n\n# `status:` declared as the controlled vocabulary it "
            "is (#181),\n# written by `luria upgrade statuses`.\n"
            + "\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
        print(f"  declared `status` for {len(lines) // 3} scheme(s) "
              f"in {CONFIG_NAME}")


if __name__ == "__main__":
    import fire
    fire.Fire(run)
