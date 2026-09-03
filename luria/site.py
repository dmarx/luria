"""Stage the record as an Obsidian/Quartz vault, ready to build (ADR-042).

    luria site --out build/site

writes `build/site/content/` — the record's markdown, every path preserved —
plus the `quartz.config.ts` and `quartz.layout.ts` derived from `luria.toml`.
Handing those to a pinned Quartz checkout produces the published site: the
decisions, the principles document, the devlog books and the reports, with
Quartz's graph and backlinks over the citations the record already carries.

Luria owns both generated files, and the layout is owned for a reason: Quartz
puts the graph in a sidebar that stacks *below the article* under 1200px, so
on most windows the one view the site exists for was the last thing on the
page (#71). Anything `stage` writes beside `content/` has to be copied by
`actions/site`, and a test holds that pair together.

Three rules do the whole job.

**Paths are preserved, so links are not rewritten.** Every relative target in
this record was spelled by `luria link --fix` for the directory the prose
lands in. Staging into the same tree shape means those targets keep resolving
and the site inherits the fixer's work whole, rather than a second link
resolver drifting from the first (DP-4).

**A source that renders into a view is not published; the view is.** That set
is derived, not listed: `Config.link_base(path)` already answers "which
directory do this file's links resolve against?", and a file whose answer is
not its own directory is a fragment, a journal entry or a document-scheme
source — prose written to be read *somewhere else*. Publishing it would both
duplicate the view and break every link in it.

**A link out of the published set goes to the repository.** The record cites
workflows, templates and the licence, which are real files and not pages. An
image is copied so it renders; anything else becomes a `source_url` link, and
`luria site` counts what it could not place rather than emitting a dead one
(DP-1).

The one thing added rather than copied: each scheme document gets a **record
line** under its title — status, date, issue, the decisions named in
`influenced_by:`, and its typed edges both ways (`luria/edges.py`): what it
supersedes, what it influenced, what a declared reference field names and
which documents name it. Those facts live in frontmatter, which a site
renders as nothing at all, and the edges are precisely the lineage a
citation graph exists to show — Quartz's own backlinks say only that a page
was mentioned. The line is composed with wikilinks and expanded by the same
resolver the record uses everywhere else.
"""

from __future__ import annotations

import fnmatch
import posixpath
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import doc_refs, edges
from .adr_index import parse_frontmatter
from .config import Site, current

# Skipped wherever they turn up: a scaffold seed whose references are
# illustrative, and directories no record keeps prose in.
ALWAYS_EXCLUDED = ("_template.md",)
EXCLUDED_DIRS = (".git", ".venv", "venv", "node_modules", "__pycache__",
                 ".pytest_cache", ".mypy_cache")

# Copied into the vault rather than linked out to the repository: these render
# in place, and a link is not a picture.
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif")

# Characters no publishable repository path contains. The backstop for the one
# quoting form `doc_refs.code_spans` does not model — a four-space indented
# block — where a regex like `[.:](\\d{4,5})` reads as a link target. Reading
# a specimen wrongly would only miscount; *rewriting* one would corrupt the
# example the prose is teaching, so the site needs the guard the lint doesn't.
NOT_A_PATH = set("\\{}*|<>\"")

# A link or image with a relative target — the same shape the index rebases,
# and for the same reason: those are the only ones a move disturbs.
#
# The raw-HTML forms are not hypothetical. Markdown isn't parsed inside an
# HTML block, so `<a href>` is what the fixer writes there (ADR-005) — and a
# README that centres its logo in a `<div align="center">` reaches its image
# by `<img src>`, which is how this repo's own banner went missing from the
# site's front page (#70).
RELATIVE_TARGET_RE = re.compile(
    r"""(?:(?<=\]\()|(?<=<a href=")|(?<=<a href=')"""
    r"""|(?<=<img src=")|(?<=<img src='))"""
    r"""(?![#/]|[A-Za-z][A-Za-z0-9+.-]*:)([^)'"\s]+)""")

