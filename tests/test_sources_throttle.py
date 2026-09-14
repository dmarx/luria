"""Fail fast when a remote is rate-limiting (#250).

A throttle is an answer: it says "not now". The version this replaces read it
as "ask again soon" — three attempts, 3s then 6s — so under a sustained rate
limit every identifier paid 9 seconds to arrive at the `throttled` it already
had after the first. `--resolve` over 225 identifiers has an 11-minute floor
before any of that, which is how it became a command nobody finished.

Nothing here opens a socket.
"""
from _config import merged
import json
import urllib.error

from luria import config, sources

from test_sources import SOURCE_BASE  # noqa: F401  (shared fixture shape)


def _project(project, network: str = "never") -> None:
    (project / "record" / "literature.d").mkdir(parents=True, exist_ok=True)
    (project / "docs" / "literature").mkdir(parents=True, exist_ok=True)
    (project / "luria.yaml").write_text(
        merged(SOURCE_BASE, {"lint": {"network": network}}))
    config.reset()
    sources.forget_refusals()


def _note(project, number: int, arxiv: str) -> None:
    (project / "record" / "literature.d" / f"LIT-{number:03d}.md").write_text(
        f"---\nstatus: Active\ntitle: 'Paper {number}'\narxiv: '{arxiv}'\n"
        f"---\n\n# LIT-{number:03d}: Paper {number}\n\nBody.\n")


def _throttle(retry_after: str | None = None):
    headers = {"Retry-After": retry_after} if retry_after else {}
    return urllib.error.HTTPError("http://x", 429, "Too Many Requests",
                                  headers, None)


def _opener(responses, calls):
    def fake(url, timeout=0):
        calls.append(url)
        got = responses.pop(0)
        if isinstance(got, Exception):
            raise got
        raise AssertionError("unused")
    return fake


# ── the fetch no longer argues with a rate limit ──────────────────────────

def test_a_throttle_without_retry_after_is_not_retried(project, monkeypatch):
    """One request, not three. The retries changed the outcome in none of the
    cases that motivated them — a rate limit is a property of the window."""
    _project(project)
    calls: list[str] = []
    monkeypatch.setattr(sources.urllib.request, "urlopen",
                        _opener([_throttle(), _throttle(), _throttle()], calls))
    monkeypatch.setattr(sources.time, "sleep",
                        lambda s: (_ for _ in ()).throw(
                            AssertionError(f"slept {s}s for a bare throttle")))

    got = sources._fetch("http://x", "<title>(.*?)</title>")
    assert got.status == "throttled"
    assert len(calls) == 1


def test_a_short_retry_after_is_honoured_once(project, monkeypatch):
    """A host that says when to come back has named the request that will
    succeed, so a short wait is the request it asked for."""
    _project(project)
    calls: list[str] = []
    slept: list[float] = []
    monkeypatch.setattr(sources.urllib.request, "urlopen",
                        _opener([_throttle("2"), _throttle("2")], calls))
    monkeypatch.setattr(sources.time, "sleep", slept.append)

    sources._fetch("http://x", "<title>(.*?)</title>")
    assert slept == [2.0]
    assert len(calls) == 2


def test_a_long_retry_after_is_reported_not_slept_through(project, monkeypatch):
    """A build that blocks two minutes on a metadata courtesy API is worse
    than one that reports what it could not check."""
    _project(project)
    calls: list[str] = []
    monkeypatch.setattr(sources.urllib.request, "urlopen",
                        _opener([_throttle("600")], calls))
    monkeypatch.setattr(sources.time, "sleep",
                        lambda s: (_ for _ in ()).throw(
                            AssertionError(f"slept {s}s")))

    got = sources._fetch("http://x", "<title>(.*?)</title>")
    assert got.status == "throttled"
    assert got.retry_after == 600.0
    assert len(calls) == 1


def test_the_wait_a_host_asked_for_is_carried_as_a_value(project):
    """It was parsed and then spent only on the message string."""
    _project(project)
    assert sources.Fetched("throttled").retry_after is None
    assert sources.Fetched("throttled", retry_after=5.0).retry_after == 5.0


# ── and a remote that refuses is not asked again this run ─────────────────

def test_one_refusal_ends_the_remote_for_the_run(project, monkeypatch):
    """The second throttled identifier tells us nothing the first did not."""
    _project(project, network="auto")
    _note(project, 1, "2305.10755")
    _note(project, 2, "1904.10509")
    _note(project, 3, "2205.14135")
    calls: list[str] = []
    monkeypatch.setattr(sources.urllib.request, "urlopen",
                        _opener([_throttle()] * 9, calls))

    idents = sources.identifiers()
    answers = [sources.ask(i) for i in idents]

    assert len(calls) == 1, "only the first identifier should reach the network"
    assert all(a.status == "throttled" for a in answers)
    assert "not asked again" in answers[-1].detail


def test_the_breaker_does_not_leak_between_runs(project, monkeypatch):
    _project(project, network="auto")
    _note(project, 1, "2305.10755")
    calls: list[str] = []
    monkeypatch.setattr(sources.urllib.request, "urlopen",
                        _opener([_throttle(), _throttle()], calls))

    sources.ask(sources.identifiers()[0])
    sources.forget_refusals()
    sources.ask(sources.identifiers()[0])
    assert len(calls) == 2


# ── the queue starts where the last run gave up ───────────────────────────

def test_unsettled_identifiers_are_asked_first(project):
    """The old order was the record's own, so a throttle partway through left
    the same tail unresolved run after run."""
    _project(project)
    for n, uid in enumerate(("2305.10755", "1904.10509", "2205.14135"), 1):
        _note(project, n, uid)
    known = {"ARXIV/2305.10755": {"title": "x"},
             "ARXIV/2205.14135": {"title": "y"}}

    order = [i.key for i in sources._queue((), known)]
    assert order[0] == "ARXIV/1904.10509"
    assert sorted(order[1:]) == ["ARXIV/2205.14135", "ARXIV/2305.10755"]


def test_the_queue_is_shuffled_so_one_bad_identifier_cannot_head_block(project):
    """Deliberately not seeded: an identifier that always errors must not sit
    at the head of the queue every run and spend the window on itself."""
    _project(project)
    for n in range(1, 13):
        _note(project, n, f"19{n:02d}.10509")

    orders = {tuple(i.key for i in sources._queue((), {})) for _ in range(12)}
    assert len(orders) > 1


def test_what_a_throttled_run_learned_is_kept(project, monkeypatch):
    """A run that dies in the middle used to write nothing at all."""
    _project(project, network="auto")
    for n in range(1, 26):
        _note(project, n, f"19{n:02d}.10509")

    served = {"count": 0}

    class _Body:
        def __init__(self, text): self.text = text
        def read(self): return self.text.encode()
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake(url, timeout=0):
        served["count"] += 1
        if served["count"] > 12:
            raise _throttle()
        return _Body("<title>A Paper</title>")

    monkeypatch.setattr(sources.urllib.request, "urlopen", fake)
    monkeypatch.setattr(sources.time, "sleep", lambda s: None)

    problems = sources.resolve()
    written = json.loads((project / "remotes.lock.json").read_text())["titles"]

    assert len(written) == 12, "every answer it got should survive the throttle"
    assert problems, "and the ones it could not settle are reported"
