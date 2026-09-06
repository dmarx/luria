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
    # `Superseded` is not in this condition's set. (It carries the built-in
    # successor finding instead, which is a different obligation.)
    assert not any("promote_when" in o for o in check("Superseded"))


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


# --- Eager validation of the condition itself (review of #172) --------------
#
# The mechanism's own justification for validating at load time is that a
# condition which can never hold "surfaces as no violations". Shape validation
# alone let exactly that through: a misspelled field and a miscased value are
# the two likeliest authoring mistakes, both were accepted, and both made the
# field silently never required.

def test_a_misspelled_condition_field_is_refused(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="staus"):
        project(tmp_path, monkeypatch,
                '[luria.schemes.SOTA.fields.promote_when]\n'
                'required_when = { staus = ["Proposed"] }\n')
        config.current()


def test_the_refusal_names_what_the_scheme_could_have_meant(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="status"):
        project(tmp_path, monkeypatch,
                '[luria.schemes.SOTA.fields.promote_when]\n'
                'required_when = { staus = ["Proposed"] }\n')
        config.current()


def test_a_miscased_status_value_is_refused(tmp_path, monkeypatch):
    """`proposed` is not a status, and a condition naming it never holds."""
    with pytest.raises(ValueError, match="proposed"):
        project(tmp_path, monkeypatch,
                '[luria.schemes.SOTA.fields.promote_when]\n'
                'required_when = { status = ["proposed"] }\n')
        config.current()


def test_a_status_outside_what_the_scheme_declares_is_refused(
        tmp_path, monkeypatch):
    """A scheme narrowing the vocabulary in `statuses.yaml` narrows what a
    condition on `status` can name too."""
    root = project(tmp_path, monkeypatch,
                   '[luria.schemes.SOTA.fields.promote_when]\n'
                   'required_when = { status = ["Deferred"] }\n')
    write(root, "record/practices.d/statuses.yaml",
          "Active:\n  label: In force\nProposed:\n  label: Not yet\n")
    config.reset()
    with pytest.raises(ValueError, match="Deferred"):
        config.current()


def test_a_condition_on_tags_is_accepted(tmp_path, monkeypatch):
    """`tags` is a built-in axis the scheme always has."""
    project(tmp_path, monkeypatch,
            '[luria.schemes.SOTA.fields.promote_when]\n'
            'required_when = { tags = ["record"] }\n')
    assert config.current().schemes["SOTA"]


def test_a_condition_on_a_declared_reference_is_accepted(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch,
            '[luria.schemes.SOTA.references]\n'
            'source = { scheme = "LIT" }\n\n'
            '[luria.schemes.SOTA.fields.promote_when]\n'
            'required_when = { source = ["LIT-001"] }\n')
    assert config.current().schemes["SOTA"]


def test_a_condition_on_a_free_text_field_leaves_its_values_alone(
        tmp_path, monkeypatch):
    """A field with no vocabulary has no set to check against, and refusing
    on that ground would forbid the ordinary case."""
    project(tmp_path, monkeypatch,
            'requires = ["stage"]\n\n'
            '[luria.schemes.SOTA.fields.promote_when]\n'
            'required_when = { stage = ["blocked"] }\n')
    assert config.current().schemes["SOTA"]


def test_a_value_outside_a_vocabulary_field_is_refused(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   '[luria.schemes.SOTA.fields.worlds]\n'
                   'vocabulary = "worlds"\n\n'
                   '[luria.schemes.SOTA.fields.promote_when]\n'
                   'required_when = { worlds = ["C"] }\n')
    write(root, "record/practices.d/worlds.yaml", "A:\n  label: A\nB:\n  label: B\n")
    config.reset()
    with pytest.raises(ValueError, match="C"):
        config.current()


def test_a_value_inside_a_vocabulary_field_is_accepted(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   '[luria.schemes.SOTA.fields.worlds]\n'
                   'vocabulary = "worlds"\n\n'
                   '[luria.schemes.SOTA.fields.promote_when]\n'
                   'required_when = { worlds = ["B"] }\n')
    write(root, "record/practices.d/worlds.yaml", "A:\n  label: A\nB:\n  label: B\n")
    config.reset()
    assert config.current().schemes["SOTA"]


# --- Resolving the condition's field through the contract -------------------

