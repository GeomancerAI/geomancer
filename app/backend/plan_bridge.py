"""Bridge helpers between family plans and the canonical plan schema."""

from __future__ import annotations

from copy import deepcopy

from .families import FAMILY_BY_KEY
from .models import GenerationPlan
from .plan_schema import CanonicalFeature, CanonicalPlan


FAMILY_TO_OBJECT_TYPE = {
    "enclosure": "enclosure",
    "housing_shell": "enclosure",
    "tray_box": "tray",
    "bracket": "bracket",
    "cable_clip": "clip",
    "planter_vessel": "planter",
    "gear": "gear",
    "adapter": "adapter",
    "panel_plate": "plate",
    "spacer_standoff": "standoff",
    "hook_mount": "hook_mount",
    "phone_stand": "phone_stand",
    "primitive_assembly": "assembly",
}


def build_canonical_plan(plan: GenerationPlan) -> CanonicalPlan:
    """Convert a family-specific normalized plan into the canonical structure."""
    object_type = FAMILY_TO_OBJECT_TYPE.get(plan.family, plan.family)
    constraints = {}
    if plan.family == "phone_stand":
        constraints = {
            "device_name": str(plan.features.get("device_name", "")),
            "orientation_preference": str(plan.features.get("orientation_preference", "portrait")),
            "style": str(plan.features.get("style", "minimal")),
            "with_cable_cutout": bool(plan.features.get("with_cable_cutout", False)),
        }
    return CanonicalPlan(
        object_type=object_type,
        source_family=plan.family,
        source_recipe=plan.recipe,
        units="mm",
        dimensions=_canonical_dimensions(plan),
        features=_build_canonical_features(plan),
        constraints=constraints,
        missing_info=[],
        warnings=list(plan.warnings),
        notes=list(plan.assumptions),
    )


def bridge_canonical_plan_to_generation_plan(canonical_plan: CanonicalPlan, source_plan: GenerationPlan | None = None) -> GenerationPlan:
    """Return the deterministic family plan used by the current generator path."""
    if source_plan is None:
        family_key = canonical_plan.source_family or _family_key_for_object_type(canonical_plan.object_type)
        family = FAMILY_BY_KEY[family_key]
        return GenerationPlan(
            family=family.key,
            family_label=family.label,
            recipe=canonical_plan.source_recipe or family.recipe,
            request_text="",
            dimensions=deepcopy(canonical_plan.dimensions),
            features={},
            assumptions=list(canonical_plan.notes),
            warnings=list(canonical_plan.warnings),
            limitations=[],
            classification={},
        )

    bridged_plan = deepcopy(source_plan)
    bridged_plan.dimensions = deepcopy(canonical_plan.dimensions)
    _extend_unique(bridged_plan.warnings, canonical_plan.warnings)
    _extend_unique(bridged_plan.assumptions, canonical_plan.notes)
    return bridged_plan