# Quartz's own palette, lifted out of the config template so a project can
# override any of it by name. The default is the generator's look, not this
# project's: a package that shipped its own brand as everyone's default would
# be handing out a costume nobody asked for.
THEME_DEFAULTS: dict[str, dict[str, str]] = {
    "light": {
        "light": "#faf8f8", "lightgray": "#e5e5e5", "gray": "#b8b8b8",
        "darkgray": "#4e4e4e", "dark": "#2b2b2b", "secondary": "#284b63",
        "tertiary": "#84a59d", "highlight": "rgba(143, 159, 169, 0.15)",
        "textHighlight": "#fff23688",
    },
    "dark": {
        "light": "#161618", "lightgray": "#393639", "gray": "#646464",
        "darkgray": "#d4d4d4", "dark": "#ebebec", "secondary": "#7b97aa",
        "tertiary": "#84a59d", "highlight": "rgba(143, 159, 169, 0.15)",
        "textHighlight": "#b3aa0288",
    },
}

# The custom property this project's brand kit exposes for re-inking a logo.
# An SVG that declares it is re-inked per theme; one that doesn't is used as
# it stands, so the accommodation costs nothing to a project that never heard
# of it.
INK_VAR = "--luria-ink"

QUARTZ_CONFIG = """\
// GENERATED by `luria site` from luria.toml — edit that, not this.
//
// Two settings are load-bearing and the rest is presentation:
//
//   markdownLinkResolution: "relative" — the record's links are ordinary
//   relative paths, spelled for the directory each page sits in. Quartz's
//   default ("shortest") re-resolves them by basename and silently lands a
//   `docs/decisions/README.md` link on the wrong page.
//
//   CreatedModifiedDate without the git provider — the vault is a staged copy
//   outside any repository, so a git lookup finds nothing and warns once per
//   file. Frontmatter first (`date:`, `created:`), filesystem as the floor.
import {{ QuartzConfig }} from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

const config: QuartzConfig = {{
  configuration: {{
    pageTitle: "{title}",
    pageTitleSuffix: "",
    enableSPA: true,
    enablePopovers: true,
    analytics: null,
    locale: "en-US",
    baseUrl: "{base_url}",
    ignorePatterns: [],
    defaultDateType: "created",
    theme: {{
      fontOrigin: "googleFonts",
      cdnCaching: true,
      typography: {{
        header: "Schibsted Grotesk",
        body: "Source Sans Pro",
        code: "IBM Plex Mono",
      }},
      colors: {{
{colors}
      }},
    }},
  }},
  plugins: {{
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({{ priority: ["frontmatter", "filesystem"] }}),
      Plugin.SyntaxHighlighting({{
        theme: {{ light: "github-light", dark: "github-dark" }},
        keepBackground: false,
      }}),
      Plugin.ObsidianFlavoredMarkdown({{ enableInHtmlEmbed: false }}),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({{ markdownLinkResolution: "relative" }}),
      Plugin.Description(),
      Plugin.Latex({{ renderEngine: "katex" }}),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({{ enableSiteMap: true, enableRSS: true }}),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.Favicon(),
      Plugin.NotFoundPage(),
      Plugin.CustomOgImages(),
    ],
  }},
}}

export default config
"""


