# tests/test_promote.py
"""`promote_vocabulary`: turn a vocabulary into a scheme, in one migration.

A vocabulary is a shorthand for a tiny constrained scheme — named values
with a label and a blurb, and nothing else. When a record needs a value to
carry more (standing, history, relations of its own, a place in a
hierarchy), that is a type error, and the repair is to promote the
vocabulary to the scheme it was abbreviating: one document per value, and
every field that drew from it becomes a grouped reference.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from luria import adr_index as builder, config, lint, migrate

CONFIG = """\
issue_url: https://example.test/issues/{n}
vocabularies:
  statuses:
    Active: {}
    Superseded: {}
  # Where a change lands. Kept short on purpose.
  area:
    runtime:
      label: Runtime
      blurb: the execution engine
    storage: {}
    network: {}
schemes:
  # Proposals, one per change.
  RFC:
    dir: record/rfcs.d
    output: docs/rfcs
    active: Active
    render: index
    axis: area
    fields:
      status: {vocabulary: statuses}
      area:
        vocabulary: area
        many: true
  NOTE:
    dir: record/notes.d
    output: docs/notes
    active: Active
    render: index
    fields:
      status: {vocabulary: statuses}
      area:
        vocabulary: area
        required: true
%s
"""

SPEC = """\
title: Areas become a scheme
operations:
- op: promote_vocabulary
  vocabulary: area
  to: AREA
%s"""


def _doc(path: Path, code: str, title: str, front: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nstatus: Active\ntitle: '{title}'\nversion: 1\n"
                    f"{front}date: '2026-01-01'\n---\n\n# {code}: {title}\n\n"
                    "area: this line is prose, not frontmatter.\n")


def project(tmp_path, monkeypatch, *, extra: str = "",
            spec_extra: str = "") -> Path:
    (tmp_path / "luria.yaml").write_text(CONFIG % extra)
    rfcs, notes = tmp_path / "record/rfcs.d", tmp_path / "record/notes.d"
    _doc(rfcs / "RFC-001.md", "RFC-001", "Durable jobs",
         "area:\n- runtime\n- storage\n")
    _doc(rfcs / "RFC-002.md", "RFC-002", "Faster boot", "area: [runtime]\n")
    _doc(rfcs / "RFC-003.md", "RFC-003", "Unfiled")
    _doc(notes / "NOTE-001.md", "NOTE-001", "A note", "area: storage\n")
    mig = tmp_path / "record/migrations.d"
    mig.mkdir(parents=True)
    (mig / "0001-areas.yaml").write_text(SPEC % spec_extra)
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def _front(path: Path) -> dict:
    return yaml.safe_load(path.read_text().split("---\n")[1])


def test_the_vocabulary_becomes_a_scheme(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    migrate.run("0001")
    raw = yaml.safe_load((root / "luria.yaml").read_text())
    assert "area" not in raw["vocabularies"]
    area = raw["schemes"]["AREA"]
    assert area["dir"] == "record/areas.d"
    assert area["output"] == "docs/areas"
    assert area["fields"]["status"] == {"vocabulary": "statuses"}
    # The value's old spelling is kept on the document it became, and can
    # name only one: it was an identity.
    assert area["fields"]["slug"] == {"unique": True}
    # And it is how the documents go on citing a term: `AREA-runtime` is
    # the readable spelling of `AREA-001` (#219), so promotion does not
    # trade an interpretable value for a number.
    assert area["alias"] == "AREA-{slug}"


def test_the_config_keeps_its_comments(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    migrate.run("0001")
    assert "issue_url: https://example.test/issues/{n}" in \
        (root / "luria.yaml").read_text()
    assert "# Proposals, one per change." in (root / "luria.yaml").read_text()


def test_one_document_per_value_in_declaration_order(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    migrate.run("0001")
    d = root / "record/areas.d"
    one, two, three = (_front(d / f"AREA-00{n}.md") for n in (1, 2, 3))
    assert (one["title"], one["slug"]) == ("Runtime", "runtime")
    assert "the execution engine" in str(one["summary"])
    assert (two["title"], two["slug"]) == ("storage", "storage")
    # Declared and unused still becomes a document — the vocabulary said
    # the value exists.
    assert three["slug"] == "network"
    assert one["status"] == "Active"
    assert "# AREA-001: Runtime" in (d / "AREA-001.md").read_text()


def test_an_open_vocabularys_undeclared_values_become_documents_too(
        tmp_path, monkeypatch):
    """A reference is closed by construction, so every value in use needs a
    target — declared ones first, then the rest alphabetically, the order an
    open field's pages already render in."""
    root = project(tmp_path, monkeypatch)
    text = (root / "luria.yaml").read_text().replace(
        "        vocabulary: area\n        many: true\n",
        "        vocabulary: area\n        many: true\n        closed: false\n")
    (root / "luria.yaml").write_text(text)
    _doc(root / "record/rfcs.d/RFC-004.md", "RFC-004", "Homemade",
         "area:\n- billing\n")
    config.reset()
    migrate.run("0001")
    assert _front(root / "record/areas.d/AREA-004.md")["slug"] == "billing"
    assert _front(root / "record/rfcs.d/RFC-004.md")["area"] == \
        ["AREA-billing"]


