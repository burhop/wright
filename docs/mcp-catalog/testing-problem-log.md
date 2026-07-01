# MCP Server Testing Problem Log

## 2026-06-26

Problem:
  Docker Compose could not connect to the selected `desktop-linux` engine:
  `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`.

Solution:
  Started the Docker service and Docker Desktop, then waited for `docker info`
  to report a ready x86_64 engine.

Result:
  Docker reported `Docker ready: 28.5.1 x86_64`.

Problem:
  The Dockerfile included MCP-specific backend tools in the base image path:
  OpenSCAD, Xvfb, a FreeCAD AppImage, `FREECAD_PATH`, and an OpenSCAD wrapper.
  That does not test the user workflow because MCP dependencies would already be
  present before the user selected a server.

Solution:
  Move to a clean base container model. MCP-specific host software is installed
  only inside the per-MCP validation step for the selected server.

Result:
  Fixed. The clean image built successfully and a direct image smoke test showed
  `openscad`, `freecadcmd`, and `openscad-headless` are absent from the base
  runtime.

Problem:
  The first OpenSCAD MCP probe sent MCP messages using `Content-Length` framing.
  The `openscad-mcp` FastMCP stdio transport rejected those lines with JSON parse
  errors.

Solution:
  Switched the validation probe to newline-delimited JSON messages for this
  server.

Result:
  `initialize` and `tools/list` succeeded and returned the OpenSCAD MCP server
  metadata plus 15 tool definitions.

Problem:
  `validate_scad` returned `success: true` and no errors for `cube([1,1,1]);`,
  but also returned `valid: false`, which is ambiguous as a pass/fail signal.

Solution:
  Used clearer backend evidence for catalog validation: `check_openscad` followed
  by `export_model` with `cube([1,1,1]);` to `/tmp/wright-validation-cube.stl`.

Result:
  `check_openscad` reported OpenSCAD 2021.01, and `export_model` produced a
  1449-byte STL file. OpenSCAD Geometry remains fully tested for the Intel Ubuntu
  container path.

Problem:
  Docker Compose could build the image, but the container restarted with
  `exec /entrypoint.sh: no such file or directory`.

Solution:
  Inspected `/entrypoint.sh` inside the built image and found CRLF bytes after
  the shebang (`#!/bin/bash\r\n`). Updated the Dockerfile to strip carriage
  returns from the entrypoint during image build before making it executable.

Result:
  Fixed. The Compose container recreated from the rebuilt image started
  successfully and reached healthy state.

Problem:
  Hermes sync wrote the Wright gateway command using a developer-specific repo
  path (`/home/burhop/repos/wright`). In the Docker container Wright lives at
  `/workspace`, so Hermes would not be able to launch `wrightgateway` from the
  generated config.

Solution:
  Updated Hermes sync to use `WRIGHT_REPO_DIR` when provided, otherwise the
  detected repository root.

Result:
  Fixed. The container generated Hermes config now points `wrightgateway` at
  `/workspace`.

Problem:
  Calling `/api/mcp/servers/openscad-mcp-server/install` discovered the MCP
  tools during startup, then stopped the server because no workspace session was
  provided. The stop path clears active tools, so `/api/mcp/tools` returned zero
  OpenSCAD tools after the installed-inactive flow.

Solution:
  For gateway validation, activated the server through the Wright API and created
  a disposable workspace. The active server path keeps discovered tools available
  for the gateway.

Result:
  `/api/mcp/tools` returned 15 OpenSCAD tools, `/api/gateway/tools` exposed 15
  prefixed `openscadgeometry__*` tools, and the Hermes-facing `wrightgateway`
  MCP listed and called them successfully.

Problem:
  The first full Hermes-equivalent validation needed to prove not just the child
  MCP server, but that Hermes can receive the MCP tool information through
  Wright's gateway.

Solution:
  Launched the exact `wrightgateway` command from Hermes config:
  `uv run --project /workspace python -m tool_registry.gateway`, then sent
  `initialize`, `tools/list`, and `tools/call` messages.

Result:
  `wrightgateway` returned 15 OpenSCAD tools, `check_openscad` reported
  OpenSCAD 2021.01, and `export_model` produced a 1449-byte STL through the
  gateway path.

Problem:
  `OpenSCAD Linter` is seeded with command `uvx openscad-linter-mcp` and source
  URL `https://github.com/topics/cad-3d`. In a clean Intel Ubuntu container,
  `uvx` was not available and the equivalent `uv tool run openscad-linter-mcp
  --help` failed because `openscad-linter-mcp` was not found in the package
  registry. Web search did not find a specific package or repository for this
  linter MCP.

Solution:
  Move the entry to the non-working tier instead of substituting a different
  OpenSCAD server. Record the exact missing-package evidence and create a
  follow-up record for source/package verification.

Result:
  `openscad-linter-trikos529` now has failed Intel Ubuntu validation evidence,
  Linux x64 platform notes, and follow-up record
  `docs/mcp-catalog/followups/openscad-linter-trikos529.md`.

Problem:
  `FreeCAD Engineering` was seeded with a developer-specific command pointing
  at `/home/burhop/repos/wright/packages/freecad_mcp`, but the public upstream
  repository is `https://github.com/sandraschi/freecad-mcp` and now supports
  launching `freecad_mcp.server` directly.

Solution:
  Validate the public install path in a clean Intel Ubuntu container using
  `uv run --with git+https://github.com/sandraschi/freecad-mcp.git python -m
  freecad_mcp.server --mode stdio`, then update the catalog command to that
  source-based launch path.

Result:
  The user-style launch initialized `FreeCAD MCP`, listed 47 tools, and exposed
  `freecad_status`.

Problem:
  `FreeCAD Engineering` cannot be marked fully tested in the base container
  because FreeCAD, CalculiX, OpenFOAM, and PrusaSlicer are selected-server
  backend dependencies rather than Wright base-image dependencies.

Solution:
  Run the safe backend-touching MCP call `freecad_status` instead of installing
  every backend into the base image.

Result:
  `freecad_status` returned `success:false` and `freecad_ok:false` without
  crashing. This pre-FreeCAD pass proved the MCP package/protocol path but did
  not qualify as full backend validation.

Problem:
  Fresh validation of `freecad-engineering-sandraschi` on commit
  `a71f60a71987ac23a65a3bdeda5f71c8f1579efb` found a current CLI-path issue.
  The server help advertises `--freecad-path`, but starting MCP with
  `--freecad-path /tmp/freecadcmd` still left backend calls unable to find
  FreeCAD.

Solution:
  Use `FREECAD_PATH=/tmp/freecadcmd` for the selected-server backend path,
  because the module reads that environment variable at import time.

Result:
  With `--freecad-path /tmp/freecadcmd`, `create_shape` returned
  `FreeCADCmd not found`. With `FREECAD_PATH=/tmp/freecadcmd`, the same tool
  launched FreeCAD 1.1.1, proving the environment variable path is honored.

Problem:
  After installing FreeCAD 1.1.1 as a selected-server dependency in a disposable
  Intel Ubuntu container, `freecad-engineering-sandraschi` still did not pass a
  real backend operation. The MCP server initialized and listed 47 tools, but
  `freecad_status` reported `success:false`/`freecad_ok:false`. Calling
  `create_shape` for a 10 mm box returned `success:true` while stderr said
  `Cannot create a mesh out of a 'Part.Solid'`, and no STL file was produced.

Solution:
  Verified the FreeCAD backend separately with `/tmp/freecadcmd -c`, creating a
  684-byte STL directly. This isolates the problem to MCP server behavior rather
  than the FreeCAD install.

Result:
  `freecad-engineering-sandraschi` is now classified as `non_working` with
  follow-up record
  `docs/mcp-catalog/followups/freecad-engineering-sandraschi.md`.

Problem:
  `FreeCAD Copilot` was seeded with command `npx freecad-mcp`, but npm returned
  404 because the published installer package is `freecad-mcp-setup`, not
  `freecad-mcp`. The actual MCP server is `working_bridge.py` after setup.

Solution:
  Validated the bridge command directly with `uv run --with mcp python
  working_bridge.py`. Without the FreeCAD workbench socket, it initialized,
  listed `check_freecad_connection` and `test_echo`, and returned the expected
  message telling the user to start FreeCAD and switch to the AI Copilot
  workbench.

Result:
  Catalog command metadata now points to the bridge script path created by the
  upstream installer.

Problem:
  Full Linux container validation for `FreeCAD Copilot` installed FreeCAD 1.1.1,
  Xvfb, and the AICopilot workbench. Installing the workbench to
  `~/.local/share/FreeCAD/Mod/AICopilot` did not start the socket. FreeCAD 1.1
  reports its user app data directory as `~/.local/share/FreeCAD/v1-1/`.

Solution:
  Installed the workbench under
  `~/.local/share/FreeCAD/v1-1/Mod/AICopilot` and restarted FreeCAD under Xvfb.

