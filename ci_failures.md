# CI Failure Report
Generated automatically for local triage and AI code patching.

---

## 1. Docker Build CI (Run #27025056226)
- **Branch**: `007-workspace-dashboard-ux`
- **Commit SHA**: `7c1464c8b505ca32bd3d7f1336b6f04c5fee24d2`
- **Time**: 2026-06-05T15:50:14Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27025056226)

### Failed Log Output
```text
build-and-push	Set up job	﻿2026-06-05T15:50:20.3585540Z Current runner version: '2.334.0'
build-and-push	Set up job	2026-06-05T15:50:20.3614741Z ##[group]Runner Image Provisioner
build-and-push	Set up job	2026-06-05T15:50:20.3616572Z Hosted Compute Agent
build-and-push	Set up job	2026-06-05T15:50:20.3617224Z Version: 20260520.533
build-and-push	Set up job	2026-06-05T15:50:20.3617969Z Commit: 189110e25284a9812c124fd27b339e2fb4f2f9db
build-and-push	Set up job	2026-06-05T15:50:20.3618739Z Build Date: 2026-05-20T17:44:04Z
build-and-push	Set up job	2026-06-05T15:50:20.3619459Z Worker ID: {139678e5-4621-41a3-beb2-5157716ef52a}
build-and-push	Set up job	2026-06-05T15:50:20.3620294Z Azure Region: westus2
build-and-push	Set up job	2026-06-05T15:50:20.3620890Z ##[endgroup]
build-and-push	Set up job	2026-06-05T15:50:20.3622593Z ##[group]Operating System
build-and-push	Set up job	2026-06-05T15:50:20.3623313Z Ubuntu
build-and-push	Set up job	2026-06-05T15:50:20.3623885Z 24.04.4
build-and-push	Set up job	2026-06-05T15:50:20.3624488Z LTS
build-and-push	Set up job	2026-06-05T15:50:20.3625363Z ##[endgroup]
build-and-push	Set up job	2026-06-05T15:50:20.3625954Z ##[group]Runner Image
build-and-push	Set up job	2026-06-05T15:50:20.3626715Z Image: ubuntu-24.04
build-and-push	Set up job	2026-06-05T15:50:20.3627334Z Version: 20260525.161.1
build-and-push	Set up job	2026-06-05T15:50:20.3628443Z Included Software: https://github.com/actions/runner-images/blob/ubuntu24/20260525.161/images/ubuntu/Ubuntu2404-Readme.md
build-and-push	Set up job	2026-06-05T15:50:20.3630252Z Image Release: https://github.com/actions/runner-images/releases/tag/ubuntu24%2F20260525.161
build-and-push	Set up job	2026-06-05T15:50:20.3631322Z ##[endgroup]
build-and-push	Set up job	2026-06-05T15:50:20.3632646Z ##[group]GITHUB_TOKEN Permissions
build-and-push	Set up job	2026-06-05T15:50:20.3635442Z Contents: read
build-and-push	Set up job	2026-06-05T15:50:20.3636113Z Metadata: read
build-and-push	Set up job	2026-06-05T15:50:20.3636770Z Packages: read
build-and-push	Set up job	2026-06-05T15:50:20.3637375Z ##[endgroup]
build-and-push	Set up job	2026-06-05T15:50:20.3639755Z Secret source: Actions
build-and-push	Set up job	2026-06-05T15:50:20.3640753Z Prepare workflow directory
build-and-push	Set up job	2026-06-05T15:50:20.4006075Z Prepare all required actions
build-and-push	Set up job	2026-06-05T15:50:20.4045401Z Getting action download info
build-and-push	Set up job	2026-06-05T15:50:21.0379101Z Download action repository 'actions/checkout@v4' (SHA:34e114876b0b11c390a56381ad16ebd13914f8d5)
build-and-push	Set up job	2026-06-05T15:50:21.1695793Z Download action repository 'docker/setup-buildx-action@v3' (SHA:8d2750c68a42422c14e847fe6c8ac0403b4cbd6f)
build-and-push	Set up job	2026-06-05T15:50:21.5121289Z Download action repository 'docker/login-action@v3' (SHA:c94ce9fb468520275223c153574b00df6fe4bcc9)
build-and-push	Set up job	2026-06-05T15:50:21.9119466Z Download action repository 'docker/metadata-action@v5' (SHA:c299e40c65443455700f0fdfc63efafe5b349051)
build-and-push	Set up job	2026-06-05T15:50:22.3821700Z Download action repository 'docker/build-push-action@v6' (SHA:10e90e3645eae34f1e60eeb005ba3a3d33f178e8)
build-and-push	Set up job	2026-06-05T15:50:22.7361702Z Download action repository 'aquasecurity/trivy-action@v0.28.0' (SHA:915b19bbe73b92a6cf82a1bc12b087c9a19a5fe2)
build-and-push	Set up job	2026-06-05T15:50:23.1194288Z Getting action download info
build-and-push	Set up job	2026-06-05T15:50:23.4930407Z ##[error]Unable to resolve action `aquasecurity/setup-trivy@v0.2.1`, unable to find version `v0.2.1`
```

