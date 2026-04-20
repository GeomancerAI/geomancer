"""Path helpers shared across backend and desktop bridge code."""

from __future__ import annotations

from urllib.parse import quote


def to_file_url(path_text: str | None) -> str:
    """Convert a local filesystem path into a browser-safe file URL.

    Returns an empty string for unsupported or missing paths.
    """
    if not path_text:
        return ""

    normalized = str(path_text).replace("\\", "/").strip()
    if not normalized:
        return ""

    if "://" in normalized:
        return normalized

    if len(normalized) >= 3 and normalized[1] == ":" and normalized[2] == "/":
        return f"file:///{quote(normalized, safe='/:')}"

    if normalized.startswith("//"):
        return f"file:{quote(normalized, safe='/:')}"

    return ""