Result:
  In the latest clean-container run, `/tmp/freecad_mcp.sock` appeared after 6
  seconds. The bridge initialized as serverInfo `freecad` version `2.0.0`,
  listed 7 tools, `check_freecad_connection` reported `FreeCAD running with AI
  Copilot workbench`, and `test_echo` returned `Bridge received: wright
  validation`.

Problem:
  The first safe backend operation for `FreeCAD Copilot`,
  `part_operations(operation=box)`, hung until the validation timeout. The latest
  run used `length=10`, `width=8`, `height=6`, and `name=WrightBox`, and timed
  out after 30 seconds. FreeCAD logged `Event observer error: No module named
  'PySide2'` plus Qt thread errors such as `Cannot create children for a parent
  that is in a different thread` and `Timers cannot be started from another
  thread`.

Solution:
  Record the operation hang as an MCP/workbench runtime issue rather than a
  missing dependency, because FreeCAD, Xvfb, the workbench, and the socket were
  all present.

Result:
  `freecad-copilot-contextform` is now classified as `non_working` with
  follow-up record
  `docs/mcp-catalog/followups/freecad-copilot-contextform.md`.

Problem:
  `AutoCAD MCP` was seeded as Windows/AutoCAD-only with command
  `python autocad_mcp.py`, but the upstream repository now ships a Python
  package with `python -m autocad_mcp` and supports a Linux-safe `ezdxf`
  backend.

Solution:
  Validated the public git install command in a clean Intel Ubuntu container:
  `AUTOCAD_MCP_BACKEND=ezdxf uv run --with
  git+https://github.com/hvkshetry/autocad-mcp.git python -m autocad_mcp`.

Result:
  The user-style command initialized MCP and listed 8 tools.

Problem:
  AutoCAD desktop/File IPC behavior cannot be tested in the Intel Ubuntu
  container because it requires a Windows AutoCAD LT 2024+ desktop host.

Solution:
  Fully validated the headless backend that does not require AutoCAD:
  `AUTOCAD_MCP_BACKEND=ezdxf`.

Result:
  Fresh validation on commit `95476a33a1c246308326eb4709d6379ef2efdbc1`
  passed 123 upstream tests. MCP initialized as `autocad-mcp` version
  `1.26.0`, listed 8 tools, `system` reported ezdxf 1.4.3,
  `drawing(create)` created `WrightValidation`, `entity(create_line)` created
  a line, `drawing(info)` reported one entity and the `WrightValidation` layer,
  and `drawing(save_as_dxf)` saved `/tmp/wright-autocad-validation.dxf` at
  15561 bytes. `autocad-mcp-hvkshetry` is tested for Linux x64 headless DXF
  generation, with the Windows AutoCAD File IPC backend explicitly untested.

Problem:
  The first AutoCAD MCP backend operation used nested arguments copied from a
  guessed shape: `entity(create_line)` received `data.start/end`, and
  `drawing(save_as_dxf)` received top-level `path`.

Solution:
  Read the MCP `tools/list` schemas and use the advertised shapes:
  `entity(create_line)` takes top-level `x1`, `y1`, `x2`, and `y2`, while
  `drawing(save_as_dxf)` takes `data: {"path": ...}`.

Result:
  The corrected MCP calls created the line, saved the DXF, and reported one
  entity through `drawing(info)`.

Problem:
  After installing uv from PowerShell into the Ubuntu container, a chained
  shell command temporarily failed to find `git` even though apt had installed
  it.

Solution:
  Use absolute paths inside the container for deterministic validation:
  `/usr/bin/git` and `/root/.local/bin/uv`.

Result:
  The source clone and all subsequent AutoCAD validation commands completed.

Problem:
  `Autodesk APS (Community)` points at
  `https://github.com/petrbroz/aps-mcp-server`, whose README states the project
  moved to `https://github.com/autodesk-platform-services/aps-mcp-server-nodejs`.
  The old repo is Node/TypeScript, but the Hermes entry still described it as a
  Python package before this validation pass.

Solution:
  Validate the real upstream install/start path in a clean Intel Ubuntu
  container, correct the Wright metadata to the Node command, and keep the
  community entry visible as a blocked redirect/duplicate. Prefer the official
  Autodesk APS entry for future setup and credential validation.

Result:
  Fresh validation on commit `557556235e806a5d74265fcf556b9dae4206abdd`
  installed `yarn` 1.22.22, ran `yarn install --frozen-lockfile`, and built
  successfully with `yarn run build`. There is no `yarn test` script. Without
  credentials, `node build/server.js` exited with the expected missing-variable
  message for `APS_CLIENT_ID`, `APS_CLIENT_SECRET`, `APS_SA_ID`,
  `APS_SA_EMAIL`, `APS_SA_KEY_ID`, and `APS_SA_PRIVATE_KEY`. With dummy APS
  variables and a generated base64 RSA private key, MCP initialized as
  `autodesk-platform-services` version `0.0.1`, listed 8 tools
  (`get-accounts`, `get-folder-contents`, `get-issue-comments`,
  `get-issue-root-causes`, `get-issue-types`, `get-issues`,
  `get-item-versions`, and `get-projects`), and `get-accounts` reached Autodesk
  auth and returned `AUTH-001` for the dummy client. The catalog records this as
  blocked/superseded because upstream redirects users to the official APS MCP.

Problem:
  `Autodesk Platform Services` requires cloud credentials and a Secure Service
  Account, which are not available in the clean Intel Ubuntu validation
  container.

Solution:
  Validate install/startup up to the credential gate using the official repo:
  `npm install` followed by `node server.js`.

Result:
  Fresh validation on commit `722591abb08c42000e9aedcabc746bbd7f413739`
  installed dependencies with `npm install`. There is no `npm test` script.
  `node server.js` exited with the expected missing-credential diagnostic for
  `APS_CLIENT_ID`, `APS_CLIENT_SECRET`, `SSA_ID`, `SSA_KEY_ID`, and
  `SSA_KEY_PATH`. With dummy APS variables and a generated dummy RSA PEM key,
  MCP initialized as `aps-mcp-server-nodejs` version `0.0.1`, listed 4 tools
  (`getFolderContentsTool`, `getIssueTypesTool`, `getIssuesTool`,
  `getProjectsTool`), and `getProjectsTool` reached Autodesk auth and returned
  `AUTH-001` for the dummy client. The catalog records this as
  credential-limited `might_work`, not fully tested.

Problem:
  Installing Ubuntu's `npm` package pulled in a large dependency set and
  exceeded the initial two-minute command timeout while `apt`/`dpkg` was still
  running.

Solution:
  Check for active `apt`/`dpkg` processes and wait for them to finish before
  continuing, instead of retrying package installation over an active dpkg
  transaction.

Result:
  `node` 18.19.1, `npm` 9.2.0, and `git` 2.43.0 were available, and APS
  validation proceeded cleanly.

Problem:
  `Autodesk Fusion 360` was seeded with command `python
  fusion360_mcp_server.py`, but the upstream package is published as
  `fusion360-mcp-server` with CLI command `fusion360-mcp-server --mode socket`.
  Full backend validation requires Autodesk Fusion 360 desktop plus the
  Fusion360MCP add-in, which cannot be installed in the Intel Ubuntu container.

Solution:
  Validate all Linux-testable layers: upstream tests, MCP mock mode, and socket
  mode's missing-host diagnostic.

Result:
  Fresh validation on commit `b44b667e440da070081795cfcbfaf75de2a44251`
  passed 282 upstream tests. MCP mock mode initialized as
  `fusion360-mcp-server` version `1.26.0`, listed 85 tools, `ping` returned
  `pong`, and `create_box` returned mock deltas when called with `length`,
  `width`, and `height`. Socket mode initialized, listed 85 tools, and `ping`
  returned the expected error: `Not connected to Fusion 360. Make sure the
  add-in is running.` The catalog records this as host-dependent `might_work`,
  not fully tested.

Problem:
  The first Fusion `create_box` probe used `depth`, but the MCP schema requires
  `length`, `width`, and `height`.

Solution:
  Read the `tools/list` schema and rerun the mock call with
  `{"length": 10, "width": 8, "height": 6}`.

Result:
  Mock `create_box` returned an OK response with `Box_mock` and body/mass
  deltas.

Problem:
  `Fusion 360 Python API Bridge` was seeded with command `python main.py`, but
  the verified repository `https://github.com/sockcymbal/autodesk-fusion-mcp-python`
  does not contain `main.py`.

Solution:
  Clone the source in a clean Intel Ubuntu container and use the repository's
  actual MCP script: `python fusion_mcp.py`.

Result:
  Fresh validation cloned commit `a3398ac5c76baa252240f301167a4cba2fe6f5b8`.
  There are no upstream tests. `pip install -r requirements.txt` succeeded in a
  Python 3.12 virtual environment.