QUARTZ_LAYOUT = """\
// GENERATED by `luria site`. Quartz's default layout, with one change.
//
// The graph moves out of the right sidebar and into the content column,
// directly under the title (#71). Quartz's sidebars stack *below* the article
// under 1200px — so on any window narrower than that, which is most of them,
// the graph a record publishes itself for was the last thing on the page. The
// obvious remedies both miss: `MobileOnly` switches at 800px, leaving the
// 800–1200px band broken, and reordering the grid in CSS couples this file to
// Quartz's internal grid areas, which is what a version bump breaks.
//
// The cost is real and accepted: on a wide screen the graph now scrolls away
// with the content instead of sitting in the sticky rail. A view that is
// always visible to some readers and never visible to others is the worse
// trade.
import {{ PageLayout, SharedLayout }} from "./quartz/cfg"
import * as Component from "./quartz/components"

export const sharedPageComponents: SharedLayout = {{
  head: Component.Head(),
  header: [],
  afterBody: [],
  footer: Component.Footer({{
    links: {{
      Repository: "{repo_url}",
      Quartz: "https://quartz.jzhao.xyz/",
    }},
  }}),
}}

export const defaultContentPageLayout: PageLayout = {{
  beforeBody: [
    Component.ConditionalRender({{
      component: Component.Breadcrumbs(),
      condition: (page) => page.fileData.slug !== "index",
    }}),
    Component.ArticleTitle(),
    Component.ContentMeta(),
    Component.TagList(),
    // Retuned for the content column: Quartz's defaults are set for a 320px
    // rail, and in a column twice that width they leave the neighbourhood
    // huddled in the middle. Depth stays at 1 — depth 2 on a record this
    // densely cross-cited renders a hairball with the current page lost in
    // it, which is a picture of nothing.
    Component.Graph({{
      localGraph: {{
        depth: 1,
        scale: 1.05,
        repelForce: 1.4,
        centerForce: 0.2,
        linkDistance: 70,
        fontSize: 0.75,
        focusOnHover: true,
      }},
    }}),
  ],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Flex({{
      components: [
        {{ Component: Component.Search(), grow: true }},
        {{ Component: Component.Darkmode() }},
        {{ Component: Component.ReaderMode() }},
      ],
    }}),
    Component.Explorer(),
  ],
  right: [
    Component.DesktopOnly(Component.TableOfContents()),
    Component.Backlinks(),
  ],
}}

export const defaultListPageLayout: PageLayout = {{
  beforeBody: [
    Component.Breadcrumbs(),
    Component.ArticleTitle(),
    Component.ContentMeta(),
  ],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Flex({{
      components: [
        {{ Component: Component.Search(), grow: true }},
        {{ Component: Component.Darkmode() }},
      ],
    }}),
    Component.Explorer(),
  ],
  right: [],
}}
"""


CUSTOM_SCSS = """\
// GENERATED by `luria site` from luria.toml — edit that, not this.
@use "./base.scss";
"""

# The site title, replaced by the project's own lockup. Image replacement
# rather than an `<img>`: the title is a link Quartz renders, and swapping its
# background is the one way to brand it without owning the component. The
# indent keeps the accessible name a screen reader announces.
LOGO_SCSS = """
.page-title a {{
  display: block;
  width: 100%;
  max-width: {width};
  aspect-ratio: {w} / {h};
  background: url("{light}") no-repeat left center;
  background-size: contain;
  text-indent: -9999px;
  overflow: hidden;
  white-space: nowrap;
}}

// Two baked variants rather than one self-inverting file, because whether
// artwork can invert itself is a *browser* question. Quartz declares
// `color-scheme` per theme, and a browser that propagates that into an
// embedded SVG resolves the artwork's own `prefers-color-scheme` against the
// site's toggle — measured, and it is what Chromium does. A browser that
// doesn't resolves it against the operating system, and a reader whose OS
// disagrees with the toggle gets dark ink on a dark page. Baking the variants
// makes the answer the same everywhere, and is the only way to theme a logo
// that has no media query of its own.
:root[saved-theme="dark"] .page-title a {{
  background-image: url("{dark}");
}}
"""


@dataclass
class Report:
    """What one staging run did, in the shape the CLI prints and a test
    asserts on. Counted rather than merely logged: a link that could not be
    placed is the number worth watching, and a silent staging run would hide
    exactly the reference the site is meant to make followable (DP-1)."""
    pages: int = 0
    assets: int = 0
    to_source: int = 0                  # links redirected at the repository
    unplaced: list[str] = field(default_factory=list)
    lineage: int = 0                    # record lines added to scheme docs

    def lines(self) -> list[str]:
        out = [f"{self.pages} pages, {self.assets} assets staged",
               f"{self.lineage} record lines added",
               f"{self.to_source} links redirected to the repository"]
        if self.unplaced:
            shown = sorted(self.unplaced)
            out.append(f"{len(shown)} reference(s) the site cannot place:")
            out += [f"  {line}" for line in shown[:20]]
            if len(shown) > 20:
                out.append(f"  …and {len(shown) - 20} more")
        return out


