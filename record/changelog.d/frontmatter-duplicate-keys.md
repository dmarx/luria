### Fixed

- The duplicate-frontmatter-key check now asks the YAML parser instead of scanning lines. It reports a key repeated in another spelling (`"title":` after `title:`) or inside a nested mapping, and names the line ([#240](https://github.com/dmarx/luria/issues/240)).
- Journal entries (devlog, changelog) get the frontmatter shape check scheme documents already had: HTML comments and duplicate keys ([#240](https://github.com/dmarx/luria/issues/240)).
