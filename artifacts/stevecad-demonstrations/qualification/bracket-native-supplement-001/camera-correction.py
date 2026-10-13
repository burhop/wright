import bpy
import json
from mathutils import Vector
scene=bpy.context.scene
assert scene.get('wright_render_run')=='90087fceacdc494d91eaff6f65d9173d'
assert scene.get('wright_cad_scene_owner')=='d65a6b4a-06c4-4240-8f43-18228b08fa26'
assert not bpy.app.is_job_running('RENDER')
camera=scene.camera
target=Vector(scene['wright_cad_target'])
camera.location=target+Vector((0,0,5))
camera.rotation_euler=(0,0,0)
bpy.context.view_layer.update()
right=camera.matrix_world.to_3x3()@Vector((1,0,0))
up=camera.matrix_world.to_3x3()@Vector((0,1,0))
assert (right-Vector((1,0,0))).length<1e-6
assert (up-Vector((0,1,0))).length<1e-6
corners=[obj.matrix_world@Vector(c) for obj in scene.objects if obj.type=='MESH' and obj.get('wright_cad_body') for c in obj.bound_box]
projected=[camera.matrix_world.inverted()@v for v in corners]
width=max(v.x for v in projected)-min(v.x for v in projected)
height=max(v.y for v in projected)-min(v.y for v in projected)
camera.data.ortho_scale=max(width/.8,height*(scene.render.resolution_x/scene.render.resolution_y)/.8)
scene.render.filepath='/outputs/90087fceacdc494d91eaff6f65d9173d/render_top-corrected.png'
result=bpy.ops.render.render(write_still=True)
assert 'FINISHED' in result
print(json.dumps({'result':list(result),'native_render_running':bpy.app.is_job_running('RENDER'),'document_id':scene['wright_cad_document'],'revision':scene['wright_cad_revision'],'build_id':scene['wright_cad_scene_owner'],'source_run_id':'90087fceacdc494d91eaff6f65d9173d','view':'top','screen_right_world':list(right),'screen_up_world':list(up),'output_file':scene.render.filepath,'scope':'Supplemental native camera correction only; original workflow outputs unchanged'}))
