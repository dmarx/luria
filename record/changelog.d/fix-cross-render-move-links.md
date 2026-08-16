### Fixed

- `luria migrate`'s `move_doc` no longer leaves links pointing at a moved
  document's old address. A move always crosses schemes, and a scheme's
  address is more than its code — a same-render move changes the directory, a
  cross-render move changes the whole shape (`page.md#anchor` ↔ `dir/CODE.md`).
  Swapping the code inside the old link fixed the label and left the target
  pointing at a file that does not exist, silently, with the lint clean.

  Citations of a moved document are now found by the ADDRESS they point at
  rather than by their label, replaced with the new code, and linked by the
  fixer from the resolver — the one place that knows how each scheme is
  addressed. A worded citation is rewritten too, label and all: keeping the
  label resurrects the problem, because the `#17` left behind is itself a
  reference the fixer re-links to the anchor the move just vacated.
