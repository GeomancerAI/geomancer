"""Main deterministic generation pipeline for Geomancer alpha families."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

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
from .runtime import GENERATED_SCRIPT_PATH, PREVIEWS_DIR
from .validation import build_validation_report


def generate_model_request(user_request: str, client=None, log=print, show_spinner: bool = True) -> dict:
    """Generate a deterministic alpha-family model request result."""
    del client
    del show_spinner
    generation_id = _build_generation_id()
    try:
        classification = classify_request(user_request)
        log(f"Classification result: {classification.status}")
        if classification.family_key:
            log(f"Selected family: {classification.family_key}")
        if classification.status != "ready":
            if classification.message:
                log(classification.message)
            return _build_nonready_result(
                generation_id=generation_id,
                user_request=user_request,
                raw_status=classification.status,
                message=classification.message,
                classification=classification.to_dict(),
            )

        raw_status, message, plan = normalize_request(user_request, classification)
        if raw_status != "ready" or plan is None:
            if message:
                log(message)
            return _build_nonready_result(
                generation_id=generation_id,
                user_request=user_request,
                raw_status=raw_status,
                message=message,
                classification=classification.to_dict(),
            )

        validation = build_validation_report(plan)
        log("Normalized plan:")
        log(str(plan.to_dict()))
        log(validation.summary)

        script_text = build_script(plan)
        save_generated_script(script_text, GENERATED_SCRIPT_PATH)
        preview_path = _generation_preview_path(generation_id)

        log("Exporting preview model for desktop viewer...")
        preview_success, preview_message = export_preview_model(
            GENERATED_SCRIPT_PATH,
            preview_path,
            export_format="GLB",
        )
        log(preview_message)
        preview_model_path = str(preview_path) if preview_success else ""
        preview_export_status = "ready" if preview_success else "error"

        saved_model_entry = add_saved_model_entry(
            generation_id=generation_id,
            user_request=user_request,
            family=plan.family,
            family_label=plan.family_label,
            plan=plan.to_dict(),
            validation=validation.to_dict(),
            script_path=str(GENERATED_SCRIPT_PATH),
            preview_model_path=preview_model_path,
            preview_export_status=preview_export_status,
        )

        _save_state(
            generation_id=generation_id,
            user_request=user_request,
            plan=plan,
            validation=validation.to_dict(),
            classification=classification.to_dict(),
            preview_model_path=preview_model_path,
            preview_asset_version=generation_id if preview_success else "",
            preview_export_status=preview_export_status,
            preview_export_message=preview_message,
            saved_model_entry=saved_model_entry,
            status="ready",
            generation_message=preview_message if not preview_success else "",
            raw_status="ready",
        )

        return {
            "generation_id": generation_id,
            "request_text": user_request,
            "status": "ready",
            "raw_status": "ready",
            "is_terminal": True,
            "family": plan.family,
            "family_label": plan.family_label,
            "plan": plan.to_dict(),
            "validation": validation.to_dict(),
            "classification": classification.to_dict(),
            "script_path": str(GENERATED_SCRIPT_PATH),
            "preview_model_path": preview_model_path,
            "preview_asset_version": generation_id if preview_success else "",
            "preview_export_status": preview_export_status,
            "preview_export_message": preview_message,
            "saved_model_entry": saved_model_entry,
            "supported_families": _supported_family_labels(),
        }
    except Exception as error:
        error_message = str(error) or "Generation failed unexpectedly."
        log(error_message)
        return _build_nonready_result(
            generation_id=generation_id,
            user_request=user_request,
            raw_status="error",
            message=error_message,
            classification={},
        )


def _save_state(
    generation_id: str,
    user_request: str,
    plan: GenerationPlan,
    validation: dict,
    classification: dict,
    preview_model_path: str,
    preview_asset_version: str,
    preview_export_status: str,
    preview_export_message: str,
    saved_model_entry: dict,
    status: str,
    generation_message: str,
    raw_status: str,
) -> None:
    state = load_state()
    state["last_user_request"] = user_request
    state["last_generation_id"] = generation_id
    state["last_generated_script_path"] = str(GENERATED_SCRIPT_PATH)
    state["last_preview_model_path"] = preview_model_path
    state["last_preview_asset_version"] = preview_asset_version
    state["last_preview_export_status"] = preview_export_status
    state["last_preview_export_message"] = preview_export_message
    state["last_generation_timestamp"] = datetime.now().isoformat(timespec="seconds")
    state["last_generation_status"] = status
    state["last_generation_message"] = generation_message
    state["last_generation_raw_status"] = raw_status
    state["last_run_status"] = status
    state["last_generation_family"] = plan.family
    state["last_validation_summary"] = validation.get("summary", "")
    state["last_plan"] = plan.to_dict()
    state["last_validation"] = validation
    state["last_classification"] = classification
    state["last_saved_model_entry"] = saved_model_entry
    save_state(state)


def _save_nonready_state(generation_id: str, user_request: str, status: str, raw_status: str, message: str, classification: dict) -> None:
    state = load_state()
    state["last_user_request"] = user_request
    state["last_generation_id"] = generation_id
    state["last_preview_model_path"] = ""
    state["last_preview_asset_version"] = ""
    state["last_preview_export_status"] = "not_requested"
    state["last_preview_export_message"] = message
    state["last_generation_timestamp"] = datetime.now().isoformat(timespec="seconds")
    state["last_generation_status"] = status
    state["last_generation_message"] = message
    state["last_generation_raw_status"] = raw_status
    state["last_run_status"] = status or "error"
    state["last_generation_family"] = classification.get("family_key", "") or ""
    state["last_classification"] = classification
    state["last_validation_summary"] = message
    state["last_plan"] = {}
    state["last_validation"] = {}
    state["last_saved_model_entry"] = {}
    save_state(state)


def _supported_family_labels() -> list[str]:
    return [family.label for family in FAMILY_DEFINITIONS]


def _build_generation_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"gen-{timestamp}-{uuid4().hex[:8]}"


def _generation_preview_path(generation_id: str) -> Path:
    return PREVIEWS_DIR / f"generated_preview_{generation_id}.glb"


def _build_nonready_result(
    *,
    generation_id: str,
    user_request: str,
    raw_status: str,
    message: str,
    classification: dict,
) -> dict:
    status = _normalize_terminal_status(raw_status)
    _save_nonready_state(
        generation_id=generation_id,
        user_request=user_request,
        status=status,
        raw_status=raw_status,
        message=message,
        classification=classification,
    )
    return {
        "generation_id": generation_id,
        "request_text": user_request,
        "status": status,
        "raw_status": raw_status,
        "is_terminal": True,
        "message": message,
        "classification": classification,
        "preview_model_path": "",
        "preview_asset_version": "",
        "preview_export_status": "not_requested",
        "preview_export_message": message,
        "supported_families": _supported_family_labels(),
    }


def _normalize_terminal_status(raw_status: str) -> str:
    if raw_status == "ready":
        return "ready"
    if raw_status == "unsupported":
        return "unsupported"
    if raw_status in {"clarify", "validation_failed"}:
        return "validation_failed"
    return "error"
