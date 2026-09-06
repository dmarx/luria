"""A field required only while another field says something (#170).

A record can say what it believes — that is `status:` — and had nothing that
says what would change its mind. The consumer project measured the cost:
across 144 practices, four stated a promotion condition, all four in prose,
and none of the four was re-read when the evidence arrived. Two of them
carried near-identical prose conditions, both were satisfied by the same
paper on the same day, and only one was acted on, because somebody happened
to be reading both bodies that afternoon.

`required_when` is the smallest mechanism that makes the condition exist as a
field on the document rather than a paragraph nothing points at. One field,
one set of literal values; deliberately not an expression language.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import config, contract


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


CONDITION = ('[luria.schemes.SOTA.fields.promote_when]\n'
             'required_when = { status = ["Proposed", "Deferred"] }\n')


def project(tmp_path, monkeypatch, sota_extra: str = CONDITION) -> Path:
    write(tmp_path, "luria.toml", f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"

[luria.schemes.LIT]
dir = "record/literature.d"

[luria.schemes.SOTA]
dir = "record/practices.d"
{sota_extra}
""")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def check(status: str, extra: str = "") -> list[str]:
    scheme = config.current().schemes["SOTA"]
    meta = {"status": status, "title": "A practice", "tags": ["record"]}
    if extra:
        meta["promote_when"] = extra
    return contract.violations(contract.for_scheme(scheme),
                               "record/practices.d/SOTA-001.md", meta, {})


def test_a_provisional_document_must_carry_the_field(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    out = check("Proposed")
    assert len(out) == 1, out
    assert "promote_when" in out[0]


def test_an_active_document_need_not(tmp_path, monkeypatch):
    """Nothing is waiting, so there is nothing to state."""
    project(tmp_path, monkeypatch)
    assert check("Active") == []


def test_a_provisional_document_that_carries_it_is_clean(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    assert check("Proposed", "A third party evaluating it against its own "
                             "baseline") == []


def test_every_listed_value_triggers_it(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    assert len(check("Deferred")) == 1
    assert check("Superseded") == []


def test_the_finding_names_the_value_that_triggered_it(tmp_path, monkeypatch):
    """A conditional requirement that reports only the rule leaves the reader
    to work out which of their fields turned it on."""
    project(tmp_path, monkeypatch)
    out = check("Proposed")[0]
    assert "status" in out and "Proposed" in out


def test_the_finding_cites_the_declaration(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    assert "schemes.SOTA.fields.promote_when" in check("Proposed")[0]


def test_a_status_note_does_not_defeat_the_condition(tmp_path, monkeypatch):
    """`Proposed — pending a replication` is the one status vocabulary's
    spelling for a qualified status (ADR-003); matching the raw string would
    read it as a different status and quietly exempt the document."""
    project(tmp_path, monkeypatch)
    assert len(check("Proposed — pending a replication")) == 1


def test_it_composes_with_a_reference_declaration(tmp_path, monkeypatch):
    """`required_when` is a property of a field, so it applies to a typed one
    the same way."""
    project(tmp_path, monkeypatch,
            '[luria.schemes.SOTA.references]\n'
            'blocked_by = { scheme = "LIT", required = false, '
            'required_when = { status = ["Deferred"] } }\n')
    scheme = config.current().schemes["SOTA"]
    def run(status, **extra):
        meta = {"status": status, "title": "A practice", "tags": ["record"],
                **extra}
        return contract.violations(contract.for_scheme(scheme),
                                   "record/practices.d/SOTA-001.md", meta,
                                   {"LIT": {"LIT-001"}})
    assert run("Active") == []
    assert len(run("Deferred")) == 1
    assert run("Deferred", blocked_by="LIT-001") == []


def test_unconditional_and_conditional_together_is_a_config_error(
        tmp_path, monkeypatch):
    """`required = true` already demands it always; the condition would say
    nothing, which is the quiet failure a declaration exists to remove."""
    with pytest.raises(ValueError, match="always required"):
        project(tmp_path, monkeypatch,
                '[luria.schemes.SOTA.fields.promote_when]\n'
                'required = true\n'
                'required_when = { status = ["Proposed"] }\n')
        config.current()


def test_two_conditions_is_a_config_error(tmp_path, monkeypatch):
    """One field against a set of values. Two keys would need an `and`/`or`
    nobody has written down, and a config that guesses is worse than one
    that refuses."""
    with pytest.raises(ValueError, match="one field"):
        project(tmp_path, monkeypatch,
                '[luria.schemes.SOTA.fields.promote_when]\n'
                'required_when = { status = ["Proposed"], tags = ["x"] }\n')
        config.current()


def test_an_empty_value_list_is_a_config_error(tmp_path, monkeypatch):
    """A condition that can never be true is a requirement that never fires."""
    with pytest.raises(ValueError, match="no values"):
        project(tmp_path, monkeypatch,
                '[luria.schemes.SOTA.fields.promote_when]\n'
                'required_when = { status = [] }\n')
        config.current()


def test_a_field_table_declaring_nothing_is_still_an_error(
        tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="declares no type"):
        project(tmp_path, monkeypatch,
                '[luria.schemes.SOTA.fields.promote_when]\n'
                'many = true\n')
        config.current()


def test_the_contract_describes_the_condition(tmp_path, monkeypatch):
    """`docs/record.md` prints what an entry must carry; a requirement that
    only exists at some statuses has to say so, or the generated page is a
    lie about the scheme."""
    project(tmp_path, monkeypatch)
    scheme = config.current().schemes["SOTA"]
    lines = contract.describe(contract.for_scheme(scheme))
    line = next(ln for ln in lines if "promote_when" in ln)
    assert "required when" in line and "Proposed" in line and "Deferred" in line


def test_the_scheme_is_not_empty_for_a_condition_alone(tmp_path, monkeypatch):
    """`Contract.empty` decides whether a scheme has a contract worth
    printing; a scheme whose only declaration is a conditional one has."""
    project(tmp_path, monkeypatch)
    scheme = config.current().schemes["SOTA"]
    assert not contract.for_scheme(scheme).empty
