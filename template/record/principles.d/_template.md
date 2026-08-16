---
# Don't copy this file by hand — run `luria new dp`, which assigns the identity
# and fills in the fields a machine can compute. WHICH identity depends on the
# scheme's `allocate` mode: `filing` (the default) takes the next free number
# on the spot, `merge` mints a temporary code that `luria concretize` numbers
# where merges serialize (FX-ADR-049).
#
# Numbering is sequential and permanent: a principle is cited by number ("per
# DP-3"), so a number can be retired but never reused. The filename is the code
# and nothing else; the title goes in `title:` below, where a revision costs an
# edit rather than a rename plus every link — which matters more here than for
# a decision, because principles are expected to be reworded. Why: LU-ADR-013.
#
# This frontmatter is the ONLY place these facts live. `docs/design-principles.md`
# is generated from it — never edit that file by hand; run `luria index`.
# Why: LU-ADR-012.

# Same vocabulary as a decision: Active | Proposed | Deferred |
# Superseded | Rejected, optionally " — <note>". A principle that stops being
# believed is Superseded, not deleted — something out there cites it.
status: Active

# The claim, as it appears in the rendered document. Repeat it as the body's
# `# DP-NNN:` heading; `luria lint` checks that the two agree.
title: The principle, stated as a claim you can disagree with

# Principles are LIVING DOCUMENTS. Bump this whenever the principle's scope or
# claim changes, and add a `history:` entry saying what changed. A principle
# stated about one artifact is a principle nobody applies to the next one, and
# the version is how the next reader can tell that already happened once.
version: 1

# Browsing categories, shared with the decisions (see decisions/tags.yaml).
tags:
- craft

date: '2026-01-01'

# The decisions whose experience produced this principle — the inverse of the
# usual direction, in which decisions cite principles. Rendered as followable
# backlinks under the principle, and they are the evidence that stops it reading
# as taste. List them as full codes, one per line. Empty is honest for a
# principle carried in from elsewhere.
influenced_by: []

# Optional, and only once there IS a version 2. One entry per version, oldest
# first, each saying what changed and why — the revision is usually the most
# useful thing the principle teaches.
# history:
# - version: 1
#   date: '2026-01-01'
#   note: >-
#     Stated narrowly, about one artifact.
# - version: 2
#   date: '2026-02-01'
#   note: >-
#     Generalized, after the second instance made the narrow statement useless.

# Where this came from: the concrete episode that made it a principle, not a
# preference. One sentence, rendered at the end of the principle's metadata
# line — so it is read every time the principle is. Prose, like `summary:`:
# references here are linked by `luria link --fix` and checked by the lint,
# because the value is rendered as markdown. (The rest of the frontmatter is
# data, read by value, and stays plain.)
origin: >-
  The specific thing that happened twice.

# Optional. Not rendered in the document — the principle's own text is right
# there — but it is what a `render = "index"` scheme would show, and what a
# reader of the frontmatter alone gets.
summary: >-
  The principle in two or three sentences, stated as a claim rather than a topic.
---

# DP-NNN: The principle, stated as a claim you can disagree with

The claim, in the imperative or the declarative — never as a topic heading. A
reader should be able to hold the first sentence in their head and apply it.

Why it is true: the mechanism, not the vibe. What goes wrong when it is ignored,
concretely enough that someone can recognize the situation from the description.

Applied here: two or three places in *this* codebase where the principle is
visibly in force. This section is what makes a principle citable instead of
decorative — it shows the reader what compliance looks like.

The corollary people skip, if there is one. Most principles have a second-order
consequence that is the actually expensive part to follow, and naming it is
worth more than restating the claim.
