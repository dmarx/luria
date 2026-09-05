"""One compiled contract per scheme (#141).

`requires`, `references` and `tag_groups` were three lint passes, each
re-parsing every document's frontmatter and each spelling its own provenance
by hand. They compile here into one representation: the obligations a scheme
places on an entry, each carrying where it was declared. The checks are the
same; what changes is that there is one place to ask "what does this scheme
demand, and why?"
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import config, contract, lint


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def doc(root: Path, rel: str, *, code: str, tags: list[str],
        extra: str = "") -> Path:
    front = ["---", "status: Active", f"title: 'Entry {code}'", "tags:"]
    front += [f"- {t}" for t in tags] or ["- record"]
    front += ["date: '2026-01-01'"]
    if extra:
        front.append(extra)
    front += ["---", "", f"# {code}: Entry {code}", "", "Body."]
    return write(root, rel, "\n".join(front) + "\n")


def project(tmp_path, monkeypatch, sota_extra: str = "") -> Path:
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


def sota() -> contract.Contract:
    return contract.for_scheme(config.current().schemes["SOTA"])


def declared(c: contract.Contract) -> list:
    """The scheme's own fields — every scheme also carries the built-ins."""
    return [f for f in c.fields if not f.builtin]


# --- compilation ----------------------------------------------------------

def test_a_scheme_declaring_nothing_has_an_empty_contract(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    c = sota()
    assert declared(c) == [] and c.groups == ()
    assert c.empty


def test_requires_compiles_to_a_required_untyped_field(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, 'requires = ["arxiv"]')
    field, = declared(sota())
    assert field.name == "arxiv"
    assert field.required and field.reference is None


def test_a_reference_compiles_to_a_typed_field(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch,
            '[luria.schemes.SOTA.references]\nsource = { scheme = "LIT" }')
    field, = declared(sota())
    assert field.name == "source"
    assert field.required and field.reference == "LIT"


def test_an_optional_reference_is_typed_but_not_required(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch,
            '[luria.schemes.SOTA.references]\n'
            'source = { scheme = "LIT", required = false }')
    field, = declared(sota())
    assert not field.required and field.reference == "LIT"


def test_a_field_in_both_tables_is_one_obligation(tmp_path, monkeypatch):
    """ADR-060 noted that a field in both `requires` and `references` was
    checked twice and reported twice. Composition is intersection: required
    and required is required, and the reference supplies the type. One
    obligation, carrying both declarations as its provenance."""
    project(tmp_path, monkeypatch,
            'requires = ["source"]\n'
            '[luria.schemes.SOTA.references]\nsource = { scheme = "LIT" }')
    field, = declared(sota())
    assert field.required and field.reference == "LIT"
    assert len(field.because) == 2


def test_every_obligation_says_where_it_was_declared(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch,
            'requires = ["arxiv"]\n'
            '[luria.schemes.SOTA.references]\nsource = { scheme = "LIT" }\n'
            '[luria.schemes.SOTA.tag_groups.axis]\n'
            'tags = ["a", "b"]\nrequire = "exactly-one"')
    c = sota()
    assert {f.name for f in declared(c)} == {"arxiv", "source"}
    for field in declared(c):
        assert field.because and all("luria.toml" in b for b in field.because)
    group, = c.groups
    assert group.name == "axis"


# --- one pass, same findings ----------------------------------------------

def test_one_pass_reports_fields_and_groups_together(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   'requires = ["arxiv"]\n'
                   '[luria.schemes.SOTA.references]\n'
                   'source = { scheme = "LIT" }\n'
                   '[luria.schemes.SOTA.tag_groups.axis]\n'
                   'tags = ["a", "b"]\nrequire = "exactly-one"')
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001",
        tags=["a", "b"], extra="source: ADR-001")
    errors: list[str] = []
    lint.check_contracts(errors)
    assert any("no `arxiv:`" in e and "SOTA scheme requires it" in e
               for e in errors), errors
    assert any("`source: ADR-001` is not a LIT code" in e for e in errors), errors
    assert any("`axis` wants exactly one" in e for e in errors), errors
    assert len(errors) == 3


def test_a_doubly_declared_missing_field_is_reported_once(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   'requires = ["source"]\n'
                   '[luria.schemes.SOTA.references]\n'
                   'source = { scheme = "LIT" }')
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001", tags=[])
    errors: list[str] = []
    lint.check_contracts(errors)
    assert len(errors) == 1, errors
    assert "no `source:`" in errors[0] and "LIT reference" in errors[0]