---

## 2. python-quality (Run #27025056259)
- **Branch**: `007-workspace-dashboard-ux`
- **Commit SHA**: `7c1464c8b505ca32bd3d7f1336b6f04c5fee24d2`
- **Time**: 2026-06-05T15:50:14Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27025056259)

### Failed Log Output
```text
python-quality	Run Tests with pytest	﻿2026-06-05T15:50:30.0194914Z ##[group]Run uv run pytest
python-quality	Run Tests with pytest	2026-06-05T15:50:30.0195232Z [36;1muv run pytest[0m
python-quality	Run Tests with pytest	2026-06-05T15:50:30.0221710Z shell: /usr/bin/bash -e {0}
python-quality	Run Tests with pytest	2026-06-05T15:50:30.0222038Z env:
python-quality	Run Tests with pytest	2026-06-05T15:50:30.0222280Z   UV_CACHE_DIR: /home/runner/work/_temp/setup-uv-cache
python-quality	Run Tests with pytest	2026-06-05T15:50:30.0222659Z   pythonLocation: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:50:30.0223080Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.13.13/x64/lib/pkgconfig
python-quality	Run Tests with pytest	2026-06-05T15:50:30.0223484Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:50:30.0223847Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:50:30.0224216Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:50:30.0224583Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.13.13/x64/lib
python-quality	Run Tests with pytest	2026-06-05T15:50:30.0224893Z ##[endgroup]
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1786642Z ============================= test session starts ==============================
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1787673Z platform linux -- Python 3.13.13, pytest-9.0.3, pluggy-1.6.0
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1788739Z rootdir: /home/runner/work/wright/wright
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1789465Z configfile: pyproject.toml
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1790063Z plugins: asyncio-1.4.0
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1791356Z asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1792536Z collected 0 items / 5 errors
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1792997Z 
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1793394Z ==================================== ERRORS ====================================
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1794363Z ____________ ERROR collecting apps/api/tests/test_hermes_adapter.py ____________
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1795683Z ImportError while importing test module '/home/runner/work/wright/wright/apps/api/tests/test_hermes_adapter.py'.
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1796958Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1797757Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1798608Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1799754Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1800573Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1801508Z apps/api/tests/test_hermes_adapter.py:3: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1802342Z     from agent_adapters import HermesAdapter, AgentChatRequest
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1803192Z E   ModuleNotFoundError: No module named 'agent_adapters'
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1804091Z _______________ ERROR collecting apps/api/tests/test_mcp_api.py ________________
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1805246Z ImportError while importing test module '/home/runner/work/wright/wright/apps/api/tests/test_mcp_api.py'.
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1806421Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1807289Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1808121Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1809251Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1810412Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1811398Z apps/api/tests/test_mcp_api.py:5: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1812123Z     from fastapi.testclient import TestClient
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1812849Z E   ModuleNotFoundError: No module named 'fastapi'
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1813761Z ________________ ERROR collecting apps/api/tests/test_webmcp.py ________________
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1815062Z ImportError while importing test module '/home/runner/work/wright/wright/apps/api/tests/test_webmcp.py'.
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1816316Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1817106Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1817959Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1819080Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1819882Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1821133Z apps/api/tests/test_webmcp.py:7: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1821882Z     from fastapi.testclient import TestClient
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1822629Z E   ModuleNotFoundError: No module named 'fastapi'
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1823539Z ____________ ERROR collecting apps/api/tests/test_workspace_api.py _____________
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1824846Z ImportError while importing test module '/home/runner/work/wright/wright/apps/api/tests/test_workspace_api.py'.
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1826202Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1826987Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1827827Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1828950Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1829754Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1830511Z apps/api/tests/test_workspace_api.py:4: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1831489Z     from fastapi.testclient import TestClient
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1832263Z E   ModuleNotFoundError: No module named 'fastapi'
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1833206Z ________ ERROR collecting packages/tool_registry/tests/test_registry.py ________
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1834537Z ImportError while importing test module '/home/runner/work/wright/wright/packages/tool_registry/tests/test_registry.py'.
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1835771Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1836513Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1837302Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1838390Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1839153Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1839929Z packages/tool_registry/tests/test_registry.py:7: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1841104Z     from tool_registry.models import McpServer, McpTool
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1841925Z E   ModuleNotFoundError: No module named 'tool_registry'
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1842746Z =========================== short test summary info ============================
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1843723Z ERROR apps/api/tests/test_hermes_adapter.py
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1844475Z ERROR apps/api/tests/test_mcp_api.py
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1845168Z ERROR apps/api/tests/test_webmcp.py
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1845845Z ERROR apps/api/tests/test_workspace_api.py
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1846632Z ERROR packages/tool_registry/tests/test_registry.py
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1847606Z !!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
python-quality	Run Tests with pytest	2026-06-05T15:50:31.1848636Z ============================== 5 errors in 0.39s ===============================
python-quality	Run Tests with pytest	2026-06-05T15:50:31.2132873Z ##[error]Process completed with exit code 2.
```

