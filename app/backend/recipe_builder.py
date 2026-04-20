"""Canonical deterministic recipe builder for Geomancer backend generation."""

from __future__ import annotations

from .plan_schema import CanonicalPlan
from .recipe_schema import (
    DeterministicRecipe,
    DeterministicRecipeBuildResult,
    RecipeOp,
    RECIPE_OP_VOCABULARY,
)


def build_deterministic_recipe(plan: CanonicalPlan) -> DeterministicRecipeBuildResult:
    """Convert a validated canonical plan into a bounded deterministic recipe."""
    warnings = list(plan.warnings)
    errors: list[str] = []

    if not plan.object_type:
        errors.append("Canonical plan is missing an object type.")
        return _build_result("invalid", plan, warnings, errors, "Canonical recipe build failed.")

    builders = {
        "enclosure": _build_enclosure_recipe,
        "tray": _build_tray_recipe,
        "bracket": _build_bracket_recipe,
        "clip": _build_clip_recipe,
        "planter": _build_planter_recipe,
        "gear": _build_gear_recipe,
        "adapter": _build_adapter_recipe,
        "plate": _build_plate_recipe,
        "standoff": _build_standoff_recipe,
        "hook_mount": _build_hook_recipe,
        "phone_stand": _build_phone_stand_recipe,
        "assembly": _build_assembly_recipe,
    }
    builder = builders.get(plan.object_type)
    if builder is None:
        errors.append(f"Unsupported canonical object type for recipe building: {plan.object_type}.")
        return _build_result("invalid", plan, warnings, errors, "Canonical recipe build failed.")

    recipe = DeterministicRecipe(
        object_type=plan.object_type,
        source_family=plan.source_family,
        source_recipe=plan.source_recipe,
        execution_recipe=plan.source_recipe,
        implementation_id=_family_implementation_id(plan.object_type, plan.source_family, plan.source_recipe),
        warnings=warnings,
        notes=list(plan.notes),
    )
    recipe.ops = builder(plan, recipe.warnings)
    if not recipe.ops:
        errors.append(f"No deterministic recipe ops were produced for {plan.object_type}.")
        return _build_result("invalid", recipe, warnings, errors, "Canonical recipe build failed.")

    _validate_ops(recipe.ops, errors)
    if errors:
        return _build_result("invalid", recipe, warnings, errors, "Canonical recipe build failed.")

    summary = f"Built deterministic recipe for {plan.object_type} with {len(recipe.ops)} ops."
    return DeterministicRecipeBuildResult(
        status="ready",
        normalized_recipe=recipe,
        warnings=warnings,
        errors=[],
        summary=summary,
    )


def _build_enclosure_recipe(plan: CanonicalPlan, warnings: list[str]) -> list[RecipeOp]:
    shell = _feature(plan, "shell")
    opening = _feature(plan, "opening")
    wall = _feature(plan, "wall")
    base_thickness = float(shell.get("base_thickness_mm", plan.dimensions.get("base_thickness_mm", wall.get("thickness_mm", 0.0))))
    shell_params = {
        "width_mm": shell.get("width_mm", 0.0),
        "depth_mm": shell.get("depth_mm", 0.0),
        "height_mm": shell.get("height_mm", 0.0),
        "wall_thickness_mm": shell.get("wall_thickness_mm", wall.get("thickness_mm", 0.0)),
        "base_thickness_mm": base_thickness,
        "open_top": bool(opening.get("open_top", False)) or plan.object_type == "enclosure",
        "front_opening": bool(opening.get("front_opening", False)),
    }
    ops = [RecipeOp(op="shell", id="shell", params=shell_params)]
    if shell_params["front_opening"]:
        opening_width = plan.dimensions.get("opening_width_mm", max(shell_params["width_mm"] * 0.55, 20.0))
        opening_height = plan.dimensions.get("opening_height_mm", max(shell_params["height_mm"] * 0.45, 20.0))
        ops.append(
            RecipeOp(
                op="boolean_difference",
                id="front_opening",
                target="shell",
                tool="front_opening",
                params={"opening_width_mm": opening_width, "opening_height_mm": opening_height},
            )
        )
    if shell_params["open_top"] and plan.object_type != "tray":
        ops.append(RecipeOp(op="flatten_bottom", id="open_top", target="shell", params={"mode": "open_top"}))
    return ops