def test_a_satisfied_contract_is_silent(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   'requires = ["arxiv"]\n'
                   '[luria.schemes.SOTA.references]\n'
                   'source = { scheme = "LIT" }')
    doc(root, "record/literature.d/LIT-001.md", code="LIT-001", tags=[])
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001", tags=[],
        extra="source: LIT-001\narxiv: '2301.00001'")
    errors: list[str] = []
    lint.check_contracts(errors)
    assert errors == []


def test_the_shipped_record_is_clean_through_the_contract():
    """No behaviour change on the corpus that runs this: every scheme here
    declares no contract, so the pass compiles to nothing and finds nothing."""
    for scheme in config.current().schemes.values():
        assert contract.for_scheme(scheme).empty
    errors: list[str] = []
    lint.check_contracts(errors)
    assert errors == []


# --- provenance, rendered (#141 step D) -----------------------------------

def test_a_finding_names_the_key_that_declared_the_obligation(tmp_path, monkeypatch):
    """Not just the file: the key. When a second authoring surface exists,
    "luria.toml" alone would send the reader to the wrong table."""
    root = project(tmp_path, monkeypatch,
                   'requires = ["arxiv"]\n'
                   '[luria.schemes.SOTA.references]\n'
                   'source = { scheme = "LIT" }')
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001", tags=[],
        extra="source: ADR-001")
    errors: list[str] = []
    lint.check_contracts(errors)
    assert any("(luria.toml: schemes.SOTA.requires)" in e for e in errors), errors
    assert any("is not a LIT code" in e
               and "(luria.toml: schemes.SOTA.references.source)" in e
               for e in errors), errors


def test_a_merged_obligation_names_both_keys(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   'requires = ["source"]\n'
                   '[luria.schemes.SOTA.references]\n'
                   'source = { scheme = "LIT" }')
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001", tags=[])
    errors: list[str] = []
    lint.check_contracts(errors)
    e, = errors
    assert "schemes.SOTA.requires" in e and "schemes.SOTA.references.source" in e


def test_a_group_finding_names_its_key_and_derived_membership(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   '[luria.schemes.SOTA.tag_groups.axis]\n'
                   'tags = ["a", "b"]\nrequire = "exactly-one"')
    doc(root, "record/practices.d/SOTA-001.md", code="SOTA-001", tags=[])
    errors: list[str] = []
    lint.check_contracts(errors)
    e, = errors
    assert "(luria.toml: schemes.SOTA.tag_groups.axis)" in e


def test_describe_is_one_renderer_for_the_whole_contract(tmp_path, monkeypatch):
    """What the record page prints and what a finding cites are the same
    words from the same place, so they cannot drift apart (DP-4)."""
    project(tmp_path, monkeypatch,
            'requires = ["arxiv"]\n'
            '[luria.schemes.SOTA.references]\n'
            'source = { scheme = "LIT" }\n'
            'cites = { scheme = "LIT", required = false }\n'
            '[luria.schemes.SOTA.tag_groups.axis]\n'
            'tags = ["a", "b"]\nrequire = "exactly-one"\nexcluded_by = ["z"]')
    lines = contract.describe(sota())
    text = "\n".join(lines)
    assert "`arxiv`" in text and "required" in text
    assert "`source`" in text and "`LIT` code" in text
    assert "`cites`" in text and "optional" in text
    assert "`axis`" in text and "exactly one of `a`, `b`" in text and "`z`" in text
    for key in ("schemes.SOTA.requires", "schemes.SOTA.references.source",
                "schemes.SOTA.references.cites", "schemes.SOTA.tag_groups.axis"):
        assert key in text, key
    assert len(lines) == 4


