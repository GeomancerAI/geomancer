"""Canonical plan validation for Geomancer backend generation."""

from __future__ import annotations

from copy import deepcopy

from .plan_schema import CanonicalPlan, CanonicalPlanValidationResult


RULES_BY_OBJECT_TYPE = {
    "enclosure": {
        "required": ("width_mm", "depth_mm", "height_mm", "wall_thickness_mm"),
        "zero_ok": ("base_thickness_mm",),
        "features": {"shell", "wall", "opening"},
    },
    "tray": {
        "required": ("width_mm", "depth_mm", "height_mm", "wall_thickness_mm"),
        "zero_ok": ("base_thickness_mm", "lip_height_mm"),
        "features": {"shell", "wall", "opening", "rim"},
    },
    "bracket": {
        "required": ("base_length_mm", "flange_width_mm", "vertical_height_mm", "thickness_mm"),
        "zero_ok": (),
        "features": {"base_leg", "vertical_leg", "hole_pattern", "gusset"},
    },
    "clip": {
        "required": ("clip_width_mm", "opening_mm", "depth_mm", "thickness_mm", "base_length_mm"),
        "zero_ok": (),
        "features": {"base_plate", "back_bar", "clip_arm", "mount_hole"},
    },
    "planter": {
        "required": ("diameter_mm", "height_mm", "wall_thickness_mm"),
        "zero_ok": ("drain_hole_mm",),
        "features": {"vessel_shell", "drain_hole"},
    },
    "gear": {
        "required": ("diameter_mm", "thickness_mm"),
        "zero_ok": ("center_hole_mm",),
        "features": {"gear_body", "tooth_pattern", "bore"},
    },
    "adapter": {
        "required": ("large_diameter_mm", "small_diameter_mm", "length_mm"),
        "zero_ok": ("center_hole_mm", "flange_diameter_mm"),
        "features": {"adapter_body", "step_transition", "flange", "through_hole"},
    },
    "plate": {
        "required": ("width_mm", "height_mm", "thickness_mm"),
        "zero_ok": ("hole_diameter_mm", "hole_spacing_mm"),
        "features": {"panel", "hole_pattern"},
    },
    "standoff": {
        "required": ("outer_diameter_mm", "length_mm", "inner_diameter_mm"),
        "zero_ok": (),
        "features": {"standoff_body", "center_hole"},
    },
    "hook_mount": {
        "required": ("width_mm", "height_mm", "depth_mm"),
        "zero_ok": ("thickness_mm", "base_thickness_mm", "hook_length_mm", "hook_radius_mm", "hook_angle_deg", "hole_count", "hole_diameter_mm", "hole_margin_mm", "base_width_mm", "base_height_mm", "arm_length_mm", "hook_drop_mm", "mount_hole_mm", "mount_hole_count"),
        "features": {"hook_mount_body", "mounting_holes", "base_plate", "hook_arm", "hook_lip"},
    },
    "phone_stand": {
        "required": ("width_mm", "depth_mm", "height_mm", "thickness_mm", "viewing_angle_deg", "lip_height_mm", "cradle_depth_mm"),
        "zero_ok": ("device_width_mm", "base_depth_mm", "base_thickness_mm", "support_thickness_mm", "slot_width_mm", "slot_depth_mm", "angle_deg", "lip_width_mm", "lip_depth_mm", "cable_cutout_width_mm", "cable_cutout_height_mm", "cable_cutout_depth_mm"),
        "features": {"base_plate", "angled_support", "retaining_lip", "cable_cutout"},
    },
    "assembly": {
        "required": ("width_mm", "depth_mm", "height_mm"),
        "zero_ok": (),
        "features": {"cube", "cylinder", "sphere"},
    },
}