---

## 3. Docker Build CI (Run #27024916913)
- **Branch**: `dev`
- **Commit SHA**: `7c1464c8b505ca32bd3d7f1336b6f04c5fee24d2`
- **Time**: 2026-06-05T15:47:20Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27024916913)

### Failed Log Output
```text
build-and-push	Set up job	﻿2026-06-05T15:47:24.8814145Z Current runner version: '2.334.0'
build-and-push	Set up job	2026-06-05T15:47:24.8870846Z ##[group]Runner Image Provisioner
build-and-push	Set up job	2026-06-05T15:47:24.8872233Z Hosted Compute Agent
build-and-push	Set up job	2026-06-05T15:47:24.8873261Z Version: 20260520.533
build-and-push	Set up job	2026-06-05T15:47:24.8874261Z Commit: 189110e25284a9812c124fd27b339e2fb4f2f9db
build-and-push	Set up job	2026-06-05T15:47:24.8875521Z Build Date: 2026-05-20T17:44:04Z
build-and-push	Set up job	2026-06-05T15:47:24.8876950Z Worker ID: {0be7b04d-4000-4627-b366-8ba6bcf84971}
build-and-push	Set up job	2026-06-05T15:47:24.8878152Z Azure Region: eastus
build-and-push	Set up job	2026-06-05T15:47:24.8879178Z ##[endgroup]
build-and-push	Set up job	2026-06-05T15:47:24.8881849Z ##[group]Operating System
build-and-push	Set up job	2026-06-05T15:47:24.8882966Z Ubuntu
build-and-push	Set up job	2026-06-05T15:47:24.8883865Z 24.04.4
build-and-push	Set up job	2026-06-05T15:47:24.8884706Z LTS
build-and-push	Set up job	2026-06-05T15:47:24.8885616Z ##[endgroup]
build-and-push	Set up job	2026-06-05T15:47:24.8886870Z ##[group]Runner Image
build-and-push	Set up job	2026-06-05T15:47:24.8887946Z Image: ubuntu-24.04
build-and-push	Set up job	2026-06-05T15:47:24.8888934Z Version: 20260525.161.1
build-and-push	Set up job	2026-06-05T15:47:24.8890676Z Included Software: https://github.com/actions/runner-images/blob/ubuntu24/20260525.161/images/ubuntu/Ubuntu2404-Readme.md
build-and-push	Set up job	2026-06-05T15:47:24.8893594Z Image Release: https://github.com/actions/runner-images/releases/tag/ubuntu24%2F20260525.161
build-and-push	Set up job	2026-06-05T15:47:24.8895246Z ##[endgroup]
build-and-push	Set up job	2026-06-05T15:47:24.8897513Z ##[group]GITHUB_TOKEN Permissions
build-and-push	Set up job	2026-06-05T15:47:24.8900668Z Contents: read
build-and-push	Set up job	2026-06-05T15:47:24.8901629Z Metadata: read
build-and-push	Set up job	2026-06-05T15:47:24.8902503Z Packages: read
build-and-push	Set up job	2026-06-05T15:47:24.8903526Z ##[endgroup]
build-and-push	Set up job	2026-06-05T15:47:24.8906977Z Secret source: Actions
build-and-push	Set up job	2026-06-05T15:47:24.8908730Z Prepare workflow directory
build-and-push	Set up job	2026-06-05T15:47:24.9379591Z Prepare all required actions
build-and-push	Set up job	2026-06-05T15:47:24.9433234Z Getting action download info
build-and-push	Set up job	2026-06-05T15:47:25.3743902Z Download action repository 'actions/checkout@v4' (SHA:34e114876b0b11c390a56381ad16ebd13914f8d5)
build-and-push	Set up job	2026-06-05T15:47:25.4947229Z Download action repository 'docker/setup-buildx-action@v3' (SHA:8d2750c68a42422c14e847fe6c8ac0403b4cbd6f)
build-and-push	Set up job	2026-06-05T15:47:25.7242910Z Download action repository 'docker/login-action@v3' (SHA:c94ce9fb468520275223c153574b00df6fe4bcc9)
build-and-push	Set up job	2026-06-05T15:47:25.9807636Z Download action repository 'docker/metadata-action@v5' (SHA:c299e40c65443455700f0fdfc63efafe5b349051)
build-and-push	Set up job	2026-06-05T15:47:26.2717475Z Download action repository 'docker/build-push-action@v6' (SHA:10e90e3645eae34f1e60eeb005ba3a3d33f178e8)
build-and-push	Set up job	2026-06-05T15:47:26.8212437Z Download action repository 'aquasecurity/trivy-action@v0.28.0' (SHA:915b19bbe73b92a6cf82a1bc12b087c9a19a5fe2)
build-and-push	Set up job	2026-06-05T15:47:27.0668317Z Getting action download info
build-and-push	Set up job	2026-06-05T15:47:27.3127760Z ##[error]Unable to resolve action `aquasecurity/setup-trivy@v0.2.1`, unable to find version `v0.2.1`
```

