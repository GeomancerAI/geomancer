"""Deterministic Blender script generation for supported alpha families."""

from __future__ import annotations

from .models import GenerationPlan


def build_script(plan: GenerationPlan) -> str:
    """Build Blender Python for the normalized plan."""
    builders = {
        "box_shell": _build_box_shell_script,
        "tray_box": _build_tray_box_script,
        "bracket": _build_bracket_script,
        "cable_clip": _build_cable_clip_script,
        "vessel": _build_vessel_script,
        "gear": _build_gear_script,
        "adapter": _build_adapter_script,
        "panel_plate": _build_panel_plate_script,
        "standoff": _build_standoff_script,
        "hook_mount": _build_hook_mount_script,
        "phone_stand": _build_phone_stand_script,
        "primitive_assembly": _build_primitive_assembly_script,
    }
    builder = builders.get(plan.recipe, _build_primitive_assembly_script)
    return _script_wrapper(plan, builder(plan))


def _script_wrapper(plan: GenerationPlan, body: str) -> str:
    return f"""import bpy
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def mm(value):
    return value / 1000.0

def set_active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

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

def apply_transforms(obj):
    if obj is None:
        return obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return obj

# Family: {plan.family}
# Recipe: {plan.recipe}

{body}

final_obj = locals().get("final_obj")
if final_obj is None:
    final_obj = bpy.context.active_object
if final_obj is not None:
    final_obj.name = "Geomancer_Final"
    set_active(final_obj)
"""


def _build_box_shell_script(plan: GenerationPlan) -> str:
    width = plan.dimensions["width_mm"]
    depth = plan.dimensions["depth_mm"]
    height = plan.dimensions["height_mm"]
    wall = float(plan.features["wall_thickness_mm"])
    base_thickness = float(plan.features.get("base_thickness_mm", wall))
    front_opening = bool(plan.features.get("front_opening"))
    wall = max(wall, 1.5)
    wall = min(wall, max(min(width, depth) * 0.45, 1.5), max((height - 0.5) / 2.0, 1.5))
    base_thickness = max(base_thickness, wall)
    base_thickness = min(base_thickness, max(height - wall - 0.5, wall))
    inner_width = max(width - (wall * 2.0), wall)
    inner_depth = max(depth - (wall * 2.0), wall)
    inner_height = max(height - base_thickness + wall, wall)
    inner_bottom_z = -(height / 2.0) + base_thickness
    inner_z = inner_bottom_z + (inner_height / 2.0)
    inner_height_cut = inner_height
    bevel_mm = max(min(wall * 0.18, 1.0), 0.25)
    front_cut = ""
    if front_opening:
        opening_width = min(float(plan.features.get("opening_width_mm", inner_width)), inner_width)
        opening_height = min(float(plan.features.get("opening_height_mm", inner_height)), inner_height)
        opening_center_z = max(base_thickness + (opening_height / 2.0), opening_height / 2.0)
        front_cut = f"""
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, mm({(depth / 2.0) - (wall / 2.0)}), mm({opening_center_z - (height / 2.0)})))
front_cutter = bpy.context.active_object
front_cutter.scale = (mm({opening_width / 2.0}), mm({wall * 1.6}), mm({opening_height / 2.0}))
apply_boolean(outer_box, front_cutter, modifier_name='FrontOpening')
"""
    return f"""bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.0))
outer_box = bpy.context.active_object
outer_box.name = "Geomancer_Box"
outer_box.scale = (mm({width / 2.0}), mm({depth / 2.0}), mm({height / 2.0}))

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, mm({inner_z})))
inner_box = bpy.context.active_object
inner_box.scale = (mm({inner_width / 2.0}), mm({inner_depth / 2.0}), mm({inner_height_cut / 2.0}))
apply_boolean(outer_box, inner_box, modifier_name='InnerCavity')
{front_cut}
apply_bevel(outer_box, {bevel_mm}, modifier_name='ShellBevel')
final_obj = outer_box"""


