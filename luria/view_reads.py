# luria/view_reads.py
"""What the views read, and what follows from it (ADR-130, phase 3).

    views.boot: record/views.d/CLAUDE.md.j2:12 transcludes CLAIM-012, which is Superseded (by CLAIM-031)

A view is a pure function of the record, so it is stale the moment the
record moves, and `luria index --check` says so. That is not the same as
being wrong. A template that transcludes a claim keeps rendering it after
the claim is superseded, faithfully, with nothing on the page to say the
record no longer holds it. The citation scan cannot see this: a view's
output is generated, so nobody can annotate it, and it is excluded like
every other view. What the scan cannot see the render can, because the
render knows which document each template line read.

**Only a transclusion of a retired document is a finding.** Naming a
superseded claim, listing its title or printing its status is what a page
about revisions does. Carrying its body, a part of it or its summary into
the output is asserting what it says. Retired means its status is the word
its scheme gives `retires_on`, the one word luria knows means "no longer
held"; a Proposed claim is still in play and is not reported.

It is a warning, failable through `lint.fail_on` like the other reference
findings (ADR-035), acknowledged at the template line that reads it, or on
the line above, with the same `inactive-ok:` the citation scan takes:

    {# inactive-ok: CLAIM-012 — quoted as the position it replaced #}
"""

from __future__ import annotations

import re

from . import views
from .config import current


def renderings(rendered: dict | None = None) -> dict[str, "views.Rendering"]:
    """Every view that renders, by name, with what it read. `rendered` is a
    view tree already built, whose renderings are reused."""
    out = {}
    for view in current().views.values():
        try:
            out[view.name] = views.rendering(
                view, (rendered or {}).get(view.output))
        except views.ViewError:
            continue        # `views.errors` reports it; nothing was read
    return out


def _acknowledged(template: str, line: int, code: str) -> bool:
    """`inactive-ok: CODE` on the site's line or the one above it."""
    try:
        lines = (current().root / template).read_text(
            encoding="utf-8").splitlines()
    except OSError:
        return False
    said = re.compile(rf"inactive-ok:[^\n]*(?<![\w-]){re.escape(code)}(?![\w-])")
    return any(said.search(lines[i]) for i in (line - 2, line - 1)
               if 0 <= i < len(lines))


def retired_rows(rendered: dict | None = None) -> list[str]:
    """One line per template site transcluding a retired document."""
    rows = []
    for name, found in renderings(rendered).items():
        for read in found.reads.values():
            if not read.retired:
                continue
            after = (f" (by {', '.join(read.successors)})"
                     if read.successors else "")
            for site in read.sites:
                if site.kind != "transcluded" or _acknowledged(
                        site.template, site.line, read.code):
                    continue
                rows.append(f"views.{name}: {site.template}:{site.line} "
                            f"transcludes {read.code}, which is "
                            f"{read.status}{after}")
    return rows


def rendered_into(rendered: dict | None = None) -> dict[str, list[str]]:
    """Each document a view read, mapped to the outputs it renders into,
    root-relative, in view order."""
    cfg = current()
    out: dict[str, list[str]] = {}
    for name, found in renderings(rendered).items():
        target = cfg.rel(cfg.views[name].output)
        for code in found.reads:
            out.setdefault(code, [])
            if target not in out[code]:
                out[code].append(target)
    return out
