# Rivet 2 Editor Artifact Contract

`integrations/rivet/editor/manifest.json` is the authority for the editor shipped by Wright.

## Required Identity

- Source repository: `https://github.com/valerypopoff/rivet2.0`
- Source revision: `4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053`
- Rivet app version: `2.8.9`
- License: `MIT`
- Entrypoint: a confined file under `integrations/rivet/editor/dist/`
- Patch list: ordered paths and SHA-256 digests
- Artifact digest: SHA-256 over a deterministic ordered inventory of relative file paths and bytes

## Build Requirements

1. Acquire exactly the configured revision with no submodule or tag substitution.
2. Verify the upstream package version and license before applying Wright patches.
3. Apply every configured patch in order and fail on fuzz/rejects.
4. Build the browser editor using the upstream-pinned Node/Yarn toolchain.
5. Reject generated HTML, CSS, or JavaScript containing executable remote asset references.
6. Produce the deterministic inventory/digest and update the manifest only from a successful build.

## Runtime Requirements

- Verify the artifact digest before returning an available surface manifest.
- Serve only the checked-in files from the confined editor root.
- Do not clone, install, rebuild, or contact a package registry at runtime.
- If verification fails, report the editor unavailable and start no process.
- Do not execute or retain Rivet 1.25.0 as a fallback.
