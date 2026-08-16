### Fixed

- **A tag page names its own scheme.** Pages for a non-ADR scheme were headed
  "ADRs tagged `x`" and counted "N of M decisions", regardless of what the
  scheme actually holds — the same wart `DEFAULT_STUB` already avoids for the
  index.
- **A tag blurb keeps its capitals.** `str.capitalize()` lowercases everything
  after the first character, so any blurb running past one sentence, or naming
  anything capitalised, was silently downcased.
