"""`[luria.schemes.X] cite` — where a citation of this scheme's code points.

A scheme rendered as one assembled document has two addresses for each of its
sources: the source's own page, and an anchor in the view it renders into.
Before this key there was no choice — every citation resolved to the anchor,
which is fine in a repository and fragile on a published site. Quartz, to name
the one that bit: `<a name="dp-3"></a>` is raw HTML, its remark→hast pipeline
drops it, so every such link lands on a page that has no such anchor. The page
always exists; the anchor exists only if the publisher keeps it.

So the target is the project's to choose. UNSET resolves to what the scheme
already does — "view" for a document scheme, "page" for an index scheme, whose
sources have no second address — which is why adding the key changes nothing
for a project that does not set it. `cite = "page"` becomes the better default
once a document scheme's sources are published as pages; until then it sends
citations out to the repository instead of into the site.

The tests below pin both directions through BOTH resolvers — `wikilink_target`
for `[[DP-2]]` and `resolve` for a bare prose `DP-2` — because they are
separate code paths that have to agree, and a reader cannot tell which one
wrote a link by looking at the output.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import config, doc_refs


def _project(root: Path, monkeypatch, cite: str | None = None,
             render: str = "document") -> None:
    """A principles-shaped project: sources in `record/principles.d`, assembled
    into `docs/design-principles.md`."""
    (root / "record" / "principles.d").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    cite_line = f'cite = "{cite}"\n' if cite is not None else ""
    output = 'output = "docs/design-principles.md"\n' if render == "document" \
        else 'output = "docs/principles"\n'
    (root / "luria.toml").write_text(
        "[luria]\n"
        "[luria.schemes.DP]\n"
        'dir = "record/principles.d"\n'
        f'render = "{render}"\n'
        f"{output}{cite_line}")
    monkeypatch.setenv("LURIA_ROOT", str(root))
    config.reset()


def _principle(root: Path, number: int, title: str) -> Path:
    path = root / "record" / "principles.d" / f"DP-{number:03d}.md"
    path.write_text(f"---\ntitle: '{title}'\nstatus: Active\n---\n\n"
                    f"# DP-{number:03d}: {title}\n\nBody.\n")
    return path


def _view(root: Path) -> Path:
    """The assembled document, carrying the explicit anchors the generator
    emits — so an anchor target is available to be chosen, and a test that
    prefers the page is choosing rather than falling back."""
    path = root / "docs" / "design-principles.md"
    path.write_text("# Design principles\n\n"
                    '<a name="dp-1"></a>\n\n## 1. First\n\nBody.\n\n'
                    '<a name="dp-2"></a>\n\n## 2. Second\n\nBody.\n')
    return path


def _ref(text: str, source: Path):
    refs = doc_refs.find_refs(text, source)
    assert refs, f"nothing matched in {text!r}"
    return refs[0]


def _prose_target(text: str, source: Path) -> str | None:
    return doc_refs.resolve(_ref(text, source), source,
                            doc_refs.adr_paths(), doc_refs.dp_anchors(), text)


# ── unset: whatever the scheme already does ─────────────────────────────────

def test_a_document_scheme_defaults_to_its_view(tmp_path, monkeypatch):
    """The key is inert until set. A project upgrading into this version finds
    its citations spelled exactly as before."""
    _project(tmp_path, monkeypatch)
    _principle(tmp_path, 1, "First")
    _principle(tmp_path, 2, "Second")
    _view(tmp_path)
    source = _principle(tmp_path, 1, "First")
    assert config.load().schemes["DP"].cite == "view"
    assert doc_refs.wikilink_target("DP-2", source) == "design-principles.md#dp-2"


def test_an_index_scheme_defaults_to_the_page(tmp_path, monkeypatch):
    """Not a choice — an index scheme assembles no view, so the document's own
    file is its only address. Recorded as `cite` all the same, so the field
    always says where a citation goes rather than sometimes meaning nothing."""
    _project(tmp_path, monkeypatch, render="index")
    assert config.load().schemes["DP"].cite == "page"


# ── cite = "page": the cited document's own file ────────────────────────────

def test_a_citation_resolves_to_the_cited_documents_own_page(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, cite="page")
    _principle(tmp_path, 1, "First")
    _principle(tmp_path, 2, "Second")
    _view(tmp_path)
    source = _principle(tmp_path, 3, "Third")

    # A principle's links resolve from `docs/`, where the assembled view
    # renders (config.link_base) — so the path climbs out and back in.
    assert doc_refs.wikilink_target("DP-2", source) == "../record/principles.d/DP-002.md"
    assert _prose_target("as DP-2 says", source) == "../record/principles.d/DP-002.md"


def test_the_anchor_is_not_used_even_though_one_exists(tmp_path, monkeypatch):
    """The instrument check: the view carries `<a name="dp-2">`, and
    `dp_anchors` finds it. Preferring the page is a decision, not an absence."""
    _project(tmp_path, monkeypatch, cite="page")
    _principle(tmp_path, 1, "First")
    _principle(tmp_path, 2, "Second")
    _view(tmp_path)
    source = _principle(tmp_path, 1, "First")

    assert doc_refs.dp_anchors().get(2) == "dp-2", "the fixture lost its anchors"
    assert "#" not in (doc_refs.wikilink_target("DP-2", source) or "")


def test_a_document_citing_itself_still_resolves_to_nothing(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, cite="page")
    source = _principle(tmp_path, 1, "First")
    _view(tmp_path)
    assert doc_refs.wikilink_target("DP-1", source) is None
    assert _prose_target("DP-1 says", source) is None


def test_a_code_with_no_document_resolves_to_nothing(tmp_path, monkeypatch):
    """Under `view` this returned an anchor into the assembled page whether or
    not the principle existed. A page target cannot: there is no file."""
    _project(tmp_path, monkeypatch, cite="page")
    _principle(tmp_path, 1, "First")
    _view(tmp_path)
    source = _principle(tmp_path, 1, "First")
    assert doc_refs.wikilink_target("DP-9", source) is None


# ── the opt-out: cite the assembled view ────────────────────────────────────

def test_cite_view_restores_the_anchor(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, cite="view")
    _principle(tmp_path, 1, "First")
    _principle(tmp_path, 2, "Second")
    _view(tmp_path)
    source = _principle(tmp_path, 1, "First")

    assert doc_refs.wikilink_target("DP-2", source) == "design-principles.md#dp-2"
    assert _prose_target("see DP-2", source) == "design-principles.md#dp-2"


def test_cite_view_from_inside_the_view_is_a_bare_fragment(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, cite="view")
    _principle(tmp_path, 1, "First")
    _principle(tmp_path, 2, "Second")
    view = _view(tmp_path)
    assert doc_refs.wikilink_target("DP-2", view) == "#dp-2"


# ── refusals ────────────────────────────────────────────────────────────────

def test_an_unknown_cite_value_is_refused_by_name(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, cite="anchor")
    with pytest.raises(ValueError, match=r"cite.*anchor.*page.*view"):
        config.load()


def test_cite_view_on_an_index_scheme_is_refused(tmp_path, monkeypatch):
    """An index-rendered scheme assembles no document, so there is no view to
    anchor into. Saying so beats silently resolving to the page anyway — the
    project asked for something that does not exist here (DP-1)."""
    _project(tmp_path, monkeypatch, cite="view", render="index")
    with pytest.raises(ValueError, match=r"cite = \"view\".*render = \"document\""):
        config.load()


def test_cite_page_on_an_index_scheme_is_accepted(tmp_path, monkeypatch):
    """Redundant but true — it describes what an index scheme already does, so
    refusing it would be pedantry rather than a caught mistake."""
    _project(tmp_path, monkeypatch, cite="page", render="index")
    cfg = config.load()
    assert cfg.schemes["DP"].cite == "page"


# ── retargeting links the record already wrote ──────────────────────────────
#
# Flipping the key resolves NEW citations. The ones already written are plain
# markdown links, which the linkifier never touches — it spells bare
# references. On this project that was 330 links across 81 pages, so a switch
# that only changed future links would have fixed nothing anybody could see.

def test_an_already_written_anchor_link_is_retargeted_at_the_page(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, cite="page")
    _principle(tmp_path, 1, "First")
    _principle(tmp_path, 2, "Second")
    _view(tmp_path)
    source = _principle(tmp_path, 1, "First")

    out, n = doc_refs.retarget_view_citations(
        "as [DP-2](design-principles.md#dp-2) says", source)
    assert n == 1
    assert out == "as [DP-2](../record/principles.d/DP-002.md) says"


def test_the_link_text_is_left_exactly_as_written(tmp_path, monkeypatch):
    """The label is the author's sentence, not a field. Retargeting is about
    where the link goes."""
    _project(tmp_path, monkeypatch, cite="page")
    _principle(tmp_path, 1, "First")
    _principle(tmp_path, 2, "Second")
    _view(tmp_path)
    source = _principle(tmp_path, 1, "First")
    out, _ = doc_refs.retarget_view_citations(
        "see [the second one](design-principles.md#dp-2)", source)
    assert out.startswith("see [the second one](")


def test_a_bare_fragment_inside_the_view_is_retargeted_too(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, cite="page")
    _principle(tmp_path, 1, "First")
    _principle(tmp_path, 2, "Second")
    view = _view(tmp_path)
    out, n = doc_refs.retarget_view_citations("per [DP-2](#dp-2) here", view)
    assert n == 1
    assert out == "per [DP-2](../record/principles.d/DP-002.md) here"


def test_it_is_idempotent(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, cite="page")
    _principle(tmp_path, 1, "First")
    _principle(tmp_path, 2, "Second")
    _view(tmp_path)
    source = _principle(tmp_path, 1, "First")
    once, _ = doc_refs.retarget_view_citations(
        "as [DP-2](design-principles.md#dp-2) says", source)
    twice, n = doc_refs.retarget_view_citations(once, source)
    assert (twice, n) == (once, 0)


def test_a_scheme_that_cites_its_view_is_left_alone(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, cite="view")
    _principle(tmp_path, 1, "First")
    _principle(tmp_path, 2, "Second")
    _view(tmp_path)
    source = _principle(tmp_path, 1, "First")
    text = "as [DP-2](design-principles.md#dp-2) says"
    assert doc_refs.retarget_view_citations(text, source) == (text, 0)


def test_a_link_to_the_view_itself_is_not_a_citation(tmp_path, monkeypatch):
    """No fragment means the author is pointing at the whole document, which is
    a real thing to link to and not a principle citation."""
    _project(tmp_path, monkeypatch, cite="page")
    _principle(tmp_path, 1, "First")
    _view(tmp_path)
    source = _principle(tmp_path, 1, "First")
    text = "see [the principles](design-principles.md)"
    assert doc_refs.retarget_view_citations(text, source) == (text, 0)


def test_an_anchor_naming_no_document_is_left_alone(tmp_path, monkeypatch):
    """Rewriting it would point at a file that does not exist — worse than the
    dead fragment it already is, and it hides the problem from the lint."""
    _project(tmp_path, monkeypatch, cite="page")
    _principle(tmp_path, 1, "First")
    _view(tmp_path)
    source = _principle(tmp_path, 1, "First")
    text = "as [DP-9](design-principles.md#dp-9) says"
    assert doc_refs.retarget_view_citations(text, source) == (text, 0)


def test_a_specimen_in_a_code_span_is_not_rewritten(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, cite="page")
    _principle(tmp_path, 1, "First")
    _principle(tmp_path, 2, "Second")
    _view(tmp_path)
    source = _principle(tmp_path, 1, "First")
    text = "write `[DP-2](design-principles.md#dp-2)` by hand"
    assert doc_refs.retarget_view_citations(text, source) == (text, 0)
