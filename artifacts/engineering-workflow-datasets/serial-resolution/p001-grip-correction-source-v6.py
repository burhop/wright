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
mod = left.modifiers.new(name='Pad_and_Bore_Rounding_1p01mm', type='BEVEL')
mod.width = 1.01
mod.use_clamp_overlap = False
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
mod = right.modifiers.new(name='Pad_and_Bore_Rounding_1p01mm', type='BEVEL')
mod.width = 1.01
mod.use_clamp_overlap = False
mod.segments = 4
mod.limit_method = 'ANGLE'
mod.angle_limit = math.radians(20.0)
bpy.context.view_layer.objects.active = right
bpy.ops.object.modifier_apply(modifier=mod.name)

# Explicit root fillets join the pad top tangentially; no post-union bevel.
# Root centers (3.9,6.2) and (92.1,6.2) preserve space for both bore lips.
# The 4.05 mm outer root radius fits inside the flat pad top: max X=7.95,
# max Y=10.25; nearest distance to the 3.25 mm rounded bore mouth is 3.2769.
# This confines root fillets to radius 1.05 mm. Larger shoulder blends use
# the available space above the pads; the central grip retains 12 x 9 mm.
left_rings = []
left_rings.append((3.9, 4.8, 4.05, 4.05, -1.0, 0.0))
for i in range(13):
    phi = math.pi * i / 24.0
    z = 5.0 + 1.05 * (1.0 - math.cos(phi))
    radius = 3.0 + 1.05 * (1.0 - math.sin(phi))
    left_rings.append((3.9, z, radius, radius, -1.0, 0.0))

# Tangent cubic centerline from the vertical root to the horizontal grip.
# Its measured analytic curvature radius is >=8.18 mm in X/Z. With the
# 4.5 mm half-thickness, the tightest inner shoulder is >=3.68 mm.
p0 = (3.9, 6.05)
p1 = (3.9, 16.0)
p2 = (3.9, 29.5)
p3 = (15.0, 29.5)
for i in range(1,49):
    t = i / 48.0
    u = 1.0 - t
    x = u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0]
    z = u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]
    dx = 3*u*u*(p1[0]-p0[0]) + 6*u*t*(p2[0]-p1[0]) + 3*t*t*(p3[0]-p2[0])
    dz = 3*u*u*(p1[1]-p0[1]) + 6*u*t*(p2[1]-p1[1]) + 3*t*t*(p3[1]-p2[1])
    length = math.sqrt(dx*dx+dz*dz)
    q = min(1.0,t/0.55)
    growth = q*q*(3.0-2.0*q)
    ry = 3.0 + 3.0*growth
    rn = 3.0 + 1.5*growth
    left_rings.append((x,z,ry,rn,-dz/length,dx/length))

stations = list(left_rings)
for x in sorted(set([float(x) for x in range(16,82,2)] + [15.5,28.0,48.0,68.0,80.5,81.0])):
    stations.append((x,29.5,6.0,4.5,0.0,1.0))
for x,z,ry,rn,nx,nz in reversed(left_rings[:-1]):
    stations.append((96.0-x,z,ry,rn,-nx,nz))

verts = []
faces = []
ring_count = len(stations)
segments = 48
for x,zc,ry,rn,nx,nz in stations:
    recess = 1.5*math.sin(math.pi*(x-28.0)/40.0)**2 if 28.0<x<68.0 else 0.0
    for j in range(segments):
        a = 2.0*math.pi*j/segments
        c = math.cos(a)
        offset = rn*math.sin(a)
        y = 6.2 + ry*c - recess*max(0.0,c)**4
        verts.append((x+nx*offset,y,zc+nz*offset))
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

stl_path = 'C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/qualification-p001-016/artifacts/source_mesh.stl'
blend_path = 'C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/printed-replacement-part-02/qualification-p001-016/artifacts/native-design.blend'
bpy.ops.wm.stl_export(filepath=stl_path, export_selected_objects=True)
bpy.ops.wm.save_as_mainfile(filepath=blend_path, copy=True)

print({'object': bow.name, 'stl': stl_path, 'blend': blend_path, 'design': {'bolt_centers_mm': 96.0, 'pads_mm': [18.0, 24.0, 5.0], 'bores_diameter_mm': 4.5, 'grip_section_mm': [12.0, 9.0], 'clearance_span_x_mm': [15.5, 80.5], 'clearance_min_z_mm': 25.0, 'outer_max_z_mm': 34.0, 'thumb_recess_max_mm': 1.5}})