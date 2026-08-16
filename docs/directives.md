# Directives

An acknowledgement is a comment that says *I know, and I mean it.*

Findings exist to be resolved, and most of them are resolved by repair. Some are
not: a record whose whole job is to name what was abandoned cites retired
material correctly, and always will. Deleting the citation would be wrong;
un-retiring the target would be worse. So there is a third answer.

```markdown
<!-- inactive-ok: ADR-012 — the decision this one replaces -->
```

This is what makes propagation survivable. In one project's first retraction
wave, seventy findings appeared and forty-two of them were correct citations of
retired material. Without a way to say so, the only route to a green build would
have been to un-retire things — which is the one move that must never be how a
build goes green.

## The shape

```
<name>[-block|-file]: <args> — <reason>
```

The directive must **open its comment**, `# noqa`-style, and is read only from
real comments: HTML comments in markdown outside code, `COMMENT` tokens in
Python, text after a comment marker elsewhere. An example inside a fence or a
docstring is not a comment and does not fire — deliberate, and learned four
separate times.

**A directive is one line.** Arguments stop at the newline, so a comment that
wraps loses everything after the break. Write a long list on one long line.

**Write the reason.** It is not decoration. A suppression with no reason is
indistinguishable from a suppression nobody thought about, and the next person
cannot tell whether removing it is safe.

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

---

## `inactive-ok` — this reference to a retired document is deliberate

The main one. Silences a citation of a document that is not in force.

```markdown
<!-- inactive-ok: ADR-012 — the decision this one replaces -->
<!-- inactive-ok-block: ADR-012, ADR-019 — every mention in this paragraph -->
<!-- inactive-ok-file: ADR-012 — this page is that history -->
```

The annotation is **stale when it stops applying** — when the target comes back
into force, or the citation goes away. A suppression that has outlived its
reason is reported, which is the property that keeps a suppression from becoming
a silence.

Foreign codes are never status-checked (luria cannot know what another
repository has retired), so a code inside a URL needs no annotation. That, rather
than a bare code, is how a foreign document should be named.

## `unresolved-ok` — this code deliberately resolves to nothing

For illustrative codes: an example in documentation, a stand-in in a template,
a number in a docstring that must not become a link.

```markdown
<!-- unresolved-ok-file: ADR-919, ADR-157 — illustrative codes in the examples above -->
```

Prefer the alternative where you can. A registered `FX` remote prefix gives you
fixture codes that *resolve by construction*, so a template can carry examples
without an annotation per code, and without stealing a number from a live
sequence.

Inverted validity, like the others: the annotation is stale when the code starts
resolving — which is exactly what happens the day somebody mints the number your
example was borrowing.

## `url-ok` — this URL is deliberately hand-written

A link whose label is a foreign code normally has its URL *constructed* from the
remote's config. When construction cannot be right — the remote's principles are
sections of one document, say, so there is no file to point at — the URL is
written by hand, and a hand-written URL is frozen at writing time.

```markdown
<!-- url-ok-block: SG-DP-18 — strata-g's principles are sections of one document -->

[SG-DP-18](https://github.com/dmarx/strata-g/blob/main/docs/design-principles.md#18-the-affordance-is-the-contract)
```

Stale when the link starts matching what construction would produce.

## `target-ok` — this relative target deliberately resolves to nothing

Every directive above is about a **code**. This one is about the **path** around
it, which is a different question: `[ADR-035](../../record/decisions.d/ADR-035.md)`
can name a document that exists while the path goes nowhere.

Targets are resolved from where the prose **renders**, not from where the file
sits. A journal entry five directories deep renders into the journal's output;
the two frames give different answers, and only one is what a reader follows.
This is the machine-checked half of *never hand-write a target*.

```markdown
<!-- target-ok: build/report.html — written by CI, not committed -->

The [coverage report](build/report.html) is published per run.
```

Not checked at all: URLs, protocol-relative and root-anchored paths, same-page
anchors, and targets carrying regex or format-template metacharacters — a
`uid = "(\d{4})[.:](\d{4,5})"` in a config example is link-shaped by accident.

## `broad-ok` — this project noun is another sense of the word

Only fires if you have supplied a vocabulary *and* marked a scheme
`titles_generalize`. A principle stated about the artifact it was first noticed
on is a principle nobody applies to the next artifact, so a transferable
document's title is checked against your own local nouns.

```markdown
<!-- broad-ok: overlay — a verb here, not the UI noun -->
```

## `unexempt` — check this region after all

The inverse. Code spans and fenced blocks are skipped by the reference rules,
because markdown showing a link is not writing one. Occasionally a fenced block
genuinely does cite:

```markdown
<!-- unexempt-block: codeblock -->
```

Regions: `codeblock`, `inline-code`.

## `unlinted` — this document opts out entirely

Deliberately blunt, and file-scoped by design. The whole document leaves the
reference machinery: the bare-reference lint, wikilink handling, the status
scan.

```markdown
<!-- unlinted-file: vendored from upstream; codes here are theirs, not ours -->
```

For a fixture-heavy or vendored page where a directive per code is maintenance
without information. The price of bluntness is visibility: the reference report
counts the files carrying it, so an exemption nobody sees is not how a report
stops being a complete account.

---

## Wikilinks

Not a directive, but the same idea from the other side. `[[ADR-012]]` is you
asserting *this is a reference*, so both failure modes are violations with
different remedies:

- resolvable, not yet linked → run `luria link --fix`
- unresolvable → an error the fixer cannot clear, because the request was
  explicit. Fix the code or remove the brackets.

`[[ADR-012|the caching decision]]` gives prose as the label. Still the fixer's
job.

## Choosing

| Situation | Answer |
|---|---|
| the citation is wrong now | repair it — this is most findings |
| the citation is *about* the retirement | `inactive-ok:` with the reason |
| a code that must never resolve | `FX` fixture prefix; `unresolved-ok:` if you can't |
| a path CI creates | `target-ok:` |
| a whole vendored page | `unlinted-file:` |
| you have not decided yet | leave it listed; a warning is not a failure |

The last row is a real answer. An undecided finding belongs in the report and in
the badge count, which is where undecided things go.
