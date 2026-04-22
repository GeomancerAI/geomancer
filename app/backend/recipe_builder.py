"""Deterministic recipe builder from validated Geomancer Plan Schema v1."""

from __future__ import annotations

from .plan_schema import GeomancerPlan
from .recipe_schema import (
    DeterministicRecipe,
    DeterministicRecipeBuildResult,
    RecipeOp,
    RECIPE_OP_VOCABULARY,
)

RECIPE_NAME_BY_OBJECT_TYPE = {
    "plate": "panel_plate",
    "crate": "crate",
    "barrel": "barrel",
    "canister": "canister",
    "pedestal": "pedestal",
    "primitive_assembly": "primitive_assembly",
}
RECIPE_IMPLEMENTATION_ID_BY_OBJECT_TYPE = {
    "enclosure": "enclosure_open_top_shell_v1",
    "tray": "tray_box_shell_v1",
    "bracket": "bracket_body_v1",
    "plate": "panel_plate_v1",
    "standoff": "spacer_standoff_v1",
    "hook_mount": "hook_mount_wall_hook_v1",
    "phone_stand": "phone_stand_cradle_v1",
    "adapter": "adapter_transition_v1",
    "crate": "crate_v1",
    "barrel": "barrel_v1",
    "canister": "canister_v1",
    "pedestal": "pedestal_v1",
    "primitive_assembly": "primitive_assembly_v1",
}


def build_deterministic_recipe(plan: GeomancerPlan) -> DeterministicRecipeBuildResult:
    warnings = list(plan.warnings)
    errors: list[str] = []
    object_type = plan.intent.object_type
    style_profile = _style_profile(plan)

    if not object_type:
        return _build_result("invalid", plan, warnings, ["Plan is missing intent.object_type."], "Recipe build failed.")

    builder = {
        "enclosure": _build_shell_recipe,
        "tray": _build_shell_recipe,
        "bracket": _build_bracket_recipe,
        "plate": _build_plate_recipe,
        "standoff": _build_standoff_recipe,
        "hook_mount": _build_hook_mount_recipe,
        "phone_stand": _build_phone_stand_recipe,
        "adapter": _build_adapter_recipe,
        "primitive_assembly": _build_composition_recipe,
        "crate": _build_composition_recipe,
        "barrel": _build_composition_recipe,
        "canister": _build_composition_recipe,
        "pedestal": _build_composition_recipe,
    }.get(object_type)
    if builder is None:
        return _build_result("invalid", plan, warnings, [f"Unsupported object type for recipe building: {object_type}."], "Recipe build failed.")

    recipe = DeterministicRecipe(
        object_type=object_type,
        source_family=object_type,
        source_recipe=_recipe_name_for_object_type(object_type),
        execution_recipe=_recipe_name_for_object_type(object_type),
        implementation_id=_recipe_implementation_id(object_type, plan.construction_mode),
        warnings=warnings,
        notes=list(plan.notes),
    )
    recipe.ops = builder(plan, recipe.warnings)
    recipe.ops.extend(_style_recipe_ops(plan, style_profile, recipe.ops[0].id if recipe.ops else ""))
    if plan.construction_mode == "hybrid":
        root_id = recipe.ops[0].id if recipe.ops else ""
        recipe.ops.extend(_build_hybrid_detail_ops(plan, recipe.warnings, root_id))
    _validate_ops(recipe.ops, errors)
    if errors:
        return _build_result("invalid", recipe, warnings, errors, "Recipe build failed.")
    mode_suffix = " hybrid" if plan.construction_mode == "hybrid" else ""
    style_suffix = f" {style_profile}" if style_profile and style_profile != "minimal" else ""
    return DeterministicRecipeBuildResult(
        status="ready",
        normalized_recipe=recipe,
        warnings=list(recipe.warnings),
        errors=[],
        summary=(
            f"Built{mode_suffix}{style_suffix} deterministic recipe {recipe.execution_recipe} "
            f"({recipe.implementation_id}) for {object_type} with {len(recipe.ops)} ops."
        ),
    )


