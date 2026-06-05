# CI Failure Report
Generated automatically for local triage and AI code patching.

---

## 1. python-quality (Run #27022549039)
- **Branch**: `dev`
- **Commit SHA**: `1aee653959237e2937c8cae3492b705703316bc1`
- **Time**: 2026-06-05T15:01:01Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27022549039)

### Failed Log Output
```text
python-quality	Lint with Ruff	﻿2026-06-05T15:01:12.7055061Z ##[group]Run uv run ruff check apps/api/ packages/
python-quality	Lint with Ruff	2026-06-05T15:01:12.7055494Z [36;1muv run ruff check apps/api/ packages/[0m
python-quality	Lint with Ruff	2026-06-05T15:01:12.7082598Z shell: /usr/bin/bash -e {0}
python-quality	Lint with Ruff	2026-06-05T15:01:12.7082852Z env:
python-quality	Lint with Ruff	2026-06-05T15:01:12.7083104Z   UV_CACHE_DIR: /home/runner/work/_temp/setup-uv-cache
python-quality	Lint with Ruff	2026-06-05T15:01:12.7083508Z   pythonLocation: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Lint with Ruff	2026-06-05T15:01:12.7083956Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.13.13/x64/lib/pkgconfig
python-quality	Lint with Ruff	2026-06-05T15:01:12.7084381Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Lint with Ruff	2026-06-05T15:01:12.7084761Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Lint with Ruff	2026-06-05T15:01:12.7085138Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Lint with Ruff	2026-06-05T15:01:12.7085519Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.13.13/x64/lib
python-quality	Lint with Ruff	2026-06-05T15:01:12.7085844Z ##[endgroup]
python-quality	Lint with Ruff	2026-06-05T15:01:12.8074241Z F401 [*] `uuid` imported but unused
python-quality	Lint with Ruff	2026-06-05T15:01:12.8075168Z  --> apps/api/src/api/database/migrate.py:6:8
python-quality	Lint with Ruff	2026-06-05T15:01:12.8075975Z   |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8076488Z 4 | import json
python-quality	Lint with Ruff	2026-06-05T15:01:12.8076970Z 5 | import time
python-quality	Lint with Ruff	2026-06-05T15:01:12.8077514Z 6 | import uuid
python-quality	Lint with Ruff	2026-06-05T15:01:12.8078320Z   |        ^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8078781Z 7 |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8079335Z 8 | # Ensure api package is importable when run directly
python-quality	Lint with Ruff	2026-06-05T15:01:12.8080014Z   |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8080516Z help: Remove unused import: `uuid`
python-quality	Lint with Ruff	2026-06-05T15:01:12.8081093Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8081485Z F401 [*] `api.config.LLM_HEALTH_URL` imported but unused
python-quality	Lint with Ruff	2026-06-05T15:01:12.8082196Z   --> apps/api/src/api/main.py:10:47
python-quality	Lint with Ruff	2026-06-05T15:01:12.8082765Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8083369Z  9 | from agent_adapters import HermesAdapter
python-quality	Lint with Ruff	2026-06-05T15:01:12.8085155Z 10 | from api.config import HERMES_WEBUI_BASE_URL, LLM_HEALTH_URL, DATABASE_PATH, get_llm_health_url
python-quality	Lint with Ruff	2026-06-05T15:01:12.8095233Z    |                                               ^^^^^^^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8096357Z 11 | from api.routers.agent import router as agent_router
python-quality	Lint with Ruff	2026-06-05T15:01:12.8097191Z 12 | from api.routers.mcp import router as mcp_router
python-quality	Lint with Ruff	2026-06-05T15:01:12.8098875Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8108583Z help: Remove unused import: `api.config.LLM_HEALTH_URL`
python-quality	Lint with Ruff	2026-06-05T15:01:12.8109343Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8109774Z E402 Module level import not at top of file
python-quality	Lint with Ruff	2026-06-05T15:01:12.8110508Z   --> apps/api/src/api/main.py:60:1
python-quality	Lint with Ruff	2026-06-05T15:01:12.8111140Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8112242Z 59 | # ── Custom exception handlers for standardized ErrorResponse ──────────────
python-quality	Lint with Ruff	2026-06-05T15:01:12.8113397Z 60 | from fastapi.exceptions import RequestValidationError
python-quality	Lint with Ruff	2026-06-05T15:01:12.8114197Z    | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8114992Z 61 | from starlette.exceptions import HTTPException as StarletteHTTPException
python-quality	Lint with Ruff	2026-06-05T15:01:12.8115665Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8115839Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8116030Z E402 Module level import not at top of file
python-quality	Lint with Ruff	2026-06-05T15:01:12.8116528Z   --> apps/api/src/api/main.py:61:1
python-quality	Lint with Ruff	2026-06-05T15:01:12.8116957Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8118027Z 59 | # ── Custom exception handlers for standardized ErrorResponse ──────────────
python-quality	Lint with Ruff	2026-06-05T15:01:12.8119120Z 60 | from fastapi.exceptions import RequestValidationError
python-quality	Lint with Ruff	2026-06-05T15:01:12.8119906Z 61 | from starlette.exceptions import HTTPException as StarletteHTTPException
python-quality	Lint with Ruff	2026-06-05T15:01:12.8120632Z    | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8121103Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8121221Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8121334Z E402 Module level import not at top of file
python-quality	Lint with Ruff	2026-06-05T15:01:12.8121632Z    --> apps/api/src/api/main.py:106:1
python-quality	Lint with Ruff	2026-06-05T15:01:12.8121891Z     |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8122172Z 104 | # Instantiate and store the Hermes adapter engine in the app state
python-quality	Lint with Ruff	2026-06-05T15:01:12.8122627Z 105 | app.state.agent_engine = HermesAdapter(HERMES_WEBUI_BASE_URL)
python-quality	Lint with Ruff	2026-06-05T15:01:12.8123046Z 106 | from core import AgentSyncManager
python-quality	Lint with Ruff	2026-06-05T15:01:12.8123332Z     | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8123850Z 107 | app.state.agent_sync_manager = AgentSyncManager(DATABASE_PATH)
python-quality	Lint with Ruff	2026-06-05T15:01:12.8124195Z     |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8124300Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8124406Z E402 Module level import not at top of file
python-quality	Lint with Ruff	2026-06-05T15:01:12.8124698Z    --> apps/api/src/api/main.py:166:1
python-quality	Lint with Ruff	2026-06-05T15:01:12.8124947Z     |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8125253Z 165 | # Serve frontend static files in production if the dist directory exists
python-quality	Lint with Ruff	2026-06-05T15:01:12.8125686Z 166 | from fastapi.staticfiles import StaticFiles
python-quality	Lint with Ruff	2026-06-05T15:01:12.8125987Z     | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8126279Z 167 | from fastapi.responses import FileResponse
python-quality	Lint with Ruff	2026-06-05T15:01:12.8126567Z 168 | import os
python-quality	Lint with Ruff	2026-06-05T15:01:12.8126756Z     |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8126854Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8126967Z E402 Module level import not at top of file
python-quality	Lint with Ruff	2026-06-05T15:01:12.8127266Z    --> apps/api/src/api/main.py:167:1
python-quality	Lint with Ruff	2026-06-05T15:01:12.8127539Z     |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8128650Z 165 | # Serve frontend static files in production if the dist directory exists
python-quality	Lint with Ruff	2026-06-05T15:01:12.8129346Z 166 | from fastapi.staticfiles import StaticFiles
python-quality	Lint with Ruff	2026-06-05T15:01:12.8129703Z 167 | from fastapi.responses import FileResponse
python-quality	Lint with Ruff	2026-06-05T15:01:12.8130000Z     | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8130252Z 168 | import os
python-quality	Lint with Ruff	2026-06-05T15:01:12.8130442Z     |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8130549Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8130660Z E402 Module level import not at top of file
python-quality	Lint with Ruff	2026-06-05T15:01:12.8130948Z    --> apps/api/src/api/main.py:168:1
python-quality	Lint with Ruff	2026-06-05T15:01:12.8131199Z     |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8131418Z 166 | from fastapi.staticfiles import StaticFiles
python-quality	Lint with Ruff	2026-06-05T15:01:12.8131739Z 167 | from fastapi.responses import FileResponse
python-quality	Lint with Ruff	2026-06-05T15:01:12.8132031Z 168 | import os
python-quality	Lint with Ruff	2026-06-05T15:01:12.8132224Z     | ^^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8132404Z 169 |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8132700Z 170 | dist_dir = os.environ.get("FRONTEND_DIST_DIR", "/workspace/apps/web/dist")
python-quality	Lint with Ruff	2026-06-05T15:01:12.8133072Z     |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8133172Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8133333Z F401 [*] `starlette.responses.Response` imported but unused
python-quality	Lint with Ruff	2026-06-05T15:01:12.8133703Z   --> apps/api/src/api/middleware/tracing.py:13:33
python-quality	Lint with Ruff	2026-06-05T15:01:12.8133991Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8134250Z 11 | from starlette.middleware.base import BaseHTTPMiddleware
python-quality	Lint with Ruff	2026-06-05T15:01:12.8134607Z 12 | from starlette.requests import Request
python-quality	Lint with Ruff	2026-06-05T15:01:12.8134912Z 13 | from starlette.responses import Response
python-quality	Lint with Ruff	2026-06-05T15:01:12.8135194Z    |                                 ^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8135463Z 14 | from opentelemetry import trace
python-quality	Lint with Ruff	2026-06-05T15:01:12.8135752Z 15 | from opentelemetry.trace import StatusCode
python-quality	Lint with Ruff	2026-06-05T15:01:12.8136024Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8136276Z help: Remove unused import: `starlette.responses.Response`
python-quality	Lint with Ruff	2026-06-05T15:01:12.8136517Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8136611Z F401 [*] `os` imported but unused
python-quality	Lint with Ruff	2026-06-05T15:01:12.8136877Z  --> apps/api/src/api/routers/mcp.py:4:8
python-quality	Lint with Ruff	2026-06-05T15:01:12.8137132Z   |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8137309Z 2 | import time
python-quality	Lint with Ruff	2026-06-05T15:01:12.8137520Z 3 | import structlog
python-quality	Lint with Ruff	2026-06-05T15:01:12.8138210Z 4 | import os
python-quality	Lint with Ruff	2026-06-05T15:01:12.8138781Z   |        ^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8138997Z 5 | from typing import List, Optional
python-quality	Lint with Ruff	2026-06-05T15:01:12.8139415Z 6 | from fastapi import APIRouter, Depends, Request, HTTPException, status, Response
python-quality	Lint with Ruff	2026-06-05T15:01:12.8139814Z   |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8140006Z help: Remove unused import: `os`
python-quality	Lint with Ruff	2026-06-05T15:01:12.8140171Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8140332Z F401 [*] `core.workspace.touch_workspace` imported but unused
python-quality	Lint with Ruff	2026-06-05T15:01:12.8140701Z   --> apps/api/src/api/routers/workspace.py:19:5
python-quality	Lint with Ruff	2026-06-05T15:01:12.8140983Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8141282Z 17 |     get_workspace_by_session, create_workspace, get_workspace_enabled_tools,
python-quality	Lint with Ruff	2026-06-05T15:01:12.8141789Z 18 |     update_workspace_enabled_tools, get_recent_workspaces, get_all_workspaces,
python-quality	Lint with Ruff	2026-06-05T15:01:12.8142291Z 19 |     touch_workspace, create_workspace_from_dashboard, get_workspace_by_id,
python-quality	Lint with Ruff	2026-06-05T15:01:12.8142662Z    |     ^^^^^^^^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8143110Z 20 |     save_agent_context, load_agent_context, update_workspace_remote,
python-quality	Lint with Ruff	2026-06-05T15:01:12.8143581Z 21 |     activate_workspace, sync_workspace_runners, update_workspace_session,
python-quality	Lint with Ruff	2026-06-05T15:01:12.8143948Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8144203Z help: Remove unused import: `core.workspace.touch_workspace`
python-quality	Lint with Ruff	2026-06-05T15:01:12.8144444Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8144618Z F841 Local variable `workspace_dir` is assigned to but never used
python-quality	Lint with Ruff	2026-06-05T15:01:12.8144995Z    --> apps/api/src/api/routers/workspace.py:313:5
python-quality	Lint with Ruff	2026-06-05T15:01:12.8145279Z     |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8145520Z 311 |     engine: BaseAgentEngine = Depends(get_agent_engine)
python-quality	Lint with Ruff	2026-06-05T15:01:12.8145820Z 312 | ):
python-quality	Lint with Ruff	2026-06-05T15:01:12.8146092Z 313 |     workspace_dir = await get_workspace_dir(body.session_id, engine)
python-quality	Lint with Ruff	2026-06-05T15:01:12.8146441Z     |     ^^^^^^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8146756Z 314 |     workspace = get_workspace_by_session(DATABASE_PATH, body.session_id)
python-quality	Lint with Ruff	2026-06-05T15:01:12.8147126Z 315 |     if not workspace:
python-quality	Lint with Ruff	2026-06-05T15:01:12.8147354Z     |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8147872Z help: Remove assignment to unused variable `workspace_dir`
python-quality	Lint with Ruff	2026-06-05T15:01:12.8148136Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8148307Z F841 Local variable `workspace_dir` is assigned to but never used
python-quality	Lint with Ruff	2026-06-05T15:01:12.8148681Z    --> apps/api/src/api/routers/workspace.py:340:5
python-quality	Lint with Ruff	2026-06-05T15:01:12.8148962Z     |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8149195Z 338 |     engine: BaseAgentEngine = Depends(get_agent_engine)
python-quality	Lint with Ruff	2026-06-05T15:01:12.8149494Z 339 | ):
python-quality	Lint with Ruff	2026-06-05T15:01:12.8149767Z 340 |     workspace_dir = await get_workspace_dir(body.session_id, engine)
python-quality	Lint with Ruff	2026-06-05T15:01:12.8150113Z     |     ^^^^^^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8150447Z 341 |     current = get_workspace_enabled_tools(DATABASE_PATH, body.session_id) or []
python-quality	Lint with Ruff	2026-06-05T15:01:12.8150904Z 342 |     if body.is_enabled and body.server_id not in current:
python-quality	Lint with Ruff	2026-06-05T15:01:12.8151247Z     |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8151495Z help: Remove assignment to unused variable `workspace_dir`
python-quality	Lint with Ruff	2026-06-05T15:01:12.8151734Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8151858Z F401 [*] `typing.Optional` imported but unused
python-quality	Lint with Ruff	2026-06-05T15:01:12.8152194Z   --> apps/api/src/api/services/hermes_sync.py:11:20
python-quality	Lint with Ruff	2026-06-05T15:01:12.8152488Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8152664Z  9 | import shlex
python-quality	Lint with Ruff	2026-06-05T15:01:12.8152874Z 10 | import subprocess
python-quality	Lint with Ruff	2026-06-05T15:01:12.8153105Z 11 | from typing import Optional, List
python-quality	Lint with Ruff	2026-06-05T15:01:12.8153373Z    |                    ^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8153597Z 12 |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8172940Z 13 | import structlog
python-quality	Lint with Ruff	2026-06-05T15:01:12.8173348Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8173670Z help: Remove unused import
python-quality	Lint with Ruff	2026-06-05T15:01:12.8173931Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8174061Z F401 [*] `typing.List` imported but unused
python-quality	Lint with Ruff	2026-06-05T15:01:12.8174401Z   --> apps/api/src/api/services/hermes_sync.py:11:30
python-quality	Lint with Ruff	2026-06-05T15:01:12.8174698Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8174882Z  9 | import shlex
python-quality	Lint with Ruff	2026-06-05T15:01:12.8175094Z 10 | import subprocess
python-quality	Lint with Ruff	2026-06-05T15:01:12.8175333Z 11 | from typing import Optional, List
python-quality	Lint with Ruff	2026-06-05T15:01:12.8175595Z    |                              ^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8175838Z 12 |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8176019Z 13 | import structlog
python-quality	Lint with Ruff	2026-06-05T15:01:12.8176416Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8176607Z help: Remove unused import
python-quality	Lint with Ruff	2026-06-05T15:01:12.8176755Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8176865Z F401 [*] `typing.Any` imported but unused
python-quality	Lint with Ruff	2026-06-05T15:01:12.8177155Z  --> apps/api/tests/test_webmcp.py:7:20
python-quality	Lint with Ruff	2026-06-05T15:01:12.8177406Z   |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8177867Z 5 | import asyncio
python-quality	Lint with Ruff	2026-06-05T15:01:12.8178101Z 6 | import json
python-quality	Lint with Ruff	2026-06-05T15:01:12.8178313Z 7 | from typing import Any
python-quality	Lint with Ruff	2026-06-05T15:01:12.8178537Z   |                    ^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8178797Z 8 | from fastapi.testclient import TestClient
python-quality	Lint with Ruff	2026-06-05T15:01:12.8179100Z 9 | from api.main import app
python-quality	Lint with Ruff	2026-06-05T15:01:12.8179332Z   |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8179536Z help: Remove unused import: `typing.Any`
python-quality	Lint with Ruff	2026-06-05T15:01:12.8179728Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8179865Z F401 [*] `tool_registry.McpTool` imported but unused
python-quality	Lint with Ruff	2026-06-05T15:01:12.8180195Z   --> apps/api/tests/test_webmcp.py:10:49
python-quality	Lint with Ruff	2026-06-05T15:01:12.8180604Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8180823Z  8 | from fastapi.testclient import TestClient
python-quality	Lint with Ruff	2026-06-05T15:01:12.8181125Z  9 | from api.main import app
python-quality	Lint with Ruff	2026-06-05T15:01:12.8181425Z 10 | from tool_registry import McpEngine, McpServer, McpTool
python-quality	Lint with Ruff	2026-06-05T15:01:12.8181765Z    |                                                 ^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8182120Z 11 | from tool_registry.db import insert_server, insert_tools
python-quality	Lint with Ruff	2026-06-05T15:01:12.8182451Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8182683Z help: Remove unused import: `tool_registry.McpTool`
python-quality	Lint with Ruff	2026-06-05T15:01:12.8182901Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8183047Z F401 [*] `tool_registry.db.insert_tools` imported but unused
python-quality	Lint with Ruff	2026-06-05T15:01:12.8183377Z   --> apps/api/tests/test_webmcp.py:11:45
python-quality	Lint with Ruff	2026-06-05T15:01:12.8183638Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8183821Z  9 | from api.main import app
python-quality	Lint with Ruff	2026-06-05T15:01:12.8184111Z 10 | from tool_registry import McpEngine, McpServer, McpTool
python-quality	Lint with Ruff	2026-06-05T15:01:12.8184476Z 11 | from tool_registry.db import insert_server, insert_tools
python-quality	Lint with Ruff	2026-06-05T15:01:12.8184808Z    |                                             ^^^^^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8185063Z 12 |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8185249Z 13 | @pytest.fixture
python-quality	Lint with Ruff	2026-06-05T15:01:12.8185448Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8185698Z help: Remove unused import: `tool_registry.db.insert_tools`
python-quality	Lint with Ruff	2026-06-05T15:01:12.8185935Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8186088Z F841 Local variable `websocket` is assigned to but never used
python-quality	Lint with Ruff	2026-06-05T15:01:12.8186425Z   --> apps/api/tests/test_webmcp.py:73:56
python-quality	Lint with Ruff	2026-06-05T15:01:12.8186676Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8186888Z 72 | def test_webmcp_websocket_connection(client):
python-quality	Lint with Ruff	2026-06-05T15:01:12.8187269Z 73 |     with client.websocket_connect("/api/webmcp/ws") as websocket:
python-quality	Lint with Ruff	2026-06-05T15:01:12.8187894Z    |                                                        ^^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8188253Z 74 |         # Check connection is active and we can close it
python-quality	Lint with Ruff	2026-06-05T15:01:12.8188550Z 75 |         pass
python-quality	Lint with Ruff	2026-06-05T15:01:12.8188741Z    |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8188972Z help: Remove assignment to unused variable `websocket`
python-quality	Lint with Ruff	2026-06-05T15:01:12.8189207Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8189327Z F401 [*] `typing.Optional` imported but unused
python-quality	Lint with Ruff	2026-06-05T15:01:12.8189655Z  --> packages/core/src/core/agent_sync.py:6:20
python-quality	Lint with Ruff	2026-06-05T15:01:12.8189915Z   |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8190098Z 4 | import subprocess
python-quality	Lint with Ruff	2026-06-05T15:01:12.8190309Z 5 | import logging
python-quality	Lint with Ruff	2026-06-05T15:01:12.8190521Z 6 | from typing import Optional
python-quality	Lint with Ruff	2026-06-05T15:01:12.8190759Z   |                    ^^^^^^^^
python-quality	Lint with Ruff	2026-06-05T15:01:12.8190970Z 7 |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8191167Z 8 | logger = logging.getLogger(__name__)
python-quality	Lint with Ruff	2026-06-05T15:01:12.8191419Z   |
python-quality	Lint with Ruff	2026-06-05T15:01:12.8191630Z help: Remove unused import: `typing.Optional`
python-quality	Lint with Ruff	2026-06-05T15:01:12.8191832Z 
python-quality	Lint with Ruff	2026-06-05T15:01:12.8191916Z Found 20 errors.
python-quality	Lint with Ruff	2026-06-05T15:01:12.8192325Z [*] 11 fixable with the `--fix` option (3 hidden fixes can be enabled with the `--unsafe-fixes` option).
python-quality	Lint with Ruff	2026-06-05T15:01:12.8201950Z ##[error]Process completed with exit code 1.
```

