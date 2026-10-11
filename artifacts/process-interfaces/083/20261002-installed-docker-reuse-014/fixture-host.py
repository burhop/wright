from pathlib import Path
import asyncio
import json
import os
import socket
import sys

private = Path('/proof-input')
context = json.loads((private / 'browser-context.json').read_bytes())
private = Path('/tmp/wright-proof/state')
private.mkdir(parents=True, exist_ok=True)
with socket.socket() as probe:
    probe.bind(('127.0.0.1', 8033))
from wright_engineering.runtime.layout import NativeLayout
from wright_engineering.runtime.server import prepare_runtime_environment
layout = NativeLayout.from_wright_home(Path(context['workspace_root']).parent.parent.parent)
prepare_runtime_environment(layout, port=8033)
os.environ.update({
    'WRIGHT_SECRETS_PATH': '/tmp/wright-proof/state/credentials.json',
    'DATABASE_PATH': context['database_path'], 'WRIGHT_API_TOKEN': context['api_token'],
    'WRIGHT_AUTH_MODE': 'enforced', 'WRIGHT_NATIVE_RUNTIME': '1',
    'WRIGHT_BIND_HOST': '0.0.0.0', 'WRIGHT_ALLOWED_ORIGINS': context['frontend_url'],
    'WRIGHT_API_MCP_AUTOSTART': '0', 'WRIGHT_PRINT_DEMO_PRINTER_ENABLED': '0',
    'WRIGHT_SURFACES_ENABLED': '1', 'WRIGHT_SURFACES_DISPLAY_ENABLED': '1',
    'WRIGHT_SURFACES_LIVE_APPS_ENABLED': '1', 'WRIGHT_SURFACE_PREVIEW_PORT': '8033',
})
for name in ('PYTHONPATH', 'WRIGHT_PROCESS_UI_TOOLCHAIN_ROOT'):
    os.environ.pop(name, None)
assert Path(sys.executable).is_relative_to(Path('/tmp/wright-proof-env'))
import uvicorn
import api.main
import core
import data_vault
import agent_adapters
import workspace_service
import tool_registry
import wright_engineering
from workspace_service.process_interfaces import toolchain

installed = Path(context['installed_root'])
modules = (api.main, core, data_vault, agent_adapters, workspace_service, tool_registry, wright_engineering)
assert all(Path(module.__file__).is_relative_to(installed) for module in modules)
assert isinstance(toolchain.discover_build_toolchain(), toolchain.UnavailableBuildToolchain)
assert Path(api.main.dist_dir).is_relative_to(installed)
record = {'installed_owning_modules': [module.__name__ for module in modules],
    'frontend_from_installed_wheel': True, 'compiler_available': False,
    'provider_autostart': False, 'original_worktree_imports': False}
(private / 'host-identity.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')

async def main():
    server = uvicorn.Server(uvicorn.Config(api.main.app, host='0.0.0.0', port=8033,
        access_log=False, log_level='warning'))
    async def stop():
        while True:
            await asyncio.sleep(.5)
            if (private / 'stop-request').exists():
                server.should_exit = True
                return
    watcher = asyncio.create_task(stop())
    try:
        await server.serve()
    finally:
        watcher.cancel()
        await asyncio.gather(watcher, return_exceptions=True)
        (private / 'host-terminal.json').write_text(json.dumps({'stopped': True}) + '\n')

asyncio.run(main())