def colors(site: Site) -> str:
    """Quartz's `colors:` block, with `[luria.site.theme]` merged over the
    generator's defaults.

    An unknown colour name is refused by name rather than dropped: a palette
    key silently ignored is a project wondering why its brand didn't take
    (DP-1)."""
    out = []
    for mode, key in (("light", "lightMode"), ("dark", "darkMode")):
        override = site.theme.get(mode, {}) or {}
        unknown = sorted(set(override) - set(THEME_DEFAULTS[mode]))
        if unknown:
            raise SystemExit(
                f"luria site: [luria.site.theme.{mode}] has no colour named "
                f"{', '.join(unknown)} — Quartz knows "
                f"{', '.join(THEME_DEFAULTS[mode])}")
        merged = {**THEME_DEFAULTS[mode], **override}
        body = "".join(f'          {k}: "{v}",\n' for k, v in merged.items())
        out.append(f"        {key}: {{\n{body}        }},")
    return "\n".join(out)


def _reinked(svg: str, ink: str) -> str:
    """The artwork, forced to one ink colour.

    Only for a logo that declares `--luria-ink`. An inline `style` on the root
    element outranks the stylesheet rules inside the file, including the
    `prefers-color-scheme` one — which is the point: the site's theme is a
    toggle, and the operating system's preference is not it."""
    if INK_VAR not in svg:
        return svg
    return re.sub(r"<svg\b", f'<svg style="{INK_VAR}:{ink}"', svg, count=1)


def _svg_size(svg: str) -> tuple[float, float]:
    """The artwork's aspect, from its viewBox — 4:1 if it hasn't got one, so
    a logo without one still renders rather than collapsing to nothing."""
    m = re.search(r'viewBox="([\d.\s-]+)"', svg)
    if m:
        parts = [float(x) for x in m.group(1).split()]
        if len(parts) == 4 and parts[2] and parts[3]:
            return parts[2], parts[3]
    return 4.0, 1.0


def _excluded(rel: str, site: Site) -> bool:
    parts = Path(rel).parts
    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    if Path(rel).name in ALWAYS_EXCLUDED:
        return True
    return any(fnmatch.fnmatch(rel, pattern) for pattern in site.exclude)


def publishable(cfg=None, skip: Path | None = None) -> list[Path]:
    """Every markdown file the site publishes, in a stable order.

    The derived rule is the second clause: a file whose links resolve against
    some *other* directory is a source rendered into a view, and the view is
    already here. Excluding it is not tidiness — its links are spelled for
    where its prose lands, so publishing it in place would break every one.

    `skip` is the staging directory when it sits inside the project — the
    default `build/site` does. Without it the second run publishes the first
    run's output, and the site grows a copy of itself per build."""
    cfg = cfg or current()
    out = []
    for path in sorted(cfg.root.rglob("*.md")):
        if skip and skip in path.parents:
            continue
        rel = path.relative_to(cfg.root).as_posix()
        if _excluded(rel, cfg.site):
            continue
        if cfg.link_base(path) != path.parent:
            continue
        out.append(path)
    return out


def destination(path: Path, cfg) -> Path:
    """Where `path` lands in the vault, relative to `content/`.

    Only the root README moves: Quartz serves `index.md` as the landing page,
    and a record whose front door is its README should not need a second copy
    of it to have one."""
    rel = path.relative_to(cfg.root)
    return Path("index.md") if rel.as_posix() == "README.md" else rel


def _alias(path: Path, cfg) -> str | None:
    """The bare code a scheme document should also answer to — `/ADR-025`.

    This is the one place Obsidian's convention and Luria's meet. A wikilink
    here is a *code*, resolved through the scheme config; in a vault it is a
    *filename*, resolved by basename. For a file-per-code scheme those agree,
    and an alias makes the short URL agree too."""
    for scheme in cfg.schemes.values():
        if scheme.render != "index" or path.parent != scheme.dir:
            continue
        number = scheme.number_of(path)
        if number is not None:
            return scheme.code(number)
    return None


# How an inbound edge reads on the page it lands on. A declared reference
# field has no built-in inverse, so it is named for the field.
_INBOUND = {edges.SUPERSEDED_BY: "Supersedes",
            edges.INFLUENCED_BY: "Influenced"}
_INBOUND_ORDER = (edges.SUPERSEDED_BY, edges.INFLUENCED_BY)


