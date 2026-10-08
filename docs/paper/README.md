<!-- docs/paper/README.md -->

# The Architecture of a Living Corpus

A conceptual paper (draft) on what makes a body of writing *living*, with Luria
as the motivating example and its own record as the case study. It argues that a
corpus lives when it can change its mind accountably, that this needs the
equivalent of Hart's secondary rules, and that the resulting architecture is a
set of six distinctions Luria happens to implement.

## Reading order

1. [Abstract](00-abstract.md)
2. [Introduction](01-introduction.md)
3. [A motivating example](02-motivating-example.md)
4. [What it is for a corpus to live](03-what-it-is-to-live.md)
5. [Secondary rules for knowledge](04-secondary-rules.md)
6. [Standing and dependence](05-standing-and-dependence.md)
7. [Authority, judgment, and self-governance](06-authority-and-judgment.md)
8. [Forgetting without deletion](07-forgetting.md)
9. [The record on itself](08-the-record-on-itself.md)
10. [Objections and limits](09-objections.md)
11. [Related work](10-related-work.md)
12. [Conclusion](11-conclusion.md)
13. [References](references.md)

## Building

The files are numbered in reading order, and `metadata.yaml` carries the title
and author. Pandoc assembles them (no LaTeX is needed for HTML or Word):

```console
$ cd docs/paper
$ pandoc --metadata-file=metadata.yaml 0*.md 1*.md references.md --number-sections \
    --standalone --toc -o living-corpus.html
```

Output files are not committed. Codes in the text are links into this
repository's record and resolve only when the pages are read in place; in a
built copy they point at files that are not there.

## How the paper relates to the record

The paper cites the decisions and principles it relies on by code, so it is a
dependent of them in the sense of [Concepts](../concepts.md): if one is retired,
`luria lint` names the paragraph that relied on it. Where a section cites a
retired decision on purpose, as history, an `inactive-ok` comment at the top of
the file says why. The figures in [the record on itself](08-the-record-on-itself.md)
were taken at the commit named there and will drift as the record moves; they
are a dated observation and not a maintained count.
