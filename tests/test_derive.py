"""A field computed from another field (#216).

The value has one source. These tests pin the three things that makes true:
the derivation resolves everywhere a field is read, writing it down is a
finding, and a declaration that could never resolve is refused at load.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import adr_index, config, contract, derive, invariants, new


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


TOPICS = """
optimizers:
  label: Optimizers
stability:
  label: Stability
encoding:
  label: Encoding
"""

DERIVED = """
[luria.schemes.LIT.fields.primary_topic]
derive     = "first:tags"
vocabulary = "tags"
"""


def project(tmp_path, monkeypatch, extra: str = DERIVED,
            topics: str = TOPICS) -> Path:
    write(tmp_path, "luria.toml", f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"

[luria.schemes.LIT]
dir = "record/literature.d"
output = "docs/literature"

[luria.schemes.LIT.references]
extends = {{ scheme = "LIT", required = false, many = true, converse = "extended_by" }}
extended_by = {{ scheme = "LIT", required = false, many = true, converse = "extends" }}
{extra}
""")
    write(tmp_path, "record/literature.d/tags.yaml", topics)
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def note(root: Path, number: int, tags: list[str], *, extends=(),
         extra: str = "") -> Path:
    front = ["---", "status: Active", f"title: 'Note {number}'", "tags:"]
    front += [f"- {t}" for t in tags]
    front.append("date: '2026-01-01'")
    if extends:
        front.append("extends:")
        front += [f"- {c}" for c in extends]
    if extra:
        front.append(extra)
    front += ["---", "", f"# LIT-{number:03d}: Note {number}", "", "Body."]
    return write(root, f"record/literature.d/LIT-{number:03d}.md",
                 "\n".join(front) + "\n")


def scheme():
    return config.current().schemes["LIT"]


def findings(root: Path, path: Path) -> list[str]:
    c = contract.for_scheme(scheme())
    meta, _ = adr_index.parse_frontmatter(path.read_text())
    return contract.violations(c, config.current().rel(path), meta, {})


# --- the derivation itself ---------------------------------------------------

