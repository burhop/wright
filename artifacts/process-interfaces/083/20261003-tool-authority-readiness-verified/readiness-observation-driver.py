"""Readiness-only observation; clone database and never start or resume a run."""
from pathlib import Path
import asyncio
import hashlib
import json
import os
import sqlite3

repo = Path('D:/repos/wright')
base = repo / '.local-run/process-interfaces-083'
root = base / 't048-authority-readiness-observation-001'
root.mkdir(exist_ok=False)
basis = base / 't048-external-slice-runtime-007'
proof = json.loads((basis / 'qualification.json').read_bytes())
assert proof['status'] == 'passed'
db = root / 'state.db'
with sqlite3.connect((basis / 'state.db').resolve().as_uri() + '?mode=ro', uri=True) as source:
    with sqlite3.connect(db) as target:
        source.backup(target)
os.environ['DATABASE_PATH'] = str(db)
os.environ['WRIGHT_WORKFLOW_INTEGRATION_TESTS'] = '1'

from api.composition import workspace_service, build_api_gateway_service
from api.config import McpTransportSettings
from core.process_interactions import ProcessRef
from core.redaction import redact_validation_payload
from tool_registry import McpEngine
from workspace_service.process_interfaces.service import ProcessScope

workspace = Path(proof['workspace'])
before = {p.relative_to(workspace).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in workspace.rglob('*') if p.is_file() and '.git' not in p.parts}

def calls():
    with sqlite3.connect(db) as connection:
        return connection.execute("SELECT COUNT(*) FROM gateway_audit_events WHERE operation='tool.call'").fetchone()[0]

async def main():
    service = workspace_service()
    engine = McpEngine(str(db))
    gateway = build_api_gateway_service(str(db), engine, McpTransportSettings.from_env())
    count = calls()
    try:
        process = ProcessRef.model_validate(proof['process'])
        scope = ProcessScope(principal_id='qualification-083-local', workspace_id=process.workspace_id,
                             capabilities=frozenset({'process.read', 'process.inputs', 'process.start'}))
        readiness = await service.process_interfaces.check_readiness(
            scope, process, proof['start_receipt']['input_snapshot_id'], gateway=gateway,
            session_id='session-083-external-slice-007')
        assert readiness.state == 'blocked'
        assert readiness.reasons[0].code == 'CAPABILITY_UNAVAILABLE'
        assert 'authorization' in readiness.reasons[0].message
        assert calls() == count
        result = {'status': 'passed', 'scope': 'Actual accepted source and actual production gateway metadata; normal readiness only on a shadow database; no run start/resume or native operation',
                  'readiness': readiness.model_dump(mode='json'), 'additional_tool_call_events': calls() - count,
                  'integration_authority_used': False, 'physical_dispatch': False,
                  'human_engineering_acceptance': False, 'basis_run_id': proof['start_receipt']['run_id']}
    finally:
        await service.close()
        await gateway.shutdown()
    after = {p.relative_to(workspace).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in workspace.rglob('*') if p.is_file() and '.git' not in p.parts}
    assert before == after
    result['all_basis_workspace_files_unchanged'] = len(before)
    result['owned_runtime_and_gateway_closed'] = True
    (root / 'observation.json').write_text(json.dumps(redact_validation_payload(result), indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'readiness': readiness.state, 'tool_calls': 0,
                      'unchanged_files': len(before)}))

asyncio.run(main())