def _canonical_dimensions(plan: GenerationPlan) -> dict[str, float]:
    dimensions = {key: float(value) for key, value in plan.dimensions.items()}

    if plan.family in {"enclosure", "housing_shell", "tray_box"}:
        dimensions["wall_thickness_mm"] = float(plan.features.get("wall_thickness_mm", dimensions.get("wall_thickness_mm", 0.0)))
        if "base_thickness_mm" in plan.features:
            dimensions["base_thickness_mm"] = float(plan.features.get("base_thickness_mm", 0.0))
        if "lip_height_mm" in plan.features:
            dimensions["lip_height_mm"] = float(plan.features.get("lip_height_mm", 0.0))
    elif plan.family == "cable_clip":
        dimensions["base_length_mm"] = float(plan.features.get("base_length_mm", 0.0))
    elif plan.family == "planter_vessel":
        dimensions["wall_thickness_mm"] = float(plan.features.get("wall_thickness_mm", 0.0))
        dimensions["drain_hole_mm"] = float(plan.features.get("drain_hole_mm", 0.0))
    elif plan.family == "gear":
        dimensions["center_hole_mm"] = float(plan.features.get("center_hole_mm", 0.0))
    elif plan.family == "adapter":
        dimensions["center_hole_mm"] = float(plan.features.get("center_hole_mm", 0.0))
        dimensions["flange_diameter_mm"] = float(plan.features.get("flange_diameter_mm", 0.0))
    elif plan.family == "panel_plate":
        dimensions["hole_diameter_mm"] = float(plan.features.get("hole_diameter_mm", 0.0))
        dimensions["hole_spacing_mm"] = float(plan.features.get("hole_spacing_mm", 0.0))
    elif plan.family == "spacer_standoff":
        dimensions["inner_diameter_mm"] = float(plan.features.get("inner_diameter_mm", 0.0))
    elif plan.family == "hook_mount":
        width = float(plan.dimensions.get("width_mm", plan.dimensions.get("base_width_mm", 0.0)))
        height = float(plan.dimensions.get("height_mm", plan.dimensions.get("base_height_mm", 0.0)))
        depth = float(plan.dimensions.get("depth_mm", plan.dimensions.get("arm_length_mm", 0.0)))
        thickness = float(plan.dimensions.get("thickness_mm", 0.0))
        base_thickness = float(plan.dimensions.get("base_thickness_mm", max(thickness * 1.25, 6.0)))
        hook_length = float(plan.dimensions.get("hook_length_mm", max(depth * 0.72, thickness * 4.0)))
        hook_radius = float(plan.dimensions.get("hook_radius_mm", max(thickness * 1.5, 3.0)))
        hook_angle = float(plan.dimensions.get("hook_angle_deg", 18.0))
        hole_count = int(plan.features.get("hole_count", plan.features.get("mount_hole_count", 2)))
        hole_diameter = float(plan.features.get("hole_diameter_mm", plan.features.get("mount_hole_mm", 5.0)))
        hole_margin = float(plan.features.get("hole_margin_mm", max(thickness * 2.0, hole_diameter * 1.5, 8.0)))
        dimensions["width_mm"] = width
        dimensions["height_mm"] = height
        dimensions["depth_mm"] = depth
        dimensions["thickness_mm"] = thickness
        dimensions["base_thickness_mm"] = base_thickness
        dimensions["hook_length_mm"] = hook_length
        dimensions["hook_radius_mm"] = hook_radius
        dimensions["hook_angle_deg"] = hook_angle
        dimensions["hole_count"] = float(hole_count)
        dimensions["hole_diameter_mm"] = hole_diameter
        dimensions["hole_margin_mm"] = hole_margin
        dimensions["base_width_mm"] = width
        dimensions["base_height_mm"] = height
        dimensions["arm_length_mm"] = depth
        dimensions["hook_drop_mm"] = float(plan.features.get("hook_drop_mm", max(hook_length * 0.35, thickness * 1.5)))
        dimensions["mount_hole_mm"] = hole_diameter
        dimensions["mount_hole_count"] = float(hole_count)
    elif plan.family == "phone_stand":
        dimensions["width_mm"] = float(plan.dimensions.get("width_mm", 0.0))
        dimensions["depth_mm"] = float(plan.dimensions.get("depth_mm", plan.dimensions.get("base_depth_mm", 0.0)))
        dimensions["height_mm"] = float(plan.dimensions.get("height_mm", 0.0))
        dimensions["thickness_mm"] = float(plan.dimensions.get("thickness_mm", plan.dimensions.get("base_thickness_mm", 0.0)))
        dimensions["viewing_angle_deg"] = float(plan.dimensions.get("viewing_angle_deg", plan.dimensions.get("angle_deg", 0.0)))
        dimensions["lip_height_mm"] = float(plan.dimensions.get("lip_height_mm", 0.0))
        dimensions["cradle_depth_mm"] = float(plan.dimensions.get("cradle_depth_mm", plan.dimensions.get("slot_depth_mm", 0.0)))
        dimensions["device_width_mm"] = float(plan.dimensions.get("device_width_mm", plan.dimensions.get("slot_width_mm", 0.0)))
        dimensions["base_depth_mm"] = float(plan.dimensions.get("base_depth_mm", plan.dimensions.get("depth_mm", 0.0)))
        dimensions["base_thickness_mm"] = float(plan.dimensions.get("base_thickness_mm", plan.dimensions.get("thickness_mm", 0.0)))
        dimensions["support_thickness_mm"] = float(plan.dimensions.get("support_thickness_mm", plan.dimensions.get("thickness_mm", 0.0)))
        dimensions["slot_width_mm"] = float(plan.dimensions.get("slot_width_mm", plan.dimensions.get("device_width_mm", 0.0)))
        dimensions["slot_depth_mm"] = float(plan.dimensions.get("slot_depth_mm", plan.dimensions.get("cradle_depth_mm", 0.0)))
        dimensions["angle_deg"] = float(plan.dimensions.get("angle_deg", plan.dimensions.get("viewing_angle_deg", 0.0)))
        dimensions["lip_width_mm"] = float(plan.dimensions.get("lip_width_mm", 0.0))
        dimensions["lip_depth_mm"] = float(plan.dimensions.get("lip_depth_mm", 0.0))
    return dimensions


