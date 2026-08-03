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
    "devlog.d" = "docs/devlog.md"

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
        "devlog.d": "docs/devlog.md",
    },
    "code": {
        "globs": [],
        # Dated records: true about the day they were written, forever. Scanning
        # them for stale references produces permanent, unactionable noise.
        "historical": ["CHANGELOG.md", "docs/devlog.md"],
    },
    "schemes": {
        "ADR": {"dir": "docs/decisions", "active": "Active", "render": "index"},
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
        import re
        return re.compile(rf"\b{self.prefix}[- ](?P<num>\d{{1,4}})\b")

    def code(self, number: str | int) -> str:
        return f"{self.prefix}-{int(number):03d}"


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

    def is_generated(self, path: Path) -> bool:
        """A view the generator owns. Rewriting one is pointless — the next
        build undoes it — so the reference fixer skips them."""
        if path == self.index or path.parent == self.tag_dir:
            return True
        return any(s.output == path for s in self.schemes.values())

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
