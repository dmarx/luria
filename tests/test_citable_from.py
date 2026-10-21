# tests/test_citable_from.py
"""`citable_from`: a retired status one scheme's documents may be cited at,
from a named scheme at a named status, with no acknowledgement.

The case it was built for is a question record: a parent question that is
still `Open` cites the child split off it, and the child is now `Answered`.
That citation is the record working, not drifting, so it should not warn —
while every OTHER citation of an answered question still should, because it
either belongs on whatever answered it or still treats it as open.

`QN` and `CM` rather than live prefixes, per the fixture-code rule.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from _config import merged

from luria import ack, config, ref_status

BASE = {
    "issue_url": "https://example.test/issues/{n}",
    "vocabularies": {
        "qstatuses": {"Open": {"blurb": "being asked"},
                      "Answered": {"blurb": "settled"},
                      "Deferred": {"blurb": "parked"}},
        "cstatuses": {"Active": {"blurb": "held"},
                      "Retracted": {"blurb": "withdrawn"}},
    },
    "schemes": {
        "QN": {"dir": "record/questions.d", "output": "docs/questions",
               "active": "Open",
               "fields": {"status": {"vocabulary": "qstatuses"}},
               "citable_from": {"Answered": ["QN:Open"]}},
        "CM": {"dir": "record/claims.d", "output": "docs/claims",
               "active": "Active",
               "fields": {"status": {"vocabulary": "cstatuses"}}},
    },
}


def project(root: Path, monkeypatch, *extra) -> Path:
    (root / "luria.yaml").write_text(merged(BASE, *extra))
    for d in ("record/questions.d", "record/claims.d", "docs"):
        (root / d).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LURIA_ROOT", str(root))
    config.reset()
    return root


def doc(root: Path, code: str, status: str, body: str = "") -> Path:
    folder = "questions.d" if code.startswith("QN") else "claims.d"
    path = root / "record" / folder / f"{code}.md"
    path.write_text(f"---\nstatus: {status}\ntitle: 'Entry {code}'\n"
                    f"date: '2026-01-01'\n---\n\n# {code}: Entry\n\n{body}\n")
    return path


def corpus(root: Path, parent_body: str = "Split off: QN-001.") -> list[Path]:
    """An answered question, the open parent citing it, and every other kind
    of citer: a question at another status, another scheme, a plain file."""
    return [
        doc(root, "QN-001", "Answered", "The answered child."),
        doc(root, "QN-002", "Open", parent_body),
        doc(root, "QN-003", "Deferred", "Waits on QN-001."),
        doc(root, "CM-001", "Active", "Settles QN-001."),
        _write(root / "notes.md", "Still asking QN-001.\n"),
    ]


def _write(path: Path, text: str) -> Path:
    path.write_text(text)
    return path


def _scan(files):
    docs = ref_status.load_docs()
    return docs, ref_status.scan(files, docs)


def _loud_files(result, docs, root):
    rows = {d.code: loud for d, loud, _ in ref_status.flagged(result, docs)}
    return sorted(c.path.relative_to(root).as_posix()
                  for c in rows.get("QN-001", []))


# ── the sanctioned citation ──────────────────────────────────────────────

def test_the_declared_citer_needs_no_acknowledgement(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    docs, result = _scan(corpus(root))
    parent = [c for c in result.cited["QN-001"]
              if c.path.name == "QN-002.md"]
    assert len(parent) == 1 and parent[0].sanctioned
    assert not parent[0].loud
    assert "record/questions.d/QN-002.md" not in _loud_files(result, docs, root)


@pytest.mark.parametrize("citer", [
    "record/questions.d/QN-003.md",     # the right scheme, another status
    "record/claims.d/CM-001.md",        # another scheme
    "notes.md",                          # not a record document at all
])
def test_every_other_citer_still_warns(tmp_path, monkeypatch, citer):
    root = project(tmp_path, monkeypatch)
    docs, result = _scan(corpus(root))
    assert citer in _loud_files(result, docs, root)


def test_undeclared_scheme_judges_exactly_as_before(tmp_path, monkeypatch):
    """Without the key, the open parent's citation warns like any other."""
    root = project(tmp_path, monkeypatch,
                   {"schemes": {"QN": {"citable_from": None}}})
    docs, result = _scan(corpus(root))
    assert "record/questions.d/QN-002.md" in _loud_files(result, docs, root)


def test_an_acknowledgement_over_a_sanctioned_site_goes_stale(tmp_path,
                                                             monkeypatch):
    """The migration signal: an `inactive-ok` written before the key existed
    now answers for nothing, and says so."""
    root = project(tmp_path, monkeypatch)
    files = corpus(root, parent_body=(
        "<!-- inactive-ok: QN-001 — the answered child -->\n"
        "Split off: QN-001."))
    docs, result = _scan(files)
    stale = ref_status.stale_annotations(result, docs)
    assert any("QN-002.md" in s and "no longer applies" in s
               and "QN-001 is cited here from where its scheme's "
                   "`citable_from` allows" in s
               for s in stale), stale


def test_ack_offers_only_the_loud_sites(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    docs, result = _scan(corpus(root))
    _, sites, refusal = ack.plan("QN-001", docs, result)
    assert refusal == ""
    assert "QN-002.md" not in {c.path.name for c in sites}
    assert len(sites) == 3


# ── the declaration ──────────────────────────────────────────────────────

def test_the_declaration_is_parsed_into_triples(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    qn = config.current().schemes["QN"]
    assert qn.citable_from == (("Answered", "QN", "Open"),)
    assert config.current().schemes["CM"].citable_from == ()


@pytest.mark.parametrize("value, message", [
    (["Answered"], r"QN\.citable_from: .*mapping"),
    ({"Answered": "QN:Open"}, r"QN\.citable_from\.Answered: .*list"),
    ({"Answered": ["QN"]}, r"QN\.citable_from\.Answered: .*'QN'"),
    ({"Answered": ["QN:"]}, r"QN\.citable_from\.Answered: .*'QN:'"),
])
def test_a_malformed_declaration_is_refused(tmp_path, monkeypatch, value,
                                            message):
    project(tmp_path, monkeypatch, {"schemes": {"QN": {"citable_from": value}}})
    with pytest.raises(ValueError, match=message):
        config.current()


@pytest.mark.parametrize("value, message", [
    ({"Gone": ["QN:Open"]},
     r"QN\.citable_from: names 'Gone', which QN's status vocabulary"),
    ({"Open": ["QN:Open"]},
     r"QN\.citable_from: names 'Open', QN's `active` word"),
    ({"Answered": ["XX:Open"]},
     r"QN\.citable_from\.Answered: names scheme 'XX', which is not declared"),
    ({"Answered": ["CM:Gone"]},
     r"QN\.citable_from\.Answered: names 'CM:Gone', but CM's status "
     r"vocabulary does not hold 'Gone'"),
])
def test_a_declaration_that_cannot_mean_anything_is_refused(
        tmp_path, monkeypatch, value, message):
    project(tmp_path, monkeypatch, {"schemes": {"QN": {"citable_from": value}}})
    with pytest.raises(ValueError, match=message):
        config.current()
