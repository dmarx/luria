"""Frontmatter shape checks that PyYAML's default loader will not raise.

PyYAML treats a line that opens with `<!--` as a mapping key and keeps the
last of two identical keys. Quartz (and other strict YAML parsers) reject
both, so `luria lint` used to report a document clean while the downstream
Pages build went red (#164).
"""

from __future__ import annotations

import yaml


class DuplicateKeyError(yaml.YAMLError):
    """A YAML mapping repeats a key that SafeLoader would overwrite."""

    def __init__(self, key) -> None:
        self.key = key
        super().__init__(f"duplicate key {key!r}")


class StrictLoader(yaml.SafeLoader):
    """SafeLoader with a duplicate-mapping-key check at every depth."""


def no_duplicates(loader, node, deep=False):
    """Raise before SafeLoader silently collapses a duplicate mapping key."""
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            hash(key)
        except TypeError:
            # Preserve SafeLoader's existing ConstructorError for a mapping
            # key that YAML cannot make hashable.
            return yaml.SafeLoader.construct_mapping(loader, node, deep)
        if key in seen:
            raise DuplicateKeyError(key)
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, no_duplicates)


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


def check(errors: list[str], rel: str, text: str) -> None:
    """Reject HTML comments and duplicate mapping keys in YAML frontmatter."""
    block = frontmatter_raw(text)
    if block is None:
        return
    for line in block.splitlines():
        # Column 0 is what makes PyYAML treat `<!--` as a mapping key.
        # An indented `<!--` inside a folded scalar (e.g. `summary: >-`)
        # is legal content and must stay silent.
        if line.startswith("<!--"):
            errors.append(
                f"{rel}: HTML comment in YAML frontmatter — use a `#` "
                f"comment (PyYAML treats `<!--` as a mapping key)")
    try:
        yaml.load(block, Loader=StrictLoader)
    except DuplicateKeyError as error:
        errors.append(
            f"{rel}: duplicate frontmatter key {error.key!r} "
            f"(PyYAML keeps the last value; strict parsers reject it)")
    except yaml.YAMLError:
        # Let the existing SafeLoader call report or preserve all other YAML
        # behavior. This check only widens it for silent duplicate keys.
        pass