Problem:
  `fusion_mcp.py` reads APS credentials at import time, so missing credentials
  fail before MCP initialization.

Solution:
  Record the no-credential startup boundary, then use dummy `APS_CLIENT_ID`,
  `APS_CLIENT_SECRET`, and `FUSION_ACTIVITY_ID` values to test MCP protocol
  startup and the backend-touching `generate_cube` tool.

Result:
  Without APS env vars, startup exited with `KeyError: 'APS_CLIENT_ID'`. With
  dummy APS env vars, MCP initialized as serverInfo `fusion` version `1.28.1`
  and listed one tool, `generate_cube`.

Problem:
  `generate_cube` cannot reach the expected APS credential boundary because the
  upstream code uses `httpx.BasicAuth(CLIENT_ID, CLIENT_SECRET).auth_header`.
  Current `httpx.BasicAuth` does not expose `auth_header`.

Solution:
  Classify this as a code-level MCP failure and create a follow-up record for an
  upstream fix. The likely fix is to generate the Basic auth header manually or
  use the current httpx auth API correctly.

Result:
  `generate_cube` returned
  `'BasicAuth' object has no attribute 'auth_header'` before any APS request.
  `autodesk-fusion-mcp-python` is classified as `non_working` with validation
  status `failed`, not `dependency_missing`, until the auth helper is fixed.

Problem:
  `Autodesk Revit BIM` was seeded with a `.NET` command, but the current
  `revit-mcp` repository is a Node/TypeScript MCP server. The README also says
  the repo is being archived in favor of
  `https://github.com/mcp-servers-for-revit/mcp-servers-for-revit`.

Solution:
  Validate the current repository command path in a clean Intel Ubuntu
  container at commit `c9ef49e4c397298d291304f822b89ba3a102e6bf`:
  `npm install`, `npm run build`, and `node build/index.js`.

Result:
  The first `npm install` failed because `better-sqlite3` needed native
  compilation and `make` was missing. Installing only the selected-server build
  prerequisite `build-essential` fixed the install. There is no upstream
  `npm test` script.

Result:
  The server initialized over newline-delimited JSON as `revit-mcp` version
  `1.0.0`, listed 25 tools, and the backend probes `say_hello` and
  `get_current_view_info` both returned the expected `connect to revit client
  failed` diagnostic with stderr `connect ECONNREFUSED ::1:8080`. The catalog
  records this as host-dependent `might_work`, because full validation requires
  Revit desktop and the revit-mcp-plugin on Windows.

Problem:
  `Siemens Element Design System` was seeded as a simple `npx
  @siemens/element-mcp` command. In a clean Intel Ubuntu container, a fresh
  `npx -y @siemens/element-mcp` attempt failed with `element-mcp: not found`
  before MCP startup.

Solution:
  Follow the package README's project-install flow instead of treating it as a
  one-shot global command: create a project, run `npm install --save-dev
  --save-exact @siemens/element-mcp@49.12.0-v.1.11.1`, then run `npx
  @siemens/element-mcp` or `npx element-mcp`.

Result:
  The npm package installed successfully. There is no upstream test script in
  the package. MCP initialized as `@siemens/element-mcp` version `1.0.0`, listed
  2 tools (`element-search`, `element-icon-search`), and both tools reached the
  backend credential boundary with `Embedding API error: 403 Forbidden`.
  `element-mcp check` reported `LLM token not found. Run 'element-mcp
  setup-token'`. The catalog records this as `might_work` with missing
  `OPENAI_API_KEY`, because full validation requires a Siemens LLM token with
  `llm` scope.

Problem:
  `Siemens WinCC Unified SCADA` points to Siemens Support Entry ID `110002407`
  and a Windows `.exe` command, but no public installable artifact could be
  fetched in a clean Intel Ubuntu container.

Solution:
  Verify the public support signal and package registries before attempting
  backend tests. Public search results confirm `Integration of MCP Server with
  WinCC Unified PC Runtime` and a login-required
  `110002407_MCPServerPCRuntime_READMEOSS.zip`. Direct `curl` requests to the
  support page and PDF returned HTTP 403 from Akamai. npm checks for
  `wincc-unified-mcp` and `@siemens/wincc-unified-mcp` returned 404; PyPI
  checks for `wincc-unified-mcp` and `wincc_unified_mcp` found no distribution.

Result:
  `wincc-unified-mcp.exe --help` failed with `command not found`; guessed
  Siemens GitHub URLs did not resolve publicly without authentication. No MCP
  stdio calls could be made. The catalog records the official Siemens entry as
  `blocked` pending a Siemens Support login/license holder obtaining the
  official artifact and validating it on Windows with WinCC Unified PC Runtime.

Problem:
  `PTC ThingWorx IoT Platform` was seeded with a local command
  `ptc-thingworx-mcp`, but PTC's ThingWorx 10.1 documentation describes an
  embedded product-hosted MCP endpoint instead.

Solution:
  Verify the official docs and registry/package availability. PTC documentation
  pages for ThingWorx MCP returned HTTP 200 and describe configuring MCP clients
  with `<ThingWorx Server URL>/mcp`, plus managing tools/resources/prompts with
  the `MCPServices` resource. npm checks for `ptc-thingworx-mcp`,
  `thingworx-mcp`, and `@ptc/thingworx-mcp` returned 404; PyPI checks for
  `ptc-thingworx-mcp` and `thingworx-mcp` found no matching distribution.

Result:
  The local `ptc-thingworx-mcp --help` command failed with `command not found`.
  A separate community repository, `doubleSlashde/thingworx-mcp-server`, exists
  at commit `7e22ef9be1af495acf1a46101ebb17380eed86ae`, but it is not the
  official PTC product-hosted MCP entry. The catalog records the official entry
  as `might_work` / `dependency_missing` and uses `${THINGWORX_BASE_URL}/mcp`
  as the endpoint template. Full validation requires a ThingWorx 10.1+ MCP
  endpoint and AppKey or OAuth credentials.

Problem:
  `RhinoMCP` was seeded as `dotnet RhinoMcp.dll`, but the current upstream
  README uses the Python package command `uvx rhinomcp` and a separate Rhino 8
  plugin bridge started inside Rhino with the `mcpstart` command.

Solution:
  Clone `https://github.com/jingcheng-chen/rhinomcp`, inspect the server
  package metadata, and validate the Python server path in a clean Intel Ubuntu
  container.

Result:
  The repository cloned at commit `b56338a9da733d17555744ab895facdc84a80542`.
  The server package is `rhinomcp` version `0.3.1`, and the catalog/API command
  is now `uvx rhinomcp`.

Problem:
  Full Rhino backend validation requires Rhino 8 plus the RhinoMCP plugin
  running `mcpstart`; Rhino desktop is not available in the Ubuntu container.

Solution:
  Validate the source and stdio server as far as possible: install the Python
  package with `uv sync --extra dev`, run upstream tests, initialize MCP, list
  tools, call read/status tools, and call one backend-touching tool to verify
  the missing bridge diagnostic.

Result:
  Upstream Python/contract tests passed 192/192 with 12 pytest return-value
  warnings. MCP initialized as `RhinoMCP` version `1.26.0`, listed 66 tools,
  and `get_commands`, `get_document_summary`, and `create_object` all returned
  the expected diagnostic: `Could not connect to Rhino at 127.0.0.1:1999.
  Please start Rhino, run the Rhino command mcpstart, then retry the MCP
  request.` `rhino-mcp` remains `might_work` with `dependency_missing`
  validation until a Rhino 8 bridge host is available.

Problem:
  `SketchUp MCP` was seeded with command `ruby server.rb`, but the current
  upstream README describes a Python MCP package command, `uvx sketchup-mcp`,
  plus a separate SketchUp Ruby extension server.

Solution:
  Clone `https://github.com/mhyrr/sketchup-mcp` in a clean Intel Ubuntu
  container, inspect the package metadata and README, and validate the Python
  MCP server path from source.

Result:
  The repository cloned at commit `aa096f04d3d7b22a70860368f2b576343feac405`.
  The package is `sketchup-mcp` version `0.1.17`, and the catalog/API command
  is now `uvx sketchup-mcp`.

Problem:
  The repository's test-like files are not a usable upstream pytest suite.
  `test_eval_ruby.py` is a script, and `examples/simple_test.py` imports removed
  API `mcp.client.Client`.

Solution:
  Record the test limitation and validate via MCP stdio calls instead.

Result:
  Pytest reported no tests for `test_eval_ruby.py`, and collection failed for
  `examples/simple_test.py` with `ImportError: cannot import name 'Client' from
  'mcp.client'`.

Problem:
  Full SketchUp backend validation requires SketchUp desktop with the
  SketchupMCP extension server running on port 9876, which is not available in
  the Ubuntu container.

Solution:
  Validate the stdio server through `initialize`, `tools/list`, actual
  read/status tool `get_selection`, and backend-touching `eval_ruby`.

