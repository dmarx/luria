"""Frontmatter shape checks that PyYAML's default loader will not raise.

PyYAML treats a line that opens with `<!--` as a mapping key and keeps the
last of two identical keys. Quartz (and other strict YAML parsers) reject
both, so `luria lint` used to report a document clean while the downstream
Pages build went red (#164).
"""

from __future__ import annotations


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
    seen: dict[str, int] = {}
    for line in block.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("<!--"):
            errors.append(
                f"{rel}: HTML comment in YAML frontmatter — use a `#` "
                f"comment (PyYAML treats `<!--` as a mapping key)")
        # Top-level mapping keys only: unindented, not a YAML `#` comment
        # or a list item, and carrying a colon. Nested keys are indented.
        if (not line or line[0].isspace() or stripped.startswith("#")
                or stripped.startswith("-")):
            continue
        if ":" not in line:
            continue
        key = line.split(":", 1)[0].rstrip()
        if not key:
            continue
        seen[key] = seen.get(key, 0) + 1
    for key, count in seen.items():
        if count > 1:
            errors.append(
                f"{rel}: duplicate frontmatter key {key!r} "
                f"(PyYAML keeps the last value; strict parsers reject it)")