def _build_tray_recipe(plan: CanonicalPlan, warnings: list[str]) -> list[RecipeOp]:
    ops = _build_enclosure_recipe(plan, warnings)
    return ops


def _build_bracket_recipe(plan: CanonicalPlan, warnings: list[str]) -> list[RecipeOp]:
    base = _feature(plan, "base_leg")
    vertical = _feature(plan, "vertical_leg")
    holes = _feature(plan, "hole_pattern")
    if any(feature.type == "gusset" for feature in plan.features):
        warnings.append("Bracket gusset was deferred while bracket body construction uses a single coherent mesh.")
    ops = [
        RecipeOp(
            op="bracket_body",
            id="bracket_body",
            params={
                "base_length_mm": base.get("length_mm", 0.0),
                "flange_width_mm": base.get("width_mm", 0.0),
                "vertical_height_mm": vertical.get("height_mm", 0.0),
                "thickness_mm": base.get("thickness_mm", 0.0),
            },
        ),
    ]
    if holes:
        ops.append(
            RecipeOp(
                op="hole_pattern",
                id="mount_holes",
                target="bracket_body",
                params={
                    "count": int(holes.get("count", 0)),
                    "diameter_mm": float(holes.get("diameter_mm", 0.0)),
                    "layout": "rectangular",
                },
            )
        )
    return ops


def _build_clip_recipe(plan: CanonicalPlan, warnings: list[str]) -> list[RecipeOp]:
    base = _feature(plan, "base_plate")
    back_bar = _feature(plan, "back_bar")
    arm = _feature(plan, "clip_arm")
    mount = _feature(plan, "mount_hole")
    half_span = max(arm.get("opening_mm", 0.0) / 2.0, 1.0)
    ops = [
        RecipeOp(
            op="add_box",
            id="base_plate",
            params={
                "size_x_mm": base.get("length_mm", 0.0),
                "size_y_mm": base.get("thickness_mm", 0.0),
                "size_z_mm": back_bar.get("width_mm", 0.0),
            },
        ),
        RecipeOp(
            op="add_box",
            id="back_bar",
            params={
                "size_x_mm": back_bar.get("width_mm", 0.0),
                "size_y_mm": back_bar.get("depth_mm", 0.0),
                "size_z_mm": max(back_bar.get("width_mm", 0.0) * 0.6, 1.0),
            },
        ),
        RecipeOp(
            op="add_box",
            id="arm_left",
            params={"size_x_mm": arm.get("opening_mm", 0.0), "size_y_mm": back_bar.get("depth_mm", 0.0), "size_z_mm": max(back_bar.get("width_mm", 0.0) * 0.6, 1.0)},
        ),
        RecipeOp(
            op="add_box",
            id="arm_right",
            params={"size_x_mm": arm.get("opening_mm", 0.0), "size_y_mm": back_bar.get("depth_mm", 0.0), "size_z_mm": max(back_bar.get("width_mm", 0.0) * 0.6, 1.0)},
        ),
        RecipeOp(op="boolean_union", id="join_clip", target="base_plate", tool="back_bar"),
        RecipeOp(op="boolean_union", id="join_clip_left", target="base_plate", tool="arm_left"),
        RecipeOp(op="boolean_union", id="join_clip_right", target="base_plate", tool="arm_right"),
    ]
    if mount.get("diameter_mm", 0.0) > 0:
        ops.append(
            RecipeOp(
                op="add_hole",
                id="mount_hole",
                target="base_plate",
                params={"diameter_mm": mount.get("diameter_mm", 0.0), "count": 1, "layout": "center"},
            )
        )
    warnings.append(f"Clip opening modeled as a symmetric half-span of {half_span:.1f} mm.")
    return ops


def _build_planter_recipe(plan: CanonicalPlan, warnings: list[str]) -> list[RecipeOp]:
    body = _feature(plan, "vessel_shell")
    drain = _feature(plan, "drain_hole")
    ops = [
        RecipeOp(
            op="shell",
            id="vessel_shell",
            params={
                "diameter_mm": body.get("diameter_mm", 0.0),
                "height_mm": body.get("height_mm", 0.0),
                "wall_thickness_mm": body.get("wall_thickness_mm", 0.0),
                "open_top": True,
            },
        )
    ]
    if drain.get("diameter_mm", 0.0) > 0:
        ops.append(
            RecipeOp(
                op="add_hole",
                id="drain_hole",
                target="vessel_shell",
                params={"diameter_mm": drain.get("diameter_mm", 0.0), "count": 1, "layout": "center_bottom"},
            )
        )
    return ops


