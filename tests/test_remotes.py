"""Foreign references: `UP-ADR-032` is another project's decision (ADR-016).

The risky part is not the URL construction — it is the *precedence*. A composed
code has a local-looking code inside it, and four different scanners can each
read the tail out of the middle and quietly say something about the wrong
project: the reference finder, the fixer, the citation scan, and the annotation
validator. One test per mouth.
"""
import json
import sys
from pathlib import Path

from _scheme import decision

from luria import config, doc_refs, ref_status, remotes

# unresolved-ok-file: ADR-999 UP-ADR-999 VP-018 — fixture codes, not claims about
# this repo. ADR-032 left the list when a real thirty-second decision arrived and
# the fixture number started resolving.
REPO = Path(__file__).resolve().parents[1]

REMOTE_TOML = (
    '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
    '[luria.remotes.UP]\nname = "upstream"\nrepo = "o/r"\n'
)


def with_remote(project, extra: str = "") -> Path:
    (project / "luria.toml").write_text(REMOTE_TOML + extra)
    config.reset()
    return project


def lockfile(project, entries: dict[str, str]) -> None:
    (project / "remotes.lock.json").write_text(
        json.dumps({"remotes": {"UP": entries}}))


# ── Construction ─────────────────────────────────────────────────────────


def test_code_only_convention_is_the_default(project):
    """Right whenever the remote follows ADR-013, and it is Luria's own
    convention — so a remote that uses it needs one config line."""
    with_remote(project)
    assert remotes.resolve("UP", "ADR-32") == (
        "https://github.com/o/r/blob/main/record/decisions.d/ADR-032.md")


def test_a_discovered_filename_wins(project):
    """The only rung that can resolve a slug-named remote — no template can
    turn a number into `adr-032-changelog-ci-collection.md`."""
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-changelog-ci-collection.md"})
    assert remotes.resolve("UP", "ADR-032").endswith(
        "/adr-032-changelog-ci-collection.md")


def test_discovery_is_authoritative_once_done(project):
    """A code absent from a lockfile that was read *from the remote* names no
    document there. Guessing a filename anyway is how `DP-004` produced a
    confident link to a file that has never existed."""
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    assert remotes.resolve("UP", "ADR-999") == ""


def test_no_lockfile_means_fall_back_rather_than_refuse(project):
    """Never refreshed is not the same claim as "not there" — a project that
    has not run discovery still gets working links for a conventional remote."""
    with_remote(project)
    assert remotes.resolve("UP", "ADR-999").endswith("/ADR-999.md")


def test_an_explicit_template_overrides_everything(project):
    with_remote(project, 'url = "https://x.test/{code}"\n')
    lockfile(project, {"ADR-032": "ignored.md"})
    assert remotes.resolve("UP", "ADR-032") == "https://x.test/ADR-032"


def test_an_unregistered_prefix_is_not_a_namespace(project):
    """`MY-ADR-004` in prose must stay prose. The pattern is built from the
    registry precisely so unregistered text is never claimed."""
    with_remote(project)
    assert remotes.resolve("MY", "ADR-004") == ""


# ── Precedence: four scanners, one composed code ─────────────────────────


def test_the_finder_claims_the_whole_composed_span(project):
    """`UP-ADR-032` must not also be read as a local `ADR-032`."""
    with_remote(project)
    refs = doc_refs.find_refs("see UP-ADR-032 for that")
    assert [(r.kind, r.remote, r.code) for r in refs] == [("remote", "UP", "ADR-032")]


def test_a_local_code_still_reads_as_local(project):
    with_remote(project)
    refs = doc_refs.find_refs("see ADR-032 for that")
    assert [(r.kind, r.prefix) for r in refs] == [("scheme", "ADR")]


def test_the_fixer_writes_a_url_not_a_relative_path(project):
    """A different repository, so no `link_base` applies and the same target is
    right from every file."""
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    out, n = doc_refs.linkify("see UP-ADR-032", project / "docs" / "page.md")
    assert n == 1
    assert out == ("see [UP-ADR-032]"
                   "(https://github.com/o/r/blob/main/record/decisions.d/adr-032-x.md)")


def test_an_unresolvable_foreign_code_is_not_linked(project):
    """The lint never demands a rewrite the fixer wouldn't make, so a code the
    remote doesn't have stays bare — and is reported instead."""
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    _, n = doc_refs.linkify("see UP-ADR-999", project / "docs" / "page.md")
    assert n == 0