def _build_shell_recipe(plan: GeomancerPlan, warnings: list[str]) -> list[RecipeOp]:
    shell = _component(plan, "shell")
    opening = _component(plan, "opening")
    width = _dimension(plan, "overall_width_mm", "width_mm")
    depth = _dimension(plan, "overall_depth_mm", "depth_mm")
    height = _dimension(plan, "overall_height_mm", "height_mm")
    wall = _component_value(shell, "wall_thickness_mm", _constraint(plan, "minimum_wall_thickness_mm", 2.4))
    base_thickness = _dimension(plan, "material_thickness_mm", default=wall)
    params = {
        "width_mm": _component_value(shell, "width_mm", width),
        "depth_mm": _component_value(shell, "depth_mm", depth),
        "height_mm": _component_value(shell, "height_mm", height),
        "wall_thickness_mm": wall,
        "base_thickness_mm": base_thickness,
        "open_top": bool(_component_value(opening, "open_top", plan.intent.object_type in {"enclosure", "tray"})),
        "front_opening": bool(_component_value(opening, "front_opening", False)),
    }
    ops = [RecipeOp(op="shell", id="shell", params=params)]
    if params["front_opening"]:
        ops.append(
            RecipeOp(
                op="boolean_difference",
                id="front_opening",
                target="shell",
                tool="front_opening",
                params={
                    "opening_width_mm": _component_value(opening, "width_mm", params["width_mm"] * 0.55),
                    "opening_height_mm": _component_value(opening, "height_mm", params["height_mm"] * 0.45),
                },
            )
        )
    if params["open_top"] and plan.intent.object_type != "tray":
        ops.append(RecipeOp(op="flatten_bottom", id="open_top", target="shell", params={"mode": "open_top"}))
    return ops


def _build_bracket_recipe(plan: GeomancerPlan, warnings: list[str]) -> list[RecipeOp]:
    horizontal = _component(plan, "horizontal_leg")
    vertical = _component(plan, "vertical_leg")
    holes = _component(plan, "hole_pattern")
    if _component(plan, "gusset"):
        warnings.append("Bracket gusset is carried in the plan but deferred by the current single-body recipe.")
    ops = [
        RecipeOp(
            op="bracket_body",
            id="bracket_body",
            params={
                "base_length_mm": _component_value(horizontal, "length_mm", _dimension(plan, "overall_width_mm")),
                "flange_width_mm": _component_value(horizontal, "width_mm", _dimension(plan, "overall_depth_mm")),
                "vertical_height_mm": _component_value(vertical, "height_mm", _dimension(plan, "overall_height_mm")),
                "thickness_mm": _component_value(horizontal, "thickness_mm", _dimension(plan, "material_thickness_mm")),
            },
        )
    ]
    if holes:
        ops.append(
            RecipeOp(
                op="hole_pattern",
                id="mount_holes",
                target="bracket_body",
                params={
                    "count": int(_component_value(holes, "count", 0)),
                    "diameter_mm": _component_value(holes, "diameter_mm", 0.0),
                    "layout": "rectangular",
                },
            )
        )
    return ops


def _build_plate_recipe(plan: GeomancerPlan, warnings: list[str]) -> list[RecipeOp]:
    base = _component(plan, "base_plate")
    holes = _component(plan, "hole_pattern")
    thickness = _component_value(base, "thickness_mm", _dimension(plan, "material_thickness_mm"))
    ops = [
        RecipeOp(
            op="add_box",
            id="panel",
            params={
                "size_x_mm": _component_value(base, "width_mm", _dimension(plan, "overall_width_mm")),
                "size_y_mm": thickness,
                "size_z_mm": _component_value(base, "height_mm", _dimension(plan, "overall_height_mm", default=_dimension(plan, "overall_depth_mm"))),
                "origin": [0.0, 0.0, 0.0],
            },
        )
    ]
    if holes:
        count = int(_component_value(holes, "count", 0))
        diameter = _component_value(holes, "diameter_mm", 0.0)
        if count > 0 and diameter > 0:
            ops.append(
                RecipeOp(
                    op="hole_pattern",
                    id="panel_holes",
                    target="panel",
                    params={
                        "count": count,
                        "diameter_mm": diameter,
                        "layout": "corners" if count >= 4 else "pair_horizontal",
                    },
                )
            )
    return ops


