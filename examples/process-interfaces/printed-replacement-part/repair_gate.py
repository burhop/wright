"""Optional authored early gate on existing MCP and Feature082 mechanisms."""
import hashlib
import json
from pathlib import Path

from core.process_validation import ValidationProfile


def qualify(binding):
    """Validate and freeze the optional declaration before staging any inputs."""
    if not isinstance(binding, dict) or set(binding) != {'server', 'tool', 'arguments_file'}:
        raise ValueError('Declare the independent repair-completion capability and exact arguments file')
    if any(not isinstance(binding[key], str) or not binding[key].strip() for key in ('server', 'tool')):
        raise ValueError('Declare the independent repair-completion server and tool')
    reference = binding['arguments_file']
    if not isinstance(reference, dict) or set(reference) != {'path', 'sha256'}:
        raise ValueError('Pin repair-completion arguments by path and SHA256')
    path = Path(reference['path'])
    if not path.is_file() or path.stat().st_size > 65536:
        raise ValueError('Repair-completion arguments must be a bounded regular file')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != reference['sha256']:
        raise ValueError('The bounded repair-completion arguments changed')
    if not isinstance(json.loads(raw), dict):
        raise ValueError('Supply actual configured tool arguments')
    return binding, raw


def add(flow, definition, qualified, original_profile, create, repair, files_server):
    binding, raw = qualified
    reference = binding['arguments_file']
    arguments = flow.input_bytes('repair-completion-arguments.json', raw, original=reference['path'], run_paths=bool(flow.run_path_template))
    retain = flow.stage('retain_repair_response', 'Retain the actual repair response for completion inspection')
    response_port = flow.reference(repair['id'] + '.' + repair['id'] + '_result', retain, 'actual_repair_response')
    response_name = 'repair-provider-response.json'
    flow.exact_mcp(retain, flow.select(files_server, 'write_text_document'), response_port, (response_name,), 'repair-response-retention-receipt.json')
    retain['fields']['settings'].update(
        mcp_arguments_source='fields',
        mcp_argument_ports=json.dumps({response_port: 'content'}),
        mcp_arguments=json.dumps({'relativePath': flow.output + '/' + response_name, 'mediaType': 'application/json', 'overwrite': False}),
    )
    flow.file_outputs(retain, {'repair_response': flow.output + '/' + response_name})
    inspect = flow.stage('inspect_repair_completion', 'Confirm the repair completed, including its preview')
    argument_port = flow.reference(arguments, inspect, 'exact_arguments')
    flow.exact_mcp(inspect, flow.select(binding['server'], binding['tool']), argument_port, ('repair-completion.json',), 'repair-completion-provider-response.json')
    dependencies = {}
    for producer, port, name in [(retain, 'repair_response', response_name), (create, 'source_mesh', 'source_mesh.stl'), (repair, 'repaired_mesh', 'repaired_mesh.stl'), (repair, 'mesh_preview', 'mesh-preview.png')]:
        key = flow.reference(producer['id'] + '.' + port, inspect, port, 'workspace_file')
        dependencies[key] = flow.output + '/' + name
    inspect['fields']['settings']['mcp_file_dependencies'] = dependencies
    flow.file_outputs(inspect, {'completion': flow.output + '/repair-completion.json'})
    # Preserve the original five mesh checks verbatim. The original full profile
    # remains later in the process, including every human-review requirement.
    checks = [item for item in original_profile['checks'] if item['subject_role'] == 'repaired_mesh']
    requirement_ids = {identity for check in checks for identity in check['requirement_ids']}
    baseline = {**original_profile['baseline'], 'id': original_profile['baseline']['id'] + '-early-mesh', 'requirements': [item for item in original_profile['baseline']['requirements'] if item['id'] in requirement_ids]}
    baseline['requirements'].append({'id': 'PRINT01-REPAIR-COMPLETION', 'text': 'The declared repair operation emits its final typed record after verifying exported mesh and completing preview generation; partial outputs cannot release slicing.', 'sources': [{'artifact_ref': flow.input_root + '/repair-completion-arguments.json', 'sha256': reference['sha256'], 'locator': 'Declared final completion record inspection'}], 'scope': 'content', 'mandatory': True, 'review_required': False})
    checks.append({'id': 'repair-program-completed', 'version': '1', 'requirement_ids': ['PRINT01-REPAIR-COMPLETION'], 'subject_role': 'completion', 'reader': 'structured', 'selector': '/completed_program_record', 'constraint': {'operator': 'equals', 'expected': True}, 'evidence_method': 'structured_value', 'parameters': {}})
    profile = ValidationProfile.model_validate({'id': original_profile['id'] + '-early-mesh', 'version': '1', 'baseline': baseline, 'checks': checks, 'supported_kinds': ['file'], 'limitations': ['Early program-completion and mesh handoff gate only; original full profile and engineering reviews remain mandatory.']})
    profile_name = 'early-mesh-profile.json'
    profile_ref = flow.input_bytes(profile_name, profile.model_dump_json(indent=2).encode(), kind='workspace_file')
    flow.reference(profile_ref, inspect, 'early_gate_definition', 'workspace_file')
    inspect['fields']['settings']['mcp_file_dependencies'][inspect['id'] + '_early_gate_definition'] = flow.input_root + '/' + profile_name
    gate = flow.stage('validate_mesh_before_slice', 'Check repaired mesh before slicing')
    gate['fields']['prompt'] = ''
    gate['fields']['outputs'] = [definition.port('early_mesh_assessment')]
    subjects = {}
    for role, producer, port in [('source_mesh', create, 'source_mesh'), ('repaired_mesh', repair, 'repaired_mesh'), ('completion', inspect, 'completion')]:
        subjects[role] = flow.reference(producer['id'] + '.' + port, gate, role, 'workspace_file')
    gate['fields']['settings'] = {'authoring_template': 'process-validator', 'max_revisions': 0, 'validation': {'profile': {'source': 'workspace', 'name': flow.input_root + '/' + profile_name, 'reference': profile.reference().model_dump()}, 'baseline': profile.baseline.reference().model_dump(), 'subjects': subjects}}
    return retain, inspect, gate
