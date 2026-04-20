"""Hybrid deterministic recipe executor for Geomancer backend generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .recipe_schema import DeterministicRecipe, RecipeOp, RECIPE_SCHEMA_VERSION


SUPPORTED_RECIPE_OBJECT_TYPES = {
    "enclosure",
    "tray",
    "bracket",
    "clip",
    "planter",
    "gear",
    "adapter",
    "plate",
    "standoff",
    "hook_mount",
    "phone_stand",
    "assembly",
}

SUPPORTED_RECIPE_OPS = {
    "add_box",
    "add_cylinder",
    "add_sphere",
    "add_hole",
    "hole_pattern",
    "shell",
    "flatten_bottom",
    "bracket_body",
    "hook_mount_body",
    "phone_stand_body",
    "boolean_union",
    "boolean_difference",
}


@dataclass
class RecipeExecutionResult:
    """Structured result for the hybrid recipe executor."""

    executed: bool
    fallback_required: bool
    script_text: str = ""
    warnings: list[str] = field(default_factory=list)
    unsupported_ops: list[str] = field(default_factory=list)
    unsupported_reasons: list[str] = field(default_factory=list)
    execution_path: str = "legacy"
    fallback_reason: str = ""
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "executed": self.executed,
            "fallback_required": self.fallback_required,
            "script_text_length": len(self.script_text),
            "warnings": list(self.warnings),
            "unsupported_ops": list(self.unsupported_ops),
            "unsupported_reasons": list(self.unsupported_reasons),
            "execution_path": self.execution_path,
            "fallback_reason": self.fallback_reason,
            "summary": self.summary,
        }


def execute_recipe(recipe: DeterministicRecipe) -> RecipeExecutionResult:
    """Render a deterministic recipe into Blender Python for supported subsets."""
    warnings = list(recipe.warnings)
    unsupported_ops: list[str] = []
    unsupported_reasons: list[str] = []

    if recipe.recipe_version != RECIPE_SCHEMA_VERSION:
        unsupported_reasons.append(f"Unsupported recipe schema version: {recipe.recipe_version}.")
        return _fallback_result(
            warnings,
            unsupported_ops,
            unsupported_reasons,
            "Legacy fallback required for recipe schema mismatch.",
            fallback_reason="recipe_schema_mismatch",
        )

    if recipe.object_type not in SUPPORTED_RECIPE_OBJECT_TYPES:
        unsupported_reasons.append(f"Unsupported recipe object type: {recipe.object_type}.")
        return _fallback_result(
            warnings,
            unsupported_ops,
            unsupported_reasons,
            "Legacy fallback required for unsupported recipe object type.",
            fallback_reason="unsupported_recipe_object_type",
        )

    emitter = _RecipeScriptEmitter(recipe)
    for op in recipe.ops:
        if op.op not in SUPPORTED_RECIPE_OPS:
            unsupported_ops.append(op.op)
            unsupported_reasons.append(f"Unsupported recipe op: {op.op}.")
            continue
        if not emitter.emit(op):
            unsupported_ops.append(op.op)
            unsupported_reasons.append(emitter.last_error or f"Recipe op '{op.op}' could not be executed safely.")

    if unsupported_ops or unsupported_reasons:
        return _fallback_result(
            warnings + emitter.warnings,
            unsupported_ops,
            unsupported_reasons,
            "Legacy fallback required for unsupported recipe execution details.",
            fallback_reason="unsupported_recipe_op",
        )

    script_text = emitter.build_script()
    return RecipeExecutionResult(
        executed=True,
        fallback_required=False,
        script_text=script_text,
        warnings=warnings + emitter.warnings,
        unsupported_ops=[],
        unsupported_reasons=[],
        execution_path="recipe",
        summary=f"Executed recipe for {recipe.object_type} with {len(recipe.ops)} ops.",
    )


def _fallback_result(
    warnings: list[str],
    unsupported_ops: list[str],
    unsupported_reasons: list[str],
    summary: str,
    *,
    fallback_reason: str,
) -> RecipeExecutionResult:
    return RecipeExecutionResult(
        executed=False,
        fallback_required=True,
        script_text="",
        warnings=warnings,
        unsupported_ops=unsupported_ops,
        unsupported_reasons=unsupported_reasons,
        execution_path="legacy",
        fallback_reason=fallback_reason,
        summary=summary,
    )


class _RecipeScriptEmitter:
    """Convert a bounded deterministic recipe into Blender Python."""

    def __init__(self, recipe: DeterministicRecipe) -> None:
        self.recipe = recipe
        self.lines: list[str] = []
        self.vars: dict[str, str] = {}
        self.dims: dict[str, dict[str, float]] = {}
        self.final_var: str = ""
        self.warnings: list[str] = []
        self.last_error: str = ""

    def emit(self, op: RecipeOp) -> bool:
        handlers = {
            "add_box": self._emit_add_box,
            "add_cylinder": self._emit_add_cylinder,
            "add_sphere": self._emit_add_sphere,
            "add_hole": self._emit_add_hole,
            "hole_pattern": self._emit_hole_pattern,
            "shell": self._emit_shell,
            "flatten_bottom": self._emit_flatten_bottom,
            "bracket_body": self._emit_bracket_body,
            "hook_mount_body": self._emit_hook_mount_body,
            "phone_stand_body": self._emit_phone_stand_body,
            "boolean_union": self._emit_boolean_union,
            "boolean_difference": self._emit_boolean_difference,
        }
        handler = handlers.get(op.op)
        if handler is None:
            self.last_error = f"Unsupported recipe op: {op.op}."
            return False
        return handler(op)

    def build_script(self) -> str:
        body = "\n\n".join(line for line in self.lines if line)
        if self.final_var:
            body = f"{body}\n\nfinal_obj = {self.final_var}" if body else f"final_obj = {self.final_var}"
        else:
            body = f"{body}\n\nfinal_obj = bpy.context.active_object" if body else "final_obj = bpy.context.active_object"
        return _wrap_script(self.recipe, body)

    def _emit_add_box(self, op: RecipeOp) -> bool:
        size_x = float(op.params.get("size_x_mm", 0.0))
        size_y = float(op.params.get("size_y_mm", 0.0))
        size_z = float(op.params.get("size_z_mm", 0.0))
        origin = _origin(op.params.get("origin"))
        rotation = _rotation(op.params.get("rotation_deg"))
        var_name = _safe_identifier(op.id or "box_part")
        self.vars[op.id or var_name] = var_name
        dims = {"size_x_mm": size_x, "size_y_mm": size_y, "size_z_mm": size_z}
        if op.id:
            self.dims[op.id] = dims
        self.dims[var_name] = dims
        self.lines.append(
            f"""bpy.ops.mesh.primitive_cube_add(size=1.0, location={_format_vector(origin)})
{var_name} = bpy.context.active_object
{var_name}.scale = (mm({size_x / 2.0}), mm({size_y / 2.0}), mm({size_z / 2.0}))"""
        )
        self.lines.append(f"apply_transforms({var_name})")
        if rotation:
            self.lines.append(f"{var_name}.rotation_euler = {_format_rotation(rotation)}")
            self.lines.append(f"apply_transforms({var_name})")
        self.final_var = var_name
        return True

    def _emit_add_cylinder(self, op: RecipeOp) -> bool:
        radius_mm = float(op.params.get("radius_mm", 0.0))
        height_mm = float(op.params.get("height_mm", 0.0))
        vertices = int(op.params.get("vertices", 32))
        origin = _origin(op.params.get("origin"))
        var_name = _safe_identifier(op.id or "cylinder_part")
        self.vars[op.id or var_name] = var_name
        self.dims[var_name] = {"radius_mm": radius_mm, "height_mm": height_mm}
        self.lines.append(
            f"""bpy.ops.mesh.primitive_cylinder_add(vertices={vertices}, radius=mm({radius_mm}), depth=mm({height_mm}), location={_format_vector(origin)})
{var_name} = bpy.context.active_object"""
        )
        rotation = _rotation(op.params.get("rotation_deg"))
        if rotation:
            self.lines.append(f"{var_name}.rotation_euler = {_format_rotation(rotation)}")
        self.lines.append(f"apply_transforms({var_name})")
        self.final_var = var_name
        return True

    def _emit_add_sphere(self, op: RecipeOp) -> bool:
        radius_mm = float(op.params.get("radius_mm", 0.0))
        origin = _origin(op.params.get("origin"))
        var_name = _safe_identifier(op.id or "sphere_part")
        self.vars[op.id or var_name] = var_name
        self.dims[var_name] = {"radius_mm": radius_mm}
        self.lines.append(
            f"""bpy.ops.mesh.primitive_uv_sphere_add(radius=mm({radius_mm}), location={_format_vector(origin)})
{var_name} = bpy.context.active_object"""
        )
        self.lines.append(f"apply_transforms({var_name})")
        self.final_var = var_name
        return True

    def _emit_bracket_body(self, op: RecipeOp) -> bool:
        base_length_mm = float(op.params.get("base_length_mm", 0.0))
        flange_width_mm = float(op.params.get("flange_width_mm", 0.0))
        vertical_height_mm = float(op.params.get("vertical_height_mm", 0.0))
        thickness_mm = float(op.params.get("thickness_mm", 0.0))
        if base_length_mm <= 0 or flange_width_mm <= 0 or vertical_height_mm <= 0 or thickness_mm <= 0:
            self.last_error = "bracket_body requires positive base_length, flange_width, vertical_height, and thickness."
            return False

        var_name = _safe_identifier(op.id or "bracket_body")
        self.vars[op.id or var_name] = var_name
        self.dims[var_name] = {
            "size_x_mm": base_length_mm,
            "size_y_mm": flange_width_mm,
            "size_z_mm": vertical_height_mm,
            "base_length_mm": base_length_mm,
            "flange_width_mm": flange_width_mm,
            "vertical_height_mm": vertical_height_mm,
            "thickness_mm": thickness_mm,
        }
        self.lines.append(
            f"""{var_name} = make_bracket_body(
    base_length_mm=mm({base_length_mm}),
    flange_width_mm=mm({flange_width_mm}),
    vertical_height_mm=mm({vertical_height_mm}),
    thickness_mm=mm({thickness_mm}),
    final_name={repr(var_name)},
)"""
        )
        self.final_var = var_name
        return True

    def _emit_phone_stand_body(self, op: RecipeOp) -> bool:
        width_mm = float(op.params.get("width_mm", 0.0))
        depth_mm = float(op.params.get("depth_mm", 0.0))
        height_mm = float(op.params.get("height_mm", 0.0))
        thickness_mm = float(op.params.get("thickness_mm", 0.0))
        viewing_angle_deg = float(op.params.get("viewing_angle_deg", 65.0))
        lip_height_mm = float(op.params.get("lip_height_mm", 0.0))
        cradle_depth_mm = float(op.params.get("cradle_depth_mm", 0.0))
        device_width_mm = float(op.params.get("device_width_mm", 0.0))
        if width_mm <= 0 or depth_mm <= 0 or height_mm <= 0 or thickness_mm <= 0:
            self.last_error = "phone_stand_body requires positive width, depth, height, and thickness."
            return False

        var_name = _safe_identifier(op.id or "phone_stand_body")
        self.vars[op.id or var_name] = var_name
        self.dims[var_name] = {
            "size_x_mm": width_mm,
            "size_y_mm": depth_mm,
            "size_z_mm": height_mm,
            "width_mm": width_mm,
            "depth_mm": depth_mm,
            "height_mm": height_mm,
            "thickness_mm": thickness_mm,
            "viewing_angle_deg": viewing_angle_deg,
            "lip_height_mm": lip_height_mm,
            "cradle_depth_mm": cradle_depth_mm,
            "device_width_mm": device_width_mm,
        }
        self.lines.append(
            f"""{var_name} = make_phone_stand_body(
    width_mm=mm({width_mm}),
    depth_mm=mm({depth_mm}),
    height_mm=mm({height_mm}),
    thickness_mm=mm({thickness_mm}),
    viewing_angle_deg={viewing_angle_deg},
    lip_height_mm=mm({lip_height_mm}),
    cradle_depth_mm=mm({cradle_depth_mm}),
    device_width_mm=mm({device_width_mm}),
    final_name={repr(var_name)},
)"""
        )
        self.final_var = var_name
        return True

    def _emit_hook_mount_body(self, op: RecipeOp) -> bool:
        width_mm = float(op.params.get("width_mm", 0.0))
        height_mm = float(op.params.get("height_mm", 0.0))
        depth_mm = float(op.params.get("depth_mm", 0.0))
        thickness_mm = float(op.params.get("thickness_mm", 0.0))
        base_thickness_mm = float(op.params.get("base_thickness_mm", thickness_mm))
        hook_length_mm = float(op.params.get("hook_length_mm", depth_mm))
        hook_radius_mm = float(op.params.get("hook_radius_mm", max(thickness_mm * 1.5, 3.0)))
        hook_angle_deg = float(op.params.get("hook_angle_deg", 18.0))
        if width_mm <= 0 or height_mm <= 0 or depth_mm <= 0 or thickness_mm <= 0:
            self.last_error = "hook_mount_body requires positive width, height, depth, and thickness."
            return False

        var_name = _safe_identifier(op.id or "hook_mount_body")
        self.vars[op.id or var_name] = var_name
        self.dims[var_name] = {
            "size_x_mm": width_mm,
            "size_y_mm": depth_mm,
            "size_z_mm": height_mm,
            "width_mm": width_mm,
            "height_mm": height_mm,
            "depth_mm": depth_mm,
            "thickness_mm": thickness_mm,
            "base_thickness_mm": base_thickness_mm,
            "hook_length_mm": hook_length_mm,
            "hook_radius_mm": hook_radius_mm,
            "hook_angle_deg": hook_angle_deg,
        }
        self.lines.append(
            f"""{var_name} = make_hook_mount_body(
    width_mm=mm({width_mm}),
    height_mm=mm({height_mm}),
    depth_mm=mm({depth_mm}),
    thickness_mm=mm({thickness_mm}),
    base_thickness_mm=mm({base_thickness_mm}),
    hook_length_mm=mm({hook_length_mm}),
    hook_radius_mm=mm({hook_radius_mm}),
    hook_angle_deg={hook_angle_deg},
    final_name={repr(var_name)},
)"""
        )
        self.final_var = var_name
        return True

    def _emit_boolean_union(self, op: RecipeOp) -> bool:
        return self._emit_boolean(op, "UNION", op.target, op.tool, op.id or "union_result")

    def _emit_boolean_difference(self, op: RecipeOp) -> bool:
        return self._emit_boolean(op, "DIFFERENCE", op.target, op.tool, op.id or "difference_result")

    def _emit_boolean(self, op: RecipeOp, operation: str, target: str, tool: str, fallback_id: str) -> bool:
        target_var = self._resolve_var(target)
        tool_var = self._resolve_var(tool)
        if not target_var or not tool_var:
            self.last_error = f"Boolean op '{op.op}' could not resolve target/tool variables."
            return False
        if operation == "UNION":
            join_id = _safe_identifier(fallback_id)
            self.lines.append(f"{target_var} = join_objects([{target_var}, {tool_var}], final_name={repr(join_id)})")
            self.vars[target] = target_var
        else:
            self.lines.append(
                f"apply_boolean({target_var}, {tool_var}, operation='{operation}', modifier_name={repr(_safe_identifier(fallback_id))})"
            )
        self.final_var = target_var
        return True

    def _emit_add_hole(self, op: RecipeOp) -> bool:
        target_var = self._resolve_var(op.target)
        if not target_var:
            self.last_error = "add_hole could not resolve target variable."
            return False
        hole_id = _safe_identifier(op.id or f"{target_var}_hole")
        cutter_var = f"{hole_id}_cutter"
        diameter_mm = float(op.params.get("diameter_mm", 0.0))
        layout = str(op.params.get("layout", "center"))
        origin = _origin(op.params.get("origin"))
        vertices = int(op.params.get("vertices", 32))
        self.lines.append(
            f"""bpy.ops.mesh.primitive_cylinder_add(vertices={vertices}, radius=mm({diameter_mm / 2.0}), depth=mm({max(diameter_mm * 2.5, 1.0)}), location={_format_vector(origin)})
{cutter_var} = bpy.context.active_object"""
        )
        self.lines.append(f"{cutter_var}.rotation_euler = (math.radians(90.0), 0.0, 0.0)")
        self.lines.append(f"apply_transforms({cutter_var})")
        self.lines.append(f"apply_boolean({target_var}, {cutter_var}, modifier_name={repr(hole_id)})")
        self.final_var = target_var
        if layout and layout != "center":
            self.warnings.append(f"add_hole layout '{layout}' was simplified to a centered cutter.")
        return True

    def _emit_hole_pattern(self, op: RecipeOp) -> bool:
        target_var = self._resolve_var(op.target)
        if not target_var:
            self.last_error = "hole_pattern could not resolve target variable."
            return False

        layout = str(op.params.get("layout", "rectangular"))
        count = int(op.params.get("count", 0))
        diameter_mm = float(op.params.get("diameter_mm", 0.0))
        if count <= 0 or diameter_mm <= 0:
            self.lines.append(f"# hole_pattern omitted for {target_var} because no mounting holes were requested.")
            self.final_var = target_var
            return True

        if self.recipe.object_type == "hook_mount" and layout == "wall_vertical_pair":
            return self._emit_hook_mount_holes(target_var, count, diameter_mm, float(op.params.get("margin_mm", 0.0)))
        if self.recipe.object_type == "bracket" and layout == "rectangular":
            return self._emit_bracket_holes(target_var, count, diameter_mm)
        if self.recipe.object_type == "plate" and layout in {"corners", "pair_horizontal"}:
            return self._emit_plate_holes(target_var, count, diameter_mm, layout)
        if layout in {"center", "center_bottom", "pair_horizontal", "vertical_pair"}:
            return self._emit_generic_hole_pattern(target_var, count, diameter_mm, layout)

        self.last_error = f"Unsupported hole pattern layout: {layout}."
        return False

    def _emit_bracket_holes(self, target_var: str, count: int, diameter_mm: float) -> bool:
        base_dims = self.dims.get(target_var, {})
        length = float(base_dims.get("base_length_mm", base_dims.get("size_x_mm", 0.0)))
        flange_width = float(base_dims.get("flange_width_mm", base_dims.get("size_y_mm", 0.0)))
        vertical_height = float(base_dims.get("vertical_height_mm", base_dims.get("size_z_mm", 0.0)))
        thickness = float(base_dims.get("thickness_mm", 0.0))
        if length <= 0 or flange_width <= 0 or vertical_height <= 0 or thickness <= 0:
            self.last_error = "Bracket hole pattern missing base dimensions."
            return False

        hole_margin = max(thickness * 1.8, diameter_mm * 1.5, 8.0)
        usable_base_span = max(length - (hole_margin * 2.0), 0.0)
        usable_vertical_span = max(vertical_height - (hole_margin * 2.0), 0.0) if vertical_height > 0 else 0.0
        base_positions = []
        if count >= 2:
            base_positions = [
                hole_margin + (usable_base_span * 0.33),
                hole_margin + (usable_base_span * 0.67),
            ]
        vertical_positions = []
        if count >= 4 and vertical_height > 0:
            vertical_positions = [
                hole_margin + (usable_vertical_span * 0.33),
                hole_margin + (usable_vertical_span * 0.67),
            ]

        self.lines.append(
            f"""base_hole_positions = []
