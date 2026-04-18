import bpy
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

# Family: enclosure
# Recipe: box_shell

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.0))
outer_box = bpy.context.active_object
outer_box.name = "Geomancer_Box"
outer_box.scale = (mm(60.0), mm(40.0), mm(25.0))

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, mm(0.0)))
inner_box = bpy.context.active_object
inner_box.scale = (mm(57.0), mm(37.0), mm(22.0))
apply_boolean(outer_box, inner_box, modifier_name='InnerCavity')

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, mm(38.5), mm(-9.5)))
front_cutter = bpy.context.active_object
front_cutter.scale = (mm(30.0), mm(4.800000000000001), mm(12.5))
apply_boolean(outer_box, front_cutter, modifier_name='FrontOpening')

final_obj = outer_box

final_obj = locals().get("final_obj")
if final_obj is None:
    final_obj = bpy.context.active_object
if final_obj is not None:
    final_obj.name = "Geomancer_Final"
    set_active(final_obj)