def _build_tray_box_script(plan: GenerationPlan) -> str:
    body = _build_box_shell_script(plan)
    lip_height = float(plan.features.get("lip_height_mm", 0.0))
    if lip_height <= 0:
        return body
    width = plan.dimensions["width_mm"]
    depth = plan.dimensions["depth_mm"]
    height = plan.dimensions["height_mm"]
    wall = float(plan.features["wall_thickness_mm"])
    rim_width = max(wall * 1.1, 2.0)
    return body.replace(
        "final_obj = outer_box",
        f"""bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, mm({(height / 2.0) - (lip_height / 2.0)})))
tray_rim = bpy.context.active_object
tray_rim.scale = (mm({width / 2.0}), mm({depth / 2.0}), mm({lip_height / 2.0}))

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, mm({(height / 2.0) - (lip_height / 2.0)})))
tray_rim_cutter = bpy.context.active_object
tray_rim_cutter.scale = (mm({max((width - (rim_width * 2.0)) / 2.0, rim_width)}), mm({max((depth - (rim_width * 2.0)) / 2.0, rim_width)}), mm({(lip_height + wall) / 2.0}))
apply_boolean(tray_rim, tray_rim_cutter, modifier_name='TrayRim')
final_obj = join_objects([outer_box, tray_rim])""",
    )


def _build_bracket_script(plan: GenerationPlan) -> str:
    base_length = plan.dimensions["base_length_mm"]
    flange_width = plan.dimensions["flange_width_mm"]
    vertical_height = plan.dimensions["vertical_height_mm"]
    thickness = plan.dimensions["thickness_mm"]
    hole_diameter = float(plan.features["hole_diameter_mm"])
    hole_count = int(plan.features.get("hole_count", 0))
    gusset = bool(plan.features.get("gusset")) and hole_count < 4
    holes = ""
    if hole_diameter > 0:
        hole_margin = max(thickness * 1.8, hole_diameter * 1.5, 8.0)
        base_span = max(base_length - (hole_margin * 2.0), 0.0)
        vertical_span = max(vertical_height - (hole_margin * 2.0), 0.0)
        base_positions = [hole_margin + (base_span * 0.33), hole_margin + (base_span * 0.67)] if hole_count >= 2 else []
        vertical_positions = [hole_margin + (vertical_span * 0.33), hole_margin + (vertical_span * 0.67)] if hole_count >= 4 else []
        holes = f"""
base_hole_positions = []
if {hole_count} >= 2:
    base_hole_positions = [(mm({base_positions[0] if base_positions else hole_margin}), mm({flange_width / 2.0}), mm({thickness / 2.0})), (mm({base_positions[1] if base_positions else hole_margin}), mm({flange_width / 2.0}), mm({thickness / 2.0}))]
for x_pos, y_pos, z_pos in base_hole_positions:
    bpy.ops.mesh.primitive_cylinder_add(radius=mm({hole_diameter / 2.0}), depth=mm({thickness * 2.5}), location=(x_pos, y_pos, z_pos))
    hole_cutter = bpy.context.active_object
    apply_transforms(hole_cutter)
    apply_boolean(base_leg, hole_cutter, modifier_name='BaseHole')

if {hole_count} >= 4:
    for z_pos in (mm({vertical_positions[0] if vertical_positions else hole_margin}), mm({vertical_positions[1] if vertical_positions else hole_margin})):
        bpy.ops.mesh.primitive_cylinder_add(radius=mm({hole_diameter / 2.0}), depth=mm({thickness * 2.5}), location=(mm({thickness / 2.0}), mm({flange_width / 2.0}), z_pos))
        vertical_hole = bpy.context.active_object
        vertical_hole.rotation_euler = (0.0, math.radians(90.0), 0.0)
        apply_transforms(vertical_hole)
        apply_boolean(base_leg, vertical_hole, modifier_name='VerticalHole')
"""
    gusset_code = ""
    if gusset:
        gusset_code = f"""
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mm({thickness / 2.0}), mm({flange_width / 2.0}), mm({vertical_height / 4.0})))
gusset_block = bpy.context.active_object
gusset_block.scale = (mm({thickness / 2.0}), mm({flange_width / 2.0}), mm({vertical_height / 4.0}))
apply_transforms(gusset_block)
"""
    gusset_join_code = "apply_boolean(base_leg, gusset_block, modifier_name='JoinGusset')\n" if gusset else ""
    return f"""bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mm({base_length / 2.0}), mm({flange_width / 2.0}), mm({thickness / 2.0})))
base_leg = bpy.context.active_object
base_leg.scale = (mm({base_length / 2.0}), mm({flange_width / 2.0}), mm({thickness / 2.0}))
apply_transforms(base_leg)

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mm({thickness / 2.0}), mm({flange_width / 2.0}), mm({vertical_height / 2.0})))
vertical_leg = bpy.context.active_object
vertical_leg.scale = (mm({thickness / 2.0}), mm({flange_width / 2.0}), mm({vertical_height / 2.0}))
apply_transforms(vertical_leg)
{gusset_code}
apply_boolean(base_leg, vertical_leg, modifier_name='JoinBracket')
{gusset_join_code}
{holes}
final_obj = base_leg
final_obj = finalize_object(final_obj)"""


