"""Read-only current migration audit. Do not run providers or change histories."""
import ast
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess
import zipfile

repo = Path('D:/repos/wright')
local = repo / '.local-run/process-interfaces-083'
private = local / 't048-migration-audit-002'
out = private / 'state-audit.json'
assert private.is_dir() and not out.exists()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=repo)

guard = runpy.run_path(str(repo / 'tests/test_process_prototype_migration.py'))
retired = list(guard['RETIRED'])
assert all(not (repo / name).exists() for name in retired)
report = {'source_commit': git('rev-parse', 'HEAD').decode().strip(),
          'retired_paths': retired, 'read_only': True,
          'fresh_model_or_provider_calls': 0, 'physical_effects': False}

# Check actual imports, and report current operational-name references separately.
symbols = sorted({Path(name).stem for name in retired if not name.startswith('tests/')})
pattern = re.compile('|'.join(re.escape(name) for name in symbols))
files = []
references = []
python_count = 0
source_folders = ['apps/api/src', 'apps/web/src', 'scripts'] + [p.relative_to(repo).as_posix() for p in (repo / 'packages').glob('*/src')]
for folder in source_folders:
    for path in (repo / folder).rglob('*'):
        if not path.is_file() or path.suffix not in {'.py', '.ts', '.tsx', '.ps1', '.json', '.yaml', '.yml', '.toml'}:
            continue
        if {'node_modules', '__pycache__', 'static', 'tests'}.intersection(path.parts) or '.spec.' in path.name:
            continue
        relative = path.relative_to(repo).as_posix()
        source = path.read_text(encoding='utf-8')
        files.append(relative)
        if path.suffix == '.py':
            tree = ast.parse(source, filename=relative)
            for node in ast.walk(tree):
                names = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                         else [node.module or '', *[alias.name for alias in node.names]] if isinstance(node, ast.ImportFrom)
                         else [])
                assert all(not guard['RETIRED_MODULES'].intersection(name.split('.')) for name in names), relative
            python_count += 1
        for line_number, line in enumerate(source.splitlines(), 1):
            if pattern.search(line):
                references.append({'path': relative, 'line': line_number, 'text': line.strip()})
assert len(references) == 1 and references[0]['path'] == 'scripts/probe_printed_blender_binding.py'
assert 'if any(' in references[0]['text'] and 'for item in command' in references[0]['text']
report['active_source_scan'] = {'files': len(files), 'python_import_graph_files': python_count,
                              'remaining_references': references,
                              'remaining_reference_disposition': 'explicit rejection of a retired embedded command, not a caller'}

# Original edited prototype bytes stay private, unchanged and inactive.
archives = []
for name in ['t048-retirement-preserved-001', 't048-retirement-preserved-002']:
    root = local / name
    rows = json.loads((root / 'manifest.json').read_bytes())['files']
    for row in rows:
        path = root / 'files' / row['path']
        assert digest(path) == row['sha256'] and path.stat().st_size == row['bytes']
    archives.append({'root': name, 'files': len(rows), 'manifest_sha256': digest(root / 'manifest.json')})

artifacts = repo / 'artifacts/process-interfaces/083'
slice_root = artifacts / '20261003-external-slice-probe-retirement'
slice_scope = json.loads((slice_root / 'checked-scope.json').read_bytes())
for row in slice_scope['original_archives'].values():
    path = slice_root / row['retained_file']
    assert digest(path) == row['sha256'] and path.stat().st_size == row['bytes']
archives.append({'root': slice_root.name, 'files': len(slice_scope['original_archives']),
                 'scope_sha256': digest(slice_root / 'checked-scope.json')})
mesh_root = artifacts / '20261003-mesh-repair-retirement'
mesh_retained = json.loads((mesh_root / 'retained-originals.json').read_bytes())
for name, row in mesh_retained['files'].items():
    path = mesh_root / ('archive-' + Path(name).name + '.txt')
    assert digest(path) == row['sha256'] and path.stat().st_size == row['bytes']
archives.append({'root': mesh_root.name, 'files': len(mesh_retained['files']),
                 'manifest_sha256': digest(mesh_root / 'retained-originals.json')})
