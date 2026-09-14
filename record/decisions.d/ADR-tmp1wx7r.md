---
status: Proposed
title: "An anchor is an id, and a fragment link is checked against one"
version: 1
tags:
- mechanism
- record
date: '2026-09-14'
summary: >-
  The generator anchored assembled documents and journal entries with
  `<a name="x">`. That is reachable on a real navigation and nowhere else, so
  every one of those links worked in the repository and on GitHub and landed
  at the top of the page on the published site — 89 of the 100 fragment links
  in this repository. Emits `id` instead, and adds a check with a `--fix`, so
  the next hand-written anchor cannot put it back. Corrects ADR-094, whose
  measurement was right and whose stated cause was not.
---

# ADR-tmp1wx7r: An anchor is an id, and a fragment link is checked against one

<!-- inactive-ok-file: ADR-094 — Proposed. This decision corrects it, so it has to name it; the citation is to what that decision said, not a claim it is settled. -->

## Context

A fragment link — `2026-09.md#20260914042025` — is resolved by whatever
renders the page, and the renderers do not agree on what an anchor is.

    <a id="x">      an element with that id. Reached by navigation and by
                    `getElementById` alike.
    <a name="x">    neither. The HTML spec has a real navigation fall back to
                    `a[name]`; nothing else does.
    ## Heading      an id from every renderer there is, derived from the text.

Luria emitted the middle one. `journal.render_book` wrote
`<a name="20260914042025"></a>` before each entry, and `render_document` wrote
`<a name="dp-3"></a>` before each source it assembled.

That works in the repository, and on GitHub, and in any editor preview —
because those are real navigations. It does not work on a Quartz site, which
is what `luria site` builds and what this record publishes to. Quartz is a
single-page app; its router scrolls with

    document.getElementById(decodeURIComponent(url.hash.substring(1)))

(v4.5.2, `quartz/components/scripts/spa.inline.ts`, both call sites), which
finds an `id` and nothing else.

**89 of the 100 fragment links in this repository resolved by `name` and no
other way.** Every entry link on every devlog index — 55 in September alone —
and every citation of a design principle. All of them landed at the top of the
page they named.

The shape of the failure is the thing to take from it: **it was correct
everywhere a contributor would check and wrong only where a reader would
read.** Every check luria runs reads markdown, and `docs/devlog/2026-09.md`
resolves perfectly as a path; the anchor is genuinely in the file; the link is
genuinely spelled right. Nothing short of loading the built site could see it.

[ADR-094](ADR-094.md) measured this and got the cause wrong — it recorded that Quartz
"drops the element", and rejected "emit anchors that survive the publisher" on
that basis, as a fix that would need re-finding for each publisher. Quartz
drops nothing: the `<a>` is in the published HTML. The rejected alternative was
one attribute, and correct. That ADR is corrected in place and versioned
([ADR-001](ADR-001.md)'s rule: the choice stood, the reason was wrong).

## Decision

**The generator emits `id`.** Both emitters, one attribute each. `id` is
reachable by every means `name` was and by `getElementById` as well, so this
is strictly a widening — no link that worked stops working.

**`doc_refs` reads either spelling.** A project whose principles are still one
hand-written file may anchor them by `name`, and that file resolves fine where
it is read. Refusing to read it would turn a publishing defect into a parsing
one.

**A check, with a `--fix`.** `luria lint` reports a fragment link whose target
answers to it by `<a name=>` alone; `luria link --fix` rewrites the anchor.
The check is what makes this stay fixed — the generator is not the only thing
that writes an anchor, and the next hand-written one would put the bug back
silently, which is the polarity [DP-3](../principles.d/DP-003.md) rules out.

Two things the check has to get right, and both were wrong first:

- **It reads views.** Every other reference rule reads sources, correctly: a
  view is rewritten by the next build, so a finding about one is a finding
  nobody can act on where it is reported. But the motivating case is a
  *journal index linking into a journal book*, and both are generated. A
  check that only reads sources is a check shaped so it cannot see the defect
  it exists for ([DP-4](../principles.d/DP-004.md)). `doc_files(views=True)` is the exception, and the
  anchor check is the only caller.
- **It resolves from `link_base`, not from the file's own directory.** A
  `render = "document"` scheme's prose is written to resolve from the page it
  assembles into, so `../../docs/values.md` in a source is correct there and
  nonsense from the source's folder. Resolving naively reported five real
  links as broken targets.

**The repair is the target's, and its owner decides the remedy.** The link is
spelled correctly; the thing it names cannot be found. So `--fix` edits the
document holding the anchor — and never a view, because the next `luria index`
would erase it. A finding about a view says `luria index` instead, which is
the repair that actually lands.

## Alternatives considered

- **`<a id="x" name="x">`.** Belt and braces, and it costs nothing. Rejected
  because `name` on `<a>` is obsolete in HTML5 and adds nothing `id` does not
  already do — carrying it would be carrying the spelling that caused this, in
  the file that documents the fix.
- **Give the entries their own pages instead of anchors in a book.** The other
  reading of "the link is broken": stop assembling. It is a real option for a
  journal and a bad trade for this one — a book read in order is the point of
  the granularity setting — and it would not have touched the principles case
  at all, where the anchors and the assembly are both wanted.
- **Leave the generator and widen `cite` to cover journals.** What [ADR-094](ADR-094.md) did
  for principles, applied again. Rejected as the same workaround twice: `cite`
  is a preference about where a citation should land, and using it to route
  around an anchor that does not work makes it impossible to tell the two
  reasons apart later. This change is why [ADR-094](ADR-094.md)'s key is now a preference.
- **Check that every fragment resolves to something.** Broader, and tempting.
  Rejected for this change: a fragment naming a heading is resolved by a slug
  each renderer computes slightly differently, so the check would have to
  model several slugifiers to avoid reporting links that work. The finding
  here needs none of that — `name`-only is unambiguous, mechanically
  repairable, and the whole of what was actually broken.

## Consequences

`luria index` rewrites every anchor in this record's views in one pass, and
the 89 links resolve. Any adopter's record does the same on its next build;
nothing in a source has to change.

The check reads views, so it is the one reference rule that can report a
finding a contributor cannot fix where it is reported. That is the right
trade here and worth knowing: the message says `luria index`, and the
existing staleness check already means a record whose views disagree with its
sources is failing for another reason too.
