"""Per-scheme status vocabularies: `statuses.yaml` beside `tags.yaml`.

ADR-003 closed the status words and put a lint behind them, because an audit
found every prose-governed surface had drifted. The layer it left uncovered is
what each word *means* in a given scheme — prose only, in a template comment —
and downstream that layer drifted exactly as ADR-003 would predict.

These tests pin the three things that follow from fixing it one level up and
not further: declaring nothing changes nothing, declaring something narrows the
five words without extending them, and the meaning reaches the page a reader
actually opens.

`VP` rather than a real prefix, per the fixture-code rule: a fixture that
borrows a live sequence's prefix is the hazard that rule exists for.
"""

from __future__ import annotations

from pathlib import Path

from luria import adr_index, config, lint, statuses


def _project(root: Path, monkeypatch) -> None:
    (root / "record" / "values.d").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.VP]\n'
        'dir = "record/values.d"\n'
        'render = "index"\n'
        'output = "docs/values"\n')
    monkeypatch.setenv("LURIA_ROOT", str(root))
    config.reset()


def _value(root: Path, number: int, status: str = "Active") -> Path:
    path = root / "record" / "values.d" / f"VP-{number:03d}.md"
    path.write_text(
        f"---\nstatus: {status}\ntitle: 'A value'\ntags:\n- craft\n"
        f"date: '2026-01-01'\n---\n\n# VP-{number:03d}: A value\n\nBody.\n")
    return path


def _declare(root: Path, text: str) -> None:
    (root / "record" / "values.d" / "statuses.yaml").write_text(text)


def _scheme():
    return config.current().schemes["VP"]


def test_declaring_nothing_leaves_every_word_available(tmp_path, monkeypatch):
    """The default posture, and it must be silent in both directions.

    A project that has not thought about this must not be told it has a
    problem, and must not be handed a legend it never asked for."""
    _project(tmp_path, monkeypatch)
    for n, s in enumerate(("Active", "Proposed", "Deferred", "Superseded",
                           "Rejected"), start=1):
        _value(tmp_path, n, s)
    errors: list[str] = []
    lint.check_frontmatter(errors)
    assert errors == []
    assert statuses.legend(_scheme()) == ""


