# MCP Server Setup Recipes

These notes capture the repeatable setup path for each MCP server validated in
the engineering catalog sprint. They are intentionally operational: future
agents should be able to retest a server after upstream changes without
rediscovering package names, backend paths, or known traps.

Use these recipes with the clean-container validation process in
`docs/mcp-catalog/mcp-server-testing-process.md`.

## Common Container Baseline

- Start from `wright:latest` on `linux/amd64`.
- Do not assume selected-server CAD/CAM/CAE software is installed.
- Prefer newline-delimited JSON MCP probes first. Several Python/FastMCP servers
  in this catalog reject `Content-Length` framing on stdio.
- Use `Content-Length` framing only after confirming the server expects the
  official SDK framing.
- For GUI-backed FreeCAD workbench tests, install Xvfb only inside the
  disposable validation container.

## OpenSCAD Geometry (`openscad-mcp-server`)

Source: https://github.com/quellant/openscad-mcp

Install selected-server dependencies:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends openscad xvfb
```

Run MCP:

```bash
uv run --with git+https://github.com/quellant/openscad-mcp.git openscad-mcp
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `check_openscad`
- `export_model` with `cube([1,1,1]);` to `/tmp/wright-validation-cube.stl`

Known notes:

- Use newline-delimited JSON over stdio.
- `validate_scad` can return ambiguous `success:true` and `valid:false`; use
  `check_openscad` plus a tiny export as the backend proof.

## OpenSCAD Linter (`openscad-linter-trikos529`)

Configured source: https://github.com/topics/cad-3d

Attempted command:

```bash
uv tool run openscad-linter-mcp --help
```

Known result:

- The configured package name does not resolve in the Python package registry.
- No specific repository/package was found during validation.
- Keep as non-working until the intended MCP source is identified.

Follow-up: `docs/mcp-catalog/followups/openscad-linter-trikos529.md`

## CAiD OpenCASCADE (`caid-opencascade-dreliq9`)

Sources:

- MCP server: https://github.com/dreliq9/caid-mcp
- CAiD backend: https://github.com/dreliq9/CAiD

Install selected-server dependencies:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends libgl1
git clone --depth 1 https://github.com/dreliq9/caid-mcp /tmp/mcp-caid
git clone --depth 1 https://github.com/dreliq9/CAiD /tmp/CAiD
cd /tmp/mcp-caid
uv venv --python 3.11 /tmp/caid-venv
. /tmp/caid-venv/bin/activate
uv pip install -e /tmp/CAiD
uv pip install -e ".[dev]"
```

Run MCP:

```bash
python /tmp/mcp-caid/server.py
```

Validation probes:

- `pytest tests/ -q`
- `initialize`
- `notifications/initialized`
- `tools/list`
- `create_box` with `name=wright_box`, `length=10`, `width=8`, `height=6`
- `list_objects` or the available scene query tool to confirm `wright_box`

Known result:

- `caid-mcp` commit `bb863e9fe64f951fac9d59daed26254544682bc3`.
- CAiD backend commit `840d9ece24499dca4d1cc6b7a7aef2b88a203f14`.
- 72 upstream MCP tests passed.
- MCP listed 107 tools.
- `create_box` returned `ok:true`, `volume_mm3:480.0`, and a 10 x 8 x 6 mm
  bounding box.

Known notes:

- `uv tool run caid-mcp` is not a valid launch path because the package does
  not provide a console script. Run `server.py` from the cloned repository.
- Installing `caid` from PyPI currently produced a package missing
  `caid.vector`, which the MCP imports. Installing CAiD from its GitHub source
  fixed the mismatch.
- OCP/CadQuery needs `libGL.so.1`; install `libgl1` in the selected-server
  container.

## CalculiX Simulation (`calculix-simulation`)

Configured source: https://github.com/calculix/calculix-mcp

Attempted commands:

```bash
git clone --depth 1 https://github.com/calculix/calculix-mcp /tmp/mcp-calculix
uv tool run calculix-mcp --help
```

Known result:

- The configured GitHub URL could not be cloned in the clean Intel Ubuntu
  container; git prompted for credentials, consistent with a missing or private
  repository.
- `calculix-mcp` was not found in the Python package registry.
- The research handoff described this row as a FreeCAD FEM capability alias or
  wrapper candidate, not a verified standalone MCP server.

Next validation path:

- Keep blocked until a concrete standalone MCP source is identified.
- If the capability is only available through a FreeCAD MCP backend, validate it
  as part of that FreeCAD server instead of as a separate server.

## FreeCAD Engineering (`freecad-engineering-sandraschi`)

Source: https://github.com/sandraschi/freecad-mcp

Run MCP:

```bash
FREECAD_PATH=/tmp/freecadcmd \
  uv run --with git+https://github.com/sandraschi/freecad-mcp.git \
  python -m freecad_mcp.server --mode stdio
```

Install selected-server FreeCAD dependency:

```bash
curl -fL -o FreeCAD.AppImage \
  https://sourceforge.net/projects/free-cad/files/1.1.1/FreeCAD_1.1.1-Linux-x86_64-py311.AppImage/download
chmod +x FreeCAD.AppImage
./FreeCAD.AppImage --appimage-extract
ln -sfn "$PWD/squashfs-root/usr/bin/freecadcmd" /tmp/freecadcmd
```

Backend control check:

```bash
/tmp/freecadcmd -c "import FreeCAD, Part, Mesh, os; doc=FreeCAD.newDocument('WrightValidation'); obj=doc.addObject('Part::Box','Box'); obj.Length=10; obj.Width=10; obj.Height=10; doc.recompute(); Mesh.export([obj], '/tmp/direct_freecad_box.stl'); print(os.path.getsize('/tmp/direct_freecad_box.stl'))"
```

Known result:

- Repository commit `a71f60a71987ac23a65a3bdeda5f71c8f1579efb`.
- Upstream tests passed with `uv sync --extra dev && uv run pytest -q`:
  94 passed, 2 integration tests deselected.
- MCP initialized as server `FreeCAD MCP` version `3.4.2`.
- MCP listed 47 tools.
- FreeCAD 1.1.1 direct CLI exported a 684-byte STL successfully.
- `freecad_status` returned `success:false` and `freecad_ok:false` even when
  `FREECAD_PATH=/tmp/freecadcmd` was set.
- The advertised `--freecad-path /tmp/freecadcmd` option did not affect the
  subprocess path; `create_shape` returned `FreeCADCmd not found`.
- With `FREECAD_PATH=/tmp/freecadcmd`, MCP `create_shape` ran FreeCAD and
  returned `success:true` while stderr reported
  `Cannot create a mesh out of a 'Part.Solid'`, and no output STL was produced.

Follow-up: `docs/mcp-catalog/followups/freecad-engineering-sandraschi.md`

## FreeCAD Booleans (`freecad-booleans-lucygoodchild`)

Source: https://github.com/lucygoodchild/freecad-mcp-server

Setup:

```bash
git clone --depth 1 https://github.com/lucygoodchild/freecad-mcp-server /tmp/mcp-freecad-booleans
cd /tmp/mcp-freecad-booleans
npm install
npm run build
```

Install selected-server FreeCAD dependency:

```bash
curl -fL -o FreeCAD.AppImage \
  https://sourceforge.net/projects/free-cad/files/1.1.1/FreeCAD_1.1.1-Linux-x86_64-py311.AppImage/download
chmod +x FreeCAD.AppImage
./FreeCAD.AppImage --appimage-extract
sudo ln -sfn "$PWD/squashfs-root/usr/bin/freecadcmd" /usr/bin/freecadcmd
```

Run MCP:

```bash
node build/index.js
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- Without FreeCAD: `list_objects` starts backend initialization and reports
  `spawn freecad ENOENT`.
- With FreeCAD AppImage symlinked to `/usr/bin/freecadcmd`: `create_box` with
  `length=10`, `width=8`, `height=6`, `name=WrightBox`
- `list_objects`

Known result:

- Repository commit `21636a406f8fd77d99ba1b679282e0995b879202`.
- MCP listed 7 tools.
- FreeCAD 1.1.1 AppImage was detected at `/usr/bin/freecadcmd`.
- `create_box` created `WrightBox`.
- `list_objects` reported FreeCAD Part boxes.

Known notes:

- The configured `uvx freecad-mcp-server` package path does not resolve in the
  Python package registry; this is a Node/TypeScript MCP server.
- The current Ubuntu apt repository did not provide a `freecad` package, so use
  the FreeCAD AppImage selected-server install path.
- The server writes operational messages such as `Starting persistent FreeCAD
  process...` to stdout during tool calls. This is a stdio protocol risk for
  strict clients even though the direct validation probe received JSON-RPC
  responses and backend operations succeeded.

## FreeCAD Core (`freecad-core-nekanat`)

Source: https://github.com/neka-nat/freecad-mcp

Run MCP:

```bash
uvx freecad-mcp --only-text-feedback
# Equivalent in the Wright Ubuntu validation container:
uv tool run freecad-mcp --only-text-feedback
```

