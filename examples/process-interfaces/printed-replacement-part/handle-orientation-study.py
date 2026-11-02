"""Authored Printed02 study for the selected independent Python inspection MCP.

Rigid auxiliary build candidates from the reviewed repaired mesh; no slicing,
selection, approval, model authoring or physical action. Original model axes and
full validation remain attached to the unmodified repaired source. Neutral mesh
inspection functions retain the existing wheel operation's bounded STL rules.
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


CANDIDATES = ('pads_down', 'side')


def transform(raw, name):
    if name not in CANDIDATES:
        raise ValueError('Unknown handle orientation')
    source = read_triangles(raw)
    original = mesh_facts(source)
    if abs(original['signed_volume_mm3']) <= 1e-12:
        raise ValueError('The source must have nonzero enclosed volume')
    side = name == 'side'
    rotated = [tuple((x, -z, y) if side else (x, y, z)
                     for x, y, z in tri) for tri in source]
    shift = -min(p[2] for tri in rotated for p in tri)
    result = [tuple((x, y, z + shift) for x, y, z in tri) for tri in rotated]
    encoded = bytearray(b'Wright Printed02 auxiliary build orientation; mm'.ljust(80, b'\0'))
    encoded.extend(struct.pack('<I', len(result)))
    for triangle in result:
        normal, _ = normal_area(triangle)
        encoded.extend(struct.pack('<12fH', *normal, *(v for p in triangle for v in p), 0))
    facts = mesh_facts(read_triangles(encoded))
    original_spans = [b-a for a,b in zip(*original['bounds_mm'])]
    expected_spans = ([original_spans[0], original_spans[2], original_spans[1]]
                      if side else original_spans)
    actual_spans = [b-a for a,b in zip(*facts['bounds_mm'])]
    matrix = ([[1,0,0,0],[0,0,-1,0],[0,1,0,shift],[0,0,0,1]] if side
              else [[1,0,0,0],[0,1,0,0],[0,0,1,shift],[0,0,0,1]])
    facts.update(
        original_frame='X drawer width; Y vertical; Z outward; mounting plane Z=0',
        build_transform=matrix, rotation_determinant=1,
        source_sha256=sha(raw), mesh_sha256=sha(encoded),
        frame_span_error_mm=max(abs(a-b) for a,b in zip(actual_spans, expected_spans)),
        volume_relative_error=abs(facts['signed_volume_mm3']-original['signed_volume_mm3'])/abs(original['signed_volume_mm3']),
        area_relative_error=abs(facts['surface_area_mm2']-original['surface_area_mm2'])/original['surface_area_mm2'],
    )
    return bytes(encoded), facts


def prepare(config):
    raw = scoped(config, config['source_mesh']).read_bytes()
    if sha(raw) != config['source_sha256']:
        raise ValueError('Upstream repaired geometry changed')
    output = scoped(config, config['output_root'], existing=False)
    output.mkdir(parents=True, exist_ok=True)
    with (output/'source_mesh.stl').open('xb') as stream:
        stream.write(raw)
    cases = {}
    for name in CANDIDATES:
        folder = output/name
        folder.mkdir()
        encoded, facts = transform(raw, name)
        with (folder/'oriented.stl').open('xb') as stream:
            stream.write(encoded)
        cases[name] = facts
    result = dict(scenario_id='printed-replacement-part-02', source_sha256=sha(raw),
                  units='mm', cases=cases, engineering_acceptance=False,
                  physical_acceptance=False)
    publish(output/'orientation-geometry.json', result)
    return result


def path_facts(view):
    if not view['layers'] or not any(layer['model'] for layer in view['layers']):
        raise ValueError('No actual model paths')
    totals = {kind: 0.0 for kind in ('model', 'support', 'unclassified')}
    support_points = []
    for layer in view['layers']:
        for kind in totals:
            for x1,y1,x2,y2 in layer[kind]:
                values = (x1,y1,x2,y2,layer['z'])
                if not all(math.isfinite(v) for v in values):
                    raise ValueError('Non-finite toolpath coordinate')
                totals[kind] += math.hypot(x2-x1, y2-y1)
                if kind == 'support':
                    support_points.extend(((x1,y1,layer['z']), (x2,y2,layer['z'])))
    bounds = None
    if support_points:
        bounds = [[fn(p[i] for p in support_points) for i in range(3)] for fn in (min,max)]
    return dict(
        layer_count=len(view['layers']), path_length_mm=totals,
        support_path_bounds_build_mm=bounds,
        classification_known=view.get('classification_source') == 'gcode_feature_comments',
        unclassified_features=view['provenance'].get('unclassified_features', []),
        support_contact_review='Required: inspect actual support paths at pads, holes, finger opening, touched grip and thumb recess. Path bounds do not establish physical contact or removability.',
    )


def compare(config):
    output = scoped(config, config['output_root'])
    geometry = json.loads((output/'orientation-geometry.json').read_bytes())
    raw = scoped(config, config['source_mesh']).read_bytes()
    digest = sha(raw)
    if (digest != config['source_sha256'] or geometry['source_sha256'] != digest
            or sha((output/'source_mesh.stl').read_bytes()) != digest):
        raise ValueError('Comparison does not bind to the exact repaired mesh')
    records = {}
    for name in CANDIDATES:
        folder = output/name
        # Recompute the deterministic transform and numerical metrics; never trust
        # a self-reported matrix or bounds when consuming actual mesh artifacts.
        expected, facts = transform(raw, name)
        if ((folder/'oriented.stl').read_bytes() != expected
                or geometry['cases'][name] != facts):
            raise ValueError('Orientation transform or evidence changed')
        view_raw = (folder/'support-preview.json').read_bytes()
        view = json.loads(view_raw)
        evidence = json.loads((folder/'slice-evidence.json').read_bytes())
        package_digest = sha((folder/'package.gcode.3mf').read_bytes())
        if (evidence['source_sha256'] != facts['mesh_sha256']
                or evidence['package_sha256'] != package_digest
                or view['package_sha256'] != package_digest):
            raise ValueError('Package, preview and candidate lineage do not agree')
        profiles = {role: sha((folder/(role+'-profile.json')).read_bytes())
                    for role in ('machine', 'process', 'filament')}
        if profiles != config['profile_sha256']:
            raise ValueError('The exact machine/material/process profiles changed')
        with zipfile.ZipFile(folder/'package.gcode.3mf') as archive:
            header = archive.read(config['gcode_entry']).decode('utf-8').splitlines()[:30]
        usage = {}
        for label, prefix in config['reported_usage_prefixes'].items():
            matches = [line[len(prefix):].strip() for line in header if line.startswith(prefix)]
            if len(matches) != 1:
                raise ValueError('Missing or ambiguous package summary: '+label)
            usage[label] = matches[0]
        records[name] = {**facts, **path_facts(view), 'profiles': profiles,
                         'package_sha256': package_digest, 'view_sha256': sha(view_raw),
                         'slicer_reported_usage': usage}
    report = dict(
        scenario_id='printed-replacement-part-02', source_sha256=digest,
        source_matches_dependency=True, same_profiles=True, cases=records,
        final_package_orientation='pads_down_original_repaired_mesh',
        decision_status='Awaiting exact engineering review; no automatic selection',
        engineering_acceptance=False, physical_acceptance=False,
    )
    publish(output/'orientation-comparison.json', report)
    lines = ['# Drawer handle: actual orientation and support evidence', '',
             'Both cases derive from the exact repaired mesh with unchanged P1S/PETG profiles, five walls and 40% infill. The original model-axis profile remains mandatory. Auxiliary side geometry does not replace the final original-frame pads-down package.', '',
             '| Observation | Pads down | Side |', '| --- | ---: | ---: |']
    for label, key in (('Layers', 'layer_count'), ('Height (mm)', 'height_mm'),
                       ('Coplanar bed contact (mm²)', 'coplanar_bed_contact_mm2')):
        lines.append(f'| {label} | {records["pads_down"][key]} | {records["side"][key]} |')
    lines += ['', 'Inspect support-contact locations at mounting faces and through holes, the finger opening, touched oval grip and thumb recess using each exact support path view. Segment lengths, bounding boxes and downward area are geometric screens; they do not prove contact, adhesion, safe removal or a successful print. Unknown classifications remain visible.', '',
              'Review the retained original mounting, label keepout, envelope, clearance, grip and action-scope requirements. Physical fit, 40 N drawer opening, fatigue, gloved comfort and print performance remain unvalidated. No printer connection, transfer or release occurs here.', '',
              f'Repaired mesh SHA-256: `{digest}`']
    for name, record in records.items():
        lines.append(f'- {name}: mesh `{record["mesh_sha256"]}`, package `{record["package_sha256"]}`, path view `{record["view_sha256"]}`.')
    with (output/'orientation-review.md').open('x', encoding='utf-8') as stream:
        stream.write('\n'.join(lines)+'\n')
    return report