def validate_canonical_plan(plan: CanonicalPlan) -> CanonicalPlanValidationResult:
    """Validate and normalize the canonical plan before generation."""
    normalized = deepcopy(plan)
    warnings = list(normalized.warnings)
    clarification_needed: list[str] = []
    errors: list[str] = []

    rules = RULES_BY_OBJECT_TYPE.get(normalized.object_type)
    if rules is None:
        errors.append(f"Unsupported canonical object type: {normalized.object_type or 'missing'}.")
        normalized.warnings = warnings
        return CanonicalPlanValidationResult(
            status="invalid",
            normalized_plan=normalized,
            warnings=warnings,
            clarification_needed=clarification_needed,
            errors=errors,
            summary="Canonical plan validation failed.",
        )

    _validate_feature_types(normalized, rules["features"], errors)

    required_dims = rules["required"]
    zero_ok_dims = set(rules["zero_ok"])
    for dim_name in required_dims:
        value = normalized.dimensions.get(dim_name)
        if value is None:
            clarification_needed.append(f"Provide {dim_name.replace('_mm', '')} in mm.")
            normalized.missing_info.append(dim_name)
            continue
        coerced, dimension_error = _coerce_number(dim_name, value, allow_zero=False)
        if dimension_error:
            errors.append(dimension_error)
            continue
        normalized.dimensions[dim_name] = coerced
        if coerced <= 0:
            errors.append(f"{dim_name} must be greater than zero.")

    for dim_name, value in list(normalized.dimensions.items()):
        if dim_name in required_dims:
            continue
        coerced, dimension_error = _coerce_number(dim_name, value, allow_zero=dim_name in zero_ok_dims)
        if dimension_error:
            errors.append(dimension_error)
            continue
        normalized.dimensions[dim_name] = coerced
        if coerced < 0:
            errors.append(f"{dim_name} cannot be negative.")
        if coerced == 0 and dim_name not in zero_ok_dims:
            errors.append(f"{dim_name} must be greater than zero.")

    _normalize_special_cases(normalized, warnings)

    if normalized.missing_info:
        clarification_needed.extend(normalized.missing_info)

    if errors:
        status = "invalid"
        summary = f"Canonical {normalized.object_type} plan is invalid."
    elif clarification_needed:
        status = "clarify"
        summary = f"Clarification needed for canonical {normalized.object_type} plan."
    else:
        status = "valid"
        summary = f"Validated canonical {normalized.object_type} plan with {len(required_dims)} required dimensions."

    normalized.warnings = warnings
    return CanonicalPlanValidationResult(
        status=status,
        normalized_plan=normalized,
        warnings=warnings,
        clarification_needed=clarification_needed,
        errors=errors,
        summary=summary,
    )


def _validate_feature_types(plan: CanonicalPlan, allowed_feature_types: set[str], errors: list[str]) -> None:
    for feature in plan.features:
        if feature.type not in allowed_feature_types:
            errors.append(f"Unsupported canonical feature type: {feature.type}.")
        for param_name, value in feature.params.items():
            if isinstance(value, (bool, int, float, str)):
                continue
            errors.append(f"Feature '{feature.type}' parameter '{param_name}' has an unsupported value type.")


