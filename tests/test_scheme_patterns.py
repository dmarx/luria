# tests/test_scheme_patterns.py
"""A scheme's code regexes, compiled once per prefix (#265).

`Scheme.pattern` and `Scheme.temp_pattern` were properties that rebuilt an
f-string and called `re.compile` on every access, and `ref_status.scan` reads
both once per line per scheme per file. One `luria lint` over this repository
touched them 911,410 and 912,206 times.

`re` memoizes internally, so that was not 1.8M compilations — but it was that
many string interpolations and cache probes, on the hottest loop in the lint.

Cached on the module rather than on the instance, for two reasons. `Scheme` is
a frozen dataclass, and `functools.cached_property` does work on one (it writes
straight into `__dict__`), but on Python 3.11 — which this package supports —
it takes a per-attribute lock, and this path runs inside `parallel.pmap`'s
thread pool. A module-level `lru_cache` is lock-free on the fast path and also
survives `config.reset()` handing out freshly built `Scheme` objects.

The codes here are spelled `ZZZ`/`QQQ`, which are not schemes this record
configures. A test of a code regex has to contain strings shaped like codes,
and spelling them with this record's own scheme prefix made `luria lint`
read three fixtures as real citations of documents that do not exist — the finding that `unresolved-ok:`
and the reserved `FX` prefix both exist to answer. Neither is needed once the
fixture prefix simply is not a scheme, which is the more honest test anyway:
the pattern is built from whatever prefix it is handed (ADR-006).
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from luria.config import Scheme  # noqa: E402


def _scheme(prefix: str = "ZZZ") -> Scheme:
    return Scheme(prefix=prefix, dir=Path("record/decisions.d"))


def test_the_same_prefix_compiles_once(monkeypatch):
    from luria import config
    config._code_pattern.cache_clear()

    calls = []
    real = re.compile
    monkeypatch.setattr(config.re, "compile",
                        lambda *a, **k: calls.append(a[0]) or real(*a, **k))

    first = _scheme().pattern
    second = _scheme().pattern
    assert first is second, "a second access should reuse the compiled pattern"
    assert len(calls) == 1, "and should not recompile it"


def test_two_prefixes_do_not_share_a_pattern():
    """The cache is keyed on the prefix, so a second scheme must not be
    handed the first one's regex — that would make every code read as ADR."""
    first, second = _scheme("ZZZ").pattern, _scheme("QQQ").pattern
    assert first is not second
    assert first.search("ZZZ-012") and not first.search("QQQ-012")
    assert second.search("QQQ-012") and not second.search("ZZZ-012")


def test_the_code_pattern_still_reads_what_it_read_before():
    """Behaviour is the contract; the cache is an implementation detail."""
    p = _scheme("ZZZ").pattern
    assert p.search("see ZZZ-012 here").group("num") == "012"
    assert p.search("see ZZZ 12 here").group("num") == "12", "space spelling"
    assert p.search("ZZZ-1234").group("num") == "1234"
    assert not p.search("ZZZ-12345"), "five digits is not a code"
    assert not p.search("XZZZ-012"), "the word boundary still holds"


def test_the_temp_pattern_still_reads_what_it_read_before():
    p = _scheme("ZZZ").temp_pattern
    assert p.search("ZZZ-tmpab12x").group("tail") == "tmpab12x"
    assert not p.search("ZZZ-012")


def test_the_temp_pattern_is_cached_per_prefix(monkeypatch):
    from luria import config
    config._temp_pattern.cache_clear()

    calls = []
    real = re.compile
    monkeypatch.setattr(config.re, "compile",
                        lambda *a, **k: calls.append(a[0]) or real(*a, **k))

    assert _scheme().temp_pattern is _scheme().temp_pattern
    assert len(calls) == 1


def test_a_scheme_overriding_the_tail_gets_its_own_temp_pattern():
    """`TEMP_TAIL` is a class attribute, so it belongs in the key rather than
    being assumed constant — a subclass that narrows it must not be handed
    the base spelling's regex."""
    class Narrow(Scheme):
        TEMP_TAIL = r"tmp[0-9]{5}"

    wide = _scheme("ZZZ").temp_pattern
    narrow = Narrow(prefix="ZZZ", dir=Path("d")).temp_pattern
    assert wide is not narrow
    assert wide.search("ZZZ-tmpab123") and not narrow.search("ZZZ-tmpab123")


def test_the_cache_does_not_need_a_scheme_to_be_hashable():
    """`Scheme` is frozen but NOT hashable — it carries dict fields, so
    `hash()` raises `TypeError`. That is why the cache keys on the prefix
    string and not on the scheme: an `lru_cache` over the instance would have
    been a bug the moment it was called."""
    import pytest
    a, b = _scheme(), _scheme()
    with pytest.raises(TypeError):
        hash(a)
    a.pattern, b.temp_pattern          # still works without being hashable
    assert a == b, "equality is untouched by the cache"