if {count} >= 2:
    base_hole_positions = [(mm({base_positions[0] if base_positions else hole_margin}), mm({flange_width / 2.0}), mm({thickness / 2.0})), (mm({base_positions[1] if base_positions else hole_margin}), mm({flange_width / 2.0}), mm({thickness / 2.0}))]
for x_pos, y_pos, z_pos in base_hole_positions:
    bpy.ops.mesh.primitive_cylinder_add(radius=mm({diameter_mm / 2.0}), depth=mm({max(diameter_mm * 2.5, 1.0)}), location=(x_pos, y_pos, z_pos))
    hole_cutter = bpy.context.active_object
    apply_transforms(hole_cutter)
    apply_boolean({target_var}, hole_cutter, modifier_name='BracketBaseHole')
"""
        )
        if count >= 4:
            self.lines.append(
                f"""if {count} >= 4:
    for z_pos in (mm({vertical_positions[0] if vertical_positions else hole_margin}), mm({vertical_positions[1] if vertical_positions else hole_margin})):
        bpy.ops.mesh.primitive_cylinder_add(radius=mm({diameter_mm / 2.0}), depth=mm({max(diameter_mm * 2.5, 1.0)}), location=(mm({thickness / 2.0}), mm({flange_width / 2.0}), z_pos))
        vertical_hole = bpy.context.active_object
        vertical_hole.rotation_euler = (0.0, math.radians(90.0), 0.0)
        apply_transforms(vertical_hole)
        apply_boolean({target_var}, vertical_hole, modifier_name='BracketVerticalHole')
