"""Once-only isolated Linux verification of current shared file authority tests."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import traceback
import xml.etree.ElementTree as ET

repo = Path('D:/repos/wright')
base = repo / '.local-run/process-interfaces-083'
root = base / 't053-linux-symlink-security-002'
root.mkdir(exist_ok=False)
snapshot = root / 'source'
snapshot.mkdir()
image = json.loads((base / 't053-linux-symlink-preflight-001/preflight.json').read_bytes())['base_image']
label = 'symlink-security-002'
owned = []
proof = {'status': 'preparing', 'base_image': image, 'physical_dispatch': False,
         'provider_execution': False, 'scope': 'Four current-source shared authority test modules on selected isolated Linux test environment'}

def run(args, timeout=60, name=None):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if name:
        (root / (name + '.log')).write_text(result.stdout + '\n' + result.stderr, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'{name or args[0]} exit {result.returncode}: ' + result.stderr[-1800:])
    return result.stdout.strip()

def docker(*args, **kw):
    return run(['docker', *args], **kw)

def create(kind, source_image, network, mount=False):
    args = ['run', '--detach', '--platform', 'linux/amd64', '--name', 'wright-083-' + label + '-' + kind,
            '--label', 'wright.feature=083-process-working-interfaces', '--label', 'wright.proof=' + label,
            '--network', network]
    if mount:
        args += ['--mount', f'type=bind,source={snapshot},target=/proof/src,readonly']
    args += ['--entrypoint', 'sleep', source_image, 'infinity']
    identity = docker(*args)
    owned.append(identity)
    state = json.loads(docker('inspect', identity))[0]
    assert state['Id'] == identity and state['State']['Running']
    assert state['Config']['Labels']['wright.proof'] == label
    assert state['HostConfig']['NetworkMode'] == network
    assert len(state['Mounts']) == int(mount)
    if mount:
        assert state['Mounts'][0]['Destination'] == '/proof/src' and not state['Mounts'][0]['RW']
    return identity

try:
    packages = ['core', 'data_vault', 'tool_registry', 'workspace_service', 'agent_adapters', 'model_registry']
    source_roots = [repo / 'packages' / name / 'src' for name in packages]
    source_roots.append(repo / 'packages/workspace_service/tests')
    inventory = []
    for source_root in source_roots:
        for source in sorted(source_root.rglob('*')):
            if not source.is_file() or source.is_symlink():
                continue
            relative = source.relative_to(repo)
            if any(part in {'__pycache__', '.pytest_cache', '.ruff_cache', 'node_modules', '.git', '.env'} for part in relative.parts):
                continue
            if source.name.startswith('.env') or source.suffix in {'.pyc', '.pyo'}:
                continue
            data = source.read_bytes()
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            assert target.read_bytes() == data
            inventory.append({'path': relative.as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    (root / 'source-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
    proof['source_files'] = len(inventory)
    print('Exact current source snapshot staged', len(inventory), flush=True)
    installer = create('install', image, 'bridge')
    metadata = "import importlib.util,json,shutil; print(json.dumps({'pip':importlib.util.find_spec('pip') is not None,'uv':shutil.which('uv')}))"
    metadata = json.loads(docker('exec', installer, 'python3', '-c', metadata))
    proof['installer_runtime'] = metadata
    if metadata['pip']:
        install = ['python3', '-m', 'pip', 'install', '--disable-pip-version-check', '--target', '/selected/test-deps', 'pytest==9.0.3', 'pytest-asyncio==1.4.0']
    else:
        assert metadata['uv'], 'No selected test package installer available'
        install = [metadata['uv'], 'pip', 'install', '--python', 'python3', '--target', '/selected/test-deps', 'pytest==9.0.3', 'pytest-asyncio==1.4.0']
    (root / 'installation-command.json').write_text(json.dumps(install, indent=2) + '\n', encoding='utf-8')
    docker('exec', installer, *install, timeout=300, name='installation')
    docker('stop', '--time', '10', installer)
    selected = docker('commit', installer)
    proof['selected_test_image'] = selected
    runtime = create('runtime', selected, 'none', mount=True)
    pythonpath = ':'.join(['/selected/test-deps', '/proof/src'] + ['/proof/src/packages/' + name + '/src' for name in packages])
    env = ['-e', 'PYTHONPATH=' + pythonpath, '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'WRIGHT_RIVET_LIVE_AI=0', '-e', 'WRIGHT_RIVET_LIVE_BREP=0', '-e', 'WRIGHT_RIVET_LIVE_HOST=0']
    metadata = "import json,sys,importlib.metadata as m; import core,data_vault,tool_registry,workspace_service;print(json.dumps({'python':sys.version,'pytest':m.version('pytest'),'pytest_asyncio':m.version('pytest-asyncio'),'modules':{x.__name__:x.__file__ for x in [core,data_vault,tool_registry,workspace_service]},'resolved_packages':sorted([{'name':d.metadata['Name'],'version':d.version} for d in m.distributions()],key=lambda d:d['name'].lower())}))"
    proof['runtime'] = json.loads(docker('exec', *env, runtime, 'python3', '-c', metadata, name='runtime-imports'))
    assert all(value.startswith('/proof/src/packages/') for value in proof['runtime']['modules'].values())
    modules = ['test_workflow_integration_document_write.py', 'test_workflow_integration_file_read.py', 'test_workflow_integration_file_copy.py', 'test_process_preparation_service.py']
    command = ['python3', '-m', 'pytest', '-c', '/dev/null', '--rootdir=/proof/src', '-p', 'no:cacheprovider', '--basetemp=/tmp/authority-proof', '--junitxml=/tmp/authority-results.xml', '-q'] + ['/proof/src/packages/workspace_service/tests/' + name for name in modules]
    (root / 'test-command.json').write_text(json.dumps(command, indent=2) + '\n', encoding='utf-8')
    print('Selected test dependencies installed; running offline Linux checks', flush=True)
    test = subprocess.run(['docker', 'exec', *env, runtime, *command], capture_output=True, text=True, timeout=240)
    (root / 'test-output.log').write_text(test.stdout + '\n' + test.stderr, encoding='utf-8')
    proof['test_exit_code'] = test.returncode
    docker('cp', runtime + ':/tmp/authority-results.xml', str(root / 'results.xml'))
    xml = ET.parse(root / 'results.xml').getroot()
    cases = list(xml.iter('testcase'))
    required = ['test_declared_path_cannot_follow_symlink_outside_attempt', 'test_symlink_outside_attempt_rejected', 'test_existing_symlink_source_is_rejected']
    proof['required_security_cases'] = []
    for name in required:
        matches = [case for case in cases if case.attrib['name'] == name]
        assert len(matches) == 1 and len(matches[0]) == 0, (name, [ET.tostring(case).decode() for case in matches])
        proof['required_security_cases'].append({'name': name, 'passed': True, 'skipped': False})
    assert test.returncode == 0
    assert not list(xml.iter('skipped')) and not list(xml.iter('failure')) and not list(xml.iter('error'))
    proof['passed_tests'] = len(cases)
    assert docker('image', 'inspect', '--format', '{{.Id}}', image) == image
    for item in inventory:
        assert hashlib.sha256((snapshot / item['path']).read_bytes()).hexdigest() == item['sha256']
        assert hashlib.sha256((repo / item['path']).read_bytes()).hexdigest() == item['sha256']
    proof['source_parity_after_tests'] = True
    proof['status'] = 'passed'
except BaseException:
    proof['status'] = 'failed'
    proof['error'] = traceback.format_exc()
    raise
finally:
    proof['owned_containers'] = []
    for identity in reversed(owned):
        state = json.loads(docker('inspect', identity))[0]
        assert state['Id'] == identity and state['Config']['Labels']['wright.proof'] == label
        if state['State']['Running']:
            docker('stop', '--time', '10', identity)
        state = json.loads(docker('inspect', identity))[0]
        assert not state['State']['Running']
        proof['owned_containers'].append({'id': identity, 'running': False})
    (root / 'outcome.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': proof['status'], 'passed_tests': proof.get('passed_tests'), 'root': str(root), 'owned_containers': proof['owned_containers']}), flush=True)
