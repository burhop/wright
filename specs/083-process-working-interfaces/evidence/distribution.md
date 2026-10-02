# Installed process-interface resources and saved assets

**Checked:** 2 October 2026. **Status:** partial T050/T051 evidence. Full installed
workspace/common/saved-interface browser acceptance remains pending. Nothing was
published or installed into a campaign runtime.

## Packages

At checkpoint `ffc6babb707108378f99a47aafeec810184e61bc`, the selected packaging
suite passed **3 tests in 45.65 seconds**, without skips. It built a root wheel,
private service wheel/source archive, and a service wheel from that archive.
Each carried the current public client/kit sources, manifests, styles, instructions,
template and fixed static runtime. Extracted-wheel imports were checked with
isolated Python. Installed compilation used an explicitly configured, already
present native dependency root; it made no package download.

```powershell
.venv/Scripts/python.exe -m pytest -q -rs --tb=short -p no:cacheprovider --basetemp=.local-run/process-interfaces-083/t050-resumed-package-proof tests/packaging/test_process_interfaces_distribution.py --junitxml=.local-run/process-interfaces-083/t050-resumed-package-proof.xml
```

The local root wheel is `wright_engineering-0.1.9-py3-none-any.whl`, SHA-256
`23f0b38abed48cdf3bba8d630388c3d2cee7934f959e28ecd2142a0419bdc5b6`.
This is an unpublished qualification artifact built from the recorded mixed
development workspace, not a new release or a clean production candidate.

## Actual previously generated saved revision

The existing actual-model proof's saved interface was copied to a fresh private
test root only after verifying its full immutable inventory:

- UI `ui-eff1d6941f434c3691c79716da3a82fd`.
- Revision `revision-c27524b10e1b435f86cff705f8224a15`.
- Inventory digest `3423993c77eb68487df33856b3e25ca6baab7012a63046ddc63b6c4d80b20220`.
- Compiled JavaScript SHA-256 `f38bd033c5148ed7be956c3fcbdea45cc8000ec8a6c3d41c7eaca9ef7c83d11c`.
- Stylesheet SHA-256 `8f8387707a902f60f5e17d82d6e82142fc22aee8e7c9ef97ce9610f0dbeb04d4`.

Native isolated Python **3.13.5** and a fresh cached Linux/amd64 container using
Python **3.13.15** both served those exact compiled bytes through installed
`ProcessStaticAssets`. All runtime imports pointed inside the extracted wheel;
the container had no Wright checkout mount. Child launches were rejected,
compiler discovery was unavailable, and client connections were confined to the
assigned loopback server. The container additionally had `--network none`, a
read-only filesystem/input mount and bounded writable temporary storage.

The image was `wright:standard-linux-amd64-mcp-isolated`, exact identity
`sha256:512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73`.
No provider, model, dependency or network install was added to it. Only the
disposable labelled test container ran; automatic removal left existing services
and campaign containers unchanged.

Both hosts checked HTTP 200 for `/`, `/app.js`, `/style.css`,
`/wright-runtime.js` and `/__wright/health`, with the restrictive static CSP.
Source, binding, build report and inventory paths returned 404. No new UI
generation, compilation, process start, review or external operation occurred.
Private reproducible preparation/probe files are
`.local-run/process-interfaces-083/t051-prepare-offline-saved.py` and
`t051-offline-saved-probe.py`; copied inputs live in `t051-offline-saved-001`.

This proves reuse of original generated **static assets over actual installed
HTTP**, not a browser presentation bridge, mounted React rendering, run
attachment or the production workspace frontend. The older packaged frontend
was not silently represented as current. T051 remains unchecked until its full
installed common/saved-view journey is verified.

## Additional scope regressions

Presentation identity, saved-start association, API authority and static-host
regressions passed **54 tests in 37.22 seconds**, with two existing dependency
deprecation warnings. Evidence is
`.local-run/process-interfaces-083/t040-resumed-authority-proof.xml`.

```powershell
.venv/Scripts/python.exe -m pytest -q -rs --tb=short -p no:cacheprovider --basetemp=.local-run/process-interfaces-083/t040-resumed-authority-proof packages/workspace_service/tests/test_process_ui_presentations.py packages/workspace_service/tests/test_process_ui_start_association.py apps/api/tests/test_process_ui_surface_authority.py packages/workspace_service/tests/surfaces/test_process_ui_static.py --junitxml=.local-run/process-interfaces-083/t040-resumed-authority-proof.xml
```

These are controlled contract/service/API checks. They do not replace the
remaining live-model, two engineering workflows, installed workspace or human
acceptance obligations.

## Current frontend qualification candidate, resumed 2 October

The complete web app passes TypeScript checking with the existing configuration:

```text
node node_modules/typescript/bin/tsc -p apps/web/tsconfig.app.json --incremental --tsBuildInfoFile .local-run/process-interfaces-083/t053-typescript-app-001.tsbuildinfo
```

An isolated production Vite build using the three existing recovery/composer/
process-definition flags compiled 936 modules in 2.56 seconds. Output is private
`t051-installed-web-002`, not the served or tracked packaged frontend. The existing
large-chunk warning remains; no network/dependency installation occurred.

A private copy of the actual wheel package/force-include sources was staged,
the existing native build script's frontend staging/manifest function was applied
only to that copy, and the standard Python wheel build ran with `--no-isolation`.
The checked native distribution inspector passes. Bundled manifest bytes match
the fresh frontend digest. Retained [build record](../../../artifacts/process-interfaces/083/20261002-current-installed-candidate/build-record.json)
and command/output identify the candidate:

- Wheel SHA-256: `88f3afa844dd8f2d5de1956a194b94922ad68c64a00bde9c173e639d5ab34820`.
- Frontend manifest SHA-256: `34ca258c1b727b49c8b9584b0a7a75f1e59c94b74600aff75304ce7d30c779b1`.
- Private root: `.local-run/process-interfaces-083/t051-current-installed-002`.

This is an unpublished local qualification artifact at the existing source
version, built from the recorded development worktree. It is not the public
artifact of that version or a release candidate approved for publication. The
original packaged frontend has no worktree changes; protected/unrelated-work
checks pass. T050/T051 remain incomplete: next verify actual installed workspace,
common/saved interface mounting, authority and compiler/model-free reuse on native
and clean Docker. The earlier static HTTP proof is not substituted for that work.
# Installed native continuation

See [installed-native reuse](installed-native-reuse.md) for the corrected private
wheel and both ten-step served workspace/common/saved/reload journeys with the
compiler unavailable. This strengthens native evidence but does not close the
remaining clean Docker, full editor or engineering parity obligations.

The subsequent [clean Docker reuse](installed-docker-reuse.md) verifies both
saved-interface/common/reload interaction checks using the same candidate.
Unexpected surrounding workspace MCP/settings errors in fixture 013 were retained;
corrected fixture 014 passes both diagnostic-strict journeys, completing T051's
installed behavior scope. Full editor and engineering proof
obligations remain separate. The current wheel passes native distribution inspection and
exact frontend manifest comparison. No release qualification is implied.