"""
            )
        self.final_var = target_var
        return True

    def _emit_hook_mount_holes(self, target_var: str, count: int, diameter_mm: float, margin_mm: float) -> bool:
        dims = self.dims.get(target_var, {})
        width = float(dims.get("width_mm", dims.get("size_x_mm", 0.0)))
        height = float(dims.get("height_mm", dims.get("size_z_mm", 0.0)))
        thickness = float(dims.get("thickness_mm", 0.0))
        base_thickness = float(dims.get("base_thickness_mm", thickness))
        if width <= 0 or height <= 0 or thickness <= 0:
            self.last_error = "Hook mount hole pattern missing base dimensions."
            return False

        margin = max(margin_mm, thickness * 1.5, diameter_mm * 1.5, 6.0)
        hole_depth = max(width * 1.15, diameter_mm * 2.5, 1.0)
        plate_thickness = max(base_thickness, thickness * 1.25)
        x_center = max(min(plate_thickness * 0.5, plate_thickness - diameter_mm * 0.5), diameter_mm * 0.5)

        if count >= 4:
            z_offset = max(min((height / 2.0) - margin, height * 0.35), diameter_mm)
            x_offset = max(min(plate_thickness * 0.3, plate_thickness / 2.0 - diameter_mm * 0.25), diameter_mm * 0.5)
            self.lines.append(
                f"""for x_pos in (mm({max(x_center - x_offset, diameter_mm * 0.5)}), mm({min(x_center + x_offset, plate_thickness - diameter_mm * 0.5)})):
    for z_pos in (mm({-z_offset}), mm({z_offset})):
        bpy.ops.mesh.primitive_cylinder_add(radius=mm({diameter_mm / 2.0}), depth=mm({hole_depth}), location=(x_pos, 0.0, z_pos))
        mount_hole = bpy.context.active_object
        mount_hole.rotation_euler = (math.radians(90.0), 0.0, 0.0)
        apply_transforms(mount_hole)
        apply_boolean({target_var}, mount_hole, modifier_name='HookMountHole')
