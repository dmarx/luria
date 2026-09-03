# Contributing

Thanks for helping. Two things make this repository slightly unusual, and
both are the point: it dogfoods its own record machinery, and the record
is part of every contribution.

## The loop

```console
$ pip install -e ".[dev]"
$ python -m pytest tests -q     # what CI runs
$ luria lint                    # also what CI runs
```

Work on a branch, open a pull request — nothing lands on `main` directly.
CI runs `luria repair` on your branch and commits what it wrote as
`github-actions[bot]` (a bare code linked, a missing `created:` filled —
pull before you push again), then regenerates the derived views on the
runner, lints the result, and runs the tests. The views themselves are
committed on `main` only, by the bot, after merge — so do not commit
regenerated views on a branch, and if you have, a conflict in one is
resolved by regenerating, never by hand.

## Every change ships its record entry

Run `luria new` in the same branch as the work:

- `luria new changelog` — a fragment describing the user-visible change.
  Fragments are collected into `CHANGELOG.md` by a scheduled job; you
  never edit that file directly.
- `luria new --title "…"` — a devlog entry, for anything worth more than a
  changelog line: the root cause, the approach that failed, the trap you
  fell into.
- `luria new adr --title "…"` — a decision document, when you chose
  between real alternatives. It gets a temporary code (`ADR-tmpxxxxx`);
  CI assigns the real number when the merge serializes on `main`, so
  parallel branches never collide on one.

Cite decisions from code comments and docs by their bare code and run
`luria link --fix` — never hand-write the link target.

## Changing the machinery

- Generated files (anything stamped `GENERATED`, plus `CHANGELOG.md` and
  the README badge region) are never edited by hand. Change the sources or
  the renderer, then `luria index`.
- A new lint check must be **always wrong and mechanically fixable** to
  fail the build; anything that needs human judgement becomes a *report*
  with an acknowledgement directive
  ([docs/directives.md](docs/directives.md)). Fire a new guard on a real
  case before trusting it, and note the firing in the devlog.
- The configuration reference is generated from the dataclasses in
  `luria/config.py` — their docstrings are the schema documentation, so a
  config change edits those docstrings, not `docs/configuration.md`.
- `tests/test_examples.py` builds each directory under `examples/` in a
  temporary tree and generates its views there; an example is a pinned,
  CI-tested claim about what a configuration does.

## Releases

Versioning is from git tags (`hatch-vcs`). Publishing a GitHub release
builds the wheel, verifies the built version matches the tag, smoke-tests
`init → index → new → lint` in a clean venv, and uploads to PyPI.
