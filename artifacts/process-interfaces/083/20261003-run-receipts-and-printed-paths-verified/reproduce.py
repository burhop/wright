from pathlib import Path
import json
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

repo = Path('D:/repos/wright')
suffix = sys.argv[1] if len(sys.argv) > 1 else '011'
assert suffix.isalnum(), 'Use a fresh alphanumeric proof suffix'
root = repo / ('.local-run/process-interfaces-083/t047-receipt-regression-' + suffix)
root.mkdir(exist_ok=False)
python = repo / '.venv/Scripts/python.exe'
test_names = [
    'test_workflow_source_execution', 'test_workflow_run_receipts',
    'test_workflow_run_paths', 'test_workflow_mcp_operations',
    'test_workflow_integration_policy', 'test_workflow_external_action_execution',
    'test_workflow_execution_continuation', 'test_workflow_artifact_review',
    'test_workflow_approval_review_settings', 'test_workflow_approval_resume',
    'test_workflow_approval_execution',
]
tests = ['packages/workspace_service/tests/' + name + '.py' for name in test_names]
tests += ['tests/test_process_interface_examples.py', 'tests/test_process_interface_operator_example.py']
cmd = [str(python), '-m', 'pytest', *tests, '-q', '--tb=short', '-p', 'no:cacheprovider',
       '--basetemp=' + str(root / 'pytest-temp'), '--junitxml=' + str(root / 'pytest.xml')]
started = time.monotonic()
result = subprocess.run(cmd, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(root / 'pytest.log').write_bytes(result.stdout)
suites = ET.parse(root / 'pytest.xml').getroot()
counts = {key: sum(int(s.get(key, 0)) for s in suites.iter('testsuite'))
          for key in ('tests', 'failures', 'errors', 'skipped')}
record = {'command': cmd, 'exit_code': result.returncode, 'elapsed_seconds': time.monotonic()-started,
          'counts': counts, 'scope': 'Controlled shared receipt/continuation and printed preparation; no native provider or browser proof.'}
(root / 'result.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
raise SystemExit(result.returncode)
