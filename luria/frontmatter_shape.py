"""Frontmatter shape checks that PyYAML's default loader will not raise.

PyYAML treats a line that opens with `<!--` as a mapping key and keeps the
last of two identical keys. Quartz (and other strict YAML parsers) reject
both, so `luria lint` used to report a document clean while the downstream
Pages build went red (#164).
"""

from __future__ import annotations

import yaml


def frontmatter_raw(text: str) -> str | None:
    """The YAML block between the opening and closing `---` fences, or None
    when the document has no well-formed frontmatter. Kept as raw text so a
    check can see what PyYAML silently rewrites."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 3)
    if end == -1:
        return None
    return text[4:end + 1]


# The C parser where it is built: this runs once per document on every lint.
_Base = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


class _Strict(_Base):
    """A loader that refuses a repeated key in any mapping, at any depth and
    in any spelling, by asking the parser that would otherwise collapse it
    (#240). The line scan this replaced missed `"title":` after `title:` and
    every indented key."""


class _Duplicate(yaml.YAMLError):
    def __init__(self, key, mark) -> None:
        super().__init__(f"duplicate key {key!r}")
        self.key, self.mark = key, mark


def _no_duplicates(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        # `<<` merges are YAML's override spelling: an explicit key after
        # one is meant to win, so only the mapping's own keys are compared.
        if key_node.tag == "tag:yaml.org,2002:merge":
            continue
        key = loader.construct_object(key_node, deep=True)
        try:
            if key in seen:
                raise _Duplicate(key, key_node.start_mark)
            seen.add(key)
        except TypeError:  # an unhashable (complex) key; nothing to compare
            continue
    return loader.construct_mapping(node, deep)


_Strict.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                        _no_duplicates)


def check(errors: list[str], rel: str, text: str) -> None:
    """Reject HTML comments and duplicate mapping keys in YAML frontmatter."""
    block = frontmatter_raw(text)
    if block is None:
        return
    for line in block.splitlines():
        # Column 0 is what makes PyYAML treat `<!--` as a mapping key.
        # An indented `<!--` inside a folded scalar (e.g. `summary: >-`)
        # is legal content and must stay silent. This half stays a text
        # check: no loader raises on a key that happens to read `<!--`.
        if line.startswith("<!--"):
            errors.append(
                f"{rel}: HTML comment in YAML frontmatter — use a `#` "
                f"comment (PyYAML treats `<!--` as a mapping key)")
    try:
        yaml.load(block, Loader=_Strict)
    except _Duplicate as dup:
        # The block starts on the file's second line, after the fence.
        errors.append(
            f"{rel}: duplicate frontmatter key {dup.key!r} at line "
            f"{dup.mark.line + 2} (PyYAML keeps the last value; strict "
            f"parsers reject it)")
    except yaml.YAMLError:
        pass  # malformed YAML is reported where the frontmatter is parsed
