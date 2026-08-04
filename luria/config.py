"""Where a project keeps its record, and what its references look like.

Everything else in Luria is generic; this module is the one place that knows a
particular project. It reads `luria.toml` from the project root:

    [luria]
    issue_url = "https://github.com/owner/repo/issues/{n}"

    [luria.paths]
    docs = "docs"
    decisions = "docs/decisions"
    design_principles = "docs/design-principles.md"

    [luria.fragments]
    "changelog.d" = "CHANGELOG.md"      # collected into…

    [luria.journals.devlog]
    dir = "devlog.d"                    # …whereas a journal's entries persist
    output = "docs/devlog"

    [luria.code]
    globs = ["src/**/*.py", "*.md"]

    [luria.schemes.ADR]
    dir = "docs/decisions"
    active = "Active"

Every key has a default, so a project with the conventional layout needs a
`luria.toml` containing only `issue_url` — and Luria still runs without one, on
defaults alone, which is what makes `luria init` able to bootstrap.

The alternative was arguments threaded through every entry point. That works
until the second caller forgets one and the linter and the fixer disagree about
which files they cover — the exact class of bug ADR-002 exists to prevent. One
config object, resolved once from disk.
"""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

CONFIG_NAME = "luria.toml"

DEFAULTS: dict = {
    "issue_url": "",
    "paths": {
        "docs": "docs",
        "decisions": "docs/decisions",
        "design_principles": "docs/design-principles.md",
        "reports": "build/doc-reports",
    },
    "fragments": {
        "changelog.d": "CHANGELOG.md",
    },
    "code": {
        "globs": [],
        # Dated records: true about the day they were written, forever. Scanning
        # them for stale references produces permanent, unactionable noise. A
        # journal is one too, and is covered without being listed here — see
        # `Config.is_historical`.
        "historical": ["CHANGELOG.md"],
    },
    "schemes": {
        "ADR": {"dir": "docs/decisions", "active": "Active", "render": "index"},
    },
    # Other projects whose records this one cites, keyed by a short prefix. A
    # reference then composes: `LU-ADR-013` is that remote's decision 13
    # (ADR-016).
    "remotes": {},
    # Dated entries that persist and render into books (ADR-020). Unlike a
    # scheme, a journal entry has no number — its identity is when it was
    # written — and unlike a fragment directory, its sources are never consumed.
    "journals": {
        "devlog": {
            "dir": "devlog.d",
            "output": "docs/devlog",
            "granularity": "month",
            "title": "Development log",
        },
    },
    "stale_days": 90,
}


def find_root(start: Path | None = None) -> Path:
    """The project root: nearest ancestor with a `luria.toml`, else with a
    `.git`, else the starting directory. Env var `LURIA_ROOT` wins, which is
    what lets the tests run against fixture trees."""
    if env := os.environ.get("LURIA_ROOT"):
        return Path(env).resolve()
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONFIG_NAME).exists():
            return candidate
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    return here


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


@dataclass(frozen=True)
class Scheme:
    """A family of referable documents — `ADR-012`, `RFC-7`, `SPEC-3`.

    Luria ships with one, and knowing that one is not built in is the point:
    the annotation vocabulary says `inactive-ok`, not `adr-ok`, and a code
    carries its prefix, so a second scheme is an entry here (ADR-006)."""
    prefix: str
    dir: Path
    active: str = "Active"
    # How this scheme's generated view is built. "index" is a table of links
    # plus per-tag pages — right when the documents are browsed and read one at
    # a time. "document" concatenates the bodies into one page — right when the
    # set is read as a whole, which is what a principles doc is (ADR-012).
    render: str = "index"
    output: Path | None = None

    @property
    def pattern(self):
        return re.compile(rf"\b{self.prefix}[- ](?P<num>\d{{1,4}})\b")

    def code(self, number: str | int) -> str:
        return f"{self.prefix}-{int(number):03d}"

    def filename(self, number: str | int) -> str:
        """`ADR-013.md` — the file is named for the code and nothing else.

        The title lives in the frontmatter, where a correction costs an edit
        rather than a rename plus every link that pointed at the old name
        (ADR-013)."""
        return f"{self.code(number)}.md"

    def number_of(self, path: Path) -> int | None:
        """The document number a filename carries, or None if it isn't one.

        Deliberately tolerant of a trailing slug: `adr-010-some-title.md` is
        what most projects arrive with, and refusing to read them would make
        adoption a rename-everything-first proposition. Luria *writes* the short
        form and *reads* both."""
        m = re.fullmatch(rf"{self.prefix}-0*(\d+)(?:-[^/]*)?\.md", path.name,
                         re.IGNORECASE)
        return int(m.group(1)) if m else None

    def documents(self) -> dict[int, Path]:
        """Number → path for every document in this scheme, ascending.

        The one place a scheme directory is read. Five copies of this glob had
        accumulated, each with its own regex — the drift DP-4 names, harmless
        only for as long as the filename shape never changed."""
        found: dict[int, Path] = {}
        for path in sorted(self.dir.glob("*.md")):
            number = self.number_of(path)
            if number is not None:
                found.setdefault(number, path)
        return dict(sorted(found.items()))


