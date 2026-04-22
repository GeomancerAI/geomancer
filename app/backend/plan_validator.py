"""Validation and normalization for Geomancer Plan Schema v1."""

from __future__ import annotations

from copy import deepcopy

from .plan_schema import (
    ALLOWED_COMPONENT_TYPES,
    ALLOWED_COMPOSITION_ITEM_TYPES,
    ALLOWED_CONSTRUCTION_MODES,
    ALLOWED_OBJECT_TYPES,
    GeomancerComponent,
    GeomancerCompositionItem,
    GeomancerHybridDetail,
    GeomancerIntent,
    GeomancerPlan,
    GeomancerStyle,
    ALLOWED_STYLE_PROFILES,
    STYLE_COMPATIBILITY_BY_OBJECT_TYPE,
    STYLE_DEFAULTS_BY_PROFILE,
    GeomancerPlanValidationResult,
    PLAN_SCHEMA_VERSION,
)


SAFE_MIN_PRINT_THICKNESS_MM = 2.4
MAX_PRINTABLE_DIMENSION_MM = 1000.0
MIN_OVERALL_DIMENSION_MM = 8.0
REQUIRED_DIMENSIONS_BY_OBJECT_TYPE = {
    "phone_stand": ("overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"),
    "bracket": ("overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"),
    "tray": ("overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"),
    "enclosure": ("overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"),
    "plate": ("overall_width_mm", "overall_height_mm", "material_thickness_mm"),
    "standoff": ("overall_width_mm", "overall_height_mm"),
    "hook_mount": ("overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"),
    "adapter": ("overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"),
    "primitive_assembly": ("overall_width_mm", "overall_depth_mm", "overall_height_mm"),
    "crate": ("overall_width_mm", "overall_depth_mm", "overall_height_mm"),
    "barrel": ("overall_width_mm", "overall_depth_mm", "overall_height_mm"),
    "canister": ("overall_width_mm", "overall_depth_mm", "overall_height_mm"),
    "pedestal": ("overall_width_mm", "overall_depth_mm", "overall_height_mm"),
}
COMPOSITIONAL_OBJECT_TYPES = {"primitive_assembly", "crate", "barrel", "canister", "pedestal"}
HYBRID_FEATURE_COMPONENT_TYPES = {"hole_pattern", "mount_hole", "through_hole", "slot", "tab", "opening"}


