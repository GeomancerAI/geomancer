"""Shared deterministic backend runtime paths."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GENERATED_SCRIPT_PATH = PROJECT_ROOT / "blender" / "generated_model.py"
PREVIEWS_DIR = PROJECT_ROOT / "data" / "previews"