def _build_gear_recipe(plan: CanonicalPlan, warnings: list[str]) -> list[RecipeOp]:
    body = _feature(plan, "gear_body")
    teeth = _feature(plan, "tooth_pattern")
    bore = _feature(plan, "bore")
    tooth_count = int(teeth.get("count", 0))
    diameter = body.get("diameter_mm", 0.0)
    ring_radius = (diameter / 2.0) * 0.88
    ops = [
        RecipeOp(
            op="add_cylinder",
            id="gear_body",
            params={"radius_mm": diameter / 2.0, "height_mm": body.get("thickness_mm", 0.0), "origin": [0.0, 0.0, 0.0]},
        )
    ]
    for index in range(max(tooth_count, 0)):
        angle = (360.0 / tooth_count) * index if tooth_count else 0.0
        ops.append(
            RecipeOp(
                op="add_box",
                id=f"tooth_{index + 1:02d}",
                params={
                    "size_x_mm": max(diameter * 0.10, 3.0),
                    "size_y_mm": max((diameter * 3.14159) / max(tooth_count * 3.0, 1.0), 2.0),
                    "size_z_mm": body.get("thickness_mm", 0.0),
                    "origin": [ring_radius, 0.0, 0.0],
                    "rotation_deg": [0.0, 0.0, angle],
                },
            )
        )
        ops.append(RecipeOp(op="boolean_union", id=f"join_tooth_{index + 1:02d}", target="gear_body", tool=f"tooth_{index + 1:02d}"))
    if bore.get("diameter_mm", 0.0) > 0:
        ops.append(
            RecipeOp(
                op="add_hole",
                id="bore",
                target="gear_body",
                params={"diameter_mm": bore.get("diameter_mm", 0.0), "count": 1, "layout": "center"},
            )
        )
    return ops


def _build_adapter_recipe(plan: CanonicalPlan, warnings: list[str]) -> list[RecipeOp]:
    body = _feature(plan, "adapter_body")
    step = _feature(plan, "step_transition")
    flange = _feature(plan, "flange")
    through = _feature(plan, "through_hole")
    large = body.get("large_diameter_mm", 0.0)
    small = body.get("small_diameter_mm", 0.0)
    length = body.get("length_mm", 0.0)
    top_len = length * float(step.get("step_ratio", 0.5))
    bottom_len = length - top_len
    ops = [
        RecipeOp(op="add_cylinder", id="adapter_large", params={"radius_mm": large / 2.0, "height_mm": top_len, "origin": [0.0, 0.0, (length / 2.0) - (top_len / 2.0)]}),
        RecipeOp(op="add_cylinder", id="adapter_small", params={"radius_mm": small / 2.0, "height_mm": bottom_len, "origin": [0.0, 0.0, -(length / 2.0) + (bottom_len / 2.0)]}),
        RecipeOp(op="boolean_union", id="join_adapter", target="adapter_large", tool="adapter_small"),
    ]
    if flange.get("diameter_mm", 0.0) > max(large, small):
        ops.append(RecipeOp(op="add_cylinder", id="adapter_flange", params={"radius_mm": flange.get("diameter_mm", 0.0) / 2.0, "height_mm": max(length * 0.15, 3.0), "origin": [0.0, 0.0, (length / 2.0) - max(length * 0.075, 1.5)]}))
        ops.append(RecipeOp(op="boolean_union", id="join_flange", target="adapter_large", tool="adapter_flange"))
    if through.get("diameter_mm", 0.0) > 0:
        ops.append(RecipeOp(op="add_hole", id="through_hole", target="adapter_large", params={"diameter_mm": through.get("diameter_mm", 0.0), "count": 1, "layout": "center"}))
    return ops


