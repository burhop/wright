import ast
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess

repo = Path('D:/repos/wright')
base = repo / '.local-run/process-interfaces-083'
out = base / 't049-coupling-audit-002.json'
assert not out.exists()
original_head = '679447bb3ad62b670b49b27a278ff14406647809'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=repo)

guard = runpy.run_path(str(repo / 'tests/test_process_platform_generality.py'))
core_paths = guard['shared_python_paths']()
core_report = []
for path in core_paths:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    assert not any(isinstance(node, ast.Constant) and isinstance(node.value, str)
                   and guard['PROVIDER_WORDS'].search(node.value) for node in ast.walk(tree)), path
    for node in ast.walk(tree):
        names = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                 else [node.module or '', *[alias.name for alias in node.names]] if isinstance(node, ast.ImportFrom)
                 else [])
        assert all(not guard['PROVIDER_IMPORTS'].intersection(name.split('.')) for name in names), path
    core_report.append({'path': path.relative_to(repo).as_posix(), 'sha256': digest(path)})

frontend = []
for folder in ['packages/process_client/src', 'packages/ui_kit/src', 'apps/web/src/components/process-interfaces']:
    for path in (repo / folder).rglob('*'):
        if path.suffix in {'.ts', '.tsx'} and '.spec.' not in path.name:
            assert not guard['PROVIDER_WORDS'].search(path.read_text(encoding='utf-8'))
            frontend.append({'path': path.relative_to(repo).as_posix(), 'sha256':digest(path)})

# Survey all tracked shared Python owners, then inspect each residual explicitly.
survey_pattern = re.compile(r'\b(?:bambu|p1s|mqtt|ftps|agentcad|oasis|blender|blender_mcp|bpy|bmesh)\b', re.I)
survey = []
residuals = []
for raw in git('ls-files', '-z', '--', 'packages', 'apps/api/src').split(b'\0'):
    if not raw:
        continue
    name = raw.decode()
    if '/src/' not in name or not name.endswith('.py') or '/static/' in name:
        continue
    path = repo / name
    tree = ast.parse(path.read_text(encoding='utf-8'))
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            matches = sorted(set(match.group(0).lower() for match in survey_pattern.finditer(node.value)))
            if matches:
                findings.append({'line':node.lineno, 'selected_provider_words':matches,
                                 'literal_sha256':hashlib.sha256(node.value.encode()).hexdigest()})
    survey.append(name)
    if findings:
        original = git('show', original_head + ':' + name)
        unchanged = original.replace(b'\r\n', b'\n') == path.read_bytes().replace(b'\r\n', b'\n')
        residuals.append({'path':name, 'findings':findings, 'sha256':digest(path),
                          'matches_pre083_source_normalized':unchanged,
                          'pre083_source_commit':original_head})

profiles = []
for prefix in ['printed-replacement-part', 'parametric-drill-jig']:
    for index in range(1,4):
        name = f'packages/workspace_service/src/workspace_service/process_validation/profiles/{prefix}-{index:02}.json'
        path = repo / name
        original = git('show', original_head + ':' + name)
        assert original.replace(b'\r\n', b'\n') == path.read_bytes().replace(b'\r\n', b'\n'), name
        value = json.loads(path.read_bytes())
        checks = [{'id':check['id'], 'expected_operation':check['parameters']['expected_operation']}
                  for check in value['checks'] if check.get('parameters',{}).get('operation') == 'slice_binding']
        assert all(isinstance(check['expected_operation'],str) and check['expected_operation'].strip() for check in checks)
        profiles.append({'path':name, 'sha256':digest(path), 'full_profile_matches_pre083_source_normalized':True,
                         'slice_binding_checks':checks})

retirement = repo / 'artifacts/process-interfaces/083/20261003-migration-disposition-verified'
retained = json.loads((retirement / '002-state-audit.json').read_bytes())
protected = retained['protected_file_hashes']
for name, expected in protected.items():
    assert digest(repo / name) == expected, name
for name in ['AGENTS.md','.specify/feature.json']:
    assert (repo / name).read_bytes().replace(b'\r\n',b'\n') == git('show','HEAD:'+name).replace(b'\r\n',b'\n')
proofs = []
for name in ['20261003-configured-preparation-and-saved-reuse-verified', '20261003-heat-repeat-and-saved-ui-verified']:
    root = repo / 'artifacts/process-interfaces/083' / name
    rows = json.loads((root / 'inventory.json').read_bytes())['files']
    for relative, item in rows.items():
        path = root / relative
        assert digest(path) == item['sha256'] and path.stat().st_size == item['bytes']
    proofs.append({'root':name, 'files':len(rows),'inventory_sha256':digest(root/'inventory.json')})

from workspace_service.process_validation.readers.printing import PrintingArtifactReader
report = {'source_commit':git('rev-parse','HEAD').decode().strip(), 'scope':'T049 current shared-code/provider survey and retained two-process comparison',
          'feature_shared_python':core_report, 'public_client_kit_views':frontend,
          'selected_provider_survey':{'tracked_python_files':len(survey),'residuals':residuals},
          'original_six_profiles':profiles, 'new_reader_identity':PrintingArtifactReader.identity.model_dump(mode='json'),
          'protected_file_hashes':protected, 'retained_actual_engineering_ui_proofs':proofs,
          'fresh_provider_model_process_execution':False, 'review_responses':0, 'physical_effects':False}
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'read_only_survey_recorded','shared_python':len(core_report),'public_client_kit_views':len(frontend),
                  'survey_files':len(survey),'residuals':[{'path':item['path'],'matches_pre083':item['matches_pre083_source_normalized']} for item in residuals],
                  'frozen_profiles':len(profiles),'declared_slice_checks':sum(len(item['slice_binding_checks']) for item in profiles),
                  'retained_proof_files':sum(item['files'] for item in proofs)}))
