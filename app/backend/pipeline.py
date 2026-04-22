"""Plan-first backend pipeline for Geomancer."""

from __future__ import annotations

import re
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

from .plan_schema import (
    GeomancerComponent,
    GeomancerCompositionItem,
    GeomancerHybridDetail,
    GeomancerIntent,
    GeomancerPlan,
    GeomancerStyle,
    ALLOWED_STYLE_PROFILES,
    STYLE_COMPATIBILITY_BY_OBJECT_TYPE,
    STYLE_DEFAULTS_BY_PROFILE,
    STYLE_DEFAULT_BY_OBJECT_TYPE,
)
from .plan_validator import validate_plan
from .recipe_builder import build_deterministic_recipe
from .recipe_executor import execute_recipe
from .runtime import GENERATED_SCRIPT_PATH, PREVIEWS_DIR


SUPPORTED_FAMILY_LABELS = [
    "Phone Stand",
    "Bracket",
    "Tray",
    "Enclosure",
    "Plate",
    "Standoff",
    "Hook Mount",
    "Adapter",
    "Primitive Assembly",
    "Crate",
    "Barrel",
    "Canister",
    "Pedestal",
]
COMPOSITIONAL_OBJECT_TYPES = {
    "primitive_assembly",
    "crate",
    "barrel",
    "canister",
    "pedestal",
}
FUNCTIONAL_OBJECT_TYPES = {
    "phone_stand",
    "bracket",
    "tray",
    "enclosure",
    "plate",
    "standoff",
    "hook_mount",
    "adapter",
}
HYBRID_ACCENT_TYPES = {"cube", "cylinder", "sphere"}
HYBRID_FEATURE_TYPES = {"hole_pattern", "mount_hole", "through_hole", "slot", "tab", "opening"}
NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
}


def generate_model_request(user_request: str, client=None, log=print, show_spinner: bool = True) -> dict:
    """Run the authoritative plan -> validate -> recipe -> execute pipeline."""
    del client
    del show_spinner
    generation_id = _build_generation_id()
    _reset_generation_context(user_request=user_request, generation_id=generation_id)
    try:
        interpreted = interpret_prompt_to_plan(user_request, log=log)
        interpretation_summary = interpreted.get("interpretation_summary", "")
        decision_summary = interpreted.get("decision_summary", "")
        style_summary = interpreted.get("style_summary", "")
        missing_info = list(interpreted.get("missing_info") or [])
        assumptions = list(interpreted.get("assumptions") or [])
        warnings = list(interpreted.get("warnings") or [])
        if interpreted["status"] != "ready":
            editable_params = _extract_editable_params(_dict_to_plan(interpreted.get("plan", {}))) if interpreted.get("plan") else []
            return _build_nonready_result(
                generation_id=generation_id,
                user_request=user_request,
                raw_status=interpreted["status"],
                message=interpreted["message"],
                classification=interpreted.get("classification", {}),
                plan=_plan_to_dict(interpreted.get("plan", {})),
                validation=interpreted.get("validation", {}),
                recipe=interpreted.get("recipe", {}),
                recipe_summary=interpreted.get("recipe_summary", ""),
                interpretation_summary=interpretation_summary,
                decision_summary=decision_summary,
                style_summary=style_summary,
                missing_info=missing_info,
                assumptions=assumptions,
                warnings=warnings,
                editable_params=editable_params,
                current_editable_params=editable_params,
                last_editable_params=editable_params,
            )

        return _finalize_generation_from_plan(
            generation_id=generation_id,
            user_request=user_request,
            plan=interpreted["plan"],
            classification=interpreted["classification"],
            interpretation_summary=interpretation_summary,
            decision_summary="",
            style_summary="",
            regeneration_source="",
            edited_plan_summary="",
            log=log,
        )
    except Exception as error:
        return _build_nonready_result(
            generation_id=generation_id,
            user_request=user_request,
            raw_status="error",
            message=str(error) or "Generation failed unexpectedly.",
            classification={},
        )


def generate_model_from_plan(
    plan: dict | GeomancerPlan,
    client=None,
    log=print,
    show_spinner: bool = True,
    *,
    source_generation_id: str = "",
    source_request_text: str = "",
    source_plan: dict | GeomancerPlan | None = None,
    current_saved_model_id: str = "",
    current_saved_model_editable: bool = False,
    last_opened_model_id: str = "",
    reopen_source: str = "",
    reopened_plan_summary: str = "",
    edited_plan_summary: str = "",
    regeneration_source: str = "edited_plan",
) -> dict:
    """Regenerate deterministically from an edited plan."""
    del client
    del show_spinner
    generation_id = _build_generation_id()
    plan_payload = _dict_to_plan(plan)
    user_request = source_request_text or plan_payload.request_text
    _reset_generation_context(user_request=user_request, generation_id=generation_id)
    classification = _classification_from_plan(
        plan_payload,
        source_generation_id=source_generation_id,
        regeneration_source=regeneration_source,
    )
    if source_plan is not None and not edited_plan_summary:
        edited_plan_summary = _summarize_plan_edits(_dict_to_plan(source_plan), plan_payload)
    if not reopened_plan_summary and current_saved_model_id:
        reopened_plan_summary = f"Reopened saved model {current_saved_model_id} for editing."
    interpretation_summary = f"Regenerated from edited parameters for {plan_payload.intent.object_type or 'the current plan'}."
    return _finalize_generation_from_plan(
        generation_id=generation_id,
        user_request=user_request,
        plan=plan_payload,
        classification=classification,
        interpretation_summary=interpretation_summary,
        decision_summary="",
        style_summary=_build_style_summary(plan_payload, "ready"),
        regeneration_source=regeneration_source,
        edited_plan_summary=edited_plan_summary,
        current_saved_model_id=current_saved_model_id,
        current_saved_model_editable=current_saved_model_editable,
        last_opened_model_id=last_opened_model_id,
        reopen_source=reopen_source,
        reopened_plan_summary=reopened_plan_summary,
        source_generation_id=source_generation_id,
        log=log,
    )


def _finalize_generation_from_plan(
    *,
    generation_id: str,
    user_request: str,
    plan: GeomancerPlan,
    classification: dict,
    interpretation_summary: str,
    decision_summary: str,
    style_summary: str = "",
    regeneration_source: str = "",
    edited_plan_summary: str = "",
    current_saved_model_id: str = "",
    current_saved_model_editable: bool = False,
    last_opened_model_id: str = "",
    reopen_source: str = "",
    reopened_plan_summary: str = "",
    source_generation_id: str = "",
    log=print,
) -> dict:
    validation_result = validate_plan(plan)
    validation = validation_result.to_dict()
    validation_summary = validation_result.summary
    normalized_plan = validation_result.normalized_plan
    editable_params = _extract_editable_params(normalized_plan)
    current_editable_params = list(editable_params)
    missing_info = list(normalized_plan.missing_info)
    assumptions = list(normalized_plan.assumptions)
    warnings = list(normalized_plan.warnings)
    if source_generation_id and regeneration_source:
        regeneration_source = f"{regeneration_source}:{source_generation_id}"
    elif source_generation_id:
        regeneration_source = source_generation_id
    if not edited_plan_summary and regeneration_source:
        edited_plan_summary = f"Regenerated from {regeneration_source}."
    if not reopened_plan_summary and current_saved_model_id:
        reopened_plan_summary = f"Reopened saved model {current_saved_model_id}."
    if not decision_summary:
        decision_summary = validation_summary
    if not style_summary:
        style_summary = _build_style_summary(normalized_plan, validation_result.status)

    log("Validated plan:")
    log(str(validation["normalized_plan"]))
    log(validation_result.summary)
    if validation_result.status != "ready":
        message = validation_result.summary
        if validation_result.clarification_needed:
            message = f"{message} {' '.join(validation_result.clarification_needed)}"
        if validation_result.errors:
            message = f"{message} {' '.join(validation_result.errors)}"
        return _build_nonready_result(
            generation_id=generation_id,
            user_request=user_request,
            raw_status=validation_result.status,
            message=message,
            classification=classification,
            plan=validation_result.normalized_plan.to_dict(),
            validation=validation,
            interpretation_summary=interpretation_summary,
            decision_summary=decision_summary,
            style_summary=style_summary,
            missing_info=missing_info,
            assumptions=assumptions,
            warnings=warnings,
            editable_params=editable_params,
            current_editable_params=current_editable_params,
            last_editable_params=current_editable_params,
            last_regeneration_source=regeneration_source,
            edited_plan_summary=edited_plan_summary,
            current_saved_model_id=current_saved_model_id,
            current_saved_model_editable=current_saved_model_editable,
            last_opened_model_id=last_opened_model_id,
            reopen_source=reopen_source,
            reopened_plan_summary=reopened_plan_summary,
        )

    recipe_build = build_deterministic_recipe(normalized_plan)
    recipe = recipe_build.normalized_recipe
    recipe.generation_id = generation_id
    recipe_summary = recipe_build.summary
    style_summary = _build_style_summary(normalized_plan, "ready")
    log("Deterministic recipe:")
    log(str(recipe.to_dict()))
    log(recipe_summary)
    if recipe_build.status != "ready":
        message = recipe_build.summary
        if recipe_build.errors:
            message = f"{message} {' '.join(recipe_build.errors)}"
        return _build_nonready_result(
            generation_id=generation_id,
            user_request=user_request,
            raw_status=recipe_build.status,
            message=message,
            classification=classification,
            plan=normalized_plan.to_dict(),
            validation=validation,
            recipe=recipe.to_dict(),
            recipe_summary=recipe_summary,
            interpretation_summary=interpretation_summary,
            decision_summary=recipe_summary,
            style_summary=style_summary,
            missing_info=missing_info,
            assumptions=assumptions,
            warnings=warnings,
            editable_params=editable_params,
            current_editable_params=current_editable_params,
            last_editable_params=current_editable_params,
            last_regeneration_source=regeneration_source,
            edited_plan_summary=edited_plan_summary,
            current_saved_model_id=current_saved_model_id,
            current_saved_model_editable=current_saved_model_editable,
            last_opened_model_id=last_opened_model_id,
            reopen_source=reopen_source,
            reopened_plan_summary=reopened_plan_summary,
        )

    recipe_execution = execute_recipe(recipe)
    log("Recipe execution:")
    log(str(recipe_execution.to_dict()))
    if not recipe_execution.executed or recipe_execution.fallback_required:
        failure_message = recipe_execution.summary or "Recipe execution failed."
        return _build_nonready_result(
            generation_id=generation_id,
            user_request=user_request,
            raw_status="error",
            message=failure_message,
            classification=classification,
            plan=normalized_plan.to_dict(),
            validation=validation,
            recipe=recipe.to_dict(),
            recipe_summary=recipe_summary,
            interpretation_summary=interpretation_summary,
            decision_summary=recipe_execution.summary,
            style_summary=style_summary,
            missing_info=missing_info,
            assumptions=assumptions,
            warnings=warnings,
            editable_params=editable_params,
            current_editable_params=current_editable_params,
            last_editable_params=current_editable_params,
            last_regeneration_source=regeneration_source,
            edited_plan_summary=edited_plan_summary,
            current_saved_model_id=current_saved_model_id,
            current_saved_model_editable=current_saved_model_editable,
            last_opened_model_id=last_opened_model_id,
            reopen_source=reopen_source,
            reopened_plan_summary=reopened_plan_summary,
        )

    script_text = recipe_execution.script_text
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
    preview_model_url = to_file_url(preview_model_path)
    preview_export_status = "ready" if preview_success else "error"
    execution_recipe = recipe.execution_recipe
    implementation_id = recipe.implementation_id
    family = classification.get("family_key", "")
    family_label = _family_label_from_plan(normalized_plan)
    execution_path = recipe_execution.execution_path or "recipe"
    decision_summary = _build_decision_summary(
        "ready",
        object_type=normalized_plan.intent.object_type,
        construction_mode=normalized_plan.construction_mode,
        recipe_name=execution_recipe,
        implementation_id=implementation_id,
        validation_summary=validation_summary,
        recipe_summary=recipe_summary,
        execution_summary=recipe_execution.summary,
        preview_success=preview_success,
    )
    if edited_plan_summary:
        decision_summary = f"{edited_plan_summary} {decision_summary}"
    saved_model_entry = add_saved_model_entry(
        generation_id=generation_id,
        user_request=user_request,
        family=family,
        family_label=family_label,
        plan=normalized_plan.to_dict(),
        validation=validation,
        recipe=recipe.to_dict(),
        recipe_summary=recipe_summary,
        execution_path=execution_path,
        execution_summary=recipe_execution.summary,
        generation_path="recipe",
        generation_route="edited_plan_success" if regeneration_source else "recipe_success",
        generation_fallback_reason="",
        implementation_id=implementation_id,
        execution_recipe=execution_recipe,
        final_model_path=preview_model_path,
        final_model_url=preview_model_url,
        final_output_source=execution_path,
        stl_export_path="",
        stl_export_status="not_requested",
        stl_export_message="",
        stl_source_model_path=preview_model_path,
        script_path=str(GENERATED_SCRIPT_PATH),
        preview_model_path=preview_model_path,
        preview_model_url=preview_model_url,
        preview_export_status=preview_export_status,
        editable_params=editable_params,
        edited_plan_summary=edited_plan_summary,
        regeneration_source=regeneration_source,
        source_generation_id=source_generation_id,
        interpretation_summary=interpretation_summary,
        decision_summary=decision_summary,
        style_summary=style_summary,
        current_saved_model_id=current_saved_model_id,
        current_saved_model_editable=current_saved_model_editable,
        last_opened_model_id=last_opened_model_id,
        reopen_source=reopen_source,
        reopened_plan_summary=reopened_plan_summary,
    )
    _save_state(
        generation_id=generation_id,
        user_request=user_request,
        family=family,
        plan=normalized_plan.to_dict(),
        validation=validation,
        recipe=recipe.to_dict(),
        recipe_summary=recipe_summary,
        execution_path=execution_path,
        execution_summary=recipe_execution.summary,
        generation_path="recipe",
        generation_route="edited_plan_success" if regeneration_source else "recipe_success",
        generation_fallback_reason="",
        implementation_id=implementation_id,
        execution_recipe=execution_recipe,
        classification=classification,
        interpretation_summary=interpretation_summary,
        decision_summary=decision_summary,
        style_summary=style_summary,
        missing_info=missing_info,
        assumptions=assumptions,
        warnings=warnings,
        preview_model_path=preview_model_path,
        preview_asset_version=generation_id if preview_success else "",
        preview_export_status=preview_export_status,
        preview_export_message=preview_message,
        saved_model_entry=saved_model_entry,
        stl_export_path="",
        stl_export_status="not_requested",
        stl_export_message="",
        stl_source_model_path=preview_model_path,
        status="ready",
        generation_message=recipe_execution.summary or "Generation completed.",
        raw_status="ready",
        final_model_path=preview_model_path,
        output_source=execution_path,
        current_editable_params=current_editable_params,
        last_editable_params=current_editable_params,
        last_regeneration_source=regeneration_source,
        edited_plan_summary=edited_plan_summary,
        current_saved_model_id=current_saved_model_id,
        current_saved_model_editable=current_saved_model_editable,
        last_opened_model_id=last_opened_model_id,
        reopen_source=reopen_source,
        reopened_plan_summary=reopened_plan_summary,
    )
    return {
        "generation_id": generation_id,
        "request_text": user_request,
        "status": "ready",
        "raw_status": "ready",
        "is_terminal": True,
        "family": family,
        "family_label": family_label,
        "plan": normalized_plan.to_dict(),
        "validation": validation,
        "recipe": recipe.to_dict(),
        "recipe_summary": recipe_summary,
        "execution_path": execution_path,
        "execution_summary": recipe_execution.summary,
        "generation_path": "recipe",
        "generation_route": "edited_plan_success" if regeneration_source else "recipe_success",
        "generation_fallback_reason": "",
        "implementation_id": implementation_id,
        "execution_recipe": execution_recipe,
        "classification": classification,
        "interpretation_summary": interpretation_summary,
        "decision_summary": decision_summary,
        "style_summary": style_summary,
        "validation_summary": validation_summary,
        "missing_info": missing_info,
        "assumptions": assumptions,
        "warnings": warnings,
        "script_path": str(GENERATED_SCRIPT_PATH),
        "preview_model_path": preview_model_path,
        "preview_model_url": preview_model_url,
        "preview_asset_version": generation_id if preview_success else "",
        "preview_export_status": preview_export_status,
        "preview_export_message": preview_message,
        "final_model_path": preview_model_path,
        "final_model_url": preview_model_url,
        "output_source": execution_path,
        "saved_model_entry": saved_model_entry,
        "stl_export_path": "",
        "stl_export_status": "not_requested",
        "stl_export_message": "",
        "stl_source_model_path": preview_model_path,
        "supported_families": list(SUPPORTED_FAMILY_LABELS),
        "editable_params": editable_params,
        "current_editable_params": current_editable_params,
        "last_editable_params": current_editable_params,
        "last_regeneration_source": regeneration_source,
        "edited_plan_summary": edited_plan_summary,
        "current_saved_model_id": current_saved_model_id,
        "current_saved_model_editable": current_saved_model_editable,
        "last_opened_model_id": last_opened_model_id,
        "reopen_source": reopen_source,
        "reopened_plan_summary": reopened_plan_summary,
    }