def validate_plan(plan: GeomancerPlan | dict) -> GeomancerPlanValidationResult:
    normalized = _coerce_plan(plan)
    warnings = list(normalized.warnings)
    assumptions = list(normalized.assumptions)
    clarification_needed: list[str] = []
    errors: list[str] = []

    normalized.schema_version = PLAN_SCHEMA_VERSION
    normalized.units = str(normalized.units or "mm").lower()
    if normalized.units != "mm":
        warnings.append(f"Units '{normalized.units}' were normalized to mm.")
        normalized.units = "mm"
    normalized.construction_mode = str(normalized.construction_mode or "constraint").lower()
    if normalized.construction_mode not in ALLOWED_CONSTRUCTION_MODES:
        errors.append(f"Unsupported construction mode: {normalized.construction_mode}.")
    hybrid_mode = normalized.construction_mode == "hybrid"
    base_mode = (
        "compositional"
        if hybrid_mode and normalized.intent.object_type.strip() in COMPOSITIONAL_OBJECT_TYPES
        else "constraint"
        if hybrid_mode
        else normalized.construction_mode
    )

    constraints = dict(normalized.constraints)
    if "minimum_wall_thickness_mm" not in constraints or constraints.get("minimum_wall_thickness_mm") in (None, ""):
        assumptions.append(f"Assumed {SAFE_MIN_PRINT_THICKNESS_MM:g} mm minimum wall thickness.")
    constraints.setdefault("minimum_wall_thickness_mm", SAFE_MIN_PRINT_THICKNESS_MM)
    constraints["minimum_wall_thickness_mm"] = max(
        _coerce_float(constraints.get("minimum_wall_thickness_mm"), SAFE_MIN_PRINT_THICKNESS_MM),
        SAFE_MIN_PRINT_THICKNESS_MM,
    )
    if normalized.intent.printable and "flat_bottom" not in constraints:
        assumptions.append("Assumed flat bottom for a printable part.")
        constraints["flat_bottom"] = True
    if "max_overhang_deg" in constraints and constraints["max_overhang_deg"] not in ("", None):
        overhang = _coerce_float(constraints["max_overhang_deg"], 55.0)
        clamped = min(max(overhang, 0.0), 80.0)
        if clamped != overhang:
            warnings.append("constraints.max_overhang_deg was clamped to a sane printable range.")
        constraints["max_overhang_deg"] = clamped
    normalized.constraints = constraints

    object_type = normalized.intent.object_type.strip()
    if not object_type:
        errors.append("Plan intent.object_type is required.")
    elif object_type not in ALLOWED_OBJECT_TYPES:
        errors.append(f"Unsupported object type: {object_type}.")
    elif object_type in COMPOSITIONAL_OBJECT_TYPES and base_mode != "compositional":
        errors.append(f"Object type '{object_type}' must use compositional construction mode.")
    else:
        _validate_style(normalized, object_type, base_mode, warnings, assumptions, clarification_needed)

    normalized.dimensions = {
        key: _coerce_scalar(value)
        for key, value in dict(normalized.dimensions).items()
    }
    normalized.hybrid_details = [
        item if isinstance(item, GeomancerHybridDetail) else _coerce_hybrid_detail(item)
        for item in normalized.hybrid_details
    ]
    if base_mode == "compositional":
        normalized.composition = [
            item if isinstance(item, GeomancerCompositionItem) else _coerce_composition_item(item)
            for item in normalized.composition
        ]
        if not normalized.composition:
            clarification_needed.append("Add at least one composition item for the compositional template.")
        else:
            _infer_compositional_dimensions(normalized, assumptions, warnings)
            _validate_composition_items(normalized, errors, warnings)
            _validate_composition_bounds(normalized, errors, warnings)
    elif base_mode == "constraint":
        required_dimensions = REQUIRED_DIMENSIONS_BY_OBJECT_TYPE.get(object_type, ())
        for key in required_dimensions:
            if normalized.dimensions.get(key) in (None, ""):
                clarification_needed.append(f"Provide {key.replace('_mm', '').replace('_', ' ')} in mm.")
                if key not in normalized.missing_info:
                    normalized.missing_info.append(key)
        if "material_thickness_mm" in normalized.dimensions:
            thickness = _coerce_float(normalized.dimensions["material_thickness_mm"], 0.0)
            if thickness < SAFE_MIN_PRINT_THICKNESS_MM:
                normalized.dimensions["material_thickness_mm"] = SAFE_MIN_PRINT_THICKNESS_MM
                warnings.append("dimensions.material_thickness_mm was clamped to the safe printable minimum.")
            else:
                normalized.dimensions["material_thickness_mm"] = thickness
        _validate_overall_dimensions(normalized, errors, clarification_needed)

        normalized_components: list[GeomancerComponent] = []
        for component in normalized.components:
            item = component if isinstance(component, GeomancerComponent) else _coerce_component(component)
            if item.type not in ALLOWED_COMPONENT_TYPES:
                errors.append(f"Unsupported component type: {item.type or 'missing'}.")
            item.params = {key: _coerce_scalar(value) for key, value in dict(item.params).items()}
            for key in ("thickness_mm", "wall_thickness_mm"):
                if key in item.params:
                    thickness = _coerce_float(item.params[key], 0.0)
                    if thickness < SAFE_MIN_PRINT_THICKNESS_MM:
                        item.params[key] = SAFE_MIN_PRINT_THICKNESS_MM
                        warnings.append(f"Component '{item.id or item.type}' {key} was clamped to the safe printable minimum.")
                    else:
                        item.params[key] = thickness
            normalized_components.append(item)
        normalized.components = normalized_components
        _validate_component_realism(normalized, errors, warnings, clarification_needed)

        if normalized.intent.printable and not normalized.components:
            clarification_needed.append("Add at least one component for a printable object.")
    else:
        errors.append(f"Unsupported construction mode: {normalized.construction_mode}.")

    if hybrid_mode:
        _validate_hybrid_details(normalized, errors, warnings, clarification_needed)

    normalized.assumptions = _clean_list(assumptions)
    normalized.warnings = _clean_list(warnings)
    normalized.notes = _clean_list(normalized.notes)
    normalized.missing_info = _clean_list(normalized.missing_info)

    if errors:
        status = "invalid"
        summary = "Plan validation failed."
    elif clarification_needed:
        status = "clarify"
        summary = "Plan needs clarification before deterministic generation."
    else:
        status = "ready"
        if hybrid_mode:
            summary = (
                f"Validated {object_type} hybrid plan with "
                f"{len(normalized.components)} components, {len(normalized.composition)} composition items, "
                f"and {len(normalized.hybrid_details)} hybrid details."
            )
        elif base_mode == "compositional":
            summary = f"Validated {object_type} plan with {len(normalized.composition)} composition items."
        else:
            summary = f"Validated {object_type} plan with {len(normalized.components)} components."

    return GeomancerPlanValidationResult(
        status=status,
        normalized_plan=normalized,
        warnings=list(normalized.warnings),
        clarification_needed=clarification_needed,
        errors=errors,
        summary=summary,
    )


def _coerce_plan(plan: GeomancerPlan | dict) -> GeomancerPlan:
    if isinstance(plan, GeomancerPlan):
        return deepcopy(plan)
    payload = dict(plan or {})
    intent = _coerce_intent(payload.get("intent", {}))
    components = [_coerce_component(item) for item in payload.get("components", [])]
    return GeomancerPlan(
        schema_version=str(payload.get("schema_version") or PLAN_SCHEMA_VERSION),
        request_text=str(payload.get("request_text") or ""),
        intent=intent,
        construction_mode=str(payload.get("construction_mode") or "constraint"),
        units=str(payload.get("units") or "mm"),
        dimensions=dict(payload.get("dimensions") or {}),
        components=components,
        composition=[_coerce_composition_item(item) for item in payload.get("composition", [])],
        hybrid_details=[_coerce_hybrid_detail(item) for item in payload.get("hybrid_details", [])],
        constraints=dict(payload.get("constraints") or {}),
        style=_coerce_style(payload.get("style") or {}),
        assumptions=list(payload.get("assumptions") or []),
        warnings=list(payload.get("warnings") or []),
        missing_info=list(payload.get("missing_info") or []),
        notes=list(payload.get("notes") or []),
    )


