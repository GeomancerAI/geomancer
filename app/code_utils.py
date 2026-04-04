"""Utilities for extracting and saving Blender Python code."""

from __future__ import annotations

import re
import json
from pathlib import Path

from prompt_builder import BLENDER_TEMPLATE


SAFE_FALLBACK_SCRIPT = """import bpy

# Clear all objects from the default scene.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def mm(value):
    return value / 1000.0

# Add a simple fallback sphere using the strict allowlisted path.
bpy.ops.mesh.primitive_uv_sphere_add(radius=mm(80), location=(0.0, 0.0, 0.0))
obj = bpy.context.active_object
obj.name = "Geomancer_Fallback_Sphere"
"""
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BANNED_PATTERNS_PATH = PROJECT_ROOT / "blender" / "rules" / "banned_patterns.json"


def extract_python_code(model_output: str) -> str:
    """Extract Blender Python code from model output.

    The model may reply with either raw Python or fenced markdown. If the
    extracted text does not appear to use bpy, a safe fallback script is used.
    """
    if not model_output or not model_output.strip():
        return SAFE_FALLBACK_SCRIPT

    fence_match = re.search(r"```(?:python)?\s*(.*?)```", model_output, re.DOTALL | re.IGNORECASE)
    candidate = fence_match.group(1).strip() if fence_match else model_output.strip()

    # Trim common accidental prose before the first import/useful line.
    lines = candidate.splitlines()
    cleaned_lines: list[str] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not started and (stripped.startswith("import ") or "bpy" in stripped):
            started = True
        if started:
            cleaned_lines.append(line)

    cleaned_code = "\n".join(cleaned_lines).strip() if cleaned_lines else candidate

    if not contains_bpy_usage(cleaned_code):
        return SAFE_FALLBACK_SCRIPT

    return cleaned_code + ("\n" if not cleaned_code.endswith("\n") else "")


def extract_template_values(model_output: str) -> dict:
    """Extract the template parameter JSON from model output."""
    default_values = {
        "radius": 80.0,
        "face_outer_diameter_mm": 90.0,
        "face_inner_diameter_mm": 67.5,
        "face_recess_depth_mm": 10.0,
        "thickness": 3.0,
    }

    if not model_output or not model_output.strip():
        return default_values

    candidate = model_output.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", candidate, re.DOTALL | re.IGNORECASE)
    if fence_match:
        candidate = fence_match.group(1).strip()

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return default_values

    if not isinstance(parsed, dict):
        return default_values

    values = default_values.copy()
    for key in values:
        values[key] = normalize_number(parsed.get(key)) or values[key]

    return values


def build_script_from_template(template_values: dict, plan: dict) -> str:
    """Build the final Blender script from the fixed local template."""
    plan_diameter = normalize_number(plan.get("diameter_mm"))
    plan_opening_diameter = normalize_number(plan.get("front_opening_diameter_mm"))
    plan_thickness = normalize_number(plan.get("shell_thickness_mm"))
    front_axis = str(plan.get("front_axis", "+Y")).strip().upper()

    radius = (plan_diameter / 2.0) if plan_diameter else template_values["radius"]
    flatten_bottom = bool(plan.get("flatten_bottom", False))
    thickness = plan_thickness if plan_thickness is not None else template_values["thickness"]
    face_outer_diameter = normalize_number(template_values.get("face_outer_diameter_mm"))
    face_inner_diameter = normalize_number(template_values.get("face_inner_diameter_mm"))
    face_recess_depth = normalize_number(template_values.get("face_recess_depth_mm"))

    if plan_opening_diameter is not None:
        if face_outer_diameter is None:
            face_outer_diameter = plan_opening_diameter
        if face_inner_diameter is None:
            face_inner_diameter = plan_opening_diameter * 0.75

    face_outer_diameter = face_outer_diameter if face_outer_diameter is not None else 90.0
    face_inner_diameter = face_inner_diameter if face_inner_diameter is not None else face_outer_diameter * 0.75
    face_recess_depth = face_recess_depth if face_recess_depth is not None else 10.0

    face_outer_radius = face_outer_diameter / 2.0
    face_inner_radius = face_inner_diameter / 2.0

    # Clamp the face features so they remain valid on the sphere.
    face_outer_radius = min(max(face_outer_radius, 1.0), max(radius - 1.0, 1.0))
    face_inner_radius = min(max(face_inner_radius, 1.0), max(face_outer_radius - 1.0, 1.0))
    face_recess_depth = max(1.0, min(face_recess_depth, radius * 0.5))
    thickness = max(thickness, 0.0)

    # Recess cut: shallow cap removal for the outer ring.
    recess_plane_y = (radius ** 2 - face_outer_radius ** 2) ** 0.5
    face_recess_offset = radius - (face_recess_depth / 2.0)

    # Inner hole cut: blind hole from the front shell into the interior cavity.
    face_hole_depth = radius * 1.2
    face_hole_offset = radius - (face_hole_depth / 2.0)

    if front_axis != "+Y":
        # Template mode currently only guarantees correct +Y behavior.
        face_recess_offset = abs(face_recess_offset)
        face_hole_offset = abs(face_hole_offset)

    # Bottom flatten is a shallow cap removal so the part rests on a surface.
    flatten_depth = max(4.0, min(8.0, radius * 0.08))
    bottom_cut_plane_z = -(radius - flatten_depth)
    features = normalize_features(
        plan,
        thickness=thickness,
        face_outer_radius=face_outer_radius,
        face_inner_radius=face_inner_radius,
        face_recess_depth=face_recess_depth,
        face_recess_offset=face_recess_offset,
        face_hole_depth=face_hole_depth,
        face_hole_offset=face_hole_offset,
        radius=radius,
        flatten_bottom=flatten_bottom,
        bottom_cut_plane_z=bottom_cut_plane_z,
    )
    feature_blocks = build_feature_blocks(features, radius=radius)

    return BLENDER_TEMPLATE.format(
        radius=radius,
        feature_blocks=feature_blocks,
    )