def _classification_from_plan(plan: GeomancerPlan, *, source_generation_id: str = "", regeneration_source: str = "") -> dict:
    object_type = plan.intent.object_type or ""
    payload = {
        "family_key": object_type,
        "family_label": _family_label_from_plan(plan),
        "confidence": 1.0 if object_type else 0.0,
    }
    if source_generation_id:
        payload["source_generation_id"] = source_generation_id
    if regeneration_source:
        payload["regeneration_source"] = regeneration_source
    return payload


def _extract_editable_params(plan: GeomancerPlan) -> list[dict]:
    params: list[dict] = []
    dimensions = plan.dimensions or {}
    for key in (
        "overall_width_mm",
        "overall_depth_mm",
        "overall_height_mm",
        "material_thickness_mm",
        "wall_thickness_mm",
        "slot_width_mm",
        "slot_height_mm",
        "slot_depth_mm",
        "hole_diameter_mm",
        "lip_height_mm",
    ):
        if key in dimensions and isinstance(dimensions.get(key), (int, float)):
            params.append(
                {
                    "id": f"dimension:{key}",
                    "label": key.replace("_mm", "").replace("_", " ").title(),
                    "kind": "number",
                    "value": float(dimensions.get(key)),
                    "unit": "mm",
                    "group": "Dimensions",
                    "path": ["dimensions", key],
                    "step": 1 if key.endswith("count") else 0.1,
                }
            )
    params.extend(_extract_style_editable_params(plan))
    params.extend(_extract_component_editable_params(plan))
    params.extend(_extract_composition_editable_params(plan))
    params.extend(_extract_hybrid_editable_params(plan))
    return params


def collect_editable_params_for_plan(plan: dict | GeomancerPlan | object) -> list[dict]:
    """Return the bounded editable parameter surface for a plan."""
    return _extract_editable_params(_dict_to_plan(plan))


def _extract_style_editable_params(plan: GeomancerPlan) -> list[dict]:
    style = plan.style
    profile = getattr(style, "style_profile", "minimal") or "minimal"
    return [
        {
            "id": "style:style_profile",
            "label": "Style",
            "kind": "select",
            "value": profile,
            "options": sorted(ALLOWED_STYLE_PROFILES),
            "group": "Style",
            "path": ["style", "style_profile"],
        }
    ]


def _extract_component_editable_params(plan: GeomancerPlan) -> list[dict]:
    editables: list[dict] = []
    for component in plan.components:
        enabled = bool(component.params.get("enabled", True))
        component_id = component.id or component.type or "component"
        editable_fields = _editable_fields_for_component(component.type)
        if component.type in {"hole_pattern", "opening", "retaining_lip", "gusset", "mount_hole", "through_hole", "slot", "tab", "drain_hole"}:
            editables.append(
                {
                    "id": f"component:{component_id}:enabled",
                    "label": f"{_component_label(component.type)} enabled",
                    "kind": "toggle",
                    "value": enabled,
                    "group": "Features",
                    "collection": "components",
                    "item_id": component_id,
                    "field": "enabled",
                    "path": ["components", component_id, "params", "enabled"],
                }
            )
        for field_name, label, unit, step in editable_fields:
            if field_name not in component.params:
                continue
            value = component.params.get(field_name)
            if not isinstance(value, (int, float)):
                continue
            editables.append(
                {
                    "id": f"component:{component_id}:{field_name}",
                    "label": label,
                    "kind": "number",
                    "value": float(value),
                    "unit": unit,
                    "group": "Features",
                    "collection": "components",
                    "item_id": component_id,
                    "field": field_name,
                    "path": ["components", component_id, "params", field_name],
                    "step": step,
                }
            )
    return editables


def _extract_composition_editable_params(plan: GeomancerPlan) -> list[dict]:
    editables: list[dict] = []
    for index, item in enumerate(plan.composition):
        item_id = item.id or f"composition_{index + 1}"
        if index > 0:
            editables.append(
                {
                    "id": f"composition:{item_id}:enabled",
                    "label": f"{_component_label(item.type)} detail enabled",
                    "kind": "toggle",
                    "value": bool(item.params.get("enabled", True)),
                    "group": "Details",
                    "collection": "composition",
                    "item_id": item_id,
                    "field": "enabled",
                    "path": ["composition", item_id, "params", "enabled"],
                }
            )
        for field_name, label, unit, step in _editable_fields_for_component(item.type):
            if index == 0 and field_name in {"width_mm", "depth_mm", "height_mm", "radius_mm"}:
                continue
            value = item.params.get(field_name)
            if not isinstance(value, (int, float)):
                continue
            editables.append(
                {
                    "id": f"composition:{item_id}:{field_name}",
                    "label": label,
                    "kind": "number",
                    "value": float(value),
                    "unit": unit,
                    "group": "Details",
                    "collection": "composition",
                    "item_id": item_id,
                    "field": field_name,
                    "path": ["composition", item_id, "params", field_name],
                    "step": step,
                }
            )
    return editables


def _extract_hybrid_editable_params(plan: GeomancerPlan) -> list[dict]:
    editables: list[dict] = []
    for detail in plan.hybrid_details:
        detail_id = detail.id or detail.type or "hybrid_detail"
        editables.append(
            {
                "id": f"hybrid:{detail_id}:enabled",
                "label": f"{_component_label(detail.type)} detail enabled",
                "kind": "toggle",
                "value": bool(detail.params.get("enabled", True)),
                "group": "Hybrid details",
                "collection": "hybrid_details",
                "item_id": detail_id,
                "field": "enabled",
                "path": ["hybrid_details", detail_id, "params", "enabled"],
            }
        )
        for field_name, label, unit, step in _editable_fields_for_component(detail.type):
            value = detail.params.get(field_name)
            if not isinstance(value, (int, float)):
                continue
            editables.append(
                {
                    "id": f"hybrid:{detail_id}:{field_name}",
                    "label": label,
                    "kind": "number",
                    "value": float(value),
                    "unit": unit,
                    "group": "Hybrid details",
                    "collection": "hybrid_details",
                    "item_id": detail_id,
                    "field": field_name,
                    "path": ["hybrid_details", detail_id, "params", field_name],
                    "step": step,
                }
            )
    return editables