def _build_standoff_recipe(plan: GeomancerPlan, warnings: list[str]) -> list[RecipeOp]:
    body = _component(plan, "cylinder")
    hole = _component(plan, "through_hole")
    outer_diameter = _component_value(body, "diameter_mm", _dimension(plan, "overall_width_mm"))
    length = _component_value(body, "height_mm", _dimension(plan, "overall_height_mm"))
    ops = [
        RecipeOp(
            op="add_cylinder",
            id="standoff_body",
            params={"radius_mm": outer_diameter / 2.0, "height_mm": length, "origin": [0.0, 0.0, 0.0]},
        )
    ]
    diameter = _component_value(hole, "diameter_mm", 0.0)
    if diameter > 0:
        ops.append(RecipeOp(op="add_hole", id="center_hole", target="standoff_body", params={"diameter_mm": diameter, "count": 1, "layout": "center"}))
    return ops


def _build_hook_mount_recipe(plan: GeomancerPlan, warnings: list[str]) -> list[RecipeOp]:
    back = _component(plan, "back_plate")
    arm = _component(plan, "hook_arm")
    tip = _component(plan, "hook_tip")
    holes = _component(plan, "hole_pattern")
    ops = [
        RecipeOp(
            op="hook_mount_body",
            id="hook_mount_body",
            params={
                "width_mm": _component_value(back, "width_mm", _dimension(plan, "overall_width_mm")),
                "height_mm": _component_value(back, "height_mm", _dimension(plan, "overall_height_mm")),
                "depth_mm": _component_value(arm, "length_mm", _dimension(plan, "overall_depth_mm")),
                "thickness_mm": _component_value(back, "thickness_mm", _dimension(plan, "material_thickness_mm")),
                "base_thickness_mm": _component_value(back, "thickness_mm", _dimension(plan, "material_thickness_mm")),
                "hook_length_mm": _component_value(arm, "length_mm", _dimension(plan, "overall_depth_mm") * 0.45),
                "hook_radius_mm": _component_value(tip, "radius_mm", _dimension(plan, "material_thickness_mm")),
                "hook_angle_deg": _component_value(tip, "angle_deg", 18.0),
            },
        )
    ]
    if holes:
        ops.append(
            RecipeOp(
                op="hole_pattern",
                id="mount_holes",
                target="hook_mount_body",
                params={
                    "count": int(_component_value(holes, "count", 2)),
                    "diameter_mm": _component_value(holes, "diameter_mm", 0.0),
                    "layout": "wall_vertical_pair",
                    "margin_mm": _component_value(holes, "margin_mm", 0.0),
                },
            )
        )
    return ops


def _build_phone_stand_recipe(plan: GeomancerPlan, warnings: list[str]) -> list[RecipeOp]:
    base = _component(plan, "base_plate")
    lip = _component(plan, "retaining_lip")
    support = _component(plan, "angled_support")
    cable = _component(plan, "opening")
    width = _component_value(base, "width_mm", _dimension(plan, "overall_width_mm"))
    depth = _component_value(base, "depth_mm", _dimension(plan, "overall_depth_mm"))
    height = _component_value(support, "height_mm", _dimension(plan, "overall_height_mm"))
    thickness = _component_value(base, "thickness_mm", _dimension(plan, "material_thickness_mm"))
    viewing_angle = _component_value(support, "angle_deg", 65.0)
    lip_height = _component_value(lip, "height_mm", max(thickness * 0.8, 4.0))
    cradle_depth = _component_value(support, "cradle_depth_mm", max(thickness * 4.0, 18.0))
    device_width = _component_value(support, "device_width_mm", max(width - (thickness * 3.0), 0.0))
    ops = [
        RecipeOp(
            op="phone_stand_body",
            id="phone_stand_body",
            params={
                "width_mm": width,
                "depth_mm": depth,
                "height_mm": height,
                "thickness_mm": thickness,
                "viewing_angle_deg": viewing_angle,
                "lip_height_mm": lip_height,
                "cradle_depth_mm": cradle_depth,
                "device_width_mm": device_width,
            },
        )
    ]
    if cable and bool(_component_value(cable, "enabled", True)):
        cable_width = _component_value(cable, "width_mm", max(device_width * 0.25, 6.0))
        cable_depth = _component_value(cable, "depth_mm", max(thickness * 2.5, 8.0))
        cable_height = _component_value(cable, "height_mm", max(thickness * 1.2, 6.0))
        ops.extend(
            [
                RecipeOp(
                    op="add_box",
                    id="cable_cutout",
                    params={
                        "size_x_mm": cable_width,
                        "size_y_mm": cable_depth,
                        "size_z_mm": cable_height,
                        "origin": [0.0, -(depth / 2.0) + (cable_depth / 2.0) + max(thickness * 0.1, 0.25), cable_height / 2.0],
                    },
                ),
                RecipeOp(op="boolean_difference", id="carve_cable_cutout", target="phone_stand_body", tool="cable_cutout"),
            ]
        )
    return ops