---

## 4. python-quality (Run #27024916944)
- **Branch**: `dev`
- **Commit SHA**: `7c1464c8b505ca32bd3d7f1336b6f04c5fee24d2`
- **Time**: 2026-06-05T15:47:20Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27024916944)

### Failed Log Output
```text
python-quality	Run Tests with pytest	﻿2026-06-05T15:47:47.6464766Z ##[group]Run uv run pytest
python-quality	Run Tests with pytest	2026-06-05T15:47:47.6465058Z [36;1muv run pytest[0m
python-quality	Run Tests with pytest	2026-06-05T15:47:47.6490871Z shell: /usr/bin/bash -e {0}
python-quality	Run Tests with pytest	2026-06-05T15:47:47.6491121Z env:
python-quality	Run Tests with pytest	2026-06-05T15:47:47.6491363Z   UV_CACHE_DIR: /home/runner/work/_temp/setup-uv-cache
python-quality	Run Tests with pytest	2026-06-05T15:47:47.6491756Z   pythonLocation: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:47:47.6492179Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.13.13/x64/lib/pkgconfig
python-quality	Run Tests with pytest	2026-06-05T15:47:47.6492608Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:47:47.6493004Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:47:47.6493406Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:47:47.6493797Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.13.13/x64/lib
python-quality	Run Tests with pytest	2026-06-05T15:47:47.6494113Z ##[endgroup]
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3120735Z ============================= test session starts ==============================
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3121838Z platform linux -- Python 3.13.13, pytest-9.0.3, pluggy-1.6.0
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3127031Z rootdir: /home/runner/work/wright/wright
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3127855Z configfile: pyproject.toml
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3128629Z plugins: asyncio-1.4.0
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3129708Z asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3131104Z collected 0 items / 5 errors
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3131558Z 
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3131969Z ==================================== ERRORS ====================================
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3132916Z ____________ ERROR collecting apps/api/tests/test_hermes_adapter.py ____________
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3134221Z ImportError while importing test module '/home/runner/work/wright/wright/apps/api/tests/test_hermes_adapter.py'.
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3135483Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3136260Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3137103Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3138249Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3139066Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3139821Z apps/api/tests/test_hermes_adapter.py:3: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3140849Z     from agent_adapters import HermesAdapter, AgentChatRequest
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3141735Z E   ModuleNotFoundError: No module named 'agent_adapters'
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3142681Z _______________ ERROR collecting apps/api/tests/test_mcp_api.py ________________
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3143932Z ImportError while importing test module '/home/runner/work/wright/wright/apps/api/tests/test_mcp_api.py'.
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3145141Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3145926Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3146772Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3147901Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3149181Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3149914Z apps/api/tests/test_mcp_api.py:5: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3150862Z     from fastapi.testclient import TestClient
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3151627Z E   ModuleNotFoundError: No module named 'fastapi'
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3152693Z ________________ ERROR collecting apps/api/tests/test_webmcp.py ________________
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3154204Z ImportError while importing test module '/home/runner/work/wright/wright/apps/api/tests/test_webmcp.py'.
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3155412Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3156202Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3157052Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3158171Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3158957Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3160026Z apps/api/tests/test_webmcp.py:7: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3161061Z     from fastapi.testclient import TestClient
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3168970Z E   ModuleNotFoundError: No module named 'fastapi'
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3169801Z ____________ ERROR collecting apps/api/tests/test_workspace_api.py _____________
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3171071Z ImportError while importing test module '/home/runner/work/wright/wright/apps/api/tests/test_workspace_api.py'.
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3172118Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3172823Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3173626Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3174714Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3175513Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3176370Z apps/api/tests/test_workspace_api.py:4: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3179891Z     from fastapi.testclient import TestClient
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3181657Z E   ModuleNotFoundError: No module named 'fastapi'
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3182675Z ________ ERROR collecting packages/tool_registry/tests/test_registry.py ________
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3184085Z ImportError while importing test module '/home/runner/work/wright/wright/packages/tool_registry/tests/test_registry.py'.
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3185404Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3186216Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3187078Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3188231Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3189055Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3189886Z packages/tool_registry/tests/test_registry.py:7: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3191028Z     from tool_registry.models import McpServer, McpTool
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3192339Z E   ModuleNotFoundError: No module named 'tool_registry'
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3193242Z =========================== short test summary info ============================
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3194079Z ERROR apps/api/tests/test_hermes_adapter.py
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3194799Z ERROR apps/api/tests/test_mcp_api.py
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3195478Z ERROR apps/api/tests/test_webmcp.py
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3196151Z ERROR apps/api/tests/test_workspace_api.py
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3196906Z ERROR packages/tool_registry/tests/test_registry.py
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3197966Z !!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3198946Z ============================== 5 errors in 0.37s ===============================
python-quality	Run Tests with pytest	2026-06-05T15:47:49.3463124Z ##[error]Process completed with exit code 2.
```