def _build_canonical_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    builders = {
        "enclosure": _build_enclosure_features,
        "housing_shell": _build_enclosure_features,
        "tray_box": _build_tray_features,
        "bracket": _build_bracket_features,
        "cable_clip": _build_clip_features,
        "planter_vessel": _build_planter_features,
        "gear": _build_gear_features,
        "adapter": _build_adapter_features,
        "panel_plate": _build_plate_features,
        "spacer_standoff": _build_standoff_features,
        "hook_mount": _build_hook_features,
        "phone_stand": _build_phone_stand_features,
        "primitive_assembly": _build_primitive_assembly_features,
    }
    builder = builders.get(plan.family)
    if builder is None:
        return []
    return builder(plan)


def _build_enclosure_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    return [
        CanonicalFeature(
            "shell",
            {
                "width_mm": plan.dimensions.get("width_mm", 0.0),
                "depth_mm": plan.dimensions.get("depth_mm", 0.0),
                "height_mm": plan.dimensions.get("height_mm", 0.0),
                "wall_thickness_mm": float(plan.features.get("wall_thickness_mm", 0.0)),
                "base_thickness_mm": float(
                    plan.features.get(
                        "base_thickness_mm",
                        plan.dimensions.get("base_thickness_mm", plan.features.get("wall_thickness_mm", 0.0)),
                    )
                ),
            },
        ),
        CanonicalFeature("wall", {"thickness_mm": float(plan.features.get("wall_thickness_mm", 0.0))}),
        CanonicalFeature(
            "opening",
            {
                "front_opening": bool(plan.features.get("front_opening")),
                "open_top": bool(plan.features.get("open_top")) or plan.family in {"enclosure", "housing_shell"},
            },
        ),
    ]


def _build_tray_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    features = _build_enclosure_features(plan)
    lip_height = float(plan.features.get("lip_height_mm", 0.0))
    if lip_height > 0:
        features.append(CanonicalFeature("rim", {"lip_height_mm": lip_height}))
    return features


def _build_bracket_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    features = [
        CanonicalFeature(
            "base_leg",
            {
                "length_mm": plan.dimensions.get("base_length_mm", 0.0),
                "width_mm": plan.dimensions.get("flange_width_mm", 0.0),
                "thickness_mm": plan.dimensions.get("thickness_mm", 0.0),
            },
        ),
        CanonicalFeature(
            "vertical_leg",
            {
                "height_mm": plan.dimensions.get("vertical_height_mm", 0.0),
                "width_mm": plan.dimensions.get("flange_width_mm", 0.0),
                "thickness_mm": plan.dimensions.get("thickness_mm", 0.0),
            },
        ),
        CanonicalFeature(
            "hole_pattern",
            {
                "count": int(plan.features.get("hole_count", 0)),
                "diameter_mm": float(plan.features.get("hole_diameter_mm", 0.0)),
            },
        ),
    ]
    if bool(plan.features.get("gusset")):
        features.append(CanonicalFeature("gusset", {"enabled": True}))
    return features