"""
            )
        else:
            z_offset = max(min((height / 4.0), (height / 2.0) - margin), diameter_mm)
            self.lines.append(
                f"""for z_pos in (mm({-z_offset}), mm({z_offset})):
    bpy.ops.mesh.primitive_cylinder_add(radius=mm({diameter_mm / 2.0}), depth=mm({hole_depth}), location=(mm({x_center}), 0.0, z_pos))
    mount_hole = bpy.context.active_object
    mount_hole.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    apply_transforms(mount_hole)
    apply_boolean({target_var}, mount_hole, modifier_name='HookMountHole')
"""
            )
        self.final_var = target_var
        return True

    def _emit_plate_holes(self, target_var: str, count: int, diameter_mm: float, layout: str) -> bool:
        dims = self.dims.get(target_var, {})
        width = float(dims.get("size_x_mm", 0.0))
        height = float(dims.get("size_z_mm", 0.0))
        thickness = float(dims.get("size_y_mm", 0.0))
        if width <= 0 or height <= 0:
            self.last_error = "Plate hole pattern missing panel dimensions."
            return False
        x_offset = max((width / 2.0) - max(diameter_mm * 1.5, 8.0), diameter_mm)
        z_offset = max((height / 2.0) - max(diameter_mm * 1.5, 8.0), diameter_mm)
        if layout == "pair_horizontal":
            x_offset = min(max((width - thickness) / 4.0, diameter_mm), (width / 2.0) - diameter_mm)
            self.lines.append(
                f"""for x_pos in (-mm({x_offset}), mm({x_offset})):
    bpy.ops.mesh.primitive_cylinder_add(radius=mm({diameter_mm / 2.0}), depth=mm({max(diameter_mm * 2.5, 1.0)}), location=(x_pos, 0.0, 0.0))
    plate_hole = bpy.context.active_object
    plate_hole.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    apply_boolean({target_var}, plate_hole, modifier_name='PlateHole')
