# luria/view_pins.py
"""A pinned view: an output that stops moving once it is published
(ADR-130, phase 4).

    views:
      paper:
        template: record/views.d/paper.md.j2
        output: docs/paper.md
        pin: true

    luria views                 # every view, and whether its pin holds
    luria views --pin paper     # render it, write it, endorse what it read

A view is a function of the record, so it moves when the record does. That
is right for a bootloader and wrong for a paper that has been submitted:
the text a reviewer read must stay the text in the repository, while the
claims it was made from go on changing. A pin keeps both.

The model is `pins.py`'s, pointed inward. `pin: true` in `luria.yaml` is the
REGISTRATION. `luria views --pin NAME` is the endorsement: it renders the
view, writes the output, and records in `views.lock.json` a hash of that
output and, per document, a hash of every value the render read from it.
After that:

- `luria index` leaves the committed output alone, so `--check` does not
  call it stale;
- `luria lint` re-renders the view and reports `view-drift` when what it
  reads has changed, naming each document that moved. A document the view
  never read from is not compared, so an edit to a part the paper does not
  quote is not drift. A template change is reported as one, and so is a
  committed output that is not the one endorsed;
- re-endorsing after review is the acknowledgement, and it re-renders.

A registered pin with no endorsement renders like any other view, and is
reported until someone endorses it.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from . import views, writes
from .config import current

LOCK = "views.lock.json"


def lock_path() -> Path:
    return current().root / LOCK


def _lock() -> dict:
    path = lock_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def endorsed(view) -> dict | None:
    """The lock entry for a pinned view, or None: not pinned, or pinned and
    not yet endorsed."""
    return _lock().get(view.name) if view.pin else None


def held(view) -> str | None:
    """The committed output a pin holds in place, or None when the view
    renders as any other: not pinned, never endorsed, or no output on disk
    to hold (a fresh checkout of a view nobody committed renders anew)."""
    if endorsed(view) is None or not view.output.exists():
        return None
    return view.output.read_text(encoding="utf-8")


def endorse(name: str) -> None:
    """Render the view, write its output, and endorse what it read."""
    cfg = current()
    view = cfg.views.get(name)
    if view is None:
        print(f"luria views: no view {name!r} "
              f"(views: {', '.join(sorted(cfg.views)) or 'none'})",
              file=sys.stderr)
        raise SystemExit(1)
    if not view.pin:
        print(f"luria views: views.{name} has no `pin: true`, so nothing "
              "would hold its output — register the pin in luria.yaml first",
              file=sys.stderr)
        raise SystemExit(1)
    found = views.rendering(view)
    view.output.parent.mkdir(parents=True, exist_ok=True)
    writes.write_text(view.output, found.text)
    lock = _lock()
    lock[name] = {"output": _digest(found.text),
                  "reads": {code: read.digest
                            for code, read in sorted(found.reads.items())}}
    writes.write_text(lock_path(),
                      json.dumps(lock, indent=2, sort_keys=True) + "\n")
    print(f"views.{name}: pinned {cfg.rel(view.output)}, "
          f"{len(found.reads)} document(s) endorsed")


def drift_rows() -> list[str]:
    """One line per pinned view whose pin no longer holds."""
    cfg = current()
    rows = []
    for view in cfg.views.values():
        if not view.pin:
            continue
        remedy = f"`luria views --pin {view.name}` after review"
        entry = endorsed(view)
        if entry is None:
            rows.append(f"views.{view.name}: `pin: true` and never endorsed "
                        f"— {remedy} holds its output")
            continue
        committed = held(view)
        if committed is not None and _digest(committed) != entry["output"]:
            rows.append(f"views.{view.name}: {cfg.rel(view.output)} is not "
                        f"the output that was pinned — regenerate it with "
                        f"{remedy}, never by hand")
            continue
        try:
            fresh = views.rendering(view)
        except views.ViewError:
            continue        # `views.errors` reports the template
        if _digest(fresh.text) == entry["output"]:
            continue
        was, now = entry.get("reads", {}), fresh.reads
        moved = sorted(code for code in set(was) | set(now)
                       if code not in now or code not in was
                       or now[code].digest != was[code])
        what = (f"{', '.join(moved)} changed" if moved
                else "the template changed")
        rows.append(f"views.{view.name}: pinned, and {what} since — "
                    f"{remedy} re-renders it")
    return rows


def run(pin: str = "") -> None:
    """Every view, and whether its pin holds. --pin NAME renders that view,
    writes its output and endorses what it read (`views.lock.json`), after
    which `luria index` leaves the output alone."""
    if pin:
        endorse(pin)
        return
    drift = {row.split(":", 1)[0] for row in drift_rows()}
    for view in current().views.values():
        state = ("unpinned" if not view.pin
                 else "drifted" if f"views.{view.name}" in drift
                 else "pinned")
        print(f"{view.name}: {current().rel(view.output)} ({state})")
