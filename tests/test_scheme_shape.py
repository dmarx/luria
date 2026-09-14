"""A scheme declaring its own vocabulary source and its own references.

Both come from the same observation, made on a record with two content schemes
that cite each other and share a topic vocabulary: the configuration could
express the schemes but not the *relationship* or the *sharing*, so both got
restated by hand — four copies of one vocabulary, and a citation rule that
turned out to check only that a field was not blank.
"""

# inactive-ok-file: ADR-098 — Proposed. Named as the decision these
# fixtures are shaped by; the citation is to the reasoning, not a claim
# the decision is settled.

import yaml
from _config import merged
from pathlib import Path

import pytest

from luria import config, lint


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def doc(root: Path, rel: str, *, code: str, title: str, tags: list[str],
        extra: str = "") -> Path:
    front = ["---", "status: Active", f"title: {title!r}", "tags:"]
    front += [f"- {t}" for t in tags]
    front += ["date: '2026-01-01'"]
    if extra:
        front.append(extra)
    front += ["---", "", f"# {code}: {title}", "", "Body."]
    return write(root, rel, "\n".join(front) + "\n")


VOCAB = """\
optimization:
  label: Optimization
  blurb: optimizers and schedules
  primary_for: [LIT, SOTA]
stability:
  label: Stability
  blurb: normalization and initialization
  primary_for: [LIT, SOTA]
generative:
  label: Generative
  blurb: samplers and conditioning
  primary_for: [LIT]
"""


@pytest.fixture
def two_schemes(tmp_path, monkeypatch):
    """Two schemes sharing one vocabulary file, as the motivating record has."""
    def build(toml_extra: str = ""):
        # The case this fixture is about: one vocabulary, two schemes.
        # It used to be a shared FILE PATH, which is the half-measure the
        # central table replaced (ADR-098).
        write(tmp_path, "luria.yaml", merged("""
                                      issue_url: https://example.test/issues/{n}
                                      schemes:
                                        LIT:
                                          dir: record/literature.d
                                          axis: tags
                                          fields:
                                            tags:
                                              vocabulary: topics
                                              many: true
                                              closed: false
                                              groups:
                                                primary_topic:
                                                  require: exactly-one
                                        SOTA:
                                          dir: record/practices.d
                                          axis: tags
                                          fields:
                                            tags:
                                              vocabulary: topics
                                              many: true
                                              closed: false
                                              groups:
                                                primary_topic:
                                                  require: exactly-one
                                      """,
                                      {"vocabularies": {"topics": yaml.safe_load(VOCAB)}},
                                      toml_extra))
        monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
        config.reset()
        return tmp_path
    yield build
    config.reset()


REFERENCES = """
schemes:
  SOTA:
    references:
      source:
        scheme: LIT
        required: true
"""


# --- one vocabulary, pointed at twice ------------------------------------

def test_two_schemes_can_share_one_vocabulary(two_schemes):
    """The duplication this removes: the shared terms were previously written
    once per scheme in tags.yaml and again per scheme in the config — and a
    shared FILE was the half-measure, since two schemes could point at one and
    simply did not (ADR-098)."""
    two_schemes()
    cfg = config.current()
    assert cfg.schemes["LIT"].tags_vocab == "topics"
    assert cfg.schemes["SOTA"].tags_vocab == "topics"
    # The same object, not two readings that happen to agree.
    assert cfg.schemes["LIT"].tags == cfg.schemes["SOTA"].tags


def test_group_membership_comes_from_the_vocabulary(two_schemes):
    """`primary_for` is what lets the group list no tags at all — and lets one
    file give two schemes DIFFERENT primaries, which an inline list can only
    do by repeating the shared part."""
    two_schemes()
    cfg = config.current()
    lit, = cfg.schemes["LIT"].tag_groups
    sota, = cfg.schemes["SOTA"].tag_groups

    assert lit.tags == {"optimization", "stability", "generative"}
    assert sota.tags == {"optimization", "stability"}
    assert lit.derived and sota.derived


def test_a_derived_group_is_enforced_like_any_other(two_schemes):
    root = two_schemes()
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
        title="Two primaries", tags=["optimization", "stability"])
    errors = []
    lint.check_contracts(errors)
    assert any("wants exactly one" in e for e in errors)


def test_a_tag_the_scheme_cannot_carry_is_not_in_its_group(two_schemes):
    """`generative` is a LIT primary only, so a practice carrying it has no
    primary at all — which is what the record wanted and could previously say
    only by writing the other list out."""
    root = two_schemes()
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
        title="Wrong axis", tags=["generative"])
    errors = []
    lint.check_contracts(errors)
    assert any("wants exactly one" in e for e in errors)


