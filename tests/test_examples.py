"""The worked configurations in `examples/` are run, not just read.

A `luria.toml` block in a guide is a claim nobody executes, and this project's
founding observation is that every surface governed by prose alone had
drifted. So each example is built into a temporary directory, the real
`luria index` and `luria lint` run against it, and the capability it advertises
is asserted.

Three of these tests assert *limits* rather than features. They exist because
each was discovered by running a configuration the documentation, at the time,
said would work — and a limit nobody has pinned is one the docs will quietly
start lying about again.

The last group is the opposite: capabilities that were *promised* and absent
until these examples found them missing. Reference checking used to know three
hardcoded patterns, so a configured `RFC` scheme was rendered, scaffolded and
indexed — and never linted.
"""
import shutil
from pathlib import Path

import pytest

from luria import adr_index, config, doc_refs, lint

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
NAMES = ["rfcs-and-specs", "collocated", "many-journals", "external-citations"]


@pytest.fixture
def example(tmp_path, monkeypatch):
    """Build one example into a temp tree and point the config at it.

    Copied rather than run in place: generating into the repository would
    leave committed views nobody regenerates, which is the exact failure the
    examples argue against."""
    def build(name: str) -> Path:
        root = tmp_path / name
        shutil.copytree(EXAMPLES / name, root)
        monkeypatch.setenv("LURIA_ROOT", str(root))
        config.reset()
        adr_index.run()
        return root
    return build


def lint_errors() -> list[str]:
    """`luria lint`'s failures, as a list rather than an exit code."""
    errors: list[str] = []
    lint.check_docs_index(errors)
    lint.check_frontmatter(errors)
    lint.check_generated_index(errors)
    lint.check_journals(errors)
    lint.check_bare_refs(errors)
    lint.check_wikilinks(errors)
    return errors


@pytest.mark.parametrize("name", NAMES)
def test_every_example_lints_clean(example, name):
    """The headline claim: these are configurations that work."""
    example(name)
    assert lint_errors() == []


@pytest.mark.parametrize("name", NAMES)
def test_every_example_render_is_stable(example, name):
    """A second `luria index` changes nothing — the views are a pure function
    of the sources, which is what makes staleness detectable at all."""
    example(name)
    first = adr_index.outputs()
    assert all(p.read_text() == text for p, text in first.items())


def test_two_schemes_render_in_their_two_shapes(example):
    """`render = "index"` browses; `render = "document"` reads whole. Neither
    is a special case, and neither is about decisions."""
    root = example("rfcs-and-specs")

    index = (root / "docs" / "rfcs" / "README.md").read_text()
    assert "RFC-001" in index
    assert (root / "docs" / "rfcs" / "tags" / "protocol.md").exists()

    document = (root / "docs" / "interfaces.md").read_text()
    assert "id, a kind and a payload" in document, "the body, not just a link"
    # A document render renumbers codes into the reader's numbering and emits
    # a stable anchor keyed to the number — `SPEC-001` becomes `## 1.` at
    # `#spec-1`, which is what a remote's `anchor` template constructs against.
    assert '<a name="spec-1"></a>' in document
    assert document.startswith("# SPEC documents"), (
        "a scheme with no README.stub is titled after itself, not after "
        "this package's principles")

    cfg = config.current()
    assert set(cfg.schemes) >= {"RFC", "SPEC"}
    assert cfg.schemes["SPEC"].render == "document"


def test_a_view_can_render_beside_its_sources(example):
    """Adoption never has to begin by moving files.

    Note what the example has to write to get this: `output` equal to `dir`,
    not `output` omitted. Omitting it works for a scheme you invent, and does
    *not* work for `ADR` — see the limit pinned at the bottom of this file."""
    root = example("collocated")
    assert (root / "decisions" / "README.md").exists()
    assert (root / "decisions" / "tags" / "record.md").exists()
    assert not (root / "docs" / "decisions").exists()


def test_three_journals_at_three_granularities(example):
    """`journals` is a family, not a fixed devlog."""
    root = example("many-journals")
    assert {j for j in config.current().journals} >= {
        "devlog", "incidents", "meetings"}

    assert (root / "docs" / "devlog" / "2026-03.md").exists()     # month
    assert (root / "docs" / "incidents" / "2026.md").exists()     # year
    assert (root / "docs" / "meetings" / "2026-03-12.md").exists()  # day


def test_uid_remotes_link_things_that_are_not_records(example):
    """The capability that has nothing to do with decision records: a regex
    and a URL template make arXiv ids, ticket keys and CVEs first-class,
    linted references."""
    root = example("external-citations")
    source = root / "record" / "notes.d" / "NOTE-001.md"

    linked, count = doc_refs.linkify(
        "Method: ARXIV-2301.07041, ticket JIRA:PLAT-88, hold CVE-2024-3094.",
        source)
    assert count == 3
    assert "https://arxiv.org/abs/2301.07041" in linked
    assert "https://acme.atlassian.net/browse/PLAT-88" in linked
    assert "https://nvd.nist.gov/vuln/detail/CVE-2024-3094" in linked


