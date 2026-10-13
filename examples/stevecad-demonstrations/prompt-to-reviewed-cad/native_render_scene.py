"""Native presentation template, embedded in the accepted workflow source.

The metadata marker is replaced with a JSON string literal by the declared jq
step. It never substitutes executable source from a design or provider.
"""
import bpy
import json
from mathutils import Matrix, Vector

basis = json.loads(__WRIGHT_BASIS_JSON_STRING__)  # noqa: F821 -- replaced template marker
run_id = '{{wright.run_id}}'
assert not bpy.app.is_job_running('RENDER')
scene_name = 'wright_' + run_id
assert bpy.data.scenes.get(scene_name) is None
assert basis['units'] == 'mm'
items = basis['items']
assert items and len(items) == basis['solids']
scene = bpy.data.scenes.new(scene_name)
scene.world = bpy.data.worlds.new(scene_name + '_world')
bpy.context.window.scene = scene
scene['wright_render_run'] = run_id
scene['wright_cad_scene_owner'] = basis['build_id']
scene['wright_cad_document'] = basis['document_id']
scene['wright_cad_revision'] = basis['revision']
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
bpy.ops.import_scene.gltf(filepath='/inputs/automatic-transfer-001/{{wright.run_id}}/design.glb')
loaded = [obj for obj in scene.objects if obj.type == 'MESH']
assert len(loaded) == len(items)
before = [(obj, obj.matrix_world.copy()) for obj in loaded]
for obj, world in before:
    obj.parent = None
    obj.matrix_world = Matrix.Scale(.001, 4) @ world
bpy.context.view_layer.update()
materials = {}
matched = []
records = []
all_corners = []
for obj in loaded:
    vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
    measured = [min(v[k] for v in vertices)*1000 for k in range(3)] + [max(v[k] for v in vertices)*1000 for k in range(3)]
    candidates = [i for i in items if max(abs(a-b) for a,b in zip(measured, i['extent_mm'])) <= .1]
    assert len(candidates) == 1, (obj.name, measured, len(candidates))
    item = candidates[0]
    assert item['instance'] not in matched
    matched.append(item['instance'])
    obj.name = item['instance']
    obj['wright_cad_body'] = True
    obj['cad_component'] = item['component']
    obj['cad_revision'] = basis['revision']
    all_corners.extend(vertices)
    error = max(abs(a-b) for a,b in zip(measured,item['extent_mm']))
    color = item.get('color') or '#aaaaaa'
    assert len(color) == 7 and color[0] == '#'
    metal = item.get('material') == 'stainless-304'
    key = (color, metal, item.get('finish'))
    if key not in materials:
        material = bpy.data.materials.new('native_' + color[1:] + str(metal))
        material.use_nodes = True
        shader = material.node_tree.nodes['Principled BSDF']
        rgb = [int(color[i:i+2],16)/255 for i in (1,3,5)]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        shader.inputs['Base Color'].default_value = tuple(linear) + (1,)
        shader.inputs['Metallic'].default_value = 1 if metal else 0
        shader.inputs['Roughness'].default_value = .28 if metal else .55
        materials[key] = material
    obj.data.materials.clear()
    obj.data.materials.append(materials[key])
    records.append({'instance':item['instance'], 'extent_error_mm':error, 'polygons':len(obj.data.polygons), 'color':color})
assert len(matched) == len(items)
bounds = [min(v[k] for v in all_corners) for k in range(3)] + [max(v[k] for v in all_corners) for k in range(3)]
assert max(abs(bounds[k]*1000-basis['extent_mm'][k]) for k in range(6)) <= .1
target = Vector([(bounds[k]+bounds[k+3])/2 for k in range(3)])
span = max(bounds[k+3]-bounds[k] for k in range(3))
assert .001 < span < 2, 'Qualified presentation size is 1 mm to 2 m'
bpy.ops.mesh.primitive_plane_add(size=span*12, location=(target.x,target.y,bounds[2]-.00002))
floor = bpy.context.object
floor.name = 'studio_floor_presentation_only'
floor['presentation_fixture'] = True
material = bpy.data.materials.new('neutral_studio_floor')
material.use_nodes = True
shader = material.node_tree.nodes['Principled BSDF']
shader.inputs['Base Color'].default_value = (.70,.70,.70,1)
shader.inputs['Roughness'].default_value = .9
floor.data.materials.append(material)
for name, offset, power, size in [('key',(.7,-.9,1.6),6,.95),('fill',(-1.1,-.3,1.1),3,1.1),('rim',(.3,1.4,1.4),4,.8)]:
    data = bpy.data.lights.new(name,'AREA')
    data.energy = power*(span/.37)**2
    data.shape = 'DISK'
    data.size = size*span
    obj = bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    obj.location = target + Vector(offset)*span
    obj.rotation_euler = (target-obj.location).to_track_quat('-Z','Y').to_euler()
camera = bpy.data.objects.new('studio_camera',bpy.data.cameras.new('studio_camera'))
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.type = 'ORTHO'
camera.data.clip_start = .0001
camera.data.clip_end = 20
scene['wright_cad_target'] = list(target)
scene['wright_native_mesh_count'] = len(records)
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.84,.84,.84,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .2
scene.render.resolution_x = 1000
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.use_denoising = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = -1
print(json.dumps({'document_id':basis['document_id'],'revision':basis['revision'],'build_id':basis['build_id'],'run_id':run_id,'CAD_meshes':len(records),'meters_per_input_mm':.001,'geometry_changes':False,'records':records}))
