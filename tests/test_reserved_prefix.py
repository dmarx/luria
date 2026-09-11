# tests/test_reserved_prefix.py
"""The fixture namespace, reserved against a project's own schemes (#231).

A test suite has to write codes to test how codes are read, and every code it
writes is read back by the scanners as a citation. `FX` already answers that
for a code that should resolve — a remote whose every code points at the note
saying it is an example (ADR-034). The other half is a code that should
resolve to NOTHING and be claimed by nobody, which is what a fixture scheme's
own documents are. The namespace is the guarantee: a project that never
declares an `FX…` scheme can spell fixture codes in its tests without any of
them landing in its record.
"""

from __future__ import annotations

from pathlib import Path

from luria import config, lint


def project(tmp_path, monkeypatch, prefix: str) -> Path:
    (tmp_path / "luria.toml").write_text(f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"

[luria.schemes.{prefix}]
dir = "record/{prefix.lower()}.d"
output = "docs/{prefix.lower()}"
""")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def errors_for(tmp_path, monkeypatch, prefix: str) -> list[str]:
    project(tmp_path, monkeypatch, prefix)
    errors: list[str] = []
    lint.check_reserved_prefix(errors)
    return errors


# --- the reservation ---------------------------------------------------------

def test_an_ordinary_prefix_is_fine(tmp_path, monkeypatch):
    assert errors_for(tmp_path, monkeypatch, "ADR") == []


def test_the_fixture_prefix_itself_is_refused(tmp_path, monkeypatch):
    errors = errors_for(tmp_path, monkeypatch, "FXL")
    assert len(errors) == 1
    assert "FXL" in errors[0] and "fixture" in errors[0]


def test_the_bare_namespace_is_refused(tmp_path, monkeypatch):
    """`FX` is the remote prefix (ADR-034); a scheme of the same name would
    make every composed `FX-ADR-032` ambiguous as well."""
    assert len(errors_for(tmp_path, monkeypatch, "FX")) == 1


def test_any_other_name_in_the_namespace_is_refused(tmp_path, monkeypatch):
    """A migration fixture needs two prefixes at once, so the reservation is a
    namespace rather than one name — and a namespace has to hold at its edges
    or the second prefix is invisible only by luck."""
    assert len(errors_for(tmp_path, monkeypatch, "FXM")) == 1


def test_a_prefix_that_merely_starts_with_f_is_fine(tmp_path, monkeypatch):
    assert errors_for(tmp_path, monkeypatch, "FAQ") == []


def test_a_prefix_containing_fx_elsewhere_is_fine(tmp_path, monkeypatch):
    """The reservation is a leading namespace, not a substring search."""
    assert errors_for(tmp_path, monkeypatch, "AFX") == []


def test_the_finding_names_the_remedy(tmp_path, monkeypatch):
    """A scheme that already has documents is renamed by `rename_scheme`
    (ADR-040), not by hand — the finding has to say so, because the obvious
    reading of "pick another prefix" is to edit the config and orphan the
    filenames."""
    errors = errors_for(tmp_path, monkeypatch, "FXL")
    assert "rename_scheme" in errors[0]


# --- it runs as part of the lint ---------------------------------------------

def test_the_check_is_wired_into_the_run(tmp_path, monkeypatch):
    import inspect
    assert "check_reserved_prefix(errors)" in inspect.getsource(lint.run)