def _build_cable_clip_script(plan: GenerationPlan) -> str:
    width = plan.dimensions["clip_width_mm"]
    opening = plan.dimensions["opening_mm"]
    depth = plan.dimensions["depth_mm"]
    thickness = plan.dimensions["thickness_mm"]
    cable_diameter = float(plan.features.get("cable_diameter_mm", max(opening - 2.0, 1.0)))
    base_length = float(plan.features.get("base_length_mm", width))
    mount_hole = float(plan.features.get("mount_hole_mm", 0.0))
    arm_height = max(cable_diameter + (thickness * 2.0), thickness * 2.5)
    half_span = (opening / 2.0) + (thickness / 2.0)
    hole_code = ""
    if mount_hole > 0:
        hole_code = f"""
bpy.ops.mesh.primitive_cylinder_add(radius=mm({mount_hole / 2.0}), depth=mm({thickness * 2.5}), location=(0.0, 0.0, 0.0))
clip_mount_hole = bpy.context.active_object
clip_mount_hole.rotation_euler = (math.radians(90.0), 0.0, 0.0)
apply_boolean(base_plate, clip_mount_hole, modifier_name='ClipMountHole')
"""
    return f"""bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.0))
base_plate = bpy.context.active_object
base_plate.scale = (mm({base_length / 2.0}), mm({thickness / 2.0}), mm({width / 2.0}))
{hole_code}

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, mm({-(depth / 2.0) + thickness}), 0.0))
back_bar = bpy.context.active_object
back_bar.scale = (mm({width / 2.0}), mm({thickness / 2.0}), mm({arm_height / 2.0}))

clip_parts = [base_plate, back_bar]
for x_offset in (-mm({half_span}), mm({half_span})):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_offset, mm({depth * 0.12}), 0.0))
    arm = bpy.context.active_object
    arm.scale = (mm({thickness / 2.0}), mm({depth / 2.0}), mm({arm_height / 2.0}))
    clip_parts.append(arm)

final_obj = join_objects(clip_parts)"""


