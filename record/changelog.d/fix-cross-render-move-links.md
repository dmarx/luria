### Fixed

- `luria migrate`'s `move_doc` no longer leaves links pointing at a moved
  document's old address. A move always crosses schemes, and a scheme's
  address is more than its code — a same-render move changes the directory, a
  cross-render move changes the whole shape (`page.md#anchor` ↔ `dir/CODE.md`).
  Swapping the code inside the old link fixed the label and left the target
  pointing at a file that does not exist, silently, with the lint clean.
  Citations of a moved document are now matched by the ADDRESS they point at,
  stripped to bare references, and rebuilt by the fixer from the resolver —
  the one place that knows how each scheme is addressed.