def _build_clip_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    return [
        CanonicalFeature(
            "base_plate",
            {
                "length_mm": plan.features.get("base_length_mm", 0.0),
                "thickness_mm": plan.dimensions.get("thickness_mm", 0.0),
            },
        ),
        CanonicalFeature(
            "back_bar",
            {
                "depth_mm": plan.dimensions.get("depth_mm", 0.0),
                "width_mm": plan.dimensions.get("clip_width_mm", 0.0),
            },
        ),
        CanonicalFeature(
            "clip_arm",
            {
                "opening_mm": plan.dimensions.get("opening_mm", 0.0),
                "cable_diameter_mm": float(plan.features.get("cable_diameter_mm", 0.0)),
            },
        ),
        CanonicalFeature("mount_hole", {"diameter_mm": float(plan.features.get("mount_hole_mm", 0.0))}),
    ]


def _build_planter_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    return [
        CanonicalFeature(
            "vessel_shell",
            {
                "diameter_mm": plan.dimensions.get("diameter_mm", 0.0),
                "height_mm": plan.dimensions.get("height_mm", 0.0),
                "wall_thickness_mm": float(plan.features.get("wall_thickness_mm", 0.0)),
            },
        ),
        CanonicalFeature("drain_hole", {"diameter_mm": float(plan.features.get("drain_hole_mm", 0.0))}),
    ]


def _build_gear_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    return [
        CanonicalFeature(
            "gear_body",
            {
                "diameter_mm": plan.dimensions.get("diameter_mm", 0.0),
                "thickness_mm": plan.dimensions.get("thickness_mm", 0.0),
            },
        ),
        CanonicalFeature("tooth_pattern", {"count": int(plan.features.get("tooth_count", 0))}),
        CanonicalFeature("bore", {"diameter_mm": float(plan.features.get("center_hole_mm", 0.0))}),
    ]


def _build_adapter_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    return [
        CanonicalFeature(
            "adapter_body",
            {
                "large_diameter_mm": plan.dimensions.get("large_diameter_mm", 0.0),
                "small_diameter_mm": plan.dimensions.get("small_diameter_mm", 0.0),
                "length_mm": plan.dimensions.get("length_mm", 0.0),
            },
        ),
        CanonicalFeature("step_transition", {"step_ratio": float(plan.features.get("step_ratio", 0.0))}),
        CanonicalFeature("flange", {"diameter_mm": float(plan.features.get("flange_diameter_mm", 0.0))}),
        CanonicalFeature("through_hole", {"diameter_mm": float(plan.features.get("center_hole_mm", 0.0))}),
    ]


def _build_plate_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    return [
        CanonicalFeature(
            "panel",
            {
                "width_mm": plan.dimensions.get("width_mm", 0.0),
                "height_mm": plan.dimensions.get("height_mm", 0.0),
                "thickness_mm": plan.dimensions.get("thickness_mm", 0.0),
            },
        ),
        CanonicalFeature(
            "hole_pattern",
            {
                "diameter_mm": float(plan.features.get("hole_diameter_mm", 0.0)),
                "spacing_mm": float(plan.features.get("hole_spacing_mm", 0.0)),
                "pattern": str(plan.features.get("hole_pattern", "none")),
            },
        ),
    ]


def _build_standoff_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    return [
        CanonicalFeature(
            "standoff_body",
            {
                "outer_diameter_mm": plan.dimensions.get("outer_diameter_mm", 0.0),
                "length_mm": plan.dimensions.get("length_mm", 0.0),
                "profile": str(plan.features.get("profile", "round")),
            },
        ),
        CanonicalFeature(
            "center_hole",
            {
                "inner_diameter_mm": float(plan.features.get("inner_diameter_mm", 0.0)),
            },
        ),
    ]