def _coerce_intent(intent: GeomancerIntent | dict) -> GeomancerIntent:
    if isinstance(intent, GeomancerIntent):
        return deepcopy(intent)
    payload = dict(intent or {})
    return GeomancerIntent(
        object_type=str(payload.get("object_type") or ""),
        object_label=str(payload.get("object_label") or ""),
        use_case=str(payload.get("use_case") or ""),
        printable=bool(payload.get("printable", True)),
        editable_in_blender=bool(payload.get("editable_in_blender", True)),
    )


def _coerce_component(component: GeomancerComponent | dict) -> GeomancerComponent:
    if isinstance(component, GeomancerComponent):
        return deepcopy(component)
    payload = dict(component or {})
    return GeomancerComponent(
        id=str(payload.get("id") or ""),
        type=str(payload.get("type") or ""),
        params=dict(payload.get("params") or {}),
    )


def _coerce_composition_item(item: GeomancerCompositionItem | dict) -> GeomancerCompositionItem:
    if isinstance(item, GeomancerCompositionItem):
        return deepcopy(item)
    payload = dict(item or {})
    return GeomancerCompositionItem(
        id=str(payload.get("id") or ""),
        type=str(payload.get("type") or ""),
        operation=str(payload.get("operation") or "union"),
        params=dict(payload.get("params") or {}),
        position=list(payload.get("position") or []),
        rotation_deg=list(payload.get("rotation_deg") or []),
    )


def _coerce_hybrid_detail(detail: GeomancerHybridDetail | dict) -> GeomancerHybridDetail:
    if isinstance(detail, GeomancerHybridDetail):
        return deepcopy(detail)
    payload = dict(detail or {})
    return GeomancerHybridDetail(
        id=str(payload.get("id") or ""),
        source_mode=str(payload.get("source_mode") or ""),
        type=str(payload.get("type") or ""),
        operation=str(payload.get("operation") or "union"),
        params=dict(payload.get("params") or {}),
        position=list(payload.get("position") or []),
        rotation_deg=list(payload.get("rotation_deg") or []),
        target=str(payload.get("target") or ""),
    )


def _coerce_style(style: GeomancerStyle | dict) -> GeomancerStyle:
    if isinstance(style, GeomancerStyle):
        return deepcopy(style)
    payload = dict(style or {})
    profile = str(payload.get("style_profile") or "minimal").strip() or "minimal"
    defaults = STYLE_DEFAULTS_BY_PROFILE.get(profile, STYLE_DEFAULTS_BY_PROFILE["minimal"])
    return GeomancerStyle(
        style_profile=profile,
        shape_language=str(payload.get("shape_language") or defaults["shape_language"]),
        edge_treatment=str(payload.get("edge_treatment") or defaults["edge_treatment"]),
        detail_density=str(payload.get("detail_density") or defaults["detail_density"]),
        accent_profile=str(payload.get("accent_profile") or defaults["accent_profile"]),
    )


def _coerce_scalar(value: object) -> object:
    if isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return value
        try:
            return float(stripped)
        except ValueError:
            return value
    return value


def _coerce_float(value: object, default: float) -> float:
    coerced = _coerce_scalar(value)
    if isinstance(coerced, bool):
        return float(int(coerced))
    if isinstance(coerced, (int, float)):
        return float(coerced)
    return default


def _clean_list(values: list[object]) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def _validate_overall_dimensions(plan: GeomancerPlan, errors: list[str], clarification_needed: list[str]) -> None:
    overall_keys = ("overall_width_mm", "overall_depth_mm", "overall_height_mm")
    present_dimensions = {
        key: _coerce_float(plan.dimensions.get(key), 0.0)
        for key in overall_keys
        if plan.dimensions.get(key) not in (None, "")
    }
    for key, value in present_dimensions.items():
        plan.dimensions[key] = value
        if value <= 0:
            errors.append(f"{key} must be greater than zero.")
        elif value < MIN_OVERALL_DIMENSION_MM:
            clarification_needed.append(f"{key.replace('_mm', '').replace('_', ' ')} is too small to be safely printable.")
        elif value > MAX_PRINTABLE_DIMENSION_MM:
            errors.append(f"{key} exceeds the current printable design envelope.")

    thickness = _coerce_float(plan.dimensions.get("material_thickness_mm"), 0.0)
    if thickness > 0 and present_dimensions:
        smallest_span = min(present_dimensions.values())
        if thickness >= smallest_span:
            errors.append("material_thickness_mm must be smaller than the overall part dimensions.")
        elif thickness > smallest_span * 0.4:
            clarification_needed.append("Material thickness is unusually large relative to the overall dimensions.")