"""
            )
            self.final_var = target_var
            return True

        self.lines.append(
            f"""for x_pos in (-mm({x_offset}), mm({x_offset})):
    for z_pos in (-mm({z_offset}), mm({z_offset})):
        bpy.ops.mesh.primitive_cylinder_add(radius=mm({diameter_mm / 2.0}), depth=mm({max(diameter_mm * 2.5, 1.0)}), location=(x_pos, 0.0, z_pos))
        plate_hole = bpy.context.active_object
        plate_hole.rotation_euler = (math.radians(90.0), 0.0, 0.0)
        apply_boolean({target_var}, plate_hole, modifier_name='PlateHole')
"""
        )
        self.final_var = target_var
        return True

    def _emit_generic_hole_pattern(self, target_var: str, count: int, diameter_mm: float, layout: str) -> bool:
        dims = self.dims.get(target_var, {})
        width = float(dims.get("size_x_mm", 0.0))
        depth = float(dims.get("size_y_mm", 0.0))
        height = float(dims.get("size_z_mm", 0.0))
        if layout == "center":
            self.lines.append(
                f"""bpy.ops.mesh.primitive_cylinder_add(radius=mm({diameter_mm / 2.0}), depth=mm({max(diameter_mm * 2.5, 1.0)}), location=(0.0, 0.0, 0.0))
