"""Numerical/lineage fixtures for the authored handle study, not provider proof."""
import importlib.util
import json
from pathlib import Path
import struct
import zipfile

import pytest

ASSET = Path(__file__).parents[1] / 'examples/process-interfaces/printed-replacement-part/handle-orientation-study.py'
spec = importlib.util.spec_from_file_location('handle_study', ASSET)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def asymmetric_tetrahedron():
    # Deliberately different Y/Z spans reveal accidental model/build frame mixing.
    points = ((0, -12, 0), (96, -12, 0), (0, 12, 0), (0, -12, 34))
    raw = bytearray(bytes(80) + struct.pack('<I', 4))
    for face in ((0,2,1), (0,1,3), (0,3,2), (1,2,3)):
        triangle = tuple(points[i] for i in face)
        normal, _ = study.normal_area(triangle)
        raw.extend(struct.pack('<12fH', *normal, *(v for p in triangle for v in p), 0))
    return bytes(raw)


@pytest.mark.parametrize('orientation,spans', [('pads_down', [96,24,34]), ('side', [96,34,24])])
def test_handle_rotation_preserves_geometry_and_records_model_to_build_frame(orientation, spans):
    raw = asymmetric_tetrahedron()
    transformed, facts = study.transform(raw, orientation)
    assert [b-a for a,b in zip(*facts['bounds_mm'])] == spans
    assert facts['bounds_mm'][0][2] == 0
    assert facts['rotation_determinant'] == 1
    assert facts['frame_span_error_mm'] == 0
    assert facts['volume_relative_error'] < 1e-10
    assert facts['area_relative_error'] < 1e-10
    assert facts['source_sha256'] == study.sha(raw)
    assert facts['mesh_sha256'] == study.sha(transformed)
    if orientation == 'side':
        assert facts['build_transform'] == [[1,0,0,0],[0,0,-1,0],[0,1,0,12],[0,0,0,1]]


@pytest.fixture
def comparison(tmp_path):
    raw = asymmetric_tetrahedron()
    (tmp_path/'repaired.stl').write_bytes(raw)
    config = dict(workspace_root=str(tmp_path), source_mesh='repaired.stl',
                  source_sha256=study.sha(raw), output_root='outputs',
                  profile_sha256={role: study.sha(b'{}') for role in ('machine','process','filament')},
                  gcode_entry='Metadata/plate_1.gcode',
                  reported_usage_prefixes={'time': '; fixture time:'})
    geometry = study.prepare(config)
    for name in study.CANDIDATES:
        folder = tmp_path/'outputs'/name
        with zipfile.ZipFile(folder/'package.gcode.3mf', 'w') as archive:
            archive.writestr(config['gcode_entry'], '; fixture time: 10s\n')
        package_sha = study.sha((folder/'package.gcode.3mf').read_bytes())
        (folder/'slice-evidence.json').write_text(json.dumps(dict(
            source_sha256=geometry['cases'][name]['mesh_sha256'], package_sha256=package_sha)))
        (folder/'support-preview.json').write_text(json.dumps(dict(
            package_sha256=package_sha, classification_source='gcode_feature_comments',
            provenance={'unclassified_features': ['fixture_unknown']},
            layers=[{'z': 0.2, 'model': [[0,0,10,0]], 'support': [[2,0,2,5]],
                     'unclassified': [[3,0,3,1]]}])))
        for role in config['profile_sha256']:
            (folder/(role+'-profile.json')).write_bytes(b'{}')
    return tmp_path, config, raw


def test_comparison_consumes_real_fixture_artifacts_without_selecting_or_accepting(comparison):
    root, config, raw = comparison
    report = study.compare(config)
    assert report['source_matches_dependency'] and report['same_profiles']
    assert report['engineering_acceptance'] is False
    assert report['physical_acceptance'] is False
    assert report['final_package_orientation'] == 'pads_down_original_repaired_mesh'
    for case in report['cases'].values():
        assert case['path_length_mm']['support'] == 5
        assert case['support_path_bounds_build_mm'] == [[2,0,0.2],[2,5,0.2]]
        assert case['unclassified_features'] == ['fixture_unknown']
        assert case['path_length_mm']['unclassified'] == 1
        assert case['classification_known'] is True
    assert (root/'repaired.stl').read_bytes() == raw
    assert (root/'outputs/source_mesh.stl').read_bytes() == raw
    with pytest.raises(FileExistsError):
        study.prepare(config)


@pytest.mark.parametrize('fault', ['source', 'source_copy', 'candidate', 'matrix', 'preview', 'profile', 'package'])
def test_comparison_rejects_changed_dependencies(comparison, fault):
    root, config, _ = comparison
    files = dict(source='repaired.stl', source_copy='outputs/source_mesh.stl',
                 candidate='outputs/side/oriented.stl', profile='outputs/side/process-profile.json',
                 package='outputs/side/package.gcode.3mf')
    if fault in files:
        path = root/files[fault]
        path.write_bytes(path.read_bytes()+b'changed')
    elif fault == 'matrix':
        path = root/'outputs/orientation-geometry.json'
        record = json.loads(path.read_bytes())
        record['cases']['side']['build_transform'][0][0] = 2
        path.write_text(json.dumps(record))
    else:
        path = root/'outputs/side/support-preview.json'
        record = json.loads(path.read_bytes())
        record['package_sha256'] = '0'*64
        path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        study.compare(config)
    assert not (root/'outputs/orientation-comparison.json').exists()


def test_unknown_classification_is_explicit():
    view = dict(layers=[dict(z=.2, model=[[0,0,1,0]], support=[], unclassified=[])], provenance={})
    result = study.path_facts(view)
    assert result['classification_known'] is False
    assert result['support_path_bounds_build_mm'] is None
    with pytest.raises(ValueError, match='Unknown handle orientation'):
        study.transform(asymmetric_tetrahedron(), 'socket_up')
