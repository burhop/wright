import bpy
import math
import mathutils
import bmesh

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.unit_settings.scale_length = 0.001

base_name = 'Wright_Handle_GripCorrection2'
idx = 1
while bpy.data.objects.get(base_name + '_' + str(idx).zfill(3)) is not None:
    idx += 1
name = base_name + '_' + str(idx).zfill(3)
owned = []

# Left mounting pad: 18 x 24 x 5 mm, centered on the first bore at X=0.
bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 2.5))
left = bpy.context.object
left.name = name + '_LeftPad'
left.dimensions = (18.0, 24.0, 5.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
owned.append(left)

bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=2.25, depth=9.0, location=(0.0, 0.0, 2.5))
left_hole = bpy.context.object
left_hole.name = name + '_LeftBoreTool'
mod = left.modifiers.new(name='Exact_4p5mm_Bore', type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.solver = 'EXACT'
mod.object = left_hole
bpy.context.view_layer.objects.active = left
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(left_hole, do_unlink=True)
mod = left.modifiers.new(name='Pad_and_Bore_Rounding_1mm', type='BEVEL')
mod.width = 1.0
mod.segments = 4
mod.limit_method = 'ANGLE'
mod.angle_limit = math.radians(20.0)
bpy.context.view_layer.objects.active = left
bpy.ops.object.modifier_apply(modifier=mod.name)

# Right mounting pad: bore center exactly 96 mm from the first.
bpy.ops.mesh.primitive_cube_add(location=(96.0, 0.0, 2.5))
right = bpy.context.object
right.name = name + '_RightPad'
right.dimensions = (18.0, 24.0, 5.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
owned.append(right)

bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=2.25, depth=9.0, location=(96.0, 0.0, 2.5))
right_hole = bpy.context.object
right_hole.name = name + '_RightBoreTool'
mod = right.modifiers.new(name='Exact_4p5mm_Bore', type='BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.solver = 'EXACT'
mod.object = right_hole
bpy.context.view_layer.objects.active = right
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(right_hole, do_unlink=True)
mod = right.modifiers.new(name='Pad_and_Bore_Rounding_1mm', type='BEVEL')
mod.width = 1.0
mod.segments = 4
mod.limit_method = 'ANGLE'
mod.angle_limit = math.radians(20.0)
bpy.context.view_layer.objects.active = right
bpy.ops.object.modifier_apply(modifier=mod.name)

# Corrected same-case bow: tangent circular shoulders, radius 5 mm in
# the X/Z longitudinal profiles. Shoulder tangency is outside the clearance
# interval, at X=15 and X=81. The central underside is exactly Z=25.
shoulder_radius = 5.0
left_start_x = 3.5
left_start_z = 2.5
plateau_x = 15.0
plateau_z = 29.5
dx = plateau_x - left_start_x
dz = plateau_z - left_start_z
low = 0.0
high = math.pi / 2.0
for iteration in range(64):
    trial = (low + high) / 2.0
    residual = (dz - shoulder_radius) * math.cos(trial) - dx * math.sin(trial) + shoulder_radius
    if residual > 0:
        low = trial
    else:
        high = trial
theta = (low + high) / 2.0
arc_start_x = plateau_x - shoulder_radius * math.sin(theta)
arc_start_z = plateau_z - shoulder_radius * (1.0 - math.cos(theta))
left_stations = []
for i in range(13):
    t = i / 12.0
    x = left_start_x + t * (arc_start_x - left_start_x)
    zc = left_start_z + t * (arc_start_z - left_start_z)
    q = min(1.0, max(0.0, (x - left_start_x) / 2.0))
    rz = 2.0 + 2.5 * q * q * (3.0 - 2.0 * q)
    left_stations.append((x, zc, rz))
for i in range(1, 25):
    angle = theta * (1.0 - i / 24.0)
    x = plateau_x - shoulder_radius * math.sin(angle)
    zc = plateau_z - shoulder_radius * (1.0 - math.cos(angle))
    left_stations.append((x, zc, 4.5))
stations = list(left_stations)
central_x = sorted(set([float(x) for x in range(16, 82, 2)] + [15.5, 28.0, 48.0, 68.0, 80.5, 81.0]))
for x in central_x:
    stations.append((x, plateau_z, 4.5))
for x, zc, rz in reversed(left_stations[:-1]):
    stations.append((96.0 - x, zc, rz))

verts = []
faces = []
ring_count = len(stations)
segments = 48
for x, zc, rz in stations:
    yc = 5.0 * math.sin(math.pi * (x - 3.5) / 89.0)
    recess = 0.0
    if 28.0 < x < 68.0:
        recess = 1.5 * math.sin(math.pi * (x - 28.0) / 40.0) ** 2
    for j in range(segments):
        a = 2.0 * math.pi * j / segments
        c = math.cos(a)
        y = yc + 6.0 * c - recess * max(0.0, c) ** 4
        z = zc + rz * math.sin(a)
        verts.append((x, y, z))
for i in range(ring_count - 1):
    for j in range(segments):
        nj = (j + 1) % segments
        a = i * segments + j
        b = i * segments + nj
        c = (i + 1) * segments + nj
        d = (i + 1) * segments + j
        faces.append((a, b, c, d))
faces.append(tuple(reversed(tuple(range(segments)))))
last = (ring_count - 1) * segments
faces.append(tuple(last + j for j in range(segments)))
mesh = bpy.data.meshes.new(name + '_BowMesh')
mesh.from_pydata(verts, [], faces)
mesh.update()
bow = bpy.data.objects.new(name + '_Bow', mesh)
scene.collection.objects.link(bow)
owned.append(bow)

# The thumb recess is part of the sweep over the full X=28..68 interval,
# with zero slope at both ends and 1.5 mm maximum centerline depth at X=48.
# Join the bow to both rounded pads as one owned solid.
mod = bow.modifiers.new(name='Union_LeftPad', type='BOOLEAN')
mod.operation = 'UNION'
mod.solver = 'EXACT'
mod.object = left
bpy.context.view_layer.objects.active = bow
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(left, do_unlink=True)
mod = bow.modifiers.new(name='Union_RightPad', type='BOOLEAN')
mod.operation = 'UNION'
mod.solver = 'EXACT'
mod.object = right
bpy.context.view_layer.objects.active = bow
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(right, do_unlink=True)

# Round only the new bow/pad intersection edges. Existing 1 mm pad and
# bore rounds are left intact; a global bevel would reprocess pad corners.
bm = bmesh.new()
bm.from_mesh(bow.data)
bm.normal_update()
root_edges = []
root_angles = []
for edge in bm.edges:
    if len(edge.link_faces) != 2:
        continue
    angle = edge.calc_face_angle()
    at_root = True
    for vertex in edge.verts:
        x, y, z = vertex.co
        if not (3.9 <= z <= 5.01 and abs(y) < 8.0 and (3.0 < x < 10.0 or 86.0 < x < 93.0)):
            at_root = False
    if at_root and angle > math.radians(25.0):
        root_edges.append(edge)
        root_angles.append(math.degrees(angle))
if not root_edges:
    raise RuntimeError('No newly created root intersection edges selected')
# A 1.5 mm offset gives radius >=1 mm for face turns up to 112.6 degrees.
if max(root_angles) > 112.6:
    raise RuntimeError('Root turn requires a larger round: ' + str(root_angles))
bmesh.ops.bevel(bm, geom=root_edges, offset=1.5, offset_type='OFFSET',
    segments=8, profile=0.5, affect='EDGES', clamp_overlap=False)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(bow.data)
bm.free()
bow.data.update()
print({'rounded_root_edges':len(root_edges), 'root_turn_degrees':root_angles,
       'root_round_offset_mm':1.5, 'root_round_segments':8})

bow.name = name + '_FinalSource'
for poly in bow.data.polygons:
    poly.use_smooth = True
tri = bow.modifiers.new(name='Export_Triangulation', type='TRIANGULATE')
tri.quad_method = 'BEAUTY'
tri.ngon_method = 'BEAUTY'
bpy.context.view_layer.objects.active = bow
bpy.ops.object.modifier_apply(modifier=tri.name)

# Select only the newly constructed source mesh for export; unrelated scene objects are retained.
bpy.ops.object.select_all(action='DESELECT')
bow.select_set(True)
bpy.context.view_layer.objects.active = bow

stl_path = 'C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/qualification-p001-012/artifacts/source_mesh.stl'
blend_path = 'C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/qualification-p001-012/artifacts/native-design.blend'
bpy.ops.wm.stl_export(filepath=stl_path, export_selected_objects=True)
bpy.ops.wm.save_as_mainfile(filepath=blend_path, copy=True)

print({'object': bow.name, 'stl': stl_path, 'blend': blend_path, 'design': {'bolt_centers_mm': 96.0, 'pads_mm': [18.0, 24.0, 5.0], 'bores_diameter_mm': 4.5, 'grip_section_mm': [12.0, 9.0], 'clearance_span_x_mm': [15.5, 80.5], 'clearance_min_z_mm': 25.0, 'outer_max_z_mm': 34.0, 'thumb_recess_max_mm': 1.5}})