---

## 5. python-quality (Run #27024915978)
- **Branch**: `dev`
- **Commit SHA**: `7c1464c8b505ca32bd3d7f1336b6f04c5fee24d2`
- **Time**: 2026-06-05T15:47:19Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27024915978)

### Failed Log Output
```text
python-quality	Run Tests with pytest	﻿2026-06-05T15:47:33.3992248Z ##[group]Run uv run pytest
python-quality	Run Tests with pytest	2026-06-05T15:47:33.3992586Z [36;1muv run pytest[0m
python-quality	Run Tests with pytest	2026-06-05T15:47:33.4020726Z shell: /usr/bin/bash -e {0}
python-quality	Run Tests with pytest	2026-06-05T15:47:33.4021178Z env:
python-quality	Run Tests with pytest	2026-06-05T15:47:33.4021451Z   UV_CACHE_DIR: /home/runner/work/_temp/setup-uv-cache
python-quality	Run Tests with pytest	2026-06-05T15:47:33.4021861Z   pythonLocation: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:47:33.4022310Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.13.13/x64/lib/pkgconfig
python-quality	Run Tests with pytest	2026-06-05T15:47:33.4022738Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:47:33.4023142Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:47:33.4023545Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:47:33.4023934Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.13.13/x64/lib
python-quality	Run Tests with pytest	2026-06-05T15:47:33.4024278Z ##[endgroup]
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9713621Z ============================= test session starts ==============================
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9714726Z platform linux -- Python 3.13.13, pytest-9.0.3, pluggy-1.6.0
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9715835Z rootdir: /home/runner/work/wright/wright
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9716735Z configfile: pyproject.toml
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9717302Z plugins: asyncio-1.4.0
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9718338Z asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9719433Z collected 0 items / 5 errors
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9719887Z 
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9720278Z ==================================== ERRORS ====================================
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9721197Z ____________ ERROR collecting apps/api/tests/test_hermes_adapter.py ____________
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9722426Z ImportError while importing test module '/home/runner/work/wright/wright/apps/api/tests/test_hermes_adapter.py'.
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9723638Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9724420Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9725247Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9726474Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9727401Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9728146Z apps/api/tests/test_hermes_adapter.py:3: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9728957Z     from agent_adapters import HermesAdapter, AgentChatRequest
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9729787Z E   ModuleNotFoundError: No module named 'agent_adapters'
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9730660Z _______________ ERROR collecting apps/api/tests/test_mcp_api.py ________________
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9731834Z ImportError while importing test module '/home/runner/work/wright/wright/apps/api/tests/test_mcp_api.py'.
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9733001Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9733761Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9734572Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9735651Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9736610Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9737314Z apps/api/tests/test_mcp_api.py:5: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9737999Z     from fastapi.testclient import TestClient
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9738722Z E   ModuleNotFoundError: No module named 'fastapi'
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9739599Z ________________ ERROR collecting apps/api/tests/test_webmcp.py ________________
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9740788Z ImportError while importing test module '/home/runner/work/wright/wright/apps/api/tests/test_webmcp.py'.
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9741945Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9742735Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9743560Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9744607Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9745366Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9746807Z apps/api/tests/test_webmcp.py:7: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9747721Z     from fastapi.testclient import TestClient
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9748441Z E   ModuleNotFoundError: No module named 'fastapi'
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9749299Z ____________ ERROR collecting apps/api/tests/test_workspace_api.py _____________
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9750538Z ImportError while importing test module '/home/runner/work/wright/wright/apps/api/tests/test_workspace_api.py'.
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9751735Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9752495Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9753309Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9754445Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9755237Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9756108Z apps/api/tests/test_workspace_api.py:4: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9756843Z     from fastapi.testclient import TestClient
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9757543Z E   ModuleNotFoundError: No module named 'fastapi'
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9758366Z ________ ERROR collecting packages/tool_registry/tests/test_registry.py ________
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9759577Z ImportError while importing test module '/home/runner/work/wright/wright/packages/tool_registry/tests/test_registry.py'.
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9760711Z Hint: make sure your test modules/packages have valid Python names.
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9761420Z Traceback:
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9762179Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/importlib/__init__.py:88: in import_module
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9763198Z     return _bootstrap._gcd_import(name[level:], package, level)
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9763931Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9764656Z packages/tool_registry/tests/test_registry.py:7: in <module>
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9765439Z     from tool_registry.models import McpServer, McpTool
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9766320Z E   ModuleNotFoundError: No module named 'tool_registry'
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9767079Z =========================== short test summary info ============================
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9767772Z ERROR apps/api/tests/test_hermes_adapter.py
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9768356Z ERROR apps/api/tests/test_mcp_api.py
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9768903Z ERROR apps/api/tests/test_webmcp.py
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9769449Z ERROR apps/api/tests/test_workspace_api.py
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9770044Z ERROR packages/tool_registry/tests/test_registry.py
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9770824Z !!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
python-quality	Run Tests with pytest	2026-06-05T15:47:34.9771728Z ============================== 5 errors in 0.35s ===============================
python-quality	Run Tests with pytest	2026-06-05T15:47:35.0090114Z ##[error]Process completed with exit code 2.
```

---