def test_the_citation_scan_does_not_read_a_local_code_out_of_it(project):
    """`UP-ADR-012` must not count as a citation of *this* project's ADR-012 —
    which would keep a local retired decision looking cited forever."""
    decision(project, 12, "Superseded", "The replaced one")
    with_remote(project)
    (project / "notes.md").write_text("per UP-ADR-012 upstream\n")
    docs = ref_status.load_docs()
    result = ref_status.scan([project / "notes.md"], docs)
    assert result.cited == {}


def test_an_unresolvable_foreign_code_is_reported(project):
    """Blanking the composed span must not make it invisible — a foreign code
    that names nothing is still a reference nobody can follow (ADR-014)."""
    decision(project, 1, "Active")
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    (project / "notes.md").write_text("per UP-ADR-999 upstream\n")
    result = ref_status.scan([project / "notes.md"], ref_status.load_docs())
    assert [c.line for c in result.dangling["UP-ADR-999"]] == [1]


def test_the_annotation_validator_reads_the_composed_code(project):
    """`unresolved-ok: UP-ADR-012` must be checked against the *remote*. Reading
    `ADR-012` out of the middle asks the wrong project, and the annotation is
    then reported as stale for a reason that isn't true."""
    decision(project, 12, "Active", "A local decision")
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    (project / "notes.md").write_text(
        "<!-- unresolved-ok: UP-ADR-999 — upstream, not here -->\nUP-ADR-999\n")
    docs = ref_status.load_docs()
    result = ref_status.scan([project / "notes.md"], docs)
    assert ref_status.dangling(result, docs) == []
    assert ref_status.stale_annotations(result, docs) == []


# ── Discovery ────────────────────────────────────────────────────────────


def test_discovery_reads_both_filename_conventions(tmp_path):
    """A remote that predates ADR-013 has slugs; one that follows it doesn't.
    Both have to read, or adoption means renaming somebody else's repo."""
    found = remotes._from_names(
        ["adr-032-changelog-ci.md", "ADR-004.md", "README.md", "tags.yaml"])
    assert found == {"ADR-032": "adr-032-changelog-ci.md", "ADR-004": "ADR-004.md"}


def test_the_remotes_own_config_says_where_its_documents_live():
    """Fetched from the remote and parsed, rather than guessed — which is the
    whole point of a config file existing."""
    assert remotes._upstream_dir(
        '[luria.schemes.ADR]\ndir = "records"\n', "docs/decisions") == "records"


def test_an_unparseable_upstream_config_leaves_the_default_standing():
    """A remote may have a `luria.toml` this version can't read. Falling back
    is right; crashing on someone else's file is not."""
    assert remotes._upstream_dir("!! not toml", "docs/decisions") == "docs/decisions"
    assert remotes._upstream_dir("", "docs/decisions") == "docs/decisions"


def test_discovery_says_why_it_found_nothing(project):
    """A discovery that silently returns nothing is indistinguishable from a
    remote with no documents (DP-1) — and it returns None, not {}, because an
    unreadable remote and an empty directory are different claims."""
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n[luria.remotes.UP]\nname = "upstream"\n')
    config.reset()
    found, how = remotes.discover(config.current().remotes["UP"])
    assert found is None and "no `repo` configured" in how


def test_failed_discovery_never_writes_an_authoritative_empty_map(project, monkeypatch, capsys):
    """Surfaced by pinning against this repo's own remotes: a private remote's
    failed discovery wrote `{}` to the lockfile, and an empty map is
    *authoritative* — every one of its references then resolved to "absent
    from the remote". Failure must leave the remote off the lockfile (or keep
    the map it had), so it stays on the code-only convention."""
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    monkeypatch.setattr(remotes, "discover",
                        lambda remote: (None, "GitHub API: not readable anonymously"))
    remotes.run(refresh=True)
    capsys.readouterr()
    assert remotes.lock()["UP"] == {"ADR-032": "adr-032-x.md"}
    assert remotes.resolve("UP", "ADR-032").endswith("/adr-032-x.md")


# ── Hand-written URLs (url-ok) ───────────────────────────────────────────


