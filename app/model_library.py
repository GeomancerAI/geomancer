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


def _saved_model_has_editable_context(plan: dict, editable_params: list[dict] | None = None) -> bool:
    if editable_params:
        return True
    if not isinstance(plan, dict) or not plan:
        return False
    if plan.get("intent") or plan.get("construction_mode"):
        return True
    if plan.get("dimensions") or plan.get("components") or plan.get("composition") or plan.get("hybrid_details"):
        return True
    return False


def add_saved_model_entry(
    *,
    generation_id: str,
    user_request: str,
    family: str,
    family_label: str,
    plan: dict,
    validation: dict,
    recipe: dict | None = None,
    recipe_summary: str = "",
    execution_path: str = "",
    execution_summary: str = "",
    generation_path: str = "",
    generation_route: str = "",
    generation_fallback_reason: str = "",
    implementation_id: str = "",
    execution_recipe: str = "",
    final_model_path: str = "",
    final_model_url: str = "",
    final_output_source: str = "",
    editable_params: list[dict] | None = None,
    interpretation_summary: str = "",
    decision_summary: str = "",
    style_summary: str = "",
    current_saved_model_id: str = "",
    current_saved_model_editable: bool = False,
    last_opened_model_id: str = "",
    edited_plan_summary: str = "",
    reopened_plan_summary: str = "",
    regeneration_source: str = "",
    source_generation_id: str = "",
    stl_export_path: str = "",
    stl_export_status: str = "",
    stl_export_message: str = "",
    stl_source_model_path: str = "",
    script_path: str,
    preview_model_path: str,
    preview_model_url: str = "",
    preview_export_status: str,
) -> dict:
    """Append a saved model entry after a successful generation."""
    library = load_model_library()
    timestamp = datetime.now().isoformat(timespec="seconds")
    editable_plan_available = _saved_model_has_editable_context(plan, editable_params)
    entry = {
        "id": f"model-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6]}",
        "generation_id": generation_id,
        "created_at": timestamp,
        "prompt": user_request,
        "family": family,
        "family_label": family_label,
        "plan": plan,
        "validation": validation,
        "validation_summary": validation.get("summary", ""),
        "recipe": recipe or {},
        "recipe_summary": recipe_summary,
        "execution_path": execution_path,
        "execution_summary": execution_summary,
        "generation_path": generation_path or execution_path,
        "generation_route": generation_route,
        "generation_fallback_reason": generation_fallback_reason,
        "implementation_id": implementation_id,
        "execution_recipe": execution_recipe,
        "interpretation_summary": interpretation_summary,
        "decision_summary": decision_summary,
        "style_summary": style_summary,
        "final_model_path": final_model_path or preview_model_path,
        "final_model_url": final_model_url or preview_model_url,
        "final_output_source": final_output_source or execution_path,
        "editable_params": list(editable_params or []),
        "editable_plan_available": editable_plan_available,
        "is_editable": editable_plan_available,
        "current_saved_model_id": current_saved_model_id,
        "current_saved_model_editable": bool(current_saved_model_editable),
        "last_opened_model_id": last_opened_model_id,
        "edited_plan_summary": edited_plan_summary,
        "reopened_plan_summary": reopened_plan_summary,
        "regeneration_source": regeneration_source,
        "source_generation_id": source_generation_id,
        "stl_export_path": stl_export_path,
        "stl_export_status": stl_export_status,
        "stl_export_message": stl_export_message,
        "stl_source_model_path": stl_source_model_path,
        "script_path": script_path,
        "preview_model_path": preview_model_path,
        "preview_model_url": preview_model_url,
        "preview_export_status": preview_export_status,
    }
    saved_models = library.get("saved_models", [])
    saved_models.insert(0, entry)
    library["saved_models"] = saved_models[:50]
    save_model_library(library)
    return entry


def update_saved_model_entry(model_id: str, updates: dict) -> dict | None:
    """Update one saved model entry and persist the library."""
    if not model_id:
        return None

    library = load_model_library()
    saved_models = library.get("saved_models", [])
    updated_entry = None
    for entry in saved_models:
        if entry.get("id") == model_id:
            entry.update(updates)
            updated_entry = entry
            break

    if updated_entry is None:
        return None

    save_model_library(library)
    return updated_entry


def get_library_summary() -> dict:
    """Return a compact summary for the desktop shell."""
    library = load_model_library()
    saved_models = [_annotate_saved_model_entry(entry) for entry in library.get("saved_models", [])]
    return {
        "saved_model_count": len(saved_models),
        "recent_saved_models": saved_models[:8],
        "project_count": len(library.get("projects", [])),
        "template_count": len(library.get("templates", [])),
        "templates": library.get("templates", []),
    }


def list_saved_models(limit: int | None = None) -> list[dict]:
    """Return saved model entries in persisted order."""
    library = load_model_library()
    saved_models = [_annotate_saved_model_entry(entry) for entry in library.get("saved_models", [])]
    if limit is None:
        return list(saved_models)
    return list(saved_models[: max(limit, 0)])


def delete_saved_model_entry(model_id: str) -> bool:
    """Delete one saved model entry by id."""
    if not model_id:
        return False

    library = load_model_library()
    saved_models = library.get("saved_models", [])
    filtered_models = [entry for entry in saved_models if entry.get("id") != model_id]
    if len(filtered_models) == len(saved_models):
        return False

    library["saved_models"] = filtered_models
    save_model_library(library)
    return True


def _annotate_saved_model_entry(entry: dict) -> dict:
    annotated = dict(entry or {})
    plan = annotated.get("plan") if isinstance(annotated.get("plan"), dict) else {}
    editable_params = annotated.get("editable_params") if isinstance(annotated.get("editable_params"), list) else []
    editable_plan_available = _saved_model_has_editable_context(plan, editable_params)
    if "editable_plan_available" not in annotated:
        annotated["editable_plan_available"] = editable_plan_available
    if "is_editable" not in annotated:
        annotated["is_editable"] = bool(editable_plan_available)
    if "current_saved_model_editable" not in annotated:
        annotated["current_saved_model_editable"] = bool(annotated["is_editable"])
    return annotated