Install selected-server FreeCAD dependency:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  xvfb xauth libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0 \
  libxrender1 libxi6 libxrandr2 libxinerama1 libxcursor1 \
  libxcomposite1 libxdamage1 libxtst6 libfontconfig1 libdbus-1-3

curl -fL -o FreeCAD.AppImage \
  https://sourceforge.net/projects/free-cad/files/1.1.1/FreeCAD_1.1.1-Linux-x86_64-py311.AppImage/download
chmod +x FreeCAD.AppImage
./FreeCAD.AppImage --appimage-extract
```

Install the addon into FreeCAD user Mod paths and enable the local RPC server:

```bash
git clone --depth 1 https://github.com/neka-nat/freecad-mcp /tmp/mcp-freecad-core

mkdir -p ~/.local/share/FreeCAD/Mod ~/.local/share/FreeCAD/v1-1/Mod ~/.FreeCAD/Mod
cp -R /tmp/mcp-freecad-core/addon/FreeCADMCP ~/.local/share/FreeCAD/Mod/FreeCADMCP
cp -R /tmp/mcp-freecad-core/addon/FreeCADMCP ~/.local/share/FreeCAD/v1-1/Mod/FreeCADMCP
cp -R /tmp/mcp-freecad-core/addon/FreeCADMCP ~/.FreeCAD/Mod/FreeCADMCP

for dir in ~/.local/share/FreeCAD ~/.local/share/FreeCAD/v1-1 ~/.FreeCAD; do
  mkdir -p "$dir"
  printf '{"remote_enabled": false, "allowed_ips": "127.0.0.1", "auto_start_rpc": true}\n' \
    > "$dir/freecad_mcp_settings.json"
done
```

Start FreeCAD under Xvfb:

```bash
xvfb-run -a /tmp/freecad-appimage/squashfs-root/usr/bin/freecad
```

Validation probes:

- Wait for `localhost:9875` to accept connections.
- `initialize`
- `notifications/initialized`
- `tools/list`
- `create_document` with `{"name":"WrightDoc"}`
- `create_object` with `doc_name=WrightDoc`, `obj_type=Part::Box`,
  `obj_name=WrightBox`, and `obj_properties` of 10 x 8 x 6 mm.
- `get_objects` with `{"doc_name":"WrightDoc"}`.

Known result:

- Repository commit `63acb305573194a011641ab13ccfb391fe95769f`.
- Package version `freecad-mcp` 0.1.18.
- No upstream test directory or `test_*.py` files were present in the cloned
  source.
- `uv tool run --from /tmp/freecad-nekanat-src freecad-mcp --help` built the
  source package and showed `--only-text-feedback` and `--host`.
- Ubuntu 24.04 `apt install freecad` had no package candidate in the clean
  validation container, so validation used the FreeCAD Linux x86_64 AppImage.
- FreeCAD 1.1.1 AppImage reported revision `20260414`.
- FreeCAD RPC became ready on localhost port 9875 after 4 seconds.
- MCP serverInfo was `FreeCADMCP` version `1.28.1`.
- MCP listed 14 tools.
- `list_documents` returned `[]`.
- `create_document` created `WrightDoc`.
- `create_object` created `WrightBox`.
- `get_objects` reported `WrightBox` as `Part::Box` with volume `480.0`.

Known notes:

- Without the FreeCAD addon RPC server running, the MCP still initializes and
  lists tools, but backend calls report connection refused. That is the expected
  diagnostic when FreeCAD is not installed or the addon is not running.
- The FreeCAD AppImage emitted locale/fontconfig warnings in the minimal Ubuntu
  container, but those warnings did not block RPC startup or modeling commands.

## FreeCAD Robust (`freecad-robust-spkane`)

Source: https://github.com/spkane/freecad-addon-robust-mcp-server

Run MCP:

```bash
uv tool run --from freecad-robust-mcp freecad-mcp --mode xmlrpc --host 127.0.0.1
```

Source validation:

```bash
git clone https://github.com/spkane/freecad-addon-robust-mcp-server \
  /tmp/freecad-robust-src
cd /tmp/freecad-robust-src
python3 -m venv /tmp/robust-venv
. /tmp/robust-venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
pytest tests/unit -q
```

Install selected-server FreeCAD dependency:

```bash
curl -fL -o FreeCAD.AppImage \
  https://sourceforge.net/projects/free-cad/files/1.1.1/FreeCAD_1.1.1-Linux-x86_64-py311.AppImage/download
chmod +x FreeCAD.AppImage
./FreeCAD.AppImage --appimage-extract
```

Start the FreeCAD-side Robust MCP Bridge in headless XML-RPC mode:

```bash
git clone --depth 1 https://github.com/spkane/freecad-addon-robust-mcp-server \
  /tmp/mcp-freecad-robust

/tmp/freecad-appimage/squashfs-root/usr/bin/freecadcmd \
  /tmp/mcp-freecad-robust/freecad/RobustMCPBridge/freecad_mcp_bridge/blocking_bridge.py
```

Check the MCP can reach FreeCAD:

```bash
FREECAD_MODE=xmlrpc FREECAD_SOCKET_HOST=127.0.0.1 \
  uv tool run --from freecad-robust-mcp freecad-mcp --check
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `create_document` with `{"name":"WrightDoc","label":"Wright Validation Document"}`
- `create_box` with `length=10`, `width=8`, `height=6`,
  `name=WrightBox`, and `doc_name=WrightDoc`
- `list_objects` with `{"doc_name":"WrightDoc"}`

Known result:

- Repository commit `d9a37118a8331e8739ad45fd97d027437984296f`.
- Source package version `0.1.dev1+gd9a37118a`.
- Upstream unit tests passed with 420 tests.
- Ubuntu 24.04 `apt install freecad` had no package candidate in the clean
  validation container, so validation used the FreeCAD Linux x86_64 AppImage.
- The installable PyPI package is `freecad-robust-mcp`; the executable is
  `freecad-mcp`.
- FreeCAD 1.1.1 AppImage reported revision `20260414`.
- `freecad-mcp --check` connected to FreeCAD 1.1.1 in headless XML-RPC mode.
- MCP serverInfo was `freecad-mcp` version `1.28.1`.
- MCP listed 152 tools.
- `get_connection_status` returned connected true in `xmlrpc` mode.
- `get_freecad_version` returned FreeCAD 1.1.1 build
  `20260414 (Git shallow)`.
- `create_document` created `WrightDoc`.
- `create_box` created `WrightBox` as `Part::Box` with volume `480.0`.
- `list_objects` returned `WrightBox`.

Known notes:

- The GitHub repository name is `freecad-addon-robust-mcp-server`, but that is
  not the package name to run with `uv tool run`.
- The FreeCAD-side bridge prints that XML-RPC is available on localhost port
  9875. The direct `freecad-mcp --check` command is the reliable readiness
  check for user setup.
- This validation used headless XML-RPC mode. GUI screenshot/view tools still
  need a separate FreeCAD GUI/Xvfb validation if those capabilities matter.

## FreeCAD Copilot (`freecad-copilot-contextform`)

Source: https://github.com/contextform/freecad-mcp

Installer/package notes:

- The npm package is `freecad-mcp-setup`, not `freecad-mcp`.
- The actual MCP bridge is `working_bridge.py`, normally installed to
  `~/.freecad-mcp/working_bridge.py`.

Run bridge directly:

```bash
uv run --with mcp python working_bridge.py
```

FreeCAD/Xvfb setup:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  xvfb xauth libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0
```

Install workbench:

```bash
mkdir -p ~/.local/share/FreeCAD/v1-1/Mod
cp -R AICopilot ~/.local/share/FreeCAD/v1-1/Mod/AICopilot
xvfb-run -a /tmp/freecad
```

Known result:

- Repository commit `de4fed2a7a4352fcb0de60d2b784063c54eeb812`.
- The setup package is `freecad-mcp-setup` 1.0.8.
- `npm install` and `npm test` passed for the installer.
- `npx freecad-mcp setup` installed the workbench and warned that FreeCAD and
  Claude Code were not detected.
- Ubuntu apt did not provide a `freecad` package candidate.
- FreeCAD 1.1.1 AppImage reported revision `20260414`.
- Installing to `~/.local/share/FreeCAD/Mod/AICopilot` did not start the socket
  for FreeCAD 1.1.
- Installing to `~/.local/share/FreeCAD/v1-1/Mod/AICopilot` started
  `/tmp/freecad_mcp.sock` after 6 seconds.
- MCP initialized as serverInfo `freecad` version `2.0.0`.
- MCP listed 7 tools: `check_freecad_connection`, `test_echo`,
  `partdesign_operations`, `part_operations`, `view_control`,
  `execute_python`, and `continue_selection`.
- `check_freecad_connection` returned `FreeCAD running with AI Copilot
  workbench`.
- `test_echo` returned `Bridge received: wright validation`.
- `part_operations(operation=box, length=10, width=8, height=6,
  name=WrightBox)` timed out after 30 seconds and FreeCAD logged Qt
  cross-thread errors plus `Event observer error: No module named 'PySide2'`.

Follow-up: `docs/mcp-catalog/followups/freecad-copilot-contextform.md`

## AutoCAD MCP (`autocad-mcp-hvkshetry`)

Source: https://github.com/hvkshetry/autocad-mcp

Run headless Linux backend:

```bash
AUTOCAD_MCP_BACKEND=ezdxf \
uv run --with git+https://github.com/hvkshetry/autocad-mcp.git \
  python -m autocad_mcp