def hand(project, body: str, name: str = "notes.md"):
    page = project / name
    page.write_text(body)
    return remotes.hand_links([page])


def test_hand_written_url_is_reported(project):
    """A hand URL is sometimes the only correct citation — and it is frozen at
    writing time, so it is reported until acknowledged, never silently kept."""
    with_remote(project)
    flagged, stale = hand(project, "[UP-ADR-032](https://example.test/elsewhere.md)\n")
    assert len(flagged) == 1
    # Names the code, the fact, and what construction would have said (DP-1).
    assert "UP-ADR-032" in flagged[0] and "hand-written" in flagged[0]
    assert "record/decisions.d/ADR-032.md" in flagged[0]
    assert stale == []


def test_constructed_url_is_not_reported(project):
    with_remote(project)
    flagged, _ = hand(project,
        "[UP-ADR-032](https://github.com/o/r/blob/main/record/decisions.d/ADR-032.md)\n")
    assert flagged == []


def test_url_ok_acknowledges_the_link(project):
    with_remote(project)
    flagged, stale = hand(project,
        "<!-- url-ok-block: UP-ADR-032 — their principles are one document -->\n"
        "\n"
        "[UP-ADR-032](https://example.test/elsewhere.md#anchor)\n")
    assert flagged == [] and stale == []


def test_url_ok_matches_unpadded_codes(project):
    """`UP-ADR-32` and `UP-ADR-032` are one document — the annotation should
    not care which spelling either side used."""
    with_remote(project)
    flagged, stale = hand(project,
        "[UP-ADR-32](https://example.test/x.md) <!-- url-ok: UP-ADR-032 — deliberate -->\n")
    assert flagged == [] and stale == []


def test_unused_url_ok_is_stale(project):
    """A directive that silently does nothing is worse than no directive."""
    with_remote(project)
    _, stale = hand(project, "<!-- url-ok: UP-ADR-032 — nothing here -->\n")
    assert len(stale) == 1 and "acknowledges no hand-written link" in stale[0]


def test_url_ok_on_a_constructed_link_is_stale(project):
    """The inverted validity check, same as `unresolved-ok`: acknowledging a
    link that matches the construction excuses nothing."""
    with_remote(project)
    _, stale = hand(project,
        "<!-- url-ok: UP-ADR-032 — was hand-written once -->\n"
        "[UP-ADR-032](https://github.com/o/r/blob/main/record/decisions.d/ADR-032.md)\n")
    assert len(stale) == 1


def test_a_quoted_hand_link_is_a_specimen_not_a_citation(project):
    with_remote(project)
    flagged, _ = hand(project, "quoting `[UP-ADR-032](https://x.test/y.md)` here\n")
    assert flagged == []


# ── Per-scheme construction (ADR-023) ────────────────────────────────────


SCHEMED = (
    '[luria.remotes.UP.schemes.VP]\ndocument = "docs/values.md"\n'
    '[luria.remotes.UP.schemes.RFC]\ndir = "docs/rfcs"\n'
)


def test_document_scheme_constructs_a_file_anchor(project):
    """A document-rendered scheme's documents are sections, not files — the
    construction is the assembled page plus an anchor."""
    with_remote(project, SCHEMED)
    assert remotes.resolve("UP", "VP-18") == (
        "https://github.com/o/r/blob/main/docs/values.md#vp-18")


def test_anchor_defaults_to_the_stable_anchor_shape(project):
    """The prefix lowercased plus the number, unpadded — the shape Luria's
    own document render emits, so a remote on current conventions needs only
    the `document` line."""
    with_remote(project, SCHEMED)
    assert remotes.resolve("UP", "VP-9").endswith("#vp-9")


def test_anchor_template_is_configurable(project):
    with_remote(project,
        '[luria.remotes.UP.schemes.VP]\ndocument = "VALUES.md"\n'
        'anchor = "value-{number}"\n')
    assert remotes.resolve("UP", "VP-4").endswith("VALUES.md#value-4")


def test_scheme_dir_scopes_the_file_convention(project):
    """Different code families in one namespace construct into different
    places; the remote-level `dir` keeps serving the rest."""
    with_remote(project, SCHEMED + '\n')
    assert remotes.resolve("UP", "RFC-7") == (
        "https://github.com/o/r/blob/main/docs/rfcs/RFC-007.md")
    assert "record/decisions.d/ADR-001.md" in remotes.resolve("UP", "ADR-1")


