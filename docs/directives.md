# Comment directives

Several checks take instructions from the prose they check. They share one
parser, one shape, and one scope rule
([ADR-008](../record/decisions.d/ADR-008.md)).

```
<name>[-block|-file]: <args> — <reason>
```

The directive must **open its comment**, `# noqa`-style, and is read only from
real comments: HTML comments in markdown (outside code), `COMMENT` tokens in
Python, text after a comment marker elsewhere. An example inside a fence or a
docstring is not a comment and does not fire — which is deliberate, and was
learned four separate times.

**A directive is one line.** Arguments stop at the newline, so a comment that
wraps loses everything after the break. Write a long list on one long line.

## Scope

The suffix decides, uniformly. **No directive has its own default.**

| form | governs |
|---|---|
| `name:` | its own line and the line below |
| `name-block:` | the run of non-blank lines it sits in |
| `name-file:` | the whole document |

A directive standing alone between blank lines has no content block of its own,
so `-block` there means the block it *introduces* — the next one. That is the
reading of "block", not an exception to it. A fenced code block counts as one
block even when it contains blank lines.

## `inactive-ok` — this reference is deliberate

Silences one reference to a retired (non-`Active`) document in the
reference-status report ([ADR-035](../record/decisions.d/ADR-035.md)).

```
<!-- inactive-ok: ADR-012 — the decision this one replaced -->
<!-- inactive-ok-block: ADR-012 — every mention in this paragraph -->
<!-- inactive-ok-file: ADR-012 — this page is that history -->
// inactive-ok: ADR-028 — proposed, but this is what shipped
```

Write the **full prefixed code**. A bare number is reported as a malformed
annotation rather than assumed to be a decision, which is what lets one
vocabulary serve more than one reference scheme
([ADR-006](../record/decisions.d/ADR-006.md)).

Acknowledgements are **counted** in the report, not hidden — and one that stops
applying (the document went `Active`, the reference moved) is reported in its
own right. A suppression that rots silently is the thing acknowledgements exist
to prevent.

## `unexempt` — lint this region anyway

The inverse: put a region the linter skips by default back under it. Code blocks
are exempt from the hyperlink lint because code is quoted, not asserted — but a
snippet in the docs can be quasi-prose, citing decisions a reader should be able
to follow.

```
<!-- unexempt-block: codeblock — the snippet below cites real decisions -->

<!-- this fence is now linted -->
```

Regions: `codeblock`, `inline-code`. An unknown region is reported, with the
known vocabulary named.

**The caveat is inherent, not a bug.** Markdown inside a fence renders
literally, so the link the lint then demands shows as `[ADR-004](…)` in the
sample. That is exactly the trade this directive exists to let an author make,
per block, rather than being settled once for a whole corpus.

## `unresolved-ok` — this code names nothing on purpose

A cited code that resolves to no document is reported
([ADR-014](../record/decisions.d/ADR-014.md)): it is a typo, another project's decision, or
an illustrative code in an example, and only a human can tell which. This
retires the third kind.

```
<!-- unresolved-ok: ADR-053 — a strata-g code, quoted as the worked example -->
# unresolved-ok-file: ADR-019 ADR-163 — fixture codes, deliberately not real
```

It is `inactive-ok` with **the validity check inverted**, which is the part
worth knowing. `inactive-ok` is malformed when it names a code that doesn't
resolve — it would excuse nothing. `unresolved-ok` is malformed when it names
one that *does*. Either way the annotation reports itself the day it stops
applying, which is the property that keeps a suppression from becoming a
silence.

A code inside a URL is never a citation, so linking out to another project's
decision needs no annotation at all — and that, rather than a bare code, is
how a foreign document should be named.

## `url-ok` — this URL is deliberately hand-written

