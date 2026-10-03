"""Once-only digital qualification of generated stages on the durable runtime."""
from pathlib import Path
import asyncio
import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import time

repo = Path('D:/repos/wright')
base = repo / '.local-run/process-interfaces-083'
root = base / 't048-external-slice-runtime-007'
root.mkdir(exist_ok=False)
workspace = Path('C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/external-slice-runtime-007')
workspace.mkdir(exist_ok=False)
db = root / 'state.db'
os.environ['DATABASE_PATH'] = str(db)
os.environ['WRIGHT_WORKFLOW_INTEGRATION_TESTS'] = '1'
os.environ['WRIGHT_MCP_TIMEOUT'] = '600'
os.environ['WRIGHT_MCP_MAX_TIMEOUT'] = '600'

from api.composition import build_api_gateway_service, workspace_service
from api.config import McpTransportSettings
from core.process_interactions import ProcessRef
from core.redaction import redact_validation_payload
from data_vault import upgrade_database
from tool_registry import McpEngine
from tool_registry.db import insert_server, insert_tools
from tool_registry.models import McpServer, McpTool
from tool_registry.runners.stdio import StdioRunner
from workspace_service.process_interfaces.service import ProcessScope
from workspace_service.workflow_mcp_execution import schema_digest
from workspace_service.workflow_source_execution import compile_prompt_workflow, validate_workspace_authoring_shape

label = 'external-slice-runtime-007'
workspace_id = 'workspace-083-external-slice-007'
session_id = 'session-083-external-slice-007'
containers = []
gateway = service = None
proof = {'status': 'preflight', 'scope': 'Generated slice/response-retention/passive-inspection declarations on the accepted source and existing durable runtime; small digital qualification only',
         'physical_dispatch': False, 'human_engineering_acceptance': False,
         'public_catalog_promotion': False, 'ai_generation': False, 'workspace': str(workspace)}


def persist():
    (root / 'qualification.json').write_text(json.dumps(redact_validation_payload(proof), indent=2) + '\n', encoding='utf-8')


