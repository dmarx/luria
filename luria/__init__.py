"""Luria — a project's memory, kept where the next collaborator will find it.

The four layers (design principles, decisions, changelog, devlog), the fragment
convention that keeps them conflict-free, the generated views, and the lint that
stops all of it from drifting.

Public surface is the CLI (`luria --help`); the modules are importable for
projects that want to extend a check rather than replace it.
"""

from importlib import metadata as _metadata

try:
    #: The installed distribution's version, read at import rather than
    #: written here. The hand-maintained copy this replaces said "0.1.0"
    #: while the package was at 0.28 — the exact drift `pyproject.toml`
    #: derives the version from VCS to prevent, reintroduced two lines into
    #: the package it was protecting (#295).
    __version__ = _metadata.version("luria")
except _metadata.PackageNotFoundError:          # a source tree, not installed
    __version__ = "0+unknown"
