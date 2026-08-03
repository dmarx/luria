# Comment directives

Two checks take instructions from the prose they check. They share one parser,
one shape, and one scope rule ([ADR-008](decisions/ADR-008.md)).

```
<name>[-block|-file]: <args> — <reason>
```

The directive must **open its comment**, `# noqa`-style, and is read only from
real comments: HTML comments in markdown (outside code), `COMMENT` tokens in
Python, text after a comment marker elsewhere. An example inside a fence or a
docstring is not a comment and does not fire — which is deliberate, and was
learned four separate times.

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
[reference-status report](decisions/ADR-007.md).

```
<!-- inactive-ok: ADR-012 — the decision this one replaced -->
<!-- inactive-ok-block: ADR-012 — every mention in this paragraph -->
<!-- inactive-ok-file: ADR-012 — this page is that history -->
// inactive-ok: ADR-028 — proposed, but this is what shipped
```

Write the **full prefixed code**. A bare number is reported as a malformed
annotation rather than assumed to be a decision, which is what lets one
vocabulary serve more than one reference scheme
([ADR-006](decisions/ADR-006.md)).

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

## Adding a third directive

A name, not a new syntax: parse it out of `luria.directives.find(...)`, validate
its arguments with `directives.problems(...)`, and report the ones that no
longer apply. The scope rules and the comment handling come free.