def extract_json_plan(model_output: str) -> dict:
    """Extract a compact JSON modeling plan from model output."""
    if not model_output or not model_output.strip():
        return default_plan()

    candidate = model_output.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", candidate, re.DOTALL | re.IGNORECASE)
    if fence_match:
        candidate = fence_match.group(1).strip()

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return default_plan()

    if not isinstance(parsed, dict):
        return default_plan()

    plan = default_plan()
    plan["primitive"] = str(parsed.get("primitive", plan["primitive"])).strip() or plan["primitive"]
    plan["diameter_mm"] = normalize_number(parsed.get("diameter_mm"))
    plan["shell_thickness_mm"] = normalize_number(parsed.get("shell_thickness_mm"))
    plan["front_opening_diameter_mm"] = normalize_number(parsed.get("front_opening_diameter_mm"))
    plan["flatten_bottom"] = bool(parsed.get("flatten_bottom", plan["flatten_bottom"]))

    front_axis = str(parsed.get("front_axis", plan["front_axis"])).strip().upper()
    plan["front_axis"] = front_axis if front_axis in {"+Y", "-Y", "+Z", "-Z", "+X", "-X"} else "+Y"

    operations = parsed.get("operations", [])
    if isinstance(operations, list):
        plan["operations"] = [str(item).strip() for item in operations if str(item).strip()][:6]

    features = parsed.get("features", [])
    if isinstance(features, list):
        plan["features"] = [feature for feature in features if isinstance(feature, dict)]

    return plan


def default_plan() -> dict:
    """Return a safe default plan object."""
    return {
        "primitive": "unknown",
        "diameter_mm": None,
        "shell_thickness_mm": None,
        "front_opening_diameter_mm": None,
        "flatten_bottom": False,
        "front_axis": "+Y",
        "operations": [],
        "features": [],
    }