def _build_vessel_script(plan: GenerationPlan) -> str:
    diameter = plan.dimensions["diameter_mm"]
    height = plan.dimensions["height_mm"]
    wall = float(plan.features["wall_thickness_mm"])
    drain = float(plan.features["drain_hole_mm"])
    inner_radius = max((diameter / 2.0) - wall, wall)
    drain_code = ""
    if drain > 0:
        drain_code = f"""
bpy.ops.mesh.primitive_cylinder_add(radius=mm({drain / 2.0}), depth=mm({wall * 3.0}), location=(0.0, 0.0, mm({-(height / 2.0) + (wall / 2.0)})))
drain_cutter = bpy.context.active_object
apply_boolean(outer_vessel, drain_cutter, modifier_name='DrainHole')
"""
    return f"""bpy.ops.mesh.primitive_cylinder_add(radius=mm({diameter / 2.0}), depth=mm({height}), location=(0.0, 0.0, 0.0))
outer_vessel = bpy.context.active_object

bpy.ops.mesh.primitive_cylinder_add(radius=mm({inner_radius}), depth=mm({height}), location=(0.0, 0.0, mm({wall})))
inner_vessel = bpy.context.active_object
apply_boolean(outer_vessel, inner_vessel, modifier_name='InnerCavity')
{drain_code}
final_obj = outer_vessel"""


def _build_gear_script(plan: GenerationPlan) -> str:
    diameter = plan.dimensions["diameter_mm"]
    thickness = plan.dimensions["thickness_mm"]
    teeth = int(plan.features["tooth_count"])
    center_hole = float(plan.features["center_hole_mm"])
    ring_radius = (diameter / 2.0) * 0.88
    tooth_length = max(diameter * 0.10, 3.0)
    tooth_width = max((diameter * 3.14159) / (teeth * 3.0), 2.0)
    bore_code = ""
    if center_hole > 0:
        bore_code = f"""
bpy.ops.mesh.primitive_cylinder_add(radius=mm({center_hole / 2.0}), depth=mm({thickness * 2.0}), location=(0.0, 0.0, 0.0))
bore_cutter = bpy.context.active_object
apply_boolean(gear_base, bore_cutter, modifier_name='CenterBore')
"""
    return f"""bpy.ops.mesh.primitive_cylinder_add(radius=mm({diameter / 2.0}), depth=mm({thickness}), location=(0.0, 0.0, 0.0))
gear_base = bpy.context.active_object

tooth_objects = [gear_base]
for index in range({teeth}):
    angle = (math.tau / {teeth}) * index
    x_pos = math.cos(angle) * mm({ring_radius})
    y_pos = math.sin(angle) * mm({ring_radius})
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_pos, y_pos, 0.0))
    tooth = bpy.context.active_object
    tooth.scale = (mm({tooth_length / 2.0}), mm({tooth_width / 2.0}), mm({thickness / 2.0}))
    tooth.rotation_euler = (0.0, 0.0, angle)
    tooth_objects.append(tooth)

final_obj = join_objects(tooth_objects)
gear_base = final_obj
{bore_code}
final_obj = gear_base"""


def _build_adapter_script(plan: GenerationPlan) -> str:
    large_diameter = plan.dimensions["large_diameter_mm"]
    small_diameter = plan.dimensions["small_diameter_mm"]
    length = plan.dimensions["length_mm"]
    center_hole = float(plan.features["center_hole_mm"])
    step_ratio = float(plan.features.get("step_ratio", 0.5))
    flange_diameter = float(plan.features.get("flange_diameter_mm", 0.0))
    flange_code = ""
    if flange_diameter > large_diameter:
        flange_code = f"""
bpy.ops.mesh.primitive_cylinder_add(radius=mm({flange_diameter / 2.0}), depth=mm({max(length * 0.15, 3.0)}), location=(0.0, 0.0, mm({(length / 2.0) - max(length * 0.075, 1.5)})))
adapter_flange = bpy.context.active_object
"""
    hole_code = ""
    if center_hole > 0:
        hole_code = f"""
bpy.ops.mesh.primitive_cylinder_add(radius=mm({center_hole / 2.0}), depth=mm({length * 1.5}), location=(0.0, 0.0, 0.0))
adapter_hole = bpy.context.active_object
apply_boolean(final_obj, adapter_hole, modifier_name='AdapterHole')
"""
    top_len = length * step_ratio
    bottom_len = length - top_len
    join_objects = "[large_section, small_section" + (", adapter_flange" if flange_code else "") + "]"
    return f"""bpy.ops.mesh.primitive_cylinder_add(radius=mm({large_diameter / 2.0}), depth=mm({top_len}), location=(0.0, 0.0, mm({(length / 2.0) - (top_len / 2.0)})))
large_section = bpy.context.active_object

bpy.ops.mesh.primitive_cylinder_add(radius=mm({small_diameter / 2.0}), depth=mm({bottom_len}), location=(0.0, 0.0, mm({-(length / 2.0) + (bottom_len / 2.0)})))
small_section = bpy.context.active_object
{flange_code}
final_obj = join_objects({join_objects})
{hole_code}"""