def _editable_fields_for_component(component_type: str) -> list[tuple[str, str, str, float]]:
    return {
        "hole_pattern": [
            ("count", "Hole count", "count", 1.0),
            ("diameter_mm", "Hole diameter", "mm", 0.1),
            ("margin_mm", "Hole margin", "mm", 0.1),
        ],
        "opening": [
            ("width_mm", "Opening width", "mm", 0.1),
            ("height_mm", "Opening height", "mm", 0.1),
            ("depth_mm", "Opening depth", "mm", 0.1),
        ],
        "retaining_lip": [
            ("height_mm", "Lip height", "mm", 0.1),
        ],
        "shell": [
            ("wall_thickness_mm", "Wall thickness", "mm", 0.1),
        ],
        "angled_support": [
            ("angle_deg", "Support angle", "deg", 0.5),
            ("cradle_depth_mm", "Cradle depth", "mm", 0.1),
        ],
        "hook_tip": [
            ("radius_mm", "Tip radius", "mm", 0.1),
            ("angle_deg", "Tip angle", "deg", 0.5),
        ],
        "hook_arm": [
            ("length_mm", "Hook length", "mm", 0.1),
        ],
        "tab": [
            ("width_mm", "Tab width", "mm", 0.1),
            ("height_mm", "Tab height", "mm", 0.1),
            ("thickness_mm", "Tab thickness", "mm", 0.1),
        ],
        "slot": [
            ("width_mm", "Slot width", "mm", 0.1),
            ("height_mm", "Slot height", "mm", 0.1),
            ("depth_mm", "Slot depth", "mm", 0.1),
        ],
        "mount_hole": [
            ("diameter_mm", "Hole diameter", "mm", 0.1),
        ],
        "through_hole": [
            ("diameter_mm", "Hole diameter", "mm", 0.1),
        ],
        "drain_hole": [
            ("diameter_mm", "Hole diameter", "mm", 0.1),
        ],
        "gusset": [
            ("thickness_mm", "Gusset thickness", "mm", 0.1),
        ],
    }.get(component_type, [])


def _component_label(component_type: str) -> str:
    return str(component_type or "feature").replace("_", " ").title()


def _summarize_plan_edits(source_plan: GeomancerPlan, edited_plan: GeomancerPlan) -> str:
    source_map = {item["id"]: item for item in _extract_editable_params(source_plan)}
    edited_map = {item["id"]: item for item in _extract_editable_params(edited_plan)}
    changes: list[str] = []
    for key, edited_descriptor in edited_map.items():
        source_descriptor = source_map.get(key)
        if source_descriptor is None:
            continue
        source_value = source_descriptor.get("value")
        edited_value = edited_descriptor.get("value")
        if source_value == edited_value:
            continue
        label = edited_descriptor.get("label") or key
        if edited_descriptor.get("kind") == "toggle":
            changes.append(f"{label} {'enabled' if edited_value else 'disabled'}")
        elif edited_descriptor.get("kind") == "select":
            changes.append(f"{label} set to {edited_value}")
        else:
            unit = edited_descriptor.get("unit") or ""
            suffix = f" {unit}" if unit else ""
            changes.append(f"{label} {source_value}{suffix} -> {edited_value}{suffix}")
        if len(changes) >= 4:
            break
    if not changes:
        return "No parameter changes were detected."
    return "Updated " + ", ".join(changes) + "."


def interpret_prompt_to_plan(user_request: str, client=None, log=print) -> dict:
    """Temporary interpretation boundary that returns Plan Schema v1."""
    del client
    request_text = str(user_request or "").strip()
    if not request_text:
        return {
            "status": "invalid",
            "message": "Enter a prompt before generating.",
            "classification": {},
            "plan": {},
            "missing_info": ["request_text"],
            "assumptions": [],
            "warnings": [],
            "notes": [],
            "interpretation_summary": "Prompt is empty.",
            "decision_summary": "No generation was started because the prompt was empty.",
            "style_summary": "",
        }
    unsupported_reason = _unsupported_request_reason(request_text)
    if unsupported_reason:
        return {
            "status": "unsupported",
            "message": unsupported_reason,
            "classification": {},
            "plan": {},
            "missing_info": [],
            "assumptions": [],
            "warnings": [],
            "notes": [],
            "interpretation_summary": "The request is outside the current supported object vocabulary.",
            "decision_summary": unsupported_reason,
            "style_summary": "",
        }
    object_type = _infer_object_type(request_text)
    construction_mode = "constraint"
    if not object_type:
        object_type = _infer_compositional_object_type(request_text)
        if object_type:
            construction_mode = "compositional"
    elif object_type in COMPOSITIONAL_OBJECT_TYPES:
        construction_mode = "compositional"
    if not object_type:
        return {
            "status": "unsupported",
            "message": "This request does not name a supported object type.",
            "classification": {},
            "plan": {},
            "missing_info": [],
            "assumptions": [],
            "warnings": [],
            "notes": [],
            "interpretation_summary": "No supported object type could be inferred from the request.",
            "decision_summary": "No supported object type could be inferred.",
            "style_summary": "",
        }
    allow_defaults = _should_use_object_defaults(request_text, object_type)
    dimension_hints = _extract_dimension_hints(request_text, object_type)
    plan = _build_interpreted_plan(
        request_text,
        object_type,
        construction_mode=construction_mode,
        allow_defaults=allow_defaults,
        dimension_hints=dimension_hints,
    )
    classification = {
        "status": "ready",
        "family_key": object_type,
        "object_type": object_type,
        "confidence": 1.0,
        "message": "",
    }
    status = "ready" if not plan.missing_info else "clarify"
    message = "" if status == "ready" else _clarification_message(plan.missing_info, object_type)
    interpretation_summary = _build_interpretation_summary(plan, status)
    decision_summary = _build_decision_summary(
        status,
        object_type=object_type,
        construction_mode=plan.construction_mode,
        missing_info=plan.missing_info,
        assumptions=plan.assumptions,
        warnings=plan.warnings,
    )
    style_summary = _build_style_summary(plan, status)
    log(f"Interpreted object type: {object_type}")
    return {
        "status": status,
        "message": message,
        "plan": plan,
        "classification": classification,
        "missing_info": list(plan.missing_info),
        "assumptions": list(plan.assumptions),
        "warnings": list(plan.warnings),
        "notes": list(plan.notes),
        "interpretation_summary": interpretation_summary,
        "decision_summary": decision_summary,
        "style_summary": style_summary,
    }


def _build_interpreted_plan(
    request_text: str,
    object_type: str,
    *,
    construction_mode: str = "constraint",
    allow_defaults: bool = False,
    dimension_hints: dict[str, object] | None = None,
) -> GeomancerPlan:
    dimension_hints = dimension_hints or {"dimensions": {}, "notes": [], "warnings": []}
    extracted_dimensions = dict(dimension_hints.get("dimensions") or {})
    notes = list(dimension_hints.get("notes") or [])
    warnings = list(dimension_hints.get("warnings") or [])
    style, style_notes, style_warnings = _style_from_request(request_text, construction_mode, object_type)
    for note in style_notes:
        if note not in notes:
            notes.append(note)
    for warning in style_warnings:
        if warning not in warnings:
            warnings.append(warning)
    thickness = _extract_natural_thickness(request_text)
    if thickness is None and "material_thickness_mm" in extracted_dimensions:
        thickness = _coerce_float(extracted_dimensions.get("material_thickness_mm"), 0.0) or None
    thickness_assumed = False
    if thickness is None and allow_defaults and not extracted_dimensions:
        thickness = _default_thickness(object_type)
        thickness_assumed = True
    hole_count = _extract_hole_count(request_text)
    hole_diameter = _extract_hole_diameter(request_text)

    plan = GeomancerPlan(
        request_text=request_text,
        construction_mode=construction_mode,
        intent=GeomancerIntent(
            object_type=object_type,
            object_label=object_type.replace("_", " "),
            use_case=_default_use_case(object_type),
            printable=True,
            editable_in_blender=True,
        ),
        constraints={
            "supports_required": False,
            "symmetry": False,
            "target_process": "fdm_3d_printing",
            "max_overhang_deg": 55,
        },
        style=style,
    )

    if construction_mode == "compositional":
        defaults = _default_compositional_dimensions(object_type)
        if extracted_dimensions:
            plan.dimensions.update(extracted_dimensions)
        for key, value in defaults.items():
            if key not in plan.dimensions:
                plan.dimensions[key] = value
                plan.assumptions.append(f"Assumed {value:g} mm {key.replace('_mm', '').replace('_', ' ')} for the {object_type.replace('_', ' ')} template.")
        if thickness is None:
            thickness = _coerce_float(plan.dimensions.get("material_thickness_mm"), 0.0)
        if thickness:
            plan.dimensions["material_thickness_mm"] = float(thickness)
        if thickness_assumed and thickness:
            plan.assumptions.append(f"Assumed {float(thickness):g} mm material thickness.")
        plan.composition = _build_compositional_template(object_type, plan.dimensions, plan.style)
        if not plan.composition:
            plan.missing_info.append("composition")
            plan.notes.append("Compositional interpretation needs a supported primitive template.")
        plan.notes.append(f"Compositional template selected: {object_type}.")
    else:
        if object_type == "plate" and "overall_width_mm" in extracted_dimensions and "overall_height_mm" not in extracted_dimensions and "material_thickness_mm" in extracted_dimensions:
            extracted_dimensions["overall_height_mm"] = extracted_dimensions["material_thickness_mm"]

        if extracted_dimensions:
            plan.dimensions.update(extracted_dimensions)
            if thickness is not None:
                plan.dimensions["material_thickness_mm"] = thickness
            if thickness_assumed:
                plan.assumptions.append(f"Assumed {float(thickness):g} mm material thickness.")
        elif allow_defaults and object_type == "phone_stand":
            defaults = _default_phone_stand_dimensions()
            plan.dimensions.update(defaults)
            plan.assumptions.extend(
                [
                    "Assumed a general smartphone-scale phone stand envelope.",
                    "Assumed default overall dimensions for a simple phone stand.",
                    f"Assumed {defaults['material_thickness_mm']:g} mm material thickness.",
                ]
            )
            thickness = _coerce_float(plan.dimensions.get("material_thickness_mm"), _default_thickness(object_type))
        else:
            plan.missing_info.extend(_required_dimension_keys_for_object_type(object_type))
            plan.notes.append("Interpretation withheld default overall dimensions pending user-provided size constraints.")

        if plan.dimensions:
            required_keys = _required_dimension_keys_for_object_type(object_type)
            missing_keys = [key for key in required_keys if key not in plan.dimensions]
            for key in missing_keys:
                if key not in plan.missing_info:
                    plan.missing_info.append(key)
            if object_type == "phone_stand" and allow_defaults and not missing_keys:
                plan.missing_info = []
            if plan.missing_info:
                plan.notes.append("Interpretation preserved extracted dimensions and narrowed clarification to the remaining fields.")

            thickness = float(thickness or 0.0)
            overall_width = _coerce_float(plan.dimensions.get("overall_width_mm"), 0.0)
            overall_depth = _coerce_float(plan.dimensions.get("overall_depth_mm"), 0.0)
            overall_height = _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0)

            if object_type == "phone_stand":
                plan.components = [
                    GeomancerComponent("base", "base_plate", {"width_mm": overall_width, "depth_mm": overall_depth, "thickness_mm": thickness}),
                    GeomancerComponent("support", "angled_support", {"height_mm": overall_height, "angle_deg": 65.0, "cradle_depth_mm": max(thickness * 4.0, 24.0)}),
                    GeomancerComponent("lip", "retaining_lip", {"height_mm": max(thickness * 0.9, 5.0)}),
                ]
                if "cable" in request_text.lower():
                    plan.components.append(GeomancerComponent("cable_cutout", "opening", {"enabled": True, "width_mm": 12.0, "depth_mm": max(thickness * 2.5, 8.0), "height_mm": 8.0}))
            elif object_type == "bracket":
                plan.components = [
                    GeomancerComponent("horizontal_leg", "horizontal_leg", {"length_mm": overall_width, "width_mm": overall_depth, "thickness_mm": thickness}),
                    GeomancerComponent("vertical_leg", "vertical_leg", {"height_mm": overall_height, "thickness_mm": thickness}),
                ]
                if "gusset" in request_text.lower() or "reinforced" in request_text.lower():
                    plan.components.append(GeomancerComponent("gusset", "gusset", {"thickness_mm": thickness}))
                if hole_count:
                    plan.components.append(GeomancerComponent("hole_pattern", "hole_pattern", {"count": hole_count, "diameter_mm": hole_diameter or 5.0}))
            elif object_type in {"enclosure", "tray"}:
                plan.components = [
                    GeomancerComponent("shell", "shell", {"width_mm": overall_width, "depth_mm": overall_depth, "height_mm": overall_height, "wall_thickness_mm": thickness}),
                    GeomancerComponent("opening", "opening", {"open_top": True, "front_opening": "opening" in request_text.lower() and "front" in request_text.lower()}),
                ]
            elif object_type == "plate":
                plan.components = [
                    GeomancerComponent("base", "base_plate", {"width_mm": overall_width, "height_mm": overall_height, "thickness_mm": thickness}),
                ]
                if hole_count:
                    plan.components.append(GeomancerComponent("holes", "hole_pattern", {"count": hole_count, "diameter_mm": hole_diameter or 5.0}))
            elif object_type == "hook_mount":
                plan.components = [
                    GeomancerComponent("back", "back_plate", {"width_mm": overall_width, "height_mm": overall_height, "thickness_mm": thickness}),
                    GeomancerComponent("arm", "hook_arm", {"length_mm": max(overall_depth * 0.45, 24.0)}),
                    GeomancerComponent("tip", "hook_tip", {"radius_mm": max(thickness, 4.0), "angle_deg": 18.0}),
                    GeomancerComponent("holes", "hole_pattern", {"count": hole_count or 2, "diameter_mm": hole_diameter or 5.0, "margin_mm": 10.0}),
                ]
            elif object_type == "standoff":
                plan.components = [
                    GeomancerComponent("body", "cylinder", {"diameter_mm": overall_width, "height_mm": overall_height}),
                    GeomancerComponent("center_hole", "through_hole", {"diameter_mm": max(thickness, 3.0)}),
                ]
            elif object_type == "adapter":
                plan.components = [
                    GeomancerComponent("large", "cylinder", {"diameter_mm": overall_width, "height_mm": overall_height * 0.5}),
                    GeomancerComponent("small", "cylinder", {"diameter_mm": max(overall_depth, overall_width * 0.6), "height_mm": overall_height * 0.5}),
                ]
                if "hole" in request_text.lower():
                    plan.components.append(GeomancerComponent("through_hole", "through_hole", {"diameter_mm": max(thickness, 3.0)}))

    for note in notes:
        if note not in plan.notes:
            plan.notes.append(note)
    for warning in warnings:
        if warning not in plan.warnings:
            plan.warnings.append(warning)

    pending_hybrid_details, hybrid_notes, hybrid_warnings, hybrid_summary = _build_hybrid_details(request_text, object_type, plan, style)

    if plan.construction_mode == "constraint":
        required_keys = _required_dimension_keys_for_object_type(object_type)
        missing_keys = []
        if plan.dimensions:
            missing_keys = [key for key in required_keys if key not in plan.dimensions]
            for key in missing_keys:
                if key not in plan.missing_info:
                    plan.missing_info.append(key)
        if object_type == "phone_stand" and allow_defaults and not missing_keys:
            plan.missing_info = []
        if plan.missing_info:
            plan.notes.append("Interpretation preserved extracted dimensions and narrowed clarification to the remaining fields.")

    if not plan.dimensions and not allow_defaults and plan.construction_mode == "constraint" and not pending_hybrid_details:
        return plan

    if pending_hybrid_details:
        plan.hybrid_details = pending_hybrid_details
        plan.construction_mode = "hybrid"
        if hybrid_summary:
            plan.notes.append(hybrid_summary)
        plan.notes.append("Hybrid interpretation combined a primary base with bounded secondary details.")
    for note in hybrid_notes:
        if note not in plan.notes:
            plan.notes.append(note)
    for warning in hybrid_warnings:
        if warning not in plan.warnings:
            plan.warnings.append(warning)

    return plan