def test_a_vocabulary_default_makes_the_condition_hold(tmp_path, monkeypatch):
    """ADR-076: a field with a default is never absent. Reading raw
    frontmatter made the condition never hold for precisely the documents it
    was written about."""
    root = project(tmp_path, monkeypatch,
                   '[luria.schemes.SOTA.fields.worlds]\n'
                   'vocabulary = "worlds"\ndefault = "B"\n\n'
                   '[luria.schemes.SOTA.fields.promote_when]\n'
                   'required_when = { worlds = ["B"] }\n')
    write(root, "record/practices.d/worlds.yaml", "A:\n  label: A\nB:\n  label: B\n")
    config.reset()
    scheme = config.current().schemes["SOTA"]
    meta = {"status": "Active", "title": "A practice", "tags": ["record"]}
    out = contract.violations(contract.for_scheme(scheme),
                              "record/practices.d/SOTA-001.md", meta, {})
    assert any("promote_when" in o for o in out), out


def test_a_list_valued_condition_field_matches_any_element(
        tmp_path, monkeypatch):
    project(tmp_path, monkeypatch,
            '[luria.schemes.SOTA.fields.promote_when]\n'
            'required_when = { tags = ["record"] }\n')
    scheme = config.current().schemes["SOTA"]
    def run(tags):
        meta = {"status": "Active", "title": "A practice", "tags": tags}
        return contract.violations(contract.for_scheme(scheme),
                                   "record/practices.d/SOTA-001.md", meta, {})
    assert any("promote_when" in o for o in run(["other", "record"]))
    assert not any("promote_when" in o for o in run(["other"]))


def test_a_missing_condition_field_does_not_hold(tmp_path, monkeypatch):
    """Absent is "the condition is not met", not an error: the document
    check has its own finding for a missing required field."""
    project(tmp_path, monkeypatch,
            'requires = ["stage"]\n\n'
            '[luria.schemes.SOTA.fields.promote_when]\n'
            'required_when = { stage = ["blocked"] }\n')
    scheme = config.current().schemes["SOTA"]
    meta = {"status": "Active", "title": "A practice", "tags": ["record"]}
    out = contract.violations(contract.for_scheme(scheme),
                              "record/practices.d/SOTA-001.md", meta, {})
    assert not any("promote_when" in o for o in out), out


# --- The built-in supersession rule, stated with the mechanism --------------
#
# ADR-071's "a Superseded document names its successor" was a hand-written
# branch in `check_frontmatter` while this module carried the mechanism that
# states it. One implementation (DP-4), and the built-in gets the same finding
# wording, `because:` provenance and record-page line for free.

def _superseded(root: Path, extra: str = "") -> dict:
    return {"status": "Superseded", "title": "A practice", "tags": ["record"]}


def test_a_superseded_document_must_name_its_successor(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, "")
    scheme = config.current().schemes["SOTA"]
    out = contract.violations(contract.for_scheme(scheme),
                              "record/practices.d/SOTA-001.md",
                              _superseded(tmp_path), {})
    assert len(out) == 1, out
    assert "superseded_by" in out[0] and "Superseded" in out[0]


def test_a_superseded_document_that_names_one_is_clean(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, "")
    scheme = config.current().schemes["SOTA"]
    meta = {**_superseded(tmp_path), "superseded_by": ["SOTA-002"]}
    out = contract.violations(contract.for_scheme(scheme),
                              "record/practices.d/SOTA-001.md", meta,
                              {"SOTA": {"SOTA-002"}})
    assert out == [], out


def test_an_active_document_need_not_name_a_successor(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, "")
    scheme = config.current().schemes["SOTA"]
    meta = {"status": "Active", "title": "A practice", "tags": ["record"]}
    assert contract.violations(contract.for_scheme(scheme),
                               "record/practices.d/SOTA-001.md", meta, {}) == []


def test_the_built_in_condition_stays_out_of_the_per_scheme_contract(
        tmp_path, monkeypatch):
    """`describe()` lists what a scheme declares *beyond* the standard
    fields, and the record page says so in its own sentence. Rendering the
    built-in there would make every scheme look as though it declared a
    contract, and would contradict the "nothing beyond the standard fields"
    line the same page prints."""
    project(tmp_path, monkeypatch, "")
    scheme = config.current().schemes["SOTA"]
    assert contract.describe(contract.for_scheme(scheme)) == []


def test_the_record_page_states_the_built_in_condition_once(tmp_path, monkeypatch):
    """It is a real rule and a reader should meet it — stated with the
    standard fields, where it belongs, rather than repeated under every
    scheme as though each had declared it."""
    from luria import record_doc
    project(tmp_path, monkeypatch, "")
    section = record_doc.render().split("## What an entry must carry")[1]
    section = section.split("\n## ")[0]
    assert "superseded_by" in section and "Superseded" in section


def test_a_scheme_declaring_nothing_is_still_empty(tmp_path, monkeypatch):
    """The built-in carrying a condition must not make every scheme look as
    though it declared a contract."""
    project(tmp_path, monkeypatch, "")
    scheme = config.current().schemes["SOTA"]
    assert contract.for_scheme(scheme).empty
