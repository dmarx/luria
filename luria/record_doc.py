#!/usr/bin/env python3
"""What *this* project's record is made of, rendered from its own config.

    luria index                 # → <docs>/record.md, with every other view

`configuration.md` is the schema: every key Luria accepts, what it defaults
to, what it means. This page is the other half of the question, and the half a
contributor actually arrives with — **not "what could I configure?" but "what
did we configure, and where does my file go?"** Those are different documents
and only one of them is about this repository. The schema is identical in
every project that installs the package; the answer here is different in every
one, which is why it is generated from `luria.yaml` rather than written once
upstream.

The load-bearing property is the same one `config_doc` has, pointed the other
way: **the tables come from the loaded `Config`, not from a list kept here.**
Declare `schemes.RFC` and RFCs appear in the tables, in the filing
commands and in the citation examples on the next `luria index`. Nothing has
to be remembered, which is the only version of this page that stays true —
a hand-written "how our record works" is precisely the projection DP-3 says
will drift, and it drifts silently, because the reader who would notice is the
newcomer who cannot tell.

**The page is a templated view** (ADR-130's machinery). Its headings,
prose and layout are `luria:record.md.j2`; `context` hands that template
facts read from the config and nothing else. Prose is edited in one place,
and a section with nothing to show is left out by the template, heading and
all. What is missing is reported by the lint, not written into the page. It
renders in the sandbox every view uses but is not linked: the page is made
of example codes, and the codes its prose cites are luria's own.

Two things this page deliberately does not do:

- **It does not repeat the schema.** Every section links to
  `configuration.md` for the key-by-key detail. Restating defaults here would
  be a second copy of the thing generated to avoid a second copy.
- **It does not explain what a decision record is for.** That is doctrine, it
  belongs in prose a human wrote, and a generator has nothing to add to it.

Like the reference, this page registers in `Config.is_generated`: it is made
of example codes, and `doc_refs.doc_files` filters on that flag, so the
bare-reference lint and `luria link --fix` both leave it alone.
"""

from __future__ import annotations

from pathlib import Path

from . import config as config_mod
from . import contract as contract_mod
from .config import current
from . import writes

SCHEMA_URL = ("https://github.com/dmarx/luria/blob/main/docs/"
              "configuration.md")

TEMPLATE = "luria:record.md.j2"


def _rel(cfg, path: Path | None, dir: bool = False) -> str:
    """A path as the reader will type it: relative to the project root, with
    a trailing slash when it names a directory.

    `dir` is passed by the caller rather than read off the disk. A first draft
    asked `Path.is_dir()`, which made the page a function of the filesystem
    and therefore not idempotent: a directory `luria index` creates on its own
    run answers differently before and after, so the page rendered one way,
    was written, and then compared unequal to itself. `luria index && luria
    lint` on a fresh `luria init` caught it — the config always knew which
    kind each path was, and this now asks the config."""
    if path is None:
        return "—"
    try:
        text = str(Path(path).relative_to(cfg.root))
    except ValueError:
        text = str(path)
    return f"`{text}/`" if dir else f"`{text}`"


def schemes_rows(cfg) -> list[list[str]]:
    """One row per referable document family — the thing a code names."""
    rows = []
    for prefix, s in cfg.schemes.items():
        if s.render == "document":
            view = f"{_rel(cfg, s.output)} (one page, read as a whole)"
        else:
            view = f"{_rel(cfg, s.index_path)} + tag pages"
        rows.append([f"`{prefix}-001`", _rel(cfg, s.dir, dir=True), view,
                     f"`{s.active}`"])
    return rows


def families(cfg) -> list[dict]:
    """What each scheme IS, where it declares it (ADR-109, #279).

    Separate from the table above, which says where a family's files live and
    how a code looks. That answers *where*; this answers *what*, and a reader
    who does not already know what a `LIT` is needs the second one first.
    Only schemes that say are listed. A project that declares none gets an
    empty list, and the template leaves the section out, heading and all.
    That a scheme says nothing is a finding, not part of the description:
    the lint reports it as `undescribed-schemes`, with the remedy."""
    return [{"prefix": p, "title": s.title, "blurb": s.blurb}
            for p, s in cfg.schemes.items() if s.title or s.blurb]


def contracts(cfg) -> list[dict]:
    """What each scheme demands of an entry beyond the standard fields —
    the compiled contract `luria lint` checks (#141), one line per
    obligation, each naming the key that declared it. Rendered from the
    same description a finding cites, so the page and the lint cannot
    disagree about what a scheme asks for."""
    out = []
    for prefix, scheme in cfg.schemes.items():
        lines = contract_mod.describe(contract_mod.for_scheme(scheme))
        if lines:
            out.append({"prefix": prefix, "lines": lines})
    return out


def journals_rows(cfg) -> list[list[str]]:
    """Dated entries that persist. Unlike a fragment directory, nothing
    consumes them — the books are a view over sources that stay."""
    return [[f"`{j.name}`",
             f"{_rel(cfg, j.dir, dir=True)} `yyyy/mm/dd/hhmmss.md`",
             _rel(cfg, j.output, dir=True), j.granularity, j.title]
            for j in cfg.journals.values()]


