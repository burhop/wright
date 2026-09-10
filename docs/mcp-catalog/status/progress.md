# Status page implementation progress

- [x] Reconcile all 78 canonical records across MCP, WebMCP, and hardware.
- [x] Define six mutually exclusive customer/QA categories and evidence rules.
- [x] Add reviewed assessment metadata and versioned schemas.
- [x] Generate matching QA and public allowlist projections.
- [x] Add explicit, idempotent history snapshots and an honest first observation.
- [x] Replace duplicate metrics with six clickable tiles and one detail list.
- [x] Add shareable filters, deep links, keyboard focus, empty state, and mobile layout.
- [x] Add green and fully-qualified history chart with accessible table/JSON.
- [x] Add focused automated tests and CI validation.
- [x] Verify QA and public served builds and capture screenshots.
- [x] Complete the final boundary audit and prepare reviewable local commits.

## 10 September 2026 in-progress review

- [x] Re-review all 36 integrations that began the campaign in In progress.
- [x] Record a dated assessment, category, test boundary, next action, priority,
  owner, and review date for every original record.
- [x] Run a fresh GitHub source scan: 48 repositories were observed and 12 were
  temporarily unavailable; no removal decision relied on HTTP availability alone.
- [x] Qualify NVIDIA Elements 2.2.2 and Grafana MCP 1.0.0 through direct MCP and
  Wright GatewayService calls in clean Intel Linux containers.
- [x] Recheck kernelCAD 0.15.0 and confirm the immutable-package-policy blocker.
- [x] Close kernelCAD after the same immutable-package-policy failure in two
  reviewed releases.
- [x] Load Web OpenSCAD in Chromium, verify all 16 browser tools, and isolate the
  remaining failure to browser-to-relay attachment.
- [x] Move nine broken, superseded records to the Excluded archive with preserved
  evidence and explicit replacement candidates where one exists.
- [x] Run OpenFOAM's advertised pipe-flow operation and independently prove that
  its successful response used the wrong geometry and a field-independent
  pressure-drop calculation.
- [x] Close two unsuitable duplicate candidates after current product-scope
  review: the incomplete Easy-MCP-AutoCAD learning project and Proximile's
  single-commit, broad-control FreeCAD stack.
- [x] Install FreeCAD 1.0 and run sergiudanstan's 165-tool server; close it after
  the first model call reproduced a hard-coded macOS runtime path on Linux.
- [x] Regenerate the 78-record dashboard: 11 Works, 6 Preview, 10 Requires login,
  21 In progress, 30 Abandoned, and 0 Vendor blocked; green total 27.
- [x] Reconcile the 21 remaining yellow records: 18 need a licensed desktop,
  solver, account endpoint, or NVIDIA deployment; 2 have specific repairs in
  progress; 1 needs a bounded dependency and bundled-artifact review. Each has a
  named next test, so none is an unreviewed placeholder.
- [x] Complete full public/QA verification, record one history snapshot, capture
  final screenshots, commit the campaign, and leave the QA dashboard running.

## 10 September 2026 classification correction

- [x] Restore SolidEdgeMCP from Excluded archive to Works; its private source
  distribution boundary does not invalidate native Windows and Wright runtime
  evidence.
- [x] Replace the obsolete SimScale API-only watchlist record with the newly
  discovered community SimScale Edge MCP.
- [x] Run its exact 0.2.0 source through a locked clean-container install and
  all 26 upstream tests; retain it as In progress pending live Edge, SimScale,
  and Wright workflow validation.