def _validate_style(
    plan: GeomancerPlan,
    object_type: str,
    base_mode: str,
    warnings: list[str],
    assumptions: list[str],
    clarification_needed: list[str],
) -> None:
    style = _coerce_style(plan.style)
    profile = str(style.style_profile or "minimal").strip() or "minimal"
    if profile not in ALLOWED_STYLE_PROFILES:
        warnings.append(f"Unsupported style profile '{profile}' was normalized to minimal.")
        profile = "minimal"
    supported_profiles = STYLE_COMPATIBILITY_BY_OBJECT_TYPE.get(object_type, {"minimal"})
    if profile not in supported_profiles:
        warnings.append(f"Style profile '{profile}' is not supported for the {object_type.replace('_', ' ')}; applied minimal styling.")
        profile = "minimal"

    defaults = STYLE_DEFAULTS_BY_PROFILE.get(profile, STYLE_DEFAULTS_BY_PROFILE["minimal"])
    style.style_profile = profile
    style.shape_language = defaults["shape_language"]
    style.edge_treatment = defaults["edge_treatment"]
    style.detail_density = defaults["detail_density"]
    style.accent_profile = defaults["accent_profile"]
    plan.style = style

    if base_mode == "compositional" and profile != "minimal":
        assumptions.append(f"Applied {profile.replace('_', ' ')} styling to the {object_type.replace('_', ' ')} template.")
    elif base_mode == "constraint" and profile == "rounded" and object_type in {"phone_stand", "enclosure", "tray", "plate"}:
        assumptions.append(f"Applied rounded styling to the {object_type.replace('_', ' ')} template.")


def _validate_component_realism(plan: GeomancerPlan, errors: list[str], warnings: list[str], clarification_needed: list[str]) -> None:
    overall_width = _coerce_float(plan.dimensions.get("overall_width_mm"), 0.0)
    overall_depth = _coerce_float(plan.dimensions.get("overall_depth_mm"), 0.0)
    overall_height = _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0)
    smallest_span = min(value for value in (overall_width, overall_depth, overall_height) if value > 0) if any(
        value > 0 for value in (overall_width, overall_depth, overall_height)
    ) else 0.0
    material_thickness = _coerce_float(plan.dimensions.get("material_thickness_mm"), 0.0)
    for component in plan.components:
        if component.type in {"hole_pattern", "mount_hole", "through_hole"}:
            _validate_hole_component(plan, component, errors)
        elif component.type == "slot":
            _validate_slot_component(plan, component, errors)
        elif component.type == "opening":
            _validate_opening_component(plan, component, errors)
        elif component.type == "shell":
            _validate_shell_component(plan, component, errors, warnings)
        elif component.type == "retaining_lip":
            _validate_retaining_lip_component(plan, component, errors, warnings)
        elif component.type in {"angled_support", "vertical_leg", "horizontal_leg"}:
            _validate_support_component(plan, component, errors, warnings, clarification_needed)
        elif component.type in {"back_plate", "base_plate"}:
            _validate_plate_component(plan, component, errors, warnings)
        elif component.type == "sphere":
            radius = _coerce_float(component.params.get("radius_mm"), 0.0)
            if smallest_span and radius * 2.0 > smallest_span:
                warnings.append(f"Component '{component.id or component.type}' sphere radius was interpreted near the overall size limit.")

        if material_thickness > 0 and component.type in {"hole_pattern", "mount_hole", "through_hole"}:
            diameter = _coerce_float(component.params.get("diameter_mm"), 0.0)
            if diameter > material_thickness * 3.0:
                errors.append(f"Component '{component.id or component.type}' hole diameter is too large for the material thickness.")


def _validate_hybrid_details(plan: GeomancerPlan, errors: list[str], warnings: list[str], clarification_needed: list[str]) -> None:
    if not plan.hybrid_details:
        return
    base_mode = "compositional" if plan.intent.object_type in COMPOSITIONAL_OBJECT_TYPES else "constraint"
    for detail in plan.hybrid_details:
        if base_mode == "constraint":
            _validate_hybrid_compositional_detail(plan, detail, errors, warnings)
        else:
            _validate_hybrid_feature_detail(plan, detail, errors, warnings, clarification_needed)


