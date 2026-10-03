from pathlib import Path
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

repo = Path('D:/repos/wright')
root = repo / '.local-run/process-interfaces-083/t049-generality-004'
assert not root.exists()
root.mkdir()
modules = [
    'tests/test_process_platform_generality.py',
    'tests/test_process_prototype_migration.py',
    'tests/external/process_validation/test_printing.py',
    'tests/external/process_validation/test_printed_profiles.py',
    'tests/external/process_validation/test_jig_profiles.py',
    'packages/workspace_service/tests/test_process_validation.py',
    'packages/workspace_service/tests/test_process_validation_subjects.py',
    'packages/workspace_service/tests/test_process_interface_service_boundaries.py',
    'packages/workspace_service/tests/test_process_interaction_projection.py',
    'packages/workspace_service/tests/test_process_interaction_owners.py',
    'packages/workspace_service/tests/test_process_input_readiness.py',
    'packages/workspace_service/tests/test_process_input_supervision.py',
    'packages/workspace_service/tests/test_process_operation_observations.py',
    'packages/workspace_service/tests/test_process_operation_cancel.py',
    'packages/workspace_service/tests/test_process_action_supervision.py',
    'packages/workspace_service/tests/test_process_interface_continuation.py',
    'packages/workspace_service/tests/test_process_ui_authoring.py',
    'packages/workspace_service/tests/test_process_ui_presentations.py',
    'packages/workspace_service/tests/test_workflow_external_action_execution.py',
    'packages/workspace_service/tests/test_workflow_async_operations.py',
    'packages/workspace_service/tests/test_workflow_mcp_source_contracts.py',
    'packages/workspace_service/tests/test_workflow_mcp_execution.py',
    'apps/api/tests/test_process_interface_actions.py',
    'apps/api/tests/test_process_interface_run_lifecycle.py',
]
assert all((repo / name).is_file() for name in modules)
command = [sys.executable, '-m', 'pytest', '-q', *modules,
           '-o', 'cache_dir=' + str(root / 'cache'), '--basetemp=' + str(root / 'pytest'),
           '--junitxml=' + str(root / 'regression.xml')]
(root / 'command.json').write_text(json.dumps(command, indent=2)+'\n', encoding='utf-8')
with (root / 'regression-output.txt').open('w', encoding='utf-8') as output:
    result = subprocess.run(command, cwd=repo, stdout=output, stderr=subprocess.STDOUT)
tree = ET.parse(root / 'regression.xml').getroot()
cases = list(tree.iter('testcase'))
counts = dict(tests=len(cases), failures=len(list(tree.iter('failure'))),
              errors=len(list(tree.iter('error'))), skipped=len(list(tree.iter('skipped'))))
counts['passed'] = counts['tests']-counts['failures']-counts['errors']-counts['skipped']
record = {'exit_code': result.returncode, 'modules': modules, 'counts': counts,
          'fresh_provider_model_execution': False, 'physical_effects':False}
(root / 'result.json').write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
print(json.dumps(record))
if result.returncode:
    print((root / 'regression-output.txt').read_text(encoding='utf-8')[-5500:])
raise SystemExit(result.returncode)