A link whose label is a composed foreign code normally gets its URL
*constructed* — from the remote's config, the lockfile, or the code-only
convention ([ADR-016](../record/decisions.d/ADR-016.md)). When the
construction cannot be right — the remote's principles are sections of one
document, say, so there is no file to point at — the URL is written by hand,
and the hand-written target is a projection frozen at writing time
([DP-3](design-principles.md#dp-3)): if the remote later adopts a convention
or the lockfile learns the real filename, nothing updates it. So each one is
reported until acknowledged:

```
<!-- url-ok-block: SG-DP-18 — strata-g's principles are sections of one document -->

[SG-DP-18](https://github.com/dmarx/strata-g/blob/main/docs/design-principles.md#18-the-affordance-is-the-contract)
```

Same inverted validity as `unresolved-ok`: the annotation is stale when the
link it covers *matches* the construction (or is gone), so a suppression
reports itself the day it stops applying. A quoted link in backticks is a
specimen, not a citation, and needs no annotation.

Foreign codes only, deliberately ([ADR-022](../record/decisions.d/ADR-022.md)):
a foreign code has exactly one constructed URL, so "differs" means something,
while a local code has a family of legitimate targets and the same check would
flag correct links until acknowledging became reflex. A project that wants
stable absolute citations to its own record registers itself as a remote — as
Luria does with `LU` — and gets the check instead of an exemption from it.

## `target-ok` — this relative target deliberately resolves to nothing

Every other directive here is about a **code**. This one is about the **path**
wrapped around it, which is a different question and until recently an unasked
one: `[ADR-035](../../record/decisions.d/ADR-035.md)` can name a document that
exists while the path goes nowhere, and every code check passes.

The target is resolved from where the prose **renders**, not from where the
file sits — a journal entry lives five directories deep in
`record/reading.d/yyyy/mm/dd/` and is assembled into `docs/reading/`, so the
two frames give different answers and only one of them is what a reader
follows. This is the machine-checked half of the rule that says never
hand-write a target: write the bare code and let `luria link --fix` spell it.

A hand-written target is sometimes right anyway — a link into a build output
that is generated but not committed, a path a downstream consumer creates — so
it is reported until acknowledged, never an error on its own:

```
<!-- target-ok: build/report.html — written by CI, not committed -->

The [coverage report](build/report.html) is published per run.
```

The argument is the target as written, and the annotation is stale when the
link it covers starts resolving (or goes away). Links to URLs, to root-anchored
paths, to a heading in the same page, and targets carrying regex or
format-template metacharacters are not paths this repo can check, so none is
reported. A quoted link in backticks is a specimen, not a citation.

Promote the class with `fail_on = ["broken-targets"]` once a project's targets
are clean. The default is a warning because a wrong path is always wrong but is
not mechanically fixable the way a bare code is
([ADR-035](../record/decisions.d/ADR-035.md)).

## `unlinted` — this document opts out of reference checking

Every directive above is code-scoped: it excuses **one code**, and the
`-file` suffix only widens where the excuse applies. This one is deliberately
blunt — the whole document leaves the reference machinery (the bare-reference
lint, wikilink handling, and the reference-status scan):

```
<!-- unlinted-file: — vendored page; its references are quotes, not claims -->
```

It is **file-scoped only**, because a narrower "don't read references here"
already exists — that is what quoting a code in backticks does. A bare
`unlinted:` or `unlinted-block:` governs nothing and is reported as such.

The price of bluntness is visibility: files carrying this directive are
**counted and listed** in the
[reference-status report](reports/reference-status.md), the same bargain an
acknowledgement makes. The reports exist to converge on what nobody has
considered, and a whole-file exemption is the one suppression they cannot
converge past — so it must never be invisible.

Everything that isn't reference checking still applies: frontmatter, titles,
the generated-view staleness gate, a journal's path-vs-`created:` agreement.

## Fixture codes

A document code used **as an example** should never come from the real
sequence: the sequence eventually arrives, and the day it does, every
specimen starts resolving and every `unresolved-ok` that excused one goes
stale at once (this repository learned that when [ADR-032](../record/decisions.d/ADR-032.md) landed).

So the `FX` prefix is registered as a remote whose every code resolves to
this section:

```toml
[luria.remotes.FX]
name = "fixtures"
url  = "https://github.com/dmarx/luria/blob/main/docs/directives.md#fixture-codes"
```

Write `FX-ADR-032` or `FX-DP-9` in prose, tests or examples and it is a
first-class reference — `luria link --fix` links it here, nothing reports it
as dangling, and it can never collide with a real decision because it is not
in the sequence. No directive needed, ever.

One boundary: **directive arguments name local codes**, so `inactive-ok:`
and `unresolved-ok:` still take `ADR-…`, never `FX-ADR-…` — the prefix is
for *references*, not for the vocabulary that governs them.

## Adding a sixth directive

A name, not a new syntax: parse it out of `luria.directives.find(...)`, validate
its arguments with `directives.problems(...)`, and report the ones that no
longer apply. The scope rules and the comment handling come free —
`unresolved-ok` needed one inverted predicate, `url-ok` one comparison, and
nothing else.