def _validate_hybrid_compositional_detail(
    plan: GeomancerPlan,
    detail: GeomancerHybridDetail,
    errors: list[str],
    warnings: list[str],
) -> None:
    if detail.source_mode and detail.source_mode not in {"compositional", "hybrid"}:
        warnings.append(f"Hybrid detail '{detail.id or detail.type}' recorded a non-compositional source mode.")
    temp_item = GeomancerCompositionItem(
        id=detail.id,
        type=detail.type,
        operation=detail.operation or "union",
        params=dict(detail.params),
        position=list(detail.position),
        rotation_deg=list(detail.rotation_deg),
    )
    if temp_item.type not in ALLOWED_COMPOSITION_ITEM_TYPES:
        errors.append(f"Unsupported hybrid detail type: {temp_item.type or 'missing'}.")
        return
    if temp_item.operation != "union":
        errors.append(f"Hybrid compositional detail '{temp_item.id or temp_item.type}' must use union operation.")
    if temp_item.position and not _is_vector3(temp_item.position):
        errors.append(f"Hybrid compositional detail '{temp_item.id or temp_item.type}' position must contain three numeric values.")
    if temp_item.rotation_deg and not _is_vector3(temp_item.rotation_deg):
        errors.append(f"Hybrid compositional detail '{temp_item.id or temp_item.type}' rotation must contain three numeric values.")
    bounds = _composition_bounds(temp_item)
    if not bounds:
        return
    width = _coerce_float(plan.dimensions.get("overall_width_mm"), 0.0)
    depth = _coerce_float(plan.dimensions.get("overall_depth_mm"), 0.0)
    height = _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0)
    if width and bounds["width_mm"] > width:
        errors.append(f"Hybrid compositional detail '{temp_item.id or temp_item.type}' exceeds the host width.")
    if depth and bounds["depth_mm"] > depth:
        errors.append(f"Hybrid compositional detail '{temp_item.id or temp_item.type}' exceeds the host depth.")
    if height and bounds["height_mm"] > height:
        errors.append(f"Hybrid compositional detail '{temp_item.id or temp_item.type}' exceeds the host height.")


def _validate_hybrid_feature_detail(
    plan: GeomancerPlan,
    detail: GeomancerHybridDetail,
    errors: list[str],
    warnings: list[str],
    clarification_needed: list[str],
) -> None:
    if detail.source_mode and detail.source_mode not in {"constraint", "hybrid"}:
        warnings.append(f"Hybrid detail '{detail.id or detail.type}' recorded a non-functional source mode.")
    detail_type = str(detail.type or "").strip()
    if detail_type not in HYBRID_FEATURE_COMPONENT_TYPES:
        errors.append(f"Unsupported hybrid feature type: {detail_type or 'missing'}.")
        return
    component = GeomancerComponent(
        id=detail.id,
        type=detail_type,
        params=dict(detail.params),
    )
    component.params = {key: _coerce_scalar(value) for key, value in dict(component.params).items()}
    if detail_type in {"hole_pattern", "mount_hole", "through_hole"}:
        if detail_type == "mount_hole" and "count" not in component.params:
            component.params["count"] = 1
        if detail_type == "through_hole" and "count" not in component.params:
            component.params["count"] = 1
        _validate_hole_component(plan, component, errors)
    elif detail_type == "slot":
        _validate_slot_component(plan, component, errors)
    elif detail_type == "opening":
        _validate_opening_component(plan, component, errors)
    elif detail_type == "tab":
        _validate_tab_component(plan, component, errors, warnings)
    if detail_type in {"slot", "opening", "tab"}:
        if detail.position and not _is_vector3(detail.position):
            errors.append(f"Hybrid feature '{detail.id or detail.type}' position must contain three numeric values.")
        if detail.rotation_deg and not _is_vector3(detail.rotation_deg):
            errors.append(f"Hybrid feature '{detail.id or detail.type}' rotation must contain three numeric values.")


def _validate_hole_component(plan: GeomancerPlan, component: GeomancerComponent, errors: list[str]) -> None:
    diameter = _coerce_float(component.params.get("diameter_mm"), 0.0)
    count = int(_coerce_float(component.params.get("count"), 0.0))
    if count < 0:
        errors.append(f"Component '{component.id or component.type}' has an invalid hole count.")
    if diameter <= 0:
        errors.append(f"Component '{component.id or component.type}' hole diameter must be greater than zero.")

    overall_width = _coerce_float(plan.dimensions.get("overall_width_mm"), 0.0)
    overall_depth = _coerce_float(plan.dimensions.get("overall_depth_mm"), 0.0)
    overall_height = _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0)
    host_span = min(value for value in (overall_width, overall_depth, overall_height) if value > 0) if any(
        value > 0 for value in (overall_width, overall_depth, overall_height)
    ) else 0.0
    if plan.intent.object_type == "bracket":
        horizontal_width = _component_dimension(plan, "horizontal_leg", "width_mm")
        host_span = max(host_span, horizontal_width)
        if horizontal_width and diameter > horizontal_width:
            errors.append(f"Component '{component.id or component.type}' hole diameter is wider than the bracket arm.")
    if host_span and diameter >= host_span * 0.6:
        errors.append(f"Component '{component.id or component.type}' hole diameter is unrealistically large.")


def _validate_tab_component(plan: GeomancerPlan, component: GeomancerComponent, errors: list[str], warnings: list[str]) -> None:
    tab_width = _coerce_float(component.params.get("width_mm"), 0.0)
    tab_height = _coerce_float(component.params.get("height_mm"), 0.0)
    tab_thickness = _coerce_float(component.params.get("thickness_mm"), 0.0)
    overall_width = _coerce_float(plan.dimensions.get("overall_width_mm"), 0.0)
    overall_depth = _coerce_float(plan.dimensions.get("overall_depth_mm"), 0.0)
    overall_height = _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0)
    if tab_width <= 0 or tab_height <= 0 or tab_thickness <= 0:
        errors.append(f"Component '{component.id or component.type}' requires positive width, height, and thickness.")
        return
    if overall_width and tab_width > overall_width:
        errors.append(f"Component '{component.id or component.type}' tab width exceeds the host width.")
    if overall_height and tab_height > overall_height:
        errors.append(f"Component '{component.id or component.type}' tab height exceeds the host height.")
    if overall_depth and tab_thickness > overall_depth:
        errors.append(f"Component '{component.id or component.type}' tab thickness exceeds the host depth.")
    smallest = min(value for value in (overall_width, overall_depth, overall_height) if value > 0) if any(
        value > 0 for value in (overall_width, overall_depth, overall_height)
    ) else 0.0
    if smallest and tab_thickness > smallest * 0.4:
        warnings.append(f"Component '{component.id or component.type}' tab thickness is large relative to the host geometry.")