def _build_adapter_recipe(plan: GeomancerPlan, warnings: list[str]) -> list[RecipeOp]:
    cylinders = [component for component in plan.components if component.type == "cylinder"]
    through_hole = _component(plan, "through_hole")
    large = max((_component_value(component, "diameter_mm", 0.0) for component in cylinders if component), default=_dimension(plan, "overall_width_mm"))
    small = min((_component_value(component, "diameter_mm", large * 0.6) for component in cylinders if component), default=max(_dimension(plan, "overall_depth_mm"), large * 0.6))
    length = max((_component_value(component, "height_mm", 0.0) for component in cylinders if component), default=_dimension(plan, "overall_height_mm"))
    top_length = length * 0.5
    ops = [
        RecipeOp(op="add_cylinder", id="adapter_large", params={"radius_mm": large / 2.0, "height_mm": top_length, "origin": [0.0, 0.0, (length / 2.0) - (top_length / 2.0)]}),
        RecipeOp(op="add_cylinder", id="adapter_small", params={"radius_mm": small / 2.0, "height_mm": length - top_length, "origin": [0.0, 0.0, -(length / 2.0) + ((length - top_length) / 2.0)]}),
        RecipeOp(op="boolean_union", id="join_adapter", target="adapter_large", tool="adapter_small"),
    ]
    diameter = _component_value(through_hole, "diameter_mm", 0.0)
    if diameter > 0:
        ops.append(RecipeOp(op="add_hole", id="through_hole", target="adapter_large", params={"diameter_mm": diameter, "count": 1, "layout": "center"}))
    return ops


def _build_composition_recipe(plan: GeomancerPlan, warnings: list[str]) -> list[RecipeOp]:
    items = list(plan.composition)
    if not items and plan.components:
        warnings.append("Compositional recipe fell back to legacy component entries.")
        items = [_component_to_composition_item(component) for component in plan.components]

    ops: list[RecipeOp] = []
    root_id: str = ""
    for index, item in enumerate(items):
        op = _composition_item_to_recipe_op(item, plan, index)
        if op is None:
            continue
        ops.append(op)
        if not root_id:
            root_id = op.id
            continue
        if _composition_item_operation(item) == "union":
            union_id = f"union_{root_id}_{op.id}"
            ops.append(RecipeOp(op="boolean_union", id=union_id, target=root_id, tool=op.id))
        else:
            warnings.append(f"Composition item '{item.id or item.type}' used unsupported operation '{_composition_item_operation(item)}'.")
    return ops


def _detail_type(detail) -> str:
    return str(detail.get("type") if isinstance(detail, dict) else getattr(detail, "type", "")).strip()


def _detail_source_mode(detail) -> str:
    return str(detail.get("source_mode") if isinstance(detail, dict) else getattr(detail, "source_mode", "")).strip()


def _detail_id(detail, index: int) -> str:
    detail_id = str(detail.get("id") if isinstance(detail, dict) else getattr(detail, "id", "")).strip()
    return detail_id or f"hybrid_detail_{index + 1}"