def normalize_number(value):
    """Normalize a numeric plan field to float or None."""
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_features(plan: dict, **derived_values) -> list[dict]:
    """Normalize feature definitions while keeping backward compatibility."""
    raw_features = plan.get("features", [])
    normalized: list[dict] = []

    if isinstance(raw_features, list):
        for feature in raw_features:
            if not isinstance(feature, dict):
                continue
            feature_type = str(feature.get("type", "")).strip()
            if feature_type not in {"shell", "recess", "hole_blind", "hole_through", "flatten_bottom"}:
                continue
            normalized.append({
                "type": feature_type,
                "parameters": feature.get("parameters", {}),
            })

    if normalized:
        return normalized

    # Backward-compatible fallback from the current top-level plan fields.
    fallback_features: list[dict] = []
    thickness = derived_values.get("thickness", 0.0)
    if thickness > 0:
        fallback_features.append({
            "type": "shell",
            "parameters": {"thickness": thickness},
        })

    fallback_features.append({
        "type": "recess",
        "parameters": {
            "face_outer_radius": derived_values["face_outer_radius"],
            "face_recess_depth": derived_values["face_recess_depth"],
            "face_recess_offset": derived_values["face_recess_offset"],
        },
    })

    fallback_features.append({
        "type": "hole_blind",
        "parameters": {
            "face_inner_radius": derived_values["face_inner_radius"],
            "face_hole_depth": derived_values["face_hole_depth"],
            "face_hole_offset": derived_values["face_hole_offset"],
        },
    })

    if derived_values.get("flatten_bottom", False):
        fallback_features.append({
            "type": "flatten_bottom",
            "parameters": {
                "radius": derived_values["radius"],
                "bottom_cut_plane_z": derived_values["bottom_cut_plane_z"],
            },
        })

    return fallback_features


def build_feature_blocks(features: list[dict], radius: float) -> str:
    """Build Blender template blocks from the normalized feature list."""
    blocks: list[str] = []

    for feature in features:
        feature_type = feature["type"]
        parameters = feature.get("parameters", {})

        if feature_type == "shell":
            thickness = normalize_number(parameters.get("thickness")) or 0.0
            if thickness > 0:
                blocks.append(f"""solidify_mod = target_obj.modifiers.new(name="Solidify", type='SOLIDIFY')
solidify_mod.thickness = mm({thickness})
solidify_mod.offset = 1.0
solidify_mod.use_quality_normals = True

bpy.ops.object.select_all(action='DESELECT')
target_obj.select_set(True)
bpy.context.view_layer.objects.active = target_obj
bpy.ops.object.modifier_apply(modifier=solidify_mod.name)""")

        if feature_type == "recess":
            face_outer_radius = normalize_number(parameters.get("face_outer_radius")) or 45.0
            face_recess_depth = normalize_number(parameters.get("face_recess_depth")) or 10.0
            face_recess_offset = normalize_number(parameters.get("face_recess_offset")) or 75.0
            blocks.append(f"""bpy.ops.mesh.primitive_cylinder_add(radius=mm({face_outer_radius}), depth=mm({face_recess_depth}), location=(0.0, mm({face_recess_offset}), 0.0))
recess_cutter_obj = bpy.context.active_object
recess_cutter_obj.name = "Geomancer_Recess_Cutter"

recess_cutter_obj.rotation_euler = (radians(90.0), 0.0, 0.0)

recess_bool_mod = target_obj.modifiers.new(name="FaceRecess", type='BOOLEAN')
recess_bool_mod.operation = 'DIFFERENCE'
recess_bool_mod.object = recess_cutter_obj

bpy.ops.object.select_all(action='DESELECT')
target_obj.select_set(True)
bpy.context.view_layer.objects.active = target_obj
bpy.ops.object.modifier_apply(modifier=recess_bool_mod.name)

bpy.data.objects.remove(recess_cutter_obj, do_unlink=True)""")

        if feature_type == "hole_blind":
            face_inner_radius = normalize_number(parameters.get("face_inner_radius")) or 30.0
            face_hole_depth = normalize_number(parameters.get("face_hole_depth")) or radius * 1.2
            face_hole_offset = normalize_number(parameters.get("face_hole_offset")) or (radius - (face_hole_depth / 2.0))
            blocks.append(f"""bpy.ops.mesh.primitive_cylinder_add(radius=mm({face_inner_radius}), depth=mm({face_hole_depth}), location=(0.0, mm({face_hole_offset}), 0.0))
hole_cutter_obj = bpy.context.active_object
hole_cutter_obj.name = "Geomancer_Hole_Cutter"

hole_cutter_obj.rotation_euler = (radians(90.0), 0.0, 0.0)

hole_bool_mod = target_obj.modifiers.new(name="FaceHole", type='BOOLEAN')
hole_bool_mod.operation = 'DIFFERENCE'
hole_bool_mod.object = hole_cutter_obj

bpy.ops.object.select_all(action='DESELECT')
target_obj.select_set(True)
bpy.context.view_layer.objects.active = target_obj
bpy.ops.object.modifier_apply(modifier=hole_bool_mod.name)

bpy.data.objects.remove(hole_cutter_obj, do_unlink=True)""")

        if feature_type == "hole_through":
            face_inner_radius = normalize_number(parameters.get("face_inner_radius")) or 30.0
            face_hole_depth = normalize_number(parameters.get("face_hole_depth")) or (radius * 3.0)
            blocks.append(f"""bpy.ops.mesh.primitive_cylinder_add(radius=mm({face_inner_radius}), depth=mm({face_hole_depth}), location=(0.0, 0.0, 0.0))
hole_cutter_obj = bpy.context.active_object
hole_cutter_obj.name = "Geomancer_Hole_Cutter"

hole_cutter_obj.rotation_euler = (radians(90.0), 0.0, 0.0)

hole_bool_mod = target_obj.modifiers.new(name="FaceHole", type='BOOLEAN')
hole_bool_mod.operation = 'DIFFERENCE'
hole_bool_mod.object = hole_cutter_obj

bpy.ops.object.select_all(action='DESELECT')
target_obj.select_set(True)
bpy.context.view_layer.objects.active = target_obj
bpy.ops.object.modifier_apply(modifier=hole_bool_mod.name)

bpy.data.objects.remove(hole_cutter_obj, do_unlink=True)""")

        if feature_type == "flatten_bottom":
            bottom_cut_plane_z = normalize_number(parameters.get("bottom_cut_plane_z")) or (-(radius - 6.0))
            blocks.append(f"""# Shallow bottom flatten cut along the -Z side for a stable resting surface.
bpy.ops.mesh.primitive_cube_add(size=mm({radius * 4.0}), location=(0.0, 0.0, mm({bottom_cut_plane_z - (radius * 2.0)})))
bottom_cutter_obj = bpy.context.active_object
bottom_cutter_obj.name = "Geomancer_Bottom_Cutter"

bottom_bool_mod = target_obj.modifiers.new(name="BottomCut", type='BOOLEAN')
bottom_bool_mod.operation = 'DIFFERENCE'
bottom_bool_mod.object = bottom_cutter_obj

bpy.ops.object.select_all(action='DESELECT')
target_obj.select_set(True)
bpy.context.view_layer.objects.active = target_obj
bpy.ops.object.modifier_apply(modifier=bottom_bool_mod.name)

bpy.data.objects.remove(bottom_cutter_obj, do_unlink=True)""")

    return "\n\n".join(blocks) if blocks else "# No feature blocks were generated."