def test_scheme_url_template_wins(project):
    with_remote(project,
        '[luria.remotes.UP.schemes.VP]\n'
        'url = "https://up.example/values/{number}"\n')
    assert remotes.resolve("UP", "VP-3") == "https://up.example/values/3"


def test_lockfile_authority_does_not_cover_document_schemes(project):
    """The lockfile maps *files*, which is all discovery can see. A section of
    a document never appears in a directory listing, so its absence from the
    lockfile is not evidence — the anchor construction must survive it."""
    with_remote(project, SCHEMED)
    lockfile(project, {"ADR-032": "adr-032-changelog-ci-collection.md"})
    assert remotes.resolve("UP", "VP-18").endswith("#vp-18")
    # …while file-per-code codes stay under its authority (ADR-016).
    assert remotes.resolve("UP", "ADR-999") == ""


def test_url_ok_retires_when_the_construction_catches_up(project):
    """The loop ADR-022 promised: configure the scheme, delete the hand URL,
    and a leftover acknowledgement reports itself stale."""
    with_remote(project, SCHEMED)
    flagged, stale = hand(project,
        "<!-- url-ok: UP-VP-18 — was unconstructible before ADR-023 -->\n"
        "[UP-VP-18](https://github.com/o/r/blob/main/docs/values.md#vp-18)\n")
    assert flagged == []                      # the link now matches construction
    assert len(stale) == 1                    # …so the annotation is done


# ── uid remotes: not everything is a numbered scheme (ADR-024) ───────────


ARXIV = (
    '[luria.remotes.ARXIV]\n'
    'uid = "(\\\\d{4})[.:](\\\\d{4,5})"\n'
    'url = "https://arxiv.org/abs/{1}.{2}"\n'
)


def test_uid_remote_constructs_through_the_template(project):
    with_remote(project, ARXIV)
    assert remotes.resolve("ARXIV", "2403.05530") == "https://arxiv.org/abs/2403.05530"


def test_uid_capture_groups_index_the_template_by_position(project):
    """{1}, {2}… are the uid pattern's capture groups; {0}/{uid} is the whole
    tail — so one template can restructure the identifier."""
    with_remote(project, ARXIV)
    assert remotes.resolve("ARXIV", "1234:5678") == "https://arxiv.org/abs/1234.5678"


def test_uid_is_exact_never_normalised(project):
    """`ADR-32` and `ADR-032` are one document; `2403.05530` is itself. A uid
    must survive canonicalisation untouched — zero-padding an arxiv id would
    quietly cite a different paper."""
    with_remote(project, ARXIV)
    remote = config.current().remotes["ARXIV"]
    assert remote.canon("2403.05530") == "2403.05530"


def test_the_delimiter_is_configurable(project):
    with_remote(project,
        '[luria.remotes.JIRA]\ndelim = ":"\nuid = "[A-Z]+-\\\\d+"\n'
        'url = "https://example.atlassian.net/browse/{uid}"\n')
    text = "tracked as JIRA:PROJ-42 upstream"
    refs = remotes.references(text)
    assert [r.composed for r in refs] == ["JIRA:PROJ-42"]
    assert remotes.link(refs[0].remote, refs[0].tail).endswith("/browse/PROJ-42")


def test_unconfigured_prefixes_do_not_match(project):
    """The pattern is built from config: `FAKE-1234.5678` must not be read as
    a namespace just because it is shaped like one."""
    with_remote(project, ARXIV)
    assert remotes.references("see FAKE-1234.5678 here") == []


def test_uid_remote_without_a_template_constructs_nothing(project):
    """One rung only — with no template there is nothing to guess with, and
    "" is what makes ref-status report the citation as dangling (DP-1)."""
    with_remote(project, '[luria.remotes.ARXIV]\nuid = "\\\\d{4}[.]\\\\d{4,5}"\n')
    assert remotes.resolve("ARXIV", "2403.05530") == ""


def test_lockfile_never_vetoes_a_uid_remote(project):
    with_remote(project, ARXIV)
    lockfile(project, {"ADR-032": "x.md"})
    assert remotes.resolve("ARXIV", "2403.05530").endswith("/abs/2403.05530")