def _edge_bits(outbound, inbound) -> list[str]:
    """The typed edges as record-line fragments, wikilinks and all.

    Supersession and influence already read from the page's own frontmatter
    (the status note, `influenced_by:`), so outbound only adds the declared
    reference fields — the one direction the site otherwise loses, since
    frontmatter renders as nothing."""
    bits = []
    out: dict[str, list[str]] = {}
    for edge in outbound:
        if edge.relation not in _INBOUND:
            out.setdefault(edge.relation, []).append(edge.target)
    for relation, targets in out.items():
        label = relation.replace("_", " ").capitalize()
        bits.append(f"**{label}** " + " · ".join(f"[[{t}]]" for t in targets))
    grouped: dict[str, list[str]] = {}
    for edge in inbound:
        grouped.setdefault(edge.relation, []).append(edge.source)

    def order(relation: str) -> tuple[int, str]:
        built_in = relation in _INBOUND_ORDER
        return (_INBOUND_ORDER.index(relation) if built_in
                else len(_INBOUND_ORDER), relation)

    for relation in sorted(grouped, key=order):
        label = _INBOUND.get(relation) or f"Cited as `{relation}` by"
        codes = " · ".join(f"[[{c}]]" for c in sorted(set(grouped[relation])))
        bits.append(f"**{label}** {codes}")
    return bits


def _vocabulary_bits(meta: dict, source: Path) -> list[str]:
    """A vocabulary field's *written* values, each linked to its page. The
    default is deliberately not shown: a reader is never shown a field the
    file does not have (ADR-tmpcso13); the record page says what absence
    means."""
    cfg = current()
    scheme = next((s for s in cfg.schemes.values()
                   if s.render == "index" and source.parent == s.dir), None)
    if scheme is None:
        return []
    bits = []
    for vocab in scheme.vocabularies:
        raw = meta.get(vocab.field)
        values = raw if isinstance(raw, list) else (
            [] if raw in (None, "") else [raw])
        if not values:
            continue
        links = " · ".join(
            f"[{v}]({posixpath.relpath((scheme.vocab_dir(vocab.name) / f'{v}.md').as_posix(), source.parent.as_posix())})"
            for v in values)
        bits.append(f"**{vocab.field.replace('_', ' ').capitalize()}** {links}")
    return bits


def record_line(meta: dict, source: Path, outbound=(), inbound=()) -> str:
    """The frontmatter facts, rendered where a reader (and a graph) can see
    them: status, when it was filed, the issue, what influenced it, and the
    typed edges in and out of it.

    Composed with wikilinks and handed to the resolver rather than spelled
    here — the fixer owns every target in this record, and a second speller
    would be the drift DP-4 names."""
    bits = []
    if status := str(meta.get("status", "")).strip():
        bits.append(f"**Status** {status}")
    # Shown only when it isn't 1, the same rule the index follows (ADR-016).
    # A version that isn't a number is somebody's mistake, not this function's
    # to interpret — it is shown as written and the lint says so.
    if (version := meta.get("version")) and str(version).strip() != "1":
        bits.append(f"**Version** {version}")
    if date := str(meta.get("date", "")).strip():
        bits.append(f"**Filed** {date}")
    # `issue: '#21, #23'` is a real shape in this record, so the separator is
    # read out of the field rather than assumed to be a space.
    if issues := re.findall(r"#\d+", str(meta.get("issue", ""))):
        bits.append("**Issue** "
                    + " · ".join(f"[[{issue}]]" for issue in issues))
    influenced = [str(c).strip() for c in (meta.get("influenced_by") or [])]
    if influenced:
        codes = " · ".join(f"[[{code}]]" for code in influenced if code)
        bits.append(f"**Influenced by** {codes}")
    bits += _vocabulary_bits(meta, source)
    bits += _edge_bits(outbound, inbound)
    if not bits:
        return ""
    expanded, _ = doc_refs.expand_wikilinks("> " + " · ".join(bits), source)
    return expanded


