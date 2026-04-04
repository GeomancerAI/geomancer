# Blender API Rules For Geomancer

## Scene Setup Rules

- Import `bpy`
- Clear the scene at the start of the script
- Define `def mm(value): return value / 1000.0`
- Use exact requested dimensions

## Supported Primitive Operators

- `bpy.ops.mesh.primitive_uv_sphere_add`
- `bpy.ops.mesh.primitive_cylinder_add`
- `bpy.ops.mesh.primitive_cube_add`

## Object Access Rules

- Use `bpy.context.active_object` after creating an object
- Name important objects clearly

## Spatial Conventions

- `Z` = up/down
- `Y` = front/back
- `X` = left/right
- `front` = `+Y`
- `back` = `-Y`
- `top` = `+Z`
- `bottom` = `-Z`

## Boolean Rules

- The boolean modifier belongs on the target object being cut
- Assign the cutter object explicitly
- Set `operation = 'DIFFERENCE'`
- Activate the target object before applying the modifier

## Solidify Rules

- Only use safe common properties:
- `thickness`
- `offset`
- `use_quality_normals`
- Do not use speculative properties like `edge_crease`
- Use the exact requested thickness, do not halve it

## Transform Rules

- Prefer direct property assignment such as `object.rotation_euler`
- Avoid unnecessary `bpy.ops.transform` calls where direct assignment is safer

## Safety Rules

- No markdown in generated code
- No explanations outside Python
- Keep scripts minimal and runnable
- Avoid unsupported or uncertain `bpy` API calls
