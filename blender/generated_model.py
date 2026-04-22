import bpy
import bmesh
import math

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def mm_to_m(value):
    return value / 1000.0

def mm(value):
    return mm_to_m(value)

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
    modifier.width = mm_to_m(width_mm)
    modifier.segments = segments
    modifier.profile = profile
    modifier.use_clamp_overlap = True
    set_active(obj)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj

def make_box_body(size_x_mm, size_y_mm, size_z_mm, final_name='GeomancerBox', location_mm=(0.0, 0.0, 0.0)):
    size_x = mm_to_m(size_x_mm)
    size_y = mm_to_m(size_y_mm)
    size_z = mm_to_m(size_z_mm)
    location = (mm_to_m(location_mm[0]), mm_to_m(location_mm[1]), mm_to_m(location_mm[2]))
    mesh = bpy.data.meshes.new(final_name + "_mesh")
    obj = bpy.data.objects.new(final_name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    hx = size_x / 2.0
    hy = size_y / 2.0
    hz = size_z / 2.0
    verts = [
        bm.verts.new((-hx, -hy, -hz)),
        bm.verts.new((hx, -hy, -hz)),
        bm.verts.new((hx, hy, -hz)),
        bm.verts.new((-hx, hy, -hz)),
        bm.verts.new((-hx, -hy, hz)),
        bm.verts.new((hx, -hy, hz)),
        bm.verts.new((hx, hy, hz)),
        bm.verts.new((-hx, hy, hz)),
    ]
    bm.faces.new((verts[0], verts[1], verts[2], verts[3]))
    bm.faces.new((verts[4], verts[5], verts[6], verts[7]))
    bm.faces.new((verts[0], verts[1], verts[5], verts[4]))
    bm.faces.new((verts[1], verts[2], verts[6], verts[5]))
    bm.faces.new((verts[2], verts[3], verts[7], verts[6]))
    bm.faces.new((verts[3], verts[0], verts[4], verts[7]))
    bm.normal_update()
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    obj.location = location
    return obj

def make_shell_body(width_mm, depth_mm, height_mm, wall_thickness_mm, base_thickness_mm=0.0, front_opening=False, opening_width_mm=0.0, opening_height_mm=0.0, final_name='GeomancerShell'):
    width = mm_to_m(width_mm)
    depth = mm_to_m(depth_mm)
    height = mm_to_m(height_mm)
    wall = mm_to_m(wall_thickness_mm)
    base_thickness = mm_to_m(base_thickness_mm) if base_thickness_mm > 0 else wall
    wall = max(wall, 0.0015)
    wall = min(wall, max(min(width, depth) * 0.45, 0.0015), max((height - 0.0005) / 2.0, 0.0015))
    base_thickness = max(base_thickness, wall)
    base_thickness = min(base_thickness, max(height - wall - 0.0005, wall))
    inner_width = max(width - (wall * 2.0), wall)
    inner_depth = max(depth - (wall * 2.0), wall)
    inner_height = max(height - base_thickness + wall, wall)
    inner_bottom_z = -(height / 2.0) + base_thickness
    inner_z = inner_bottom_z + (inner_height / 2.0)
    bevel_m = max(min(wall * 0.18, 0.001), 0.00025)

    outer_box = make_box_body(width_mm, depth_mm, height_mm, final_name=final_name)
    inner_box = make_box_body(inner_width * 1000.0, inner_depth * 1000.0, inner_height * 1000.0, final_name=f"{final_name}_inner", location_mm=(0.0, 0.0, inner_z * 1000.0))
    apply_boolean(outer_box, inner_box, modifier_name='InnerCavity')
    if front_opening:
        opening_width = mm_to_m(opening_width_mm) if opening_width_mm > 0 else inner_width
        opening_height = mm_to_m(opening_height_mm) if opening_height_mm > 0 else inner_height
        opening_center_z = max(base_thickness + (opening_height / 2.0), opening_height / 2.0)
        front_cutter = make_box_body(opening_width * 1000.0, wall * 1000.0 * 1.6, opening_height * 1000.0, final_name=f"{final_name}_front", location_mm=(0.0, ((depth / 2.0) - (wall / 2.0)) * 1000.0, (opening_center_z - (height / 2.0)) * 1000.0))
        apply_boolean(outer_box, front_cutter, modifier_name='FrontOpening')
    apply_bevel(outer_box, bevel_m * 1000.0, modifier_name='ShellBevel')
    return outer_box

def make_bracket_body(base_length_mm, flange_width_mm, vertical_height_mm, thickness_mm, final_name='GeomancerBracket'):
    mesh = bpy.data.meshes.new(final_name + "_mesh")
    obj = bpy.data.objects.new(final_name, mesh)
    bpy.context.collection.objects.link(obj)

    base_length = mm_to_m(base_length_mm)
    flange_width = mm_to_m(flange_width_mm)
    vertical_height = mm_to_m(vertical_height_mm)
    thickness = mm_to_m(thickness_mm)
    bm = bmesh.new()
    profile = [
        (0.0, 0.0),
        (base_length, 0.0),
        (base_length, thickness),
        (thickness, thickness),
        (thickness, vertical_height),
        (0.0, vertical_height),
    ]
    face_verts = [bm.verts.new((x, 0.0, z)) for x, z in profile]
    bm.faces.new(face_verts)
    bm.normal_update()
    extruded = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    extruded_verts = [elem for elem in extruded['geom'] if isinstance(elem, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=extruded_verts, vec=(0.0, flange_width, 0.0))
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

    base_thickness = max(mm_to_m(thickness_mm), 0.003)
    lip_height = max(mm_to_m(lip_height_mm), 0.003)
    depth = max(mm_to_m(depth_mm), base_thickness * 2.0)
    width = max(mm_to_m(width_mm), base_thickness * 2.0)
    height = max(mm_to_m(height_mm), base_thickness + lip_height + 0.003)
    cradle_depth = max(min(mm_to_m(cradle_depth_mm), depth * 0.45), base_thickness * 4.0)
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

    width = max(mm_to_m(width_mm), 0.012)
    height = max(mm_to_m(height_mm), 0.024)
    depth = max(mm_to_m(depth_mm), 0.01)
    thickness = max(mm_to_m(thickness_mm), 0.003)
    plate_thickness = max(min(mm_to_m(base_thickness_mm), depth * 0.45), thickness * 1.25)
    hook_length = max(min(mm_to_m(hook_length_mm), depth - plate_thickness), max(depth * 0.28, 0.01))
    hook_length = min(hook_length, max(depth * 0.58, plate_thickness + thickness * 2.5))
    hook_radius = max(min(mm_to_m(hook_radius_mm), hook_length * 0.35), thickness * 0.75)
    hook_angle = math.radians(max(min(float(hook_angle_deg), 35.0), 12.0))
    plate_top_z = height / 2.0
    plate_bottom_z = -(height / 2.0)
    arm_base_z = max(plate_bottom_z + max(height * 0.24, thickness * 3.0), plate_bottom_z + thickness * 2.5)
    arm_base_z = min(arm_base_z, plate_top_z - max(thickness * 2.5, height * 0.18))
    arm_start_x = min(plate_thickness + max(hook_length * 0.42, thickness * 2.5), plate_thickness + hook_length * 0.72)
    arm_tip_x = min(plate_thickness + hook_length, depth)
    if arm_tip_x <= arm_start_x + max(thickness * 1.8, 0.003):
        arm_tip_x = arm_start_x + max(thickness * 2.6, 0.01)
    tip_backoff = max(min(hook_radius, (arm_tip_x - arm_start_x) * 0.3), thickness * 1.1)
    hook_tip_z = min(arm_base_z + max(thickness * 1.15, min((arm_tip_x - arm_start_x) * math.tan(hook_angle) * 0.18, height * 0.12)), plate_top_z - max(thickness * 0.7, 0.002))
    if hook_tip_z <= arm_base_z + thickness * 0.25:
        hook_tip_z = min(arm_base_z + max(thickness * 1.25, 0.004), plate_top_z - max(thickness * 0.7, 0.002))
    profile = [
        (0.0, plate_bottom_z),
        (0.0, plate_top_z),
        (plate_thickness, plate_top_z),
        (plate_thickness, arm_base_z + thickness),
        (arm_start_x, arm_base_z + thickness),
        (arm_start_x, arm_base_z),
        (arm_tip_x - tip_backoff, arm_base_z),
        (arm_tip_x, hook_tip_z),
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

# Recipe schema version: 1.0
# Family: crate
# Recipe: crate
# Execution recipe: crate
# Family implementation: crate
# Implementation ID: crate_v1
# Generation ID: gen-20260422184358-f20f3b5a
# Object type: crate

crate_body = make_box_body(
    size_x_mm=80.0,
    size_y_mm=80.0,
    size_z_mm=60.0,
    final_name='crate_body',
    location_mm=(-12.0, 0.0, 0.0),
)

crate_cap = make_box_body(
    size_x_mm=67.2,
    size_y_mm=67.2,
    size_z_mm=10.799999999999999,
    final_name='crate_cap',
    location_mm=(6.4, 0.0, 9.0),
)

crate_body = join_objects([crate_body, crate_cap], final_name='union_crate_body_crate_cap')

final_obj = crate_body

final_obj = locals().get("final_obj")
if final_obj is None:
    final_obj = bpy.context.active_object
if final_obj is not None:
    final_obj = finalize_object(final_obj, "Geomancer_Final")