def _should_use_object_defaults(request_text: str, object_type: str) -> bool:
    if object_type != "phone_stand":
        return False
    text = request_text.lower()
    return any(term in text for term in ("simple", "basic", "compact", "minimal"))


def _default_phone_stand_dimensions() -> dict[str, float]:
    return {
        "overall_width_mm": 90.0,
        "overall_depth_mm": 85.0,
        "overall_height_mm": 120.0,
        "material_thickness_mm": 5.0,
    }


def _default_compositional_dimensions(object_type: str) -> dict[str, float]:
    return {
        "crate": {
            "overall_width_mm": 80.0,
            "overall_depth_mm": 80.0,
            "overall_height_mm": 60.0,
            "material_thickness_mm": 4.0,
        },
        "barrel": {
            "overall_width_mm": 60.0,
            "overall_depth_mm": 60.0,
            "overall_height_mm": 100.0,
            "material_thickness_mm": 3.0,
        },
        "canister": {
            "overall_width_mm": 60.0,
            "overall_depth_mm": 60.0,
            "overall_height_mm": 120.0,
            "material_thickness_mm": 3.0,
        },
        "pedestal": {
            "overall_width_mm": 70.0,
            "overall_depth_mm": 70.0,
            "overall_height_mm": 90.0,
            "material_thickness_mm": 5.0,
        },
        "primitive_assembly": {
            "overall_width_mm": 90.0,
            "overall_depth_mm": 90.0,
            "overall_height_mm": 90.0,
            "material_thickness_mm": 4.0,
        },
    }.get(object_type, {
        "overall_width_mm": 80.0,
        "overall_depth_mm": 80.0,
        "overall_height_mm": 80.0,
        "material_thickness_mm": 4.0,
    })


def _style_from_request(request_text: str, construction_mode: str, object_type: str) -> tuple[GeomancerStyle, list[str], list[str]]:
    text = request_text.lower()
    requested_profile, style_warnings = _infer_style_profile(text)
    style_profile = requested_profile or STYLE_DEFAULT_BY_OBJECT_TYPE.get(object_type, "minimal")
    notes: list[str] = []
    warnings: list[str] = []
    warnings.extend(style_warnings)
    if style_profile not in ALLOWED_STYLE_PROFILES:
        warnings.append(f"Unsupported style profile '{style_profile}' was normalized to minimal.")
        style_profile = "minimal"
    supported_profiles = STYLE_COMPATIBILITY_BY_OBJECT_TYPE.get(object_type, {"minimal"})
    if style_profile not in supported_profiles:
        warnings.append(f"Style profile '{style_profile}' is not supported for the {object_type.replace('_', ' ')}; applied minimal styling.")
        style_profile = "minimal"
    if not requested_profile and construction_mode == "compositional":
        notes.append(f"Applied the {style_profile} default style for the {object_type.replace('_', ' ')} template.")
    defaults = STYLE_DEFAULTS_BY_PROFILE.get(style_profile, STYLE_DEFAULTS_BY_PROFILE["minimal"])
    return (
        GeomancerStyle(
            style_profile=style_profile,
            shape_language=defaults["shape_language"],
            edge_treatment=defaults["edge_treatment"],
            detail_density=defaults["detail_density"],
            accent_profile=defaults["accent_profile"],
        ),
        notes,
        warnings,
    )


def _infer_style_profile(request_text: str) -> tuple[str, list[str]]:
    terms = (
        ("rounded", (r"\brounded\b",)),
        ("sci_fi", (r"\bsci[-\s]?fi\b",)),
        ("industrial", (r"\bindustrial\b",)),
        ("low_poly", (r"\blow\s+poly\b",)),
        ("minimal", (r"\bminimal\b",)),
    )
    matches: list[tuple[int, int, str]] = []
    for priority, (profile, patterns) in enumerate(terms):
        for pattern in patterns:
            match = re.search(pattern, request_text)
            if match:
                matches.append((match.start(), priority, profile))
                break
    if not matches:
        return "", []
    matches.sort(key=lambda item: (item[0], item[1]))
    profile = matches[0][2]
    if len({item[2] for item in matches}) > 1:
        return profile, [f"Multiple style descriptors were detected; using {profile.replace('_', ' ')} styling."]
    return profile, []