def _build_plate_recipe(plan: CanonicalPlan, warnings: list[str]) -> list[RecipeOp]:
    panel = _feature(plan, "panel")
    hole_pattern = _feature(plan, "hole_pattern")
    ops = [RecipeOp(op="add_box", id="panel", params={"size_x_mm": panel.get("width_mm", 0.0), "size_y_mm": panel.get("thickness_mm", 0.0), "size_z_mm": panel.get("height_mm", 0.0), "origin": [0.0, 0.0, 0.0]})]
    diameter = float(hole_pattern.get("diameter_mm", 0.0))
    if diameter > 0:
        ops.append(
            RecipeOp(
                op="hole_pattern",
                id="panel_holes",
                target="panel",
                params={
                    "diameter_mm": diameter,
                    "spacing_mm": float(hole_pattern.get("spacing_mm", 0.0)),
                    "pattern": str(hole_pattern.get("pattern", "none")),
                },
            )
        )
    return ops


def _build_standoff_recipe(plan: CanonicalPlan, warnings: list[str]) -> list[RecipeOp]:
    body = _feature(plan, "standoff_body")
    hole = _feature(plan, "center_hole")
    vertices = 6 if body.get("profile", "round") == "hex" else 32
    ops = [RecipeOp(op="add_cylinder", id="standoff_body", params={"vertices": vertices, "radius_mm": body.get("outer_diameter_mm", 0.0) / 2.0, "height_mm": body.get("length_mm", 0.0), "origin": [0.0, 0.0, 0.0]})]
    if hole.get("inner_diameter_mm", 0.0) > 0:
        ops.append(RecipeOp(op="add_hole", id="center_hole", target="standoff_body", params={"diameter_mm": hole.get("inner_diameter_mm", 0.0), "count": 1, "layout": "center"}))
    return ops


def _build_hook_recipe(plan: CanonicalPlan, warnings: list[str]) -> list[RecipeOp]:
    body = _feature(plan, "hook_mount_body")
    mounts = _feature(plan, "mounting_holes")
    if not body:
        base = _feature(plan, "base_plate")
        arm = _feature(plan, "hook_arm")
        lip = _feature(plan, "hook_lip")
        body = {
            "width_mm": base.get("width_mm", 0.0),
            "height_mm": base.get("height_mm", 0.0),
            "depth_mm": arm.get("arm_length_mm", 0.0),
            "thickness_mm": base.get("thickness_mm", 0.0),
            "base_thickness_mm": base.get("thickness_mm", 0.0),
            "hook_length_mm": arm.get("arm_length_mm", 0.0),
            "hook_radius_mm": lip.get("thickness_mm", 0.0),
            "hook_angle_deg": 18.0,
        }
    ops = [
        RecipeOp(
            op="hook_mount_body",
            id="hook_mount_body",
            params={
                "width_mm": body.get("width_mm", 0.0),
                "height_mm": body.get("height_mm", 0.0),
                "depth_mm": body.get("depth_mm", 0.0),
                "thickness_mm": body.get("thickness_mm", 0.0),
                "base_thickness_mm": body.get("base_thickness_mm", 0.0),
                "hook_length_mm": body.get("hook_length_mm", 0.0),
                "hook_radius_mm": body.get("hook_radius_mm", 0.0),
                "hook_angle_deg": float(body.get("hook_angle_deg", 18.0)),
            },
        ),
    ]
    hole_diameter = float(mounts.get("diameter_mm", 0.0))
    if hole_diameter > 0:
        ops.append(
            RecipeOp(
                op="hole_pattern",
                id="mount_holes",
                target="hook_mount_body",
                params={
                    "count": int(mounts.get("count", 0)) or 2,
                    "diameter_mm": hole_diameter,
                    "layout": "wall_vertical_pair",
                    "margin_mm": float(mounts.get("margin_mm", 0.0)),
                },
            )
        )
    return ops


