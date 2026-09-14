# tests/test_documents_cache.py
"""The glob under `Scheme.documents()`.

`number_of` is cached on `(mtime, size)` and its docstring says why:
"`documents()` runs on every lint, index and link pass". The inner call was
cached; the glob and sort around it were not. Profiled serially
(`LURIA_JOBS=1`, which `parallel.py` provides so profiling is honest), one
`luria lint` over a 726-document record called `documents()` 24,960 times and
spent 161 of 239 seconds inside it — 73s in `sorted`, 44s comparing `Path`
objects, 33s in `stat`.

The invalidation is the one `number_of` already argues for, a directory up: a
directory's mtime moves when a document is added, removed or renamed, which
is exactly when the set of documents changes. A rewrite that leaves the set
alone does not move it — and does not need to, because the number itself is
cached on the file's own mtime.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import pytest  # noqa: E402

from luria import config  # noqa: E402

CONFIG = """\
issue_url: https://example.test/{n}
schemes:
  ADR:
    dir: record/decisions.d
    output: docs/decisions
"""


def _doc(path: Path, number: int) -> Path:
    path.write_text(f"---\nnumber: {number}\nstatus: Active\n"
                    f"title: 'D{number}'\n---\n\nbody\n", encoding="utf-8")
    return path


@pytest.fixture
def scheme_dir(tmp_path, monkeypatch):
    """The ADR scheme of a real config, and the directory it reads."""
    (tmp_path / "luria.yaml").write_text(CONFIG, encoding="utf-8")
    d = tmp_path / "record" / "decisions.d"
    d.mkdir(parents=True)
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    yield config.current().schemes["ADR"], d
    config.reset()


def _scheme(pair):
    return pair


def test_a_second_call_does_not_reglob(scheme_dir, monkeypatch):
    scheme, d = scheme_dir
    _doc(d / "ADR-001.md", 1)
    config.forget_documents()

    globs = []
    real = Path.glob
    monkeypatch.setattr(Path, "glob",
                        lambda self, pat: globs.append(pat) or real(self, pat))

    assert set(scheme.documents()) == {1}
    assert set(scheme.documents()) == {1}
    assert len(globs) == 1, f"one glob, got {len(globs)}"


def test_temp_documents_shares_the_same_glob(scheme_dir, monkeypatch):
    """Both read the same directory listing; one walk answers both."""
    scheme, d = scheme_dir
    _doc(d / "ADR-001.md", 1)
    _doc(d / "ADR-tmpabcde.md", 2)
    config.forget_documents()

    globs = []
    real = Path.glob
    monkeypatch.setattr(Path, "glob",
                        lambda self, pat: globs.append(pat) or real(self, pat))

    assert set(scheme.documents()) == {1}
    assert set(scheme.temp_documents()) == {"tmpabcde"}
    assert len(globs) == 1, f"one glob, got {len(globs)}"


def test_a_new_document_is_seen(scheme_dir):
    scheme, d = scheme_dir
    _doc(d / "ADR-001.md", 1)
    config.forget_documents()
    assert set(scheme.documents()) == {1}

    _doc(d / "ADR-002.md", 2)
    assert set(scheme.documents()) == {1, 2}, "adding a file moves the dir mtime"


def test_a_removed_document_is_seen(scheme_dir):
    scheme, d = scheme_dir
    _doc(d / "ADR-001.md", 1)
    _doc(d / "ADR-002.md", 2)
    config.forget_documents()
    assert set(scheme.documents()) == {1, 2}

    (d / "ADR-002.md").unlink()
    assert set(scheme.documents()) == {1}


def test_a_rename_is_seen(scheme_dir):
    """`luria concretize` renames a temporary document into its number."""
    scheme, d = scheme_dir
    _doc(d / "ADR-tmpabcde.md", 7)
    config.forget_documents()
    assert set(scheme.temp_documents()) == {"tmpabcde"}

    (d / "ADR-tmpabcde.md").rename(d / "ADR-007.md")
    assert set(scheme.documents()) == {7}
    assert scheme.temp_documents() == {}


def test_forget_clears_it(scheme_dir):
    """The escape hatch, for a writer that outruns mtime resolution."""
    scheme, d = scheme_dir
    _doc(d / "ADR-001.md", 1)
    config.forget_documents()
    assert set(scheme.documents()) == {1}
    config.forget_documents()
    assert set(scheme.documents()) == {1}