def test_an_inline_list_still_wins(tmp_path, monkeypatch):
    """Derivation is the fallback, not a replacement: a group that lists tags
    means those tags, whatever the vocabulary says."""
    write(tmp_path, "luria.yaml", merged({"vocabularies": {
        "topics": yaml.safe_load(VOCAB)}}, """
issue_url: https://example.test/issues/{n}
schemes:
  SOTA:
    dir: record/practices.d
    axis: tags
    fields:
      tags:
        vocabulary: topics
        many: true
        closed: false
        groups:
          primary_topic:
            require: exactly-one
            tags:
            - stability
"""))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    group, = config.current().schemes["SOTA"].tag_groups
    assert group.tags == {"stability"} and not group.derived
    config.reset()


def test_a_group_that_derives_nothing_is_a_config_error(tmp_path, monkeypatch):
    """The eager-validation promise: a group constraining nothing must not
    surface as "no violations"."""
    write(tmp_path, "luria.yaml", merged(
        {"vocabularies": {"topics": {"optimization": {"label": "O"}}}}, """
issue_url: https://example.test/issues/{n}
schemes:
  SOTA:
    dir: record/practices.d
    axis: tags
    fields:
      tags:
        vocabulary: topics
        many: true
        closed: false
        groups:
          primary_topic:
            require: exactly-one
"""))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    with pytest.raises(ValueError, match="constrains nothing"):
        config.current()
    config.reset()


# --- references that mean something --------------------------------------

def test_a_declared_reference_must_be_present(two_schemes):
    root = two_schemes(REFERENCES)
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
        title="No source", tags=["optimization"])
    errors = []
    lint.check_contracts(errors)
    assert any("no `source:`" in e for e in errors)


def test_a_reference_must_be_a_code(two_schemes):
    """The gap `requires` left: a required field is satisfied by any truthy
    value, so an arbitrary sentence passed."""
    root = two_schemes(REFERENCES)
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
        title="Prose source", tags=["optimization"],
        extra="source: 'a paper I read once'")
    errors = []
    lint.check_contracts(errors)
    assert any("is not a code" in e for e in errors)


def test_a_reference_must_belong_to_the_named_scheme(two_schemes):
    """The other half of the gap: a practice citing a decision as its
    evidence passed silently."""
    root = two_schemes(REFERENCES)
    doc(root, "record/literature.d/LIT-001.md", code="LIT-001",
        title="A paper", tags=["optimization"])
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
        title="Wrong scheme", tags=["optimization"], extra="source: ADR-001")
    errors = []
    lint.check_contracts(errors)
    assert any("is not a LIT code" in e for e in errors)


def test_a_reference_must_resolve(two_schemes):
    root = two_schemes(REFERENCES)
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
        title="Dangling", tags=["optimization"], extra="source: LIT-999")
    errors = []
    lint.check_contracts(errors)
    assert any("resolves to no LIT document" in e for e in errors)


def test_a_good_reference_is_silent(two_schemes):
    root = two_schemes(REFERENCES)
    doc(root, "record/literature.d/LIT-001.md", code="LIT-001",
        title="A paper", tags=["optimization"])
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
        title="Cited", tags=["optimization"], extra="source: LIT-001")
    errors = []
    lint.check_contracts(errors)
    assert errors == []


def test_a_linked_reference_still_reads(two_schemes):
    """Reference fields are data and stay bare, but a hand-edited file can
    carry a link; refusing that would be a lint nobody could satisfy twice."""
    root = two_schemes(REFERENCES)
    doc(root, "record/literature.d/LIT-001.md", code="LIT-001",
        title="A paper", tags=["optimization"])
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
        title="Linked", tags=["optimization"],
        extra="source: '[LIT-001](../literature.d/LIT-001.md)'")
    errors = []
    lint.check_contracts(errors)
    assert errors == []


def test_an_optional_reference_may_be_absent(two_schemes):
    root = two_schemes("""
                       schemes:
                         SOTA:
                           references:
                             source:
                               scheme: LIT
                               required: false
                       """)
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
        title="No source", tags=["optimization"])
    errors = []
    lint.check_contracts(errors)
    assert errors == []


def test_referencing_an_undeclared_scheme_is_a_config_error(two_schemes):
    two_schemes("""
                schemes:
                  SOTA:
                    references:
                      source:
                        scheme: NOPE
                """)
    with pytest.raises(ValueError, match="not declared"):
        config.current()
