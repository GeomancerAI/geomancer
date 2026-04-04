"""Prompt builder for Geomancer."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_RULES_PATH = PROJECT_ROOT / "blender" / "templates" / "base_rules.txt"
PLANNING_SCHEMA = {
    "type": "object",
    "properties": {
        "primitive": {"type": "string"},
        "diameter_mm": {"type": ["number", "null"]},
        "shell_thickness_mm": {"type": ["number", "null"]},
        "front_opening_diameter_mm": {"type": ["number", "null"]},
        "flatten_bottom": {"type": "boolean"},
        "front_axis": {"type": "string"},
        "operations": {"type": "array", "items": {"type": "string"}},
        "features": {"type": "array", "items": {"type": "object"}}
    },
    "required": [
        "primitive",
        "diameter_mm",
        "shell_thickness_mm",
        "front_opening_diameter_mm",
        "flatten_bottom",
        "front_axis",
        "operations"
    ]
}


def load_base_rules() -> str:
    """Load the shared modeling rules from the template file."""
    if not BASE_RULES_PATH.exists():
        return (
            "- Use metric units\n"
            "- Use millimeters for dimensions\n"
            "- Use stable primitive-based geometry\n"
            "- Output valid Python only\n"
        )

    return BASE_RULES_PATH.read_text(encoding="utf-8").strip()


CODE_PARAM_SCHEMA = {
    "type": "object",
    "properties": {
        "radius": {"type": "number"},
        "face_outer_diameter_mm": {"type": "number"},
        "face_inner_diameter_mm": {"type": "number"},
        "face_recess_depth_mm": {"type": "number"},
        "thickness": {"type": "number"}
    },
    "required": ["radius", "face_outer_diameter_mm", "face_inner_diameter_mm", "face_recess_depth_mm", "thickness"]
}

BLENDER_TEMPLATE = """import bpy
from math import radians

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def mm(value):
    return value / 1000.0

# Main sphere from exact requested diameter.
bpy.ops.mesh.primitive_uv_sphere_add(radius=mm({radius}), location=(0.0, 0.0, 0.0))
target_obj = bpy.context.active_object
target_obj.name = "Geomancer_Model"

{feature_blocks}

target_obj.name = "Geomancer_Final"
"""


def build_planning_prompt(user_request: str) -> str:
    """Build a compact planning prompt that requests JSON only."""
    wrapped_request = json.dumps({"model_request": user_request}, indent=2)

    return f"""You are Geomancer planning a Blender mechanical blockout.

Return JSON only. No markdown. No prose. No code fences.

Create a compact modeling plan using these keys only:
- primitive
- diameter_mm
- shell_thickness_mm
- front_opening_diameter_mm
- flatten_bottom
- front_axis
- operations
- features

Planning rules:
- Use exact requested dimensions in millimeters
- "front" means +Y
- "back" means -Y
- "top" means +Z
- "bottom" means -Z
- A 160mm sphere means diameter 160mm and radius 80mm
- A 90mm opening means opening diameter 90mm and cutter radius 45mm
- Keep the plan short and mechanically useful
- Keep backward-compatible top-level fields
- Also add a compact features list when helpful
- Each feature should be an object with:
  - type
  - parameters needed for that feature
- Supported feature types:
  - shell
  - recess
  - hole_blind
  - hole_through
  - flatten_bottom

User request payload:
{wrapped_request}
"""


def build_code_prompt(user_request: str, plan: dict) -> str:
    """Build the template-parameter prompt from the compact JSON plan."""
    wrapped_plan = json.dumps(plan, indent=2)

    return f"""You are Geomancer preparing values for a fixed Blender Python template.

Return JSON only. No markdown. No prose. No code fences. Do not output Python.

The fixed local template already does this:
- import bpy
- clear the scene
- define mm(value)
- create a UV sphere target
- create a shallow front recess cutter
- create a second front hole cutter
- rotate both cutters to align with the Y axis
- apply the recess Boolean first
- apply the hole Boolean second
- optionally flatten the bottom
- optionally apply a Solidify modifier
- generation logic controls cutter depth and final geometry

Output only these numeric fields:
- radius
- face_outer_diameter_mm
- face_inner_diameter_mm
- face_recess_depth_mm
- thickness

Value rules:
- All values are millimeters
- radius means sphere radius in mm
- face_outer_diameter_mm means the outer recessed ring diameter
- face_inner_diameter_mm means the central hole diameter
- face_recess_depth_mm means the shallow recess depth into the front face
- thickness means shell thickness in mm
- Use exact requested dimensions
- Keep values simple and mechanically safe
- Do not invent extra keys
- Ignore noisy planner operation strings
- Operation strings are informational only and may be ignored
- Use only these normalized plan fields:
  - diameter_mm
  - shell_thickness_mm
  - front_opening_diameter_mm
  - flatten_bottom
  - front_axis
- Defaults if the planner does not provide more detail:
  - face_outer_diameter_mm = front_opening_diameter_mm
  - face_inner_diameter_mm = front_opening_diameter_mm * 0.75
  - face_recess_depth_mm = 10

Use this compact modeling plan:
{wrapped_plan}
"""


def build_prompt(user_request: str) -> str:
    """Backward-compatible alias for the code-generation prompt."""
    return build_code_prompt(user_request, {})
