# MCP task call budget extension — 2026-09-08

The shared AI task with MCP block now supports `max_tool_calls` from1 through32 inclusive. Its default remains8. The task time limit remains30–600seconds, with its existing300-second default. Existing workflow files keep their saved values; raising the supported ceiling does not raise any saved task's budget automatically.

This extends the current block for engineering tasks that need several inspection or application calls. The workflow compiler validates the integer bound before execution; the editor uses the same bound in its numeric input and shared command/source configuration validation. Configuration remains ordinary canonical scalar settings, so no API/schema migration is needed. The API's existing saved-source compilation applies the bound.

The executor's existing call counter, final evidence requirement, mutation policy, time limit and failure behavior are unchanged.32 dispatched calls may be followed by the existing final model decision; a33rd tool call is rejected before dispatch. The separate16-file output declaration limit remains unchanged.

Historical16-call evidence in `block-interoperability-20260906.md` is preserved as evidence of that version. This amendment does not retroactively change failed runs or workflow acceptance.

Focused tests cover32 accepted,33/zero/fraction/boolean rejected, default8 retained, actual controlled32-call completion and rejection before a33rd dispatch, editor limits and canonical save/reopen. Browser verification and service load remain parent-coordinated; no live workflow is executed by this change.
