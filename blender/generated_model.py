import bpy
from math import radians

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def mm(value):
    return value / 1000.0

# Main sphere from exact requested diameter.
bpy.ops.mesh.primitive_uv_sphere_add(radius=mm(25.4), location=(0.0, 0.0, 0.0))
target_obj = bpy.context.active_object
target_obj.name = "Geomancer_Model"

solidify_mod = target_obj.modifiers.new(name="Solidify", type='SOLIDIFY')
solidify_mod.thickness = mm(1.5)
solidify_mod.offset = 1.0
solidify_mod.use_quality_normals = True

bpy.ops.object.select_all(action='DESELECT')
target_obj.select_set(True)
bpy.context.view_layer.objects.active = target_obj
bpy.ops.object.modifier_apply(modifier=solidify_mod.name)

bpy.ops.mesh.primitive_cylinder_add(radius=mm(45.0), depth=mm(10.0), location=(0.0, mm(75.0), 0.0))
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

bpy.data.objects.remove(recess_cutter_obj, do_unlink=True)

bpy.ops.mesh.primitive_cylinder_add(radius=mm(30.0), depth=mm(30.479999999999997), location=(0.0, mm(10.16), 0.0))
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

bpy.data.objects.remove(hole_cutter_obj, do_unlink=True)

# Shallow bottom flatten cut along the -Z side for a stable resting surface.
bpy.ops.mesh.primitive_cube_add(size=mm(101.6), location=(0.0, 0.0, mm(-70.19999999999999)))
bottom_cutter_obj = bpy.context.active_object
bottom_cutter_obj.name = "Geomancer_Bottom_Cutter"

bottom_bool_mod = target_obj.modifiers.new(name="BottomCut", type='BOOLEAN')
bottom_bool_mod.operation = 'DIFFERENCE'
bottom_bool_mod.object = bottom_cutter_obj

bpy.ops.object.select_all(action='DESELECT')
target_obj.select_set(True)
bpy.context.view_layer.objects.active = target_obj
bpy.ops.object.modifier_apply(modifier=bottom_bool_mod.name)

bpy.data.objects.remove(bottom_cutter_obj, do_unlink=True)

target_obj.name = "Geomancer_Final"