def test_scheme_shaped_references_still_scan_beside_uid_remotes(project):
    with_remote(project, ARXIV)
    text = "per UP-ADR-032 and ARXIV-2403.05530"
    assert [r.composed for r in remotes.references(text)] == [
        "UP-ADR-032", "ARXIV-2403.05530"]


def test_url_ok_covers_uid_remotes_too(project):
    """A hand URL for a uid code is the same acknowledged state — the check
    and the directive are shape-agnostic because both go through the remote's
    own parser."""
    with_remote(project, ARXIV)
    flagged, stale = hand(project,
        "[ARXIV-2403.05530](https://arxiv.org/pdf/2403.05530v2)\n")
    assert len(flagged) == 1 and "ARXIV-2403.05530" in flagged[0]
    flagged, stale = hand(project,
        "<!-- url-ok: ARXIV-2403.05530 — the v2 PDF specifically -->\n"
        "[ARXIV-2403.05530](https://arxiv.org/pdf/2403.05530v2)\n")
    assert flagged == [] and stale == []


# ── Content pins (#135) ──────────────────────────────────────────────────


def cite(project, text: str) -> None:
    (project / "docs" / "notes.md").write_text(text)


def pinfile(project) -> dict:
    return json.loads((project / "remotes.lock.json").read_text())


def serve(monkeypatch, body: bytes) -> None:
    monkeypatch.setattr(remotes, "_fetch_bytes", lambda url: (body, ""))


def test_raw_url_rebases_the_blob_construction(project):
    """The pinned bytes must be the document, not GitHub's page around it —
    the page's markup churns under identical content."""
    with_remote(project)
    remote = config.current().remotes["UP"]
    assert remotes.raw_url(remote, "ADR-032") == (
        "https://raw.githubusercontent.com/o/r/main/record/decisions.d/ADR-032.md")


def test_raw_url_drops_a_document_anchor(project):
    """A fragment selects nothing server-side; the endorsement covers the
    document the anchor lands in."""
    with_remote(project, SCHEMED)
    remote = config.current().remotes["UP"]
    assert remotes.raw_url(remote, "VP-18") == (
        "https://raw.githubusercontent.com/o/r/main/docs/values.md")


def test_a_url_template_has_no_stable_bytes_to_pin(project):
    """An arXiv abstract or a Jira ticket is a rendered page — hashing it
    would drift on its own schedule, and the pin would cry wolf."""
    with_remote(project, ARXIV)
    assert remotes.raw_url(config.current().remotes["ARXIV"], "2403.05530") == ""


def test_pin_stores_the_endorsed_hash(project, monkeypatch):
    with_remote(project)
    serve(monkeypatch, b"the decision, as endorsed")
    remotes.pin_codes(("UP-ADR-032",))
    entry = pinfile(project)["pins"]["UP"]["ADR-032"]
    digest = remotes.content_hash(b"the decision, as endorsed")
    assert entry == {"endorsed": digest, "seen": digest}


def test_pin_survives_a_refresh_and_vice_versa(project, monkeypatch):
    """One lockfile, two writers — a refresh must not lose the pins, nor a
    pin the discovered filenames."""
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    serve(monkeypatch, b"v1")
    remotes.pin_codes(("UP-ADR-032",))
    assert pinfile(project)["remotes"]["UP"] == {"ADR-032": "adr-032-x.md"}
    remotes.write_lock({"UP": {"ADR-033": "ADR-033.md"}})
    assert pinfile(project)["pins"]["UP"]["ADR-032"]["endorsed"] \
        == remotes.content_hash(b"v1")


def test_refresh_moves_seen_and_never_endorsed(project, monkeypatch):
    """`endorsed` is a human's claim; only `--pin` may move it. The refresh
    records the observation, and the committed diff carries the drift."""
    with_remote(project)
    serve(monkeypatch, b"v1")
    remotes.pin_codes(("UP-ADR-032",))
    serve(monkeypatch, b"v2")
    assert remotes.refresh_seen() == ["UP-ADR-032"]
    entry = pinfile(project)["pins"]["UP"]["ADR-032"]
    assert entry["endorsed"] == remotes.content_hash(b"v1")
    assert entry["seen"] == remotes.content_hash(b"v2")