---

## 2. Docker Build CI (Run #27022549130)
- **Branch**: `dev`
- **Commit SHA**: `1aee653959237e2937c8cae3492b705703316bc1`
- **Time**: 2026-06-05T15:01:01Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27022549130)

### Failed Log Output
```text
build-and-push	Set up job	﻿2026-06-05T15:01:06.8178234Z Current runner version: '2.334.0'
build-and-push	Set up job	2026-06-05T15:01:06.8214063Z ##[group]Runner Image Provisioner
build-and-push	Set up job	2026-06-05T15:01:06.8215684Z Hosted Compute Agent
build-and-push	Set up job	2026-06-05T15:01:06.8216609Z Version: 20260520.533
build-and-push	Set up job	2026-06-05T15:01:06.8217540Z Commit: 189110e25284a9812c124fd27b339e2fb4f2f9db
build-and-push	Set up job	2026-06-05T15:01:06.8218900Z Build Date: 2026-05-20T17:44:04Z
build-and-push	Set up job	2026-06-05T15:01:06.8220037Z Worker ID: {218d4462-7651-4972-8534-35e853763887}
build-and-push	Set up job	2026-06-05T15:01:06.8221404Z Azure Region: westcentralus
build-and-push	Set up job	2026-06-05T15:01:06.8222362Z ##[endgroup]
build-and-push	Set up job	2026-06-05T15:01:06.8224918Z ##[group]Operating System
build-and-push	Set up job	2026-06-05T15:01:06.8226095Z Ubuntu
build-and-push	Set up job	2026-06-05T15:01:06.8226882Z 24.04.4
build-and-push	Set up job	2026-06-05T15:01:06.8227728Z LTS
build-and-push	Set up job	2026-06-05T15:01:06.8228536Z ##[endgroup]
build-and-push	Set up job	2026-06-05T15:01:06.8229370Z ##[group]Runner Image
build-and-push	Set up job	2026-06-05T15:01:06.8230399Z Image: ubuntu-24.04
build-and-push	Set up job	2026-06-05T15:01:06.8231268Z Version: 20260525.161.1
build-and-push	Set up job	2026-06-05T15:01:06.8232933Z Included Software: https://github.com/actions/runner-images/blob/ubuntu24/20260525.161/images/ubuntu/Ubuntu2404-Readme.md
build-and-push	Set up job	2026-06-05T15:01:06.8236053Z Image Release: https://github.com/actions/runner-images/releases/tag/ubuntu24%2F20260525.161
build-and-push	Set up job	2026-06-05T15:01:06.8237781Z ##[endgroup]
build-and-push	Set up job	2026-06-05T15:01:06.8239664Z ##[group]GITHUB_TOKEN Permissions
build-and-push	Set up job	2026-06-05T15:01:06.8242782Z Contents: read
build-and-push	Set up job	2026-06-05T15:01:06.8244035Z Metadata: read
build-and-push	Set up job	2026-06-05T15:01:06.8244872Z Packages: read
build-and-push	Set up job	2026-06-05T15:01:06.8245892Z ##[endgroup]
build-and-push	Set up job	2026-06-05T15:01:06.8248826Z Secret source: Actions
build-and-push	Set up job	2026-06-05T15:01:06.8250015Z Prepare workflow directory
build-and-push	Set up job	2026-06-05T15:01:06.8807867Z Prepare all required actions
build-and-push	Set up job	2026-06-05T15:01:06.8862652Z Getting action download info
build-and-push	Set up job	2026-06-05T15:01:07.6246246Z ##[error]Unable to resolve action `aquasecurity/trivy-action@0.28.0`, unable to find version `0.28.0`
```

---

## 3. frontend-quality (Run #27022549034)
- **Branch**: `dev`
- **Commit SHA**: `1aee653959237e2937c8cae3492b705703316bc1`
- **Time**: 2026-06-05T15:01:01Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27022549034)

### Failed Log Output
```text
frontend-quality	Lint with ESLint	﻿2026-06-05T15:01:20.3541135Z ##[group]Run npx eslint apps/web/
frontend-quality	Lint with ESLint	2026-06-05T15:01:20.3541708Z [36;1mnpx eslint apps/web/[0m
frontend-quality	Lint with ESLint	2026-06-05T15:01:20.3577914Z shell: /usr/bin/bash -e {0}
frontend-quality	Lint with ESLint	2026-06-05T15:01:20.3578360Z ##[endgroup]
frontend-quality	Lint with ESLint	2026-06-05T15:01:20.8567594Z sh: 1: eslint: not found
frontend-quality	Lint with ESLint	2026-06-05T15:01:20.8708413Z ##[error]Process completed with exit code 127.
```

---