def _normalize_special_cases(plan: CanonicalPlan, warnings: list[str]) -> None:
    if plan.object_type == "adapter":
        large = plan.dimensions.get("large_diameter_mm")
        small = plan.dimensions.get("small_diameter_mm")
        if large is not None and small is not None and large < small:
            plan.dimensions["large_diameter_mm"], plan.dimensions["small_diameter_mm"] = small, large
            warnings.append("Adapter diameters were reordered so the large diameter stays first.")

    if plan.object_type == "standoff":
        outer = plan.dimensions.get("outer_diameter_mm")
        inner = plan.dimensions.get("inner_diameter_mm")
        if outer is not None and inner is not None and inner >= outer:
            adjusted = max(outer - 2.0, 1.0)
            plan.dimensions["inner_diameter_mm"] = adjusted
            warnings.append("Standoff inner diameter was clamped to remain inside the outer diameter.")

    if plan.object_type == "hook_mount":
        thickness = plan.dimensions.get("thickness_mm")
        hook_length = plan.dimensions.get("hook_length_mm")
        hook_angle = plan.dimensions.get("hook_angle_deg")
        depth = plan.dimensions.get("depth_mm")
        base_thickness = plan.dimensions.get("base_thickness_mm")

        if thickness is not None:
            adjusted_thickness = max(thickness, 3.0)
            if adjusted_thickness != thickness:
                plan.dimensions["thickness_mm"] = adjusted_thickness
                warnings.append("Hook mount thickness was clamped to remain printable.")
                thickness = adjusted_thickness

        if hook_length is not None:
            adjusted_hook_length = max(hook_length, 10.0)
            if adjusted_hook_length != hook_length:
                plan.dimensions["hook_length_mm"] = adjusted_hook_length
                warnings.append("Hook mount hook length was clamped to remain visually readable.")
                hook_length = adjusted_hook_length

        if thickness is not None:
            min_base = max(thickness * 1.25, 4.0)
            if base_thickness is None or base_thickness < min_base:
                plan.dimensions["base_thickness_mm"] = min_base
                warnings.append("Hook mount base thickness was clamped to keep the mounting plate readable.")
                base_thickness = min_base

        if hook_angle is not None:
            adjusted_angle = min(max(hook_angle, 12.0), 35.0)
            if adjusted_angle != hook_angle:
                plan.dimensions["hook_angle_deg"] = adjusted_angle
                warnings.append("Hook mount tip angle was clamped to remain visibly functional.")

        if depth is not None and hook_length is not None and thickness is not None:
            min_depth = hook_length + max(thickness * 1.5, 6.0)
            if depth < min_depth:
                plan.dimensions["depth_mm"] = min_depth
                warnings.append("Hook mount depth was expanded so the hook arm can read clearly.")

    if plan.object_type == "bracket":
        base_length = plan.dimensions.get("base_length_mm")
        flange_width = plan.dimensions.get("flange_width_mm")
        vertical_height = plan.dimensions.get("vertical_height_mm")
        thickness = plan.dimensions.get("thickness_mm")
        if base_length is not None and flange_width is not None and vertical_height is not None and thickness is not None:
            max_thickness = max(min(base_length, flange_width, vertical_height) * 0.35, 1.5)
            adjusted_thickness = min(max(thickness, 1.5), max_thickness)
            if adjusted_thickness != thickness:
                plan.dimensions["thickness_mm"] = adjusted_thickness
                warnings.append("Bracket thickness was clamped to keep the flanges printable.")
                thickness = adjusted_thickness
            if base_length <= thickness * 2.0:
                plan.dimensions["base_length_mm"] = thickness * 2.5
                warnings.append("Bracket base length was expanded to preserve the flange silhouette.")
            if vertical_height <= thickness * 2.0:
                plan.dimensions["vertical_height_mm"] = thickness * 2.5
                warnings.append("Bracket vertical height was expanded to preserve the flange silhouette.")

        hole_pattern = next((feature for feature in plan.features if feature.type == "hole_pattern"), None)
        if hole_pattern and base_length is not None and flange_width is not None and vertical_height is not None:
            hole_diameter = float(hole_pattern.params.get("diameter_mm", 0.0))
            max_safe_diameter = max(min(base_length, flange_width, vertical_height) * 0.2, 1.5)
            if hole_diameter > max_safe_diameter:
                hole_pattern.params["diameter_mm"] = max_safe_diameter
                warnings.append("Bracket hole diameter was clamped to preserve flange margins.")

    if plan.object_type in {"enclosure", "tray"}:
        width = plan.dimensions.get("width_mm")
        depth = plan.dimensions.get("depth_mm")
        height = plan.dimensions.get("height_mm")
        wall = plan.dimensions.get("wall_thickness_mm")
        base_thickness = plan.dimensions.get("base_thickness_mm")

        if width is not None and depth is not None and height is not None and wall is not None:
            min_span = min(width, depth)
            max_wall_by_span = max(min_span * 0.45, 1.5)
            max_wall_by_height = max((height - 0.5) / 2.0, 1.5)
            adjusted_wall = min(max(wall, 1.5), max_wall_by_span, max_wall_by_height)
            if adjusted_wall != wall:
                plan.dimensions["wall_thickness_mm"] = adjusted_wall
                warnings.append("Enclosure wall thickness was clamped to preserve a printable cavity.")
                wall = adjusted_wall

        if height is not None and wall is not None:
            if base_thickness is None:
                base_thickness = wall
                plan.dimensions["base_thickness_mm"] = base_thickness
            adjusted_base = max(base_thickness, wall)
            max_base_by_height = max(height - wall - 0.5, wall)
            adjusted_base = min(adjusted_base, max_base_by_height)
            if adjusted_base != base_thickness:
                plan.dimensions["base_thickness_mm"] = adjusted_base
                warnings.append("Enclosure base thickness was clamped to keep the cavity open.")

    if plan.object_type == "tray":
        width = plan.dimensions.get("width_mm")
        depth = plan.dimensions.get("depth_mm")
        height = plan.dimensions.get("height_mm")
        wall = plan.dimensions.get("wall_thickness_mm")
        base_thickness = plan.dimensions.get("base_thickness_mm")
        if width is not None and depth is not None and height is not None and wall is not None:
            min_height = max(wall * 4.0, 14.0)
            max_height = max(min(width, depth) * 0.35, 18.0)
            adjusted_height = min(max(height, min_height), max_height)
            if adjusted_height != height:
                plan.dimensions["height_mm"] = adjusted_height
                warnings.append("Tray height was clamped to preserve a shallow open-top profile.")
                height = adjusted_height
        if height is not None and base_thickness is not None:
            max_base = max(height * 0.45, wall or 1.5)
            adjusted_base = min(max(base_thickness, wall or 1.5), max_base)
            if adjusted_base != base_thickness:
                plan.dimensions["base_thickness_mm"] = adjusted_base
                warnings.append("Tray base thickness was clamped to keep the tray readable.")

    if plan.object_type == "phone_stand":
        width = plan.dimensions.get("width_mm")
        depth = plan.dimensions.get("depth_mm")
        height = plan.dimensions.get("height_mm")
        thickness = plan.dimensions.get("thickness_mm")
        angle = plan.dimensions.get("viewing_angle_deg", plan.dimensions.get("angle_deg"))
        lip_height = plan.dimensions.get("lip_height_mm")
        cradle_depth = plan.dimensions.get("cradle_depth_mm")
        device_width = plan.dimensions.get("device_width_mm")

        if width is not None and depth is not None and depth < max(width * 0.95, 80.0):
            plan.dimensions["depth_mm"] = max(width * 0.95, 80.0)
            depth = plan.dimensions["depth_mm"]
            warnings.append("Phone stand depth was expanded to keep the footprint stable.")

        if thickness is not None:
            max_thickness = max(min(width or thickness, depth or thickness, height or thickness) * 0.22, 3.5)
            adjusted_thickness = min(max(thickness, 3.5), max_thickness)
            if adjusted_thickness != thickness:
                plan.dimensions["thickness_mm"] = adjusted_thickness
                thickness = adjusted_thickness
                warnings.append("Phone stand thickness was clamped to stay printable.")

        if lip_height is not None and height is not None:
            max_lip_height = max(min(height * 0.18, (thickness or height) * 2.0), 3.5)
            if lip_height > max_lip_height:
                plan.dimensions["lip_height_mm"] = max_lip_height
                lip_height = max_lip_height
                warnings.append("Phone stand lip height was clamped to stay practical.")

        if cradle_depth is not None and depth is not None and thickness is not None:
            min_cradle = max(thickness * 4.0, 18.0)
            max_cradle = max(depth * 0.45, min_cradle)
            adjusted_cradle = min(max(cradle_depth, min_cradle), max_cradle)
            if adjusted_cradle != cradle_depth:
                plan.dimensions["cradle_depth_mm"] = adjusted_cradle
                cradle_depth = adjusted_cradle
                warnings.append("Phone stand cradle depth was clamped to keep the support readable.")

        if lip_height is not None and thickness is not None:
            min_lip_height = max(thickness * 0.75, 4.0)
            if lip_height < min_lip_height:
                plan.dimensions["lip_height_mm"] = min_lip_height
                lip_height = min_lip_height
                warnings.append("Phone stand lip height was raised to stay visibly distinct.")

        if device_width is not None and width is not None and device_width > max(width - 8.0, 8.0):
            plan.dimensions["device_width_mm"] = max(width - 12.0, 8.0)
            device_width = plan.dimensions["device_width_mm"]
            warnings.append("Phone stand device width was clamped to stay within the stand width.")

        if angle is not None and not 35.0 <= angle <= 80.0:
            adjusted_angle = min(max(angle, 35.0), 80.0)
            plan.dimensions["viewing_angle_deg"] = adjusted_angle
            plan.dimensions["angle_deg"] = adjusted_angle
            warnings.append("Phone stand viewing angle was clamped to keep the stand usable.")

        if depth is not None:
            plan.dimensions["base_depth_mm"] = depth
        if thickness is not None:
            plan.dimensions["base_thickness_mm"] = thickness
            plan.dimensions["support_thickness_mm"] = thickness
        if device_width is not None:
            plan.dimensions["slot_width_mm"] = device_width
        if cradle_depth is not None:
            plan.dimensions["slot_depth_mm"] = cradle_depth
        if width is not None:
            plan.dimensions["lip_width_mm"] = min(max((device_width or width * 0.75) + 18.0, width * 0.6), width - 12.0)
        if lip_height is not None:
            plan.dimensions["lip_height_mm"] = lip_height
        if thickness is not None:
            plan.dimensions["lip_depth_mm"] = max(thickness * 0.9, 4.0)


def _coerce_number(name: str, value: object, *, allow_zero: bool) -> tuple[float, str | None]:
    if isinstance(value, bool):
        return 0.0, f"{name} must be numeric."
    if isinstance(value, (int, float)):
        coerced = float(value)
        if coerced < 0:
            return coerced, f"{name} cannot be negative."
        if coerced == 0 and not allow_zero:
            return coerced, f"{name} must be greater than zero."
        return coerced, None
    return 0.0, f"{name} must be numeric."
