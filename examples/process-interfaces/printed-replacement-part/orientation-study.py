"""Authored study operation for an independent engineering Python MCP.

Wright supplies exact files and runs the declared tool. This operation performs
rigid mesh transformations and passive numerical inspection, never slicing or
machine dispatch. The existing slicer and passive package reader are separate
declared producers. Digital observations do not establish physical acceptance.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import struct
import zipfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_triangles(raw):
    if len(raw) < 84:
        raise ValueError("A complete binary STL is required")
    count = struct.unpack_from('<I', raw, 80)[0]
    if not 1 <= count <= 80000 or len(raw) != 84 + count * 50:
        raise ValueError("STL facet count or size is outside the declared bound")
    triangles = []
    for record in struct.iter_unpack('<12fH', raw[84:]):
        vertices = tuple(tuple(record[start:start + 3]) for start in (3, 6, 9))
        if not all(math.isfinite(v) for point in vertices for v in point):
            raise ValueError("Non-finite mesh geometry")
        triangles.append(vertices)
    return triangles


def normal_area(triangle):
    a, b, c = triangle
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    length = math.sqrt(sum(x*x for x in cross))
    if length == 0:
        raise ValueError("Degenerate source facet")
    return tuple(x/length for x in cross), length/2


def mesh_facts(triangles):
    low = [min(p[i] for triangle in triangles for p in triangle) for i in range(3)]
    high = [max(p[i] for triangle in triangles for p in triangle) for i in range(3)]
    volume = area = contact = down = 0.0
    for triangle in triangles:
        a,b,c = triangle
        n, facet_area = normal_area(triangle)
        area += facet_area
        volume += (a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
        if n[2] < -0.999 and max(abs(p[2]) for p in triangle) <= 0.0001:
            contact += facet_area
        if n[2] < -math.sqrt(0.5) and min(p[2] for p in triangle) > 0.2:
            down += facet_area * -n[2]
    return {'facets':len(triangles),'bounds_mm':[low,high],
            'height_mm':high[2]-low[2],'signed_volume_mm3':volume,'surface_area_mm2':area,
            'coplanar_bed_contact_mm2':contact,
            'downward_projected_area_above_first_layer_mm2':down}


def transform(raw, socket_up):
    source = read_triangles(raw)
    low = min(p[2] for tri in source for p in tri)
    high = max(p[2] for tri in source for p in tri)
    sign = -1 if socket_up else 1
    shift = high if socket_up else -low
    result = [tuple((x,sign*y,sign*z+shift) for x,y,z in tri) for tri in source]
    encoded = bytearray(b'Wright rigid orientation study; mm'.ljust(80,b'\0'))
    encoded.extend(struct.pack('<I',len(result)))
    for triangle in result:
        n,_ = normal_area(triangle)
        encoded.extend(struct.pack('<12fH',*n,*(v for p in triangle for v in p),0))
    # Inspect exported float32 values, rather than merely the in-memory proposal.
    facts = mesh_facts(read_triangles(encoded))
    original = mesh_facts(source)
    facts.update(transform=[[1,0,0,0],[0,sign,0,0],[0,0,sign,shift],[0,0,0,1]],
                 rotation_determinant=1,source_sha256=sha(raw),mesh_sha256=sha(encoded),
                 volume_relative_error=abs(facts['signed_volume_mm3']-original['signed_volume_mm3'])/abs(original['signed_volume_mm3']),
                 area_relative_error=abs(facts['surface_area_mm2']-original['surface_area_mm2'])/original['surface_area_mm2'])
    return bytes(encoded), facts


def scoped(config, relative, *, existing=True):
    root = Path(config['workspace_root']).resolve(strict=True)
    path = (root/relative).resolve(strict=existing)
    if not path.is_relative_to(root):
        raise ValueError("Study paths must remain in the declared workspace")
    return path


def publish(path, value):
    raw = (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    with path.open('xb') as stream:
        stream.write(raw)
    return sha(raw)


def prepare(config):
    raw = scoped(config,config['source_mesh']).read_bytes()
    if sha(raw) != config['source_sha256']:
        raise ValueError('Upstream geometry changed')
    output = scoped(config,config['output_root'],existing=False)
    output.mkdir(parents=True,exist_ok=True)
    # The validation contract binds task outputs. Retain the exact incoming
    # bytes as an explicit output alongside the two transformed candidates.
    with (output/'source_mesh.stl').open('xb') as stream:
        stream.write(raw)
    records = {}
    for name in ('socket_down','socket_up'):
        folder = output/name
        folder.mkdir()  # No uncertain replay or overwriting earlier cases.
        mesh,facts = transform(raw,name=='socket_up')
        with (folder/'oriented.stl').open('xb') as stream:
            stream.write(mesh)
        records[name] = facts
    result={'source_sha256':sha(raw),'units':'mm','cases':records,
            'method':'Rigid proper rotations of every facet; original mm frame from pinned native CAD export. Contact area uses coplanar facets, not adhesion simulation. Downward area uses a declared 45 degree geometric screen, not predicted support.',
            'engineering_acceptance':False,'physical_acceptance':False}
    publish(output/'orientation-geometry.json',result)
    return result


def path_facts(view, socket_up):
    model=[(x,y) for layer in view['layers'] for seg in layer['model'] for x,y in ((seg[0],seg[1]),(seg[2],seg[3]))]
    if not model:
        raise ValueError('No actual model paths')
    center=[(min(p[i] for p in model)+max(p[i] for p in model))/2 for i in range(2)]
    totals={kind:0.0 for kind in ('model','support','unclassified')}
    internal=0.0
    support_layers=[]
    for layer in view['layers']:
        if layer['support']:
            support_layers.append(layer['z'])
        for kind in totals:
            for x1,y1,x2,y2 in layer[kind]:
                length=math.hypot(x2-x1,y2-y1)
                totals[kind]+=length
                x,y=(x1+x2)/2-center[0],(y1+y2)/2-center[1]
                inside=(x*x+y*y < 3.2**2 and x > -2.4)
                cavity_z=(8 < layer['z'] < 18) if socket_up else (0 < layer['z'] < 10)
                if kind=='support' and inside and cavity_z:
                    internal+=length
    return {'layer_count':len(view['layers']), 'path_length_mm':totals,
            'support_midpoint_length_in_nominal_socket_mm':internal,
            'model_path_center_xy_mm':center,
            'support_layer_z_range_mm':[min(support_layers),max(support_layers)] if support_layers else None,
            'classification_known':view.get('classification_source')=='gcode_feature_comments',
            'unclassified_features':view['provenance'].get('unclassified_features',[]),
            'method':'Sum recorded segment lengths. Socket screening tests support-segment midpoints in the nominal D cavity after locating the symmetric model path envelope. No bead-width/contact/adhesion or support-removability simulation; boundary-crossing segments and unclassified paths remain limits.'}


def compare(config):
    output=scoped(config,config['output_root'])
    geometry=json.loads((output/'orientation-geometry.json').read_bytes())
    source_digest = sha(scoped(config, config['source_mesh']).read_bytes())
    if (source_digest != config['source_sha256']
            or geometry['source_sha256'] != source_digest
            or sha((output/'source_mesh.stl').read_bytes()) != source_digest
            or any(case['source_sha256'] != source_digest for case in geometry['cases'].values())):
        raise ValueError('Orientation evidence does not match the exact upstream geometry')
    records={}
    for name in ('socket_down','socket_up'):
        folder=output/name
        view=json.loads((folder/'support-preview.json').read_bytes())
        evidence=json.loads((folder/'slice-evidence.json').read_bytes())
        if evidence['source_sha256'] != geometry['cases'][name]['mesh_sha256']:
            raise ValueError('Slice does not bind to the oriented mesh')
        if sha((folder/'package.gcode.3mf').read_bytes()) != evidence['package_sha256']:
            raise ValueError('Slice package changed')
        profiles={key:sha((folder/(key+'-profile.json')).read_bytes()) for key in ('machine','process','filament')}
        if profiles != config['profile_sha256']:
            raise ValueError('Machine, material or process profile changed')
        with zipfile.ZipFile(folder/'package.gcode.3mf') as archive:
            header=archive.read(config['gcode_entry']).decode('utf-8').splitlines()[:30]
        usage={}
        for label,prefix in config['reported_usage_prefixes'].items():
            matches=[line[len(prefix):].strip() for line in header if line.startswith(prefix)]
            if len(matches)!=1:
                raise ValueError('Missing or ambiguous declared package summary: '+label)
            usage[label]=matches[0]
        records[name]={**geometry['cases'][name], **path_facts(view,name=='socket_up'),
                       'package_sha256':evidence['package_sha256'],'profiles':profiles,
                       'slicer_reported_usage':usage,
                       'view_sha256':sha((folder/'support-preview.json').read_bytes())}
    report={'cases':records,'same_profiles':True,'source_sha256':geometry['source_sha256'],
            'source_matches_dependency':True,
            'engineering_acceptance':False,'physical_acceptance':False,
            'decision_status':'Awaiting engineer orientation/support review',
            'decision_basis':'Preserve the critical D socket first; compare support within the nominal cavity, then external contact/removal and material use. Counts do not prove safe removal or printed fit.'}
    publish(output/'orientation-comparison.json',report)
    down,up=records['socket_down'],records['socket_up']
    rows=[('Layers',down['layer_count'],up['layer_count']),
          ('Nominal model paths · mm',down['path_length_mm']['model'],up['path_length_mm']['model']),
          ('Nominal support paths · mm',down['path_length_mm']['support'],up['path_length_mm']['support']),
          ('Support midpoint paths inside nominal D socket · mm',down['support_midpoint_length_in_nominal_socket_mm'],up['support_midpoint_length_in_nominal_socket_mm']),
          ('Unclassified extrusion paths · mm',down['path_length_mm']['unclassified'],up['path_length_mm']['unclassified']),
          ('Coplanar geometric bed contact · mm²',down['coplanar_bed_contact_mm2'],up['coplanar_bed_contact_mm2']),
          ('Projected downward facets above first layer · mm²',down['downward_projected_area_above_first_layer_mm2'],up['downward_projected_area_above_first_layer_mm2'])]
    lines=['# Focus wheel — build orientation and support review','',
           '## Decision to make','',report['decision_basis'],'',
           'Both candidates use the same retained native wheel geometry, P1S 0.4 mm machine, PETG, 0.20 mm layers, four walls, 35% infill and enabled supports. No physical print is started.','',
           '## Observed comparison','', '| Observation | Socket down | Socket up |','| --- | ---: | ---: |']
    lines += [f'| {label} | {a:.3f} | {b:.3f} |' for label,a,b in rows]
    for label in config['reported_usage_prefixes']:
        lines += [f'| Slicer-reported {label} | {down["slicer_reported_usage"][label]} | {up["slicer_reported_usage"][label]} |']
    lines += ['', '## Geometry, contact and removal','',
              '- Socket down: the main rear face rests on the bed. The blind cavity opens toward the bed; any interior support must be removed through the nominal 6.4 mm round / 5.6 mm across-flat opening. Inspect socket roof bridging, support contact and surface finish.',
              '- Socket up: a 180° X rotation places the raised front hub against the bed. The blind cavity opens upward. The body, front grip dots and rounded surfaces can require external support around the hub; inspect those contacts and removal access.',
              '- The socket screening uses segment midpoints in the nominal cavity, located from the symmetric model-path envelope. It omits bead width, boundary-crossing detail and unclassified extrusion. It does not establish contact-free geometry.',
              '- Compare actual path viewers and native drawing before selecting. Printed clearance, support removal, layer adhesion, creep, torque capacity and gloved comfort require physical trials. No strength or fit result is inferred.',
              '', '## Inspection plan','',
              'After an engineer selects the orientation, retain its exact package and profile identities. Print only under separate authority. Inspect the D profile and 10 mm depth using the identified shaft/gauge; measure insertion/removal force and play; inspect the roof and support-contact damage. Apply the retained torque/environment and drawing inspection plan. Sampling, tolerances and acceptance remain with the responsible engineer.',
              '', '## Exact evidence','',f'- Source mesh SHA-256: `{geometry["source_sha256"]}`']
    for name,record in records.items():
        lines += [f'- {name} STL: `{record["mesh_sha256"]}`; package: `{record["package_sha256"]}`; path view: `{record["view_sha256"]}`.']
    with (output/'orientation-review.md').open('x',encoding='utf-8') as stream:
        stream.write('\n'.join(lines)+'\n')
    return report