def _build_compositional_template(object_type: str, dimensions: dict[str, object], style: GeomancerStyle) -> list[GeomancerCompositionItem]:
    width = _coerce_float(dimensions.get("overall_width_mm"), _default_compositional_dimensions(object_type)["overall_width_mm"])
    depth = _coerce_float(dimensions.get("overall_depth_mm"), _default_compositional_dimensions(object_type)["overall_depth_mm"])
    height = _coerce_float(dimensions.get("overall_height_mm"), _default_compositional_dimensions(object_type)["overall_height_mm"])
    profile = str(getattr(style, "style_profile", "minimal") or "minimal")

    if object_type == "crate":
        items = [
            GeomancerCompositionItem(
                id="crate_body",
                type="cube",
                params={"width_mm": width, "depth_mm": depth, "height_mm": height},
            )
        ]
        if profile == "low_poly":
            cap_height = max(height * 0.18, 6.0)
            items.append(
                GeomancerCompositionItem(
                    id="crate_cap",
                    type="cube",
                    params={"width_mm": width * 0.84, "depth_mm": depth * 0.84, "height_mm": cap_height},
                    position=[0.0, 0.0, (height / 2.0) - (cap_height / 2.0)],
                )
            )
        elif profile == "industrial":
            band_height = max(height * 0.12, 4.0)
            items.append(
                GeomancerCompositionItem(
                    id="crate_band",
                    type="cube",
                    params={"width_mm": width * 0.9, "depth_mm": depth * 0.9, "height_mm": band_height},
                    position=[0.0, 0.0, (height / 2.0) - (band_height / 2.0)],
                )
            )
        elif profile == "sci_fi":
            band_height = max(height * 0.1, 4.0)
            items.extend(
                [
                    GeomancerCompositionItem(
                        id="crate_panel_left",
                        type="cube",
                        params={"width_mm": width * 0.12, "depth_mm": depth * 0.75, "height_mm": max(height * 0.72, 18.0)},
                        position=[-(width * 0.31), 0.0, 0.0],
                    ),
                    GeomancerCompositionItem(
                        id="crate_panel_right",
                        type="cube",
                        params={"width_mm": width * 0.12, "depth_mm": depth * 0.75, "height_mm": max(height * 0.72, 18.0)},
                        position=[width * 0.31, 0.0, 0.0],
                    ),
                    GeomancerCompositionItem(
                        id="crate_band",
                        type="cube",
                        params={"width_mm": width * 0.86, "depth_mm": depth * 0.86, "height_mm": band_height},
                        position=[0.0, 0.0, 0.0],
                    ),
                ]
            )
        return items
    if object_type == "barrel":
        vertices = 12 if profile == "low_poly" else 20 if profile == "industrial" else 28 if profile == "sci_fi" else 40 if profile == "rounded" else 24
        items = [
            GeomancerCompositionItem(
                id="barrel_body",
                type="cylinder",
                params={"radius_mm": min(width, depth) / 2.0, "height_mm": height, "vertices": vertices},
            )
        ]
        if profile in {"industrial", "sci_fi"}:
            band_height = max(height * 0.08, 4.0)
            band_radius = min(width, depth) * 0.49
            items.extend(
                [
                    GeomancerCompositionItem(
                        id="barrel_top_band",
                        type="cylinder",
                        params={"radius_mm": band_radius, "height_mm": band_height, "vertices": vertices},
                        position=[0.0, 0.0, (height * 0.32)],
                    ),
                    GeomancerCompositionItem(
                        id="barrel_bottom_band",
                        type="cylinder",
                        params={"radius_mm": band_radius, "height_mm": band_height, "vertices": vertices},
                        position=[0.0, 0.0, -(height * 0.32)],
                    ),
                ]
            )
        return items
    if object_type == "canister":
        vertices = 12 if profile == "low_poly" else 20 if profile == "industrial" else 28 if profile == "sci_fi" else 40 if profile == "rounded" else 24
        body_height = max(height * 0.72, 24.0)
        cap_height = max(height - body_height, 12.0)
        items = [
            GeomancerCompositionItem(
                id="canister_body",
                type="cylinder",
                params={"radius_mm": min(width, depth) / 2.0, "height_mm": body_height, "vertices": vertices},
                position=[0.0, 0.0, -(cap_height / 2.0)],
            ),
            GeomancerCompositionItem(
                id="canister_cap",
                type="cylinder",
                params={"radius_mm": min(width, depth) * 0.46, "height_mm": cap_height, "vertices": vertices},
                position=[0.0, 0.0, body_height / 2.0],
            ),
        ]
        if profile in {"industrial", "sci_fi"}:
            items.append(
                GeomancerCompositionItem(
                    id="canister_band",
                    type="cylinder",
                    params={"radius_mm": min(width, depth) * 0.49, "height_mm": max(height * 0.08, 4.0), "vertices": vertices},
                    position=[0.0, 0.0, 0.0],
                )
            )
        return items
    if object_type == "pedestal":
        base_height = max(height * 0.24, 12.0)
        shaft_height = max(height * 0.52, 24.0)
        cap_height = max(height - base_height - shaft_height, 8.0)
        items = [
            GeomancerCompositionItem(
                id="pedestal_base",
                type="cube",
                params={"width_mm": width, "depth_mm": depth, "height_mm": base_height},
                position=[0.0, 0.0, -(height / 2.0) + (base_height / 2.0)],
            ),
            GeomancerCompositionItem(
                id="pedestal_shaft",
                type="cube",
                params={"width_mm": width * 0.68, "depth_mm": depth * 0.68, "height_mm": shaft_height},
                position=[0.0, 0.0, -(height / 2.0) + base_height + (shaft_height / 2.0)],
            ),
            GeomancerCompositionItem(
                id="pedestal_cap",
                type="cube",
                params={"width_mm": width * 0.82, "depth_mm": depth * 0.82, "height_mm": cap_height},
                position=[0.0, 0.0, (height / 2.0) - (cap_height / 2.0)],
            ),
        ]
        if profile == "rounded":
            items.append(
                GeomancerCompositionItem(
                    id="pedestal_top_sphere",
                    type="sphere",
                    params={"radius_mm": min(width, depth) * 0.12},
                    position=[0.0, 0.0, (height / 2.0) + (min(width, depth) * 0.08)],
                )
            )
        return items
    if object_type == "primitive_assembly":
        vertices = 12 if profile == "low_poly" else 20 if profile == "industrial" else 28 if profile == "sci_fi" else 40 if profile == "rounded" else 24
        return [
            GeomancerCompositionItem(
                id="assembly_cube",
                type="cube",
                params={"width_mm": width * 0.48, "depth_mm": depth * 0.48, "height_mm": height * 0.48},
                position=[-width * 0.18, 0.0, -height * 0.06],
            ),
            GeomancerCompositionItem(
                id="assembly_cylinder",
                type="cylinder",
                params={"radius_mm": min(width, depth) * 0.14, "height_mm": height * 0.9, "vertices": vertices},
                position=[width * 0.12, 0.0, 0.0],
            ),
            GeomancerCompositionItem(
                id="assembly_sphere",
                type="sphere",
                params={"radius_mm": min(width, depth, height) * 0.18},
                position=[width * 0.22, 0.0, height * 0.1],
            ),
        ]
    return []


def _build_hybrid_details(
    request_text: str,
    object_type: str,
    plan: GeomancerPlan,
    style: GeomancerStyle,
) -> tuple[list[GeomancerHybridDetail], list[str], list[str], str]:
    text = request_text.lower()
    details: list[GeomancerHybridDetail] = []
    notes: list[str] = []
    warnings: list[str] = []
    width = _coerce_float(plan.dimensions.get("overall_width_mm"), _default_compositional_dimensions(object_type)["overall_width_mm"])
    depth = _coerce_float(plan.dimensions.get("overall_depth_mm"), _default_compositional_dimensions(object_type)["overall_depth_mm"])
    height = _coerce_float(plan.dimensions.get("overall_height_mm"), _default_compositional_dimensions(object_type)["overall_height_mm"])
    thickness = _coerce_float(plan.dimensions.get("material_thickness_mm"), _default_thickness(object_type))

    if object_type in COMPOSITIONAL_OBJECT_TYPES:
        features = _build_hybrid_functional_features(text, object_type, width, depth, height, thickness)
        details.extend(features)
        if details:
            notes.append("Mapped supported functional features onto the compositional base.")
    else:
        accents = _build_hybrid_compositional_accents(text, object_type, width, depth, height, style)
        details.extend(accents)
        if details:
            notes.append("Mapped supported compositional accents onto the functional base.")

    if not details:
        return [], notes, warnings, ""
    summary = _hybrid_summary(object_type, details)
    return details, notes, warnings, summary


def _build_hybrid_compositional_accents(
    request_text: str,
    object_type: str,
    width: float,
    depth: float,
    height: float,
    style: GeomancerStyle,
) -> list[GeomancerHybridDetail]:
    text = request_text.lower()
    style_profile = str(getattr(style, "style_profile", "") or "minimal")
    accent_requested = any(
        phrase in text
        for phrase in (
            "decorative",
            "accent",
            "detail",
            "raised",
            "rib",
            "band",
            "panel",
            "sci fi",
            "sci-fi",
            "industrial",
            "block",
            "cylinder",
        )
    )
    if not accent_requested and style_profile not in {"industrial", "sci_fi"}:
        return []
    accent_details: list[GeomancerHybridDetail] = []
    use_cylinders = "cylinder" in text or "round" in text or "rib" in text or (style_profile == "rounded" and accent_requested)
    use_blocks = "block" in text or "accent" in text or "detail" in text or "panel" in text or "band" in text or style_profile in {"industrial", "sci_fi"}
    size_scale = max(min(width, depth, height) * 0.12, 4.0)
    accent_height = max(height * 0.18, 6.0)
    accent_radius = max(min(width, depth) * 0.08, 3.5)
    if object_type == "enclosure":
        if use_cylinders:
            accent_details.extend(
                [
                    GeomancerHybridDetail(
                        id="enclosure_accent_left",
                        source_mode="compositional",
                        type="cylinder",
                        params={"radius_mm": accent_radius, "height_mm": accent_height},
                        position=[-(width * 0.22), 0.0, (height * 0.26)],
                    ),
                    GeomancerHybridDetail(
                        id="enclosure_accent_right",
                        source_mode="compositional",
                        type="cylinder",
                        params={"radius_mm": accent_radius, "height_mm": accent_height},
                        position=[width * 0.22, 0.0, (height * 0.26)],
                    ),
                ]
            )
        elif use_blocks:
            accent_details.extend(
                [
                    GeomancerHybridDetail(
                        id="enclosure_block_left",
                        source_mode="compositional",
                        type="cube",
                        params={"width_mm": size_scale, "depth_mm": size_scale, "height_mm": max(size_scale * 0.9, 4.0)},
                        position=[-(width * 0.2), 0.0, (height * 0.22)],
                    ),
                    GeomancerHybridDetail(
                        id="enclosure_block_right",
                        source_mode="compositional",
                        type="cube",
                        params={"width_mm": size_scale, "depth_mm": size_scale, "height_mm": max(size_scale * 0.9, 4.0)},
                        position=[width * 0.2, 0.0, (height * 0.22)],
                    ),
                ]
            )
    elif object_type == "phone_stand":
        accent_type = "cylinder" if style_profile == "rounded" or use_cylinders else "cube"
        accent_params = (
            {"radius_mm": max(accent_radius, 3.5), "height_mm": max(size_scale * 0.8, 4.0)}
            if accent_type == "cylinder"
            else {"width_mm": size_scale, "depth_mm": size_scale * 0.8, "height_mm": max(size_scale * 0.8, 4.0)}
        )
        accent_details.extend(
            [
                GeomancerHybridDetail(
                    id="phone_stand_accent_left",
                    source_mode="compositional",
                    type=accent_type,
                    params=dict(accent_params),
                    position=[-(width * 0.16), -(depth * 0.08), (height * 0.18)],
                ),
                GeomancerHybridDetail(
                    id="phone_stand_accent_right",
                    source_mode="compositional",
                    type=accent_type,
                    params=dict(accent_params),
                    position=[width * 0.16, -(depth * 0.08), (height * 0.18)],
                ),
            ]
        )
    elif object_type == "bracket":
        accent_details.append(
            GeomancerHybridDetail(
                id="bracket_rib",
                source_mode="compositional",
                type="cylinder" if style_profile == "rounded" else "cube",
                params=(
                    {"radius_mm": max(min(width, depth) * 0.08, 4.0), "height_mm": max(height * 0.14, 6.0)}
                    if style_profile == "rounded"
                    else {"width_mm": max(width * 0.18, 8.0), "depth_mm": max(depth * 0.9, 10.0), "height_mm": max(height * 0.14, 6.0)}
                ),
                position=[-(width * 0.18), 0.0, -(height * 0.08)],
            )
        )
    elif object_type == "tray":
        accent_details.append(
            GeomancerHybridDetail(
                id="tray_band",
                source_mode="compositional",
                type="cube",
                params={"width_mm": width * 0.92, "depth_mm": depth * 0.92, "height_mm": max(height * 0.1, 4.0)},
                position=[0.0, 0.0, (height * 0.34)],
            )
        )
    elif object_type == "plate":
        accent_details.append(
            GeomancerHybridDetail(
                id="plate_block_accent",
                source_mode="compositional",
                type="cube",
                params={"width_mm": width * 0.18, "depth_mm": width * 0.18, "height_mm": max(height * 0.15, 4.0)},
                position=[-(width * 0.2), 0.0, 0.0],
            )
        )
    return accent_details