center_hole = bpy.context.active_object
center_hole.rotation_euler = (math.radians(90.0), 0.0, 0.0)
apply_boolean({target_var}, center_hole, modifier_name='CenterHole')
"""
            )
            self.final_var = target_var
            return True
        if layout == "center_bottom":
            self.lines.append(
                f"""bpy.ops.mesh.primitive_cylinder_add(radius=mm({diameter_mm / 2.0}), depth=mm({max(diameter_mm * 3.0, 1.0)}), location=(0.0, 0.0, mm({-(height / 2.0) + (diameter_mm / 2.0)})))
bottom_hole = bpy.context.active_object
apply_boolean({target_var}, bottom_hole, modifier_name='BottomHole')
"""
            )
            self.final_var = target_var
            return True
        if layout == "pair_horizontal":
            x_offset = max((width / 4.0), diameter_mm)
            self.lines.append(
                f"""for x_pos in (-mm({x_offset}), mm({x_offset})):
    bpy.ops.mesh.primitive_cylinder_add(radius=mm({diameter_mm / 2.0}), depth=mm({max(diameter_mm * 2.5, 1.0)}), location=(x_pos, 0.0, 0.0))
    pair_hole = bpy.context.active_object
    pair_hole.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    apply_boolean({target_var}, pair_hole, modifier_name='PairHole')
"""
            )
            self.final_var = target_var
            return True
        if layout == "vertical_pair":
            z_offset = max((height / 4.0), diameter_mm)
            self.lines.append(
                f"""for z_pos in (-mm({z_offset}), mm({z_offset})):
    bpy.ops.mesh.primitive_cylinder_add(radius=mm({diameter_mm / 2.0}), depth=mm({max(diameter_mm * 2.5, 1.0)}), location=(0.0, 0.0, z_pos))
    vertical_hole = bpy.context.active_object
    vertical_hole.rotation_euler = (0.0, math.radians(90.0), 0.0)
    apply_boolean({target_var}, vertical_hole, modifier_name='VerticalPairHole')
"""
            )
            self.final_var = target_var
            return True

        self.last_error = f"Unsupported generic hole pattern layout: {layout}."
        return False

    def _emit_shell(self, op: RecipeOp) -> bool:
        params = op.params
        diameter = float(params.get("diameter_mm", 0.0))
        width = float(params.get("width_mm", 0.0)) or diameter
        depth = float(params.get("depth_mm", 0.0)) or diameter
        height = float(params.get("height_mm", 0.0))
        wall = float(params.get("wall_thickness_mm", 0.0))
        base_thickness = float(params.get("base_thickness_mm", wall))
        front_opening = bool(params.get("front_opening", False))
        if width <= 0 or depth <= 0 or height <= 0 or wall <= 0:
            self.last_error = "shell requires positive width, depth, height, and wall thickness."
            return False

        target_var = _safe_identifier(op.id or "shell")
        self.vars[op.id or target_var] = target_var
        self.dims[target_var] = {"size_x_mm": width, "size_y_mm": depth, "size_z_mm": height}
        wall = max(wall, 1.5)
        max_wall_by_span = max(min(width, depth) * 0.45, 1.5)
        max_wall_by_height = max((height - 0.5) / 2.0, 1.5)
        wall = min(wall, max_wall_by_span, max_wall_by_height)
        base_thickness = max(base_thickness, wall)
        max_base_by_height = max(height - wall - 0.5, wall)
        base_thickness = min(base_thickness, max_base_by_height)
        inner_width = max(width - (wall * 2.0), wall)
        inner_depth = max(depth - (wall * 2.0), wall)
        inner_height = max(height - base_thickness + wall, wall)
        inner_bottom_z = -(height / 2.0) + base_thickness
        inner_z = inner_bottom_z + (inner_height / 2.0)
        inner_height_cut = inner_height
        bevel_mm = max(min(wall * 0.18, 1.0), 0.25)

        self.lines.append(
            f"""bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.0))
{target_var} = bpy.context.active_object
{target_var}.scale = (mm({width / 2.0}), mm({depth / 2.0}), mm({height / 2.0}))

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, mm({inner_z})))
{target_var}_inner = bpy.context.active_object
{target_var}_inner.scale = (mm({inner_width / 2.0}), mm({inner_depth / 2.0}), mm({inner_height_cut / 2.0}))
apply_boolean({target_var}, {target_var}_inner, modifier_name='InnerCavity')
"""
        )
        if front_opening:
            opening_width = float(params.get("opening_width_mm", max(width * 0.55, 20.0)))
            opening_height = float(params.get("opening_height_mm", max(height * 0.45, 20.0)))
            opening_center_z = max(height * 0.5 - (opening_height / 2.0), opening_height / 2.0)
            self.lines.append(
                f"""bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, mm({(depth / 2.0) - (wall / 2.0)}), mm({opening_center_z - (height / 2.0)})))
{target_var}_front = bpy.context.active_object
{target_var}_front.scale = (mm({opening_width / 2.0}), mm({wall * 1.6}), mm({opening_height / 2.0}))
apply_boolean({target_var}, {target_var}_front, modifier_name='FrontOpening')
"""
            )
        self.lines.append(f"apply_bevel({target_var}, {bevel_mm}, modifier_name='ShellBevel')")
        self.final_var = target_var
        return True

    def _emit_flatten_bottom(self, op: RecipeOp) -> bool:
        target_var = self._resolve_var(op.target)
        if not target_var:
            self.last_error = "flatten_bottom could not resolve target variable."
            return False
        self.lines.append(f"# flatten_bottom preserved by deterministic recipe alignment for {target_var}")
        self.final_var = target_var
        return True

    def _resolve_var(self, key: str) -> str:
        if not key:
            return ""
        return self.vars.get(key, key)


def _wrap_script(recipe: DeterministicRecipe, body: str) -> str:
    return f"""import bpy