Result:
  MCP initialized as `SketchupMCP` version `1.28.1` and listed 10 tools.
  README-advertised `get_scene_info` is not present in `tools/list`.
  `get_selection` returned `Error getting selection: Could not connect to
  Sketchup. Make sure the Sketchup extension is running.` Backend-touching
  `eval_ruby` returned JSON `success: false` with the same missing-extension
  diagnostic. `sketchup-mcp` remains `might_work` with `dependency_missing`
  validation until a SketchUp extension host is available.

Problem:
  `Blender 3D` was seeded with an underspecified command. The upstream README
  recommends using `uvx` and pinning Python 3.11 for the MCP server.

Solution:
  Validate and store the upstream/user-facing command:
  `uvx --python 3.11 blender-mcp`.

Result:
  Fresh validation used `uv`/`uvx` 0.11.25 from the official installer. The
  package downloaded CPython 3.11.15, installed 37 packages, and launched the
  MCP server successfully. Without Blender or the add-on socket, `initialize`
  succeeded as `BlenderMCP` 1.28.1, `tools/list` returned 22 tools, and
  `get_scene_info` plus `execute_blender_code` returned the expected diagnostic:
  `Could not connect to Blender. Make sure the Blender addon is running.`

Problem:
  Full Blender validation cannot use `blender -b` background mode. The upstream
  add-on explicitly refuses to start in background mode because commands would
  never execute.

Solution:
  Install Blender as a selected-server dependency in the disposable container
  and launch a normal Blender process under Xvfb with
  `xvfb-run -a blender --python /tmp/start_blendermcp.py`.

Result:
  Blender 4.0.2 started under Xvfb and the validation script could load the
  add-on registration path.

Problem:
  Loading `addon.py` in Ubuntu 24.04 Blender 4.0.2 failed with
  `ModuleNotFoundError: No module named 'requests'`. The package was not
  installed by the Blender dependency set.

Solution:
  Install `python3-requests` as part of the selected-server Blender validation
  setup.

Result:
  The add-on loaded, started its socket on `localhost:9876`, and the MCP server
  connected to Blender.

Problem:
  `Blender 3D` needed a real backend-touching probe before it could be marked
  fully tested for Linux x64.

Solution:
  With Blender, Xvfb, `python3-requests`, and the add-on socket running, call the
  read-only MCP tool `get_scene_info`, then call the backend-mutating
  `execute_blender_code` and verify with `get_object_info`.

Result:
  Clean Intel Ubuntu validation passed. MCP initialized, listed tools, and
  `get_scene_info` returned the default scene containing `Cube`, `Light`, and
  `Camera`. `execute_blender_code` created `WrightValidationCube` at
  `(1.0, 2.0, 3.0)`, and `get_object_info` verified the cube mesh with 8
  vertices, 12 edges, and 6 polygons. `blender-mcp-ahujasid` is now classified
  as `tested` for Linux x64, with cloud/asset services still left for separate
  credential/network testing.

Problem:
  `multiCAD MCP` was seeded with command `python multicad_mcp.py`, but the
  repository README uses `python src/server.py` after `uv sync --dev` and
  `pywin32` installation.

Solution:
  Clone `https://github.com/AnCode666/multiCAD-mcp` in a clean Intel Ubuntu
  container and inspect the package metadata, README, and source layout.

Result:
  The repository cloned at commit `360ec77c970ec95a962bd4d0a3238715ee78dd7c`.
  The package is `multiCAD-mcp` version `0.2.0`, and the validated entrypoint is
  `python src/server.py`.

Problem:
  `multiCAD MCP` cannot install or start in the Intel Ubuntu container because
  it is a Windows COM bridge. The package declares `pywin32>=300`, and source
  imports raise `ImportError: AutoCAD adapter requires Windows OS with COM
  support` on non-Windows platforms.

Solution:
  Treat Windows, `pywin32`, Windows COM, and a supported CAD host as selected
  MCP dependencies. Test Linux only to the dependency boundary: exact
  `pip install -e '.[dev]'`, source install with `--no-deps` plus non-Windows
  dependencies, upstream unit collection, and direct server startup.

Result:
  Exact `pip install -e '.[dev]'` failed because `pywin32>=300` has no Linux
  distribution. Installing the source with `--no-deps` plus non-Windows
  dependencies succeeded, but upstream unit collection failed with
  `ImportError: AutoCAD adapter requires Windows OS with COM support`.
  `python src/server.py --help` and direct startup both exited before MCP
  initialization with the same diagnostic, so no MCP `initialize` or
  `tools/list` calls were possible in Linux. `multicad-mcp` remains
  `might_work` with `dependency_missing` validation for Linux x64 and explicit
  Windows/COM/CAD host requirements.

Problem:
  `CAD-MCP Universal` was originally treated like a URL-needed seed, but the
  catalog row has a concrete source URL:
  `https://github.com/daobataotie/CAD-MCP`. The seeded command
  `python cad_mcp.py` did not match the repository README.

Solution:
  Clone the upstream repo in a clean Intel Ubuntu container and use the README
  command path, `python src/server.py`.

Result:
  The catalog command now matches the repository layout. The repo was validated
  at commit `352541820a56823568a90993dd773e7014205f44`.

Problem:
  `CAD-MCP Universal` cannot install or start in the Ubuntu container because it
  is a Windows COM bridge. `requirements.txt` requires `pywin32>=228`, and
  `src/cad_controller.py` imports `win32com.client` and `pythoncom` at import
  time.

Solution:
  Test dependency resolution with Python 3.12 inside the clean Intel Ubuntu
  container. Then install only the platform-neutral dependencies and attempt
  `python src/server.py` to capture the exact startup boundary.

Result:
  `pip install -r requirements.txt` failed with
  `ERROR: Could not find a version that satisfies the requirement pywin32>=228`
  and `ERROR: No matching distribution found for pywin32>=228`. Installing only
  `mcp`, `pydantic`, and `typing` succeeded, but `python src/server.py` exited
  before MCP initialization with `ModuleNotFoundError: No module named
  'win32com'` from `src/cad_controller.py`. `cad-mcp-daobataotie` remains
  `might_work` with `dependency_missing` validation for Linux x64 and explicit
  Windows/CAD host requirements.

Problem:
  `Creo/CadQuery MCP` was seeded as a generic Creo desktop bridge, but the
  verified repository is `https://github.com/yangkunyi/creo-mcp`, a Python
  package that exposes local CadQuery code execution, optional Creo file
  opening through CREOSON, and an optional Volcengine knowledge-base query.

Solution:
  Validate the real user command shape with `uvx creo-mcp --authorization ...
  --service-resource-id ...`, and validate the source checkout with Python 3.12
  plus the repository's `pip install -e .` path in a clean Intel Ubuntu
  container.

Result:
  Fresh validation cloned commit `1a2f164c88c896c0b98a8edec36a7dc4e2eb06ff`.
  No upstream tests were present. The catalog/API command now uses `uvx
  creo-mcp --authorization ${VOLCENGINE_AUTHORIZATION} --service-resource-id
  ${VOLCENGINE_SERVICE_RESOURCE_ID}`.

Problem:
  The first `creo-mcp` startup failed before MCP initialization because the
  CadQuery/OCP stack needed a Linux OpenGL runtime library:
  `ImportError: libGL.so.1: cannot open shared object file: No such file or
  directory`.

Solution:
  Install `libgl1` as a selected-server runtime dependency for this MCP only.

Result:
  After `apt-get install -y libgl1`, MCP initialized as
  `python-code-executor` version `1.28.1` and listed 3 tools:
  `execute_python_code`, `open_file_in_cad`, and
  `retrieve_from_knowledge_base`.

Problem:
  `creo-mcp` needed a real backend-touching operation before classification,
  but the Intel Ubuntu container does not have Creo desktop, CREOSON, or real
  Volcengine credentials.

Solution:
  Call a local CadQuery operation through `execute_python_code`, then call the
  two dependency-boundary tools with dummy inputs to capture exact diagnostics:
  `open_file_in_cad` for CREOSON/Creo and `retrieve_from_knowledge_base` for
  Volcengine.

Result:
  `execute_python_code` exported `/tmp/wright_creo_box.step` at 15418 bytes.
  `open_file_in_cad` returned the expected CREOSON connection-refused
  diagnostic for `localhost:9056`. `retrieve_from_knowledge_base` reached the
  Volcengine endpoint and returned `400 Client Error: Bad Request` with dummy
  credentials. The entry is classified as `might_work` with validation status
  `dependency_missing`; local CadQuery is validated, but full Creo/CREOSON and
  Volcengine workflows require user-provided host software and credentials.

Problem:
  `CREOSON JSON-RPC Server` was listed as an MCP server with `java -jar
  creoson.jar`, but the upstream project is a Creo JSON/JLINK bridge, not an
  MCP protocol server.

