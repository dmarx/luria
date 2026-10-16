### Added

- `views`: a Jinja template rendered over the record into any file in the
  repository, a root `CLAUDE.md` included ([ADR-tmpi08sj](record/decisions.d/ADR-tmpi08sj.md)). `luria index`
  renders each view with the others, and `--check` reports a stale one.
  A template reads the record through `doc(code)`, `docs(scheme, **where)`,
  `vocabulary(name)`, `schemes()` and `journals()`. A document's
  attributes are its scheme's fields, read as the scheme's contract reads
  them: any frontmatter field, a vocabulary default, a reference as the
  documents it names. A document also has `code`, `body` and
  `part(heading)`.
  Templates write codes bare: the output is linked by the same fixer
  `luria link --fix` uses, in the output's own frame, and transcluded
  text is rebased from its source's frame. Templates compose with Jinja's
  `include`, `import` and `extends`, resolved from the project root. The
  environment is sandboxed and strict, so an unknown code, field or part
  is an error naming the template's line, and `luria lint` renders every
  view so a broken template fails its own branch.
- `match(pattern)` in a view: every match of a path pattern as a row
  mapping each named node to its document, as in
  `{% for r in match("(c:CLAIM)<-[:concludes]-(g:ARG)") %}`. The pattern
  is one `luria.yaml` declares, by name, or one written inline in the same
  syntax and checked against the schemes the same way.
- `jinja2` is a new dependency.