def _validate_slot_component(plan: GeomancerPlan, component: GeomancerComponent, errors: list[str]) -> None:
    slot_width = _coerce_float(component.params.get("width_mm"), 0.0)
    slot_height = _coerce_float(component.params.get("height_mm"), 0.0)
    slot_depth = _coerce_float(component.params.get("depth_mm"), 0.0)
    overall_width = _coerce_float(plan.dimensions.get("overall_width_mm"), 0.0)
    overall_depth = _coerce_float(plan.dimensions.get("overall_depth_mm"), 0.0)
    overall_height = _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0)
    if overall_width and slot_width and slot_width > overall_width:
        errors.append(f"Component '{component.id or component.type}' slot width exceeds the host width.")
    if overall_height and slot_height and slot_height > overall_height:
        errors.append(f"Component '{component.id or component.type}' slot height exceeds the host height.")
    if overall_depth and slot_depth and slot_depth > overall_depth:
        errors.append(f"Component '{component.id or component.type}' slot depth exceeds the host depth.")


def _validate_opening_component(plan: GeomancerPlan, component: GeomancerComponent, errors: list[str]) -> None:
    opening_width = _coerce_float(component.params.get("width_mm"), 0.0)
    opening_height = _coerce_float(component.params.get("height_mm"), 0.0)
    opening_depth = _coerce_float(component.params.get("depth_mm"), 0.0)
    overall_width = _coerce_float(plan.dimensions.get("overall_width_mm"), 0.0)
    overall_depth = _coerce_float(plan.dimensions.get("overall_depth_mm"), 0.0)
    overall_height = _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0)
    if overall_width and opening_width and opening_width > overall_width:
        errors.append(f"Component '{component.id or component.type}' opening width exceeds the host face.")
    if overall_height and opening_height and opening_height > overall_height:
        errors.append(f"Component '{component.id or component.type}' opening height exceeds the host face.")
    if overall_depth and opening_depth and opening_depth > overall_depth:
        errors.append(f"Component '{component.id or component.type}' opening depth exceeds the host depth.")


def _validate_shell_component(plan: GeomancerPlan, component: GeomancerComponent, errors: list[str], warnings: list[str]) -> None:
    width = _coerce_float(component.params.get("width_mm"), _coerce_float(plan.dimensions.get("overall_width_mm"), 0.0))
    depth = _coerce_float(component.params.get("depth_mm"), _coerce_float(plan.dimensions.get("overall_depth_mm"), 0.0))
    height = _coerce_float(component.params.get("height_mm"), _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0))
    wall = _coerce_float(component.params.get("wall_thickness_mm"), _coerce_float(plan.constraints.get("minimum_wall_thickness_mm"), SAFE_MIN_PRINT_THICKNESS_MM))
    smallest_span = min(value for value in (width, depth, height) if value > 0) if any(value > 0 for value in (width, depth, height)) else 0.0
    if smallest_span and wall >= smallest_span / 2.0:
        errors.append(f"Component '{component.id or component.type}' wall thickness is too large for the shell dimensions.")
    elif smallest_span and wall > smallest_span * 0.35:
        warnings.append(f"Component '{component.id or component.type}' wall thickness is unusually large for the shell dimensions.")


def _validate_retaining_lip_component(plan: GeomancerPlan, component: GeomancerComponent, errors: list[str], warnings: list[str]) -> None:
    lip_height = _coerce_float(component.params.get("height_mm"), 0.0)
    overall_height = _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0)
    material_thickness = _coerce_float(plan.dimensions.get("material_thickness_mm"), 0.0)
    if overall_height and lip_height > overall_height * 0.35:
        errors.append(f"Component '{component.id or component.type}' retaining lip is too tall for the host geometry.")
    elif overall_height and lip_height > overall_height * 0.2:
        warnings.append(f"Component '{component.id or component.type}' retaining lip is tall relative to the host geometry.")
    if material_thickness and lip_height > material_thickness * 6.0:
        warnings.append(f"Component '{component.id or component.type}' retaining lip is large relative to material thickness.")