def test_describe_of_an_empty_contract_is_empty(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    assert contract.describe(sota()) == []


# --- one code or many (#141, the world-building record's report) ---------

def scenes(tmp_path, monkeypatch, many: str = "many = true") -> Path:
    write(tmp_path, "luria.toml", f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"
[luria.schemes.SCENE]
dir = "record/scenes.d"
[luria.schemes.SCENE.references]
follows = {{ scheme = "SCENE", {many} }}
""")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    for n in (1, 2):
        doc(tmp_path, f"record/scenes.d/SCENE-00{n}.md", code=f"SCENE-00{n}", tags=[])
    return tmp_path


def scene(root: Path, extra: str) -> Path:
    return doc(root, "record/scenes.d/SCENE-003.md", code="SCENE-003", tags=[],
               extra=extra)


def findings() -> list[str]:
    """Contract findings for the document under test. The two supporting
    scenes declare no `follows` of their own and are not what is being
    asked about."""
    errors: list[str] = []
    lint.check_contracts(errors)
    return [e for e in errors if "SCENE-003" in e]


def test_a_reference_declares_whether_it_holds_one_code_or_many(tmp_path, monkeypatch):
    scenes(tmp_path, monkeypatch)
    ref, = config.current().schemes["SCENE"].references
    assert ref.many
    field, = declared(contract.for_scheme(config.current().schemes["SCENE"]))
    assert field.many and field.reference == "SCENE"


def test_the_default_is_one(tmp_path, monkeypatch):
    scenes(tmp_path, monkeypatch, many="required = true")
    ref, = config.current().schemes["SCENE"].references
    assert not ref.many


def test_a_list_where_one_code_was_declared_is_a_finding(tmp_path, monkeypatch):
    """The reported defect: a list was stringified, its first code checked
    and the rest ignored, silently. Structured input coerced to prose and
    half-read is worse than no support at all."""
    root = scenes(tmp_path, monkeypatch, many="required = true")
    scene(root, "follows:\n- SCENE-001\n- SCENE-999")
    e, = findings()
    assert "`follows:` holds 2 values" in e and "one SCENE reference" in e
    assert "many = true" in e
    assert "SCENE-999" not in e, "a malformed shape is not half-interpreted"


def test_every_element_of_a_plural_reference_is_checked(tmp_path, monkeypatch):
    root = scenes(tmp_path, monkeypatch)
    scene(root, "follows:\n- SCENE-001\n- SCENE-999\n- 'a scene I meant to write'")
    errors = findings()
    assert any("`follows: SCENE-999` resolves to no SCENE document" in e
               for e in errors), errors
    assert any("is not a code" in e for e in errors), errors
    assert len(errors) == 2


def test_a_plural_reference_that_resolves_is_silent(tmp_path, monkeypatch):
    root = scenes(tmp_path, monkeypatch)
    scene(root, "follows:\n- SCENE-001\n- SCENE-002")
    assert findings() == []


def test_a_required_plural_reference_may_not_be_empty(tmp_path, monkeypatch):
    root = scenes(tmp_path, monkeypatch, many="many = true, required = true")
    scene(root, "follows: []")
    e, = findings()
    assert "no `follows:`" in e


def test_an_optional_plural_reference_may_be_empty_or_absent(tmp_path, monkeypatch):
    root = scenes(tmp_path, monkeypatch, many="many = true, required = false")
    scene(root, "follows: []")
    assert findings() == []
    scene(root, "")
    assert findings() == []


def test_a_single_code_in_a_plural_field_is_a_list_of_one(tmp_path, monkeypatch):
    """Unambiguous, so accepted: one value is fully interpreted. The
    asymmetry with the scalar case is deliberate — a list in a scalar field
    leaves the tool guessing which element was meant."""
    root = scenes(tmp_path, monkeypatch)
    scene(root, "follows: SCENE-001")
    assert findings() == []


def test_describe_says_one_or_many(tmp_path, monkeypatch):
    scenes(tmp_path, monkeypatch)
    line, = contract.describe(contract.for_scheme(config.current().schemes["SCENE"]))
    assert "one or more `SCENE` codes" in line


# --- one of several fields (#144 review) ---------------------------------

def papers(tmp_path, monkeypatch, group: str = 'fields = ["arxiv", "doi", "url"]') -> Path:
    write(tmp_path, "luria.toml", f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"
[luria.schemes.LIT]
dir = "record/literature.d"
[luria.schemes.LIT.field_groups.source]
{group}
""")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def paper(root: Path, extra: str = "") -> Path:
    return doc(root, "record/literature.d/LIT-001.md", code="LIT-001", tags=[],
               extra=extra)


def lit_findings() -> list[str]:
    errors: list[str] = []
    lint.check_contracts(errors)
    return errors


def test_a_field_group_is_read_with_its_rule(tmp_path, monkeypatch):
    papers(tmp_path, monkeypatch)
    group, = config.current().schemes["LIT"].field_groups
    assert (group.name, group.fields, group.require) == \
        ("source", ("arxiv", "doi", "url"), "at-least-one")


def test_at_least_one_of_the_fields_satisfies_the_group(tmp_path, monkeypatch):
    """A paper never posted to arXiv still has a DOI, or failing that a URL:
    the requirement is *a source*, and several fields can be one."""
    root = papers(tmp_path, monkeypatch)
    paper(root, "doi: '10.1000/example'")
    assert lit_findings() == []
    paper(root, "url: 'https://example.org/report'")
    assert lit_findings() == []


def test_none_of_the_fields_is_a_finding_that_names_them_all(tmp_path, monkeypatch):
    root = papers(tmp_path, monkeypatch)
    paper(root)
    e, = lit_findings()
    assert "no `source`" in e and "one of `arxiv:`, `doi:`, `url:`" in e
    assert "(luria.toml: schemes.LIT.field_groups.source)" in e


def test_an_empty_field_does_not_count(tmp_path, monkeypatch):
    root = papers(tmp_path, monkeypatch)
    paper(root, "arxiv: ''")
    assert len(lit_findings()) == 1


def test_exactly_one_and_at_most_one_are_rules_too(tmp_path, monkeypatch):
    root = papers(tmp_path, monkeypatch,
                  'fields = ["arxiv", "doi"]\nrequire = "exactly-one"')
    paper(root, "arxiv: '1'\ndoi: '2'")
    e, = lit_findings()
    assert "exactly one of" in e and "has `arxiv:`, `doi:`" in e
    root = papers(tmp_path, monkeypatch,
                  'fields = ["arxiv", "doi"]\nrequire = "at-most-one"')
    paper(root)
    assert lit_findings() == []


def test_a_group_with_no_fields_or_a_bad_rule_is_a_config_error(tmp_path, monkeypatch):
    papers(tmp_path, monkeypatch, "fields = []")
    with pytest.raises(ValueError, match="lists no fields"):
        config.current()
    config.reset()
    papers(tmp_path, monkeypatch, 'fields = ["arxiv"]\nrequire = "one"')
    with pytest.raises(ValueError, match="require = 'one'"):
        config.current()


def test_describe_lists_the_group_with_its_provenance(tmp_path, monkeypatch):
    papers(tmp_path, monkeypatch)
    line, = contract.describe(contract.for_scheme(config.current().schemes["LIT"]))
    assert line.startswith("`source` — at least one of `arxiv`, `doi`, `url`")
    assert "schemes.LIT.field_groups.source" in line


# --- remote codes in reference fields --------------------------------------

REMOTES = '''
[luria.remotes.ARXIV]
uid = "(\\\\d{4})[.:](\\\\d{4,5})"
url = "https://arxiv.org/abs/{1}.{2}"

[luria.remotes.DOI]
uid = "10\\\\.\\\\d{4,9}/[^\\\\s\\\\]\\\\)>,;]+"
delim = ":"
url = "https://doi.org/{uid}"
'''


def test_a_remote_code_is_read_whole(tmp_path, monkeypatch):
    """A uid remote's tail is opaque, so the scheme-shaped pattern read
    `ARXIV-2110` out of the first and nothing out of the second."""
    project(tmp_path, monkeypatch, REMOTES)
    assert contract.reference_code("ARXIV-2110.08058") == "ARXIV-2110.08058"
    assert contract.reference_code("DOI:10.1145/3600006.3613165") == "DOI:10.1145/3600006.3613165"
    assert contract.reference_code(
        "[ARXIV-2110.08058](https://arxiv.org/abs/2110.08058)") == "ARXIV-2110.08058"
    assert contract.reference_code("LIT-041") == "LIT-041"
    assert contract.reference_code("[LIT-041](LIT-041.md)") == "LIT-041"


def test_a_scheme_code_is_still_read_without_any_remote(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    assert contract.reference_code("LIT-041") == "LIT-041"
    assert contract.reference_code("not a code") is None


def test_superseded_by_may_name_remote_documents(tmp_path, monkeypatch):
    """The docstring always said "or a remote code"; the reader truncated it
    before the check could see it, so a paper superseded by a paper failed
    as "names no scheme or remote"."""
    root = project(tmp_path, monkeypatch, REMOTES)
    doc(root, "record/literature.d/LIT-001.md", code="LIT-001", tags=["record"],
        extra="superseded_by:\n- ARXIV-2110.08058\n- DOI:10.1145/3600006.3613165")
    errors: list[str] = []
    lint.check_contracts(errors)
    assert not [e for e in errors if "superseded_by" in e], errors


def test_an_undeclared_prefix_in_superseded_by_is_still_a_finding(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, REMOTES)
    doc(root, "record/literature.d/LIT-001.md", code="LIT-001", tags=["record"],
        extra="superseded_by: FAKE-2110.08058")
    errors: list[str] = []
    lint.check_contracts(errors)
    assert any("superseded_by" in e and "names no scheme or remote" in e for e in errors), errors
