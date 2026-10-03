from pathlib import Path
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

repo = Path('D:/repos/wright')
private = repo / '.local-run/process-interfaces-083/t048-migration-audit-002'
assert not private.exists(), 'Inspect the original attempt before using a fresh continuation'
private.mkdir()
modules = [
    'tests/test_process_prototype_migration.py',
    'apps/api/tests/test_process_prototype_retirement.py',
    'packages/workspace_service/tests/test_process_legacy_results.py',
    'packages/workspace_service/tests/test_workflow_run_history.py',
    'packages/workspace_service/tests/test_workflow_run_paths.py',
    'tests/packaging/test_process_prototype_distribution_boundary.py',
    'tests/test_embedded_slice_retirement.py',
    'tests/test_embedded_mesh_retirement.py',
    'tests/test_engineering_external_slice_binding.py',
    'tests/test_external_mesh_binding.py',
    'tests/test_independent_slice_diagnostic.py',
    'tests/test_drill_jig_source_paths.py',
    'tests/test_printed_dataset_bindings.py',
]
command = [sys.executable, '-m', 'pytest', '-q', *modules,
           '--basetemp=' + str(private / 'pytest'),
           '--junitxml=' + str(private / 'regression.xml')]
(private / 'command.json').write_text(json.dumps(command, indent=2)+'\n', encoding='utf-8')
with (private / 'regression-output.txt').open('w', encoding='utf-8') as log:
    result = subprocess.run(command, cwd=repo, stdout=log, stderr=subprocess.STDOUT)
root = ET.parse(private / 'regression.xml').getroot()
cases = list(root.iter('testcase'))
counts = {'tests': len(cases), 'failures': len(list(root.iter('failure'))),
          'errors': len(list(root.iter('error'))), 'skipped': len(list(root.iter('skipped')))}
counts['passed'] = counts['tests']-counts['failures']-counts['errors']-counts['skipped']
report = {'exit_code': result.returncode, 'modules': modules, 'counts': counts,
          'fresh_provider_or_model_execution': False, 'physical_effects': False}
(private / 'result.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report))
if result.returncode:
    print((private / 'regression-output.txt').read_text(encoding='utf-8')[-4500:])
raise SystemExit(result.returncode)