Solution:
  Validate the source and the user-facing release ZIP in a clean Intel Ubuntu
  container. Source cloned at commit
  `1939a585a1fcc94b6c05586af92c2da00adebdb0`. Latest release `v3.0.1` asset
  `CreosonServer-3.0.1-win64.zip` downloaded and unpacked.

Result:
  Source build instructions require Creo JLINK `text/java/pfcasync.jar`,
  CreosonSetup ZIPs, Commons Codec, and Jackson jars. The release ZIP contains
  `CreosonServer-3.0.0.jar`, support JARs, `creoson_run.bat`, and
  `jshellnative.dll`. `java -jar CreosonServer-3.0.0.jar` failed with
  `no main manifest attribute`. Calling the actual main class
  `com.simplifiedlogic.nitro.jshell.MainServer` with the release JARs failed
  with `NoClassDefFoundError: com/ptc/cipjava/jxthrowable`, the expected missing
  Creo/JLINK Java class. No MCP `initialize` or `tools/list` calls could be
  made because CREOSON does not implement MCP stdio/SSE. The catalog records it
  as a blocked capability alias and keeps it as middleware for Creo MCPs.

Problem:
  `CAiD OpenCASCADE` was seeded with `uvx caid-mcp`, but the package does not
  provide a console script. `uv tool run caid-mcp --help` installed
  dependencies and then reported: `Package caid-mcp does not provide any
  executables.`

Solution:
  Use the upstream README launch path: clone the repository and run
  `python server.py` from the repo environment.

Result:
  Catalog command metadata now uses `python server.py`.

Problem:
  Installing the README dependency `caid` from PyPI allowed package installation
  after adding `libgl1`, but MCP startup and tests failed with
  `ModuleNotFoundError: No module named 'caid.vector'`.

Solution:
  Inspect the linked CAiD source repository and install CAiD from GitHub instead
  of the current PyPI artifact:
  `uv pip install -e /tmp/CAiD`.

Result:
  The GitHub CAiD source includes `caid/vector.py`, imports succeeded, and the
  MCP server could start.

Problem:
  CAiD/OCP import initially failed in the clean Intel Ubuntu container with
  `ImportError: libGL.so.1: cannot open shared object file`.

Solution:
  Install `libgl1` as a selected-server native dependency for CAiD.

Result:
  CAiD and OCP imported successfully.

Problem:
  `CAiD OpenCASCADE` needed a real backend operation before it could be marked
  fully tested.

Solution:
  In a clean Intel Ubuntu container, install `libgl1`, CAiD from GitHub commit
  `840d9ece24499dca4d1cc6b7a7aef2b88a203f14`, and caid-mcp from commit
  `bb863e9fe64f951fac9d59daed26254544682bc3`; run upstream tests and probe MCP.

Result:
  72 upstream MCP tests passed. MCP initialized, listed 107 tools, `create_box`
  returned `ok:true` with `volume_mm3:480.0`, and scene query reported
  `wright_box` at 10 x 8 x 6 mm. `caid-opencascade-dreliq9` is now classified
  as `tested` for Linux x64.

Problem:
  `CalculiX Simulation` was seeded with
  `https://github.com/calculix/calculix-mcp` and command
  `uv run calculix-mcp`, but the research handoff described the row as a
  FreeCAD FEM capability alias or wrapper candidate rather than a verified
  standalone MCP server.

Solution:
  Check both the configured repository and package name in a clean Intel Ubuntu
  container.

Result:
  `git clone https://github.com/calculix/calculix-mcp` failed with a GitHub
  credential prompt, consistent with a missing or private repo, and
  `uv tool run calculix-mcp --help` reported that `calculix-mcp` was not found
  in the package registry. `calculix-simulation` is now classified as `blocked`
  until a concrete standalone MCP source is verified. No non-working follow-up
  record was created because this is currently not an installable MCP server.

Problem:
  `Easy-MCP-AutoCAD` was seeded with a URL-needed status and command
  `python easy_mcp_autocad.py`, but the current catalog has a real source URL
  and the repository README uses `python server.py`.

Solution:
  Clone `https://github.com/zh19980811/Easy-MCP-AutoCad` in a clean Intel
  Ubuntu container and inspect the repository layout and README.

Result:
  The repository cloned at commit `332215b91e976c1738dfd3940e9f9770c0fd5856`.
  The catalog command now uses `python server.py`.

Problem:
  `Easy-MCP-AutoCAD` cannot install or start in the Intel Ubuntu container. The
  README requires Windows OS and AutoCAD 2018+ with COM support, and
  `server.py` imports `win32com.client` at module import time.

Solution:
  Test both declared Python install paths with Python 3.13:
  `uv pip install -r requirements.txt` and `uv pip install -e .`.

Result:
  Both dependency installs failed because `pywin32` has no Linux wheels.
  A fresh check on commit `332215b91e976c1738dfd3940e9f9770c0fd5856`
  confirmed `pip install -r requirements.txt` cannot resolve `pywin32` on
  Linux, and `uv pip install -e .` with Python 3.13 reports that
  `pywin32>=309` only has `win32`, `win_amd64`, and `win_arm64` wheels.
  After installing only non-Windows dependencies, direct `python server.py`
  failed at module import with `ModuleNotFoundError: No module named
  'win32com'`. `easy-mcp-autocad` remains `might_work` with
  `dependency_missing` validation for Linux x64 and explicit
  Windows/AutoCAD host requirements.

Problem:
  `FreeCAD Booleans` was seeded with command `uvx freecad-mcp-server`, but the
  source repo `https://github.com/lucygoodchild/freecad-mcp-server` is a
  Node/TypeScript MCP server. `uv tool run freecad-mcp-server --help` reported
  the package was not found in the Python package registry.

Solution:
  Use the repository README path: `npm install`, `npm run build`, and
  `node build/index.js`.

Result:
  The TypeScript server built successfully and initialized over MCP stdio,
  listing 7 tools.

Problem:
  `FreeCAD Booleans` requires FreeCAD for backend operations. Without FreeCAD,
  `list_objects` started backend initialization and reported `spawn freecad
  ENOENT`.

Solution:
  Install FreeCAD as a selected-server dependency. The current Ubuntu apt
  repository did not provide a `freecad` package, so use the FreeCAD 1.1.1
  Linux x86_64 AppImage and symlink its extracted `freecadcmd` to
  `/usr/bin/freecadcmd`, which the server auto-detects.

Result:
  The server detected `Using FreeCAD at: /usr/bin/freecadcmd`.

Problem:
  `FreeCAD Booleans` needed a real backend operation before being marked fully
  tested.

Solution:
  With FreeCAD 1.1.1 AppImage available, call `create_box` for a 10 x 8 x 6 mm
  `WrightBox`, then call `list_objects`.

Result:
  Clean Intel Ubuntu validation passed with a caveat. `create_box` reported
  `SUCCESS: Created box: WrightBox with dimensions 10x8x6mm`, and
  `list_objects` reported FreeCAD Part boxes. The server also writes operational
  log lines to stdout during tool calls, which is a stdio protocol risk for
  strict clients. `freecad-booleans-lucygoodchild` is now classified as
  `tested` for Linux x64 with that caveat recorded.

Problem:
  `FreeCAD Core` starts as a Python MCP server, but backend operations require
  the separate FreeCADMCP addon RPC server inside FreeCAD. Without that backend,
  the MCP initialized and listed tools, but `get_objects` reported connection
  refused on localhost.

Solution:
  Treat FreeCAD and the addon as selected-server dependencies. Install FreeCAD
  1.1.1 from the Linux x86_64 AppImage, copy `addon/FreeCADMCP` into FreeCAD
  user Mod directories, and write `freecad_mcp_settings.json` with
  `auto_start_rpc: true` and localhost-only access.

Result:
  FreeCAD launched under Xvfb and the addon opened localhost port 9875 after 4
  seconds.

Problem:
  In Ubuntu 24.04, `python3 -m pip install --break-system-packages --upgrade
  pip uv` failed because the apt-managed `pip 24.0` package has no Python wheel
  `RECORD` file and cannot be uninstalled by pip.

Solution:
  Leave system pip alone and install only the selected user-space tool with
  `python3 -m pip install --break-system-packages uv`.

Result:
  `uv 0.11.25 (x86_64-unknown-linux-gnu)` installed successfully without
  disturbing apt's pip package.

Problem:
  The current Ubuntu apt repository did not provide a directly installable
  `freecad` package for this container flow.

Solution:
  Use the FreeCAD 1.1.1 Linux x86_64 AppImage as the selected-server backend
  install path, extract it, and launch the extracted `usr/bin/freecad` under
  Xvfb.

Result:
  `/tmp/freecad-appimage/squashfs-root/usr/bin/freecadcmd --version` reported
  FreeCAD 1.1.1 revision `20260414`.

Problem:
  The FreeCAD 1.1.1 AppImage download from SourceForge can exceed a short
  command timeout; the first validation command timed out while `curl` was still
  writing the AppImage.

