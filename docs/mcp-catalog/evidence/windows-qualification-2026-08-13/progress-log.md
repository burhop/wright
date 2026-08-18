# Windows MCP Qualification Progress

- 2026-08-14T03:13:43.976756+00:00: `brep-mcp` -> **failed**
- 2026-08-14T03:14:37.293030+00:00: `solid-edge-mcp-burhop` -> **failed**
- 2026-08-14T03:14:37.508822+00:00: `aps-mcp-server-nodejs` -> **obsolete_or_unavailable**
- 2026-08-14T03:14:38.809589+00:00: `autodesk-product-help-mcp` -> **partial**
- 2026-08-14T03:14:38.952365+00:00: `autodesk-fusion-desktop-mcp` -> **obsolete_or_unavailable**
- 2026-08-14T03:14:39.083892+00:00: `autodesk-fusion-data-mcp` -> **safety_blocked**
- 2026-08-14T03:14:39.243338+00:00: `onshape-labs-featurescript-mcp` -> **obsolete_or_unavailable**

## Consolidated findings

- `brep-mcp`: pinned `brepjs-cad@0.103.0` installed, initialized, negotiated MCP 2025-11-25, and listed 2 tools. The approved disposable geometry probe failed in the upstream entrypoint when a data URL reached `fileURLToPath`; Wright setup and gateway routing were not represented as passed.
- `solid-edge-mcp-burhop`: pinned source built, initialized as `SolidEdgeMcpServer` 1.0.0.0, negotiated MCP 2025-11-25, and listed 12 tools. The read-only `cad.get_status` probe failed because an omitted nullable `activeDocument` property violates the advertised output schema when no document is open. Wright did not launch, configure, save, close, or otherwise change Solid Edge.
- `aps-mcp-server-nodejs`: the official Autodesk repository is archived and the server requires APS/ACC credentials plus private-key material, so the Windows run stopped without installation.
- `autodesk-product-help-mcp`: the exact public endpoint initialized as `autodesk-knowledge-public-v1-mcp-server` 3.0.2, negotiated MCP 2025-11-25, listed 2 tools, and passed `get_available_products`. Wright's production onboarding planner then stopped at the unrecorded publisher-terms boundary; no terms were accepted and no plan was applied.
- `autodesk-fusion-desktop-mcp`: no preconfigured clean Fusion MCP session was available; Wright did not launch, configure, or modify Autodesk Fusion.
- `autodesk-fusion-data-mcp`: the run stopped before network contact because an exact credential-free endpoint was unavailable and Autodesk OAuth was outside the approved boundary.
- `onshape-labs-featurescript-mcp`: the official Labs page still marks the MCP as coming soon, so Wright did not contact the endpoint, subscribe, authenticate, or accept terms.

No server earned the catalog claim `Installs on Windows with no problems`. The catalog records the independent package/registration, startup, protocol, host/backend, Wright setup, gateway, and cleanup results instead.

## Focused verification

- Final backend/catalog Windows qualification tranche: 67 tests passed, including all harness, projection, recipe, writer, catalog-resource, and platform tests.
- Saved evidence/catalog binding: 4 writer tests passed, including recipe-schema, evidence-schema, recipe-digest, evidence-digest, and seven-entry catalog projection checks.
- React Windows qualification summary and Capability Library tranche: 2 files and 7 tests passed. The runner also emitted a pre-existing Vite native-config warning about `__dirname`; it did not affect the result.
- Full web regression suite: 86 files and 339 tests passed after repairing stale onboarding/registry expectations and the Rivet exact-call dialog focus behavior.
- The gateway mediation performance regression passed five consecutive focused runs after its p95 measurement was hardened against a single Windows scheduler delay while retaining the under-10-percent requirement.

## Development merge gate

- `scripts/check-dev-merge.sh` was run from native Git Bash against the current working tree. All non-live stages passed through Ruff, Prettier, TypeScript, primary mypy, Python distribution validation, release/native/security/program-hardening suites, every configured Python test root, Hermes plugin tests, all 339 web tests, the production web build, and strict MkDocs build.
- The optional broad-workspace mypy invocation reported the repository's known duplicate `conftest` module warning; the gate deliberately treats that invocation as warning-only and continued.
- The final isolated Playwright launch was unavailable because the user-requested local Wright installation was already healthy on port 8000. The gate's port guard stopped rather than replacing that running instance or attaching its tests to a non-isolated database. Port 5173 was free. No merge was attempted, and the running Wright instance was preserved.

## Spec Kit consistency review

- The final read-only analysis found 22 unique functional requirements, 8 unique success criteria, 44 unique implementation tasks, no clarification markers, and no unresolved coverage, ambiguity, duplication, or constitution conflicts.
- One interactive evidence expander lacked the constitution-required stable test identifier. It was corrected, its component regression passed, and the saved-evidence/catalog binding tests remained green.
- `AGENTS.md` continues to point at `specs/074-windows-mcp-qualification/plan.md`; all 44 tasks are complete.

## Cleanup proof

- All disposable per-server roots were removed. `.local-run/windows-mcp-qualification/` contains only ignored safety-decision files.
- Owned MCP process checks completed and no qualification process tree remains.
- Pre-existing Solid Edge process PID 8912 remained running and unchanged.
- `non-allowlist-proof.json` records zero actions.
