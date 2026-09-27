# Configuration reference

Luria reads `luria.yaml` from the project root.

This page is a structured reference to the main public configuration concepts. The code/schema should remain the ultimate exact contract; generated reference can replace parts of this page where practical.

## Top-level families and settings

Common top-level keys include:

```text
issue_url
paths
code
lint
site
vocabularies
schemes
chains
journals
fragments
remotes
include_records
```

Settings tables such as `paths`, `code`, `lint`, and `site` merge by key with defaults. Project-named family tables such as schemes/fragments/journals/remotes are the project's declared families rather than fixed built-ins.

## `vocabularies`

A named vocabulary declares allowed terms and their display/explanatory metadata.

A vocabulary can back fields on one or more schemes.

Use vocabularies for:

- standing,
- categories,
- epistemic axes,
- chain facets,
- other closed/open semantic languages.

## `schemes`

A scheme commonly declares:

```yaml
schemes:
  RFC:
    dir: record/rfcs.d
    output: docs/rfcs
    active: Accepted
    render: index
    allocate: merge

    fields: {}
    references: {}
    field_groups: {}
```

### Common scheme concepts

- `dir` — authoritative source directory.
- `output` — generated read surface.
- `active` — standing treated as active/current.
- `render` — how the scheme is projected (for example index/document).
- `allocate` — filing-time or merge-time identity allocation.
- `fields` — plain or vocabulary-backed structured fields.
- `references` — typed relations.
- `field_groups` — cardinality constraints across alternative fields.

### Field options

A field may be:

- required,
- list-valued (`many`),
- unique,
- conditionally required (`required_when`),
- vocabulary-backed,
- labeled/described for readers.

### Field groups

Use a field group when several fields collectively satisfy one semantic requirement.

Example:

```yaml
field_groups:
  source:
    fields:
      - arxiv
      - doi
      - url
    require: at-least-one
```

### Reference options

A reference declares:

```yaml
references:
  extends:
    scheme: RFC
    required: false
    many: false
    converse: extended_by
    invariant: tags
```

References may also carry labels/blurbs and conditional requirements.

## `chains`

A chain walks one or more same-scheme references into generated sequences.

```yaml
chains:
  lineage:
    scheme: RFC
    relation:
      - extends
      - corrects
    sibling: compared_against
    facet_by:
      - status
      - consensus
    invariant: tags
    output: docs/lineage.md
    title: RFC lineage
    blurb: How the design developed
```

### `scheme`

The scheme whose objects make up the sequence.

### `relation`

One relation field or a list of relation fields forming the chain spine.

Each must be a declared reference on the scheme and must point back to the same scheme.

### `sibling`

Optional declared same-scheme relation rendered as a peer/rival rather than a successor step.

### `facet_by`

One field or a list of fields rendered on each step.

Every facet must be nameable on the scheme.

The default is `status`.

### `invariant`

Optional field whose values are asserted to bind the line.

Use relation-level invariants instead when the assertion belongs to a specific edge or crosses schemes.

### `output`

Required generated page path.

### `title`, `blurb`

Human-facing description of the generated chain.

## `journals`

A journal declares persistent dated observations.

Common keys:

```yaml
journals:
  devlog:
    dir: record/devlog.d
    output: docs/devlog
    granularity: month
    title: Development log
```

## `fragments`

A fragment directory declares contributions assembled into another artifact.

Example:

```yaml
fragments:
  record/changelog.d:
    file: CHANGELOG.md
    style: changelog
```

## `remotes`

Remotes declare foreign records or identifier namespaces.

Use them to make external identifiers part of the citation model rather than leaving them as arbitrary URLs.

## `lint`

Common policy controls include:

```yaml
lint:
  fail_on: []
  mute: []
  baseline: {}
  narrow_terms: []
  network: auto
```

- `fail_on` — promote warning classes to failures.
- `mute` — hide selected classes.
- `baseline` — hold a class to a known count/regression threshold.
- `narrow_terms` — project-specific vocabulary for title checks.
- `network` — remote verification policy (`auto`, `never`, or `require` in the current implementation).

## `site`

Publication settings include:

```text
publish
title
base_url
source_url
exclude
icon
logo
logo_dark
theme
```

The default publishing model and site staging are governed by [ADR-042](../../record/decisions.d/ADR-042.md).

## Validation philosophy

Luria validates declarations eagerly when a wrong declaration would otherwise produce a silent empty result.

For example, a chain over a nonexistent relation could render an empty page indistinguishable from a legitimately empty lineage.

This follows the broader principle that silent non-events should not masquerade as success.