def test_an_unreachable_document_keeps_its_last_observation(project, monkeypatch):
    """Unreachable is not changed — inventing a new `seen` on a network error
    would report drift that never happened."""
    with_remote(project)
    serve(monkeypatch, b"v1")
    remotes.pin_codes(("UP-ADR-032",))
    monkeypatch.setattr(remotes, "_fetch_bytes",
                        lambda url: (b"", "unreachable (URLError)"))
    assert remotes.refresh_seen() == []
    entry = pinfile(project)["pins"]["UP"]["ADR-032"]
    assert entry["seen"] == entry["endorsed"] == remotes.content_hash(b"v1")


def test_drift_is_read_offline_from_the_lockfile(project):
    """The whole point of committing both hashes: `luria lint` compares them
    without opening a socket, like every other check."""
    with_remote(project)
    cite(project, "per UP-ADR-032 upstream\n")
    remotes.write_lock(pinned={"UP": {"ADR-032": {
        "endorsed": "sha256:aaa", "seen": "sha256:bbb"}}})
    lines = remotes.drift_lines()
    assert len(lines) == 1
    assert "UP-ADR-032" in lines[0] and "changed since it was endorsed" in lines[0]
    assert "luria remotes --pin UP-ADR-032" in lines[0]


def test_an_agreeing_pin_is_silent(project):
    with_remote(project)
    cite(project, "per UP-ADR-032 upstream\n")
    remotes.write_lock(pinned={"UP": {"ADR-032": {
        "endorsed": "sha256:aaa", "seen": "sha256:aaa"}}})
    assert remotes.drift_lines() == []


def test_a_pin_nothing_cites_is_reported(project):
    """A pin that outlived its citation is the lockfile's version of a stale
    directive — committed state that no longer governs anything."""
    with_remote(project)
    remotes.write_lock(pinned={"UP": {"ADR-032": {
        "endorsed": "sha256:aaa", "seen": "sha256:aaa"}}})
    lines = remotes.drift_lines()
    assert len(lines) == 1 and "nothing cites it" in lines[0]


def test_bare_pin_endorses_the_cited_and_prunes_the_rest(project, monkeypatch):
    with_remote(project)
    cite(project, "per UP-ADR-032 upstream\n")
    remotes.write_lock(pinned={"UP": {"ADR-999": {
        "endorsed": "sha256:old", "seen": "sha256:old"}}})
    serve(monkeypatch, b"current")
    remotes.pin_codes(())
    pinned = pinfile(project)["pins"]["UP"]
    assert set(pinned) == {"ADR-032"}
    assert pinned["ADR-032"]["endorsed"] == remotes.content_hash(b"current")


def test_re_endorsing_clears_the_drift(project, monkeypatch):
    """The issue's loop closed: review the change, run the CLI, and the
    lockfile again says a human vouched for what is there (#135)."""
    with_remote(project)
    cite(project, "per UP-ADR-032 upstream\n")
    serve(monkeypatch, b"v1")
    remotes.pin_codes(("UP-ADR-032",))
    serve(monkeypatch, b"v2")
    remotes.refresh_seen()
    assert remotes.drift_lines() != []
    remotes.pin_codes(("UP-ADR-032",))
    assert remotes.drift_lines() == []


def test_remote_drift_can_be_promoted_to_a_failure(project, monkeypatch, capsys):
    """The dial works for this class like any other (ADR-035): named in
    `fail_on`, the drifted pins fail the build instead of printing."""
    from luria import lint
    with_remote(project, '[luria.lint]\nfail_on = ["remote-drift"]\n')
    cite(project, "per UP-ADR-032 upstream\n")
    remotes.write_lock(pinned={"UP": {"ADR-032": {
        "endorsed": "sha256:aaa", "seen": "sha256:bbb"}}})
    errors: list[str] = []
    lint.report_warnings(errors)
    capsys.readouterr()
    assert any("failing: `fail_on`" in e for e in errors)
    assert any("UP-ADR-032" in e for e in errors)


def test_fixture_prefix_resolves_to_the_convention_note():
    """Dogfood, corpus-dependent: this repo registers `FX` (#38) so a fixture
    code is resolvable by construction — it points at the note that explains
    it, and can never collide with the real sequence."""
    url = remotes.resolve("FX", "ADR-032")
    assert url.endswith("docs/directives.md#fixture-codes")
    assert remotes.resolve("FX", "DP-9").endswith("#fixture-codes")