```

Upstream test command:

```bash
AUTOCAD_MCP_BACKEND=ezdxf \
uv run --with pytest --with pytest-asyncio \
  pytest tests/test_ezdxf_backend.py tests/test_ipc_protocol.py -q
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `system(operation="status")`
- `drawing(operation="create", data={"name":"wright_validation"})`
- `entity(operation="create_line", x1=0, y1=0, x2=10, y2=0, layer="0")`
- `drawing(operation="info")`
- `drawing(operation="save_as_dxf", data={"path":"/tmp/wright_autocad_validation.dxf"})`

Known result:

- Repository commit `95476a33a1c246308326eb4709d6379ef2efdbc1`.
- 123 upstream tests passed.
- MCP initialized as server `autocad-mcp` version `1.26.0`.
- MCP listed 8 tools.
- `system` reported backend `ezdxf` version `1.4.3`.
- `drawing(create)` created `WrightValidation`.
- `entity(create_line)` created a `LINE` entity on layer `WrightValidation`.
- `drawing(save_as_dxf)` produced `/tmp/wright-autocad-validation.dxf`
  at 15561 bytes.
- `drawing(info)` reported one entity and the `WrightValidation` layer.
- Windows AutoCAD File IPC backend is separate and remains untested in the
  Linux container.

Known notes:

- Use `data: {"path": ...}` for `drawing(save_as_dxf)`. Passing `path` as a
  top-level argument returns a tool-level error.
- Use top-level `x1`, `y1`, `x2`, and `y2` for `entity(create_line)`, not a
  nested `data` object.

## multiCAD MCP (`multicad-mcp-ancode666`)

Source: https://github.com/AnCode666/multiCAD-mcp

Repository command from README:

```powershell
git clone https://github.com/AnCode666/multiCAD-mcp.git
cd multiCAD-mcp
uv sync --dev
uv run python -m pip install --upgrade pywin32
python src/server.py
```

Clean Linux validation probes:

```bash
python3 -m venv /tmp/multicad-venv
. /tmp/multicad-venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e '.[dev]'
```

Known result:

- Repository commit `360ec77c970ec95a962bd4d0a3238715ee78dd7c`.
- Package version `multiCAD-mcp` 0.2.0.
- README requires Windows, Python 3.10+, `pywin32`, and AutoCAD 2018+,
  ZWCAD 2020+, GstarCAD 2020+, or BricsCAD 21+ through Windows COM.
- Exact `pip install -e '.[dev]'` failed on Linux because `pywin32>=300` has
  no Linux distribution.
- Installing the source with `--no-deps` plus non-Windows dependencies worked,
  but upstream unit collection failed with
  `ImportError: AutoCAD adapter requires Windows OS with COM support`.
- `python src/server.py --help` and direct startup both exited before MCP
  initialization with the same Windows COM diagnostic, so `initialize` and
  `tools/list` could not be called in the Linux container.

Expected Windows setup:

- Windows desktop host.
- Python 3.10+ environment with `pywin32`.
- One supported COM-capable CAD application installed: AutoCAD 2018+,
  ZWCAD 2020+, GstarCAD 2020+, or BricsCAD 21+.
- Run `python src/server.py`, then probe `initialize`, `tools/list`,
  `manage_session` with `{"action":"status"}`, and a safe read/list tool before
  attempting drawing or file-writing operations.

## CAD-MCP Universal (`cad-mcp-daobataotie`)

Source: https://github.com/daobataotie/CAD-MCP

Repository command from README:

```bash
python src/server.py
```

Declared dependencies:

```bash
python3 -m venv /tmp/cad-mcp-venv
. /tmp/cad-mcp-venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Known result in the clean Intel Ubuntu container:

- Repository cloned at `352541820a56823568a90993dd773e7014205f44`.
- There are no upstream test files in the cloned repository.
- `requirements.txt` requires `pywin32>=228`, `mcp>=0.1.0`,
  `pydantic>=2.0.0`, and `typing>=3.7.4.3`.
- Dependency installation fails on Python 3.12/Linux with:
  `ERROR: Could not find a version that satisfies the requirement pywin32>=228`
  and `ERROR: No matching distribution found for pywin32>=228`.
- Installing only `mcp>=0.1.0`, `pydantic>=2.0.0`, and `typing>=3.7.4.3`
  succeeds, but `python src/server.py` exits before MCP initialization with:
  `ModuleNotFoundError: No module named 'win32com'`.
- MCP protocol startup cannot be tested in the Ubuntu container because
  `src/cad_controller.py` imports `win32com.client` and `pythoncom` at import
  time.
- Full validation needs Windows, `pywin32`, and a supported AutoCAD, GstarCAD,
  or ZWCAD COM host.

Expected Windows setup:

- Windows desktop host.
- AutoCAD, GstarCAD, or ZWCAD installed and reachable through COM.
- Python environment with `pywin32`.
- Run `python src/server.py`, then probe `initialize`, `tools/list`, and a safe
  read/status command if one is exposed before attempting drawing commands.

## Creo/CadQuery MCP (`creo-mcp`)

Source: https://github.com/yangkunyi/creo-mcp

User install command:

```bash
uvx creo-mcp --authorization "$VOLCENGINE_AUTHORIZATION" \
  --service-resource-id "$VOLCENGINE_SERVICE_RESOURCE_ID"
```

Source validation setup:

```bash
apt-get update
apt-get install -y git python3 python3-venv libgl1
git clone --depth 1 https://github.com/yangkunyi/creo-mcp /tmp/creo-mcp
cd /tmp/creo-mcp
python3 -m venv /tmp/creo-mcp-venv
. /tmp/creo-mcp-venv/bin/activate
pip install --upgrade pip
pip install -e .
creo-mcp --authorization dummy-token --service-resource-id dummy-service
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `execute_python_code` using CadQuery to export a small STEP box
- `open_file_in_cad` against the generated STEP file
- `retrieve_from_knowledge_base` with dummy Volcengine credentials

Known result:

- Repository commit `1a2f164c88c896c0b98a8edec36a7dc4e2eb06ff`.
- There are no upstream test files in the cloned repository.
- The package requires Python 3.12+ and installs CadQuery/OCP plus `creopyson`.
- First MCP startup failed with `ImportError: libGL.so.1: cannot open shared
  object file`; installing `libgl1` fixed startup.
- MCP initialized as server `python-code-executor` version `1.28.1`.
- MCP listed 3 tools: `execute_python_code`, `open_file_in_cad`, and
  `retrieve_from_knowledge_base`.
- `execute_python_code` used CadQuery to export `/tmp/wright_creo_box.step` at
  15418 bytes.
- `open_file_in_cad` reached the expected host boundary:
  `HTTPConnectionPool(host='localhost', port=9056)` connection refused because
  CREOSON/Creo were not running in the container.
- `retrieve_from_knowledge_base` with dummy credentials reached the Volcengine
  endpoint and returned `400 Client Error: Bad Request`.

Known notes:

- This is broader than a Creo-only bridge: local CadQuery STEP generation works
  headlessly, while opening files in Creo requires a local CREOSON server and
  Creo desktop.
- Full knowledge-base validation requires real `VOLCENGINE_AUTHORIZATION` and
  `VOLCENGINE_SERVICE_RESOURCE_ID` values.
- Wright should classify this as `might_work` / `dependency_missing`, not fully
  tested, until Creo, CREOSON, and real Volcengine credentials are available.

## CREOSON Bridge (`creoson-mcp-bridge`)

Source: https://github.com/SimplifiedLogic/creoson

Latest release validated:

- Git commit: `1939a585a1fcc94b6c05586af92c2da00adebdb0`
- Release: `v3.0.1`
- Asset: `CreosonServer-3.0.1-win64.zip`

Expected non-MCP setup:

```bash
curl -L -o CreosonServer-3.0.1-win64.zip \
  https://github.com/SimplifiedLogic/creoson/releases/download/v3.0.1/CreosonServer-3.0.1-win64.zip
unzip CreosonServer-3.0.1-win64.zip
```

Known result in the clean Intel Ubuntu container:

- Source clone succeeded.
- Source build instructions require a Creo installation with JLINK
  `text/java/pfcasync.jar`, CreosonSetup ZIPs, Commons Codec, Jackson jars, and
  an output directory.