def _insert_after_title(body: str, line: str) -> str:
    """Put the record line under the document's `# ` heading, or at the top
    when there isn't one. A superseded decision announces itself above the
    fold or not at all."""
    if not line:
        return body
    for match in re.finditer(r"^# .+$", body, re.MULTILINE):
        cut = match.end()
        return body[:cut] + "\n\n" + line + body[cut:]
    return line + "\n\n" + body


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """(raw YAML, body). `None` for the YAML when there is no frontmatter —
    a generated view has none, and is copied through untouched."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 3)
    if end == -1:
        return None, text
    return text[4:end + 1], text[end + 5:]


def _with_alias(front: str, alias: str | None) -> str:
    if not alias:
        return front
    return front.rstrip("\n") + f'\naliases:\n- "{alias}"\n'


def landing_page(text: str, cfg) -> str:
    """Give the README the name and the second address it needs as `index.md`.

    Two things break in the rename. A site derives a page's title from its
    frontmatter or its first heading, and a README that opens with a centred
    logo has neither — so the front page was titled `index`, after the file we
    renamed it to. And anything still pointing at `README.md` now points at a
    page that isn't there; the alias is what keeps that link answering."""
    yaml_text, body = split_frontmatter(text)
    added = f'title: "{cfg.site.title}"\naliases:\n- "README"\n'
    if yaml_text is None:
        return "---\n" + added + "---\n\n" + text
    # A README that already names itself keeps its own title.
    if re.search(r"^title:", yaml_text, re.MULTILINE):
        added = 'aliases:\n- "README"\n'
    return "---\n" + yaml_text.rstrip("\n") + "\n" + added + "---\n" + body


def _retarget(text: str, source: Path, cfg, published: set[Path],
              staged_assets: dict[Path, Path], report: Report) -> str:
    """Send every relative link that leaves the published set somewhere real.

    An image is staged so it renders; anything else — a workflow, the scaffold,
    the licence — becomes a link at the repository, because the site is a view
    of the record and those files are the record's subject, not its pages."""
    site = cfg.site
    rel_source = cfg.rel(source)
    # Code is quoted, not asserted — the same rule the reference lint runs on
    # (ADR-008). A path inside a fence is a specimen, and "re-pointing" it
    # would rewrite the example the prose is teaching.
    quoted = doc_refs.code_spans(text)

    def fix(match: re.Match) -> str:
        target = match.group(1)
        if any(a <= match.start() < b for a, b in quoted):
            return target
        if NOT_A_PATH & set(target):
            return target
        path_part, sep, fragment = target.partition("#")
        if not path_part:
            return target
        try:
            resolved = (source.parent / path_part).resolve()
            inside = resolved.relative_to(cfg.root.resolve())
        except (ValueError, OSError):
            return target
        absolute = cfg.root / inside
        if absolute in published or absolute.is_dir():
            return target
        if not absolute.exists():
            report.unplaced.append(f"{rel_source} → {target}")
            return target
        if absolute.suffix.lower() in IMAGE_SUFFIXES:
            staged_assets[absolute] = inside
            return target
        if not site.source_url:
            report.unplaced.append(f"{rel_source} → {target}")
            return target
        report.to_source += 1
        return f"{site.source_url.rstrip('/')}/{inside.as_posix()}{sep}{fragment}"

    return RELATIVE_TARGET_RE.sub(fix, text)


def brand(out: Path, cfg, report: Report) -> str:
    """Stage the project's artwork and return the stylesheet that uses it.

    The icon is copied verbatim and rasterized by `actions/site` with the
    `sharp` the generator already depends on — so a project points at the
    vector master it maintains and nothing derived from it is ever committed
    to drift (DP-3).

    The logo is written twice, once per theme, because a stylesheet can switch
    on Quartz's toggle and an SVG's own media query cannot. Missing artwork is
    named rather than skipped in silence (DP-1)."""
    site = cfg.site
    static = out / "static"
    static.mkdir(parents=True, exist_ok=True)

    for label, source in (("icon", site.icon), ("logo", site.logo),
                          ("logo_dark", site.logo_dark)):
        if source is not None and not source.exists():
            report.unplaced.append(f"[luria.site] {label} → {cfg.rel(source)} "
                                   f"(no such file)")

    if site.icon is not None and site.icon.exists():
        shutil.copyfile(site.icon, static / f"icon{site.icon.suffix.lower()}")
        report.assets += 1

    if site.logo is None or not site.logo.exists():
        return CUSTOM_SCSS

    light_svg = site.logo.read_text(encoding="utf-8")
    dark_source = site.logo_dark if (site.logo_dark
                                     and site.logo_dark.exists()) else None
    dark_svg = (dark_source.read_text(encoding="utf-8") if dark_source
                else light_svg)
    palette = {mode: {**THEME_DEFAULTS[mode], **(site.theme.get(mode) or {})}
               for mode in ("light", "dark")}
    # Re-ink to the strongest text colour of each mode, so the lockup and the
    # headings it sits above are the same weight of black.
    light_svg = _reinked(light_svg, palette["light"]["dark"])
    if dark_source is None:
        dark_svg = _reinked(dark_svg, palette["dark"]["dark"])

    (static / "logo-light.svg").write_text(light_svg, encoding="utf-8")
    (static / "logo-dark.svg").write_text(dark_svg, encoding="utf-8")
    report.assets += 2

    w, h = _svg_size(light_svg)
    # A tall logo would eat the sidebar, so the cap is on height, expressed as
    # the width that produces it.
    width = f"{min(15.0, 3.6 * w / h):.1f}rem"
    return CUSTOM_SCSS + LOGO_SCSS.format(
        width=width, w=w, h=h,
        light="static/logo-light.svg", dark="static/logo-dark.svg")


