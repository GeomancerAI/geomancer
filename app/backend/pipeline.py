"""Main deterministic generation pipeline for Geomancer alpha families."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

try:
    from app.blender_runner import export_preview_model
    from app.code_utils import save_generated_script
    from app.model_library import add_saved_model_entry
    from app.state import load_state, save_state
except ImportError:
    from blender_runner import export_preview_model
    from code_utils import save_generated_script
    from model_library import add_saved_model_entry
    from state import load_state, save_state

from .classifier import classify_request
from .families import FAMILY_DEFINITIONS
from .geometry import build_script
from .models import GenerationPlan
from .normalizer import normalize_request
from .validation import build_validation_report


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GENERATED_SCRIPT_PATH = PROJECT_ROOT / "blender" / "generated_model.py"
GENERATED_PREVIEW_PATH = PROJECT_ROOT / "data" / "previews" / "generated_preview.glb"


def generate_model_request(user_request: str, client=None, log=print, show_spinner: bool = True) -> dict:
    """Generate a deterministic alpha-family model request result."""
    del client
    del show_spinner

    classification = classify_request(user_request)
    log(f"Classification result: {classification.status}")
    if classification.family_key:
        log(f"Selected family: {classification.family_key}")
    if classification.status != "ready":
        if classification.message:
            log(classification.message)
        _save_nonready_state(
            user_request=user_request,
            status=classification.status,
            message=classification.message,
            classification=classification.to_dict(),
        )
        return {
            "status": classification.status,
            "message": classification.message,
            "classification": classification.to_dict(),
            "supported_families": _supported_family_labels(),
        }

    status, message, plan = normalize_request(user_request, classification)
    if status != "ready" or plan is None:
        if message:
            log(message)
        _save_nonready_state(
            user_request=user_request,
            status=status,
            message=message,
            classification=classification.to_dict(),
        )
        return {
            "status": status,
            "message": message,
            "classification": classification.to_dict(),
            "supported_families": _supported_family_labels(),
        }

    validation = build_validation_report(plan)
    log("Normalized plan:")
    log(str(plan.to_dict()))
    log(validation.summary)

    script_text = build_script(plan)
    save_generated_script(script_text, GENERATED_SCRIPT_PATH)

    log("Exporting preview model for desktop viewer...")
    preview_success, preview_message = export_preview_model(
        GENERATED_SCRIPT_PATH,
        GENERATED_PREVIEW_PATH,
        export_format="GLB",
    )
    log(preview_message)
    preview_model_path = str(GENERATED_PREVIEW_PATH) if preview_success else ""

    saved_model_entry = add_saved_model_entry(
        user_request=user_request,
        family=plan.family,
        family_label=plan.family_label,
        plan=plan.to_dict(),
        validation=validation.to_dict(),
        script_path=str(GENERATED_SCRIPT_PATH),
        preview_model_path=preview_model_path,
        preview_export_status="ready" if preview_success else "unavailable",
    )

    _save_state(
        user_request=user_request,
        plan=plan,
        validation=validation.to_dict(),
        classification=classification.to_dict(),
        preview_model_path=preview_model_path,
        preview_export_status="ready" if preview_success else "unavailable",
        preview_export_message=preview_message,
        saved_model_entry=saved_model_entry,
    )

    return {
        "status": "ready",
        "family": plan.family,
        "family_label": plan.family_label,
        "plan": plan.to_dict(),
        "validation": validation.to_dict(),
        "classification": classification.to_dict(),
        "script_path": str(GENERATED_SCRIPT_PATH),
        "preview_model_path": preview_model_path,
        "preview_export_status": "ready" if preview_success else "unavailable",
        "preview_export_message": preview_message,
        "saved_model_entry": saved_model_entry,
        "supported_families": _supported_family_labels(),
    }


def _save_state(
    user_request: str,
    plan: GenerationPlan,
    validation: dict,
    classification: dict,
    preview_model_path: str,
    preview_export_status: str,
    preview_export_message: str,
    saved_model_entry: dict,
) -> None:
    state = load_state()
    state["last_user_request"] = user_request
    state["last_generated_script_path"] = str(GENERATED_SCRIPT_PATH)
    state["last_preview_model_path"] = preview_model_path
    state["last_preview_export_status"] = preview_export_status
    state["last_preview_export_message"] = preview_export_message
    state["last_generation_timestamp"] = datetime.now().isoformat(timespec="seconds")
    state["last_generation_status"] = "ready"
    state["last_generation_message"] = ""
    state["last_run_status"] = "not run yet"
    state["last_generation_family"] = plan.family
    state["last_validation_summary"] = validation.get("summary", "")
    state["last_plan"] = plan.to_dict()
    state["last_validation"] = validation
    state["last_classification"] = classification
    state["last_saved_model_entry"] = saved_model_entry
    save_state(state)


def _save_nonready_state(user_request: str, status: str, message: str, classification: dict) -> None:
    state = load_state()
    state["last_user_request"] = user_request
    state["last_preview_model_path"] = ""
    state["last_preview_export_status"] = "unavailable"
    state["last_preview_export_message"] = message
    state["last_generation_timestamp"] = datetime.now().isoformat(timespec="seconds")
    state["last_generation_status"] = status
    state["last_generation_message"] = message
    state["last_generation_family"] = classification.get("family_key", "") or ""
    state["last_classification"] = classification
    state["last_validation_summary"] = message
    state["last_plan"] = {}
    state["last_validation"] = {}
    state["last_saved_model_entry"] = {}
    save_state(state)


def _supported_family_labels() -> list[str]:
    return [family.label for family in FAMILY_DEFINITIONS]
