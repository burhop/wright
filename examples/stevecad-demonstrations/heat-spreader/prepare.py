"""Prepare a pinned SteveCAD/OASiS comparison; Wright alone executes it.

STEP transfer is an explicit preparation input from the documented CAD export.
This does not claim unattended downloading or arbitrary STEP-to-FE meshing.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
for package in (ROOT / "packages").iterdir():
    if (package / "src").is_dir():
        sys.path.insert(0, str(package / "src"))
spec = importlib.util.spec_from_file_location("example_helpers", ROOT / "scripts/engineering_campaign_binding_helpers.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
from workspace_service.workflow_run_paths import TOKEN, VERSION
from workspace_service.workflow_source_execution import compile_prompt_workflow, validate_workspace_authoring_shape

CASES = ("baseline_40", "revision_60")
ASSIGNMENT = ROOT / "tests/datasets/engineering-workflows/scenarios/heat-spreader-sizing/01-eink-sign-controller-strap"


def prepare(workspace: Path, attempt: str, tools: list, cad: Path, solver: str):
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", attempt):
        raise ValueError("Use a distinct lowercase attempt name")
    workspace = workspace.resolve(strict=True)
    relative = "stevecad/heat-spreader/" + attempt
    inputs = relative + "/inputs"
    outputs = relative + "/outputs/" + TOKEN
    sections, staged = [], []
    chain = []

    def select(server, name):
        matches = [x for x in tools if x['server_id'] == server and x['tool_name'] == name]
        if len(matches) != 1 or not re.fullmatch(r"[0-9a-f]{64}", matches[0]['schema_digest']):
            raise ValueError("Missing exact selected capability: " + server + "/" + name)
        return matches[0]

    def input_file(name, data, kind='engineering_document'):
        path = inputs + '/' + name
        h.write_once(workspace / path, data)
        key = 'input_' + re.sub(r'[^a-z0-9_]', '_', name.lower())
        staged.append({'path': path, 'sha256': h.digest(data)})
        sections.append({'kind': 'input', 'id': key, 'fields': {
            'name': name, 'purpose': 'Exact prepared input, not an execution result',
            'step_type': 'work', 'group': None, 'provided_by': 'engineer', 'inputs': [],
            'outputs': [h.port(key + '_artifact', kind)], 'instructions': 'Preserve exact bytes and declared scope.',
            'settings': {'input_mode': 'workspace-file', 'workspace_file': path}, 'tool': None, 'reusable_step': None}})
        return key + '.' + key + '_artifact', path

    def connect(source, target, key, kind='engineering_document'):
        target['fields']['inputs'].append(h.port(key, kind))
        sections.append({'kind': 'connection', 'id': 'bind_' + target['id'] + '_' + key,
                         'fields': {'type': 'item', 'from': source, 'to': target['id'] + '.' + key,
                                    'label': 'Exact upstream subject', 'when': None}})

    def task(identity, title, selected, arguments, filename):
        node = {'kind': 'task', 'id': identity, 'fields': {
            'name': title, 'purpose': title, 'step_type': 'work', 'group': None,
            'performed_by': 'configured_tool', 'inputs': [], 'outputs': [h.port(identity + '_response')],
            'prompt': '', 'tool': None, 'reusable_step': None,
            'settings': {'authoring_template': 'mcp-tool', 'mcp_server': selected['server_id'],
                         'mcp_tool': selected['name'], 'mcp_schema_digest': selected['schema_digest'],
                         'mcp_arguments': json.dumps(arguments), 'output_format': 'json',
                         'save_output': True, 'output_filename': outputs + '/' + filename,
                         'file_policy': 'indexed', 'run_path_template': VERSION, 'timeout_seconds': 180}}}
        sections.append(node)
        chain.append(node)
        return node

    def file_ports(node, paths):
        node['fields']['outputs'].extend(h.port(role, 'workspace_file') for role in paths)
        node['fields']['settings']['expected_file_ports'] = paths
        node['fields']['settings']['expected_files'] = '\n'.join(paths.values())

    def review(identity, title, source, profile=None):
        node = {'kind': 'task', 'id': identity, 'fields': {
            'name': title, 'purpose': title, 'step_type': 'review', 'group': None,
            'performed_by': 'engineer', 'inputs': [], 'outputs': [],
            'instructions': title + '. No physical acceptance or manufacturing authorization.',
            'settings': {'authoring_template': 'external-action-approval', 'action_kind': 'local_review',
                         'approval_binding': {'server': 'wright', 'tool': 'review_artifacts', 'schema': h.digest(b'wright.local_review.v1')},
                         'approval_destination': {'kind': 'local_review', 'id': 'workspace'},
                         'approval_settings': {'review_task_id': identity},
                         'approval_action': {'kind': 'local_review', 'mode': 'review_only'}},
            'tool': None, 'reusable_step': None}}
        if profile:
            node['fields']['settings']['approval_settings']['validation_review'] = profile
        connect(source, node, identity + '_subject', 'workspace_file' if identity == 'review_basis' else 'engineering_document')
        sections.append(node)
        chain.append(node)
        return node

    sections.append({'kind': 'workflow', 'id': 'stevecad_heat_spreader', 'fields': {
        'name': 'SteveCAD heat-spreader comparison', 'purpose': 'Select the narrowest original candidate using CAD identity and actual numerical fields.',
        'discipline': 'thermal', 'reviewed_ai_suggestions': True}})
    profile_name = 'heat-spreader-sizing-01-full'
    profile_root = ROOT / 'packages/workspace_service/src/workspace_service/process_validation/profiles'
    profile = json.loads((profile_root / (profile_name + '.json')).read_bytes())
    coverage = json.loads((profile_root / 'coverage.json').read_bytes())
    pinned = next(x['full_profile'] for x in coverage['scenarios'] if x['scenario_id'] == 'heat-spreader-sizing-01')
    basis_bytes = (ASSIGNMENT / 'context.md').read_bytes()
    basis_source = "from pathlib import Path\nimport skfem\nimport numpy as np\np = Path(" + repr('/workspace/' + outputs) + ")\np.mkdir(parents=True, exist_ok=True)\nwith (p/'thermal-basis.md').open('x', encoding='utf-8') as stream:\n    stream.write(" + repr(basis_bytes.decode('utf-8')) + ")\nprint('Recorded original model assumptions; scikit-fem', skfem.__version__)\n"
    basis = task('record_basis', 'Record the original thermal assumptions and backend readiness', select(solver, 'run_simulation'),
                 {'solver':'skfem', 'job_name':'stevecad-heat-basis-' + TOKEN, 'critic_approved':False, 'input_content':basis_source}, 'basis-receipt.json')
    file_ports(basis, {'basis': outputs + '/thermal-basis.md'})
    review('review_basis', 'Review the exact conduction-only model and claim scope', 'record_basis.basis',
           {'profile_ref': pinned['profile_ref'], 'requirement_ids': sorted(x['id'] for x in profile['baseline']['requirements'] if x['review_required'])})

    subjects = {'basis': ('record_basis.basis', 'workspace_file')}
    dependencies = {}
    measurements = {'source': 'SteveCAD full-build metadata, bound to exact exported STEP', 'cases': {}}
    model_ids = {}
    for case in CASES:
        receipt = json.loads((cad / ('02-generate-' + case + '.json')).read_bytes())
        model = receipt['result']['structuredContent']['model']
        document = receipt['result']['structuredContent']['document']
        data = (cad / (case + '.step')).read_bytes()
        if h.digest(data) != receipt['export']['sha256'] or model['status'] != 'succeeded':
            raise ValueError('Missing successful exact export for ' + case)
        metadata = model['metadata']
        span = metadata['bounds_mm']
        width = 40 if case == 'baseline_40' else 60
        if (span != [100.0, float(width), 2.0]
                or metadata['extent_mm'] != [0.,0.,0.,100.,float(width),2.]
                or metadata['solids'] != 1 or metadata['faces'] != 6
                or metadata['units'] != 'mm'
                or not math.isclose(metadata['volume_mm3'], 100 * width * 2, rel_tol=0, abs_tol=1e-6)):
            raise ValueError('Native CAD differs from original rectangular model')
        source, path = input_file(case + '.step', data, 'workspace_file')
        dependencies[case + '_geometry'] = (source, path)
        measurements['cases'][case] = {'dimensions_mm': dict(zip(('x','y','z'), span)), 'step_sha256': h.digest(data),
                                      'document_id': document['id'], 'revision': document['revision'], 'model_id': model['id']}
        model_ids[case] = model['id']
        read = task('read_' + case, 'Read editable ' + case + ' source', select('stevecad-mcp','read_design'), {'document_id':document['id']}, 'read-' + case + '.json')
        generate = task('generate_' + case, 'Generate the pinned ' + case + ' revision', select('stevecad-mcp','generate_model'),
                        {'document_id':document['id'], 'revision':document['revision']}, 'generate-' + case + '.json')
        file_ports(read, {'readback_' + case: outputs + '/read-' + case + '.json'})
        file_ports(generate, {'generated_' + case: outputs + '/generate-' + case + '.json'})
        dependencies['read_' + case] = (read['id'] + '.readback_' + case, outputs + '/read-' + case + '.json')
        dependencies['generate_' + case] = (generate['id'] + '.generated_' + case, outputs + '/generate-' + case + '.json')
    measurement_source, measurement_path = input_file('geometry-measurements.json', (json.dumps(measurements,indent=2)+'\n').encode(), 'workspace_file')
    dependencies['measurements'] = (measurement_source, measurement_path)
    csv_source, csv_path = input_file('alternatives.csv', (ASSIGNMENT / 'alternatives.csv').read_bytes(), 'workspace_file')
    dependencies['alternatives'] = (csv_source, csv_path)
    solver_code = (ROOT / 'scripts/engineering/heat_conduction_skfem.py').read_text(encoding='utf-8')
    code_source, code_path = input_file('heat_conduction_skfem.py', solver_code.encode(), 'workspace_file')
    dependencies['solver_source'] = (code_source, code_path)
    config = {'geometry_root': '/workspace/' + outputs, 'geometry_measurements': '/workspace/' + measurement_path,
              'alternatives_csv': '/workspace/' + csv_path, 'output_root': '/workspace/' + outputs}
    guard = "from pathlib import Path\nimport json\nimport shutil\n"
    guard += 'model_ids = ' + repr(model_ids) + '\n'
    guard += 'measurements = ' + repr(measurements['cases']) + '\n'
    guard += 'root = Path(' + repr('/workspace/' + outputs) + ')\n'
    guard += 'geometry_inputs = Path(' + repr('/workspace/' + inputs) + ')\n'
    guard += '''for case, expected in measurements.items():
    native = json.loads((root / ('generate-' + case + '.json')).read_text())
    source = json.loads((root / ('read-' + case + '.json')).read_text())
    assert native['model']['status'] == 'succeeded'
    assert native['model']['id'] == expected['model_id'], 'Pinned CAD build changed'
    assert native['document']['revision'] == expected['revision'], 'CAD revision changed'
    assert source['document']['revision'] == expected['revision'], 'Current source requires a new accepted binding'
    assert native['model']['metadata']['bounds_mm'] == list(expected['dimensions_mm'].values())
    destination = root / (case + '.step')
    assert not destination.exists(), 'Fresh run output required'
    shutil.copyfile(geometry_inputs / (case + '.step'), destination)
'''
    arguments = {'solver': 'skfem', 'job_name': 'stevecad-heat-' + TOKEN, 'critic_approved': False,
                 'input_content': guard + 'HEAT_CONFIG = ' + repr(config) + '\nexec(compile(' + repr(solver_code) + ", 'heat_conduction_skfem.py', 'exec'))\n"}
    solve = task('compute_fields', 'Compute both numerical fields and refinement checks', select(solver, 'run_simulation'), arguments, 'solver-execution.json')
    dep_paths = {}
    for key, (source, path) in dependencies.items():
        connect(source, solve, 'dependency_' + key, 'workspace_file')
        dep_paths['dependency_' + key] = path
    solve['fields']['settings']['mcp_file_dependencies'] = dep_paths
    paths = {case + '_' + level: outputs + '/' + case + '-' + level + '-temperature.csv' for case in CASES for level in ('coarse','fine')}
    paths.update({case + '_geometry':outputs + '/' + case + '.step' for case in CASES})
    paths.update({'decision':outputs + '/sizing-decision.json','correspondence':outputs + '/geometry-analysis-correspondence.json'})
    file_ports(solve, paths)
    solve['fields']['settings']['expected_files'] += '\n' + '\n'.join(outputs + '/' + case + '-' + level + '-temperature.vtu' for case in CASES for level in ('coarse','fine'))
    for role in paths:
        subjects[role] = ('compute_fields.' + role, 'workspace_file')
    validation = {'kind':'task','id':'validate_outputs','fields':{
        'name':'Independently validate exact geometry and thermal fields','purpose':'Original complete 082 engineering checks and genuine review authority',
        'step_type':'work','group':None,'performed_by':'configured_tool','inputs':[],'outputs':[h.port('assessment')], 'prompt':'',
        'settings':{'authoring_template':'process-validator','output_format':'json','max_revisions':0,
                    'validation':{'profile':{'source':'packaged','name':profile_name,'reference':pinned['profile_ref']},
                                  'baseline':pinned['baseline_ref'],'subjects':{role:'validate_' + role for role in subjects}}},'tool':None,'reusable_step':None}}
    for role, (source, kind) in subjects.items():
        connect(source, validation, 'validate_' + role, kind)
    sections.append(validation)
    chain.append(validation)
    review('review_result', 'Review the sizing decision, field checks and pending provider critic', 'validate_outputs.assessment')
    for before, after in zip(chain, chain[1:]):
        sections.append({'kind':'connection','id':'order_' + after['id'], 'fields':{'type':'order','from':before['id'],'to':after['id'],'label':'Declared process order','when':None}})
    source = h.render_new_draft(sections)
    validate_workspace_authoring_shape(source)
    plan = compile_prompt_workflow(source)
    target = workspace / relative / 'prepared.workflow.wflow'
    h.write_once(target, source.encode())
    report = {'status':'prepared_not_executed','source_path':relative + '/prepared.workflow.wflow',
              'accepted_source_path':'workflows/stevecad-heat-spreader-' + attempt + '.workflow.wflow',
              'source_sha256':h.digest(source.encode()),'inputs':staged,'step_count':len(plan.steps),
              'cad_measurements':measurements, 'solver_server':solver,'output_template':outputs,
              'limitations':['Exact STEP exports are explicit preparation inputs; no unattended transfer is claimed.',
                             'Solver constructs rectangular FE meshes from measured dimensions; it does not mesh arbitrary STEP topology.',
                             'OASiS critic remains false; real reviews are not granted by this preparer.']}
    h.write_once(workspace / relative / 'preparation.json', (json.dumps(report,indent=2)+'\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--attempt', required=True)
    parser.add_argument('--tools', required=True, type=Path)
    parser.add_argument('--cad', required=True, type=Path)
    parser.add_argument('--solver-server', required=True)
    args = parser.parse_args()
    tools = json.loads(args.tools.read_bytes())
    result = prepare(args.workspace, args.attempt, tools['tools'] if isinstance(tools,dict) else tools, args.cad, args.solver_server)
    print(json.dumps(result,indent=2))