Solution:
  Check the container process and file state, wait for `curl` to finish, then
  extract the completed AppImage instead of restarting the whole container.

Result:
  The AppImage completed at 783 MB, extracted successfully, and reported FreeCAD
  1.1.1 revision `20260414`.

Problem:
  `FreeCAD Core` needed a real backend operation before it could be marked fully
  tested.

Solution:
  In a clean Intel Ubuntu container, run `uv tool run freecad-mcp
  --only-text-feedback`, initialize MCP, list tools, call `create_document`,
  call `create_object` for a 10 x 8 x 6 mm `Part::Box`, then call
  `get_objects`.

Result:
  Clean Intel Ubuntu validation passed. Repository commit
  `63acb305573194a011641ab13ccfb391fe95769f` listed 14 tools through MCP
  serverInfo `FreeCADMCP` version `1.28.1`; `list_documents` returned `[]`;
  `create_document` created `WrightDoc`, `create_object` created `WrightBox`,
  and `get_objects` reported `WrightBox` as `Part::Box` with volume `480.0`.
  Package `freecad-mcp` was version `0.1.18`; no upstream tests were present;
  Ubuntu's missing `freecad` apt candidate was handled by installing FreeCAD
  1.1.1 revision `20260414` from the Linux x86_64 AppImage.
  `freecad-core-nekanat` and Hermes alias `freecad-mcp-nekanat` are now
  classified as `tested` for Linux x64.

Problem:
  The minimal Ubuntu container emitted locale and fontconfig warnings when
  launching FreeCAD AppImage under Xvfb.

Solution:
  Record the warnings as non-blocking for this validation path. They did not
  prevent RPC startup, MCP initialization, or modeling commands.

Result:
  No catalog downgrade is needed for the warnings.

Problem:
  `FreeCAD Robust` was seeded with command
  `uvx freecad-addon-robust-mcp-server`, but the GitHub repository name is not
  the PyPI executable path.

Solution:
  Verify the package with `uv tool run --from freecad-robust-mcp
  freecad-mcp --help`.

Result:
  The installable package is `freecad-robust-mcp` and the executable is
  `freecad-mcp`. The catalog command now uses
  `uv tool run --from freecad-robust-mcp freecad-mcp`.

Problem:
  `FreeCAD Robust` requires a FreeCAD-side bridge before backend operations can
  run. The MCP server alone is only the client side of the bridge.

Solution:
  Use the upstream source bridge script with the selected FreeCAD backend:
  `freecadcmd freecad/RobustMCPBridge/freecad_mcp_bridge/blocking_bridge.py`.

Result:
  The bridge started in headless mode and advertised XML-RPC on localhost port
  9875 and socket mode on localhost port 9876.

Problem:
  A raw XML-RPC `ping()` probe was not a reliable readiness check for this
  bridge even though the TCP port was open and the bridge log reported startup.

Solution:
  Use the MCP package's own connection check:
  `FREECAD_MODE=xmlrpc FREECAD_SOCKET_HOST=127.0.0.1 uv tool run --from
  freecad-robust-mcp freecad-mcp --check`.

Result:
  The command reported `Connection successful`, FreeCAD version `1.1.1`, and
  GUI availability `0`, matching the expected headless backend.

Problem:
  `FreeCAD Robust` needed a real backend operation before it could be marked
  fully tested.

Solution:
  In a clean Intel Ubuntu container, install FreeCAD 1.1.1 AppImage, start the
  Robust MCP Bridge with `freecadcmd`, run the MCP in XML-RPC mode, initialize
  MCP, list tools, create a document, create a 10 x 8 x 6 mm box, and list
  objects.

Result:
  Clean Intel Ubuntu validation passed. Repository commit
  `d9a37118a8331e8739ad45fd97d027437984296f` initialized MCP serverInfo
  `freecad-mcp` version `1.28.1`, listed 152 tools, created `WrightDoc`,
  created `WrightBox` as `Part::Box` with volume `480.0`, and `list_objects`
  returned `WrightBox`. Source package `freecad-robust-mcp` installed as
  version `0.1.dev1+gd9a37118a`, upstream unit tests passed with 420 tests, and
  Ubuntu's missing `freecad` apt candidate was handled by installing FreeCAD
  1.1.1 revision `20260414` from the Linux x86_64 AppImage.
  `freecad-robust-spkane` is now classified as `tested` for Linux x64.

Problem:
  `KiCad MCP` was seeded with command `uv run python main.py`, matching the
  README, but that path failed in the clean Intel Ubuntu validation container.

Solution:
  Verify the package console script and use the GitHub install-style command:
  `uv tool run --from git+https://github.com/lamaalrajih/kicad-mcp.git
  kicad-mcp`.

Result:
  The GitHub package installed from commit
  `98c9ea41cb393393a8bafd157a93e84431e00afb` and started the MCP server. The
  `python main.py` path raised `ValueError: a coroutine was expected, got None`.

Problem:
  `KiCad MCP` needed basic protocol validation before testing KiCad-backed
  operations.

Solution:
  Create a sample project directory with `.kicad_pro`, `.kicad_pcb`, and
  `.kicad_sch` files, set `KICAD_SEARCH_PATHS`, then call `initialize`,
  `tools/list`, `list_projects`, and `get_project_structure`.

Result:
  MCP initialized as server `KiCad` version `1.11.0`, listed 16 tools,
  discovered sample project `WrightBoard`, and returned the sample project
  files. Read-only project discovery works.

Problem:
  Backend-touching and analysis tools are not callable by a normal MCP client.
  11 of 16 tools expose `ctx` as a required input property, including DRC, BOM,
  netlist, thumbnail, and pattern-analysis tools.

Solution:
  Attempt a normal MCP client call to `run_drc_check` with only the documented
  `project_path` argument.

Result:
  `run_drc_check` failed before KiCad CLI execution with
  `Input validation error: 'ctx' is a required property`. `kicad-mcp-lamaalrajih`
  is now classified as `non_working` until the tool schemas hide or inject
  FastMCP context parameters.

Problem:
  Upstream tests fail the default validation command even without running KiCad
  backend operations.

Solution:
  Run both the default and no-coverage forms.

Result:
  `uv run pytest -q` executed 37 tests and skipped 2, then failed the configured
  80% coverage gate with 10.04% total coverage. `uv run pytest -q --no-cov`
  passed with 37 passed and 2 skipped.

Problem:
  The upstream README requires KiCad 9.0+, but Ubuntu 24.04 default apt only
  offers KiCad 7.0.11.

Solution:
  Record the backend dependency mismatch and defer full KiCad CLI validation
  until the MCP schema issue is fixed.

Result:
  No KiCad 9 backend validation was attempted for this pass because the MCP
  schema blocks normal calls before `kicad-cli` is reached.

Problem:
  `ROSBag MCP` was seeded with command `python -m mcp_rosbags`, but no
  `mcp-rosbags` or `mcp_rosbags` package tool was found in the Python registry.

Solution:
  Clone the verified source repository and use the README source command path
  with `PYTHONPATH` set to the repo `src` directory.

Result:
  The catalog command now records the source-run command `python src/server.py`.

Problem:
  The default source install failed at MCP startup after installing
  `requirements.txt` because the current unpinned `rosbags` dependency no
  longer exports `deserialize_cdr`.

Solution:
  Apply a selected-server dependency pin after installing requirements:
  `uv pip install --reinstall rosbags==0.10.10`.

Result:
  The import succeeded and the server started.

Problem:
  `ROSBag MCP` needed a real bag-reading operation before it could be marked
  fully tested.

Solution:
  Generate a small ROS 2 bag with two `/chatter` `std_msgs/msg/String` messages
  using the `rosbags` writer, then call `list_bags`, `bag_info`, and
  `get_message_at_time` over MCP.

Result:
  Clean Intel Ubuntu validation passed. Repository commit
  `9b6b3b7a7b10d2ef004c1b50d38395d07e0b47b6` initialized MCP serverInfo
  `rosbag-memory` version `1.28.1`, listed 15 tools, discovered generated bag
  `wright_chatter`, `bag_info` reported topic `/chatter` with 2 messages over 1
  second, and `get_message_at_time` returned `std_msgs/msg/String` data
  `hello`. `rosbag-mcp-binabik` is now classified as `tested` for Linux x64
  with the `rosbags==0.10.10` dependency pin recorded.

Problem:
  The next desired FEA MCP candidate was found under the research name
  `Open FEM Agent`, but the current GitHub URL redirects to the canonical
  OASiS repository.

Solution:
  Use `https://github.com/Hereon-InstituteMS/OASiS` as the source URL and keep
  `Open FEM Agent` / `Open-FEM-agent` as aliases in catalog documentation.

Result:
  Clean Intel Ubuntu validation cloned commit
  `117c35769c0eb00181db003e8dcdc305546b08b7` and installed OASiS from source
  with `pip install -e .`.

