"""What a config object IS, as data rather than as a comment (#279).

A vocabulary *value* has carried `label` and `blurb` for as long as there have
been vocabularies, and a relation gained the pair in #254. The things they
belong to had neither — so a reader could learn what `training-optimization`
means and not what the axis it sits on is for, and a project's most careful
prose about its own schema lived in comments no view could reach.

Two spellings, and the split is deliberate: a thing that renders its own page
takes `title` + `blurb` (a scheme, a journal, a chain), and a thing named
inside a scheme takes `label` + `blurb` (a vocabulary, a group, a field, a
relation).
"""

from __future__ import annotations

from pathlib import Path

from luria import config, contract, record_doc, vocabularies
from luria.adr_index import load_scheme

BASE = """
issue_url: https://example.test/issues/{n}
vocabularies:
  topics:
    alpha: {label: Alpha, blurb: the first one}
    beta: {label: Beta, blurb: the second one}
schemes:
  LIT:
    dir: record/literature.d
    output: docs/literature
    axis: tags
    fields:
      tags:
        vocabulary: topics
        many: true
"""


def project(tmp_path: Path, monkeypatch, cfg: str = BASE) -> Path:
    (tmp_path / "luria.yaml").write_text(cfg)
    d = tmp_path / "record" / "literature.d"
    d.mkdir(parents=True, exist_ok=True)
    (d / "LIT-001.md").write_text(
        "---\nstatus: Active\ntitle: N\ntags:\n- alpha\ndate: '2026-01-01'\n"
        "---\n\n# LIT-001: N\n\nBody.\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def lines(prefix: str = "LIT") -> list[str]:
    scheme = config.current().schemes[prefix]
    return contract.describe(contract.for_scheme(scheme))


def line_for(name: str, prefix: str = "LIT") -> str:
    return next(l for l in lines(prefix) if l.startswith(f"`{name}`"))


# --- the scheme: `title` + `blurb`, because it renders its own page ---------

def test_a_scheme_says_what_the_family_is(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, BASE.replace(
        "    dir: record/literature.d",
        "    dir: record/literature.d\n"
        "    title: The reading list\n"
        "    blurb: One note per paper, recording its standing here."))
    page = record_doc.render()
    assert "## What each family is" in page
    assert "**`LIT`** — The reading list" in page
    assert "One note per paper, recording its standing here." in page


def test_a_scheme_that_says_nothing_gets_no_section(tmp_path, monkeypatch):
    """No table of blanks. A project that declares none should read exactly
    as it did before the key existed."""
    project(tmp_path, monkeypatch)
    assert record_doc.families_section(config.current()) == ""


def test_a_title_without_a_blurb_is_enough(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, BASE.replace(
        "    dir: record/literature.d",
        "    dir: record/literature.d\n    title: The reading list"))
    assert "**`LIT`** — The reading list" in record_doc.render()


# --- the vocabulary --------------------------------------------------------

# The set describes ITSELF, in the central table — not on the field that
# invokes it. A vocabulary two schemes share is described once, which is the
# whole reason it is declared centrally.
VOCAB = """
issue_url: https://example.test/issues/{n}
vocabularies:
  topics:
    label: Topics
    blurb: the primary axis, in the order the index shows them
    values:
      alpha: {label: Alpha, blurb: the first one}
      beta: {label: Beta, blurb: the second one}
schemes:
  LIT:
    dir: record/literature.d
    output: docs/literature
    axis: tags
    fields:
      tags:
        vocabulary: topics
        many: true
"""


def test_a_vocabulary_blurb_reaches_the_contract_line(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, VOCAB)
    assert line_for("tags").endswith(
        "— *the primary axis, in the order the index shows them*")


def test_a_vocabulary_describes_itself_above_its_values(tmp_path, monkeypatch):
    """The set's purpose, on the page of one of its members — so a reader
    who lands on `alpha` learns what axis they are standing on."""
    root = project(tmp_path, monkeypatch, VOCAB)
    scheme = config.current().schemes["LIT"]
    pages = vocabularies.pages(scheme, load_scheme(scheme))
    page = next(t for p, t in pages.items() if p.name == "alpha.md")
    assert "*Topics — the primary axis, in the order the index shows them*" in page
    # and the value's own blurb still follows it
    assert "**Alpha** — the first one." in page


def test_a_vocabulary_without_a_blurb_renders_as_before(tmp_path, monkeypatch):
    """The absence case, asserted directly: nothing is added, not even an
    empty separator."""
    root = project(tmp_path, monkeypatch)
    scheme = config.current().schemes["LIT"]
    page = next(t for p, t in vocabularies.pages(scheme, load_scheme(scheme)).items()
                if p.name == "alpha.md")
    assert "*" not in page.split("**Alpha**")[0].split("# LITs")[1]
    assert "—" not in line_for("tags").split("(luria.yaml")[1]


# --- the other three carriers ----------------------------------------------

def test_a_plain_field_can_say_what_it_is_for(tmp_path, monkeypatch):
    """The case with the least description available before: a plain field
    has no vocabulary to carry the explanation, so there was nowhere at all."""
    project(tmp_path, monkeypatch, BASE + """      stage:
        many: true
        blurb: how far through the pipeline this sits
""")
    assert line_for("stage").endswith("— *how far through the pipeline this sits*")


def test_a_relation_blurb_now_renders(tmp_path, monkeypatch):
    """`Reference` has carried `blurb` since #254 and nothing printed it."""
    project(tmp_path, monkeypatch, BASE + """    references:
      extends:
        scheme: LIT
        required: false
        blurb: the paper this one builds on
""")
    assert line_for("extends").endswith("— *the paper this one builds on*")


def test_a_tag_group_blurb_reaches_its_line(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, VOCAB + """        groups:
          primary:
            tags:
            - alpha
            - beta
            require: exactly-one
            blurb: the one thing a document is most about
""")
    assert line_for("primary").endswith("— *the one thing a document is most about*")


def test_a_field_group_blurb_reaches_its_line(tmp_path, monkeypatch):
    """`source` on a reading list means *a citable identifier* — the thing
    `arxiv`, `doi` and `url` have in common and none of them names.

    The members carry `many` only to satisfy the declares-no-type check: a
    `blurb` describes a field and does not constrain one, so it does not
    count as typing it. That is deliberate and is the decision's one left-open
    item."""
    project(tmp_path, monkeypatch, BASE + """      arxiv:
        required: false
        many: true
      doi:
        required: false
        many: true
    field_groups:
      source:
        fields:
        - arxiv
        - doi
        require: at-least-one
        blurb: a citable identifier, whichever kind the paper has
""")
    assert line_for("source").endswith(
        "— *a citable identifier, whichever kind the paper has*")


# --- the pair the split resolves -------------------------------------------

def test_a_chain_takes_the_blurb_half_of_its_pair(tmp_path, monkeypatch):
    """`Chain` already had `title`; it renders a page, so it takes `blurb`."""
    project(tmp_path, monkeypatch, BASE + """    references:
      extends:
        scheme: LIT
        required: false
        many: true
chains:
  lineage:
    scheme: LIT
    relation: extends
    output: docs/lineage.md
    title: Lines of work
    blurb: what each paper builds on, walked transitively
""")
    chain = config.current().chains["lineage"]
    assert chain.title == "Lines of work"
    assert chain.blurb == "what each paper builds on, walked transitively"


# --- the two shapes of the central table -----------------------------------

def test_the_flat_vocabulary_form_is_unchanged(tmp_path, monkeypatch):
    """Every config written before this reads exactly as it did: with no
    `values:` key the whole table is values, and the set describes nothing."""
    project(tmp_path, monkeypatch)
    cfg = config.current()
    assert set(cfg.vocabularies["topics"]) == {"alpha", "beta"}
    assert cfg.vocabulary_meta == {}
    vocab = next(v for v in cfg.schemes["LIT"].vocabularies if v.field == "tags")
    assert (vocab.label, vocab.blurb) == ("", "")


def test_the_nested_form_separates_the_set_from_its_values(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, VOCAB)
    cfg = config.current()
    assert set(cfg.vocabularies["topics"]) == {"alpha", "beta"}
    assert cfg.vocabulary_meta["topics"]["label"] == "Topics"
    vocab = next(v for v in cfg.schemes["LIT"].vocabularies if v.field == "tags")
    assert vocab.label == "Topics"


def test_one_description_reaches_every_scheme_that_names_it(tmp_path, monkeypatch):
    """The reason it lives on the set. Two schemes, one vocabulary, one
    description — not a copy per field free to drift, which is the failure
    ADR-098 moved the values themselves to fix."""
    project(tmp_path, monkeypatch, VOCAB + """  SOTA:
    dir: record/practices.d
    output: docs/practices
    axis: tags
    fields:
      tags:
        vocabulary: topics
        many: true
""")
    said = {p: next(v.blurb for v in s.vocabularies if v.field == "tags")
            for p, s in config.current().schemes.items()}
    assert said == {"LIT": "the primary axis, in the order the index shows them",
                    "SOTA": "the primary axis, in the order the index shows them"}


def test_a_value_named_values_is_refused_rather_than_guessed_at(
        tmp_path, monkeypatch):
    """The one ambiguous case. Reading it as metadata would empty the
    vocabulary and report that as no violations."""
    import pytest
    project(tmp_path, monkeypatch, BASE.replace(
        "    alpha: {label: Alpha, blurb: the first one}",
        "    alpha: {label: Alpha, blurb: the first one}\n    values: {label: V}"))
    with pytest.raises(ValueError, match="a value named `values`"):
        config.current()


# --- the set carries the alert too (#281) -----------------------------------

BOTH = """
issue_url: https://example.test/issues/{n}
vocabularies:
  topics:
    label: Topics
    blurb: the primary axis of both indexes
    alert: >-
      Closed so every tag is one somebody chose, not because the list is
      finished — add a value rather than reaching for the nearest wrong one.
    values:
      alpha: {label: Alpha, blurb: the first one}
schemes:
  LIT:
    dir: record/literature.d
    output: docs/literature
    axis: tags
    fields:
      tags:
        vocabulary: topics
        many: true
        closed: true
  SOTA:
    dir: record/practices.d
    output: docs/practices
    axis: tags
    fields:
      tags:
        vocabulary: topics
        many: true
        closed: true
"""


def test_a_vocabulary_carries_its_alert_beside_its_blurb(tmp_path, monkeypatch):
    """The first record to use #273 and #279 together was refused: the nested
    form's key list was spelled inline and did not know about `alert`."""
    project(tmp_path, monkeypatch, BOTH)
    vocab = next(v for v in config.current().schemes["LIT"].vocabularies
                 if v.field == "tags")
    assert vocab.label == "Topics"
    assert vocab.blurb.startswith("the primary axis")
    assert vocab.alert.startswith("Closed so every tag")


def test_one_alert_reaches_every_scheme_that_names_the_vocabulary(
        tmp_path, monkeypatch):
    """Why it belongs on the set: declared per field, a vocabulary three
    schemes share would carry the same sentence three times — the drift
    ADR-098 centralised vocabularies to prevent."""
    project(tmp_path, monkeypatch, BOTH)
    said = {p: next(v.alert for v in s.vocabularies if v.field == "tags")
            for p, s in config.current().schemes.items()}
    assert len(set(said.values())) == 1
    assert set(said) == {"LIT", "SOTA"}


def test_the_refusal_names_every_key_a_nested_table_may_carry(
        tmp_path, monkeypatch):
    """The message listed three keys while the code allowed four, which is
    the drift the named constant exists to stop."""
    import pytest
    project(tmp_path, monkeypatch, BASE.replace(
        "    alpha: {label: Alpha, blurb: the first one}",
        "    alpha: {label: Alpha, blurb: the first one}\n    values: {label: V}"))
    with pytest.raises(ValueError) as caught:
        config.current()
    for key in ("`alert`", "`blurb`", "`label`", "`values`"):
        assert key in str(caught.value)