def _build_hybrid_functional_features(
    request_text: str,
    object_type: str,
    width: float,
    depth: float,
    height: float,
    thickness: float,
) -> list[GeomancerHybridDetail]:
    text = request_text.lower()
    feature_details: list[GeomancerHybridDetail] = []
    hole_diameter = _extract_hole_diameter(request_text) or max(thickness * 1.25, 4.0)
    if "mount" in text or "hole" in text:
        count = 4 if any(word in text for word in ("four", "4", "corner")) or object_type in {"crate", "pedestal", "primitive_assembly"} else 2
        feature_details.append(
            GeomancerHybridDetail(
                id=f"{object_type}_mount_holes",
                source_mode="constraint",
                type="hole_pattern",
                operation="difference",
                params={
                    "count": count,
                    "diameter_mm": hole_diameter,
                    "layout": "corners" if count >= 4 else "pair_horizontal",
                    "margin_mm": max(thickness * 2.0, 8.0),
                },
            )
        )
    if "cable slot" in text or ("slot" in text and object_type in {"pedestal", "primitive_assembly", "crate", "canister", "barrel"}):
        feature_details.append(
            GeomancerHybridDetail(
                id=f"{object_type}_slot",
                source_mode="constraint",
                type="slot",
                operation="difference",
                params={
                    "width_mm": max(width * 0.18, 12.0),
                    "height_mm": max(height * 0.16, 10.0),
                    "depth_mm": max(depth * 0.22, thickness * 3.0),
                },
                position=[0.0, depth * 0.18, 0.0],
            )
        )
    if "tab" in text:
        feature_details.append(
            GeomancerHybridDetail(
                id=f"{object_type}_tabs",
                source_mode="constraint",
                type="tab",
                operation="union",
                params={
                    "width_mm": max(width * 0.16, 10.0),
                    "height_mm": max(height * 0.08, 6.0),
                    "thickness_mm": max(thickness, 3.0),
                },
                position=[0.0, -(depth * 0.22), (height * 0.18)],
            )
        )
    if "through hole" in text:
        feature_details.append(
            GeomancerHybridDetail(
                id=f"{object_type}_through_hole",
                source_mode="constraint",
                type="through_hole",
                operation="difference",
                params={"diameter_mm": hole_diameter, "count": 1},
            )
        )
    if "opening" in text and not any(detail.type == "slot" for detail in feature_details):
        feature_details.append(
            GeomancerHybridDetail(
                id=f"{object_type}_opening",
                source_mode="constraint",
                type="opening",
                operation="difference",
                params={
                    "width_mm": max(width * 0.22, 12.0),
                    "height_mm": max(height * 0.18, 10.0),
                    "depth_mm": max(depth * 0.18, thickness * 2.5),
                },
                position=[0.0, depth * 0.2, 0.0],
            )
        )
    return feature_details


def _hybrid_summary(object_type: str, details: list[GeomancerHybridDetail]) -> str:
    if not details:
        return ""
    phrases = [_hybrid_detail_phrase(detail) for detail in details[:2]]
    detail_text = " and ".join(phrases) if len(phrases) == 2 else phrases[0]
    return f"Hybrid construction: {object_type.replace('_', ' ')} with {detail_text}."


def _hybrid_detail_phrase(detail: GeomancerHybridDetail) -> str:
    if detail.source_mode == "compositional":
        if detail.type == "cube":
            return "decorative block accents"
        if detail.type == "cylinder":
            return "raised cylinder accents"
        if detail.type == "sphere":
            return "simple sphere accents"
        return f"{detail.type.replace('_', ' ')} accents"
    if detail.type == "hole_pattern":
        count = int(float(detail.params.get("count", 0) or 0))
        return "four mounting holes" if count >= 4 else "mounting holes"
    if detail.type == "slot":
        return "a cable slot"
    if detail.type == "tab":
        return "mounting tabs"
    if detail.type == "through_hole":
        return "a through hole"
    if detail.type == "opening":
        return "an opening"
    return detail.type.replace("_", " ")


def _extract_dimension_hints(request_text: str, object_type: str) -> dict[str, object]:
    text = request_text.lower()
    dimensions: dict[str, float] = {}
    notes: list[str] = []
    warnings: list[str] = []

    labeled_dimensions, labeled_notes, labeled_warnings = _extract_labeled_dimensions(text)
    dimensions.update(labeled_dimensions)
    notes.extend(labeled_notes)
    warnings.extend(labeled_warnings)

    compact_dimensions = _compact_dimension_triplet(text, object_type)
    if compact_dimensions:
        mapped = _compact_dimensions_to_plan_fields(compact_dimensions, object_type)
        for key, value in mapped.items():
            dimensions.setdefault(key, value)
        if mapped:
            notes.append("Mapped compact dimension form to canonical fields.")

    return {
        "dimensions": dimensions,
        "notes": notes,
        "warnings": warnings,
    }


def _extract_labeled_dimensions(request_text: str) -> tuple[dict[str, float], list[str], list[str]]:
    dimensions: dict[str, float] = {}
    notes: list[str] = []
    warnings: list[str] = []
    patterns = (
        ("overall_width_mm", (
            r"(?:overall\s+)?width(?:\s+of)?\s*(\d+(?:\.\d+)?)\s*mm\b",
            r"\b(\d+(?:\.\d+)?)\s*mm\s+wide\b",
            r"\b(\d+(?:\.\d+)?)\s*mm\s+width\b",
        )),
        ("overall_depth_mm", (
            r"(?:overall\s+)?depth(?:\s+of)?\s*(\d+(?:\.\d+)?)\s*mm\b",
            r"\b(\d+(?:\.\d+)?)\s*mm\s+deep\b",
            r"\b(\d+(?:\.\d+)?)\s*mm\s+depth\b",
        )),
        ("overall_height_mm", (
            r"(?:overall\s+)?height(?:\s+of)?\s*(\d+(?:\.\d+)?)\s*mm\b",
            r"\b(\d+(?:\.\d+)?)\s*mm\s+(?:tall|high)\b",
            r"\b(\d+(?:\.\d+)?)\s*mm\s+height\b",
        )),
        ("material_thickness_mm", (
            r"(?:material\s+)?(?:wall\s+)?thickness(?:\s+of)?\s*(\d+(?:\.\d+)?)\s*mm\b",
            r"\b(\d+(?:\.\d+)?)\s*mm\s+thick\b",
            r"\b(\d+(?:\.\d+)?)\s*mm\s+thickness\b",
            r"\b(\d+(?:\.\d+)?)\s*mm\s+walls?\b",
        )),
    )
    for key, key_patterns in patterns:
        matches: list[float] = []
        for pattern in key_patterns:
            for match in re.finditer(pattern, request_text):
                value = next((group for group in match.groups() if group), None)
                if value is not None:
                    matches.append(float(value))
        if matches:
            dimensions[key] = matches[0]
            if any(abs(candidate - matches[0]) > 1e-6 for candidate in matches[1:]):
                warnings.append(f"Conflicting {key.replace('_', ' ')} values were reduced to the clearest match.")
    if dimensions:
        notes.append("Mapped labeled dimension phrases to canonical fields.")
    return dimensions, notes, warnings


def _compact_dimension_triplet(request_text: str, object_type: str) -> tuple[float, float, float] | None:
    text = request_text.lower()
    pattern = r"(\d+(?:\.\d+)?)\s*(?:mm)?\s*(?:x|by)\s*(\d+(?:\.\d+)?)\s*(?:mm)?\s*(?:x|by)\s*(\d+(?:\.\d+)?)\s*(?:mm)?"
    match = re.search(pattern, text)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2)), float(match.group(3))


def _compact_dimensions_to_plan_fields(values: tuple[float, float, float], object_type: str) -> dict[str, float]:
    first, second, third = values
    if object_type == "plate":
        return {
            "overall_width_mm": first,
            "overall_height_mm": second,
            "material_thickness_mm": third,
        }
    return {
        "overall_width_mm": first,
        "overall_depth_mm": second,
        "overall_height_mm": third,
    }


def _clarification_message(missing_info: list[str], object_type: str) -> str:
    readable = [_dimension_key_to_phrase(key) for key in missing_info if key]
    if not readable:
        return f"Need more detail before generating the {object_type.replace('_', ' ')}."
    return f"Provide {', '.join(readable)} before generating the {object_type.replace('_', ' ')}."


def _dimension_key_to_phrase(key: str) -> str:
    if key.endswith("_mm"):
        key = key[:-3]
    return key.replace("_", " ")


def _build_interpretation_summary(plan: GeomancerPlan, status: str) -> str:
    object_type = plan.intent.object_type or "request"
    if status == "ready":
        parts = [f"Interpreted {object_type}"]
        if plan.construction_mode == "hybrid":
            parts.append("hybrid mode")
            if plan.composition:
                parts.append(f"{len(plan.composition)} base item(s)")
            if plan.components:
                parts.append(f"{len(plan.components)} base component(s)")
            if plan.hybrid_details:
                parts.append(f"{len(plan.hybrid_details)} hybrid detail(s)")
        elif plan.construction_mode == "compositional":
            parts.append("compositional mode")
            if plan.composition:
                parts.append(f"{len(plan.composition)} composition item(s)")
        if plan.assumptions:
            parts.append(f"{len(plan.assumptions)} assumption(s)")
        if plan.warnings:
            parts.append(f"{len(plan.warnings)} warning(s)")
        return ", ".join(parts) + "."
    if status == "clarify":
        if plan.construction_mode == "hybrid":
            return f"Interpreted {object_type} in hybrid mode but needs clarification: {', '.join(plan.missing_info[:3])}."
        return f"Interpreted {object_type} but needs clarification: {', '.join(plan.missing_info[:3])}."
    return f"Could not interpret {object_type} into a supported plan."


def _build_style_summary(plan: GeomancerPlan, status: str) -> str:
    style = getattr(plan, "style", None)
    profile = str(getattr(style, "style_profile", "") or (style.get("style_profile") if isinstance(style, dict) else "") or "minimal").strip() or "minimal"
    shape_language = str(getattr(style, "shape_language", "") or (style.get("shape_language") if isinstance(style, dict) else "") or "prismatic").strip() or "prismatic"
    edge_treatment = str(getattr(style, "edge_treatment", "") or (style.get("edge_treatment") if isinstance(style, dict) else "") or "soft").strip() or "soft"
    detail_density = str(getattr(style, "detail_density", "") or (style.get("detail_density") if isinstance(style, dict) else "") or "low").strip() or "low"
    accent_profile = str(getattr(style, "accent_profile", "") or (style.get("accent_profile") if isinstance(style, dict) else "") or "none").strip() or "none"
    if status == "unsupported":
        return f"Style profile {profile.replace('_', ' ')} was not applied."
    if status == "clarify":
        return f"Style profile {profile.replace('_', ' ')} selected with {shape_language.replace('_', ' ')} forms."
    return (
        f"Applied {profile.replace('_', ' ')} style with {shape_language.replace('_', ' ')} forms, "
        f"{edge_treatment} edges, {detail_density} detail density, and {accent_profile.replace('_', ' ')} accents."
    )


def _collect_editable_params(plan: GeomancerPlan) -> list[dict[str, object]]:
    editable: list[dict[str, object]] = []
    dims = plan.dimensions or {}
    style = getattr(plan, "style", None)
    style_profile = str(getattr(style, "style_profile", "") or (style.get("style_profile") if isinstance(style, dict) else "") or "minimal").strip() or "minimal"
    style_options = sorted(ALLOWED_STYLE_PROFILES)
    dimension_fields = (
        ("overall_width_mm", "Width"),
        ("overall_depth_mm", "Depth"),
        ("overall_height_mm", "Height"),
        ("material_thickness_mm", "Material thickness"),
    )
    for key, label in dimension_fields:
        if key in dims or plan.construction_mode in {"constraint", "hybrid"}:
            editable.append({
                "group": "Dimensions",
                "key": f"dimensions.{key}",
                "label": label,
                "type": "number",
                "value": dims.get(key, ""),
                "step": 1.0,
                "min": 0.1,
                "max": 1000.0,
            })

    editable.append({
        "group": "Style",
        "key": "style.style_profile",
        "label": "Style profile",
        "type": "select",
        "value": style_profile,
        "options": style_options,
    })
    if hasattr(style, "detail_density") or isinstance(style, dict):
        editable.append({
            "group": "Style",
            "key": "style.detail_density",
            "label": "Detail density",
            "type": "select",
            "value": str(getattr(style, "detail_density", "") or (style.get("detail_density") if isinstance(style, dict) else "") or "low"),
            "options": ["low", "medium", "high"],
        })
    if hasattr(style, "edge_treatment") or isinstance(style, dict):
        editable.append({
            "group": "Style",
            "key": "style.edge_treatment",
            "label": "Edge treatment",
            "type": "select",
            "value": str(getattr(style, "edge_treatment", "") or (style.get("edge_treatment") if isinstance(style, dict) else "") or "soft"),
            "options": ["soft", "hard", "rounded", "faceted"],
        })

    component_map = {component.type: component for component in plan.components}
    feature_controls = {
        "hole_pattern": [("diameter_mm", "Hole diameter"), ("count", "Hole count")],
        "mount_hole": [("diameter_mm", "Hole diameter")],
        "through_hole": [("diameter_mm", "Through-hole diameter")],
        "slot": [("width_mm", "Slot width"), ("height_mm", "Slot height"), ("depth_mm", "Slot depth")],
        "opening": [("width_mm", "Opening width"), ("height_mm", "Opening height"), ("depth_mm", "Opening depth")],
        "retaining_lip": [("height_mm", "Lip height")],
        "shell": [("wall_thickness_mm", "Wall thickness")],
        "angled_support": [("height_mm", "Support height"), ("angle_deg", "Support angle"), ("cradle_depth_mm", "Cradle depth")],
        "tab": [("width_mm", "Tab width"), ("height_mm", "Tab height"), ("thickness_mm", "Tab thickness")],
    }
    for component_type, controls in feature_controls.items():
        component = component_map.get(component_type)
        if not component:
            continue
        for key, label in controls:
            if key in component.params:
                editable.append({
                    "group": "Features",
                    "key": f"components.{component.id or component.type}.{key}",
                    "label": label,
                    "type": "number",
                    "value": component.params.get(key, ""),
                    "step": 1.0,
                    "min": 0.0,
                    "max": 1000.0,
                })

    if plan.hybrid_details:
        for detail in plan.hybrid_details:
            editable.append({
                "group": "Details",
                "key": f"hybrid_details.{detail.id or detail.type}.enabled",
                "label": _hybrid_detail_phrase(detail).capitalize(),
                "type": "toggle",
                "value": True,
            })
    return editable