def fragments_rows(cfg) -> list[list[str]]:
    """Many small files assembled into one document, and then consumed —
    which is what makes a fragment directory conflict-free per contribution
    and a journal permanent."""
    return [[_rel(cfg, cfg.root / d, dir=True), _rel(cfg, cfg.root / f.target),
             f.style] for d, f in cfg.fragments.items()]


def remotes_rows(cfg) -> list[list[str]]:
    """Another project's codes, citable from this one by a prefixed code."""
    rows = []
    for prefix, r in cfg.remotes.items():
        example = next(iter(r.schemes), "ADR")
        rows.append([f"`{prefix}-{example}-001`", r.name or r.repo or "—",
                     r.repo or "—", r.ref or "—"])
    return rows


def filing_rows(cfg) -> list[list[str]]:
    """What to type. Derived from `new.kinds()`, the same mapping the CLI
    dispatches on, so the command in this table is the command that works."""
    from .new import default_kind, kinds
    default = default_kind()
    rows = []
    for kind, (sort, target) in sorted(kinds().items()):
        if sort == "scheme":
            what = f"a document in the `{target.prefix}` scheme, numbered for you"
        elif sort == "journal":
            what = f"a dated entry in the `{target.name}` journal"
        elif sort == "fragment":
            what = f"a fragment in `{target}/`"
        else:
            what = "a migration spec"
        cmd = f'`luria new --kind {kind} --title "…"`'
        if kind == default:
            cmd += ' — or just `luria new --title "…"`, the default kind'
        rows.append([cmd, what])
    return rows


def _flatten(prefix: str, value, depth: int) -> list[tuple[str, object]]:
    """`{"site": {"theme": {...}}}` as `site.theme`, and no deeper.

    `depth` stops at a settings table's own keys, which is where a *decision*
    lives. A theme is one choice with twenty-four colours in it; flattening all
    the way turns one changed setting into twenty-four rows and buries the
    other five."""
    if isinstance(value, dict) and depth > 0:
        out: list[tuple[str, object]] = []
        for k, v in value.items():
            out += _flatten(f"{prefix}.{k}" if prefix else k, v, depth - 1)
        return out
    return [(prefix, value)]


def _value(v) -> str:
    """A configured value as a reader would recognize it — a scalar as itself,
    a list spelled out, a nested table by the count that makes it one."""
    if isinstance(v, dict):
        return f"*{len(v)} key{'s' if len(v) != 1 else ''} set*" if v \
            else "*empty*"
    if isinstance(v, (list, tuple)):
        return ", ".join(f"`{x}`" for x in v) if v else "*empty*"
    if v == "":
        return "*empty*"
    return f"`{v}`"


#: Family tables describe themselves in the sections above; repeating their
#: keys here would be a third copy of the same fact.
FAMILIES = ("schemes", "fragments", "journals", "remotes")


def settings_rows(cfg) -> list[list[str]]:
    """The settings this project moved off Luria's defaults, and nothing else.

    A diff, not a dump: a reader looking at a full key table cannot tell which
    rows were decided and which merely happened. Family tables are excluded —
    they *are* the sections above, and are replaced whole rather than merged
    (ADR-047), so "differs from the default" is not a meaningful question to
    ask of one."""
    sentinel = object()
    defaults = dict(_flatten("", config_mod.DEFAULTS, 2))
    rows = []
    for key, value in _flatten("", cfg._raw, 2):
        if key.split(".")[0] in FAMILIES:
            continue
        was = defaults.get(key, sentinel)
        if value == was:
            continue
        rows.append([f"`{key}`", _value(value),
                     "*unset*" if was is sentinel else _value(was)])
    return rows


def context(cfg) -> dict:
    """Everything the template reads: facts from the loaded config, and no
    prose. The prose, the headings and the layout are the template's."""
    return {"schema": SCHEMA_URL,
            "schemes": schemes_rows(cfg),
            "families": families(cfg),
            "contracts": contracts(cfg),
            "journals": journals_rows(cfg),
            "fragments": fragments_rows(cfg),
            "remotes": remotes_rows(cfg),
            "filing": filing_rows(cfg),
            "settings": settings_rows(cfg)}


def render() -> str:
    """The page: `luria:record.md.j2` over `context`, in the sandbox every
    view renders in (ADR-130). Not linked: the page is made of example
    codes, and the codes its prose cites are luria's own."""
    from . import views
    return views._environment().get_template(TEMPLATE).render(
        context(current()))


def outputs(out_dir: Path | None = None) -> dict[Path, str]:
    """The page, keyed by where it lands — the unit `luria index` renders, so
    a stale page fails the same check as every other view."""
    cfg = current()
    path = cfg.record_doc if out_dir is None else out_dir / "record.md"
    return {path: render()}


def write(out_dir: Path | None = None) -> list[Path]:
    rendered = outputs(out_dir)
    for path, text in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        writes.write_text(path, text)
    return sorted(rendered)


if __name__ == "__main__":
    import fire
    fire.Fire(write)