Problem:
  OASiS exposes eight solver backends, but installing every advertised solver
  would violate the selected-server process and pull in heavy or
  host-specific software.

Solution:
  Install the MCP base package first, call `discover`, then install only one
  lightweight backend for full validation: `pip install scikit-fem`.

Result:
  Base `discover` returned clear not-installed diagnostics for optional
  backends, including FEniCSx, deal.II, FEBio, NGSolve, scikit-fem, Kratos,
  DUNE-fem, and 4C. After installing `scikit-fem==12.0.2`, `discover` reported
  `skfem` available while the other optional backends remained cleanly
  diagnosed as not installed.

Problem:
  The upstream focused MCP stdio test could not run immediately after
  `pip install -e .`.

Solution:
  Install the upstream test runner inside the selected-server virtual
  environment: `pip install pytest`.

Result:
  `PYTHONPATH=src PYVISTA_OFF_SCREEN=true pytest tests/test_mcp_stdio.py -q`
  passed with 5 tests.

Problem:
  OASiS needed a real backend-touching FEA call before it could be marked
  fully tested.

Solution:
  Call `initialize`, `tools/list`, `discover`, `prepare_simulation` for
  `solver=skfem` and `physics=poisson`, then call `run_simulation` with the
  upstream scikit-fem Poisson smoke script.

Result:
  MCP initialized as serverInfo `OASiS` version `1.28.1`, listed 15 tools,
  returned Poisson knowledge/pitfalls, completed the scikit-fem Poisson solve
  in 0.46 seconds, wrote `result.vtu`, and reported
  `max_phi 0.07389930610869422`. `oasis-open-fem-agent` is now classified as
  `tested` for Linux x64 with scikit-fem as the validated backend.

Problem:
  `SolidWorks API Docs` was seeded as a Python/uvx command, but the verified
  source is a Bun/TypeScript MCP server with a local documentation corpus.

Solution:
  Clone `https://github.com/kilwizac/solidworks-api-mcp`, install Bun, run
  `bun install`, and launch from the clone with `bun run start`. Set
  `SW_API_DATA_ROOT` only when overriding the default `solidworks-api`
  directory.

Result:
  Catalog command is now recorded as `bun run start`. The server does not
  require SolidWorks desktop software because it only searches local
  documentation data.

Problem:
  The Bun installer failed in the clean Ubuntu container because `unzip` was
  not installed.

Solution:
  Install `unzip` as a selected-server setup dependency before running
  `curl -fsSL https://bun.sh/install | bash`.

Result:
  Bun installed successfully as version `1.3.14`.

Problem:
  Sourcing `/root/.bashrc` after installing Bun failed in the noninteractive
  script with `PS1: unbound variable` under `set -u`.

Solution:
  Export Bun's path directly instead of sourcing the profile:
  `export PATH=/root/.bun/bin:$PATH`.

Result:
  `bun install`, `bun run typecheck`, and `bun run test` ran successfully.

Problem:
  `SolidWorks API Docs` needed real MCP calls against the local documentation
  corpus before it could be marked fully tested.

Solution:
  Start `bun run start` over stdio and call `initialize`, `tools/list`,
  `solidworks_search_api`, `solidworks_get_interface_members`,
  `solidworks_lookup_method`, and `solidworks_get_examples`.

Result:
  Clean Intel Ubuntu validation passed. Repository commit
  `f5a0ccf63337187695b3461cb750977be7d860f6` initialized MCP serverInfo
  `solidworks-mcp` version `0.1.0`, listed 6 tools, searched for
  `OpenDoc6 model document`, listed 333 `ISldWorks` members, returned
  structured docs for `ISldWorks.OpenDoc6`, and returned OpenDoc6 examples.
  Upstream typecheck passed and upstream tests passed 40/40.
  `solidworks-api-docs` is now classified as `tested` for Linux x64.

Problem:
  `onshape-mcp-hedless` was seeded as an SSE endpoint, but the verified source
  repository is a Python stdio MCP server.

Solution:
  Clone `https://github.com/hedless/onshape-mcp`, install with
  `pip install -e .`, and launch with `python -m onshape_mcp.server`.

Result:
  Catalog command is now recorded as `python -m onshape_mcp.server`, with
  required `ONSHAPE_ACCESS_KEY` and `ONSHAPE_SECRET_KEY` environment variables.

Problem:
  Full Onshape CAD operations require cloud API credentials that are not
  available in the validation container.

Solution:
  Validate install/start/tool-list behavior without credentials, then call a
  real API-touching tool (`list_documents`) to confirm the credential failure
  is clear and expected.

Result:
  Clean Intel Ubuntu validation installed commit
  `54d21ccc4a5376f692cddd01959305be01e40a53`, initialized MCP serverInfo
  `onshape-mcp` version `1.28.1`, listed 45 tools, and `list_documents`
  returned `API returned 401. Please check your API credentials.`
  `onshape-mcp-hedless` remains `might_work` with validation status
  `dependency_missing` until credentials are available for full cloud testing.

Problem:
  Upstream tests needed the development extras, not just the runtime install.

Solution:
  Run `pip install -e .[dev]` before `pytest -q`.

Result:
  Upstream tests passed with 497 tests and 86.28% coverage.

Problem:
  `jarvis-onshape-mcp` was still classified as URL-needed/blocked in the API
  metadata even though the catalog source URL points to a real installable
  repository: `https://github.com/ReshefElisha/jarvis-onshape-mcp`.

Solution:
  Validate the GitHub install path in a clean Intel Ubuntu container using
  `uv run --with git+https://github.com/ReshefElisha/jarvis-onshape-mcp.git
  onshape-mcp`, and test the source checkout with `uv sync --extra dev`.

Result:
  Fresh validation cloned commit `b0e725852280ebcfda5d46a4f2ed2d0b720beace`.
  The package is `onshape-mcp` version 1.2.0. Upstream tests passed 698/698
  with 3 Pydantic deprecation warnings.

Problem:
  Full Jarvis Onshape validation requires live Onshape API credentials, which
  are not available in the clean Intel Ubuntu validation container.

Solution:
  Use dummy `ONSHAPE_API_KEY` and `ONSHAPE_API_SECRET` values to validate MCP
  startup, tool discovery, a local/read-only MCP call, and cloud API credential
  boundaries.

Result:
  MCP initialized as serverInfo `onshape-mcp` version `1.17.0`, listed 69
  tools, and `list_cached_images` returned the expected empty-cache message.
  `list_documents` reached `https://cad.onshape.com/api/v6/documents` and
  returned `API returned 401. Please check your API credentials.`.
  `create_document` reached `https://cad.onshape.com/api/v10/documents` and
  returned `Unauthenticated API request`. `jarvis-onshape-mcp` is now
  classified as `might_work` with validation status `dependency_missing` until
  real Onshape credentials are available.

Problem:
  `zoo-dev-cloud-cad` / `zoo-mcp` was seeded as a Node `npx` command, but the
  verified repository is a Python/uv stdio MCP server.

Solution:
  Clone `https://github.com/KittyCAD/zoo-mcp`, install with `uv sync --dev`,
  and use `uvx zoo-mcp` for user install/start or `uv run python -m zoo_mcp`
  when validating from a source checkout.

Result:
  Catalog command is now recorded as `uvx zoo-mcp`, with required
  `ZOO_API_TOKEN`.

Problem:
  Zoo MCP constructs the KittyCAD client during import, so missing credentials
  fail before the MCP handshake instead of returning a tool-level diagnostic.

Solution:
  Validate the no-token path separately, then use a dummy `ZOO_API_TOKEN` for
  MCP initialization, tool listing, and credential-limited backend calls.

Result:
  No-token startup failed with `No API token provided. Either pass token
  parameter or set KITTYCAD_API_TOKEN or ZOO_API_TOKEN environment variable.`
  With a dummy token, MCP initialized as `Zoo MCP Server` version `1.27.1`,
  listed 30 tools, and `calculate_volume` returned a clear Zoo API
  bad-authentication diagnostic.

Problem:
  Passing pytest marker expression `-m "not live"` through PowerShell and
  `docker exec bash -lc` was reduced to `not`, causing pytest expression
  parsing to fail.

Solution:
  Bypass shell quoting by invoking pytest through Python:
  `uv run python -c "import pytest; raise SystemExit(pytest.main(['-q', '-m', 'not live']))"`.

Result:
  The intended non-live selection ran. With a dummy token, upstream produced
  120 passed, 2 skipped, 6 deselected, and 33 failures from cloud/KCL-engine
  operations that require valid Zoo credentials.

Problem:
  Zoo needed a Hermes-style MCP probe that showed the LLM-facing tool metadata
  was available, not just package installation.

Solution:
  Start `uv run python -m zoo_mcp` over stdio with a dummy token and call
  `initialize`, `tools/list`, `search_kcl_docs`, and `calculate_volume`.

