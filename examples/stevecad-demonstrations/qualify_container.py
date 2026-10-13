"""Opt-in remote MCP qualification in a fresh neutral Wright container.

No CAD host is installed. The operator mounts source read-only, a private OAuth
store read-only, and a fresh evidence directory. Credentials are copied only to
the container's ephemeral /tmp directory for the existing refresh mechanism.
This qualifies registry/transport/gateway operations, not a process UI or solver.
"""
from __future__ import annotations

import asyncio
import base64
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path('/source')
for package in (ROOT / 'packages').iterdir():
    if (package / 'src').is_dir():
        sys.path.insert(0, str(package / 'src'))

from core.redaction import redact_mapping
from data_vault import install_default_secret_provider, upgrade_database
from tool_registry.canonical_catalog import load_catalog_document
from tool_registry.catalog_models import CatalogEntry
from tool_registry.catalog_loader import catalog_entry_to_mcp_seed
from tool_registry.gateway_adapters import DatabaseGatewayCatalog, EngineGatewayLifecycle
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
from tool_registry.manager import McpEngine
from tool_registry.models import McpServerCreate
from tool_registry.safety import ApprovalContext
from tool_registry.services import register_server, install_server
from tool_registry.db import get_tools

OUT = Path('/evidence')
STATE = Path('/tmp/stevecad-qualification')
DOCUMENT = '875dbd4e-aec5-4c07-8eae-cf34e1161557'


def record(name, value):
    (OUT / name).write_text(json.dumps(redact_mapping(value), indent=2) + '\n')


async def main():
    STATE.mkdir(exist_ok=False)
    shutil.copyfile('/run/stevecad-credentials.json', STATE / 'credentials.json')
    os.chmod(STATE / 'credentials.json', 0o600)
    os.environ['WRIGHT_SECRETS_PATH'] = str(STATE / 'credentials.json')
    os.environ.pop('WRIGHT_TESTING', None)
    install_default_secret_provider()
    database = str(STATE / 'wright.db')
    upgrade_database(database)
    entry = CatalogEntry.model_validate(next(x for x in load_catalog_document()['servers'] if x['id'] == 'stevecad-mcp'))
    register_server(database, McpServerCreate.model_validate(catalog_entry_to_mcp_seed(entry)), server_id=entry.id)
    spec = importlib.util.spec_from_file_location('qualification_ports', ROOT / 'scripts/qualify_stdio_mcp.py')
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    audit = h._Audit()
    engine = McpEngine(database, operation_timeout=120)
    approvals = {'network_access_approval', 'cloud_data_approval'}
    context = ApprovalContext(machine_approvals=approvals, workspace_approvals=approvals, workspace_id='clean-stevecad', session_id='clean-stevecad')
    gateway = GatewayService(workspaces=h._Workspaces(STATE, entry.id), catalog=DatabaseGatewayCatalog(database), lifecycle=EngineGatewayLifecycle(engine), audit=audit, notifier=GatewayNotificationHub(), operation_timeout=120)
    try:
        await install_server(engine, entry.id, session_id='clean-stevecad', is_server_enabled_for_session=lambda _: True, approval_context=context)
        runner = engine.lifecycle.runner_for(entry.id)
        record('initialize.json', runner._probe_response)
        tools = get_tools(database, entry.id)
        record('tools.json', {'tools':[t.model_dump(mode='json') for t in tools]})
        direct = await engine.call_tool(entry.id, 'read_design', {'document_id':DOCUMENT}, approval_context=context)
        record('direct-read-design.json', direct)
        assert not direct.get('isError'), 'Direct backend read failed'
        gateway.open_session(session_id='clean-stevecad', principal_id='wright-validator', workspace_id='clean-stevecad', transport='stdio')
        gateway.initialize_session('clean-stevecad', protocol_version=SUPPORTED_PROTOCOL_VERSION, client_name='stevecad-clean-qualification', client_version='1', client_capabilities={})
        names = [t.name for t in gateway.list_tools('clean-stevecad')]
        record('gateway-tools.json', {'tools':names})
        result = await gateway.call_tool('clean-stevecad', 'inspect-coupon', 'stevecad-mcp__inspect_model', {'document_id':DOCUMENT, 'view':'isometric'}, workspace_approvals=approvals)
        content = []
        for i, item in enumerate(result.content):
            item = dict(item)
            if item.get('type') == 'image':
                data = base64.b64decode(item.pop('data'))
                name = f'coupon-inspection-{i}.png'
                (OUT / name).write_bytes(data)
                item.update(path=name, size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            content.append(item)
        record('gateway-inspection.json', {'content':content, 'structuredContent':result.structured_content,'isError':result.is_error})
        assert not result.is_error, 'Actual gateway inspection failed'
        record('summary.json', {'status':'passed','observed_at':datetime.now(timezone.utc).isoformat(),'platform':'Linux amd64 fresh neutral Wright container','source_overlay':'current checkout read-only; core/data-vault/tool-registry','installed_selected_host_software':[], 'tool_count':len(tools),'gateway_tool_count':len(names),'backend_probe':'read_design exact native coupon revision','gateway_probe':'inspect_model exact coupon and actual image','workspace_port':'existing qualification fixture; real registry, lifecycle, policy, audit and remote backend','audit':audit.events,'not_proved':['container workspace UI','CAD creation on Linux','structural or thermal validity','full installed distribution qualification']})
        print('Clean container passed: '+str(len(tools))+' tools, direct CAD read, gateway CAD image.', flush=True)
    except Exception as error:
        record('failure.json', {'status':'failed','error_type':type(error).__name__,'message':str(error)})
        raise
    finally:
        await engine.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
