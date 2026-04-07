"""Version helpers for Geomancer backend passes."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VERSION_PATH = PROJECT_ROOT / "VERSION"


def load_version() -> str:
    """Load the current project version from the root VERSION file."""
    if not VERSION_PATH.exists():
        return "0.0.0-dev"
    version_text = VERSION_PATH.read_text(encoding="utf-8").strip()
    return version_text or "0.0.0-dev"
