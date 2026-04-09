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

# Family: bracket
# Recipe: bracket

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, mm(3.0)))
base_leg = bpy.context.active_object
base_leg.scale = (mm(50.0), mm(15.0), mm(3.0))

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mm(-47.0), 0.0, mm(40.0)))
vertical_leg = bpy.context.active_object
vertical_leg.scale = (mm(3.0), mm(15.0), mm(40.0))


final_obj = join_objects([base_leg, vertical_leg])

final_obj = locals().get("final_obj")
if final_obj is None:
    final_obj = bpy.context.active_object
if final_obj is not None:
    final_obj.name = "Geomancer_Final"
    set_active(final_obj)