import bmesh
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def mm(value):
    return value / 1000.0

def set_active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def apply_transforms(obj):
    if obj is None:
        return obj
    set_active(obj)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return obj

def apply_boolean(target, cutter, operation='DIFFERENCE', modifier_name='GeomancerBool'):
    modifier = target.modifiers.new(name=modifier_name, type='BOOLEAN')
    modifier.operation = operation
    modifier.object = cutter
    set_active(target)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)

def apply_bevel(obj, width_mm, segments=2, profile=0.7, modifier_name='GeomancerBevel'):
    if obj is None or width_mm <= 0:
        return obj
    modifier = obj.modifiers.new(name=modifier_name, type='BEVEL')
    modifier.width = mm(width_mm)
    modifier.segments = segments
    modifier.profile = profile
    modifier.use_clamp_overlap = True
    set_active(obj)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj

def make_bracket_body(base_length_mm, flange_width_mm, vertical_height_mm, thickness_mm, final_name='GeomancerBracket'):
    mesh = bpy.data.meshes.new(final_name + "_mesh")
    obj = bpy.data.objects.new(final_name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    profile = [
        (0.0, 0.0),
        (base_length_mm, 0.0),
        (base_length_mm, thickness_mm),
        (thickness_mm, thickness_mm),
        (thickness_mm, vertical_height_mm),
        (0.0, vertical_height_mm),
    ]
    face_verts = [bm.verts.new((x, 0.0, z)) for x, z in profile]
    bm.faces.new(face_verts)
    bm.normal_update()
    extruded = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    extruded_verts = [elem for elem in extruded['geom'] if isinstance(elem, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=extruded_verts, vec=(0.0, flange_width_mm, 0.0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    set_active(obj)
    return obj

def make_phone_stand_body(width_mm, depth_mm, height_mm, thickness_mm, viewing_angle_deg=65.0, lip_height_mm=5.0, cradle_depth_mm=24.0, device_width_mm=72.0, final_name='GeomancerPhoneStand'):
    mesh = bpy.data.meshes.new(final_name + "_mesh")
    obj = bpy.data.objects.new(final_name, mesh)
    bpy.context.collection.objects.link(obj)

    base_thickness = max(float(thickness_mm), 0.003)
    lip_height = max(float(lip_height_mm), 0.003)
    depth = max(float(depth_mm), base_thickness * 2.0)
    width = max(float(width_mm), base_thickness * 2.0)
    height = max(float(height_mm), base_thickness + lip_height + 0.003)
    cradle_depth = max(min(float(cradle_depth_mm), depth * 0.45), base_thickness * 4.0)
    edge_clearance = max(base_thickness * 0.9, 0.004)
    front_y = -(depth / 2.0)
    rear_y = depth / 2.0
    lip_depth = max(min(cradle_depth * 0.28, depth * 0.18), base_thickness * 1.4)
    lip_back_y = min(front_y + lip_depth, rear_y - edge_clearance * 5.0)
    base_back_y = min(front_y + max(depth * 0.58, cradle_depth * 0.55, base_thickness * 8.0), rear_y - edge_clearance * 3.0)
    if base_back_y <= lip_back_y + base_thickness * 1.8:
        base_back_y = min(lip_back_y + max(base_thickness * 3.5, 0.02), rear_y - edge_clearance * 3.0)
    support_front_y = min(base_back_y + max(depth * 0.08, base_thickness * 1.8), rear_y - edge_clearance)
    lip_top_z = base_thickness + lip_height
    if lip_top_z >= height:
        lip_top_z = max(height - max(base_thickness * 0.4, 0.004), lip_height)
    support_step_z = max(lip_top_z + max(base_thickness * 0.75, 2.0), base_thickness + max(base_thickness * 0.9, 4.0))
    if support_step_z >= height:
        support_step_z = max(height - max(base_thickness * 0.45, 0.004), lip_top_z + max(base_thickness * 0.35, 0.01))
    support_angle = math.radians(max(min(float(viewing_angle_deg), 80.0), 35.0))
    support_span = max(rear_y - support_front_y, base_thickness * 2.0)
    support_peak_z = min(height, support_step_z + max(support_span * math.tan(support_angle), base_thickness * 2.0))
    if support_peak_z <= support_step_z + base_thickness * 0.5:
        support_peak_z = min(height, support_step_z + max(base_thickness * 2.0, 0.01))
    profile = [
        (front_y, 0.0),
        (front_y, lip_top_z),
        (lip_back_y, lip_top_z),
        (lip_back_y, base_thickness),
        (base_back_y, base_thickness),
        (base_back_y, support_step_z),
        (support_front_y, support_step_z),
        (rear_y, support_peak_z),
        (rear_y, 0.0),
    ]

    bm = bmesh.new()
    profile_verts = [bm.verts.new((0.0, y, z)) for y, z in profile]
    bm.faces.new(profile_verts)
    bm.normal_update()
    extruded = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    extruded_verts = [elem for elem in extruded['geom'] if isinstance(elem, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=extruded_verts, vec=(width, 0.0, 0.0))
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=(-width / 2.0, 0.0, 0.0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    set_active(obj)
    return obj

def make_hook_mount_body(width_mm, height_mm, depth_mm, thickness_mm, base_thickness_mm=8.0, hook_length_mm=24.0, hook_radius_mm=4.0, hook_angle_deg=18.0, final_name='GeomancerHookMount'):
    mesh = bpy.data.meshes.new(final_name + "_mesh")
    obj = bpy.data.objects.new(final_name, mesh)
    bpy.context.collection.objects.link(obj)

    width = max(float(width_mm), 12.0)
    height = max(float(height_mm), 24.0)
    depth = max(float(depth_mm), 10.0)
    thickness = max(float(thickness_mm), 3.0)
    plate_thickness = max(min(float(base_thickness_mm), depth * 0.45), thickness * 1.25)
    hook_length = max(min(float(hook_length_mm), depth - plate_thickness), 10.0)
    hook_radius = max(min(float(hook_radius_mm), hook_length * 0.45), thickness * 0.75)
    hook_angle = math.radians(max(min(float(hook_angle_deg), 35.0), 12.0))
    plate_top_z = height / 2.0
    plate_bottom_z = -(height / 2.0)
    support_start_z = min(plate_top_z - max(thickness * 0.85, 3.0), plate_top_z - max(height * 0.08, 2.0))
    support_start_z = max(support_start_z, plate_bottom_z + max(thickness * 2.0, 4.0))
    arm_start_x = min(plate_thickness + max(hook_length * 0.22, thickness * 2.0), plate_thickness + hook_length * 0.6)
    arm_tip_x = min(plate_thickness + hook_length, depth)
    if arm_tip_x <= arm_start_x + thickness * 0.75:
        arm_tip_x = arm_start_x + max(thickness * 2.5, 10.0)
    tip_rise = max(math.tan(hook_angle) * max(arm_tip_x - arm_start_x, thickness * 2.0), thickness * 1.5)
    hook_tip_z = min(support_start_z + tip_rise, plate_top_z - max(thickness * 0.6, 2.0))
    if hook_tip_z <= support_start_z + thickness * 0.5:
        hook_tip_z = support_start_z + max(thickness * 1.5, 3.0)
    arm_return_x = max(arm_tip_x - hook_radius, arm_start_x + thickness * 0.5)
    hook_return_z = max(hook_tip_z - max(hook_radius * 0.6, thickness * 0.9), plate_bottom_z + max(thickness * 1.5, 4.0))
    profile = [
        (0.0, plate_bottom_z),
        (0.0, plate_top_z),
        (plate_thickness, plate_top_z),
        (plate_thickness, support_start_z),
        (arm_start_x, support_start_z),
        (arm_tip_x, hook_tip_z),
        (arm_return_x, hook_return_z),
        (plate_thickness, plate_bottom_z),
    ]

    bm = bmesh.new()
    profile_verts = [bm.verts.new((x, 0.0, z)) for x, z in profile]
    bm.faces.new(profile_verts)
    bm.normal_update()
    extruded = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    extruded_verts = [elem for elem in extruded['geom'] if isinstance(elem, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=extruded_verts, vec=(0.0, width, 0.0))
    bmesh.ops.translate(bm, verts=bm.verts[:], vec=(0.0, -width / 2.0, 0.0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    set_active(obj)
    return obj

def join_objects(objects, final_name='Geomancer_Final'):
    valid_objects = [obj for obj in objects if obj is not None]
    if not valid_objects:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for obj in valid_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = valid_objects[0]
    if len(valid_objects) > 1:
        bpy.ops.object.join()
    final_obj = bpy.context.view_layer.objects.active
    final_obj.name = final_name
    return final_obj

def finalize_object(obj, final_name='Geomancer_Final'):
    if obj is None:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.name = final_name
    return obj

# Recipe schema version: {recipe.recipe_version}
# Family: {recipe.source_family}
# Recipe: {recipe.source_recipe}
# Execution recipe: {recipe.execution_recipe or recipe.source_recipe}
# Family implementation: {recipe.object_type or recipe.source_family or "geometry"}
# Implementation ID: {recipe.implementation_id or "unassigned"}
# Generation ID: {recipe.generation_id or "unassigned"}
# Object type: {recipe.object_type}

{body}

final_obj = locals().get("final_obj")
if final_obj is None:
    final_obj = bpy.context.active_object
if final_obj is not None:
    final_obj = finalize_object(final_obj, "Geomancer_Final")
"""


def _safe_identifier(value: str) -> str:
    cleaned = [char if char.isalnum() or char == "_" else "_" for char in value.strip()]
    result = "".join(cleaned).strip("_")
    return result or "recipe_part"


def _origin(value: object) -> tuple[float, float, float]:
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return float(value[0]), float(value[1]), float(value[2])
    return 0.0, 0.0, 0.0


def _rotation(value: object) -> tuple[float, float, float]:
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return float(value[0]), float(value[1]), float(value[2])
    return ()


def _format_vector(value: tuple[float, float, float]) -> str:
    return f"(mm({value[0]}), mm({value[1]}), mm({value[2]}))"


def _format_rotation(value: tuple[float, float, float]) -> str:
    return f"(math.radians({value[0]}), math.radians({value[1]}), math.radians({value[2]}))"
