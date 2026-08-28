### Changed

- A remote's code now relates to a set of *named URIs* rendered through one
  template vocabulary ([ADR-tmpo1286](record/decisions.d/ADR-tmpo1286.md)): `url` and `pin_url` are the short
  spellings of `uris.read` and `uris.bytes`, a `[luria.remotes.X.uris]`
  table names further relations, and {filename} is an ordinary template
  variable fed by the discovered lockfile map, authority semantics
  included — so a GitLab-style raw scheme with slug filenames is two
  template lines. The GitHub blob→raw rebase regex is gone, replaced by
  shipped default templates; the one behavioral change is that a `url`
  template rendering a blob-shaped URL no longer implies pinnable bytes —
  declare `uris.bytes` (or `pin_url`) instead.
