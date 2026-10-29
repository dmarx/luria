### Fixed

- **`luria lint` no longer stalls on a long author list.** The reference-entry
  detector's author-lead pattern backtracked exponentially on an entry with
  more names than it allows. One 26-author entry in dmarx/nucleation took four
  minutes, holding the interpreter lock, so every other thread stalled with
  it. The run of names is now possessive and fails in linear time.

### Changed

- **`luria lint` is about four times faster on a large record**, with
  byte-identical output: dmarx/nucleation (5,519 scanned files, network off)
  went from 614s to 145s on one machine. Besides the fix above: the reference
  scanners skip a scheme's or remote's patterns when its prefix is absent
  from the text, build their masks and line indexes with slices and `bisect`
  instead of a loop per character, and match the reference report's codes
  over a whole file rather than line by line. `is_generated`,
  `is_historical` and `link_base` index the config once instead of comparing
  paths on every call. A scheme's set of resolvable codes is kept until its
  directory changes. The lint's reference report reuses the corpus scan the
  report render already made, as `reports.reference_status` already did.