@dataclass(frozen=True)
class Remote:
    """Another project's record, cited from this one.

    A reference to it composes the remote's prefix with the foreign scheme's
    own code — `LU-ADR-013` — so the namespace is explicit at the point of use
    and nothing has to guess which project an unprefixed code meant (ADR-016).

        [luria.remotes.LU]
        name = "luria"
        repo = "dmarx/luria"             # GitHub owner/name
        ref  = "main"                    # branch or tag the links point at
        dir  = "docs/decisions"          # where its documents live
        url  = "https://…/{code}.md"     # optional: overrides construction

    Everything but `repo` (or `url`) has a default, because the defaults are
    Luria's own conventions — a remote that uses them needs one line."""
    prefix: str
    repo: str = ""
    ref: str = "main"
    dir: str = "docs/decisions"
    name: str = ""
    url: str = ""

    @property
    def label(self) -> str:
        return self.name or self.repo or self.prefix

    def base(self) -> str:
        """The directory its documents live in, as a URL."""
        return f"https://github.com/{self.repo}/blob/{self.ref}/{self.dir}".rstrip("/")

    def link(self, code: str, filename: str = "") -> str:
        """The URL for a foreign code, best available construction.

        Three rungs, strongest first: an explicit `url` template; a filename
        discovered from the remote (`luria remotes --refresh`), which is the
        only thing that can resolve a title-slug name; and the code-only
        convention (ADR-013), which is right whenever the remote follows it."""
        if self.url:
            return self.url.format(code=code, number=int(code.rsplit("-", 1)[1]),
                                   prefix=code.rsplit("-", 1)[0])
        if not self.repo:
            return ""
        return f"{self.base()}/{filename or code + '.md'}"


@dataclass(frozen=True)
class Journal:
    """Dated entries that persist, rendered into books (ADR-020).

        [luria.journals.devlog]
        dir         = "devlog.d"        # entries, partitioned yyyy/mm/dd/
        output      = "docs/devlog"     # a directory of books plus an index
        granularity = "month"           # year | month | day
        title       = "Development log"
        blurb       = "…"               # optional prose for the index

    The difference from a fragment directory is that nothing is consumed: an
    entry was true when written and stays true, so the view is *generated* from
    sources that persist rather than collected from sources that are deleted."""
    name: str
    dir: Path
    output: Path
    granularity: str = "month"
    title: str = "Journal"
    blurb: str = ""
    _root: Path = Path(".")

    @property
    def rel_dir(self) -> str:
        try:
            return str(self.dir.relative_to(self._root))
        except ValueError:
            return self.dir.name


