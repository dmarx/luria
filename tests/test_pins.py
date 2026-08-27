"""Content pins (#135): remote knowledge endorsed by hash.

The construction fixtures live in `test_remotes` — a pin is one more consumer
of the same remotes, so the tests share one vocabulary rather than keeping a
second copy that drifts (DP-4).
"""
import json

from test_remotes import ARXIV, SCHEMED, lockfile, with_remote

from luria import config, pins, remotes

# unresolved-ok-file: ADR-999 — a fixture code, not a claim about this repo


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
    assert pins.stable_url(remote, "ADR-032") == (
        "https://raw.githubusercontent.com/o/r/main/record/decisions.d/ADR-032.md")


def test_raw_url_drops_a_document_anchor(project):
    """A fragment selects nothing server-side; the endorsement covers the
    document the anchor lands in."""
    with_remote(project, SCHEMED)
    remote = config.current().remotes["UP"]
    assert pins.stable_url(remote, "VP-18") == (
        "https://raw.githubusercontent.com/o/r/main/docs/values.md")


def test_a_url_template_has_no_stable_bytes_to_pin(project):
    """An arXiv abstract or a Jira ticket is a rendered page — hashing it
    would drift on its own schedule, and the pin would cry wolf."""
    with_remote(project, ARXIV)
    assert pins.stable_url(config.current().remotes["ARXIV"], "2403.05530") == ""


def test_a_declared_pin_url_makes_a_uid_remote_pinnable(project):
    """`url` is where a reader lands; `pin_url` is what a pin hashes. The
    declaration takes the same substitutions, so arXiv's immutable e-print
    stands behind the abstract page a reader sees."""
    with_remote(project, ARXIV + 'pin_url = "https://arxiv.org/e-print/{1}.{2}"\n')
    remote = config.current().remotes["ARXIV"]
    assert pins.stable_url(remote, "2403.05530") == (
        "https://arxiv.org/e-print/2403.05530")
    # …and the reader's link is untouched by the declaration.
    assert remotes.link(remote, "2403.05530") == (
        "https://arxiv.org/abs/2403.05530")


def test_a_declared_pin_url_wins_over_the_github_rebase(project):
    """The project's declaration is the strongest evidence there is — a
    remote that mirrors its record somewhere stabler than the repo can say
    so, and the construction steps aside."""
    with_remote(project, 'pin_url = "https://mirror.test/{code}.md"\n')
    remote = config.current().remotes["UP"]
    assert pins.stable_url(remote, "ADR-032") == "https://mirror.test/ADR-032.md"


def test_a_scheme_level_pin_url_scopes_the_declaration(project):
    with_remote(project,
        '[luria.remotes.UP.schemes.VP]\n'
        'url = "https://up.example/values/{number}"\n'
        'pin_url = "https://up.example/raw/values-{number}.txt"\n')
    remote = config.current().remotes["UP"]
    assert pins.stable_url(remote, "VP-18") == (
        "https://up.example/raw/values-18.txt")
    # The other schemes stay on the GitHub construction.
    assert pins.stable_url(remote, "ADR-032").startswith(
        "https://raw.githubusercontent.com/o/r/")


def test_pin_stores_the_endorsed_hash(project, monkeypatch):
    with_remote(project)
    serve(monkeypatch, b"the decision, as endorsed")
    pins.pin_codes(("UP-ADR-032",))
    entry = pinfile(project)["pins"]["UP"]["ADR-032"]
    digest = pins.content_hash(b"the decision, as endorsed")
    assert entry == {"endorsed": digest, "seen": digest}


def test_pin_survives_a_refresh_and_vice_versa(project, monkeypatch):
    """One lockfile, two writers — a refresh must not lose the pins, nor a
    pin the discovered filenames."""
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    serve(monkeypatch, b"v1")
    pins.pin_codes(("UP-ADR-032",))
    assert pinfile(project)["remotes"]["UP"] == {"ADR-032": "adr-032-x.md"}
    remotes.write_lock({"UP": {"ADR-033": "ADR-033.md"}})
    assert pinfile(project)["pins"]["UP"]["ADR-032"]["endorsed"] \
        == pins.content_hash(b"v1")