def stage(out: Path, cfg=None) -> Report:
    """Write the vault and its config under `out`. Idempotent: the content
    directory is rebuilt from scratch, so a rename in the record cannot leave
    a stale page behind to be served forever."""
    cfg = cfg or current()
    out = out.resolve()
    content = out / "content"
    if content.exists():
        shutil.rmtree(content)
    content.mkdir(parents=True)

    pages = publishable(cfg, skip=out)
    published = set(pages)
    report, assets = Report(), {}
    # Read once for the whole record: a page's backlinks are somebody else's
    # frontmatter.
    typed = edges.graph()

    for path in pages:
        text = path.read_text(encoding="utf-8")
        yaml_text, body = split_frontmatter(text)
        if yaml_text is not None:
            meta = parse_frontmatter(text)[0]
            code = edges.code_of(path)
            line = record_line(
                meta, path,
                outbound=typed.outbound(code) if code else (),
                inbound=typed.inbound(code) if code else ())
            if line:
                body = _insert_after_title(body, line)
                report.lineage += 1
                # A wikilink the resolver could not expand survives as literal
                # brackets. Visible, but visible is not the same as reported —
                # the frontmatter it came from is data, which the prose scanner
                # never reads, so this is the only place it can be counted.
                if "[[" in line:
                    report.unplaced.append(
                        f"{cfg.rel(path)} → unresolved in frontmatter: "
                        + " ".join(re.findall(r"\[\[[^\]]+\]\]", line)))
            # The YAML itself is carried over verbatim — only the alias is
            # added — so a re-serialization can never quietly reorder or
            # requote a field the record is the source of truth for.
            text = ("---\n" + _with_alias(yaml_text, _alias(path, cfg))
                    + "---\n" + body)
        dest_rel = destination(path, cfg)
        if dest_rel.as_posix() == "index.md":
            text = landing_page(text, cfg)
        text = _retarget(text, path, cfg, published, assets, report)
        dest = content / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        report.pages += 1

    for absolute, rel in assets.items():
        dest = content / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(absolute, dest)
        report.assets += 1

    (out / "quartz.config.ts").write_text(
        QUARTZ_CONFIG.format(title=cfg.site.title,
                             base_url=cfg.site.base_url,
                             colors=colors(cfg.site)),
        encoding="utf-8")
    (out / "custom.scss").write_text(brand(out, cfg, report), encoding="utf-8")
    # The footer points home. `source_url` is a blob base; two segments up is
    # the repository, which is the only link a reader of the site wants there.
    repo_url = re.sub(r"/blob/[^/]+/?$", "", cfg.site.source_url)
    (out / "quartz.layout.ts").write_text(
        QUARTZ_LAYOUT.format(repo_url=repo_url or cfg.site.source_url),
        encoding="utf-8")
    return report


def run(out: str = "build/site") -> None:
    """Stage the record as a Quartz vault — `content/` plus `quartz.config.ts`
    — under OUT, ready for `npx quartz build`."""
    cfg = current()
    report = stage(Path(out) if Path(out).is_absolute() else cfg.root / out,
                   cfg)
    print(f"staged {out}/content")
    for line in report.lines():
        print(f"  {line}")
    if not cfg.site.base_url:
        print("  no site.base_url and none derivable from issue_url — "
              "the site will build with relative URLs only")


if __name__ == "__main__":
    sys.exit(run())
