# Verification record — partial feature acceptance

## Generated-interface and existing surface boundaries, 2 October 2026

Code checkpoint before this run: `beb3339a` on
`codex/083-process-working-interfaces`. Existing unrelated mixed prototype
changes remain preserved; this is a development-workspace verification, not a
clean production release candidate. No API/model/engineering service was started
for this test group.

Command, from the repository root:

```powershell
.venv/Scripts/python.exe -m pytest -q -rs --tb=short -p no:cacheprovider --basetemp=.local-run/process-interfaces-083/t040-resume-security-010 packages/workspace_service/tests/test_process_ui_authoring.py packages/workspace_service/tests/test_process_ui_build.py packages/workspace_service/tests/test_process_ui_presentations.py packages/workspace_service/tests/test_process_ui_start_association.py packages/workspace_service/tests/test_process_interface_service_boundaries.py packages/workspace_service/tests/surfaces/test_process_ui_static.py apps/api/tests/test_process_ui_surface_authority.py apps/api/tests/test_process_ui_authoring_api.py apps/api/tests/test_surface_scope_security.py apps/api/tests/test_surface_webmcp_security.py apps/api/tests/test_surface_preview_security.py --junitxml=.local-run/process-interfaces-083/t040-resume-security-010.xml
```

Observed terminal completion: **149 passed, zero skips, 117.98 seconds**.
Seven existing Starlette/httpx/AnyIO warnings concern deprecated client/cookie
interfaces; dependency upgrades were not introduced into this feature.

The group checks controlled owner/API boundaries: exact workspace/process/UI/run
and source identities; origin, expiry, revocation and replacement; read-only
preview mutation denial; no generic tool authority; malformed/oversized input;
corrupt immutable assets; fixed build/import/CSS restrictions; repair budgets and
role retention; durable duplicate-request handling; explicit authoring cancel
versus observer disconnect; saved reuse without model/compiler; and closing a
presentation without cancelling its process. Existing MCP App and WebMCP scope
checks remain separate from generated-interface grants.

The models/providers are controlled fixtures. Some builds use the actual fixed
local compiler, but this group does not make a fresh actual-model, live-MCP,
browser, installed-distribution or engineering-acceptance claim. It completes
T040's scoped regression requirement; T053 remains pending the full affected
regression/acceptance record.

## Separate served evidence

Historical result navigation has six passing served-workspace checks and
sixty-four previously recorded focused component checks; see
`workspace-acceptance.md` and
`artifacts/process-interfaces/083/20261002-historical-result-navigation/`.
Its two failed attempts remain retained. Those numbers are separate suites and
are not added into a purported unique total. The original failed engineering run
was neither replayed nor relabelled successful.
