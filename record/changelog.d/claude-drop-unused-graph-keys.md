### Removed

- **`[luria.site] graph`, `graph_height` and `graph_depth` are gone**, having
  never done anything. They reached `main` as schema without an implementation:
  documented in the configuration reference, accepted in `luria.toml`, parsed
  into a `Path`, and read by nothing. A project that set `graph` got its
  Quartz local graph and no explanation. They return with the code that
  implements them.

### Added

- A test that a `[luria.site]` setting is read by something. A key in the
  schema publishes itself into the generated reference, so an unimplemented
  one looks exactly like a working feature from the outside.