def _detail_params(detail) -> dict:
    params = detail.get("params") if isinstance(detail, dict) else getattr(detail, "params", {})
    return dict(params or {})


def _detail_vector(detail, key: str) -> list[float]:
    values = _detail_params(detail).get(key)
    if isinstance(values, (list, tuple)) and len(values) == 3:
        return [float(values[0]), float(values[1]), float(values[2])]
    return []


def _numeric(params: dict, keys: tuple[str, ...], default: float) -> float:
    for key in keys:
        value = params.get(key)
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return default


def _default_hybrid_origin(plan: GeomancerPlan, detail_type: str, detail_id: str) -> list[float]:
    width = _dimension(plan, "overall_width_mm")
    depth = _dimension(plan, "overall_depth_mm")
    height = _dimension(plan, "overall_height_mm")
    if detail_type == "cylinder":
        return [0.0, 0.0, height * 0.24]
    if detail_type == "sphere":
        return [width * 0.18, 0.0, height * 0.12]
    return [width * 0.18, 0.0, height * 0.18]


def _default_hybrid_feature_origin(plan: GeomancerPlan, detail_type: str) -> list[float]:
    depth = _dimension(plan, "overall_depth_mm")
    height = _dimension(plan, "overall_height_mm")
    if detail_type in {"slot", "opening"}:
        return [0.0, depth * 0.18, 0.0]
    if detail_type == "tab":
        return [0.0, -(depth * 0.22), height * 0.18]
    return [0.0, 0.0, 0.0]


def _build_hybrid_detail_ops(plan: GeomancerPlan, warnings: list[str], root_id: str) -> list[RecipeOp]:
    if not root_id:
        warnings.append("Hybrid recipe could not resolve a base root op.")
        return []
    ops: list[RecipeOp] = []
    for index, detail in enumerate(getattr(plan, "hybrid_details", []) or []):
        detail_type = _detail_type(detail)
        detail_mode = _detail_source_mode(detail)
        detail_id = _detail_id(detail, index)
        params = _detail_params(detail)
        position = _detail_vector(detail, "position")
        rotation = _detail_vector(detail, "rotation_deg")
        if detail_mode == "compositional":
            ops.extend(_build_hybrid_accent_ops(plan, detail_type, detail_id, params, position, rotation, root_id, warnings))
        else:
            ops.extend(_build_hybrid_feature_ops(plan, detail_type, detail_id, params, position, rotation, root_id, warnings))
    return ops


def _build_hybrid_accent_ops(
    plan: GeomancerPlan,
    detail_type: str,
    detail_id: str,
    params: dict,
    position: list[float],
    rotation: list[float],
    root_id: str,
    warnings: list[str],
) -> list[RecipeOp]:
    if detail_type == "cube":
        op = RecipeOp(
            op="add_box",
            id=detail_id,
            params={
                "size_x_mm": _numeric(params, ("width_mm", "size_x_mm"), _dimension(plan, "overall_width_mm") * 0.14),
                "size_y_mm": _numeric(params, ("depth_mm", "size_y_mm"), _dimension(plan, "overall_depth_mm") * 0.14),
                "size_z_mm": _numeric(params, ("height_mm", "size_z_mm"), _dimension(plan, "overall_height_mm") * 0.14),
                "origin": position or _default_hybrid_origin(plan, detail_type, detail_id),
                "rotation_deg": rotation,
            },
        )
    elif detail_type == "cylinder":
        op = RecipeOp(
            op="add_cylinder",
            id=detail_id,
            params={
                "radius_mm": _numeric(params, ("radius_mm",), min(_dimension(plan, "overall_width_mm"), _dimension(plan, "overall_depth_mm")) * 0.08),
                "height_mm": _numeric(params, ("height_mm",), _dimension(plan, "overall_height_mm") * 0.18),
                "origin": position or _default_hybrid_origin(plan, detail_type, detail_id),
                "rotation_deg": rotation,
            },
        )
    else:
        op = RecipeOp(
            op="add_sphere",
            id=detail_id,
            params={
                "radius_mm": _numeric(params, ("radius_mm",), min(_dimension(plan, "overall_width_mm"), _dimension(plan, "overall_depth_mm"), _dimension(plan, "overall_height_mm")) * 0.12),
                "origin": position or _default_hybrid_origin(plan, detail_type, detail_id),
                "rotation_deg": rotation,
            },
        )
    return [op, RecipeOp(op="boolean_union", id=f"union_{root_id}_{detail_id}", target=root_id, tool=detail_id)]