def _build_panel_plate_script(plan: GenerationPlan) -> str:
    width = plan.dimensions["width_mm"]
    height = plan.dimensions["height_mm"]
    thickness = plan.dimensions["thickness_mm"]
    hole_diameter = float(plan.features["hole_diameter_mm"])
    hole_pattern = str(plan.features.get("hole_pattern", "none"))
    hole_spacing = float(plan.features.get("hole_spacing_mm", 0.0))
    holes = ""
    if hole_diameter > 0:
        if hole_pattern == "pair_horizontal":
            x_offset = min(hole_spacing / 2.0, (width / 2.0) - max(hole_diameter, 6.0))
            holes = f"""
for x_pos in (-mm({x_offset}), mm({x_offset})):
    bpy.ops.mesh.primitive_cylinder_add(radius=mm({hole_diameter / 2.0}), depth=mm({thickness * 2.5}), location=(x_pos, 0.0, 0.0))
    plate_hole = bpy.context.active_object
    plate_hole.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    apply_boolean(panel, plate_hole, modifier_name='PanelHole')
"""
        else:
            x_offset = max((width / 2.0) - max(hole_diameter * 1.5, 8.0), hole_diameter)
            z_offset = max((height / 2.0) - max(hole_diameter * 1.5, 8.0), hole_diameter)
            holes = f"""
for x_pos in (-mm({x_offset}), mm({x_offset})):
    for z_pos in (-mm({z_offset}), mm({z_offset})):
        bpy.ops.mesh.primitive_cylinder_add(radius=mm({hole_diameter / 2.0}), depth=mm({thickness * 2.5}), location=(x_pos, 0.0, z_pos))
        plate_hole = bpy.context.active_object
        plate_hole.rotation_euler = (math.radians(90.0), 0.0, 0.0)
        apply_boolean(panel, plate_hole, modifier_name='PanelHole')
"""
    return f"""bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.0))
panel = bpy.context.active_object
panel.scale = (mm({width / 2.0}), mm({thickness / 2.0}), mm({height / 2.0}))
{holes}
final_obj = panel"""


def _build_standoff_script(plan: GenerationPlan) -> str:
    outer_diameter = plan.dimensions["outer_diameter_mm"]
    length = plan.dimensions["length_mm"]
    inner_diameter = float(plan.features["inner_diameter_mm"])
    profile = str(plan.features.get("profile", "round"))
    vertices = 6 if profile == "hex" else 32
    return f"""bpy.ops.mesh.primitive_cylinder_add(vertices={vertices}, radius=mm({outer_diameter / 2.0}), depth=mm({length}), location=(0.0, 0.0, 0.0))
standoff = bpy.context.active_object

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=mm({inner_diameter / 2.0}), depth=mm({length * 1.5}), location=(0.0, 0.0, 0.0))
standoff_hole = bpy.context.active_object
apply_boolean(standoff, standoff_hole, modifier_name='CenterHole')
final_obj = standoff"""


