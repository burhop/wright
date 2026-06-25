# Windows Testing Guide

This directory contains scripts for testing Wright (and the Hermes Desktop integration) on Windows 11 in an isolated environment.

## Two Approaches

| | Hyper-V VM (Recommended) | Windows Sandbox |
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
4. **Auto-provisions**: Copies and runs `provision-vm.ps1` inside the VM (installs Chocolatey, Git, Node, Python, `uv`, copies the Wright codebase, builds the Wright frontend, downloads/installs the official Hermes Desktop app silently, and copies the Wright plugin to the Hermes plugins folder).
5. **Starts everything**: Launches Hermes Desktop inside the VM.
6. **Opens GUI window**: Launches the VM Connection console (`vmconnect`) on your desktop so you can see and interact with Hermes Desktop.

---

### How to Use the Wright Plugin
Once the VM starts and the Hermes Desktop window opens:
1. Open the Hermes chat interface.
2. Run the `/wright` slash commands to control the plugin:
   - **/wright start**: Automatically builds the Wright frontend, starts the FastAPI backend server (on port 8000), and opens the Wright UI in your default browser.
   - **/wright status**: Shows the active connection status, current workspaces, and active MCP tools.
   - **/wright doctor**: Performs a full diagnostics check on the local database, secrets configuration, and tool paths.
   - **/wright stop**: Shuts down the background FastAPI server process.

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

### `provision-vm.ps1`
* **Execution Location**: Guest VM (PowerShell)
* **Purpose**: Prepares the Windows 11 guest OS to run Hermes Desktop + Wright.
* **Key Tasks**:
  - Installs required packages (Git, Node.js LTS, Python 3, Astral `uv`) via Chocolatey.
  - Downloads the official pre-built `Hermes-Setup.exe` installer and runs it silently.
  - Registers a temporary Scheduled Task to launch the installer in the interactive user's session (bypassing WinRM Session 0 constraints).
  - Compiles the production build of the Wright frontend.
  - Copies the Wright plugin files (`hermes-plugin-wright`) to the standard `~/.hermes/plugins/wright` folder.
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
