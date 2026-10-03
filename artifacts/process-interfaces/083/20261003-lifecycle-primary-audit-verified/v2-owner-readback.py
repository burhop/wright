from pathlib import Path
import hashlib
import json
import sqlite3

from data_vault.workflow_continuation_repository import WorkflowContinuationRepository
from workspace_service.workflow_external_actions import WorkflowExternalActionService

repo=Path('D:/repos/wright')
folder=repo/'.pytest-tmp/t056-lifecycle-regression-001'
directories=list(folder.glob('test_two_sequential_checkpoint*'))
assert len(directories)==1
path=directories[0]/'state.db'
assert path.is_file()
with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
    rows=db.execute('SELECT checkpoint_id,continuation_json FROM workflow_continuation_checkpoints ORDER BY checkpoint_id').fetchall()
assert len(rows)==2
owner=WorkflowExternalActionService(WorkflowContinuationRepository(str(path)))
records=[]
for identifier,raw in rows:
    original=json.loads(raw)
    assert original['schema_version']==2
    checkpoint=owner.lookup(identifier)
    assert checkpoint.continuation==original
    assert checkpoint.checkpoint_kind=='approval'
    records.append({'checkpoint_id':identifier,'run_id':checkpoint.run_id,'step_id':checkpoint.step_id,
        'schema_version':checkpoint.continuation['schema_version'],
        'checkpoint_kind':checkpoint.checkpoint_kind,
        'continuation_sha256':hashlib.sha256(raw.encode()).hexdigest(),
        'readback_matches':True})
with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
    after=db.execute('SELECT checkpoint_id,continuation_json FROM workflow_continuation_checkpoints ORDER BY checkpoint_id').fetchall()
assert after==rows and len({record['run_id'] for record in records})==1
report={'status':'passed','scope':'Fresh persisted v2 checkpoints from the controlled canonical two-review fixture; recreated current service owner readback.',
    'fixture':'packages/workspace_service/tests/test_workflow_execution_continuation.py::test_two_sequential_checkpoints_resume_same_run_and_execute_true_final_step',
    'state_path':path.relative_to(repo).as_posix(),'recorded_continuations_unchanged':True,
    'lookup_only_no_decision_dispatch_or_resume':True,'checkpoints':records,
    'source_sha256':{name:hashlib.sha256((repo/name).read_bytes()).hexdigest() for name in [
        'packages/workspace_service/src/workspace_service/workflow_external_actions.py',
        'packages/data_vault/src/data_vault/workflow_continuation_repository.py',
        'packages/workspace_service/tests/test_workflow_execution_continuation.py']}}
output=repo/'.local-run/process-interfaces-083/t056-v2-owner-readback-001.json'
assert not output.exists()
output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'passed','checkpoints':2,'schema_version':2,'recorded_continuations_unchanged':True}))
