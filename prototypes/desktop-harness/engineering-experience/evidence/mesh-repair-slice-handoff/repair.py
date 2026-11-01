import bpy, bmesh, json
from mathutils import Vector
before=set(bpy.data.objects)
bpy.ops.wm.stl_import(filepath='/qualification/source-defect.stl')
owned=[obj for obj in bpy.data.objects if obj not in before and obj.type=='MESH']
assert len(owned)==1
obj=owned[0]
obj.name='wright_disposable_repair_036'
mesh=obj.data
before_faces=len(mesh.polygons)
mesh.validate(verbose=True)
bm=bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.00001)
bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=0.00001)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
nonmanifold=sum(not edge.is_manifold for edge in bm.edges)
assert nonmanifold==0, str(nonmanifold)
volume=abs(bm.calc_volume(signed=True))
bm.to_mesh(mesh)
bm.free()
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active=obj
bpy.ops.wm.stl_export(filepath='/qualification/repaired.stl',export_selected_objects=True)
print(json.dumps({'source_faces_after_import':before_faces,'repaired_faces':len(mesh.polygons),'dimensions':list(obj.dimensions),'volume':volume,'nonmanifold_edges':nonmanifold}))