def _validate_support_component(plan: GeomancerPlan, component: GeomancerComponent, errors: list[str], warnings: list[str], clarification_needed: list[str]) -> None:
    support_thickness = _coerce_float(component.params.get("thickness_mm"), _coerce_float(plan.dimensions.get("material_thickness_mm"), 0.0))
    support_height = _coerce_float(component.params.get("height_mm"), 0.0)
    support_length = _coerce_float(component.params.get("length_mm"), 0.0)
    cradle_depth = _coerce_float(component.params.get("cradle_depth_mm"), 0.0)
    overall_width = _coerce_float(plan.dimensions.get("overall_width_mm"), 0.0)
    overall_depth = _coerce_float(plan.dimensions.get("overall_depth_mm"), 0.0)
    overall_height = _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0)
    if support_thickness and overall_width and support_thickness >= overall_width:
        errors.append(f"Component '{component.id or component.type}' thickness exceeds the host width.")
    if support_thickness and overall_depth and support_thickness >= overall_depth:
        errors.append(f"Component '{component.id or component.type}' thickness exceeds the host depth.")
    if support_height and overall_height and support_height > overall_height * 1.5:
        errors.append(f"Component '{component.id or component.type}' support height is unrealistically large.")
    elif support_height and overall_height and support_height > overall_height * 1.2:
        warnings.append(f"Component '{component.id or component.type}' support height is near the host limit.")
    if support_length and overall_width and support_length > overall_width * 1.2:
        errors.append(f"Component '{component.id or component.type}' support length exceeds the host width.")
    if cradle_depth and overall_depth and cradle_depth > overall_depth:
        errors.append(f"Component '{component.id or component.type}' cradle depth exceeds the host depth.")


def _validate_plate_component(plan: GeomancerPlan, component: GeomancerComponent, errors: list[str], warnings: list[str]) -> None:
    width = _coerce_float(component.params.get("width_mm"), 0.0)
    height = _coerce_float(component.params.get("height_mm"), 0.0)
    thickness = _coerce_float(component.params.get("thickness_mm"), 0.0)
    overall_width = _coerce_float(plan.dimensions.get("overall_width_mm"), 0.0)
    overall_height = _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0)
    largest_face = max(value for value in (overall_width, overall_height) if value > 0) if any(value > 0 for value in (overall_width, overall_height)) else 0.0
    if overall_width and width and width > overall_width:
        errors.append(f"Component '{component.id or component.type}' width exceeds the host width.")
    if overall_height and height and height > overall_height:
        errors.append(f"Component '{component.id or component.type}' height exceeds the host height.")
    if largest_face and thickness and thickness > largest_face * 0.35:
        warnings.append(f"Component '{component.id or component.type}' thickness is large relative to the host face.")


def _infer_compositional_dimensions(plan: GeomancerPlan, assumptions: list[str], warnings: list[str]) -> None:
    width = _coerce_float(plan.dimensions.get("overall_width_mm"), 0.0)
    depth = _coerce_float(plan.dimensions.get("overall_depth_mm"), 0.0)
    height = _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0)
    inferred = False
    for item in plan.composition:
        bounds = _composition_bounds(item)
        if not bounds:
            continue
        inferred = True
        width = max(width, bounds["width_mm"])
        depth = max(depth, bounds["depth_mm"])
        height = max(height, bounds["height_mm"])
    if inferred:
        if width > 0 and "overall_width_mm" not in plan.dimensions:
            plan.dimensions["overall_width_mm"] = width
        if depth > 0 and "overall_depth_mm" not in plan.dimensions:
            plan.dimensions["overall_depth_mm"] = depth
        if height > 0 and "overall_height_mm" not in plan.dimensions:
            plan.dimensions["overall_height_mm"] = height
        if "Inferred compositional envelope from primitive items." not in assumptions:
            assumptions.append("Inferred compositional envelope from primitive items.")
    if "material_thickness_mm" in plan.dimensions:
        thickness = _coerce_float(plan.dimensions["material_thickness_mm"], 0.0)
        if thickness < SAFE_MIN_PRINT_THICKNESS_MM:
            plan.dimensions["material_thickness_mm"] = SAFE_MIN_PRINT_THICKNESS_MM
            warnings.append("dimensions.material_thickness_mm was clamped to the safe printable minimum.")
        else:
            plan.dimensions["material_thickness_mm"] = thickness


