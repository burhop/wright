# Windows Testing Guide

This directory contains scripts for testing Wright (and the Hermes Desktop integration) on Windows 11 in an isolated environment.

## Recommended Path: Image Factory

For reliable unattended Wright + Hermes Desktop testing, use the image factory
in [`image-factory/`](image-factory/). It builds a deterministic Windows
Hyper-V image from ISO with unattended setup, a known local administrator,
WinRM/Packer provisioning, Hermes Desktop installed and verified, then runs
Wright install tests on disposable differencing-disk child VMs.

This is the industry-standard path for CI-style validation because the base
image has deterministic identity, versioned artifacts, and validation gates
before promotion. Use the older scripts below for interactive debugging or
short-term rescue of existing local VMs.

```powershell
cd d:\repos\wright\windows-sandbox\image-factory
.\Build-WrightHermesImage.ps1 `
  -WindowsIsoPath C:\iso\Win11_23H2_English_x64.iso `
  -WindowsIsoChecksum sha256:REPLACE_WITH_REAL_CHECKSUM `
  -GuestPassword "Use-A-Strong-Local-Test-Password!"

.\New-WrightHermesTestVm.ps1 `
  -ParentVhdx d:\repos\wright\windows-sandbox\.vm\image-factory\published\wright-hermes-ready.vhdx `
  -GuestPassword "Use-A-Strong-Local-Test-Password!"
```

## Legacy / Interactive Approaches

| | Hyper-V VM (Legacy Interactive) | Windows Sandbox |
|:---|:---|:---|
| **Best for** | Full interactive testing — see Wright running inside Hermes Desktop | Quick automated test suite runs |
| **Persistence** | ✅ Install once, checkpoint, revert in seconds | ❌ Ephemeral — reinstalls everything every launch (~35 min) |
| **GUI testing** | ✅ Full Electron/desktop app testing | ✅ Full GUI, but slow to reach it |
| **Setup time** | ~30 min first time, then instant from checkpoint | ~35 min every time |
| **Files** | `provision-vm.ps1` | `test-windows.wsb` + `setup-and-test.ps1` |

---

## Option A: Hyper-V VM (Recommended)

Use this when you want to install Wright + Hermes Desktop on Windows and interact with it as a real user would. Tools are installed once and persisted via VM checkpoints.

### Prerequisites

1. Windows 11 Pro, Education, or Enterprise with **Hyper-V** enabled.

### Setup (One-Time, ~30 minutes)

We have completely automated the virtual machine creation, tool configuration, package installation, and execution into a single, unified pipeline.

1. **Open PowerShell as Administrator** on your Windows 11 host machine.

2. **Run the automation script**:
   ```powershell
   cd d:\repos\wright\windows-sandbox
   Set-ExecutionPolicy Bypass -Scope Process -Force
   .\run-vm-test.ps1
   ```
   *Note: If you have already downloaded Microsoft's Windows 11 Dev VM `.zip` or `.vhdx` file, you can pass it with `-ImagePath "C:\path\to\file"` to avoid downloading it again.*

### What the script does:
1. **Checks for VM**: Detects if the `Wright-Hermes-Sandbox` VM already exists.
2. **Auto-creates VM**: If not found, it downloads Microsoft's pre-built Windows 11 VM, extracts it, creates the VM with 4GB RAM + 4 vCPUs, and enables Guest Service Integration.
3. **PowerShell Direct Connection**: Connects to the VM automatically via VM guest integration (using default Windows developer credentials: `User` / `P@ssw0rd!`).
4. **Auto-provisions**: Copies and runs `provision-vm.ps1` inside the VM (installs Chocolatey, Git, Node, Python, `uv`, copies the Wright codebase, builds the Wright frontend, downloads/installs the official Hermes Desktop app silently, and copies the Wright plugin to every known Hermes load path).
5. **Starts everything**: Launches Hermes Desktop inside the VM.
6. **Opens GUI window**: Launches the VM Connection console (`vmconnect`) on your desktop so you can see and interact with Hermes Desktop.

For unattended CI-style runs, `run-vm-test.ps1` tries the known Windows
developer image credentials and fails fast if they are rejected. It does not
pause for interactive input unless you pass `-AllowCredentialPrompt`. If your
base image uses a custom login, pass it explicitly:

```powershell
.\run-vm-test.ps1 -GuestUsername User -GuestPassword password
```

If the VM never becomes responsive to PowerShell Direct and only reports
`A remote session might have ended`, the base image is not ready for unattended
provisioning yet. Open the VM console from an elevated Hyper-V/Administrator
context, complete any first-login/OOBE steps, verify the local account
credentials, and then run the bootstrap wrapper. It preserves the manually
bootstrapped VM, verifies PowerShell Direct, and saves `base-ready` before any
Hermes or Wright install happens:

```powershell
.\bootstrap-base-vm.ps1 -VmName Wright-Hermes-Automation-Test -GuestUsername User -GuestPassword password
```

Once `base-ready` exists, rerun `run-vm-test.ps1` normally. It restores
`base-ready`, installs tools, installs the latest Hermes Desktop, enables the
Hermes API Server, installs Wright, and creates the later checkpoints.

---

### VM Control Commands

`vmconnect` windows are only console views into the VM. Closing one does not stop
the VM, and opening more than one can make it look like multiple VMs are running.
On this host, `vmconnect` must be launched from an elevated context or it may
show a misleading "could not find the virtual machine" permission error. Use
`manage-vm.ps1` from an Administrator PowerShell on the host for explicit control:

```powershell
cd d:\repos\wright\windows-sandbox
.\manage-vm.ps1 status
.\manage-vm.ps1 connect
.\manage-vm.ps1 restart
.\manage-vm.ps1 stop
.\manage-vm.ps1 start
.\manage-vm.ps1 expose
.\manage-vm.ps1 clear-expose
```

For repeated plugin install tests, run the provisioner without opening another
console window:

```powershell
.\run-vm-test.ps1 -SkipDownload -HermesAlreadyInstalled -NoConnect
```

The `hermes-installed` checkpoint should be treated as a clean Hermes Desktop
base image. It does not need Wright runtime state, and it may not have Hermes'
API Server enabled yet. The Wright install/start scripts enable the API Server
with the local test key and seed only the intended clean Wright settings.

Then open exactly one console window when you are ready to interact:

```powershell
.\manage-vm.ps1 connect
```

If a PowerShell runner is still printing output, let it finish or close that
PowerShell window only after you no longer need its automation. Use
`.\manage-vm.ps1 status` to check the actual VM state.

For real-user Hermes Desktop setup notes, including the API Server requirement,
plugin load paths, LLM status light, and fresh-install hygiene, see
[`docs/hermes-desktop-wright.md`](../docs/hermes-desktop-wright.md).

### Hermes Gateway API Server Requirement

Wright talks to Hermes through the Hermes Gateway API Server. Hermes Desktop
can be running and the Wright plugin can be enabled while the Gateway API is
still off. In that state Wright opens, but chat/session calls fail because
`http://127.0.0.1:8642` is not serving the Hermes API.