def _build_hybrid_feature_ops(
    plan: GeomancerPlan,
    detail_type: str,
    detail_id: str,
    params: dict,
    position: list[float],
    rotation: list[float],
    root_id: str,
    warnings: list[str],
) -> list[RecipeOp]:
    if detail_type in {"hole_pattern", "mount_hole", "through_hole"}:
        count = int(_numeric(params, ("count",), 1))
        if detail_type != "hole_pattern":
            count = 1
        diameter = _numeric(params, ("diameter_mm",), max(_dimension(plan, "material_thickness_mm") * 1.25, 4.0))
        layout = str(params.get("layout") or ("corners" if count >= 4 else "center"))
        return [
            RecipeOp(
                op="hole_pattern",
                id=detail_id,
                target=root_id,
                params={
                    "count": count,
                    "diameter_mm": diameter,
                    "layout": layout,
                    "margin_mm": _numeric(params, ("margin_mm",), max(_dimension(plan, "material_thickness_mm") * 2.0, 8.0)),
                },
            )
        ]
    if detail_type == "slot" or detail_type == "opening":
        cutter_id = f"{detail_id}_cutout"
        width = _numeric(params, ("width_mm",), max(_dimension(plan, "overall_width_mm") * 0.18, 12.0))
        depth = _numeric(params, ("depth_mm",), max(_dimension(plan, "overall_depth_mm") * 0.22, 10.0))
        height = _numeric(params, ("height_mm",), max(_dimension(plan, "overall_height_mm") * 0.18, 10.0))
        cutter_origin = position or _default_hybrid_feature_origin(plan, detail_type)
        return [
            RecipeOp(
                op="add_box",
                id=cutter_id,
                params={
                    "size_x_mm": width,
                    "size_y_mm": depth,
                    "size_z_mm": height,
                    "origin": cutter_origin,
                    "rotation_deg": rotation,
                },
            ),
            RecipeOp(op="boolean_difference", id=detail_id, target=root_id, tool=cutter_id),
        ]
    if detail_type == "tab":
        tab_id = detail_id
        return [
            RecipeOp(
                op="add_box",
                id=tab_id,
                params={
                    "size_x_mm": _numeric(params, ("width_mm", "size_x_mm"), max(_dimension(plan, "overall_width_mm") * 0.16, 10.0)),
                    "size_y_mm": _numeric(params, ("thickness_mm", "depth_mm", "size_y_mm"), max(_dimension(plan, "material_thickness_mm"), 3.0)),
                    "size_z_mm": _numeric(params, ("height_mm", "size_z_mm"), max(_dimension(plan, "overall_height_mm") * 0.08, 6.0)),
                    "origin": position or _default_hybrid_feature_origin(plan, detail_type),
                    "rotation_deg": rotation,
                },
            ),
            RecipeOp(op="boolean_union", id=f"union_{root_id}_{tab_id}", target=root_id, tool=tab_id),
        ]
    warnings.append(f"Hybrid feature '{detail_id}' was not mapped to a supported recipe op.")
    return []


def _build_assembly_recipe(plan: GeomancerPlan, warnings: list[str]) -> list[RecipeOp]:
    return _build_composition_recipe(plan, warnings)


def _style_object(plan: GeomancerPlan):
    style = getattr(plan, "style", None)
    if hasattr(style, "to_dict"):
        return style
    return style or {}


def _style_profile(plan: GeomancerPlan) -> str:
    style = _style_object(plan)
    if hasattr(style, "style_profile"):
        return str(getattr(style, "style_profile", "") or "minimal").strip() or "minimal"
    if isinstance(style, dict):
        return str(style.get("style_profile") or "minimal").strip() or "minimal"
    return "minimal"