def _validate_composition_items(plan: GeomancerPlan, errors: list[str], warnings: list[str]) -> None:
    for item in plan.composition:
        if item.type not in ALLOWED_COMPOSITION_ITEM_TYPES:
            errors.append(f"Unsupported composition item type: {item.type or 'missing'}.")
            continue
        operation = str(item.operation or "union").strip() or "union"
        if operation != "union":
            errors.append(f"Unsupported composition item operation: {operation}.")
        if item.position and not _is_vector3(item.position):
            errors.append(f"Composition item '{item.id or item.type}' position must contain three numeric values.")
            item.position = [0.0, 0.0, 0.0]
        else:
            item.position = _coerce_vector3(item.position, [0.0, 0.0, 0.0])
        if item.rotation_deg and not _is_vector3(item.rotation_deg):
            errors.append(f"Composition item '{item.id or item.type}' rotation must contain three numeric values.")
            item.rotation_deg = []
        else:
            item.rotation_deg = _coerce_vector3(item.rotation_deg, [])
        if item.type == "cube":
            width = _composition_param(item, ("width_mm", "size_x_mm"), 0.0)
            depth = _composition_param(item, ("depth_mm", "size_y_mm"), 0.0)
            height = _composition_param(item, ("height_mm", "size_z_mm"), 0.0)
            if width <= 0 or depth <= 0 or height <= 0:
                errors.append(f"Composition item '{item.id or item.type}' requires positive width, depth, and height.")
            if max(width, depth, height) > MAX_PRINTABLE_DIMENSION_MM:
                errors.append(f"Composition item '{item.id or item.type}' exceeds the printable envelope.")
        elif item.type == "cylinder":
            radius = _composition_param(item, ("radius_mm",), 0.0)
            height = _composition_param(item, ("height_mm",), 0.0)
            if radius <= 0 or height <= 0:
                errors.append(f"Composition item '{item.id or item.type}' requires positive radius and height.")
            if radius * 2.0 > MAX_PRINTABLE_DIMENSION_MM or height > MAX_PRINTABLE_DIMENSION_MM:
                errors.append(f"Composition item '{item.id or item.type}' exceeds the printable envelope.")
        elif item.type == "sphere":
            radius = _composition_param(item, ("radius_mm",), 0.0)
            if radius <= 0:
                errors.append(f"Composition item '{item.id or item.type}' requires a positive radius.")
            if radius * 2.0 > MAX_PRINTABLE_DIMENSION_MM:
                errors.append(f"Composition item '{item.id or item.type}' exceeds the printable envelope.")
        if item.position and len(item.position) != 3:
            errors.append(f"Composition item '{item.id or item.type}' position must contain three numeric values.")
        if item.rotation_deg and len(item.rotation_deg) != 3:
            errors.append(f"Composition item '{item.id or item.type}' rotation must contain three numeric values.")


def _validate_composition_bounds(plan: GeomancerPlan, errors: list[str], warnings: list[str]) -> None:
    width = _coerce_float(plan.dimensions.get("overall_width_mm"), 0.0)
    depth = _coerce_float(plan.dimensions.get("overall_depth_mm"), 0.0)
    height = _coerce_float(plan.dimensions.get("overall_height_mm"), 0.0)
    if width <= 0 or depth <= 0 or height <= 0:
        return
    for item in plan.composition:
        bounds = _composition_bounds(item)
        if not bounds:
            continue
        pos = item.position if isinstance(item.position, list) and len(item.position) == 3 else [0.0, 0.0, 0.0]
        if bounds["width_mm"] > width:
            errors.append(f"Composition item '{item.id or item.type}' exceeds the host width.")
        if bounds["depth_mm"] > depth:
            errors.append(f"Composition item '{item.id or item.type}' exceeds the host depth.")
        if bounds["height_mm"] > height:
            errors.append(f"Composition item '{item.id or item.type}' exceeds the host height.")
        if bounds["width_mm"] * 0.5 + abs(pos[0]) > width * 0.5:
            errors.append(f"Composition item '{item.id or item.type}' extends beyond the host width bounds.")
        if bounds["depth_mm"] * 0.5 + abs(pos[1]) > depth * 0.5:
            errors.append(f"Composition item '{item.id or item.type}' extends beyond the host depth bounds.")
        if bounds["height_mm"] * 0.5 + abs(pos[2]) > height * 0.5:
            errors.append(f"Composition item '{item.id or item.type}' extends beyond the host height bounds.")


def _composition_bounds(item: GeomancerCompositionItem) -> dict[str, float]:
    if item.type == "cube":
        width = _composition_param(item, ("width_mm", "size_x_mm"), 0.0)
        depth = _composition_param(item, ("depth_mm", "size_y_mm"), 0.0)
        height = _composition_param(item, ("height_mm", "size_z_mm"), 0.0)
        return {"width_mm": width, "depth_mm": depth, "height_mm": height}
    if item.type == "cylinder":
        radius = _composition_param(item, ("radius_mm",), 0.0)
        height = _composition_param(item, ("height_mm",), 0.0)
        return {"width_mm": radius * 2.0, "depth_mm": radius * 2.0, "height_mm": height}
    if item.type == "sphere":
        radius = _composition_param(item, ("radius_mm",), 0.0)
        diameter = radius * 2.0
        return {"width_mm": diameter, "depth_mm": diameter, "height_mm": diameter}
    return {}


def _composition_param(item: GeomancerCompositionItem, keys: tuple[str, ...], default: float) -> float:
    for key in keys:
        value = item.params.get(key)
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return default


def _coerce_vector3(values: list[float] | tuple[float, float, float] | object, default: list[float]) -> list[float]:
    if isinstance(values, (list, tuple)) and len(values) == 3:
        try:
            return [float(values[0]), float(values[1]), float(values[2])]
        except (TypeError, ValueError):
            return list(default)
    return list(default)


def _is_vector3(values: list[float] | tuple[float, float, float] | object) -> bool:
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        return False
    try:
        float(values[0])
        float(values[1])
        float(values[2])
        return True
    except (TypeError, ValueError):
        return False


def _component_dimension(plan: GeomancerPlan, component_type: str, key: str) -> float:
    for component in plan.components:
        if component.type == component_type:
            return _coerce_float(component.params.get(key), 0.0)
    return 0.0
