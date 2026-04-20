"""Main deterministic generation pipeline for Geomancer alpha families."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

try:
    from app.blender_runner import export_preview_model
    from app.code_utils import save_generated_script
    from app.model_library import add_saved_model_entry
    from app.path_utils import to_file_url
    from app.state import load_state, save_state
except ImportError:
    from blender_runner import export_preview_model
    from code_utils import save_generated_script
    from model_library import add_saved_model_entry
    from path_utils import to_file_url
    from state import load_state, save_state

from .classifier import classify_request
from .archetypes import build_phone_stand_generation_plan, select_archetype
from .families import FAMILY_DEFINITIONS
from .geometry import build_script
from .models import GenerationPlan
from .plan_bridge import bridge_canonical_plan_to_generation_plan, build_canonical_plan
from .normalizer import normalize_request
from .recipe_executor import execute_recipe
from .recipe_builder import build_deterministic_recipe
from .plan_validator import validate_canonical_plan
from .runtime import GENERATED_SCRIPT_PATH, PREVIEWS_DIR
from .validation import build_validation_report

RECIPE_ONLY_FAMILIES = {family.key for family in FAMILY_DEFINITIONS if family.key != "primitive_assembly"}


def generate_model_request(user_request: str, client=None, log=print, show_spinner: bool = True) -> dict:
    """Generate a deterministic alpha-family model request result."""
    del client
    del show_spinner
    generation_id = _build_generation_id()
    _reset_generation_context(user_request=user_request, generation_id=generation_id)
    try:
        archetype = select_archetype(user_request)
        if archetype and archetype.archetype_key == "phone_stand":
            classification = {
                "status": "ready",
                "family_key": "phone_stand",
                "family_summary": archetype.summary,
                "matched_alias": archetype.matched_alias,
                "confidence": archetype.confidence,
                "message": "",
                "archetype_key": archetype.archetype_key,
                "archetype_summary": archetype.summary,
            }
            log(f"Archetype result: {archetype.archetype_key}")
            log(f"Selected archetype: {archetype.matched_alias}")
            plan = build_phone_stand_generation_plan(user_request, archetype)
        else:
            classification_result = classify_request(user_request)
            log(f"Classification result: {classification_result.status}")
            if classification_result.family_key:
                log(f"Selected family: {classification_result.family_key}")
            if classification_result.status != "ready":
                if classification_result.message:
                    log(classification_result.message)
                return _build_nonready_result(
                    generation_id=generation_id,
                    user_request=user_request,
                    raw_status=classification_result.status,
                    message=classification_result.message,
                    classification=classification_result.to_dict(),
                )

            raw_status, message, plan = normalize_request(user_request, classification_result)
            if raw_status != "ready" or plan is None:
                if message:
                    log(message)
                return _build_nonready_result(
                    generation_id=generation_id,
                    user_request=user_request,
                    raw_status=raw_status,
                    message=message,
                    classification=classification_result.to_dict(),
                )
            classification = classification_result.to_dict()

        canonical_plan = build_canonical_plan(plan)
        canonical_validation = validate_canonical_plan(canonical_plan)
        log("Canonical plan:")
        log(str(canonical_validation.normalized_plan.to_dict()))
        log(canonical_validation.summary)
        if not canonical_validation.is_valid:
            validation_message = canonical_validation.summary
            if canonical_validation.clarification_needed:
                validation_message = f"{validation_message} {' '.join(canonical_validation.clarification_needed)}"
            if canonical_validation.errors:
                validation_message = f"{validation_message} {' '.join(canonical_validation.errors)}"
            return _build_nonready_result(
                generation_id=generation_id,
                user_request=user_request,
                raw_status=canonical_validation.status,
                message=validation_message,
                classification=classification,
            )

        plan = bridge_canonical_plan_to_generation_plan(canonical_validation.normalized_plan, source_plan=plan)
        _merge_plan_feedback(plan, canonical_validation.warnings, canonical_validation.normalized_plan.notes)
        recipe_build = build_deterministic_recipe(canonical_validation.normalized_plan)
        log("Deterministic recipe:")
        log(str(recipe_build.normalized_recipe.to_dict()))
        log(recipe_build.summary)
        if not recipe_build.is_valid:
            validation_message = recipe_build.summary
            if recipe_build.errors:
                validation_message = f"{validation_message} {' '.join(recipe_build.errors)}"
            return _build_nonready_result(
                generation_id=generation_id,
                user_request=user_request,
                raw_status=recipe_build.status,
                message=validation_message,
                classification=classification,
            )

        recipe = recipe_build.normalized_recipe
        recipe.generation_id = generation_id
        _merge_plan_feedback(plan, recipe_build.warnings, recipe.notes)
        recipe_execution = execute_recipe(recipe)
        log("Recipe execution:")
        log(str(recipe_execution.to_dict()))
        implementation_id = recipe.implementation_id or _implementation_id_for_recipe(recipe)
        execution_recipe = recipe.execution_recipe or recipe.source_recipe
        generation_path = "recipe"
        generation_route = "recipe_success"
        generation_fallback_reason = ""
        if recipe_execution.fallback_required or not recipe_execution.executed:
            log(recipe_execution.summary)
            if recipe_execution.unsupported_reasons:
                log("Recipe execution fallback reasons:")
                for reason in recipe_execution.unsupported_reasons:
                    log(reason)
            if _legacy_fallback_allowed(plan.family):
                generation_path = "legacy"
                generation_fallback_reason = recipe_execution.fallback_reason or _infer_fallback_reason(recipe_execution)
                generation_route = f"legacy_fallback_{generation_fallback_reason}" if generation_fallback_reason else "legacy_fallback"
                script_text = build_script(plan)
            else:
                failure_message = (
                    f"Recipe execution failed for recipe-only family '{plan.family}'. "
                    "Legacy fallback is quarantined for migrated families."
                )
                return _build_nonready_result(
                    generation_id=generation_id,
                    user_request=user_request,
                    raw_status="error",
                    message=failure_message,
                    classification=classification,
                )
        else:
            plan.recipe = recipe.execution_recipe or plan.recipe
            script_text = recipe_execution.script_text

        if recipe_execution.fallback_required or not recipe_execution.executed:
            execution_path = "legacy"
        else:
            execution_path = recipe_execution.execution_path

        validation = build_validation_report(plan)
        log("Normalized plan:")
        log(str(plan.to_dict()))
        log(validation.summary)

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
        _log_generation_truth_block(
            log,
            family=plan.family,
            generation_id=generation_id,
            generation_path=generation_path,
            generation_route=generation_route,
            execution_recipe=execution_recipe,
            implementation_id=implementation_id,
            script_path=str(GENERATED_SCRIPT_PATH),
            preview_path=preview_model_path or str(preview_path),
        )

        saved_model_entry = add_saved_model_entry(
            generation_id=generation_id,
            user_request=user_request,
            family=plan.family,
            family_label=plan.family_label,
            plan=plan.to_dict(),
            validation=validation.to_dict(),
            recipe=recipe.to_dict(),
            recipe_summary=recipe_build.summary,
            execution_path=execution_path,
            execution_summary=recipe_execution.summary,
            generation_path=generation_path,
            generation_route=generation_route,
            generation_fallback_reason=generation_fallback_reason,
            implementation_id=implementation_id,
            execution_recipe=execution_recipe,
            final_model_path=preview_model_path,
            final_model_url=to_file_url(preview_model_path),
            final_output_source=execution_path,
            script_path=str(GENERATED_SCRIPT_PATH),
            preview_model_path=preview_model_path,
            preview_model_url=to_file_url(preview_model_path),
            preview_export_status=preview_export_status,
        )

        _save_state(
            generation_id=generation_id,
            user_request=user_request,
            plan=plan,
            validation=validation.to_dict(),
            recipe=recipe.to_dict(),
            recipe_summary=recipe_build.summary,
            execution_path=execution_path,
            execution_summary=recipe_execution.summary,
            generation_path=generation_path,
            generation_route=generation_route,
            generation_fallback_reason=generation_fallback_reason,
            implementation_id=implementation_id,
            execution_recipe=execution_recipe,
            classification=classification,
            preview_model_path=preview_model_path,
            preview_asset_version=generation_id if preview_success else "",
            preview_export_status=preview_export_status,
            preview_export_message=preview_message,
            saved_model_entry=saved_model_entry,
            status="ready",
            generation_message=preview_message if not preview_success else "",
            raw_status="ready",
            final_model_path=preview_model_path,
            output_source=execution_path,
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
            "recipe": recipe.to_dict(),
            "recipe_summary": recipe_build.summary,
            "execution_path": execution_path,
            "execution_summary": recipe_execution.summary,
            "generation_path": generation_path,
            "generation_route": generation_route,
            "generation_fallback_reason": generation_fallback_reason,
            "implementation_id": implementation_id,
            "execution_recipe": execution_recipe,
            "classification": classification,
            "script_path": str(GENERATED_SCRIPT_PATH),
            "preview_model_path": preview_model_path,
            "preview_model_url": to_file_url(preview_model_path),
            "preview_asset_version": generation_id if preview_success else "",
            "preview_export_status": preview_export_status,
            "preview_export_message": preview_message,
            "final_model_path": preview_model_path,
            "final_model_url": to_file_url(preview_model_path),
            "output_source": execution_path,
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
    recipe: dict,
    recipe_summary: str,
    execution_path: str,
    execution_summary: str,
    generation_path: str,
    generation_route: str,
    generation_fallback_reason: str,
    implementation_id: str,
    execution_recipe: str,
    classification: dict,
    preview_model_path: str,
    preview_asset_version: str,
    preview_export_status: str,
    preview_export_message: str,
    saved_model_entry: dict,
    status: str,
    generation_message: str,
    raw_status: str,
    final_model_path: str = "",
    output_source: str = "",
) -> None:
    state = load_state()
    state["last_user_request"] = user_request
    state["last_generation_id"] = generation_id
    state["last_generated_script_path"] = str(GENERATED_SCRIPT_PATH)
    state["last_preview_model_path"] = preview_model_path
    state["last_preview_model_url"] = to_file_url(preview_model_path)
    state["last_preview_asset_version"] = preview_asset_version
    state["last_preview_export_status"] = preview_export_status
    state["last_preview_export_message"] = preview_export_message
    state["last_final_model_path"] = final_model_path
    state["last_final_model_url"] = to_file_url(final_model_path)
    state["last_output_source"] = output_source
    state["last_generation_timestamp"] = datetime.now().isoformat(timespec="seconds")
    state["last_generation_status"] = status
    state["last_generation_message"] = generation_message
    state["last_generation_raw_status"] = raw_status
    state["last_run_status"] = status
    state["last_generation_family"] = plan.family
    state["last_validation_summary"] = validation.get("summary", "")
    state["last_plan"] = plan.to_dict()
    state["last_recipe"] = recipe
    state["last_recipe_summary"] = recipe_summary
    state["last_execution_path"] = execution_path
    state["last_execution_summary"] = execution_summary
    state["last_generation_path"] = generation_path
    state["last_generation_route"] = generation_route
    state["last_generation_fallback_reason"] = generation_fallback_reason
    state["last_implementation_id"] = implementation_id
    state["last_execution_recipe"] = execution_recipe
    state["last_validation"] = validation
    state["last_classification"] = classification
    state["last_saved_model_entry"] = saved_model_entry
    save_state(state)


def _save_nonready_state(generation_id: str, user_request: str, status: str, raw_status: str, message: str, classification: dict) -> None:
    state = load_state()
    state["last_user_request"] = user_request
    state["last_generation_id"] = generation_id
    state["last_preview_model_path"] = ""
    state["last_preview_model_url"] = ""
    state["last_preview_asset_version"] = ""
    state["last_preview_export_status"] = "not_requested"
    state["last_preview_export_message"] = message
    state["last_final_model_path"] = ""
    state["last_final_model_url"] = ""
    state["last_output_source"] = ""
    state["last_generation_timestamp"] = datetime.now().isoformat(timespec="seconds")
    state["last_generation_status"] = status
    state["last_generation_message"] = message
    state["last_generation_raw_status"] = raw_status
    state["last_run_status"] = status or "error"
    state["last_generation_family"] = classification.get("family_key", "") or ""
    state["last_classification"] = classification
    state["last_validation_summary"] = message
    state["last_plan"] = {}
    state["last_recipe"] = {}
    state["last_recipe_summary"] = ""
    state["last_execution_path"] = ""
    state["last_execution_summary"] = ""
    state["last_generation_path"] = ""
    state["last_generation_route"] = ""
    state["last_generation_fallback_reason"] = ""
    state["last_implementation_id"] = ""
    state["last_execution_recipe"] = ""
    state["last_validation"] = {}
    state["last_saved_model_entry"] = {}
    save_state(state)


def _reset_generation_context(*, user_request: str, generation_id: str) -> None:
    """Clear generation-specific state before starting a new request."""
    state = load_state()
    state["last_user_request"] = user_request
    state["last_generation_id"] = generation_id
    state["last_generation_family"] = ""
    state["last_validation_summary"] = ""
    state["last_plan"] = {}
    state["last_recipe"] = {}
    state["last_recipe_summary"] = ""
    state["last_execution_path"] = ""
    state["last_execution_summary"] = ""
    state["last_generation_path"] = ""
    state["last_generation_route"] = ""
    state["last_generation_fallback_reason"] = ""
    state["last_implementation_id"] = ""
    state["last_execution_recipe"] = ""
    state["last_validation"] = {}
    state["last_classification"] = {}
    state["last_saved_model_entry"] = {}
    state["last_output_source"] = ""
    save_state(state)


def _merge_plan_feedback(plan: GenerationPlan, warnings: list[str], notes: list[str]) -> None:
    for warning in warnings:
        if warning and warning not in plan.warnings:
            plan.warnings.append(warning)
    for note in notes:
        if note and note not in plan.assumptions:
            plan.assumptions.append(note)


def _supported_family_labels() -> list[str]:
    return [family.label for family in FAMILY_DEFINITIONS]


def _legacy_fallback_allowed(family: str) -> bool:
    return family not in RECIPE_ONLY_FAMILIES


def _infer_fallback_reason(recipe_execution) -> str:
    if recipe_execution.unsupported_ops:
        return "unsupported_recipe_op"
    if recipe_execution.unsupported_reasons:
        return "unsupported_recipe_execution"
    return "execution_failure"


def _implementation_id_for_recipe(recipe) -> str:
    mapping = {
        "enclosure": "enclosure_open_top_shell_v1",
        "tray": "tray_box_shell_v1",
        "bracket": "bracket_body_v1",
        "clip": "cable_clip_v1",
        "planter": "planter_vessel_v1",
        "gear": "gear_body_v1",
        "adapter": "adapter_transition_v1",
        "plate": "panel_plate_v1",
        "standoff": "spacer_standoff_v1",
        "hook_mount": "hook_mount_wall_hook_v1",
        "phone_stand": "phone_stand_cradle_v1",
        "assembly": "primitive_assembly_v1",
    }
    return mapping.get(recipe.object_type) or f"{recipe.source_recipe or recipe.object_type or 'geometry'}_v1"


def _log_generation_truth_block(
    log,
    *,
    family: str,
    generation_id: str,
    generation_path: str,
    generation_route: str,
    execution_recipe: str,
    implementation_id: str,
    script_path: str,
    preview_path: str,
) -> None:
    log("Generation truth:")
    log(f"  family={family}")
    log(f"  generation_id={generation_id}")
    log(f"  generation_path={generation_path}")
    log(f"  generation_route={generation_route}")
    log(f"  execution_recipe={execution_recipe}")
    log(f"  implementation_id={implementation_id}")
    log(f"  script_path={script_path}")
    log(f"  preview_path={preview_path}")


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
        "preview_model_url": "",
        "preview_asset_version": "",
        "preview_export_status": "not_requested",
        "preview_export_message": message,
        "final_model_path": "",
        "final_model_url": "",
        "output_source": "",
        "generation_path": "",
        "generation_route": "",
        "generation_fallback_reason": "",
        "implementation_id": "",
        "execution_recipe": "",
        "supported_families": _supported_family_labels(),
    }


def _normalize_terminal_status(raw_status: str) -> str:
    if raw_status == "ready":
        return "ready"
    if raw_status == "unsupported":
        return "unsupported"
    if raw_status in {"clarify", "validation_failed", "invalid"}:
        return "validation_failed"
    return "error"