def test_a_declared_vocabulary_narrows_the_five(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _declare(tmp_path, "Active:\n  blurb: in force\nRejected:\n  blurb: wrong\n")
    _value(tmp_path, 1, "Active")
    _value(tmp_path, 2, "Deferred")
    errors: list[str] = []
    lint.check_frontmatter(errors)
    assert len(errors) == 1
    assert "VP-002" in errors[0] and "'Deferred'" in errors[0]


def test_a_trailing_note_does_not_defeat_the_check(tmp_path, monkeypatch):
    """ADR-003 allows `Superseded — by X`, and the note qualifies the word
    rather than being part of it. Comparing the whole string would reject every
    annotated status a project declared."""
    _project(tmp_path, monkeypatch)
    _declare(tmp_path, "Active:\n  blurb: in force\nSuperseded:\n  blurb: replaced\n")
    _value(tmp_path, 1, "Superseded — by [VP-002](VP-002.md)")
    _value(tmp_path, 2, "Active")
    errors: list[str] = []
    lint.check_frontmatter(errors)
    assert errors == []

    _value(tmp_path, 3, "Deferred — until the audit")
    errors = []
    lint.check_frontmatter(errors)
    assert len(errors) == 1 and "'Deferred'" in errors[0]


def test_the_vocabulary_cannot_be_extended(tmp_path, monkeypatch):
    """The one thing this feature must not become. A file naming `Accepted`
    would render a legend and silence nothing, so it would look like it was
    working — which is why this is an error rather than a warning."""
    _project(tmp_path, monkeypatch)
    _declare(tmp_path, "Active:\n  blurb: in force\nAccepted:\n  blurb: ditto\n")
    _value(tmp_path, 1)
    errors: list[str] = []
    lint.check_status_vocabulary(errors)
    assert len(errors) == 1
    assert "'Accepted'" in errors[0] and "closed" in errors[0]


def test_the_meaning_reaches_the_generated_index(tmp_path, monkeypatch):
    """The point of the feature. A template comment is read once, by whoever
    mints a record; the index is read by everyone else, and until now its
    status column was five bare words with no way to learn what they meant
    here."""
    _project(tmp_path, monkeypatch)
    _declare(tmp_path,
             "Active:\n  label: Asserted\n  blurb: the record asserts this\n"
             "Rejected:\n  label: Defeated\n"
             "  blurb: the corpus contains it and it is wrong\n")
    _value(tmp_path, 1, "Active")
    scheme = _scheme()
    page = adr_index.render_index(adr_index.load_scheme(scheme), [], scheme)
    assert "Asserted" in page and "The record asserts this" in page
    assert "Defeated" in page, "a declared status renders even when unused"
    assert page.index("| Status |") < page.index("| # | Title |"), \
        "the legend explains the column, so it belongs above the table"


def test_an_undeclared_status_is_not_reported_when_nothing_is_declared(
        tmp_path, monkeypatch):
    """Guards the inert default against the obvious refactor that breaks it —
    treating an absent file as an empty vocabulary would reject every record in
    every project that has not adopted this."""
    _project(tmp_path, monkeypatch)
    _value(tmp_path, 1, "Rejected")
    assert not statuses.undeclared(_scheme(), "Rejected")
    assert statuses.declared(_scheme()) == {}


# ── The inert-status report (#104) ──────────────────────────────────────

def _values(root: Path, n: int, status: str = "Active") -> None:
    for i in range(1, n + 1):
        _value(root, i, status)


def test_a_uniform_status_field_is_reported(tmp_path, monkeypatch):
    """The finding: nothing here has ever been judged.

    Worth catching because `active` is what `retired-citations` reads. A scheme
    where nothing is ever retired has an enforcement mechanism that cannot
    fire, and its green build says only that no one has looked."""
    _project(tmp_path, monkeypatch)
    _values(tmp_path, 12)
    hit = statuses.uniform(_scheme())
    assert hit == ("Active", 12)
    assert "inert-status" in {n for n, _, _ in lint.status_sections()}


def test_one_dissenting_record_clears_it(tmp_path, monkeypatch):
    """The distinction is live as soon as anything varies. This is not a rule
    about proportion — a corpus whose claims all survive is legitimate — so a
    single retirement is enough to say a judgment is being made."""
    _project(tmp_path, monkeypatch)
    _values(tmp_path, 12)
    _value(tmp_path, 12, "Rejected")
    assert statuses.uniform(_scheme()) is None


def test_a_trailing_note_does_not_look_like_variety(tmp_path, monkeypatch):
    """`Superseded — by X` and `Superseded — by Y` are one status wearing two
    strings. Comparing whole values would call that variety and clear a scheme
    that has none."""
    _project(tmp_path, monkeypatch)
    for i in range(1, 13):
        _value(tmp_path, i, f"Active — since revision {i}")
    assert statuses.uniform(_scheme()) == ("Active", 12)


def test_a_young_scheme_is_not_reported(tmp_path, monkeypatch):
    """Below the floor, uniformity is evidence of nothing. Three records all in
    force is a scheme someone started last week."""
    _project(tmp_path, monkeypatch)
    _values(tmp_path, 3)
    assert statuses.uniform(_scheme()) is None


def test_a_scheme_declaring_one_status_has_said_so_on_purpose(tmp_path,
                                                              monkeypatch):
    """The interesting interaction with #102. A project that declares exactly
    one status has answered this question already, and reporting it would be
    telling it off for doing the configuration right."""
    _project(tmp_path, monkeypatch)
    _declare(tmp_path, "Active:\n  blurb: in force\n")
    _values(tmp_path, 12)
    assert statuses.uniform(_scheme()) is None


def test_a_document_rendered_scheme_is_exempt(tmp_path, monkeypatch):
    """A design-principles page where every principle is in force is the
    expected state, not a smell — principles are superseded by revision, and
    `version:` carries that."""
    _project(tmp_path, monkeypatch)
    (tmp_path / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.VP]\n'
        'dir = "record/values.d"\n'
        'render = "document"\n'
        'output = "docs/values.md"\n')
    config.reset()
    _values(tmp_path, 12)
    assert statuses.uniform(_scheme()) is None


def test_the_class_is_failable(tmp_path, monkeypatch):
    assert "inert-status" in lint.FAILABLE