def test_refresh_moves_seen_and_never_endorsed(project, monkeypatch):
    """`endorsed` is a human's claim; only `--pin` may move it. The refresh
    records the observation, and the committed diff carries the drift."""
    with_remote(project)
    serve(monkeypatch, b"v1")
    pins.pin_codes(("UP-ADR-032",))
    serve(monkeypatch, b"v2")
    assert pins.refresh_seen() == ["UP-ADR-032"]
    entry = pinfile(project)["pins"]["UP"]["ADR-032"]
    assert entry["endorsed"] == pins.content_hash(b"v1")
    assert entry["seen"] == pins.content_hash(b"v2")


def test_an_unreachable_document_keeps_its_last_observation(project, monkeypatch):
    """Unreachable is not changed — inventing a new `seen` on a network error
    would report drift that never happened."""
    with_remote(project)
    serve(monkeypatch, b"v1")
    pins.pin_codes(("UP-ADR-032",))
    monkeypatch.setattr(remotes, "_fetch_bytes",
                        lambda url: (b"", "unreachable (URLError)"))
    assert pins.refresh_seen() == []
    entry = pinfile(project)["pins"]["UP"]["ADR-032"]
    assert entry["seen"] == entry["endorsed"] == pins.content_hash(b"v1")


def test_drift_is_read_offline_from_the_lockfile(project):
    """The whole point of committing both hashes: `luria lint` compares them
    without opening a socket, like every other check."""
    with_remote(project)
    cite(project, "per UP-ADR-032 upstream\n")
    remotes.write_lock(pinned={"UP": {"ADR-032": {
        "endorsed": "sha256:aaa", "seen": "sha256:bbb"}}})
    lines = pins.drift_lines()
    assert len(lines) == 1
    assert "UP-ADR-032" in lines[0] and "changed since it was endorsed" in lines[0]
    assert "luria remotes --pin UP-ADR-032" in lines[0]


def test_an_agreeing_pin_is_silent(project):
    with_remote(project)
    cite(project, "per UP-ADR-032 upstream\n")
    remotes.write_lock(pinned={"UP": {"ADR-032": {
        "endorsed": "sha256:aaa", "seen": "sha256:aaa"}}})
    assert pins.drift_lines() == []


def test_a_pin_nothing_cites_is_reported(project):
    """A pin that outlived its citation is the lockfile's version of a stale
    directive — committed state that no longer governs anything."""
    with_remote(project)
    remotes.write_lock(pinned={"UP": {"ADR-032": {
        "endorsed": "sha256:aaa", "seen": "sha256:aaa"}}})
    lines = pins.drift_lines()
    assert len(lines) == 1 and "nothing cites it" in lines[0]


def test_bare_pin_endorses_the_cited_and_prunes_the_rest(project, monkeypatch):
    with_remote(project)
    cite(project, "per UP-ADR-032 upstream\n")
    remotes.write_lock(pinned={"UP": {"ADR-999": {
        "endorsed": "sha256:old", "seen": "sha256:old"}}})
    serve(monkeypatch, b"current")
    pins.pin_codes(())
    pinned = pinfile(project)["pins"]["UP"]
    assert set(pinned) == {"ADR-032"}
    assert pinned["ADR-032"]["endorsed"] == pins.content_hash(b"current")


def test_re_endorsing_clears_the_drift(project, monkeypatch):
    """The issue's loop closed: review the change, run the CLI, and the
    lockfile again says a human vouched for what is there (#135)."""
    with_remote(project)
    cite(project, "per UP-ADR-032 upstream\n")
    serve(monkeypatch, b"v1")
    pins.pin_codes(("UP-ADR-032",))
    serve(monkeypatch, b"v2")
    pins.refresh_seen()
    assert pins.drift_lines() != []
    pins.pin_codes(("UP-ADR-032",))
    assert pins.drift_lines() == []


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
