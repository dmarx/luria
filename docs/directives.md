# Comment directives

The lint's warning classes are judgement calls: a citation of a superseded
decision might be exactly right (history, or a rejection worth pointing
at), and only a human can say so. Directives are how a judgement, once
made, is written down *where the finding is* — so the check stops asking,
the reason survives, and the report still counts what was acknowledged.

## Shape

A directive lives in a comment — HTML comments in markdown, `#`, `//`,
`/* */` or `--` comments in code — and reads:

```
<!-- inactive-ok: ADR-012 — the rejection is the point being made -->
```

That is: a **name**, optional **scope suffix**, a colon, **arguments**
(codes, paths, or keywords, separated by spaces or commas), and after an
em-dash, the **reason**. The reason is prose for the next reader; write
one.

Scope is how much text the directive governs:

| spelling | governs |
|---|---|
| `name:` | its own line and the next line |
| `name-block:` | the paragraph (blank-line-delimited block) it sits in, or the following block when the comment stands alone |
| `name-file:` | the whole file |

A directive that no longer matches anything — the document went `Active`
again, the hand-written URL was fixed, the argument has a typo — is itself
reported under `stale-directives`, so acknowledgements cannot quietly
outlive what they excuse.

## The vocabulary

| directive | acknowledges | argument |
|---|---|---|
| `inactive-ok:` | a citation of a document that is not in force (`retired-citations`) | the code(s) |
| `unresolved-ok:` | a code that resolves to no document, kept deliberately (`unresolved-codes`) | the code(s) |
| `url-ok:` | a remote code linked to a hand-written URL instead of the constructed one (`hand-written-urls`) | the code(s) |
| `target-ok:` | a relative link target that resolves to nothing from where the prose renders (`broken-targets`) | the exact target |
| `broad-ok:` | a term flagged by `narrow-titles`, used in a legitimately broad sense | the term(s) |
| `unlinted-file:` | opts the entire file out of reference checking — the blunt tool for fixture-heavy or vendored pages. File-scoped by design; counted in the report rather than hidden | — |
| `unexempt:` | the reverse of an exemption: makes the linker treat code regions as prose again, for pages *about* the reference syntax | `codeblock`, `inline-code` |
| `pin:` | not an acknowledgement — a *registration*: marks a cited URL for content pinning, so `luria remotes --pin` endorses its bytes and the lint reports when they change (`remote-drift`) | the URL(s) |

Each acknowledgement covers findings at its own site only — that locality
is the point. Vouching for one citation of a retired decision says nothing
about the next one, which gets its own look and its own reason.

One warning class is acknowledged without a directive on purpose:
`remote-drift` (a pinned document whose content changed upstream) is
cleared by re-endorsing — `luria remotes --pin CODE` after reviewing the
change — because the judgement lives in the lockfile, not in prose at a
citation site.

`pin:` runs the other way from every acknowledgement: it *arms* a check
rather than quieting one. Flag a URL where it is cited —

```
<!-- pin: https://spec.example/v1.html — the spec this implements -->
We follow [the spec](https://spec.example/v1.html).
```

— and `luria remotes --pin` endorses its content by hash; from then on the
lint reports when the bytes change. The URL must appear in text the
directive governs (its own comment doesn't count), so a flag whose
citation was deleted reports itself under `stale-directives` like any
other directive. Deleting the flag retires the pin — the next bare
`luria remotes --pin` prunes it — so a pin that fires too often costs one
removed comment, and the URL goes back to being an ordinary, unwatched
link. Foreign codes need no flag: `luria remotes --pin LU-ADR-013`
already covers them.

## Mentioning a code without citing it

Backticks are the lighter tool and usually the right one: a code inside
`` ` `` inline code `` ` `` or a fenced block is masked from the reference
machinery entirely — not linked, not counted, not checked. That is how
documentation (including this page) shows codes as *syntax*. A directive is
for the cases where the code should stay bare prose and still be excused.

## Fixture codes

Documentation and tests need example codes that look real but
deliberately resolve to nothing in this record. Rather than sprinkle
`unresolved-ok:` everywhere, this project reserves the `FX` remote prefix
for them: a code like `FX-ADR-001` is declared, resolves by a fixed URL
template (to this section), and reads unambiguously as "an example, not a
citation". Any project can adopt the same convention with a one-table
remote:

```toml
[luria.remotes.FX]
name = "fixtures"
url  = "https://github.com/dmarx/luria/blob/main/docs/directives.md#fixture-codes"
```

## Design notes

- Directives are found by tokenising real comment syntax per file type, so
  a string that merely *looks* like a directive in running prose does not
  fire.
- Arguments are validated: a directive naming an unknown code, an unknown
  region keyword, or nothing at all is reported rather than silently inert.
- The reports remain a complete account. Every acknowledgement is counted
  next to what it silenced — the bargain is *quiet checks*, never *hidden
  findings*.