- Release download succeeded.
- Release ZIP contains `CreosonServer-3.0.0.jar`, support JARs,
  `creoson_run.bat`, and `jshellnative.dll`.
- `java -jar CreosonServer-3.0.0.jar` failed with
  `no main manifest attribute`.
- The actual Java main class is
  `com.simplifiedlogic.nitro.jshell.MainServer`.
- Calling the main class with the release JARs failed with
  `NoClassDefFoundError: com/ptc/cipjava/jxthrowable`, which is the expected
  missing Creo/JLINK Java dependency.
- No MCP `initialize` or `tools/list` calls could be made because CREOSON is a
  JSON/JLINK micro-server, not an MCP stdio/SSE server.

Classification:

- `blocked` / `capability_alias`.
- Keep CREOSON as a dependency for Creo MCPs unless a real MCP wrapper is added
  later.

## Easy-MCP-AutoCAD (`easy-mcp-autocad`)

Source: https://github.com/zh19980811/Easy-MCP-AutoCad

Repository command from README:

```bash
python server.py
```

Declared install paths:

```bash
uv venv --python 3.13 /tmp/easy-autocad-venv313
. /tmp/easy-autocad-venv313/bin/activate
uv pip install -r requirements.txt
# or
uv pip install -e .
```

Known result in the clean Intel Ubuntu container:

- Repository cloned at `332215b91e976c1738dfd3940e9f9770c0fd5856`.
- README requires Windows OS and AutoCAD 2018+ with COM support.
- `server.py` imports `win32com.client` at module import time.
- `requirements.txt` and `pyproject.toml` both require Windows-only COM
  dependencies, including `pywin32`.
- `pip install -r requirements.txt` fails on Linux because `pywin32` has no
  Linux wheels.
- `uv pip install -e .` with Python 3.13 fails because `pywin32>=309` only
  provides `win32`, `win_amd64`, and `win_arm64` wheels.
- After installing only non-Windows dependencies, direct `python server.py`
  fails immediately with `ModuleNotFoundError: No module named 'win32com'`.

Expected Windows setup:

- Windows desktop host.
- AutoCAD 2018+ installed with COM support.
- Python 3.13+ environment, matching upstream `pyproject.toml`.
- Install dependencies and run `python server.py`.
- Probe `initialize`, `tools/list`, then prefer a read-only database/query or
  drawing-inspection tool before issuing drawing commands.

## RhinoMCP (`rhino-mcp-mcneel`)

Source: https://github.com/jingcheng-chen/rhinomcp

Run MCP:

```bash
uvx rhinomcp
```

Source validation:

```bash
git clone https://github.com/jingcheng-chen/rhinomcp /tmp/rhino-src
cd /tmp/rhino-src/server
uv sync --extra dev
uv run pytest -q ../contracts/test_schemas.py tests
```

Expected Rhino bridge setup:

- Install Rhino 8 on Windows or macOS.
- Install the RhinoMCP plugin from Rhino Package Manager or the upstream repo.
- Start Rhino and run the Rhino command `mcpstart`.
- The Python stdio server connects to the Rhino bridge on `127.0.0.1:1999` by
  default. Set `RHINO_MCP_HOST` when the bridge is on another host.

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `get_commands`
- `get_document_summary`
- `create_object` with a small box or other safe primitive after a Rhino bridge
  is available.

Known result:

- Repository commit `b56338a9da733d17555744ab895facdc84a80542`.
- Python package `rhinomcp` version 0.3.1.
- Upstream Python/contract tests passed 192/192 with 12 pytest return-value
  warnings.
- MCP initialized as serverInfo `RhinoMCP` version `1.26.0`.
- MCP listed 66 tools.
- Without Rhino 8 plus `mcpstart`, `get_commands`, `get_document_summary`, and
  backend-touching `create_object` returned:
  `Could not connect to Rhino at 127.0.0.1:1999. Please start Rhino, run the Rhino command mcpstart, then retry the MCP request.`

## SketchUp MCP (`sketchup-mcp-mhyrr`)

Source: https://github.com/mhyrr/sketchup-mcp

Run MCP:

```bash
uvx sketchup-mcp
```

Install selected-server SketchUp dependency:

- Install SketchUp desktop.
- Install the repository's `.rbz`/Ruby extension in SketchUp Extension Manager.
- In SketchUp, run `Extensions > SketchupMCP > Start Server`.
- The extension server listens on the default port 9876.

Source validation:

```bash
git clone https://github.com/mhyrr/sketchup-mcp /tmp/sketchup-src
cd /tmp/sketchup-src
uv tool run --from /tmp/sketchup-src sketchup-mcp
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `get_selection`
- `eval_ruby` with a read-only Ruby expression first; use mutating Ruby only
  after the extension server is confirmed.

Known result:

- Repository commit `aa096f04d3d7b22a70860368f2b576343feac405`.
- Python package `sketchup-mcp` version 0.1.17.
- The repo has no real pytest suite. `test_eval_ruby.py` is a script and
  pytest reports no tests; `examples/simple_test.py` fails to collect because
  it imports removed `mcp.client.Client`.
- `uv tool run --from /tmp/sketchup-src sketchup-mcp --help` built the source
  package but started the MCP server rather than printing CLI help.
- MCP initialized as serverInfo `SketchupMCP` version `1.28.1`.
- MCP listed 10 tools:
  `create_component`, `delete_component`, `transform_component`,
  `get_selection`, `set_material`, `export_scene`, `create_mortise_tenon`,
  `create_dovetail`, `create_finger_joint`, and `eval_ruby`.
- README-advertised `get_scene_info` is not in `tools/list`.
- Without SketchUp plus the extension server, `get_selection` returned:
  `Error getting selection: Could not connect to Sketchup. Make sure the Sketchup extension is running.`
- Backend-touching `eval_ruby` returned JSON `success: false` with the same
  missing-extension diagnostic.

## WebMCP OpenSCAD (`webmcp-openscad-jherr`)

Source: https://github.com/jherr/webmcp-openscad

Install and build the browser app:

```bash
git clone https://github.com/jherr/webmcp-openscad /tmp/webmcp-openscad-src
cd /tmp/webmcp-openscad-src
npm install -g pnpm
pnpm install --frozen-lockfile
pnpm build
node .output/server/index.mjs
```

Run the MCP-B local relay:

```bash
npx -y @mcp-b/webmcp-local-relay@latest
```

Expected browser setup:

- Open the built app in a browser tab.
- Connect the page through MCP-B Chrome extension, the MCP-B local relay embed,
  or native browser WebMCP when available.
- The page registers 16 OpenSCAD tools on `navigator.modelContext`.

Validation probes:

- Relay MCP `initialize`
- `notifications/initialized`
- Relay MCP `tools/list`
- `webmcp_list_sources`
- `webmcp_list_tools`
- After a browser page is connected, call page tools such as `get_source`,
  `render`, `get_render_status`, and `export_stl`.

Known result:

- Repository commit `a3acb68578701001f0251459c75716a55aadfa10`.
- Ubuntu 24.04 default Node 18 could not run pnpm 11.9.0; validation installed
  Node 22.23.1 with `n` after adding `curl`.
- `pnpm install --frozen-lockfile` succeeded with pnpm 11.9.0.
- `pnpm test` is not a usable upstream suite today: Vitest found no test files
  and exited 1, with additional Vite shutdown noise
  `ReferenceError: module is not defined`.
- `pnpm build` succeeded for the TanStack/Nitro app.
- Serving `node .output/server/index.mjs` produced a 7156-byte HTML page titled
  `scad-webmcp · agent-driven parametric CAD` that embeds
  `@mcp-b/webmcp-local-relay@latest/dist/browser/embed.js`.
- MCP stdio probing `npx -y @mcp-b/webmcp-local-relay@latest` initialized as
  serverInfo `webmcp-local-relay` version `0.0.0`.
- The relay listed 4 tools:
  `webmcp_call_tool`, `webmcp_list_sources`, `webmcp_list_tools`, and
  `webmcp_open_page`.
- `webmcp_list_sources` and `webmcp_list_tools` returned zero sources/tools
  because no browser tab was connected inside the headless container.
- Classify as `might_work` / `dependency_missing` until the browser page's
  advertised 16 OpenSCAD tools can be validated through a connected WebMCP
  browser source.

## Web3D MCP (`web3d-mcp-r3f`)

Source: https://github.com/dev261004/web3d-mcp-server

Install selected-server runtime:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends ca-certificates curl git nodejs npm
npm install -g n
n 22
hash -r
```

Install and build from source:

```bash
git clone https://github.com/dev261004/web3d-mcp-server /tmp/web3d-mcp-server
cd /tmp/web3d-mcp-server
npm install
npm test -- --runInBand
npm run build
```

Run MCP:

```bash
node dist/server.js
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `generate_scene` with `scene_plan.objects=["cube"]`
- `validate_scene` on the generated `scene_data`
- `preview` on the generated `scene_data`
- `generate_r3f_code` with `framework=vite` and `typing=typescript`

Known result:

- Configured seed command `npx web3d-mcp` is invalid: npm returned 404 for both
  `web3d-mcp` and `web3d-mcp-server`.
- Configured seed URL `https://web3d-mcp.dev` did not resolve in DNS.
- Reddit/LobeHub source discovery mapped the entry to
  `https://github.com/dev261004/web3d-mcp-server`.
- Repository commit `b6e3cb59ba243ab53be2e1b1a674e5199bfc0c6a`.
- Ubuntu Node 18.19.1 could install, build, and run health checks, but direct
  MCP startup failed with `ReferenceError: File is not defined` from `undici`.
- Node 22.23.1 fixed MCP startup in the clean Intel Ubuntu container.
- `npm test -- --runInBand` passed 10 suites and 65 tests.
- `npm run build` prechecks passed 7 health suites and 54 tests, then compiled
  `dist/server.js`.
- npm audit reported 33 vulnerabilities in installed dependencies.
- MCP uses newline-delimited JSON over stdio, not `Content-Length` framing.
- MCP initialized as serverInfo `3d-scene-mcp` version `1.0.0`.
- MCP listed 12 tools:
  `refine_prompt`, `generate_scene_plan`, `generate_scene`, `preview`,
  `validate_scene`, `edit_scene`, `apply_animation`, `optimize_for_web`,
  `generate_r3f_code`, `export_asset`, `synthesize_geometry`, and
  `integration_help`.
- `generate_scene` created a cube scene with a stable `scene_id`.
- `validate_scene` returned `is_valid:true` with all 13 validation checks
  passed.
- `preview` returned SVG wireframe data.
- `generate_r3f_code` returned `SUCCESS` with 948 bytes of Vite/TypeScript
  React Three Fiber code.

## Blender MCP (`blender-mcp-ahujasid`)

Source: https://github.com/ahujasid/blender-mcp

Run MCP from a clean Wright container:

```bash
uvx --python 3.11 blender-mcp
```

Install selected-server Blender dependencies:

```bash
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  blender python3-requests xvfb xauth procps
```

Start the Blender add-on under Xvfb:

```bash
git clone --depth 1 https://github.com/ahujasid/blender-mcp /tmp/mcp-blender
cat >/tmp/start_blendermcp.py <<'PY'
import sys
sys.path.insert(0, "/tmp/mcp-blender")
import addon
addon.register()
print("WRIGHT_BLENDERMCP_RUNNING", flush=True)
PY
xvfb-run -a blender --python /tmp/start_blendermcp.py
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- Without Blender/add-on socket: `get_scene_info` should return
  `Could not connect to Blender. Make sure the Blender addon is running.`
- With Blender/add-on socket: `get_scene_info` should return the default
  scene containing `Cube`, `Light`, and `Camera`.
- With Blender/add-on socket: `execute_blender_code` can create a temporary
  cube and `get_object_info` should verify its mesh data.

Known notes:

- Repository commit `6e99eb5a442b83766a5796975ec7bb5bfc791341`.
- There are no upstream test files in the cloned repository.
- Clean Intel Ubuntu validation installed `uv`/`uvx` 0.11.25 using the official
  installer and used `uvx --python 3.11 blender-mcp`.
- The package downloaded CPython 3.11.15 and installed 37 Python packages.
- MCP initialized as server `BlenderMCP` version `1.28.1`.
- MCP lists 22 tools, including `get_scene_info`, `get_object_info`,
  `get_viewport_screenshot`, `execute_blender_code`, Poly Haven tools,
  Sketchfab tools, Hyper3D tools, and Hunyuan3D tools.
- The add-on refuses `blender -b` background mode because commands would not
  execute. Use a normal Blender process inside `xvfb-run`.
- Ubuntu 24.04 installed Blender 4.0.2. Its Python environment did not include
  `requests` by default. Install `python3-requests` before loading `addon.py`.
- Backend validation created `WrightValidationCube` at `(1.0, 2.0, 3.0)` and
  verified it with `get_object_info`: 8 vertices, 12 edges, 6 polygons.
- Cloud/asset features such as Poly Haven, Sketchfab, Hyper3D, and Hunyuan3D
  were disabled for this local backend validation and still need separate
  credential/network testing.

## Fusion 360 MCP (`fusion360-mcp-faust`)

Source: https://github.com/faust-machines/fusion360-mcp-server

Run package:

```bash
uv run --with fusion360-mcp-server fusion360-mcp-server --mode socket
```

Run mock mode:

```bash
uv run --with fusion360-mcp-server fusion360-mcp-server --mode mock
```

Upstream test command:

```bash
uv sync --dev
uv run pytest -q
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- Mock mode: `ping`, `create_box`
- Socket mode without Fusion: `ping`

Known result:

- Repository commit `b44b667e440da070081795cfcbfaf75de2a44251`.
- 282 upstream tests passed.
- Mock mode initialized as server `fusion360-mcp-server` version `1.26.0`,
  listed 85 tools, `ping` returned `pong`, and `create_box` with
  `length`, `width`, and `height` returned mock deltas.
- Socket mode listed 85 tools, and `ping` returned the expected error:
  `Not connected to Fusion 360. Make sure the add-in is running.`
- Full validation requires Autodesk Fusion 360 and the `Fusion360MCP` add-in on
  Windows or macOS. Fusion 360 is not installed or testable inside the Intel
  Ubuntu container.

Known notes:

- `create_box` requires `length`, `width`, and `height`. A `depth` argument is
  rejected by the MCP schema.

## Fusion 360 Python API Bridge (`autodesk-fusion-mcp-python`)

Source: https://github.com/sockcymbal/autodesk-fusion-mcp-python

Setup:

```bash
git clone --depth 1 https://github.com/sockcymbal/autodesk-fusion-mcp-python /tmp/autodesk-fusion-mcp-python
cd /tmp/autodesk-fusion-mcp-python
python3 -m venv /tmp/fusion-python-venv
. /tmp/fusion-python-venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Run MCP:

```bash
APS_CLIENT_ID=... \
APS_CLIENT_SECRET=... \
FUSION_ACTIVITY_ID=... \
python fusion_mcp.py
```

Validation probes:

- No-credential startup
- `initialize`
- `notifications/initialized`
- `tools/list`
- `generate_cube`

Known result:

- Repository commit `a3398ac5c76baa252240f301167a4cba2fe6f5b8`.
- No upstream tests were present.
- The seeded `python main.py` command is stale; no `main.py` exists. The MCP
  script is `fusion_mcp.py`.
- Without APS env vars, startup exits with `KeyError: 'APS_CLIENT_ID'`.
- With dummy `APS_CLIENT_ID`, `APS_CLIENT_SECRET`, and `FUSION_ACTIVITY_ID`,
  MCP initialized as server `fusion` version `1.28.1`.
- MCP listed 1 tool: `generate_cube`.
- `generate_cube` failed before making an APS request:
  `'BasicAuth' object has no attribute 'auth_header'`.

Known notes:

- This is currently `non_working` / `failed`, not merely
  `dependency_missing`, because the only MCP backend tool fails due a code bug
  before reaching APS credentials or Fusion 360.
- The repository also includes `fusion_server.py` and a `LiveCube` Fusion add-in
  for a local Fusion workflow, but the MCP tool path in `fusion_mcp.py` is APS
  Design Automation based.

Follow-up: `docs/mcp-catalog/followups/autodesk-fusion-mcp-python.md`

## Revit MCP (`revit-mcp-servers`)

Source: https://github.com/mcp-servers-for-revit/revit-mcp

Setup:

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends git curl ca-certificates nodejs npm build-essential
git clone --depth 1 https://github.com/mcp-servers-for-revit/revit-mcp /tmp/revit-mcp
cd /tmp/revit-mcp
npm install
npm run build
node build/index.js
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `say_hello`

Known result:

- Repository commit `c9ef49e4c397298d291304f822b89ba3a102e6bf`.
- Repository README says this repo is being archived in favor of
  https://github.com/mcp-servers-for-revit/mcp-servers-for-revit.
- `npm install` first failed because `better-sqlite3` needed native
  compilation and `make` was missing; installing `build-essential` fixed the
  install. `npm run build` then succeeded.
- There is no upstream `npm test` script.
- Use newline-delimited JSON over stdio for this server.
- MCP initialized as `revit-mcp` version `1.0.0` and listed 25 tools.
- `say_hello` returned `Say hello failed: connect to revit client failed`, and
  `get_current_view_info` returned `get current view info failed: connect to
  revit client failed`. Stderr logged `connect ECONNREFUSED ::1:8080`.
- Full validation requires Autodesk Revit desktop and the `revit-mcp-plugin`,
  which are Windows-only and unavailable in the Intel Ubuntu container.

## Autodesk APS Official (`autodesk-aps-official`)

Source: https://github.com/autodesk-platform-services/aps-mcp-server-nodejs

Setup:

```bash
npm install
node server.js
```

Required credentials:

- `APS_CLIENT_ID`
- `APS_CLIENT_SECRET`
- `SSA_ID`
- `SSA_KEY_ID`
- `SSA_KEY_PATH`

Known result:

- Repository commit `722591abb08c42000e9aedcabc746bbd7f413739`.
- `npm install` succeeds in the clean Intel Ubuntu container.
- There is no `npm test` script.
- Without credentials, `node server.js` exits before MCP startup with:
  `Missing one or more required environment variables: APS_CLIENT_ID,
  APS_CLIENT_SECRET, SSA_ID, SSA_KEY_ID, SSA_KEY_PATH`.
- With dummy APS variables and a generated dummy RSA PEM key, MCP initializes
  as server `aps-mcp-server-nodejs` version `0.0.1`.
- MCP lists 4 tools:
  `getFolderContentsTool`, `getIssueTypesTool`, `getIssuesTool`, and
  `getProjectsTool`.
- `getProjectsTool` reaches Autodesk auth and returns `AUTH-001` for the
  dummy client, proving the server runs until the real credential boundary.
- Full API-backed validation needs Autodesk APS server-to-server credentials,
  a Secure Service Account, a private key PEM file, and ACC project access.

Known notes:

- Installing Ubuntu's `npm` package pulls in a large dependency set and can
  exceed a short command timeout. Check for active `apt`/`dpkg` processes
  before retrying.

## Autodesk APS Community (`autodesk-aps-petrbroz`)

Source: https://github.com/petrbroz/aps-mcp-server

Known setup:

```bash
yarn install --frozen-lockfile
yarn run build
node build/server.js
```

Known notes:

- Repository commit `557556235e806a5d74265fcf556b9dae4206abdd`.
- README states the project moved to
  https://github.com/autodesk-platform-services/aps-mcp-server-nodejs.
- `yarn install --frozen-lockfile` succeeds in the clean Intel Ubuntu
  container after installing `yarn` 1.22.22 with `npm install -g yarn`.
- `yarn run build` succeeds.
- There is no `yarn test` script.
- Server exits before MCP startup if these are missing:
  `APS_CLIENT_ID`, `APS_CLIENT_SECRET`, `APS_SA_ID`, `APS_SA_EMAIL`,
  `APS_SA_KEY_ID`, `APS_SA_PRIVATE_KEY`.
- With dummy APS variables and a generated base64 RSA private key, MCP
  initializes as server `autodesk-platform-services` version `0.0.1`.
- MCP lists 8 tools: `get-accounts`, `get-folder-contents`,
  `get-issue-comments`, `get-issue-root-causes`, `get-issue-types`,
  `get-issues`, `get-item-versions`, and `get-projects`.
- `get-accounts` reaches Autodesk auth and returns `AUTH-001` for the dummy
  client, proving the server runs until the real credential boundary.
- Treat this entry as blocked/superseded and steer users to the official APS
  Node MCP unless the old repo later regains unique supported behavior.

## Siemens Element MCP (`siemens-element-mcp`)

Source: https://element.siemens.io/get-started/element-mcp/

Package: `@siemens/element-mcp@49.12.0-v.1.11.1`

Setup:

```bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends curl ca-certificates nodejs npm
mkdir element-project
cd element-project
npm init -y
npm install --save-dev --save-exact @siemens/element-mcp@49.12.0-v.1.11.1
npx @siemens/element-mcp
```

Configuration:

```bash
export SDL_MCP_TOKEN_ENV=true
export OPENAI_API_KEY=<siemens-llm-token-with-llm-scope>
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `element-search` with `button component`
- `element-icon-search` with `settings`

Known result:

- npm package version `49.12.0-v.1.11.1`.
- Package tarball:
  `https://registry.npmjs.org/@siemens/element-mcp/-/element-mcp-49.12.0-v.1.11.1.tgz`.
- Package metadata points to `https://code.siemens.com/ux/sdl-mcp`; the npm
  artifact does not include a public commit hash.
- There is no upstream test script in the package.
- A fresh `npx -y @siemens/element-mcp` failed before local project install
  with `element-mcp: not found`; after project install, `npx
  @siemens/element-mcp`, `npx element-mcp`, and `npm exec -- element-mcp` all
  worked.
- MCP initialized as `@siemens/element-mcp` version `1.0.0`.
- MCP listed 2 tools: `element-search` and `element-icon-search`.
- Without a Siemens token, both tools reached the cloud embeddings credential
  boundary and returned `Embedding API error: 403 Forbidden`.
- `element-mcp check` reported `LLM token not found. Run 'element-mcp
  setup-token'`.
- Full validation requires a Siemens LLM token with `llm` scope.

## Siemens WinCC Unified MCP (`wincc-unified-mcp`)

Source: https://support.industry.siemens.com/cs/document/110002407

Expected official artifact:

- Siemens Support Entry ID `110002407`
- `Integration of MCP Server with WinCC Unified PC Runtime`
- Login-gated `110002407_MCPServerPCRuntime_READMEOSS.zip`

Catalog command:

```bash
wincc-unified-mcp.exe
```

Known result:

- Public search results confirm the support entry exists and describe a WinCC
  Unified PC Runtime MCP Server, but the package download is login-gated.
- Direct container requests to the support page and PDF attachment returned
  HTTP 403 from Akamai:
  `https://support.industry.siemens.com/cs/document/110002407/...`
  and
  `https://support.industry.siemens.com/cs/attachments/110002407/110002407_WinCC_Unified_PCRT_MCP_Server_Docu_V1.0.pdf`.
- `npm view wincc-unified-mcp` and `npm view
  @siemens/wincc-unified-mcp` returned npm 404.
- `pip index versions wincc-unified-mcp` and `pip index versions
  wincc_unified_mcp` found no matching distribution.
- `wincc-unified-mcp.exe --help` failed with `command not found` in the clean
  Intel Ubuntu container.
- Guessed Siemens GitHub repository URLs did not resolve publicly without
  authentication.
- No MCP stdio calls could be made because no installable official artifact was
  available.

Classification:

- `blocked` until a Siemens Support login/license holder obtains the official
  artifact and validates it on Windows with WinCC Unified PC Runtime.

## PTC ThingWorx MCP (`thingworx-mcp`)

Source: https://support.ptc.com/help/thingworx/platform/r10.1/

Client endpoint:

```text
${THINGWORX_BASE_URL}/mcp
```

Configuration:

```bash
export THINGWORX_BASE_URL=https://your-thingworx-host.example.com
export THINGWORX_APP_KEY=<thingworx-app-key>
# or provide an OAuth bearer token for deployments using OAuth-protected MCP metadata
export THINGWORX_OAUTH_TOKEN=<thingworx-oauth-token>
```

Known result:

- PTC ThingWorx 10.1 MCP documentation pages returned HTTP 200 in the clean
  Intel Ubuntu container.
- PTC docs describe configuring an MCP client with an HTTP/SSE endpoint:
  `<ThingWorx Server URL>/mcp`.
- PTC docs describe managing exposed tools, resources, and prompts through the
  `MCPServices` resource.
- No standalone package exists for the catalog's old local command:
  `npm view ptc-thingworx-mcp`, `npm view thingworx-mcp`, and `npm view
  @ptc/thingworx-mcp` all returned npm 404.
- `pip index versions ptc-thingworx-mcp` and `pip index versions
  thingworx-mcp` found no matching distribution.
- `ptc-thingworx-mcp --help` failed with `command not found`.
- A separate community repository exists:
  `https://github.com/doubleSlashde/thingworx-mcp-server` at commit
  `7e22ef9be1af495acf1a46101ebb17380eed86ae`. That repository was not
  substituted for the official PTC product-hosted entry in this pass.
- No MCP calls could be made without a live ThingWorx 10.1+ MCP endpoint and
  credentials.

Classification:

- `might_work` / `dependency_missing` for the official product-hosted MCP.
- Requires a ThingWorx 10.1+ server with MCP enabled and either AppKey or OAuth
  credentials before tool discovery/backend operations can be validated.

## KiCad MCP (`kicad-mcp-lamaalrajih`)

Source: https://github.com/lamaalrajih/kicad-mcp

Install-style command:

```bash
uv tool run --from git+https://github.com/lamaalrajih/kicad-mcp.git kicad-mcp
```

Repository setup:

```bash
git clone --depth 1 https://github.com/lamaalrajih/kicad-mcp /tmp/kicad-mcp
cd /tmp/kicad-mcp
uv sync --group dev
uv run kicad-mcp
```

Configuration:

```bash
export KICAD_SEARCH_PATHS=/path/to/kicad/projects
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `list_projects`
- `get_project_structure`
- Backend-touching probe attempted: `run_drc_check`

Known result:

- Repository commit `98c9ea41cb393393a8bafd157a93e84431e00afb`.
- GitHub package command installed and started the MCP server.
- MCP initialized as server `KiCad` version `1.11.0`.
- MCP listed 16 tools.
- `list_projects` found the sample `WrightBoard` project.
- `get_project_structure` returned the sample `.kicad_pro`, `.kicad_pcb`, and
  `.kicad_sch` files.

Known problems:

- The README/catalog `python main.py` path raised
  `ValueError: a coroutine was expected, got None`.
- 11 of 16 tools expose `ctx` as a required input property, including DRC, BOM,
  netlist, thumbnail, and pattern-analysis tools.
- `run_drc_check` failed normal MCP client validation with
  `Input validation error: 'ctx' is a required property`.
- `uv run pytest -q` failed the configured 80% coverage gate at 10.04% total
  coverage, though `uv run pytest -q --no-cov` passed with 37 passed and 2
  skipped.
- Ubuntu 24.04 default apt provides KiCad 7.0.11, while upstream requires KiCad
  9.0+. Full KiCad CLI validation should wait until the MCP schema issue is
  fixed.

Follow-up: `docs/mcp-catalog/followups/kicad-mcp-lamaalrajih.md`

## ROSBag MCP (`rosbag-mcp-binabik`)

Source: https://github.com/binabik-ai/mcp-rosbags

Setup:

```bash
git clone --depth 1 https://github.com/binabik-ai/mcp-rosbags /tmp/rosbag-mcp
cd /tmp/rosbag-mcp
uv venv
uv pip install -r requirements.txt
uv pip install --reinstall rosbags==0.10.10
```

Run MCP:

```bash
PYTHONPATH=/tmp/rosbag-mcp/src \
MCP_ROSBAG_DIR=/path/to/rosbags \
MCP_ROSBAG_CONFIG=/tmp/rosbag-mcp/src/config \
  /tmp/rosbag-mcp/.venv/bin/python /tmp/rosbag-mcp/src/server.py
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `list_bags`
- `bag_info`
- `get_message_at_time`

Known result:

- Repository commit `9b6b3b7a7b10d2ef004c1b50d38395d07e0b47b6`.
- MCP initialized as server `rosbag-memory` version `1.28.1`.
- MCP listed 15 tools.
- A generated ROS 2 bag `wright_chatter` contained two `/chatter`
  `std_msgs/msg/String` messages.
- `list_bags` found `wright_chatter`.
- `bag_info` reported `/chatter`, 2 messages, and 1 second duration.
- `get_message_at_time` returned message data `hello`.

Known notes:

- No published `mcp-rosbags` or `mcp_rosbags` tool package was found in the
  Python registry during validation.
- The documented source path works, but `PYTHONPATH` must include
  `/tmp/rosbag-mcp/src`.
- `requirements.txt` currently leaves `rosbags` unpinned. The latest resolved
  version, `rosbags==0.11.3`, failed at MCP startup because
  `rosbags.serde.deserialize_cdr` is no longer exported.
- Pinning `rosbags==0.10.10` restored the API and read the generated ROS 2 bag.

## OASiS Open FEM Agent (`oasis-open-fem-agent`)

Source: https://github.com/Hereon-InstituteMS/OASiS

Legacy/search names:

- Open FEM Agent
- Open-FEM-agent

Setup:

```bash
git clone --depth 1 https://github.com/Hereon-InstituteMS/OASiS /tmp/oasis
cd /tmp/oasis
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Validated lightweight backend:

```bash
pip install scikit-fem
```

Run MCP:

```bash
PYVISTA_OFF_SCREEN=true /tmp/oasis/.venv/bin/python -m server
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `discover`
- `prepare_simulation` with `solver=skfem`, `physics=poisson`
- `run_simulation` with `solver=skfem` and a fixed Poisson smoke script
- Upstream focused tests: `PYTHONPATH=src PYVISTA_OFF_SCREEN=true pytest tests/test_mcp_stdio.py -q`

Known result:

- Repository commit `117c35769c0eb00181db003e8dcdc305546b08b7`.
- MCP initialized as server `OASiS` version `1.28.1`.
- MCP listed 15 tools.
- With only the base package installed, `discover` returned clear
  not-installed diagnostics for optional backends including FEniCSx, deal.II,
  FEBio, NGSolve, scikit-fem, Kratos, DUNE-fem, and 4C.
- After installing `scikit-fem==12.0.2`, `discover` reported `skfem`
  available.
- `prepare_simulation` returned Poisson knowledge and pitfalls for `skfem`.
- `run_simulation` completed a scikit-fem Poisson solve in 0.46 seconds,
  wrote `result.vtu`, and reported `max_phi 0.07389930610869422`.
- Upstream focused MCP stdio tests passed: 5 passed.

Known notes:

- The original research name `Open FEM Agent` now redirects to the canonical
  OASiS repository.
- `pip install -e .` does not install the upstream test runner. Install
  `pytest` before running upstream tests.
- Do not install every advertised solver backend by default. Install only the
  backend the user selects. The Linux x64 catalog validation fully tested the
  lightweight `scikit-fem` backend; other backends remain optional and
  backend-specific.

## SolidWorks API Docs (`solidworks-api-docs`)

Source: https://github.com/kilwizac/solidworks-api-mcp

Setup:

```bash
apt-get update
apt-get install -y git python3 curl ca-certificates unzip
curl -fsSL https://bun.sh/install | bash
export PATH=/root/.bun/bin:$PATH
git clone --depth 1 https://github.com/kilwizac/solidworks-api-mcp /tmp/solidworks-api-mcp
cd /tmp/solidworks-api-mcp
bun install
```

Run validation:

```bash
bun run typecheck
bun run test
```

Run MCP:

```bash
SW_API_DATA_ROOT=/tmp/solidworks-api-mcp/solidworks-api \
  bun run start
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `solidworks_search_api`
- `solidworks_get_interface_members`
- `solidworks_lookup_method`
- `solidworks_get_examples`

Known result:

- Repository commit `f5a0ccf63337187695b3461cb750977be7d860f6`.
- Bun version `1.3.14`.
- `bun run typecheck` passed.
- `bun run test` passed with 40 tests.
- MCP initialized as server `solidworks-mcp` version `0.1.0`.
- MCP listed 6 tools.
- `solidworks_search_api` found `ISldWorks.OpenDoc6` from the local
  documentation corpus.
- `solidworks_get_interface_members` listed 333 members for `ISldWorks`.
- `solidworks_lookup_method` returned structured documentation for
  `ISldWorks.OpenDoc6`.
- `solidworks_get_examples` returned OpenDoc6 examples.

Known notes:

- This is a read-only documentation/search MCP. It does not require SolidWorks
  desktop software.
- The Ubuntu base image needs `unzip` before the Bun installer can run.
- Avoid sourcing `/root/.bashrc` under `set -u`; Bun's installer profile update
  referenced `PS1`. Export `/root/.bun/bin` directly in noninteractive
  validation scripts.

## Onshape MCP (`onshape-mcp-hedless`)

Source: https://github.com/hedless/onshape-mcp

Setup:

```bash
git clone --depth 1 https://github.com/hedless/onshape-mcp /tmp/onshape-mcp
cd /tmp/onshape-mcp
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Run upstream tests:

```bash
pip install -e .[dev]
pytest -q
```

Run MCP:

```bash
ONSHAPE_ACCESS_KEY=... \
ONSHAPE_SECRET_KEY=... \
  /tmp/onshape-mcp/.venv/bin/python -m onshape_mcp.server
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `list_documents`

Known result:

- Repository commit `54d21ccc4a5376f692cddd01959305be01e40a53`.
- MCP initialized as server `onshape-mcp` version `1.28.1`.
- MCP listed 45 tools.
- Without `ONSHAPE_ACCESS_KEY` and `ONSHAPE_SECRET_KEY`, `list_documents`
  returned `API returned 401. Please check your API credentials.`
- Upstream tests passed with 497 tests and 86.28% coverage.

Known notes:

- This is a cloud Onshape MCP. Full CAD operations require real Onshape API
  credentials.
- The server can be installed, started, and tool-listed in a clean Ubuntu
  container without credentials, but catalog validation remains
  `dependency_missing` until credentials are available for a full API workflow.

## Jarvis Onshape MCP (`jarvis-onshape-mcp`)

Source: https://github.com/ReshefElisha/jarvis-onshape-mcp

User install command:

```bash
ONSHAPE_API_KEY=... ONSHAPE_API_SECRET=... \
  uv run --with git+https://github.com/ReshefElisha/jarvis-onshape-mcp.git onshape-mcp
```

Source validation setup:

```bash
git clone --depth 1 https://github.com/ReshefElisha/jarvis-onshape-mcp /tmp/jarvis-onshape-mcp
cd /tmp/jarvis-onshape-mcp
uv sync --extra dev
ONSHAPE_API_KEY=dummy ONSHAPE_API_SECRET=dummy uv run pytest -q
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `list_cached_images`
- `list_documents`
- `create_document` with dummy credentials

Known result:

- Repository commit `b0e725852280ebcfda5d46a4f2ed2d0b720beace`.
- Package version is `onshape-mcp` 1.2.0.
- Upstream tests passed: 698 passed with 3 Pydantic deprecation warnings.
- MCP initialized as server `onshape-mcp` version `1.17.0`.
- MCP listed 69 tools.
- `list_cached_images` returned `No images cached yet. Call
  render_part_studio_views or render_assembly_views first.`
- `list_documents` reached `https://cad.onshape.com/api/v6/documents` and
  returned `API returned 401. Please check your API credentials.` with dummy
  credentials.
- `create_document` reached `https://cad.onshape.com/api/v10/documents` and
  returned `Unauthenticated API request` with dummy credentials.

Known notes:

- This is a real cloud Onshape MCP and should be classified as
  `might_work` / `dependency_missing` until real credentials are available.
- The package and README use `ONSHAPE_API_KEY` and `ONSHAPE_API_SECRET`, not
  the `ONSHAPE_ACCESS_KEY` / `ONSHAPE_SECRET_KEY` names used by
  `hedless/onshape-mcp`.

## Zoo.dev Cloud CAD API (`zoo-dev-cloud-cad` / `zoo-mcp`)

Source: https://github.com/KittyCAD/zoo-mcp

Setup:

```bash
apt-get update
apt-get install -y git curl ca-certificates python3
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH=/root/.local/bin:$PATH
git clone --depth 1 https://github.com/KittyCAD/zoo-mcp /tmp/zoo-mcp
cd /tmp/zoo-mcp
uv sync --dev
```

Run upstream tests without live external-service tests:

```bash
ZOO_API_TOKEN=dummy-token \
  uv run python -c "import pytest; raise SystemExit(pytest.main(['-q', '-m', 'not live']))"
```

Run MCP:

```bash
ZOO_API_TOKEN=... uv run python -m zoo_mcp
```

User install command:

```bash
ZOO_API_TOKEN=... uvx zoo-mcp
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `search_kcl_docs` with query `extrude`
- `calculate_volume` against `tests/data/cube.stl`

Known result:

- Repository commit `0868cac70443f1151226a2a33663730765ad038b`.
- Without `ZOO_API_TOKEN`, startup fails before MCP initialization with
  `No API token provided`.
- With a dummy `ZOO_API_TOKEN`, MCP initialized as server `Zoo MCP Server`
  version `1.27.1`.
- MCP listed 30 tools.
- `search_kcl_docs` returned structured KCL documentation results for
  `extrude`.
- `calculate_volume` reached `https://api.zoo.dev` and returned a clear
  bad-authentication diagnostic with the dummy token.
- Upstream non-live test selection with a dummy token produced 120 passed,
  2 skipped, 6 deselected, and 33 failures from cloud/KCL-engine operations
  that require valid credentials.

Known notes:

- The verified source is a Python/uv stdio MCP, not the previously seeded
  Node package command.
- Full cloud CAD compute, file conversion, snapshots, and KCL execution need a
  real Zoo.dev API token.
- KCL docs and samples are fetched from `zoo.dev` at runtime; they are useful
  local validation probes because they confirm MCP calls work before testing
  paid/cloud CAD operations.

## SolidWorks Python COM (`solidworks-mcp-python`)

Source: https://github.com/andrewbartels1/SolidworksMCP-python

Setup:

```bash
apt-get update
apt-get install -y git curl ca-certificates python3 python3-venv python3-pip
git clone --depth 1 https://github.com/andrewbartels1/SolidworksMCP-python /tmp/solidworks-mcp-python
cd /tmp/solidworks-mcp-python
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e ".[test]"
```

Run upstream tests:

```bash
pytest -q --no-cov \
  tests/solidworks_mcp/test_server.py \
  tests/solidworks_mcp/test_config.py \
  tests/solidworks_mcp/test_version.py \
  tests/solidworks_mcp/test_exceptions.py \
  tests/solidworks_mcp/test_server_cli_fixed.py \
  test_api_response.py \
  test_docs_discovery_run.py \
  test_workflow_fields.py
```

Run MCP:

```bash
python -m solidworks_mcp.server
```

Validation probes:

- `initialize` was not reachable.
- `notifications/initialized` was not reachable.
- `tools/list` was not reachable.

Known result:

- Repository commit `f0858a7b9cf8cb9a7838ddfaa91a706ef6439cab`.
- Package version `solidworks-mcp-python` 1.0.0.
- Dependency resolution installed `pydantic-ai` 2.0.0, `fastmcp` 3.4.2,
  and `mcp` 1.28.1.
- Linux correctly skipped the Windows-only `pywin32`, `pywin32-ctypes`, and
  `comtypes` dependencies.
- Focused upstream tests failed during import because
  `src/solidworks_mcp/server.py` imports
  `pydantic_ai.toolsets.fastmcp.FastMCPToolset`.
- `solidworks-mcp --help` and `python -m solidworks_mcp.server` both failed
  with `ModuleNotFoundError: No module named 'pydantic_ai.toolsets.fastmcp'`.

Known notes:

- This entry is classified as `non_working` / `failed` because the current
  declared Python dependency range breaks before MCP startup.
- Full CAD validation also requires Windows 10/11, SolidWorks, and Windows COM
  after the Python dependency mismatch is fixed.
- The README says Linux/WSL is useful only for docs, tests, and mock-mode
  development, not direct SolidWorks COM automation.

## SolidWorks TypeScript COM (`solidworks-mcp-ts`)

Source: https://github.com/vespo92/SolidworksMCP-TS

Setup:

```bash
apt-get update
apt-get install -y git curl ca-certificates nodejs npm build-essential python3
npm install -g n
n 20
hash -r
git clone --depth 1 https://github.com/vespo92/SolidworksMCP-TS /tmp/solidworks-mcp-ts
cd /tmp/solidworks-mcp-ts
npm install
npm run build
```

Run upstream tests:

```bash
USE_MOCK_SOLIDWORKS=true npm test
```

Run MCP:

```bash
node dist/index.js
```

Validation probes:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `generate_vba_script`
- `create_part`

Known result:

- Repository commit `c50ba5867f1d1632a5f6857a2b4aa5ad9b1838b7`.
- Package version `solidworks-mcp-server` 3.1.3.
- Node version `20.20.2`; npm version `10.8.2`.
- `npm install` completed, with `npm audit` reporting 15 vulnerabilities.
- `npm run build` passed.
- `USE_MOCK_SOLIDWORKS=true npm test` passed with 52 tests across 4 files.
- `npm ls winax --depth=0` reported `winax` 3.6.2.
- MCP initialized as serverInfo `solidworks-mcp-server` version 3.1.3.
- MCP listed 86 tools.
- `generate_vba_script` and `create_part` both returned:
  `The winax native module is not available. SolidWorks COM automation requires
  it on Windows`.
- The underlying Linux load error was
  `Module did not self-register:
  '/tmp/solidworks-mcp-ts/node_modules/winax/build/Release/node_activex.node'`.

Known notes:

- This is a valid stdio MCP package, but it remains `might_work` /
  `dependency_missing` until a Windows/SolidWorks host validates live COM
  operations.
- The README requires Node 20+; Ubuntu 24.04's default Node 18 package is not
  the intended runtime.
- The runtime tool path still reached the winax boundary in Ubuntu even when
  `USE_MOCK_SOLIDWORKS=true`; upstream mock tests pass, but Wright should not
  treat mock tests as backend validation.

## SolidWorks MCP by alisamsam (`solidworks-mcp-alisamsam`)

Source: https://github.com/alisamsam/solidworks-mcp

Setup:

```bash
apt-get update
apt-get install -y git curl ca-certificates python3 python3-venv python3-pip
git clone --depth 1 https://github.com/alisamsam/solidworks-mcp /tmp/solidworks-mcp-alisamsam
cd /tmp/solidworks-mcp-alisamsam
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Run upstream tests:

```bash
# No upstream tests were present in the validated checkout.
```

Run MCP:

```bash
python solidworks_mcp_server.py
```

Validation probes:

- `initialize` was not reachable.
- `notifications/initialized` was not reachable.
- `tools/list` was not reachable.

Known result:

- Repository commit `ee8f42a1a919af5e0fa8d1dcd24270c9983ce027`.
- The documented install path failed at `pip install -r requirements.txt`.
- `asyncio-compat>=0.1.0` has no matching PyPI distribution.
- `pip index versions asyncio-compat` returned no matching distribution.
- `pip index versions pywin32` also returned no matching distribution on Linux.
- After installing only `mcp` and `python-dotenv` to continue as far as
  possible, `python solidworks_mcp_server.py` failed with
  `ModuleNotFoundError: No module named 'win32com'`.

Known notes:

- This entry is classified as `non_working` / `failed` because the documented
  requirements are not installable as written.
- The README advertises 22 tools and requires Windows 10/11 plus SolidWorks
  2023-2025, but Windows validation should wait until the requirements file is
  fixed.
- `pywin32` should be marked as a Windows-only dependency rather than an
  unconditional Linux install requirement.