def test_fields_become_grouped_references(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    migrate.run("0001")
    raw = yaml.safe_load((root / "luria.yaml").read_text())
    rfc, note = raw["schemes"]["RFC"], raw["schemes"]["NOTE"]
    assert "area" not in rfc["fields"]
    # `required` is written out: a reference is required unless it says
    # otherwise, and a vocabulary field was optional unless it said so.
    assert rfc["references"]["area"] == {
        "scheme": "AREA", "many": True, "required": False, "group": True}
    assert note["references"]["area"] == {
        "scheme": "AREA", "many": False, "required": True, "group": True}
    assert rfc["axis"] == "area"


def test_documents_keep_a_readable_spelling(tmp_path, monkeypatch):
    """The value becomes the term's alias, so `runtime` reads `AREA-runtime`
    rather than `AREA-001`: typed, and still interpretable."""
    root = project(tmp_path, monkeypatch)
    migrate.run("0001")
    rfcs = root / "record/rfcs.d"
    assert _front(rfcs / "RFC-001.md")["area"] == ["AREA-runtime",
                                                   "AREA-storage"]
    assert _front(rfcs / "RFC-002.md")["area"] == ["AREA-runtime"]
    assert "area" not in _front(rfcs / "RFC-003.md")
    assert _front(root / "record/notes.d/NOTE-001.md")["area"] == \
        "AREA-storage"
    # The body is prose, and prose is never swept for a value's spelling.
    assert "area: this line is prose" in (rfcs / "RFC-001.md").read_text()


def test_the_promoted_record_lints_and_keeps_its_views(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    migrate.run("0001")
    config.reset()
    errors: list[str] = []
    lint.check_contracts(errors)
    assert errors == [], errors
    out = builder.outputs()
    page = out[root / "docs/rfcs/area/AREA-001.md"]
    assert "Runtime" in page and "RFC-001" in page and "RFC-002" in page
    assert root / "docs/notes/area/AREA-002.md" in out


def test_a_dry_run_writes_nothing(tmp_path, monkeypatch, capsys):
    root = project(tmp_path, monkeypatch)
    before = (root / "luria.yaml").read_text()
    migrate.run("0001", dry_run=True)
    said = capsys.readouterr().out
    assert "area -> AREA" in said
    assert "runtime -> AREA-001 (cited as AREA-runtime)" in said
    assert "RFC.area" in said and "NOTE.area" in said
    assert (root / "luria.yaml").read_text() == before
    assert not (root / "record/areas.d").exists()


def test_the_paths_can_be_named(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   spec_extra="  dir: record/terms.d\n  output: docs/terms\n")
    migrate.run("0001")
    assert (root / "record/terms.d/AREA-001.md").exists()


def test_an_existing_scheme_is_not_overwritten(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch,
            extra="  AREA:\n    dir: record/x.d\n    output: docs/x\n")
    with pytest.raises(SystemExit, match="already exists"):
        migrate.run("0001")


def test_a_status_vocabulary_is_not_promoted(tmp_path, monkeypatch):
    """`status` is the one field the machinery reads standing off; its words
    are not documents."""
    root = project(tmp_path, monkeypatch)
    (root / "record/migrations.d/0001-areas.yaml").write_text(
        SPEC.replace("vocabulary: area", "vocabulary: statuses") % "")
    with pytest.raises(SystemExit, match="status"):
        migrate.run("0001")


def test_an_unknown_vocabulary_is_refused(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    (root / "record/migrations.d/0001-areas.yaml").write_text(
        SPEC.replace("vocabulary: area", "vocabulary: nope") % "")
    with pytest.raises(SystemExit, match="nope"):
        migrate.run("0001")


@pytest.mark.parametrize("key", [
    "        default: [runtime]\n",
    "        groups:\n          one:\n            require: at-most-one\n"
    "            tags: [runtime, storage]\n",
])
def test_a_field_carrying_what_a_reference_cannot_is_refused(
        tmp_path, monkeypatch, key):
    """Refused, not dropped: a migration that silently loses a constraint
    reports success over a record that now checks less (DP-1)."""
    root = project(tmp_path, monkeypatch)
    text = (root / "luria.yaml").read_text().replace(
        "        vocabulary: area\n        many: true\n",
        "        vocabulary: area\n        many: true\n" + key)
    (root / "luria.yaml").write_text(text)
    config.reset()
    before = text
    with pytest.raises(SystemExit, match="RFC.area"):
        migrate.run("0001")
    assert (root / "luria.yaml").read_text() == before


def test_the_new_scheme_starts_like_a_declared_one(tmp_path, monkeypatch):
    """A template and a view stub, so the next term is `luria new area` — and
    term documents shaped like terms, not like decisions: no `tags` the
    scheme never declared, and the blurb as the body rather than the
    template's placeholder prose."""
    root = project(tmp_path, monkeypatch)
    migrate.run("0001")
    d = root / "record/areas.d"
    assert (d / "_template.md").exists() and (d / "README.stub").exists()
    one = (d / "AREA-001.md").read_text()
    assert "tags" not in _front(d / "AREA-001.md")
    assert one.rstrip().endswith("the execution engine")
    assert "Promoted from the `area` vocabulary, where it was `storage`." \
        in (d / "AREA-002.md").read_text()


def test_a_value_an_alias_cannot_spell_is_slugged(tmp_path, monkeypatch):
    """An alias tail is letters, digits, dots and hyphens. A value with a
    space or an underscore keeps its readable form, slugged — and the slug
    is what `slug:` records, since it is what the alias renders from."""
    root = project(tmp_path, monkeypatch)
    text = (root / "luria.yaml").read_text().replace(
        "    network: {}\n", "    network: {}\n    long_term: {}\n")
    (root / "luria.yaml").write_text(text)
    _doc(root / "record/rfcs.d/RFC-004.md", "RFC-004", "Plans",
         "area:\n- long_term\n")
    config.reset()
    migrate.run("0001")
    assert _front(root / "record/areas.d/AREA-004.md")["slug"] == "long-term"
    assert _front(root / "record/rfcs.d/RFC-004.md")["area"] == \
        ["AREA-long-term"]


def test_two_values_one_slug_is_refused(tmp_path, monkeypatch):
    """Two terms answering to one spelling would make the alias ambiguous,
    and an ambiguous alias resolves for one of them silently."""
    root = project(tmp_path, monkeypatch)
    text = (root / "luria.yaml").read_text().replace(
        "    network: {}\n", "    network: {}\n    net_work: {}\n"
        "    net work: {}\n")
    (root / "luria.yaml").write_text(text)
    config.reset()
    with pytest.raises(SystemExit, match="net-work"):
        migrate.run("0001")


def test_a_value_that_would_read_as_a_number_is_refused(
        tmp_path, monkeypatch):
    """`AREA-7` is a code, and a code outranks an alias — so a value `7`
    would silently cite whatever document is numbered 7."""
    root = project(tmp_path, monkeypatch)
    text = (root / "luria.yaml").read_text().replace(
        "    network: {}\n", "    network: {}\n    '7': {}\n")
    (root / "luria.yaml").write_text(text)
    config.reset()
    with pytest.raises(SystemExit, match="reads as a code"):
        migrate.run("0001")


def test_a_forbidden_when_rides_the_promotion(tmp_path, monkeypatch):
    """A reference takes the condition a vocabulary field did, in both
    senses (ADR-tmpt3gtr), so promotion carries it like `required_when`."""
    root = project(tmp_path, monkeypatch)
    cfg = root / "luria.yaml"
    cfg.write_text(cfg.read_text().replace(
        "        vocabulary: area\n        many: true\n",
        "        vocabulary: area\n        many: true\n"
        "        forbidden_when: {status: [Superseded]}\n"))
    config.reset()
    migrate.run("0001")
    raw = yaml.safe_load(cfg.read_text())
    assert raw["schemes"]["RFC"]["references"]["area"]["forbidden_when"] == {
        "status": ["Superseded"]}
