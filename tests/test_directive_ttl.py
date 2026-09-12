"""`until <date>` — an acknowledgement that stops excusing things on a date (#58).

An acknowledgement is a promise about the future: *this reference to a Proposed
decision is deliberate, I know what I am doing.* Promises about the future go
stale, and the whole point of the acknowledgement is that it silences a check —
so when it goes stale, it goes stale quietly. That is the failure mode the
directives exist to prevent, reproduced one level up.

So a directive can carry an expiry, and after it passes the linter behaves as
if the directive were not written. Uniform across every directive name, because
`find` is the one place they are read: nothing at a call site knows or cares.

The clock is injected (`as_of`), the way `adr_pending` already takes one. A
test that depends on the wall clock passes until the day it doesn't.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from luria import directives

TODAY = dt.date(2026, 9, 12)


def _md(tmp_path: Path, body: str) -> tuple[Path, str]:
    path = tmp_path / "note.md"
    path.write_text(body, encoding="utf-8")
    return path, body


def _one(tmp_path: Path, body: str, as_of: dt.date | None = TODAY):
    path, text = _md(tmp_path, body)
    found = directives.find(path, text, as_of=as_of)
    return found[0] if found else None


# ── no expiry: exactly as before ────────────────────────────────────────────

def test_a_directive_without_an_expiry_never_expires(tmp_path):
    d = _one(tmp_path, "<!-- inactive-ok: ADR-012 — the one this replaced -->\ncites ADR-012\n")
    assert d is not None
    assert d.expires is None
    assert d.args == ("ADR-012",)
    assert d.reason == "the one this replaced"


# ── until <date> ────────────────────────────────────────────────────────────

def test_an_unexpired_directive_still_governs_and_knows_its_date(tmp_path):
    d = _one(tmp_path, "<!-- inactive-ok: ADR-012 until 2026-10-01 — circle back -->\ncites ADR-012\n")
    assert d is not None
    assert d.expires == dt.date(2026, 10, 1)
    # The expiry is not one of the codes it names — otherwise every consumer
    # that validates arguments would report `until` as an unknown one.
    assert d.args == ("ADR-012",)
    assert d.reason == "circle back"


def test_the_last_day_is_included(tmp_path):
    """`until 2026-09-12` reads as "good until the 12th", not "dead on it"."""
    body = "<!-- inactive-ok: ADR-012 until 2026-09-12 — until then -->\ncites ADR-012\n"
    assert _one(tmp_path, body, as_of=dt.date(2026, 9, 12)) is not None
    assert _one(tmp_path, body, as_of=dt.date(2026, 9, 13)) is None


def test_an_expired_directive_is_not_returned_at_all(tmp_path):
    """"Behaves as if the annotation isn't even there" — and the way to be sure
    of that everywhere is to drop it at `find`, the one place they are read."""
    assert _one(tmp_path, "<!-- inactive-ok: ADR-012 until 2026-01-01 — done -->\ncites ADR-012\n") is None


def test_expiry_is_uniform_across_directive_names(tmp_path):
    """Not a feature of `inactive-ok`. `find` parses the shape, so every
    directive gets this the same way — which is the promise the syntax makes."""
    for name in ("inactive-ok", "unexempt", "target-ok", "url-ok"):
        live = f"<!-- {name}: codeblock until 2026-10-01 — soon -->\nbody\n"
        dead = f"<!-- {name}: codeblock until 2026-01-01 — over -->\nbody\n"
        assert _one(tmp_path, live) is not None, name
        assert _one(tmp_path, dead) is None, name


def test_scope_still_works_with_an_expiry(tmp_path):
    d = _one(tmp_path, "<!-- inactive-ok-file: ADR-012 until 2026-10-01 — all of it -->\n\ncites ADR-012\n")
    assert d is not None
    assert d.scope == directives.FILE
    assert d.covers(99)


# ── reporting what expired ──────────────────────────────────────────────────

def test_expired_directives_are_findable_for_reporting(tmp_path):
    """Dropping them from `find` makes them inert; it must not make them
    invisible. A check that starts failing again with no word about the
    acknowledgement sitting right above it is a puzzle, not a report."""
    path, text = _md(tmp_path, "<!-- inactive-ok: ADR-012 until 2026-01-01 — done -->\ncites ADR-012\n")
    gone = directives.find_expired(path, text, as_of=TODAY)
    assert [d.name for d in gone] == ["inactive-ok"]
    assert gone[0].expires == dt.date(2026, 1, 1)
    assert gone[0].args == ("ADR-012",)


def test_nothing_expired_is_an_empty_list_not_a_surprise(tmp_path):
    path, text = _md(tmp_path, "<!-- inactive-ok: ADR-012 until 2026-10-01 — soon -->\ncites ADR-012\n")
    assert directives.find_expired(path, text, as_of=TODAY) == []


def test_find_and_find_expired_partition_the_file(tmp_path):
    path, text = _md(
        tmp_path,
        "<!-- inactive-ok: ADR-011 until 2026-10-01 — soon -->\n"
        "<!-- inactive-ok: ADR-012 until 2026-01-01 — over -->\n"
        "<!-- inactive-ok: ADR-013 — forever -->\n"
        "cites ADR-011 ADR-012 ADR-013\n")
    live = {d.args[0] for d in directives.find(path, text, as_of=TODAY)}
    dead = {d.args[0] for d in directives.find_expired(path, text, as_of=TODAY)}
    assert live == {"ADR-011", "ADR-013"}
    assert dead == {"ADR-012"}
    assert not live & dead


# ── a malformed expiry is reported, not silently obeyed ─────────────────────

def test_an_unparseable_date_keeps_the_directive_live_and_reports_it(tmp_path):
    """Fail-safe, and loud. Dropping the suppression on a typo would break a
    build for a reason the message would not explain; keeping it and reporting
    the typo says what to fix without breaking anything."""
    d = _one(tmp_path, "<!-- inactive-ok: ADR-012 until nextweek — oops -->\ncites ADR-012\n")
    assert d is not None
    assert d.expires is None
    assert "nextweek" in (directives.problems(d) or "")


def test_until_with_no_date_is_reported(tmp_path):
    d = _one(tmp_path, "<!-- inactive-ok: ADR-012 until — oops -->\ncites ADR-012\n")
    assert d is not None
    assert "until" in (directives.problems(d) or "")


def test_a_well_formed_expiry_is_not_a_problem(tmp_path):
    d = _one(tmp_path, "<!-- inactive-ok: ADR-012 until 2026-10-01 — fine -->\ncites ADR-012\n")
    assert directives.problems(d) is None


def test_a_malformed_expiry_does_not_eat_the_codes(tmp_path):
    """The report is about the date. The codes it names are still the codes it
    names, so whatever the directive was excusing stays excused."""
    d = _one(tmp_path, "<!-- inactive-ok: ADR-012 until soon — oops -->\ncites ADR-012\n")
    assert "ADR-012" in d.args


# ── the report ──────────────────────────────────────────────────────────────
#
# Dropping an expired directive is the feature; saying which one expired is
# what keeps it from being a mystery. `luria lint` reports them as their own
# finding rather than folding them into "no longer applies", because they are
# different facts: one means the subject changed under the acknowledgement, the
# other means its author set a deadline and the deadline arrived.

def test_the_report_names_the_file_the_directive_and_the_date(tmp_path, monkeypatch):
    from luria import config, lint
    (tmp_path / "record" / "decisions.d").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "luria.toml").write_text('[luria]\n')
    (tmp_path / "docs" / "guide.md").write_text(
        "<!-- inactive-ok: ADR-012 until 2026-01-01 — circle back after the release -->\n"
        "as ADR-012 says\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()

    found = lint.expired_directives(as_of=TODAY)
    assert len(found) == 1, found
    line = found[0]
    assert "docs/guide.md" in line
    assert "inactive-ok" in line
    assert "2026-01-01" in line
    # The author's own words are the most useful thing in the report: they say
    # what the deadline was FOR.
    assert "circle back after the release" in line


def test_a_live_directive_is_not_reported(tmp_path, monkeypatch):
    from luria import config, lint
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "luria.toml").write_text('[luria]\n')
    (tmp_path / "docs" / "guide.md").write_text(
        "<!-- inactive-ok: ADR-012 until 2026-10-01 — soon -->\nas ADR-012 says\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    assert lint.expired_directives(as_of=TODAY) == []