def _style_recipe_ops(plan: GeomancerPlan, style_profile: str, root_id: str) -> list[RecipeOp]:
    if not root_id or style_profile in {"", "minimal", "low_poly"}:
        return []
    bevel_width_mm, segments, profile = _style_bevel_settings(style_profile)
    if bevel_width_mm <= 0:
        return []
    return [
        RecipeOp(
            op="apply_bevel",
            id=f"{root_id}_{style_profile}_style",
            target=root_id,
            params={
                "width_mm": bevel_width_mm,
                "segments": segments,
                "profile": profile,
            },
        )
    ]


def _style_bevel_settings(style_profile: str) -> tuple[float, int, float]:
    if style_profile == "rounded":
        return 2.2, 4, 0.8
    if style_profile == "industrial":
        return 1.2, 2, 0.35
    if style_profile == "sci_fi":
        return 1.6, 3, 0.6
    return 0.0, 0, 0.0


def _component_to_composition_item(component) -> object:
    params = dict(getattr(component, "params", {}) or {})
    item_type = getattr(component, "type", "")
    position = list(params.pop("position", []) or params.pop("origin", []) or [])
    rotation = list(params.pop("rotation_deg", []) or [])
    operation = str(params.pop("operation", "union") or "union")
    return {
        "id": getattr(component, "id", ""),
        "type": item_type,
        "operation": operation,
        "params": params,
        "position": position,
        "rotation_deg": rotation,
    }


def _composition_item_to_recipe_op(item, plan: GeomancerPlan, index: int) -> RecipeOp | None:
    item_type = _composition_item_type(item)
    if item_type not in {"cube", "cylinder", "sphere"}:
        return None
    item_id = _composition_item_id(item, index)
    position = _composition_item_vector(item, "position", "origin")
    rotation = _composition_item_vector(item, "rotation_deg")
    params = _composition_item_params(item)
    if item_type == "cube":
        return RecipeOp(
            op="add_box",
            id=item_id,
            params={
                "size_x_mm": _composition_numeric(params, ("width_mm", "size_x_mm"), _dimension(plan, "overall_width_mm") * 0.5),
                "size_y_mm": _composition_numeric(params, ("depth_mm", "size_y_mm"), _dimension(plan, "overall_depth_mm") * 0.5),
                "size_z_mm": _composition_numeric(params, ("height_mm", "size_z_mm"), _dimension(plan, "overall_height_mm") * 0.5),
                "origin": position or _default_composition_origin(plan, index),
                "rotation_deg": rotation,
            },
        )
    if item_type == "cylinder":
        return RecipeOp(
            op="add_cylinder",
            id=item_id,
            params={
                "radius_mm": _composition_numeric(params, ("radius_mm",), min(_dimension(plan, "overall_width_mm"), _dimension(plan, "overall_depth_mm")) * 0.14),
                "height_mm": _composition_numeric(params, ("height_mm",), _dimension(plan, "overall_height_mm") * 0.9),
                "vertices": int(_composition_numeric(params, ("vertices",), 32)),
                "origin": position or _default_composition_origin(plan, index),
                "rotation_deg": rotation,
            },
        )
    return RecipeOp(
        op="add_sphere",
        id=item_id,
        params={
            "radius_mm": _composition_numeric(params, ("radius_mm",), min(_dimension(plan, "overall_width_mm"), _dimension(plan, "overall_depth_mm"), _dimension(plan, "overall_height_mm")) * 0.18),
            "origin": position or _default_composition_origin(plan, index),
            "rotation_deg": rotation,
        },
    )


def _composition_item_type(item) -> str:
    return str(item.get("type") if isinstance(item, dict) else getattr(item, "type", "")).strip()


def _composition_item_id(item, index: int) -> str:
    item_id = str(item.get("id") if isinstance(item, dict) else getattr(item, "id", "")).strip()
    return item_id or f"composition_part_{index + 1}"


def _composition_item_operation(item) -> str:
    return str(item.get("operation") if isinstance(item, dict) else getattr(item, "operation", "union") or "union").strip() or "union"


def _composition_item_params(item) -> dict:
    params = item.get("params") if isinstance(item, dict) else getattr(item, "params", {})
    return dict(params or {})