def _build_hook_mount_script(plan: GenerationPlan) -> str:
    base_width = plan.dimensions["base_width_mm"]
    base_height = plan.dimensions["base_height_mm"]
    arm_length = plan.dimensions["arm_length_mm"]
    thickness = plan.dimensions["thickness_mm"]
    hole_diameter = float(plan.features["mount_hole_mm"])
    hole_count = int(plan.features.get("mount_hole_count", 0))
    hook_drop = float(plan.features.get("hook_drop_mm", max(arm_length * 0.25, thickness * 2.0)))
    holes = ""
    if hole_diameter > 0 and hole_count > 0:
        z_offset = max((base_height / 2.0) - max(hole_diameter * 1.8, 10.0), hole_diameter)
        if hole_count == 1:
            holes = f"""
for z_pos in (0.0,):
    bpy.ops.mesh.primitive_cylinder_add(radius=mm({hole_diameter / 2.0}), depth=mm({thickness * 2.5}), location=(0.0, 0.0, z_pos))
    mount_hole = bpy.context.active_object
    mount_hole.rotation_euler = (0.0, math.radians(90.0), 0.0)
    apply_boolean(base_plate, mount_hole, modifier_name='MountHole')
"""
        else:
            holes = f"""
for z_pos in (-mm({z_offset}), mm({z_offset})):
    bpy.ops.mesh.primitive_cylinder_add(radius=mm({hole_diameter / 2.0}), depth=mm({thickness * 2.5}), location=(0.0, 0.0, z_pos))
    mount_hole = bpy.context.active_object
    mount_hole.rotation_euler = (0.0, math.radians(90.0), 0.0)
    apply_boolean(base_plate, mount_hole, modifier_name='MountHole')
"""
    return f"""bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.0))
base_plate = bpy.context.active_object
base_plate.scale = (mm({thickness / 2.0}), mm({base_width / 2.0}), mm({base_height / 2.0}))

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mm({arm_length / 2.0}), 0.0, mm({base_height * 0.18})))
hook_arm = bpy.context.active_object
hook_arm.scale = (mm({arm_length / 2.0}), mm({thickness / 2.0}), mm({thickness / 2.0}))

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mm({arm_length}), 0.0, mm({(base_height * 0.18) - hook_drop})))
hook_lip = bpy.context.active_object
hook_lip.scale = (mm({thickness / 2.0}), mm({thickness / 2.0}), mm({hook_drop / 2.0}))
{holes}
final_obj = join_objects([base_plate, hook_arm, hook_lip])"""


