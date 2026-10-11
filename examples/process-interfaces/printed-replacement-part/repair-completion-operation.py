"""Authored passive inspection of this example's explicit completion record.

Sent to an independent configured Python-capable MCP provider. It does not infer
success from human-readable error wording or file existence, and never executes
the repair again. Independent STL validation remains Wright's existing reader.
"""
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath

CONFIG = __WRIGHT_REPAIR_COMPLETION_CONFIG__  # noqa: F821
response_path = Path(CONFIG['response_path'])
response_raw = response_path.read_bytes()
response = json.loads(response_raw)
assert isinstance(response, dict) and isinstance(response.get('result'), str), 'The declared repair response record is missing'
marker = 'W083_FINAL_REPORT '
records = [line[len(marker):] for line in response['result'].splitlines() if line.startswith(marker)]
assert len(records) == 1, 'Repair did not emit its one declared final completion record; partial files do not release slicing'
record = ast.literal_eval(records[0])
assert isinstance(record, dict), 'Malformed final repair completion record'
required = {'source_actual', 'repair', 'transform', 'post_transform_object', 'exported_binary_stl_verified', 'outputs', 'support_consequences', 'remaining_review_limits'}
assert set(record) == required, 'Unexpected repair completion schema'
for role in ('source_actual', 'post_transform_object', 'exported_binary_stl_verified'):
    values = record[role]
    assert isinstance(values, dict)
    for key in ('non_manifold_edges', 'boundary_edges', 'degenerate_faces', 'winding_conflicts'):
        assert type(values.get(key)) is int and values[key] == 0, 'Repair completion reports invalid topology: ' + role + '/' + key
    assert type(values.get('triangles')) is int and 0 < values['triangles'] <= 80000
assert record['repair']['dimensions_preserved'] is True
output = Path(CONFIG['output_path'])
assert not output.exists(), 'Preserve prior completion evidence'
output.parent.mkdir(parents=True, exist_ok=True)
file_records = {}
for role in ('source_path', 'repaired_path', 'preview_path'):
    path = Path(CONFIG[role])
    assert path.is_file() and path.stat().st_size > 0, 'Expected actual repair file is missing: ' + role
    raw = path.read_bytes()
    file_records[role] = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
path_types = {'windows': PureWindowsPath, 'posix': PurePosixPath}
assert CONFIG.get('producer_path_style') in path_types, 'Declare the producer path convention'
producer_path = path_types[CONFIG['producer_path_style']]
expected_outputs = CONFIG['producer_output_paths']
assert set(expected_outputs) == {'repaired_mesh_stl', 'geometry_only_preview_png'}
for role in expected_outputs:
    observed = producer_path(record['outputs'][role])
    expected = producer_path(expected_outputs[role])
    assert observed.is_absolute() and expected.is_absolute()
    assert '..' not in observed.parts and '..' not in expected.parts
    assert observed == expected, 'Repair completion refers to another output: ' + role
receipt = {'schema_version': 'wright.example-repair-completion/1', 'completed_program_record': True, 'producer_reported_topology_valid': True,
           'response_sha256': hashlib.sha256(response_raw).hexdigest(), 'files': file_records, 'reported': record,
           'scope': 'Explicit program completion and typed producer observations only; independent mesh reader checks remain mandatory',
           'engineering_acceptance': False, 'physical_acceptance': False}
output.write_text(json.dumps(receipt, indent=2))
print(json.dumps({'operation_status': 'completed_record_inspection', 'receipt': str(output), 'engineering_acceptance': False}))