def _build_decision_summary(
    status: str,
    *,
    object_type: str = "",
    construction_mode: str = "",
    missing_info: list[str] | None = None,
    assumptions: list[str] | None = None,
    warnings: list[str] | None = None,
    recipe_name: str = "",
    implementation_id: str = "",
    validation_summary: str = "",
    recipe_summary: str = "",
    execution_summary: str = "",
    preview_success: bool | None = None,
) -> str:
    missing_info = list(missing_info or [])
    assumptions = list(assumptions or [])
    warnings = list(warnings or [])
    if status == "ready":
        parts = [f"Ready {object_type or 'request'}"]
        if construction_mode == "hybrid":
            parts.append("hybrid build")
        elif object_type and object_type in COMPOSITIONAL_OBJECT_TYPES:
            parts.append("compositional build")
        if recipe_name:
            parts.append(f"recipe {recipe_name}")
        if implementation_id:
            parts.append(f"implementation {implementation_id}")
        if preview_success is False:
            parts.append("preview export needs attention")
        return ", ".join(parts) + "."
    if status == "clarify":
        if construction_mode == "hybrid":
            return f"Hybrid clarification needed: {', '.join(missing_info[:3])}." if missing_info else "Hybrid clarification needed before generation."
        return f"Clarification needed: {', '.join(missing_info[:3])}." if missing_info else "Clarification needed before generation."
    if status == "unsupported":
        return "Unsupported request; no deterministic plan was selected."
    if validation_summary:
        return validation_summary
    if recipe_summary:
        return recipe_summary
    if execution_summary:
        return execution_summary
    if assumptions:
        return f"Assumptions recorded: {', '.join(assumptions[:3])}."
    if warnings:
        return f"Warnings recorded: {', '.join(warnings[:3])}."
    return "Generation could not proceed."