def _build_phone_stand_script(plan: GenerationPlan) -> str:
    width = plan.dimensions["width_mm"]
    height = plan.dimensions["height_mm"]
    base_depth = plan.dimensions["base_depth_mm"]
    base_thickness = plan.dimensions.get("base_thickness_mm", plan.dimensions["thickness_mm"])
    support_thickness = plan.dimensions.get("support_thickness_mm", max(base_thickness * 0.85, 4.0))
    slot_width = plan.dimensions["slot_width_mm"]
    lip_width = plan.dimensions.get("lip_width_mm", max(slot_width + 16.0, width * 0.55))
    lip_height = plan.dimensions.get("lip_height_mm", max(base_thickness * 0.8, 4.0))
    lip_depth = plan.dimensions.get("lip_depth_mm", max(base_thickness * 0.9, 4.0))
    angle_deg = float(plan.dimensions.get("angle_deg", 65.0))
    with_cable_cutout = bool(plan.features.get("with_cable_cutout"))
    cable_cutout_width = float(plan.features.get("cable_cutout_width_mm", max(slot_width * 0.65, 6.0)))
    cable_cutout_depth = float(plan.features.get("cable_cutout_depth_mm", max(base_thickness * 2.5, 8.0)))
    cable_cutout_height = float(plan.features.get("cable_cutout_height_mm", max(base_thickness * 1.2, 6.0)))
    support_width = max(width * 0.86, slot_width + 18.0)
    support_rotation = 90.0 - angle_deg

    cable_cutout_code = ""
    if with_cable_cutout:
        cable_cutout_code = f"""
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, mm({-(base_depth / 2.0) + (cable_cutout_depth / 2.0) + max(base_thickness * 0.1, 0.25)}), mm({cable_cutout_height / 2.0})))
cable_cutout = bpy.context.active_object
cable_cutout.scale = (mm({cable_cutout_width / 2.0}), mm({cable_cutout_depth / 2.0}), mm({cable_cutout_height / 2.0}))
apply_boolean(final_obj, cable_cutout, modifier_name='CableCutout')
"""

    return f"""bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, mm({base_thickness / 2.0})))
base_plate = bpy.context.active_object
base_plate.scale = (mm({width / 2.0}), mm({base_depth / 2.0}), mm({base_thickness / 2.0}))

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, mm({(base_depth / 2.0) - (max(base_thickness * 1.1, 4.0) / 2.0)}), mm({base_thickness + (max(base_thickness * 1.35, 6.0) / 2.0)})))
support_anchor = bpy.context.active_object
support_anchor.scale = (mm({max(support_width * 0.72, slot_width + 10.0) / 2.0}), mm({max(base_thickness * 1.1, 4.0) / 2.0}), mm({max(base_thickness * 1.35, 6.0) / 2.0}))

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, mm({(base_depth / 2.0) - (support_thickness / 2.0) - max(base_thickness * 0.35, 1.5)}), mm({base_thickness + (height / 2.0)})))
support_panel = bpy.context.active_object
support_panel.scale = (mm({support_width / 2.0}), mm({support_thickness / 2.0}), mm({height / 2.0}))
support_panel.rotation_euler = (math.radians({support_rotation}), 0.0, 0.0)

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, mm({-(base_depth / 2.0) + (lip_depth / 2.0) + max(base_thickness * 0.15, 0.5)}), mm({base_thickness + (lip_height / 2.0) - max(base_thickness * 0.1, 0.25)})))
retaining_lip = bpy.context.active_object
retaining_lip.scale = (mm({lip_width / 2.0}), mm({lip_depth / 2.0}), mm({lip_height / 2.0}))

final_obj = join_objects([base_plate, support_anchor, support_panel, retaining_lip])
{cable_cutout_code}
final_obj = finalize_object(final_obj)"""


def _build_primitive_assembly_script(plan: GenerationPlan) -> str:
    width = plan.dimensions["width_mm"]
    depth = plan.dimensions["depth_mm"]
    height = plan.dimensions["height_mm"]
    include_cube = bool(plan.features.get("include_cube"))
    include_cylinder = bool(plan.features.get("include_cylinder"))
    include_sphere = bool(plan.features.get("include_sphere"))
    lines = []
    object_names: list[str] = []
    if include_cube:
        lines.append(
            f"""bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mm({-(width * 0.35)}), 0.0, 0.0))
cube_part = bpy.context.active_object
cube_part.scale = (mm({width * 0.25}), mm({depth * 0.25}), mm({height * 0.25}))"""
        )
        object_names.append("cube_part")
    if include_cylinder:
        lines.append(
            f"""bpy.ops.mesh.primitive_cylinder_add(radius=mm({min(width, depth) * 0.14}), depth=mm({height * 0.9}), location=(0.0, 0.0, 0.0))
cylinder_part = bpy.context.active_object"""
        )
        object_names.append("cylinder_part")
    if include_sphere:
        lines.append(
            f"""bpy.ops.mesh.primitive_uv_sphere_add(radius=mm({min(width, depth, height) * 0.18}), location=(mm({width * 0.35}), 0.0, mm({height * 0.1})))
sphere_part = bpy.context.active_object"""
        )
        object_names.append("sphere_part")
    joined = ", ".join(object_names) if object_names else ""
    lines.append(f"final_obj = join_objects([{joined}])" if joined else "final_obj = None")
    return "\n\n".join(lines)