Result:
  `search_kcl_docs` returned structured KCL documentation results for
  `extrude`, proving local/read-only MCP calls work. `calculate_volume`
  reached `https://api.zoo.dev` and returned the expected authentication
  diagnostic. The entry remains `might_work` with validation status
  `dependency_missing` until a real Zoo.dev API token is available.

Problem:
  `SolidWorks Python COM` installs from source in a clean Intel Ubuntu
  container, but the server import fails before MCP initialization.

Solution:
  Record this as an upstream dependency/API break, not as a missing SolidWorks
  host dependency. The likely upstream fix is to pin `pydantic-ai` to a
  compatible version or update `src/solidworks_mcp/server.py` to the current
  PydanticAI/FastMCP integration API before attempting Windows/SolidWorks COM
  validation.

Result:
  Clean Intel Ubuntu validation cloned commit
  `f0858a7b9cf8cb9a7838ddfaa91a706ef6439cab`, installed with
  `pip install -e ".[test]"`, and resolved `pydantic-ai` 2.0.0, `fastmcp`
  3.4.2, and `mcp` 1.28.1. Focused upstream tests, `solidworks-mcp --help`,
  and `python -m solidworks_mcp.server` all failed with
  `ModuleNotFoundError: No module named 'pydantic_ai.toolsets.fastmcp'`.
  No MCP `initialize` or `tools/list` calls could be made. The entry is
  classified as `non_working` / `failed`; full CAD validation also requires
  Windows 10/11, SolidWorks, and Windows COM after the dependency mismatch is
  fixed.

Problem:
  `SolidWorks TypeScript COM` requires Node 20+, but Ubuntu 24.04's default
  package currently installs Node 18.

Solution:
  Install Node 20 only inside the selected-server validation container:
  `npm install -g n && n 20 && hash -r`.

Result:
  Node 20.20.2 and npm 10.8.2 were active for the upstream install, build, test,
  and MCP stdio validation.

Problem:
  The TypeScript server installs, builds, initializes, and lists tools in
  Ubuntu, but meaningful tool calls require the Windows-only `winax` COM
  backend.

Solution:
  Classify this as `might_work` / `dependency_missing`, not `tested`, and record
  the exact diagnostic returned through MCP tool calls. Do not install
  SolidWorks or Windows COM software in the shared container.

Result:
  Clean Intel Ubuntu validation cloned commit
  `c50ba5867f1d1632a5f6857a2b4aa5ad9b1838b7`, ran `npm install`,
  `npm run build`, and `USE_MOCK_SOLIDWORKS=true npm test`; tests passed 52/52.
  MCP initialized as `solidworks-mcp-server` version 3.1.3 and listed 86 tools.
  `generate_vba_script` and `create_part` both returned
  `The winax native module is not available. SolidWorks COM automation requires
  it on Windows`, with underlying load error
  `Module did not self-register:
  '/tmp/solidworks-mcp-ts/node_modules/winax/build/Release/node_activex.node'`.

Problem:
  `solidworks-mcp-alisamsam` cannot install from its documented requirements
  file in a clean Intel Ubuntu container.

Solution:
  Record the exact failed requirement and create a follow-up for upstream
  dependency cleanup before any Windows/SolidWorks validation. Continue only far
  enough to confirm the next runtime boundary.

Result:
  Clean Intel Ubuntu validation cloned commit
  `ee8f42a1a919af5e0fa8d1dcd24270c9983ce027`. `pip install -r
  requirements.txt` failed because `asyncio-compat>=0.1.0` has no matching PyPI
  distribution. `pip index versions asyncio-compat` and `pip index versions
  pywin32` both returned no matching distribution on Linux. After installing the
  available runtime dependencies `mcp` and `python-dotenv`, `python
  solidworks_mcp_server.py` failed with `ModuleNotFoundError: No module named
  'win32com'`. No upstream tests were present, and no MCP initialization or tool
  listing could be performed. The entry is classified as `non_working` /
  `failed`.

Problem:
  `WebMCP OpenSCAD` is a browser-hosted WebMCP app, not a standalone CAD stdio
  server. The MCP-B local relay can initialize over stdio, but page-provided
  OpenSCAD tools only appear after a browser tab connects to the relay.

Solution:
  Validate the source and relay path separately in a clean Intel Ubuntu
  container. Build the app with pnpm, serve the generated Nitro app, then probe
  `npx -y @mcp-b/webmcp-local-relay@latest` with MCP `initialize`,
  `notifications/initialized`, `tools/list`, `webmcp_list_sources`, and
  `webmcp_list_tools`.

Result:
  Clean Intel Ubuntu validation cloned commit
  `a3acb68578701001f0251459c75716a55aadfa10`. Ubuntu's default Node 18 could
  not run pnpm 11.9.0, so validation installed Node 22.23.1 with `n` after
  adding `curl`. `pnpm install --frozen-lockfile` succeeded. `pnpm test` found
  no test files and exited 1 with Vite/Vitest shutdown noise, so this repo does
  not currently provide a usable upstream test suite. `pnpm build` succeeded.
  The served app produced a 7156-byte HTML page titled
  `scad-webmcp · agent-driven parametric CAD` and embedded
  `@mcp-b/webmcp-local-relay@latest/dist/browser/embed.js`. The relay MCP
  initialized as `webmcp-local-relay` version `0.0.0`, listed 4 relay tools,
  and returned zero sources/tools because no browser page was connected. The
  entry is classified as `might_work` / `dependency_missing` until a browser
  tab connected through MCP-B or native WebMCP exposes the advertised 16
  OpenSCAD page tools.

Problem:
  `web3d-mcp` was seeded with `npx web3d-mcp`, source context from a Reddit
  post, and UI URL `https://web3d-mcp.dev`. The package and URL do not exist in
  the current clean Intel Ubuntu validation path.

Solution:
  Verify the catalog seed first, then map the Reddit/LobeHub listing to the
  real source repository: `https://github.com/dev261004/web3d-mcp-server`.
  Use the upstream local install path (`npm install`, `npm run build`,
  `node dist/server.js`) instead of the nonexistent npm package.

Result:
  npm returned 404 for both `web3d-mcp` and `web3d-mcp-server`, and DNS could
  not resolve `web3d-mcp.dev`. The real source cloned successfully at commit
  `b6e3cb59ba243ab53be2e1b1a674e5199bfc0c6a`. Catalog and UI metadata now point
  to `dev261004/web3d-mcp-server` and local stdio command `node dist/server.js`.

Problem:
  The upstream README says Node.js 18+, and build/test paths pass on Ubuntu
  Node 18.19.1, but direct MCP startup fails before initialization.

Solution:
  Treat Node 22 as the selected-server runtime for the Wright validation path.
  Install it inside the disposable container with `npm install -g n && n 22`.

Result:
  On Node 18.19.1, `node dist/server.js` failed with
  `ReferenceError: File is not defined` from `undici`. On Node 22.23.1, MCP
  startup succeeded.

Problem:
  `web3d-mcp-server` uses newline-delimited JSON on stdio, while the first MCP
  probe used `Content-Length` framing.

Solution:
  Use newline-delimited JSON messages for this server.

Result:
  MCP initialized as serverInfo `3d-scene-mcp` version `1.0.0`, listed 12 tools,
  and the cube scene workflow passed: `generate_scene` produced scene data,
  `validate_scene` returned `is_valid:true` with all 13 checks passed, `preview`
  returned SVG wireframe data, and `generate_r3f_code` returned `SUCCESS` with
  Vite/TypeScript React Three Fiber code. Upstream `npm test -- --runInBand`
  passed 10 suites and 65 tests; `npm run build` prechecks passed 7 health
  suites and 54 tests. npm audit still reported 33 dependency vulnerabilities,
  which should be reviewed upstream but did not block local MCP validation.

Problem:
  The Hermes-facing Wright gateway could publish a tool list for the wrong
  workspace because `/api/gateway/tools` selected the latest
  `engineering_workspaces.updated_at` row. In the Nous hackathon container this
  made Hermes intermittently report only a subset of the active MCPs even though
  Wright showed Blender, OpenSCAD, Jarvis OnShape, and Autodesk Product Help as
  active.

Solution:
  Pin the active Hermes gateway session in `system_settings` whenever a
  workspace/session is activated or synced to Hermes, and resolve
  `/api/gateway/tools` and `/api/gateway/call` from that pinned session before
  falling back to the latest workspace row.

Result:
  Targeted tests passed for the gateway and Hermes sync paths. The running
  `wright_nous_hackathon` container was restarted without rebuilding, the API
  returned healthy, `/api/workspace/mcp-status` showed all four MCPs active, and
  `/api/gateway/tools` listed 108 tools: 22 Blender, 15 OpenSCAD, 69 Jarvis
  OnShape, and 2 Autodesk Product Help. Hermes logged a `tools/list_changed`
  refresh followed by `dynamically refreshed 108 tool(s)`.
