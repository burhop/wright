"""Fixed Blender mesh-repair operation for the printed-part campaign.

The model creates the source geometry.  This operation performs the repeatable
manufacturing cleanup, measurement, bed placement, STL export, and preview in
the lifecycle-owned Blender process.  Paths come only from a staged,
same-attempt configuration validated by the MCP wrapper.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blender_code(configuration: dict) -> str:
    source = str(Path(configuration["source"]).resolve())
    repaired = str(Path(configuration["repaired"]).resolve())
    preview = str(Path(configuration["preview"]).resolve())
    triangle_limit = int(configuration.get("triangle_limit", 80_000))
    merge_tolerance = float(configuration.get("merge_tolerance_mm", 0.001))
    degenerate_tolerance = float(
        configuration.get("degenerate_tolerance_mm", 0.000001)
    )
    object_name = str(configuration["object_name"])
    return f'''import bpy, bmesh, json, math, mathutils

source = {source!r}
repaired = {repaired!r}
preview = {preview!r}
triangle_limit = {triangle_limit!r}
merge_tolerance = {merge_tolerance!r}
degenerate_tolerance = {degenerate_tolerance!r}
object_name = {object_name!r}

before_objects = set(bpy.context.scene.objects)
result = bpy.ops.wm.stl_import(filepath=source, global_scale=1.0)
if result != {{'FINISHED'}}:
    raise RuntimeError('STL import failed: ' + str(result))
owned = [item for item in bpy.context.scene.objects if item not in before_objects and item.type == 'MESH']
if len(owned) == 0:
    raise RuntimeError('STL import created no mesh object')
bpy.ops.object.select_all(action='DESELECT')
for item in owned:
    item.select_set(True)
bpy.context.view_layer.objects.active = owned[0]
if len(owned) > 1:
    bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = object_name
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

def metrics(item):
    bm = bmesh.new()
    bm.from_mesh(item.data)
    bm.normal_update()
    vertices = len(bm.verts)
    edges = len(bm.edges)
    faces = len(bm.faces)
    triangles = sum(max(0, len(face.verts) - 2) for face in bm.faces)
    boundary = sum(1 for edge in bm.edges if edge.is_boundary)
    nonmanifold = sum(1 for edge in bm.edges if not edge.is_manifold)
    degenerate = sum(1 for face in bm.faces if face.calc_area() <= 0.0000000001)
    remaining = set(bm.verts)
    components = 0
    while len(remaining) > 0:
        components += 1
        seed = remaining.pop()
        stack = [seed]
        while len(stack) > 0:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                neighbor = edge.other_vert(vertex)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    volume = float(bm.calc_volume(signed=True))
    bm.free()
    return {{'vertices':vertices,'edges':edges,'faces':faces,'triangles':triangles,'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'degenerate_faces':degenerate,'connected_components':components,'signed_volume_mm3':round(volume,6)}}

def dimensions(item):
    bpy.context.view_layer.update()
    return [round(float(value),6) for value in item.dimensions]

before_dimensions = dimensions(obj)
before_metrics = metrics(obj)
bm = bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=merge_tolerance)
bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=degenerate_tolerance)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.normal_update()
if bm.calc_volume(signed=True) < 0:
    bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.normal_update()
bm.to_mesh(obj.data)
bm.free()
obj.data.update()

clean_metrics = metrics(obj)
voxel_remesh_used = False
voxel_size_mm = None
voxel_iterations = 0
discarded_components = 0

def keep_largest_component(item):
    bm = bmesh.new()
    bm.from_mesh(item.data)
    remaining = set(bm.verts)
    components = []
    while len(remaining) > 0:
        seed = remaining.pop()
        component = {{seed}}
        stack = [seed]
        while len(stack) > 0:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                neighbor = edge.other_vert(vertex)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    removed = max(0, len(components) - 1)
    if removed > 0:
        largest = max(components, key=len)
        discard = [vertex for component in components if component is not largest for vertex in component]
        bmesh.ops.delete(bm, geom=discard, context='VERTS')
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.normal_update()
        if bm.calc_volume(signed=True) < 0:
            bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
            bm.normal_update()
        bm.to_mesh(item.data)
        item.data.update()
    bm.free()
    return removed

if clean_metrics['boundary_edges'] != 0 or clean_metrics['nonmanifold_edges'] != 0 or clean_metrics['connected_components'] != 1:
    voxel_size_mm = max(0.08, min(0.30, min(before_dimensions) / 100.0))
    while True:
        obj.data.remesh_voxel_size = voxel_size_mm
        obj.data.remesh_voxel_adaptivity = 0.0
        obj.data.use_remesh_preserve_volume = True
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.voxel_remesh()
        voxel_iterations += 1
        discarded_components += keep_largest_component(obj)
        clean_metrics = metrics(obj)
        topology_ok = clean_metrics['boundary_edges'] == 0 and clean_metrics['nonmanifold_edges'] == 0 and clean_metrics['connected_components'] == 1
        if topology_ok and clean_metrics['triangles'] <= triangle_limit:
            break
        if voxel_iterations >= 6:
            raise RuntimeError('Bounded voxel repair did not converge: ' + json.dumps(clean_metrics))
        triangle_factor = math.sqrt(max(1.0, clean_metrics['triangles'] / max(1.0, triangle_limit - 500.0)))
        voxel_size_mm *= max(1.15, min(2.0, triangle_factor * 1.05))
    remeshed_dimensions = dimensions(obj)
    for axis in range(3):
        if remeshed_dimensions[axis] <= 0:
            raise RuntimeError('Voxel remesh produced a zero dimension')
        obj.scale[axis] *= before_dimensions[axis] / remeshed_dimensions[axis]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.update()
    clean_metrics = metrics(obj)
    voxel_remesh_used = True
decimation_used = False

post_metrics = metrics(obj)
if post_metrics['boundary_edges'] != 0 or post_metrics['nonmanifold_edges'] != 0:
    raise RuntimeError('Repair did not retain closed manifold topology: ' + json.dumps(post_metrics))
if post_metrics['degenerate_faces'] != 0 or post_metrics['connected_components'] != 1:
    raise RuntimeError('Repair did not produce one nondegenerate component: ' + json.dumps(post_metrics))
if post_metrics['signed_volume_mm3'] <= 0 or post_metrics['triangles'] > triangle_limit:
    raise RuntimeError('Repair did not satisfy normals or triangle limit: ' + json.dumps(post_metrics))

# Preserve the model-authored axes and translate its lowest point onto the bed.
world_coordinates = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
minimum_z = min(point.z for point in world_coordinates)
obj.location.z -= minimum_z
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
bpy.context.view_layer.update()
final_dimensions = dimensions(obj)
final_metrics = metrics(obj)
if not all(value <= 256.000001 for value in final_dimensions):
    raise RuntimeError('Part does not fit the P1S 256 mm build cube: ' + str(final_dimensions))
if final_metrics['boundary_edges'] != 0 or final_metrics['nonmanifold_edges'] != 0 or final_metrics['connected_components'] != 1:
    raise RuntimeError('Bed placement changed retained topology: ' + json.dumps(final_metrics))

bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
export_result = bpy.ops.wm.stl_export(filepath=repaired, export_selected_objects=True, ascii_format=False, apply_modifiers=True, global_scale=1.0)
if export_result != {{'FINISHED'}}:
    raise RuntimeError('Repaired STL export failed: ' + str(export_result))

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.unit_settings.scale_length = 0.001
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 900
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = preview
scene.render.film_transparent = False
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
material = bpy.data.materials.new(object_name + '_preview_material')
material.diffuse_color = (0.12,0.32,0.55,1.0)
obj.data.materials.clear()
obj.data.materials.append(material)
points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
center = mathutils.Vector(((min(point.x for point in points)+max(point.x for point in points))/2.0,(min(point.y for point in points)+max(point.y for point in points))/2.0,(min(point.z for point in points)+max(point.z for point in points))/2.0))
span = max(final_dimensions)
camera_data = bpy.data.cameras.new(object_name + '_camera_data')
camera = bpy.data.objects.new(object_name + '_camera', camera_data)
scene.collection.objects.link(camera)
camera.location = center + mathutils.Vector((1.45*span,-1.65*span,1.25*span))
camera.rotation_euler = (center-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = span*1.55
scene.camera = camera
render_result = bpy.ops.render.render(write_still=True)
if render_result != {{'FINISHED'}}:
    raise RuntimeError('Preview render failed: ' + str(render_result))

report = {{'operation':'fixed_native_blender_mesh_repair','source_preserved':source,'artifacts':[repaired,preview],'before':{{'dimensions_mm':before_dimensions,'mesh':before_metrics}},'after':{{'dimensions_mm':final_dimensions,'mesh':final_metrics}},'repair':{{'merge_tolerance_mm':merge_tolerance,'degenerate_tolerance_mm':degenerate_tolerance,'voxel_remesh_used':voxel_remesh_used,'voxel_size_mm':voxel_size_mm,'voxel_iterations':voxel_iterations,'discarded_components':discarded_components,'decimation_used':decimation_used,'triangle_limit':triangle_limit}},'orientation':{{'action':'preserved_model_axes_and_translated_minimum_z_to_build_plate','supports':'assigned by the pinned slicer operation'}},'checks':{{'closed_manifold':True,'outward_normals':final_metrics['signed_volume_mm3']>0,'single_component':True,'within_triangle_limit':True,'fits_p1s_256mm_cube':True}},'content_validated':False}}
print(json.dumps(report,separators=(',',':')))
'''


def run(configuration_path: Path, *, blender_connection, validate_code) -> dict:
    configuration = json.loads(configuration_path.read_text(encoding="utf-8"))
    code = blender_code(configuration)
    validate_code(code)
    result = blender_connection.send_command("execute_code", {"code": code})
    raw = str(result.get("result", "")).strip()
    if not raw:
        raise RuntimeError("Blender repair returned no operation report")
    report = json.loads(raw.splitlines()[-1])
    output_files = [Path(configuration["repaired"]), Path(configuration["preview"])]
    for path in output_files:
        if not path.is_file() or path.stat().st_size <= 0:
            raise RuntimeError(f"Blender repair did not create a nonempty output: {path}")
    report["produced_files"] = [
        {"path": str(path), "size_bytes": path.stat().st_size, "sha256": _sha256(path)}
        for path in output_files
    ]
    return report
