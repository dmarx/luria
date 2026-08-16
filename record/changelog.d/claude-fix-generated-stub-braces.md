### Fixed

- **A generated scheme's index no longer renders stray `{` and `}`.** The
  `README.stub` scaffolded for every non-ADR scheme carried `{{categories}}` and
  `{{table}}` — the `str.format` escaping convention — while `init.py`
  substitutes with `str.replace`, so the doubled braces survived into the file
  and every generated index carried two literal braces. The hand-shipped
  decisions stub uses single braces and was always correct, which is why this
  only affected schemes `luria init` generated.