def contains_bpy_usage(code_text: str) -> bool:
    """Check whether the script looks like Blender Python code."""
    return "bpy" in code_text and ("import bpy" in code_text or "bpy." in code_text)


def load_banned_patterns() -> list[str]:
    """Load banned code patterns from the local rule library."""
    if not BANNED_PATTERNS_PATH.exists():
        return [".edge_crease"]

    try:
        data = json.loads(BANNED_PATTERNS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [".edge_crease"]

    patterns = data.get("banned_patterns", [])
    return [str(pattern) for pattern in patterns]


def contains_banned_patterns(code_text: str) -> bool:
    """Check for clearly risky or unsupported generated API usage."""
    lowered = code_text.lower()
    if any(pattern.lower() in lowered for pattern in load_banned_patterns()):
        return True

    # Reject the known bad case where the Boolean cutter is assigned to the target object.
    lines = [line.strip() for line in code_text.splitlines() if line.strip()]
    bool_host_names: set[str] = set()
    for line in lines:
        match = re.search(r"(\w+)\s*=\s*(\w+)\.modifiers\.new\(", line)
        if match:
            bool_host_names.add(match.group(2))

    for host_name in bool_host_names:
        if f"bool_mod.object = {host_name}" in code_text:
            return True

    return False


def save_generated_script(script_text: str, output_path: Path) -> Path:
    """Write the generated Blender script to disk."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_script = (script_text or "").strip()
    use_fallback = False

    if not contains_bpy_usage(cleaned_script):
        print("Warning: generated output did not contain valid bpy usage. Using safe fallback script.")
        use_fallback = True
    elif contains_banned_patterns(cleaned_script):
        print("Warning: generated output contained unsupported Blender API patterns. Using safe fallback script.")
        use_fallback = True

    final_script = SAFE_FALLBACK_SCRIPT if use_fallback else cleaned_script
    output_path.write_text(final_script, encoding="utf-8")
    return output_path