def test_a_uid_remote_can_move_its_delimiter(example):
    """Ticket keys contain the default delimiter themselves, so `JIRA:PLAT-88`
    has to be spellable. Without `delim`, the prefix and the key are
    indistinguishable."""
    example("external-citations")
    assert config.current().remotes["JIRA"].delim == ":"


# --- the two limits, pinned ---------------------------------------------

def test_active_selects_a_status_it_does_not_define(example):
    """`active = "Accepted"` does not make `Accepted` legal.

    The five statuses are closed and lint-enforced on purpose (ADR-003) — an
    audit found thirty spellings of "this one counts" across 121 files. So
    `active` picks the in-force state *from* the vocabulary. Documented in
    `examples/README.md`; pinned here so it cannot quietly stop being true."""
    root = example("rfcs-and-specs")
    rfc = root / "record" / "rfcs.d" / "RFC-001.md"
    rfc.write_text(rfc.read_text().replace("status: Active", "status: Accepted"))

    errors: list[str] = []
    lint.check_frontmatter(errors)
    assert any("nonstandard status" in e for e in errors)


def test_omitting_output_does_not_collocate_the_shipped_adr_scheme(example):
    """The same root cause as the test below, and the one that bites hardest.

    Config merges over `DEFAULTS`, and the shipped `[luria.schemes.ADR]`
    carries `output = "docs/decisions"`. So an existing project that points
    `dir` at its decisions and omits `output` — the documented way to keep an
    existing layout — silently gets its index relocated to `docs/decisions/`.
    The workaround is to set `output` equal to `dir`, which is what
    `examples/collocated` does and says."""
    example("rfcs-and-specs")            # sets no `output` for ADR at all
    adr = config.current().schemes["ADR"]
    assert adr.output is not None, "inherited from DEFAULTS, not unset"
    assert adr.output.name == "decisions"
    assert adr.view != adr.dir, "so the view is NOT beside the sources"


def test_the_shipped_adr_scheme_cannot_be_removed(example):
    """Config merges over the defaults, so `[luria.schemes.ADR]` is always
    present. A project that wants only RFCs still carries an ADR scheme and
    still renders an empty decision index.

    Asserted rather than wished away: `examples/README.md` tells adopters
    this, and a doc that states a limit has to be right about it."""
    root = example("rfcs-and-specs")
    assert "ADR" in config.current().schemes, "no way to opt out today"
    assert (root / "docs" / "decisions" / "README.md").exists()


# --- reference checking is scheme-driven ---------------------------------

def test_a_configured_scheme_is_linted_like_any_other(example):
    """The promise ADR-006 made, at the layer that was missing it.

    `find_refs` used to know three hardcoded patterns — ADR, the `#` spelling
    of DP, and issues. A project that configured `RFC` got indexes, tag pages
    and `luria new rfc`, and no reference checking at all: `RFC-7` in prose was
    neither linked nor reported. Rendering was general; the linter was not."""
    root = example("rfcs-and-specs")
    source = root / "record" / "specs.d" / "SPEC-001.md"

    refs = doc_refs.find_refs("see RFC-001 and SPEC-001", source)
    assert [(r.kind, r.prefix, r.num) for r in refs] == [
        ("scheme", "RFC", 1), ("scheme", "SPEC", 1)]


def test_cross_scheme_references_resolve_to_each_shape(example):
    """An index-rendered scheme resolves to the document's own file; a
    document-rendered one to an anchor in the assembled page. Both from the
    right base, which is where the text *renders*, not where it lives."""
    root = example("rfcs-and-specs")

    from_rfc, _ = doc_refs.linkify(
        "See SPEC-001.", root / "record" / "rfcs.d" / "RFC-001.md")
    assert "interfaces.md#spec-1" in from_rfc

    from_spec, _ = doc_refs.linkify(
        "Motivated by RFC-001.", root / "record" / "specs.d" / "SPEC-001.md")
    assert "rfcs.d/RFC-001.md" in from_spec


def test_the_dp_code_spelling_is_found_not_only_the_prose_one(example):
    """`CLAUDE.md` and the scaffolded template both tell contributors to write
    the bare code and let the fixer spell the target. For `DP-6` that was
    false: `DP_RE` matched only `design principles #6`, so a bare `DP-6` was
    neither linked nor reported — the worst of the three behaviours."""
    root = example("rfcs-and-specs")
    source = root / "record" / "specs.d" / "SPEC-001.md"
    assert doc_refs.find_refs("per SPEC-1 exactly", source)
    assert doc_refs.find_refs("per SPEC 1 exactly", source)


def test_a_document_never_links_to_itself(example):
    """A fragment is a different file from the page it assembles into, so the
    `target == source` test that protects an index-rendered scheme does not
    fire here. Without an explicit guard a principle's own `# DP-001:` heading
    becomes a link, and the title check then fails on a heading that no longer
    matches its frontmatter — which is exactly what happened first."""
    root = example("rfcs-and-specs")
    spec = root / "record" / "specs.d" / "SPEC-001.md"
    linked, count = doc_refs.linkify(spec.read_text(), spec)
    assert count == 0
    assert linked.count("# SPEC-001:") == 1