report['original_archives'] = archives

# Reconcile the retained installed-history proof with current owning source.
history_root = artifacts / '20261003-original-history-verified'
history_scope = json.loads((history_root / 'checked-scope.json').read_bytes())
unchanged = {}
for name, expected in history_scope['source_hashes'].items():
    unchanged[name] = digest(repo / name)
    assert unchanged[name] == expected
report['installed_history_owner_sources_unchanged'] = unchanged

# Every retained evidence inventory is checked, including the supplemental mesh scope.
inventories = []
for root in [slice_root, mesh_root, history_root,
             artifacts / '20261003-configured-preparation-and-saved-reuse-verified',
             artifacts / '20261003-heat-repeat-and-saved-ui-verified']:
    for name in ['inventory.json', 'supplemental-inventory.json']:
        path = root / name
        if not path.exists():
            continue
        rows = json.loads(path.read_bytes())['files']
        for relative, expected in rows.items():
            item = repo / relative if relative.startswith('artifacts/') else root / relative
            assert digest(item) == expected['sha256'] and item.stat().st_size == expected['bytes'], relative
        inventories.append({'path': path.relative_to(repo).as_posix(), 'files': len(rows), 'sha256': digest(path)})
report['retained_evidence_inventories'] = inventories

# Current installed wheel excludes retired code and includes exact history owners.
build_root = local / 't052-current-installed-005'
record = json.loads((build_root / 'build-record.json').read_bytes())
wheel = build_root / 'dist' / record['wheel']
assert digest(wheel) == record['wheel_sha256']
wheel_sources = {}
with zipfile.ZipFile(wheel) as archive:
    names = archive.namelist()
    assert not any(any(symbol in name for symbol in symbols) for name in names)
    for relative in [
        'packages/workspace_service/src/workspace_service/process_interfaces/legacy_results.py',
        'packages/workspace_service/src/workspace_service/workflow_run_record.py',
        'apps/api/src/api/main.py', 'apps/api/src/api/routers/workspace.py',
        'apps/api/src/api/routers/process_interfaces.py', 'apps/api/src/api/schemas/workspace.py',
    ]:
        zipped = relative.split('/src/', 1)[1]
        assert archive.read(zipped) == (repo / relative).read_bytes(), relative
        wheel_sources[relative] = digest(repo / relative)
report['installed005_package'] = {'wheel_sha256': digest(wheel),
                                 'retired_names_absent': True, 'exact_current_owners': wheel_sources,
                                 'fresh_installed_browser_execution': False}

protected = json.loads((mesh_root / 'checked-scope.json').read_bytes())['protected_file_hashes']
for name, expected in protected.items():
    assert digest(repo / name) == expected, name
for name in ['AGENTS.md', '.specify/feature.json']:
    assert (repo / name).read_bytes().replace(b'\r\n', b'\n') == git('show', 'HEAD:' + name).replace(b'\r\n', b'\n')
report['protected_file_hashes'] = protected
report['context_matches_head'] = True
report['source_sha256'] = {name: digest(repo / name) for name in [
    *wheel_sources,
    'apps/web/src/components/pages/WorkflowRecoveryPage.tsx',
    'apps/web/src/components/chat/WorkspacePanel.tsx',
    'apps/web/src/services/workspace-service.ts',
    'apps/web/src/components/process-interfaces/HistoricalResultView.tsx',
    'scripts/engineering_external_slice_binding.py',
    'scripts/engineering_external_mesh_binding.py',
    'scripts/prepare-printed-dataset-campaign.py',
    'scripts/prepare-drill-jig-dataset-campaign.py',
    'scripts/probe_printed_blender_binding.py',
    'tests/test_process_prototype_migration.py']}
out.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'status': 'passed', 'retired_paths': len(retired), 'scan': report['active_source_scan'],
                  'archives': sum(row['files'] for row in archives), 'inventories': inventories,
                  'installed_history_sources_unchanged': len(unchanged), 'current_wheel_owners': len(wheel_sources)}))