def _composition_item_vector(item, key: str, fallback_key: str | None = None) -> list[float]:
    values = _composition_item_params(item).get(key)
    if values is None and fallback_key is not None:
        values = _composition_item_params(item).get(fallback_key)
    if isinstance(values, (list, tuple)) and len(values) == 3:
        return [float(values[0]), float(values[1]), float(values[2])]
    return []


def _composition_numeric(params: dict, keys: tuple[str, ...], default: float) -> float:
    for key in keys:
        value = params.get(key)
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return default


def _default_composition_origin(plan: GeomancerPlan, index: int) -> list[float]:
    width = _dimension(plan, "overall_width_mm")
    depth = _dimension(plan, "overall_depth_mm")
    height = _dimension(plan, "overall_height_mm")
    offsets = [
        [-width * 0.15, 0.0, 0.0],
        [width * 0.08, 0.0, height * 0.15],
        [width * 0.12, 0.0, -height * 0.1],
    ]
    return offsets[index] if index < len(offsets) else [0.0, 0.0, 0.0]


def _component(plan: GeomancerPlan, component_type: str) -> object:
    for component in plan.components:
        if component.type == component_type:
            return component
    return None


def _component_value(component: object, key: str, default: float | bool = 0.0) -> float | bool:
    if not component:
        return default
    value = getattr(component, "params", {}).get(key, default)
    if isinstance(default, bool):
        return bool(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _component_origin(component: object, default: list[float]) -> list[float]:
    if not component:
        return list(default)
    origin = getattr(component, "params", {}).get("origin")
    if isinstance(origin, (list, tuple)) and len(origin) == 3:
        return [float(origin[0]), float(origin[1]), float(origin[2])]
    return list(default)


def _dimension(plan: GeomancerPlan, key: str, fallback_key: str | None = None, default: float = 0.0) -> float:
    for name in (key, fallback_key):
        if not name:
            continue
        value = plan.dimensions.get(name)
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return default


def _constraint(plan: GeomancerPlan, key: str, default: float) -> float:
    value = plan.constraints.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _recipe_implementation_id(object_type: str, construction_mode: str = "") -> str:
    base_id = RECIPE_IMPLEMENTATION_ID_BY_OBJECT_TYPE.get(object_type, f"{object_type or 'geometry'}_v1")
    if construction_mode == "hybrid" and not base_id.endswith("_hybrid"):
        return f"{base_id}_hybrid"
    return base_id


def _recipe_name_for_object_type(object_type: str) -> str:
    return RECIPE_NAME_BY_OBJECT_TYPE.get(object_type, object_type)


def _validate_ops(ops: list[RecipeOp], errors: list[str]) -> None:
    if not ops:
        errors.append("No deterministic recipe ops were produced.")
        return
    for op in ops:
        if op.op not in RECIPE_OP_VOCABULARY:
            errors.append(f"Unsupported recipe op: {op.op}.")
        if not op.id:
            errors.append(f"Recipe op '{op.op}' is missing an id.")


def _build_result(
    status: str,
    recipe_or_plan: DeterministicRecipe | GeomancerPlan,
    warnings: list[str],
    errors: list[str],
    summary: str,
) -> DeterministicRecipeBuildResult:
    if isinstance(recipe_or_plan, DeterministicRecipe):
        recipe = recipe_or_plan
    else:
        object_type = recipe_or_plan.intent.object_type
        recipe = DeterministicRecipe(
            object_type="assembly" if object_type == "primitive_assembly" else object_type,
            source_family=object_type,
            source_recipe=_recipe_name_for_object_type(object_type),
            execution_recipe=_recipe_name_for_object_type(object_type),
            implementation_id=_recipe_implementation_id(object_type, getattr(recipe_or_plan, "construction_mode", "")),
            warnings=list(recipe_or_plan.warnings),
            notes=list(recipe_or_plan.notes),
        )
    return DeterministicRecipeBuildResult(
        status=status,
        normalized_recipe=recipe,
        warnings=warnings,
        errors=errors,
        summary=summary,
    )