def _build_phone_stand_recipe(plan: CanonicalPlan, warnings: list[str]) -> list[RecipeOp]:
    cable = _feature(plan, "cable_cutout")
    with_cable_cutout = bool(cable.get("enabled")) or bool(plan.constraints.get("with_cable_cutout", False))

    width = float(plan.dimensions.get("width_mm", 0.0))
    depth = float(plan.dimensions.get("depth_mm", plan.dimensions.get("base_depth_mm", 0.0)))
    height = float(plan.dimensions.get("height_mm", 0.0))
    thickness = float(plan.dimensions.get("thickness_mm", plan.dimensions.get("base_thickness_mm", 0.0)))
    viewing_angle_deg = float(plan.dimensions.get("viewing_angle_deg", plan.dimensions.get("angle_deg", 65.0)))
    lip_height = float(plan.dimensions.get("lip_height_mm", max(thickness * 0.8, 4.0)))
    cradle_depth = float(plan.dimensions.get("cradle_depth_mm", plan.dimensions.get("slot_depth_mm", max(thickness * 4.0, 18.0))))
    device_width = float(plan.dimensions.get("device_width_mm", plan.dimensions.get("slot_width_mm", 0.0)))

    ops = [
        RecipeOp(
            op="phone_stand_body",
            id="phone_stand_body",
            params={
                "width_mm": width,
                "depth_mm": depth,
                "height_mm": height,
                "thickness_mm": thickness,
                "viewing_angle_deg": viewing_angle_deg,
                "lip_height_mm": lip_height,
                "cradle_depth_mm": cradle_depth,
                "device_width_mm": device_width,
            },
        )
    ]

    if with_cable_cutout:
        cable_width = float(cable.get("width_mm", max(device_width * 0.25, 6.0)))
        cable_depth = float(cable.get("depth_mm", max(thickness * 2.5, 8.0)))
        cable_height = float(cable.get("height_mm", max(thickness * 1.2, 6.0)))
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


def _build_assembly_recipe(plan: CanonicalPlan, warnings: list[str]) -> list[RecipeOp]:
    ops: list[RecipeOp] = []
    if plan.dimensions.get("width_mm", 0.0) > 0:
        ops.append(
            RecipeOp(
                op="add_box",
                id="cube_part",
                params={
                    "size_x_mm": plan.dimensions.get("width_mm", 0.0) * 0.5,
                    "size_y_mm": plan.dimensions.get("depth_mm", 0.0) * 0.5,
                    "size_z_mm": plan.dimensions.get("height_mm", 0.0) * 0.5,
                    "origin": [-(plan.dimensions.get("width_mm", 0.0) * 0.35), 0.0, 0.0],
                },
            )
        )
    if plan.dimensions.get("depth_mm", 0.0) > 0:
        ops.append(
            RecipeOp(
                op="add_cylinder",
                id="cylinder_part",
                params={"radius_mm": min(plan.dimensions.get("width_mm", 0.0), plan.dimensions.get("depth_mm", 0.0)) * 0.14, "height_mm": plan.dimensions.get("height_mm", 0.0) * 0.9, "origin": [0.0, 0.0, 0.0]},
            )
        )
    if plan.dimensions.get("height_mm", 0.0) > 0:
        ops.append(
            RecipeOp(
                op="add_sphere",
                id="sphere_part",
                params={"radius_mm": min(plan.dimensions.get("width_mm", 0.0), plan.dimensions.get("depth_mm", 0.0), plan.dimensions.get("height_mm", 0.0)) * 0.18, "origin": [plan.dimensions.get("width_mm", 0.0) * 0.35, 0.0, plan.dimensions.get("height_mm", 0.0) * 0.1]},
            )
        )
    return ops


def _feature(plan: CanonicalPlan, feature_type: str) -> dict[str, object]:
    for feature in plan.features:
        if feature.type == feature_type:
            return dict(feature.params)
    return {}


def _family_implementation_id(object_type: str, source_family: str, source_recipe: str) -> str:
    implementation_ids = {
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
    return implementation_ids.get(object_type) or implementation_ids.get(source_family) or f"{source_recipe or object_type or 'geometry'}_v1"


def _validate_ops(ops: list[RecipeOp], errors: list[str]) -> None:
    for op in ops:
        if op.op not in RECIPE_OP_VOCABULARY:
            errors.append(f"Unsupported recipe op: {op.op}.")
        if not op.id:
            errors.append(f"Recipe op '{op.op}' is missing an id.")


def _build_result(status: str, recipe_or_plan: DeterministicRecipe | CanonicalPlan, warnings: list[str], errors: list[str], summary: str) -> DeterministicRecipeBuildResult:
    if isinstance(recipe_or_plan, DeterministicRecipe):
        recipe = recipe_or_plan
    else:
        recipe = DeterministicRecipe(
            object_type=recipe_or_plan.object_type,
            source_family=recipe_or_plan.source_family,
            source_recipe=recipe_or_plan.source_recipe,
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
