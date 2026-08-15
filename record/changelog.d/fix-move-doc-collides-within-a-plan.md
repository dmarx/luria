### Fixed

- **`move_doc` lands a document under a temporary code, not a number.** "The
  next free number" is no more a fact inside a migration than it is on a
  branch: every operation plans against the tree as it is *now*, so two moves
  into one scheme both read the same highest number, and the second `git mv`
  silently overwrote the first. The move now mints a temp code
  ([ADR-049](record/decisions.d/ADR-049.md)) and `luria concretize` assigns the
  real number afterwards, at the serialization point — the same bargain
  `luria new` already makes, rather than a second allocator with its own
  arithmetic. The document ends up carrying both aliases: the code it migrated
  from, and the provisional one it wore in between.

- **`luria concretize` rewrites the anchor spelling too.** Its sweep was a
  case-sensitive replace, so it upgraded `ADR-tmp47fje` but walked straight
  past `#adr-tmp47fje` — leaving a live link pointing at a heading that no
  longer existed. Generated views are re-derived and were never at risk; a
  hand-written or migration-written link was.

- **`Pair` no longer returns a tail typed `int | str`.** The padded-number
  spelling and the opaque temporary identity are not the same kind of value,
  and collapsing them pushed the ambiguity out to every call site, which then
  had to test the type to learn which it had. Replaced with `old_parts`,
  `new_parts`, `new_is_provisional` and `new_anchor_tail`, so the padding
  question and the provisional question are asked separately — they are
  separate questions. A test now pins that a rename mirrors each citation's
  own spelling: `DP-004` stays padded, `DP-4` stays bare, the anchor stays
  bare.