def test_the_first_value_becomes_the_field(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    path = note(root, 1, ["stability", "optimizers"])
    assert adr_index.Adr(path, scheme()).meta["primary_topic"] == "stability"


def test_order_is_the_whole_statement(tmp_path, monkeypatch):
    """The same two tags the other way round are a different primary. This is
    the cost the feature accepts, so it is pinned rather than implied."""
    root = project(tmp_path, monkeypatch)
    a = note(root, 1, ["stability", "optimizers"])
    b = note(root, 2, ["optimizers", "stability"])
    assert adr_index.Adr(a, scheme()).meta["primary_topic"] == "stability"
    assert adr_index.Adr(b, scheme()).meta["primary_topic"] == "optimizers"


def test_last_reads_the_other_end(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   DERIVED.replace('"first:tags"', '"last:tags"'))
    path = note(root, 1, ["stability", "optimizers"])
    assert adr_index.Adr(path, scheme()).meta["primary_topic"] == "optimizers"


def test_an_empty_source_derives_nothing(tmp_path, monkeypatch):
    """Absence rather than a blank: a document with no tags has no primary
    topic, and inventing one would be a value nobody wrote."""
    root = project(tmp_path, monkeypatch)
    path = write(root, "record/literature.d/LIT-001.md",
                 "---\nstatus: Active\ntitle: 'Note 1'\ndate: '2026-01-01'\n"
                 "---\n\n# LIT-001: Note 1\n")
    assert "primary_topic" not in adr_index.Adr(path, scheme()).meta


def test_the_document_on_disk_is_untouched(tmp_path, monkeypatch):
    """A derived value lives in the reading, never in the file — the property
    that makes folding it into `meta` safe."""
    root = project(tmp_path, monkeypatch)
    path = note(root, 1, ["stability"])
    before = path.read_text()
    adr_index.Adr(path, scheme())
    assert path.read_text() == before
    assert "primary_topic" not in before


# --- read-only ---------------------------------------------------------------

def test_writing_a_derived_field_is_a_finding(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    path = note(root, 1, ["stability"], extra="primary_topic: optimizers")
    out = findings(root, path)
    assert len(out) == 1
    assert "`primary_topic:` is written in frontmatter" in out[0]
    assert "first:tags" in out[0]


def test_a_written_value_that_agrees_is_still_a_finding(tmp_path, monkeypatch):
    """Agreeing today is not the property that matters. Two copies of one fact
    are free to diverge tomorrow, and nothing would notice."""
    root = project(tmp_path, monkeypatch)
    path = note(root, 1, ["stability"], extra="primary_topic: stability")
    assert len(findings(root, path)) == 1


def test_the_scaffold_offers_no_flag_for_one(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    assert "primary_topic" not in new.declared_fields(scheme())
    assert "extends" in new.declared_fields(scheme())


# --- it is an ordinary field to everything else ------------------------------

def test_the_derived_value_is_checked_against_its_vocabulary(
        tmp_path, monkeypatch):
    """"The first tag must be a real topic" costs no new check — the
    vocabulary machinery already written does it once the field exists."""
    root = project(tmp_path, monkeypatch)
    path = note(root, 1, ["homemade", "stability"])
    out = findings(root, path)
    assert len(out) == 1
    assert "`primary_topic: homemade` is not in the `tags` vocabulary" in out[0]


def test_a_secondary_tag_outside_the_vocabulary_is_fine(tmp_path, monkeypatch):
    """Only the first position is constrained. `tags` stays open, which is
    what lets a private tag ride along behind a real topic."""
    root = project(tmp_path, monkeypatch)
    assert findings(root, note(root, 1, ["stability", "homemade"])) == []


def test_a_chain_can_assert_the_derived_field(tmp_path, monkeypatch):
    """The point of the exercise: `invariant` reads a derived field like any
    other, so a relation can assert the primary rather than any tag."""
    root = project(tmp_path, monkeypatch, DERIVED + """
[luria.chains.lineage]
scheme    = "LIT"
relation  = "extends"
output    = "docs/lineage.md"
invariant = "primary_topic"
""")
    note(root, 1, ["stability", "optimizers"])
    note(root, 2, ["optimizers", "stability"], extends=["LIT-001"])
    chain = config.current().chains["lineage"]
    assert [h.codes for h in invariants.edges(chain)] == [("LIT-001", "LIT-002")]

    root = project(tmp_path, monkeypatch, DERIVED + """
[luria.chains.lineage]
scheme    = "LIT"
relation  = "extends"
output    = "docs/lineage.md"
invariant = "primary_topic"
""")
    note(root, 1, ["stability", "optimizers"])
    note(root, 2, ["stability"], extends=["LIT-001"])
    assert invariants.edges(config.current().chains["lineage"]) == []


def test_sharing_a_secondary_binds_tags_but_not_the_primary(
        tmp_path, monkeypatch):
    """The two readings the pair makes available, on one record: `tags` is
    satisfied by any shared value, `primary_topic` only by the first."""
    both = DERIVED + """
[luria.chains.lineage]
scheme    = "LIT"
relation  = "extends"
output    = "docs/lineage.md"
invariant = "tags"
"""
    root = project(tmp_path, monkeypatch, both)
    note(root, 1, ["optimizers", "stability"])
    note(root, 2, ["encoding", "stability"], extends=["LIT-001"])
    assert invariants.edges(config.current().chains["lineage"]) == []

    root = project(tmp_path, monkeypatch,
                   both.replace('invariant = "tags"',
                                'invariant = "primary_topic"'))
    note(root, 1, ["optimizers", "stability"])
    note(root, 2, ["encoding", "stability"], extends=["LIT-001"])
    assert [h.codes for h in
            invariants.edges(config.current().chains["lineage"])] == [
        ("LIT-001", "LIT-002")]


def test_the_record_page_says_where_the_value_comes_from(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    lines = contract.describe(contract.for_scheme(scheme()))
    line = next(l for l in lines if l.startswith("`primary_topic`"))
    assert "derived — the first of `tags:`, never written" in line


# --- refused at load ---------------------------------------------------------

@pytest.mark.parametrize("spec,message", [
    ('"tags"', "is not a derivation"),
    ('"middle:tags"', "not one of first, last"),
    ('"first:primary_topic"', "derives from itself"),
    ('"first:nonexistent"', "is not a field LIT declares"),
    ('"first:status"', "renames a field rather than deriving one"),
])
def test_a_derivation_that_could_never_resolve_is_refused(
        tmp_path, monkeypatch, spec, message):
    project(tmp_path, monkeypatch, DERIVED.replace('"first:tags"', spec))
    with pytest.raises(ValueError, match=message):
        config.current()


@pytest.mark.parametrize("extra,message", [
    ("many = true", "drop `many`"),
    ("required = true", "require `tags` instead"),
    ('default = "stability"', "two answers to where the value comes from"),
])
def test_a_second_answer_about_the_value_is_refused(
        tmp_path, monkeypatch, extra, message):
    project(tmp_path, monkeypatch, DERIVED + extra + "\n")
    with pytest.raises(ValueError, match=message):
        config.current()


def test_a_derivation_needs_no_vocabulary_to_be_a_field(tmp_path, monkeypatch):
    """`derive` types a field on its own. Without this the bare case would be
    resolved onto documents but described nowhere, which is a field the record
    page cannot tell a reader about."""
    project(tmp_path, monkeypatch, '''
[luria.schemes.LIT.fields.primary_topic]
derive = "first:tags"
''')
    root = tmp_path
    path = note(root, 1, ["homemade"])
    assert adr_index.Adr(path, scheme()).meta["primary_topic"] == "homemade"
    assert findings(root, path) == []
    line = next(l for l in contract.describe(contract.for_scheme(scheme()))
                if l.startswith("`primary_topic`"))
    assert "derived — the first of `tags:`, never written" in line