def docker(*args, timeout=30):
    result = subprocess.run(['docker', *args], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError('Owned Docker command failed: ' + result.stderr[-1800:])
    return result.stdout.strip()


def container(image, name):
    identity = docker('run', '--detach', '--platform', 'linux/amd64', '--name', name,
                      '--label', 'wright.feature=083-process-working-interfaces', '--label', 'wright.proof=' + label,
                      '--network', 'none', '--mount', f'type=bind,src={workspace},dst=/workspace',
                      '--entrypoint', 'sleep', image, 'infinity')
    containers.append(identity)
    state = json.loads(docker('inspect', identity))[0]
    assert state['Id'] == identity and state['State']['Running']
    assert state['HostConfig']['NetworkMode'] == 'none'
    assert len(state['Mounts']) == 1 and state['Mounts'][0]['Destination'] == '/workspace'
    persist()
    return identity


async def discover(server_id, command, env, source_url, revision, cwd=None):
    runner = StdioRunner(command, env=env, cwd=cwd, startup_timeout=60, operation_timeout=600)
    try:
        await runner.start()
        tools = await runner.list_tools()
        (root / (server_id + '-tools.json')).write_text(json.dumps(redact_validation_payload({'tools': tools}), indent=2) + '\n', encoding='utf-8')
    finally:
        await runner.stop()
    now = int(time.time())
    insert_server(str(db), McpServer(server_id=server_id, name='Isolated runtime qualification ' + server_id,
        type='stdio', command=command, launch_env=env, is_active=True, is_installed=True,
        status='active', created_at=now, updated_at=now, source_url=source_url,
        installed_version=revision, risk_level='high', default_enabled=False))
    insert_tools(str(db), [McpTool(tool_id=server_id + ':' + row['name'], server_id=server_id,
        name=row['name'], title=row.get('title'), description=row.get('description'),
        input_schema=row['inputSchema'], output_schema=row.get('outputSchema'),
        annotations=row.get('annotations') or {}, meta=row.get('_meta') or {},
        is_enabled=True, created_at=now) for row in tools])
    return tools


async def main():
    global gateway, service
    upgrade_database(db)
    service = workspace_service()
    service.ensure_workspace_path_safe(str(workspace))
    inspection_basis = json.loads((base / 't043-oasis-clean-base-003/qualification.json').read_bytes())
    geometry_basis = json.loads((base / 't043-blender-clean-continuation-002/qualification.json').read_bytes())
    assert inspection_basis['status'] == geometry_basis['status'] == 'passed'
    inspector = container(inspection_basis['selected_image'], 'wright-083-external-slice-inspection-007')
    geometry = container(geometry_basis['selected_image'], 'wright-083-external-slice-geometry-007')
    (workspace / 'bootstrap.py').write_bytes((base / 't043-blender-clean-continuation-002/workspace/bootstrap.py').read_bytes())
    docker('exec', '--detach', '-e', 'LIBGL_ALWAYS_SOFTWARE=1', '-e', 'BLENDER_MCP_SAFE_MODE=true', geometry,
           'sh', '-c', 'exec xvfb-run -a blender --factory-startup --python /workspace/bootstrap.py > /workspace/blender.log 2>&1')
    ready = docker('exec', geometry, 'python3', '-c',
        "import socket,time\nfor n in range(60):\n try:\n  s=socket.create_connection(('127.0.0.1',19988),timeout=1);s.close();print('ready');break\n except OSError:time.sleep(1)\nelse:raise SystemExit('Owned Blender did not become ready')", timeout=75)
    assert ready == 'ready'
    inspection_definition = json.loads((base / 't043-oasis-clean-base-003/gateway-definition.json').read_bytes())
    inspect_command = [inspector if part == inspection_basis['runtime_container'] else part for part in inspection_definition['command']]
    inspection_id = 'qualification-083-runtime-inspection'
    await discover(inspection_id, inspect_command, {}, inspection_basis['source_url'], inspection_basis['source_revision'])
    geometry_id = 'qualification-083-runtime-geometry'
    geometry_command = ['docker', 'exec', '-i', '-e', 'PYTHONPATH=', '-e', 'BLENDER_HOST=127.0.0.1', '-e', 'BLENDER_PORT=19988',
                        '-e', 'BLENDER_MCP_SAFE_MODE=true', '-e', 'BLENDER_MCP_DISABLE_TELEMETRY=true', geometry,
                        '/selected/venv/bin/python', '-m', 'blender_mcp.server']
    await discover(geometry_id, geometry_command, {}, geometry_basis['source_url'], geometry_basis['source_revision'])
    slicer_definition = json.loads((base / 't048-external-slice-probe-retirement-001/native-independent-002/definition.json').read_bytes())
    slicer_id = 'qualification-083-runtime-slicer'
    slicer_env = dict(slicer_definition['env'])
    slicer_env.update(BAMBU_STUDIO_CONFIG=str(workspace / 'provider-config'), BAMBU_SLICE_DIR=str(workspace / 'provider-slice-cache'))
    await discover(slicer_id, slicer_definition['command'], slicer_env,
                   'https://github.com/marctheshark3/bambu-p1s-mcp', '7b50d0288fb7b91af8af422b96c4df4db0f1110c')
    now = int(time.time())
    with sqlite3.connect(db) as connection:
        connection.execute('INSERT INTO engineering_workspaces (workspace_id,session_id,local_path,enabled_tools,created_at,updated_at) VALUES (?,?,?,?,?,?)',
                           (workspace_id, session_id, str(workspace), json.dumps([inspection_id, geometry_id, slicer_id, 'wright-workspace-files']), now, now))
        connection.execute('INSERT INTO workspace_agent_sessions (workspace_id,session_id,agent_id,created_at,updated_at) VALUES (?,?,?,?,?)',
                           (workspace_id, session_id, 'hermes', now, now))
    engine = McpEngine(str(db), operation_timeout=600)
    gateway = build_api_gateway_service(str(db), engine, McpTransportSettings.from_env())
    gateway.open_session(session_id='discovery-083-slice-runtime', principal_id='qualification-083-local',
                         workspace_id=workspace_id, transport='streamable_http', binding_session_id=session_id)
    gateway.initialize_session('discovery-083-slice-runtime', protocol_version='2025-11-25', client_name='bounded-qualification', client_version='1', client_capabilities={})
    tools = gateway.list_tools('discovery-083-slice-runtime')
    rows = {tool.name: {'server_id': tool.server_id, 'tool_name': tool.tool_name,
                       'name': tool.name, 'schema_digest': schema_digest(tool)} for tool in tools}
    spec = importlib.util.spec_from_file_location('runtime_slice_declarations', repo / 'scripts/engineering_external_slice_binding.py')
    declarations = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(declarations)
    helpers = declarations.helpers
    scenario = 'printed-replacement-part-01'
    original = json.loads((repo / 'tests/datasets/engineering-workflows/bindings/printed-replacement-part.json').read_bytes())['scenarios'][scenario]['process']
    selected = {role: next(row for row in rows.values() if row['server_id'] == identity and row['tool_name'] == tool_name)
                for role, identity, tool_name in [('slicer', slicer_id, 'slice_model_file'),
                    ('files', 'wright-workspace-files', 'write_text_document'), ('inspection', inspection_id, 'run_simulation'),
                    ('geometry', geometry_id, 'execute_blender_code')]}
    binding = {'schema_version': 1, 'scenario_id': scenario,
               **{role: {'server': selected[role]['server_id'], 'tool': selected[role]['tool_name'], 'schema_digest': selected[role]['schema_digest']} for role in ('slicer', 'files', 'inspection')},
               **{key: slicer_definition[key] for key in ('profiles', 'success_field', 'success_contract', 'expected_response_fields', 'gcode_entry')}}
    binding['slicer']['arguments'] = slicer_definition['arguments']
    binding['inspection'].update(workspace_mount='/workspace', backend='skfem')
    binding['nominal_layer_section'] = {'start_marker': '; MACHINE_START_GCODE_END', 'end_marker': '; MACHINE_END_GCODE_START'}
    binding_path = root / 'external-binding.json'
    binding_path.write_text(json.dumps(binding, indent=2) + '\n', encoding='utf-8')
    prepared = declarations.preflight(binding_path, scenario, rows, original)
    output_root, input_root = 'qualification/artifacts', 'qualification/inputs'
    (workspace / output_root).mkdir(parents=True)
    (workspace / input_root).mkdir(parents=True)
    source_mesh = output_root + '/source_mesh.stl'
    geometry_code = "import bpy\nbpy.ops.mesh.primitive_cube_add(size=1)\nobj=bpy.context.object\nobj.name='RuntimeQualificationCube'\nobj.dimensions=(10,8,6)\nbpy.ops.object.transform_apply(location=False,rotation=False,scale=True)\nbpy.ops.wm.stl_export(filepath='/workspace/qualification/artifacts/source_mesh.stl',export_selected_objects=True)\nprint('Actual qualification geometry exported: 10 x 8 x 6 model units')\n"
    producer = {'kind': 'task', 'id': 'qualified_geometry', 'fields': {
        'name': 'Create isolated qualification geometry', 'purpose': 'Actual small native geometry for stage integration; not the engineering assignment',
        'step_type': 'work', 'group': None, 'performed_by': 'configured_tool', 'inputs': [],
        'outputs': [helpers.port('geometry_result'), helpers.port('source_mesh', 'workspace_file')],
        'prompt': '', 'tool': None, 'reusable_step': None,
        'settings': {'authoring_template': 'mcp-tool', 'mcp_server': geometry_id,
            'mcp_tool': selected['geometry']['name'], 'mcp_schema_digest': selected['geometry']['schema_digest'],
            'mcp_arguments': json.dumps({'code': geometry_code, 'user_prompt': 'resume'}),
            'output_format': 'json', 'save_output': True, 'output_filename': output_root + '/geometry-response.json',
            'file_policy': 'overwrite', 'expected_files': source_mesh, 'expected_file_ports': {'source_mesh': source_mesh}, 'timeout_seconds': 600}}}
    inspection = {'kind': 'task', 'id': 'inspect_actual_package', 'fields': {'name': 'Inspect actual package', 'purpose': 'Retain passive evidence from the actual independently sliced package', 'group': None, 'inputs': [], 'outputs': [], 'settings': {}}}
    sections = [{'kind': 'workflow', 'id': 'external_slice_qualification', 'fields': {'name': 'Independent slice runtime qualification', 'purpose': 'Qualify actual tool handoffs through the accepted source runtime without physical dispatch', 'discipline': 'engineering.integration', 'reviewed_ai_suggestions': True}}, producer, inspection]
    staged = []
    proof['declaration'] = declarations.bind(sections, inspection, 'qualified_geometry.source_mesh',
        workspace=workspace, input_root=input_root, output_root=output_root, source=source_mesh,
        prepared=prepared, staged=staged, operation_label='actual_local_bambu_slice')
    source_text = helpers.render(sections)
    shape = validate_workspace_authoring_shape(source_text)
    plan = compile_prompt_workflow(source_text)
    source_path = 'workflows/external-slice-qualification.workflow.wflow'
    document = await service.workflow_sources.create(str(workspace), source_path, source_text)
    process = ProcessRef(workspace_id=workspace_id, source_path=source_path, source_digest=document.storage_digest)
    scope = ProcessScope(principal_id='qualification-083-local', workspace_id=workspace_id,
                         capabilities=frozenset({'process.read', 'process.inputs', 'process.start', 'process.results'}))
    policy_digest = service.workflow_integration_policies.enroll(
        campaign_id='083-external-slice-runtime-007', dataset_id='isolated-stage-integration-007',
        dataset_digest=hashlib.sha256(json.dumps(staged, sort_keys=True).encode()).hexdigest(),
        workspace_id=workspace_id, source_path=source_path, source_digest=document.storage_digest,
        input_files={item['path']:item['sha256'] for item in staged}, output_root=output_root,
        allowed_tools=[{key:value[key] for key in ('server_id','name','schema_digest')} for value in selected.values()],
        approval_mode='auto', test_destinations=(), expires_at=int(time.time())+3600)
    proof.update(integration_policy_digest=policy_digest, integration_test=True,
                 actor='integration_test:083-external-slice-runtime-007', synthetic_review_decisions=0)
    app = service.process_interfaces
    values = await app.set_inputs(scope, process, gateway=gateway, session_id=session_id)
    readiness = await app.check_readiness(scope, process, values.snapshot.snapshot_id, gateway=gateway, session_id=session_id)
    proof.update(process=process.model_dump(mode='json'), readiness=readiness.model_dump(mode='json'),
                 staged_inputs=staged, steps=[step.id for step in plan.steps], shape=shape)
    assert readiness.state == 'ready'
    assert not (workspace / source_mesh).exists()
    assert not (workspace / output_root / 'slice_package.gcode.3mf').exists()
    persist()

    async def no_model(*args, **kwargs):
        raise AssertionError('Configured qualification must not ask an opportunistic AI question or invoke a model')

    receipt = await app.runs.start(scope, process, values.snapshot.snapshot_id, 'qualification-start-once',
        expected_input_digest=values.snapshot.digest, response_generator=no_model, gateway=gateway, session_id=session_id, integration_policy_digest=policy_digest)
    proof.update(status='running', start_receipt=receipt.model_dump(mode='json'))
    persist()
    result = await asyncio.wait_for(asyncio.shield(app.runs.wait(scope, process, receipt.run_id)), 600)
    proof['result'] = result
    persist()
    assert result['status'] == 'completed', 'Recorded canonical run did not complete; reconcile retained stages, never replay its start'
    second_receipt = await app.runs.start(scope, process, values.snapshot.snapshot_id, 'qualification-start-once',
        expected_input_digest=values.snapshot.digest, response_generator=no_model, gateway=gateway, session_id=session_id, integration_policy_digest=policy_digest)
    assert second_receipt == receipt
    proof['duplicate_start_reconciles_same_receipt'] = True
    with sqlite3.connect(db) as connection:
        proof['audit'] = [dict(zip(('operation', 'target', 'outcome', 'reason'), row)) for row in connection.execute(
            "SELECT operation,target_name,outcome,reason_code FROM gateway_audit_events WHERE operation='tool.call' ORDER BY occurred_at")]
    completed = [row['target'] for row in proof['audit'] if row['outcome'] == 'succeeded']
    assert completed.count('slice_model_file') == 1
    assert completed.count('run_simulation') == 1
    assert completed.count('execute_blender_code') == 1
    assert completed.count('write_text_document') == 1
    proof.update(status='passed', completed_tool_calls=completed, source_sha256=hashlib.sha256(source_text.encode()).hexdigest())


async def owned_run():
    try:
        await main()
    except Exception as error:
        proof.update(status='failed', error_type=type(error).__name__, diagnostic=str(error)[:2000])
    finally:
        if service is not None:
            await service.close()
            proof['durable_runtime_owner_closed'] = True
        if gateway is not None:
            await gateway.shutdown()
            proof['gateway_closed'] = True
        cleanup = []
        for identity in containers:
            state = json.loads(docker('inspect', identity))[0]
            assert state['Id'] == identity and state['Config']['Labels']['wright.proof'] == label
            assert state['Config']['Labels']['wright.feature'] == '083-process-working-interfaces'
            docker('stop', '--time', '10', identity)
            assert not json.loads(docker('inspect', identity))[0]['State']['Running']
            cleanup.append({'container_id': identity, 'running': False})
        proof['cleanup'] = cleanup
        persist()
    print(json.dumps({key: proof.get(key) for key in ('status', 'diagnostic', 'completed_tool_calls', 'duplicate_start_reconciles_same_receipt', 'cleanup')}))


asyncio.run(owned_run())
raise SystemExit(0 if proof['status'] == 'passed' else 2)