For Windows test VMs, the required settings must exist for the `wright` user in
the env file Hermes Desktop actually loads:

```text
%LOCALAPPDATA%\hermes\.env
```

The image scripts also write the profile copy for CLI compatibility:

```text
%USERPROFILE%\.hermes\.env
```

Both files should contain:

```text
API_SERVER_ENABLED=true
API_SERVER_HOST=127.0.0.1
API_SERVER_PORT=8642
API_SERVER_KEY=wright-local-dev
```

The durable image setup command is:

```powershell
hermes gateway install
```

For current-session repair or manual debugging:

```powershell
hermes gateway run
Invoke-WebRequest http://127.0.0.1:8642/health -Headers @{ Authorization = "Bearer wright-local-dev" }
```

The manual Hyper-V image chain now includes a checkpoint named
`hermes-gateway-enabled`, created after the Gateway returned HTTP 200 from
`/health`. Restore that checkpoint when testing Wright without repeating Hermes
Gateway setup.

By default, `run-vm-test.ps1` exposes guest port `8000` on host port `18000`
after starting the Wright backend so endpoints can be tested from the host:

```powershell
Invoke-WebRequest http://127.0.0.1:18000/api/health
```

Pass `-NoExpose` if you want to skip host port forwarding. To set or refresh
the mapping manually:

```powershell
.\manage-vm.ps1 expose
Invoke-WebRequest http://127.0.0.1:18000/api/health
```

The VM IP can change after checkpoint restore or restart, so rerun
`.\manage-vm.ps1 expose` after the VM is restored. To remove the host mapping:

```powershell
.\manage-vm.ps1 clear-expose
```

---

### How to Use the Wright Plugin
Once the VM starts and the Hermes Desktop window opens:
1. Open the Hermes chat interface.
2. Run the `/wright` slash commands to control the plugin:
   - **/wright start**: Automatically builds the Wright frontend, starts the FastAPI backend server (on port 8000), and opens the Wright UI in your default browser.
   - **/wright status**: Shows the active connection status, current workspaces, and active MCP tools.
   - **/wright doctor**: Performs a full diagnostics check on the local database, secrets configuration, and tool paths.
   - **/wright stop**: Shuts down the background FastAPI server process.

### Hermes Desktop Plugin Load Path

On Windows, Hermes Desktop may load the plugin from its bundled agent directory,
not from the profile copy. The provisioning script now installs and verifies the
Wright plugin at:

```text
%LOCALAPPDATA%\hermes\hermes-agent\plugins\wright
```

It also updates the Hermes agent profile plugin folder, removes the older
`%USERPROFILE%\.hermes\plugins\wright` duplicate if present, runs
`hermes plugins enable wright`, and sets `WRIGHT_REPO_DIR=C:\wright` for the
interactive user. If you manually replace the plugin during debugging, fully
quit Hermes Desktop from the system tray before restarting it; the app can cache
loaded plugin modules in memory.

---

## Option B: Windows Sandbox (Ephemeral)

Use this for running the automated test suite (pytest, vitest, playwright) in a disposable environment. Everything is reinstalled from scratch each time (~35 min).

### Prerequisites

1. Windows 11 Pro, Education, or Enterprise.
2. **Windows Sandbox** feature enabled:
   - Search for "Turn Windows features on or off" in the Start menu.
   - Check **Windows Sandbox** and click OK.
   - Restart if prompted.

### How to Run

1. Open `test-windows.wsb` in a text editor.
2. Update the `<HostFolder>` path to point to your cloned wright repo:
   ```xml
   <HostFolder>d:\repos\wright</HostFolder>
   ```
3. Save the file and **double-click `test-windows.wsb`** to launch.
4. The sandbox boots, copies the repo locally (mapped folders don't support symlinks), installs all tools and dependencies, then runs the full test suite automatically.

### What It Runs

The `setup-and-test.ps1` script:
1. Installs Chocolatey, then git, Node.js, Python 3, and uv.
2. Copies the repo to a local sandbox path (`C:\wright-local`) for symlink support.
3. Runs `uv sync` and `npm install`.
4. Installs Playwright Chromium.
5. Runs pytest, vitest, and Playwright integration tests.

---

## Windows Script Reference

### `run-vm-test.ps1`
* **Execution Location**: Host Machine (Administrator PowerShell)
* **Purpose**: Orchestrates the local Hyper-V VM test environment.
* **Key Tasks**:
  - Checks if Hyper-V cmdlets are active (prompts to enable them if missing).
  - Downloads and extracts Microsoft's pre-built Windows 11 Developer VHDX image (approx. 20GB).
  - Configures and boots the virtual machine with 4GB RAM, 4 vCPUs, and Guest Service Integration.
  - Connects using PowerShell Direct, packages the local workspace repository, copies it to the guest VM, and starts `provision-vm.ps1`.
  - Creates VM checkpoints at key states (`tools-ready` and `ready-to-run`) to allow instantaneous rollbacks.
  - Launches `vmconnect` to show the VM GUI.

### `manage-vm.ps1`
* **Execution Location**: Host Machine (Administrator PowerShell)
* **Purpose**: Explicitly starts, stops, restarts, connects to, and reports status for the Hyper-V VM.
* **Key Tasks**:
  - Shows VM state and available checkpoints.
  - Opens a single VM console window when requested.
  - Stops or restarts the VM without running the full provisioning workflow.
  - Exposes the guest Wright API port to the host for endpoint testing.

### `provision-vm.ps1`
* **Execution Location**: Guest VM (PowerShell)
* **Purpose**: Prepares the Windows 11 guest OS to run Hermes Desktop + Wright.
* **Key Tasks**:
  - Installs required packages (Git, Node.js LTS, Python 3, Astral `uv`) via Chocolatey.
  - Downloads the official pre-built `Hermes-Setup.exe` installer and runs it silently.
  - Registers a temporary Scheduled Task to launch the installer in the interactive user's session (bypassing WinRM Session 0 constraints).
  - Compiles the production build of the Wright frontend.
  - Copies the Wright plugin files (`hermes-plugin-wright`) to Hermes agent plugin folders and removes stale duplicate user-level copies.
  - Installs lightweight plugin dependencies into the bundled Hermes Desktop agent venv when it exists.
  - Enables the plugin with `hermes plugins enable wright` and verifies the active plugin is not reported as `not enabled`.
  - Registers Scheduled Tasks to run Hermes Desktop under the interactive logon session with environment variables.

### `setup-and-test.ps1`
* **Execution Location**: Ephemeral Windows Sandbox (PowerShell)
* **Purpose**: Automated test pipeline inside Windows Sandbox.
* **Key Tasks**:
  - Automatically provisions system tools using Chocolatey inside the sandbox.
  - Copies the mapped repository to `C:\wright-local` to support NTFS-native symbolic links needed by npm workspaces.
  - Installs project dependencies via `uv sync` and `npm install`.
  - Spawns the background FastAPI backend server and Vite frontend dev server.
  - Executes the full testing stack: backend `pytest` suite, frontend `vitest` unit tests, and Playwright UI E2E integration tests.