def _build_hook_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    return [
        CanonicalFeature(
            "hook_mount_body",
            {
                "width_mm": plan.dimensions.get("width_mm", plan.dimensions.get("base_width_mm", 0.0)),
                "height_mm": plan.dimensions.get("height_mm", plan.dimensions.get("base_height_mm", 0.0)),
                "depth_mm": plan.dimensions.get("depth_mm", plan.dimensions.get("arm_length_mm", 0.0)),
                "thickness_mm": plan.dimensions.get("thickness_mm", 0.0),
                "base_thickness_mm": plan.dimensions.get("base_thickness_mm", 0.0),
                "hook_length_mm": plan.dimensions.get("hook_length_mm", plan.dimensions.get("depth_mm", 0.0)),
                "hook_radius_mm": plan.dimensions.get("hook_radius_mm", 0.0),
                "hook_angle_deg": plan.dimensions.get("hook_angle_deg", 18.0),
            },
        ),
        CanonicalFeature(
            "mounting_holes",
            {
                "count": int(plan.features.get("hole_count", plan.features.get("mount_hole_count", 0))),
                "diameter_mm": float(plan.features.get("hole_diameter_mm", plan.features.get("mount_hole_mm", 0.0))),
                "margin_mm": float(plan.features.get("hole_margin_mm", 0.0)),
            },
        ),
    ]


def _build_phone_stand_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    width = float(plan.dimensions.get("width_mm", 0.0))
    depth = float(plan.dimensions.get("depth_mm", plan.dimensions.get("base_depth_mm", 0.0)))
    height = float(plan.dimensions.get("height_mm", 0.0))
    thickness = float(plan.dimensions.get("thickness_mm", plan.dimensions.get("base_thickness_mm", 0.0)))
    viewing_angle_deg = float(plan.dimensions.get("viewing_angle_deg", plan.dimensions.get("angle_deg", 0.0)))
    lip_height = float(plan.dimensions.get("lip_height_mm", 0.0))
    cradle_depth = float(plan.dimensions.get("cradle_depth_mm", plan.dimensions.get("slot_depth_mm", 0.0)))
    device_width = float(plan.dimensions.get("device_width_mm", plan.dimensions.get("slot_width_mm", 0.0)))
    cable_notch = bool(plan.features.get("cable_notch", plan.features.get("with_cable_cutout", False)))
    features = [
        CanonicalFeature(
            "base_plate",
            {
                "width_mm": width,
                "depth_mm": depth,
                "thickness_mm": thickness,
            },
        ),
        CanonicalFeature(
            "angled_support",
            {
                "height_mm": height,
                "viewing_angle_deg": viewing_angle_deg,
                "thickness_mm": float(plan.dimensions.get("support_thickness_mm", thickness)),
                "cradle_depth_mm": cradle_depth,
                "device_width_mm": device_width,
            },
        ),
        CanonicalFeature(
            "retaining_lip",
            {
                "width_mm": float(plan.dimensions.get("lip_width_mm", min(max(device_width + 18.0, width * 0.6), width - 12.0) if width > 0 else 0.0)),
                "depth_mm": float(plan.dimensions.get("lip_depth_mm", max(thickness * 0.9, 4.0))),
                "height_mm": lip_height,
            },
        ),
        CanonicalFeature("cable_cutout", {"enabled": cable_notch}),
    ]
    if cable_notch:
        features[-1].params.update(
            {
                "width_mm": float(plan.features.get("cable_cutout_width_mm", max(device_width * 0.25, 6.0))),
                "height_mm": float(plan.features.get("cable_cutout_height_mm", max(thickness * 2.0, 6.0))),
                "depth_mm": float(plan.features.get("cable_cutout_depth_mm", max(thickness * 2.5, 8.0))),
            }
        )
    return features


def _build_primitive_assembly_features(plan: GenerationPlan) -> list[CanonicalFeature]:
    features: list[CanonicalFeature] = []
    if bool(plan.features.get("include_cube")):
        features.append(CanonicalFeature("cube", {"enabled": True}))
    if bool(plan.features.get("include_cylinder")):
        features.append(CanonicalFeature("cylinder", {"enabled": True}))
    if bool(plan.features.get("include_sphere")):
        features.append(CanonicalFeature("sphere", {"enabled": True}))
    return features


def _family_key_for_object_type(object_type: str) -> str:
    for family_key, mapped_object_type in FAMILY_TO_OBJECT_TYPE.items():
        if mapped_object_type == object_type:
            return family_key
    return "primitive_assembly"


def _extend_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        if value and value not in target:
            target.append(value)
