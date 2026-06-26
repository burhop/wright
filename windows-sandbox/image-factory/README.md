# Wright + Hermes Hyper-V Image Factory

This directory contains the professional, repeatable Windows image pipeline for
testing the Wright installer and Hermes Desktop integration.

The workflow treats VM images as versioned test artifacts:

1. Build a deterministic Windows base image from ISO with unattended setup.
2. Create a known local administrator during setup.
3. Bootstrap remote management and required tools during image build.
4. Install and verify Hermes Desktop in the image pipeline.
5. Publish only validated VHDX artifacts.
6. Run Wright tests in disposable Hyper-V children created from differencing disks.

The older `../run-vm-test.ps1` flow is still useful for interactive rescue and
manual debugging. New automation should prefer this image-factory path because
it does not depend on opaque developer VM credentials or first-boot state.

## Prerequisites

- Windows 11 Pro, Enterprise, or Education host with Hyper-V enabled
- Administrator PowerShell on the host
- [Packer](https://developer.hashicorp.com/packer) on `PATH`
- `oscdimg.exe` on `PATH` or installed through Winget as `Microsoft.OSCDIMG`
- A Windows 11 ISO path or URL available to the host
- The Hermes Desktop installer URL, or a downloaded installer exposed by URL

## Build the Hermes-Ready Image

Run from an Administrator PowerShell on the host:

```powershell
cd D:\repos\wright\windows-sandbox\image-factory
.\Build-WrightHermesImage.ps1 `
  -WindowsIsoPath C:\iso\Win11_23H2_English_x64.iso `
  -WindowsIsoChecksum sha256:REPLACE_WITH_REAL_CHECKSUM `
  -GuestPassword "Use-A-Strong-Local-Test-Password!" `
  -HermesSetupUrl "https://hermes-assets.nousresearch.com/Hermes-Setup.exe" `
  -HermesSetupArguments "/S"
```

Outputs are written under `windows-sandbox/.vm/image-factory/` and are ignored
by Git. The build script generates an `Autounattend.xml` file in that ignored
workspace so no guest password is committed.

By default the script remasters the supplied Windows ISO into a local
`.noprompt.iso` that uses `efisys_noprompt.bin`. This avoids the Hyper-V
`Press any key to boot from CD or DVD` race and lets Packer boot deterministically.
Use `-SkipNoPromptIso` only for interactive troubleshooting.

Hermes Desktop must support unattended installation for the image build to
publish. The build passes `-HermesSetupArguments` to the installer and fails
closed if the installer remains interactive past the timeout. If the public
installer opens a WebView setup UI, request or provide a silent installer
artifact before treating the image as production-ready test infrastructure.

## Run a Disposable Wright Install Test

After a successful image build, create a disposable VM from the published VHDX:

```powershell
.\New-WrightHermesTestVm.ps1 `
  -ParentVhdx D:\repos\wright\windows-sandbox\.vm\image-factory\published\wright-hermes-ready.vhdx `
  -GuestPassword "Use-A-Strong-Local-Test-Password!"
```

The child VM uses a differencing disk. Delete the child VM after the run; keep
the published parent immutable.

## Pipeline Contract

The image factory fails closed:

- no Packer build starts without a generated unattended setup file;
- no image is published until Hermes Desktop is installed, the Wright plugin can
  load, and Hermes Gateway API settings are seeded into
  `%LOCALAPPDATA%\hermes\.env`;
- Windows images install Hermes Gateway auto-start with `hermes gateway install`
  and verify `http://127.0.0.1:8642/health` with the configured bearer token;
- no Wright child VM is considered valid until `/wright start`-equivalent
  runtime checks can reach both the Wright API and Hermes Gateway API.

The intended checkpoint/artifact chain is:

```text
Windows ISO
  -> unattended base image
  -> tools-ready image
  -> hermes-ready image
  -> immutable published VHDX
  -> disposable differencing VM for each Wright test run
```

## Manual Checkpoint Chain

When the fully automated image build cannot be used because the public Hermes
installer is interactive, use the manual Hyper-V chain:

```text
windows-installed-pre-hermes
  -> hermes-configured-pre-wright
  -> wright-plugin-load-verified
  -> wright-installed-verified
  -> hermes-gateway-enabled
```

`hermes-gateway-enabled` is the first checkpoint where Wright should be tested
end-to-end. It has these properties:

- Hermes Desktop is configured and logged in.
- Wright is installed and the plugin is enabled.
- `%LOCALAPPDATA%\hermes\.env` and `%USERPROFILE%\.hermes\.env` contain
  `API_SERVER_ENABLED=true`, `API_SERVER_PORT=8642`, and
  `API_SERVER_KEY=wright-local-dev`.
- `hermes gateway install` has created the Windows login scheduled task.
- `http://127.0.0.1:8642/health` returns HTTP 200 with bearer token
  `wright-local-dev`.

If Gateway regresses, repair the running manual VM from an Administrator
PowerShell on the host:

```powershell
.\Start-HermesGatewayInManualVm.ps1 `
  -VmName wright-hermes-manual `
  -GuestUsername wright `
  -GuestPassword wright `
  -ApiServerKey wright-local-dev `
  -ApiServerPort 8642
```
