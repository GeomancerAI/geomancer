import bpy
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

    width = max(float(width_mm), max(float(thickness_mm) * 3.0, 0.01))
    height = max(float(height_mm), max(float(thickness_mm) * 4.0, 0.01))
    depth = max(float(depth_mm), max(float(thickness_mm) * 3.0, 0.01))
    thickness = max(float(thickness_mm), 0.01)
    plate_depth = max(min(float(base_thickness_mm), depth * 0.58), thickness * 1.25)
    hook_projection = max(min(float(hook_length_mm), max(depth - plate_depth, thickness * 2.5)), thickness * 2.5)
    hook_radius = max(min(float(hook_radius_mm), hook_projection * 0.45), thickness * 0.75)
    hook_angle = math.radians(max(min(float(hook_angle_deg), 35.0), 8.0))
    hook_base_z = max(-height * 0.12, -(height / 2.0) + max(thickness * 1.8, 6.0))
    hook_start_upper = min(hook_base_z + max(thickness * 0.9, 3.0), (height / 2.0) - max(thickness * 0.9, 3.0))
    hook_start_lower = max(hook_base_z - max(thickness * 0.55, 1.0), -(height / 2.0) + max(thickness * 1.5, 4.0))
    hook_tip_z = min(hook_start_upper + max(math.tan(hook_angle) * hook_projection, thickness * 1.2), (height / 2.0) - max(thickness * 0.6, 2.0))
    hook_tip_return_z = max(hook_tip_z - max(hook_radius * 0.45, thickness * 0.8), hook_start_lower)
    profile = [
        (0.0, -(height / 2.0)),
        (0.0, height / 2.0),
        (plate_depth, height / 2.0),
        (plate_depth, hook_start_upper),
        (plate_depth + hook_projection, hook_tip_z),
        (plate_depth + hook_projection - hook_radius, hook_tip_return_z),
        (plate_depth, hook_start_lower),
        (plate_depth, -(height / 2.0)),
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
# Family: hook_mount
# Recipe: hook_mount
# Execution recipe: hook_mount
# Family implementation: hook_mount
# Implementation ID: hook_mount_wall_hook_v1
# Generation ID: gen-20260419212526-2001c010
# Object type: hook_mount

hook_mount_body = make_hook_mount_body(
    width_mm=mm(50.0),
    height_mm=mm(80.0),
    depth_mm=mm(35.0),
    thickness_mm=mm(6.0),
    base_thickness_mm=mm(7.5),
    hook_length_mm=mm(25.2),
    hook_radius_mm=mm(9.0),
    hook_angle_deg=18.0,
    final_name='hook_mount_body',
)

for z_pos in (mm(-20.0), mm(20.0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=mm(2.5), depth=mm(18.75), location=(0.0, mm(3.75), z_pos))
    mount_hole = bpy.context.active_object
    mount_hole.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    apply_transforms(mount_hole)
    apply_boolean(hook_mount_body, mount_hole, modifier_name='HookMountHole')


final_obj = hook_mount_body

final_obj = locals().get("final_obj")
if final_obj is None:
    final_obj = bpy.context.active_object
if final_obj is not None:
    final_obj = finalize_object(final_obj, "Geomancer_Final")