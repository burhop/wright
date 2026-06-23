# Windows Sandbox Testing Guide

This directory contains the automation files needed to test **Wright** and its native integration scripts inside a clean, isolated **Windows 11** environment without modifying your laptop's configuration.

## Prerequisites

1. A laptop running **Windows 11 Pro, Education, or Enterprise**.
2. **Windows Sandbox** feature enabled.
   * Search for "Turn Windows features on or off" in the Windows start menu.
   * Check the box for **Windows Sandbox** and click OK.
   * Restart your computer if prompted.

## How to Run

1. Open `test-windows.wsb` in a text editor (like Notepad) on your Windows host.
2. Locate the `<HostFolder>` tag:
   ```xml
   <HostFolder>C:\Users\YOUR_USERNAME\repos\wright</HostFolder>
   ```
   Replace `C:\Users\YOUR_USERNAME\repos\wright` with the absolute path to your cloned `wright` repository on your laptop.
3. Save the file.
4. **Double-click `test-windows.wsb`** to start the Sandbox.
5. The sandbox will boot, mount your workspace folder to `C:\wright`, launch PowerShell, and run the automated tests.

## Under the Hood

The LogonCommand runs `setup-and-test.ps1` inside the sandbox which:
1. Installs Chocolatey.
2. Installs Node.js, Python 3.13, and `uv`.
3. Synces all Python package workspace dependencies.
4. Installs frontend node packages and Playwright dependencies.
5. Runs the full test suite (`pytest`, `vitest`, and `playwright`).
