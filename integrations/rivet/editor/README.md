# Wright Rivet 2 canvas artifact

Wright ships a source-built, canvas-only Rivet editor pinned to commit
`4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053` of
`https://github.com/valerypopoff/rivet2.0.git`. The upstream checkout is a
build-time input only; runtime installations use the verified files in `dist/`.

From the repository root:

```powershell
node integrations/rivet/editor/scripts/acquire-rivet2.mjs
node integrations/rivet/editor/scripts/build-rivet2.mjs
python -m pytest integrations/rivet/editor/tests/test_rivet2_editor_artifact.py
```

The build requires a clean ignored checkout. Remove and reacquire only
`integrations/rivet/spike/.work/rivet2` before a subsequent rebuild. Never point
the build script at a user workspace or another source checkout.

The tracked patch adds the typed `canvasOnly` host policy. The tracked wrapper
uses the supported workspace-host API, memory-only editor storage, and the
origin-scoped Wright message bridge. `manifest.json` records hashes for every
source override and every shipped artifact file.
