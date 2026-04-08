"""Lightweight local-first model library store for the desktop alpha shell."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_LIBRARY_PATH = PROJECT_ROOT / "data" / "model_library.json"

DEFAULT_TEMPLATE_ENTRIES = [
    {
        "id": "template-panel-plate",
        "name": "Panel Plate",
        "family": "panel_plate",
        "prompt": "Make a 120 x 80 x 4 mm panel plate with four 5 mm mounting holes",
    },
    {
        "id": "template-bracket",
        "name": "Mounting Bracket",
        "family": "bracket",
        "prompt": "Make a reinforced mounting bracket 120 x 30 x 80 mm with four 5 mm holes and 6 mm thickness",
    },
    {
        "id": "template-enclosure",
        "name": "Small Enclosure",
        "family": "enclosure",
        "prompt": "Create an enclosure 120 x 80 x 50 mm with 3 mm walls and a 60 x 25 mm front opening",
    },
]


def _default_library() -> dict:
    return {
        "saved_models": [],
        "projects": [],
        "templates": DEFAULT_TEMPLATE_ENTRIES,
    }


def load_model_library() -> dict:
    """Load the local model library store."""
    if not MODEL_LIBRARY_PATH.exists():
        return _default_library()

    try:
        raw_text = MODEL_LIBRARY_PATH.read_text(encoding="utf-8").strip()
        if not raw_text:
            return _default_library()
        loaded = json.loads(raw_text)
    except (json.JSONDecodeError, OSError):
        return _default_library()

    if not isinstance(loaded, dict):
        return _default_library()

    library = _default_library()
    for key in library:
        value = loaded.get(key, library[key])
        library[key] = value if isinstance(value, list) else library[key]
    return library


def save_model_library(library: dict) -> Path:
    """Persist the local model library store."""
    MODEL_LIBRARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged = _default_library()
    merged.update(library)
    MODEL_LIBRARY_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return MODEL_LIBRARY_PATH


def add_saved_model_entry(
    *,
    generation_id: str,
    user_request: str,
    family: str,
    family_label: str,
    plan: dict,
    validation: dict,
    script_path: str,
    preview_model_path: str,
    preview_export_status: str,
) -> dict:
    """Append a saved model entry after a successful generation."""
    library = load_model_library()
    timestamp = datetime.now().isoformat(timespec="seconds")
    entry = {
        "id": f"model-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6]}",
        "generation_id": generation_id,
        "created_at": timestamp,
        "prompt": user_request,
        "family": family,
        "family_label": family_label,
        "plan": plan,
        "validation_summary": validation.get("summary", ""),
        "script_path": script_path,
        "preview_model_path": preview_model_path,
        "preview_export_status": preview_export_status,
    }
    saved_models = library.get("saved_models", [])
    saved_models.insert(0, entry)
    library["saved_models"] = saved_models[:50]
    save_model_library(library)
    return entry


def get_library_summary() -> dict:
    """Return a compact summary for the desktop shell."""
    library = load_model_library()
    saved_models = library.get("saved_models", [])
    return {
        "saved_model_count": len(saved_models),
        "recent_saved_models": saved_models[:8],
        "project_count": len(library.get("projects", [])),
        "template_count": len(library.get("templates", [])),
        "templates": library.get("templates", []),
    }
