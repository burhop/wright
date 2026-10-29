# Readiness navigation — 29 October 2026

Compiled native resource from commit `332ce508`; Linux Chromium, simulated MCP
App host and explicitly labeled inert readiness fixture. No workflow ran, source
was saved, tool was configured, or review was granted. This is not Windows
acceptance.

The visible blocked message offers **Open affected step**, resolves the exact
accepted workflow digest and CAD block, and opens its inspector. **Run workflow**
returns to the same preparation view. The correction link remains in the viewport
at 480 pixels. The full-width selected CAD block and inspector are shown in the
screenshots. The inspector title is clipped at its current width; its full name
is readable in the step description. That presentation limitation remains.

The probe does not perform a tool-binding correction or prove prepared-input
migration across source edits. Same-revision input recovery is covered separately
by the shared working-view component test. Real owner navigation/stale-source
checks are in `test_process_readiness_navigation.py`.

Reproduce from the repository root using the tested Node runtime:

```sh
node prototypes/desktop-harness/native_readiness_acceptance.mjs /tmp/wright-readiness-fresh-proof
```

The destination must not exist. `report.json` records the native resource hash
and exact read/navigation calls. Screenshots contain fixture information only.