@dataclass(frozen=True)
class Config:
    root: Path
    issue_url: str
    docs: Path
    decisions: Path
    design_principles: Path
    reports: Path
    fragments: dict[str, Path]          # fragment dir name → assembled file
    code_globs: tuple[str, ...]
    historical: frozenset[Path]
    schemes: dict[str, Scheme]
    remotes: dict[str, Remote]
    journals: dict[str, Journal]
    stale_days: int
    _raw: dict = field(default_factory=dict, repr=False)

    @property
    def index(self) -> Path:
        return self.decisions / "README.md"

    @property
    def stub(self) -> Path:
        return self.decisions / "README.stub"

    @property
    def tags_yaml(self) -> Path:
        return self.decisions / "tags.yaml"

    @property
    def tag_dir(self) -> Path:
        return self.decisions / "tags"

    @property
    def remotes_lock(self) -> Path:
        """Discovered code→filename maps for the remotes, checked in.

        A lockfile rather than a live lookup: CI and an offline checkout have
        to resolve a foreign reference the same way a laptop with network does,
        and a private remote can only be read from a local clone anyway."""
        return self.root / "remotes.lock.json"

    def is_generated(self, path: Path) -> bool:
        """A view the generator owns. Rewriting one is pointless — the next
        build undoes it — so the reference fixer skips them."""
        if path == self.index or path.parent == self.tag_dir:
            return True
        if any(path.parent == j.output for j in self.journals.values()):
            return True
        return any(s.output == path for s in self.schemes.values())

    def is_historical(self, path: Path) -> bool:
        """A dated record: true about the day it was written, and never
        updated to stay true. Scanning one for stale references produces
        permanent, unactionable rows, so the status report skips it.

        Three shapes qualify: a file listed in `[luria.code] historical`, an
        uncollected fragment (it is about to *become* one), and anything in a
        journal — its entries and the books they render into alike. The last
        one is why this is a method rather than the set-membership test it used
        to be: a journal's entries are nested, so `path.parent` is not the
        journal directory."""
        if path in self.historical:
            return True
        if path.parent in {self.root / d for d in self.fragments}:
            return True
        return any(j.dir in path.parents or j.output in path.parents
                   for j in self.journals.values())

    def link_base(self, path: Path) -> Path:
        """The directory a link written in `path` resolves against.

        Not always `path.parent`. A fragment is *assembled into* a file that
        lives somewhere else, so a link relative to the fragment's own directory
        breaks the moment it is collected (ADR-005). Two kinds of fragment
        qualify — a changelog/devlog fragment, and a document-rendered scheme's
        source, which is the same relationship wearing a different name."""
        target = self.fragments.get(path.parent.name)
        if target:
            return (self.root / target).parent
        for scheme in self.schemes.values():
            if scheme.render == "document" and scheme.output \
                    and path.parent == scheme.dir:
                return scheme.output.parent
        for journal in self.journals.values():
            if journal.dir in path.parents:
                return journal.output
        return path.parent

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)


def load(root: Path | None = None) -> Config:
    root = root or find_root()
    raw = DEFAULTS
    config_file = root / CONFIG_NAME
    if config_file.exists():
        parsed = tomllib.loads(config_file.read_text())
        raw = _merge(DEFAULTS, parsed.get("luria", parsed))

    paths = raw["paths"]
    return Config(
        root=root,
        issue_url=raw.get("issue_url", ""),
        docs=root / paths["docs"],
        decisions=root / paths["decisions"],
        design_principles=root / paths["design_principles"],
        reports=root / paths["reports"],
        fragments={k: Path(v) for k, v in raw["fragments"].items()},
        code_globs=tuple(raw["code"]["globs"]),
        historical=frozenset(root / p for p in raw["code"]["historical"]),
        schemes={
            prefix: Scheme(
                prefix, root / spec["dir"], spec.get("active", "Active"),
                spec.get("render", "index"),
                root / spec["output"] if spec.get("output") else None,
            )
            for prefix, spec in raw["schemes"].items()
        },
        remotes={
            prefix.upper(): Remote(
                prefix.upper(),
                repo=spec.get("repo", ""),
                ref=spec.get("ref", "main"),
                dir=spec.get("dir", "docs/decisions"),
                name=spec.get("name", ""),
                url=spec.get("url", ""),
            )
            for prefix, spec in raw.get("remotes", {}).items()
        },
        journals={
            name: Journal(
                name,
                dir=root / spec["dir"],
                output=root / spec["output"],
                granularity=spec.get("granularity", "month"),
                title=spec.get("title", name.title()),
                blurb=spec.get("blurb", ""),
                _root=root,
            )
            for name, spec in raw.get("journals", {}).items()
        },
        stale_days=int(raw.get("stale_days", 90)),
        _raw=raw,
    )


@lru_cache(maxsize=1)
def current() -> Config:
    """The config for this process. Cached because every module wants it and
    re-reading per call would make the file's mtime a source of skew."""
    return load()


def reset() -> None:
    """Drop the cache — for tests that point `LURIA_ROOT` at a fixture."""
    current.cache_clear()
