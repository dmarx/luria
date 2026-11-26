### Added

- The published site titles a page by `site.page_title`, a template over
  `{code}` and `{title}` ([#405](https://github.com/dmarx/luria/issues/405)). The default, `{code}: {title}`, is today's
  form; `"{title}"` titles pages by their title alone. A body heading that
  repeats the page title, with or without the code, is dropped either way.
  The template is checked by the same rule as a scheme's `heading:`.