def _save_state(
    *,
    generation_id: str,
    user_request: str,
    family: str,
    plan: dict,
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
    interpretation_summary: str,
    decision_summary: str,
    style_summary: str,
    missing_info: list[str],
    assumptions: list[str],
    warnings: list[str],
    current_saved_model_id: str = "",
    current_saved_model_editable: bool = False,
    last_opened_model_id: str = "",
    reopen_source: str = "",
    reopened_plan_summary: str = "",
    current_editable_params: list[dict] | None = None,
    last_editable_params: list[dict] | None = None,
    last_regeneration_source: str = "",
    edited_plan_summary: str = "",
    preview_model_path: str,
    preview_asset_version: str,
    preview_export_status: str,
    preview_export_message: str,
    saved_model_entry: dict,
    stl_export_path: str,
    stl_export_status: str,
    stl_export_message: str,
    stl_source_model_path: str,
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
    state["last_generation_family"] = family
    state["last_interpretation_summary"] = interpretation_summary
    state["last_decision_summary"] = decision_summary
    state["last_style_summary"] = style_summary
    state["current_saved_model_id"] = current_saved_model_id
    state["current_saved_model_editable"] = bool(current_saved_model_editable)
    state["last_opened_model_id"] = last_opened_model_id
    state["reopen_source"] = reopen_source
    state["reopened_plan_summary"] = reopened_plan_summary
    state["current_editable_params"] = list(current_editable_params or [])
    state["last_editable_params"] = list(last_editable_params or current_editable_params or [])
    state["last_regeneration_source"] = last_regeneration_source
    state["edited_plan_summary"] = edited_plan_summary
    state["last_missing_info"] = list(missing_info)
    state["last_assumptions"] = list(assumptions)
    state["last_warnings"] = list(warnings)
    state["last_validation_summary"] = validation.get("summary", "")
    state["last_plan"] = plan
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
    state["last_stl_export_path"] = stl_export_path
    state["last_stl_export_status"] = stl_export_status
    state["last_stl_export_message"] = stl_export_message
    state["last_stl_source_model_path"] = stl_source_model_path
    save_state(state)


def _save_nonready_state(
    generation_id: str,
    user_request: str,
    status: str,
    raw_status: str,
    message: str,
    classification: dict,
    plan: dict,
    validation: dict,
    recipe: dict,
    recipe_summary: str,
    interpretation_summary: str,
    decision_summary: str,
    style_summary: str,
    missing_info: list[str],
    assumptions: list[str],
    warnings: list[str],
    current_saved_model_id: str = "",
    current_saved_model_editable: bool = False,
    last_opened_model_id: str = "",
    reopen_source: str = "",
    reopened_plan_summary: str = "",
    current_editable_params: list[dict] | None = None,
    last_editable_params: list[dict] | None = None,
    last_regeneration_source: str = "",
    edited_plan_summary: str = "",
    stl_export_path: str = "",
    stl_export_status: str = "not_requested",
    stl_export_message: str = "",
    stl_source_model_path: str = "",
) -> None:
    state = load_state()
    state["last_user_request"] = user_request
    state["last_generation_id"] = generation_id
    state["last_generated_script_path"] = str(GENERATED_SCRIPT_PATH)
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
    state["last_interpretation_summary"] = interpretation_summary
    state["last_decision_summary"] = decision_summary
    state["last_style_summary"] = style_summary
    state["current_saved_model_id"] = current_saved_model_id
    state["current_saved_model_editable"] = bool(current_saved_model_editable)
    state["last_opened_model_id"] = last_opened_model_id
    state["reopen_source"] = reopen_source
    state["reopened_plan_summary"] = reopened_plan_summary
    state["current_editable_params"] = list(current_editable_params or [])
    state["last_editable_params"] = list(last_editable_params or current_editable_params or [])
    state["last_regeneration_source"] = last_regeneration_source
    state["edited_plan_summary"] = edited_plan_summary
    state["last_missing_info"] = list(missing_info)
    state["last_assumptions"] = list(assumptions)
    state["last_warnings"] = list(warnings)
    state["last_classification"] = classification
    state["last_validation_summary"] = validation.get("summary") or message
    state["last_plan"] = plan
    state["last_recipe"] = recipe
    state["last_recipe_summary"] = recipe_summary
    state["last_execution_path"] = ""
    state["last_execution_summary"] = ""
    state["last_generation_path"] = ""
    state["last_generation_route"] = ""
    state["last_generation_fallback_reason"] = ""
    state["last_implementation_id"] = ""
    state["last_execution_recipe"] = ""
    state["last_validation"] = validation
    state["last_saved_model_entry"] = {}
    state["last_stl_export_path"] = stl_export_path
    state["last_stl_export_status"] = stl_export_status
    state["last_stl_export_message"] = stl_export_message
    state["last_stl_source_model_path"] = stl_source_model_path
    save_state(state)


def _reset_generation_context(*, user_request: str, generation_id: str) -> None:
    state = load_state()
    state["last_user_request"] = user_request
    state["last_generation_id"] = generation_id
    state["last_generated_script_path"] = str(GENERATED_SCRIPT_PATH)
    state["last_generation_family"] = ""
    state["last_interpretation_summary"] = ""
    state["last_decision_summary"] = ""
    state["last_style_summary"] = ""
    state["current_saved_model_id"] = ""
    state["current_saved_model_editable"] = False
    state["last_opened_model_id"] = ""
    state["reopen_source"] = ""
    state["reopened_plan_summary"] = ""
    state["current_editable_params"] = []
    state["last_editable_params"] = []
    state["last_regeneration_source"] = ""
    state["edited_plan_summary"] = ""
    state["last_missing_info"] = []
    state["last_assumptions"] = []
    state["last_warnings"] = []
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
    state["last_stl_export_path"] = ""
    state["last_stl_export_status"] = ""
    state["last_stl_export_message"] = ""
    state["last_stl_source_model_path"] = ""
    save_state(state)


def _build_nonready_result(
    *,
    generation_id: str,
    user_request: str,
    raw_status: str,
    message: str,
    classification: dict,
    plan: dict | None = None,
    validation: dict | None = None,
    recipe: dict | None = None,
    recipe_summary: str = "",
    interpretation_summary: str = "",
    decision_summary: str = "",
    style_summary: str = "",
    missing_info: list[str] | None = None,
    assumptions: list[str] | None = None,
    warnings: list[str] | None = None,
    current_saved_model_id: str = "",
    current_saved_model_editable: bool = False,
    last_opened_model_id: str = "",
    reopen_source: str = "",
    reopened_plan_summary: str = "",
    editable_params: list[dict] | None = None,
    current_editable_params: list[dict] | None = None,
    last_editable_params: list[dict] | None = None,
    last_regeneration_source: str = "",
    edited_plan_summary: str = "",
    stl_export_path: str = "",
    stl_export_status: str = "not_requested",
    stl_export_message: str = "",
    stl_source_model_path: str = "",
) -> dict:
    status = _normalize_terminal_status(raw_status)
    safe_plan = _plan_to_dict(plan)
    safe_validation = validation or {}
    safe_recipe = recipe or {}
    safe_missing_info = list(missing_info or safe_plan.get("missing_info") or safe_validation.get("clarification_needed") or [])
    safe_assumptions = list(assumptions or safe_plan.get("assumptions") or [])
    safe_warnings = list(warnings or safe_plan.get("warnings") or safe_validation.get("warnings") or [])
    safe_editable_params = list(editable_params or current_editable_params or safe_plan.get("editable_params") or [])
    safe_current_editable_params = list(current_editable_params or safe_editable_params)
    safe_last_editable_params = list(last_editable_params or safe_current_editable_params)
    validation_summary = safe_validation.get("summary", "")
    if not decision_summary:
        decision_summary = _build_decision_summary(
            raw_status,
            construction_mode=safe_plan.get("construction_mode", ""),
            missing_info=safe_missing_info,
            assumptions=safe_assumptions,
            warnings=safe_warnings,
            validation_summary=validation_summary,
            recipe_summary=recipe_summary,
        )
    if not interpretation_summary:
        interpretation_summary = "Unsupported request." if raw_status == "unsupported" else "Clarification required."
    if not style_summary and safe_plan:
        style_summary = _build_style_summary(_dict_to_plan(safe_plan), status)
    _save_nonready_state(
        generation_id=generation_id,
        user_request=user_request,
        status=status,
        raw_status=raw_status,
        message=message,
        classification=classification,
        plan=safe_plan,
        validation=safe_validation,
        recipe=safe_recipe,
        recipe_summary=recipe_summary,
        interpretation_summary=interpretation_summary,
        decision_summary=decision_summary,
        style_summary=style_summary,
        current_editable_params=safe_current_editable_params,
        last_editable_params=safe_last_editable_params,
        last_regeneration_source=last_regeneration_source,
        edited_plan_summary=edited_plan_summary,
        current_saved_model_id=current_saved_model_id,
        current_saved_model_editable=current_saved_model_editable,
        last_opened_model_id=last_opened_model_id,
        reopen_source=reopen_source,
        reopened_plan_summary=reopened_plan_summary,
        missing_info=safe_missing_info,
        assumptions=safe_assumptions,
        warnings=safe_warnings,
        stl_export_path=stl_export_path,
        stl_export_status=stl_export_status,
        stl_export_message=stl_export_message,
        stl_source_model_path=stl_source_model_path,
    )
    return {
        "generation_id": generation_id,
        "request_text": user_request,
        "status": status,
        "raw_status": raw_status,
        "is_terminal": True,
        "message": message,
        "plan": safe_plan,
        "validation": safe_validation,
        "recipe": safe_recipe,
        "recipe_summary": recipe_summary,
        "validation_summary": validation_summary,
        "execution_path": "",
        "execution_summary": "",
        "generation_path": "",
        "generation_route": "",
        "generation_fallback_reason": "",
        "implementation_id": "",
        "execution_recipe": "",
        "classification": classification,
        "interpretation_summary": interpretation_summary,
        "decision_summary": decision_summary,
        "style_summary": style_summary,
        "missing_info": safe_missing_info,
        "assumptions": safe_assumptions,
        "warnings": safe_warnings,
        "current_saved_model_id": current_saved_model_id,
        "current_saved_model_editable": current_saved_model_editable,
        "last_opened_model_id": last_opened_model_id,
        "reopen_source": reopen_source,
        "reopened_plan_summary": reopened_plan_summary,
        "editable_params": safe_editable_params,
        "current_editable_params": safe_current_editable_params,
        "last_editable_params": safe_last_editable_params,
        "last_regeneration_source": last_regeneration_source,
        "edited_plan_summary": edited_plan_summary,
        "preview_model_path": "",
        "preview_model_url": "",
        "preview_asset_version": "",
        "preview_export_status": "not_requested",
        "preview_export_message": message,
        "final_model_path": "",
        "final_model_url": "",
        "output_source": "",
        "stl_export_path": stl_export_path,
        "stl_export_status": stl_export_status,
        "stl_export_message": stl_export_message,
        "stl_source_model_path": stl_source_model_path,
        "saved_model_entry": {},
        "supported_families": list(SUPPORTED_FAMILY_LABELS),
    }


def _plan_to_dict(plan: dict | GeomancerPlan | object) -> dict:
    if isinstance(plan, GeomancerPlan):
        return plan.to_dict()
    if hasattr(plan, "to_dict"):
        try:
            payload = plan.to_dict()
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
    if isinstance(plan, dict):
        return dict(plan)
    return {}


def _dict_to_plan(plan: dict | GeomancerPlan | object) -> GeomancerPlan:
    if isinstance(plan, GeomancerPlan):
        return plan
    payload = _plan_to_dict(plan)
    return GeomancerPlan(
        schema_version=str(payload.get("schema_version") or "1.0"),
        request_text=str(payload.get("request_text") or ""),
        intent=GeomancerIntent(
            object_type=str((payload.get("intent") or {}).get("object_type") or ""),
            object_label=str((payload.get("intent") or {}).get("object_label") or ""),
            use_case=str((payload.get("intent") or {}).get("use_case") or ""),
            printable=bool((payload.get("intent") or {}).get("printable", True)),
            editable_in_blender=bool((payload.get("intent") or {}).get("editable_in_blender", True)),
        ),
        construction_mode=str(payload.get("construction_mode") or "constraint"),
        units=str(payload.get("units") or "mm"),
        dimensions=dict(payload.get("dimensions") or {}),
        components=[GeomancerComponent(id=str(item.get("id") or ""), type=str(item.get("type") or ""), params=dict(item.get("params") or {})) for item in payload.get("components", [])],
        composition=[GeomancerCompositionItem(id=str(item.get("id") or ""), type=str(item.get("type") or ""), operation=str(item.get("operation") or "union"), params=dict(item.get("params") or {}), position=list(item.get("position") or []), rotation_deg=list(item.get("rotation_deg") or [])) for item in payload.get("composition", [])],
        hybrid_details=[GeomancerHybridDetail(id=str(item.get("id") or ""), source_mode=str(item.get("source_mode") or ""), type=str(item.get("type") or ""), operation=str(item.get("operation") or "union"), params=dict(item.get("params") or {}), position=list(item.get("position") or []), rotation_deg=list(item.get("rotation_deg") or []), target=str(item.get("target") or "")) for item in payload.get("hybrid_details", [])],
        constraints=dict(payload.get("constraints") or {}),
        style=_coerce_style(payload.get("style") or {}),
        assumptions=list(payload.get("assumptions") or []),
        warnings=list(payload.get("warnings") or []),
        missing_info=list(payload.get("missing_info") or []),
        notes=list(payload.get("notes") or []),
    )


def _coerce_style(style: object) -> GeomancerStyle:
    if isinstance(style, GeomancerStyle):
        return style
    payload = dict(style or {}) if isinstance(style, dict) else {}
    profile = str(payload.get("style_profile") or "minimal").strip() or "minimal"
    defaults = STYLE_DEFAULTS_BY_PROFILE.get(profile, STYLE_DEFAULTS_BY_PROFILE["minimal"])
    return GeomancerStyle(
        style_profile=profile,
        shape_language=str(payload.get("shape_language") or defaults["shape_language"]),
        edge_treatment=str(payload.get("edge_treatment") or defaults["edge_treatment"]),
        detail_density=str(payload.get("detail_density") or defaults["detail_density"]),
        accent_profile=str(payload.get("accent_profile") or defaults["accent_profile"]),
    )


def _infer_object_type(request_text: str) -> str:
    text = request_text.lower()
    if "phone stand" in text:
        return "phone_stand"
    if "primitive assembly" in text:
        return "primitive_assembly"
    if "low poly crate" in text or "crate" in text or "boxy prop" in text:
        return "crate"
    if "barrel" in text:
        return "barrel"
    if "canister" in text or "capsule" in text:
        return "canister"
    if "pedestal" in text or "block prop" in text:
        return "pedestal"
    if "wall hook" in text or "hook mount" in text or "hook" in text:
        return "hook_mount"
    if "bracket" in text:
        return "bracket"
    if "tray" in text or "parts box" in text:
        return "tray"
    if "enclosure" in text:
        return "enclosure"
    if "panel plate" in text or re.search(r"\bplate\b", text):
        return "plate"
    if "standoff" in text or "spacer" in text:
        return "standoff"
    if "adapter" in text:
        return "adapter"
    return ""


def _infer_compositional_object_type(request_text: str) -> str:
    text = request_text.lower()
    if any(term in text for term in ("dragon", "sculpture", "statue", "figurine", "character", "organic", "creature", "helmet", "shoe", "chair")):
        return ""
    if "primitive assembly" in text:
        return "primitive_assembly"
    if "crate" in text or "boxy prop" in text or "simple prop" in text:
        return "crate"
    if "barrel" in text:
        return "barrel"
    if "canister" in text or "capsule" in text:
        return "canister"
    if "pedestal" in text or "block prop" in text:
        return "pedestal"
    return ""


def _extract_natural_thickness(request_text: str) -> float | None:
    text = request_text.lower()
    patterns = (
        r"(?:material\s+)?(?:wall\s+)?thickness(?:\s+of)?\s*(\d+(?:\.\d+)?)\s*mm\b",
        r"\b(\d+(?:\.\d+)?)\s*mm\s+thick\b",
        r"\b(\d+(?:\.\d+)?)\s*mm\s+thickness\b",
        r"\b(\d+(?:\.\d+)?)\s*mm\s+walls?\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
    return None


def _extract_hole_count(request_text: str) -> int:
    match = re.search(r"(\d+)\s*(?:x\s*)?holes?\b", request_text.lower())
    if match:
        return int(match.group(1))
    for word, value in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\s+[\w-]*\s*holes?\b", request_text.lower()):
            return value
    return 0


def _extract_hole_diameter(request_text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*mm\s+holes?\b", request_text.lower())
    return float(match.group(1)) if match else None


def _coerce_float(value: object, default: float) -> float:
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return default


def _default_thickness(object_type: str) -> float:
    return {
        "phone_stand": 5.0,
        "bracket": 6.0,
        "tray": 3.0,
        "enclosure": 3.0,
        "plate": 4.0,
        "standoff": 4.0,
        "hook_mount": 6.0,
        "adapter": 4.0,
        "crate": 4.0,
        "barrel": 3.0,
        "canister": 3.0,
        "pedestal": 5.0,
        "primitive_assembly": 4.0,
    }[object_type]


def _default_use_case(object_type: str) -> str:
    return {
        "phone_stand": "hold_phone",
        "bracket": "mount_support",
        "tray": "hold_parts",
        "enclosure": "protect_components",
        "plate": "mount_surface",
        "standoff": "space_components",
        "hook_mount": "hang_items",
        "adapter": "join_sizes",
        "crate": "store_items",
        "barrel": "store_items",
        "canister": "store_items",
        "pedestal": "display_object",
        "primitive_assembly": "compose_primitives",
    }[object_type]


def _family_label_from_plan(plan: GeomancerPlan) -> str:
    label = plan.intent.object_label.strip()
    if label:
        return label
    return plan.intent.object_type.replace("_", " ")


def _required_dimension_keys_for_object_type(object_type: str) -> list[str]:
    return {
        "phone_stand": ["overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"],
        "bracket": ["overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"],
        "tray": ["overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"],
        "enclosure": ["overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"],
        "plate": ["overall_width_mm", "overall_height_mm", "material_thickness_mm"],
        "standoff": ["overall_width_mm", "overall_height_mm"],
        "hook_mount": ["overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"],
        "adapter": ["overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"],
        "primitive_assembly": ["overall_width_mm", "overall_depth_mm", "overall_height_mm"],
        "crate": ["overall_width_mm", "overall_depth_mm", "overall_height_mm"],
        "barrel": ["overall_width_mm", "overall_depth_mm", "overall_height_mm"],
        "canister": ["overall_width_mm", "overall_depth_mm", "overall_height_mm"],
        "pedestal": ["overall_width_mm", "overall_depth_mm", "overall_height_mm"],
    }.get(object_type, [])


def _unsupported_request_reason(request_text: str) -> str:
    text = request_text.lower()
    unsupported_terms = (
        "dragon",
        "sculpture",
        "statue",
        "figurine",
        "character",
        "organic",
        "creature",
        "helmet",
        "shoe",
        "chair",
    )
    if any(term in text for term in unsupported_terms):
        return "This request reads as an organic or sculptural model and is outside the current deterministic plan coverage."
    if "life size" in text or "full size" in text:
        return "Life-size requests are outside the current deterministic printable-part scope."
    return ""


def _normalize_terminal_status(raw_status: str) -> str:
    if raw_status == "ready":
        return "ready"
    if raw_status == "unsupported":
        return "unsupported"
    if raw_status in {"clarify", "validation_failed", "invalid"}:
        return "validation_failed"
    return "error"


def _build_generation_id() -> str:
    return f"gen-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"


def _generation_preview_path(generation_id: str) -> Path:
    return PREVIEWS_DIR / f"generated_preview_{generation_id}.glb"
